"""
Copilot Engine - Persistent Dependency Graph Engine
Maintains an incrementally-updated dependency graph with:
  - File → File edges (imports)
  - Entity → Entity edges (references, extends, uses)
  - Upstream / Downstream queries
  - Impact radius calculation (BFS)
  - Circular dependency detection
  - Incremental edge updates (only rebuild changed file edges)

All edges persisted in SQLite via the DependencyEdge model.
In-memory adjacency lists for fast queries, rebuilt from DB on init.
"""
import os
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from collections import defaultdict, deque
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class GraphEngine:
    """
    Persistent, incrementally-updated dependency graph.
    
    Two layers:
      1. File-level graph: file A imports file B
      2. Entity-level graph: ClassA → extends → ClassB, ServiceX → uses → ModelY

    In-memory adjacency lists for fast traversal.
    SQLite storage for persistence across sessions.
    """

    def __init__(self):
        # In-memory adjacency lists
        self._forward: Dict[str, Set[str]] = defaultdict(set)   # file → files it imports
        self._reverse: Dict[str, Set[str]] = defaultdict(set)   # file → files that import it
        self._entity_forward: Dict[str, Set[str]] = defaultdict(set)  # entity → entities it uses
        self._entity_reverse: Dict[str, Set[str]] = defaultdict(set)  # entity → entities that use it
        self._all_files: Set[str] = set()
        self._loaded = False

    # ══════════════════════════════════════════════
    # Initialization
    # ══════════════════════════════════════════════

    def load_from_db(self, workspace_path: str, db_session) -> Dict[str, Any]:
        """Rebuild in-memory graph from stored DB edges."""
        from models import DependencyEdge, Workspace

        ws = db_session.query(Workspace).filter(Workspace.path == workspace_path).first()
        if not ws:
            return {'loaded': False, 'reason': 'workspace_not_found'}

        self._forward.clear()
        self._reverse.clear()
        self._entity_forward.clear()
        self._entity_reverse.clear()
        self._all_files.clear()

        edges = db_session.query(DependencyEdge).filter(DependencyEdge.workspace_id == ws.id).all()

        file_edges = 0
        entity_edges = 0
        for edge in edges:
            self._all_files.add(edge.source_file)
            self._all_files.add(edge.target_file)

            if edge.edge_type == 'import':
                self._forward[edge.source_file].add(edge.target_file)
                self._reverse[edge.target_file].add(edge.source_file)
                file_edges += 1
            else:
                src_key = f"{edge.source_file}::{edge.source_entity or ''}"
                tgt_key = f"{edge.target_file}::{edge.target_entity or ''}"
                self._entity_forward[src_key].add(tgt_key)
                self._entity_reverse[tgt_key].add(src_key)
                entity_edges += 1

        self._loaded = True
        return {
            'loaded': True,
            'total_files': len(self._all_files),
            'file_edges': file_edges,
            'entity_edges': entity_edges,
        }

    def build_from_indexer(self, workspace_path: str, indexer, db_session) -> Dict[str, Any]:
        """
        Build the entire graph from the semantic indexer's parse results.
        Called after a full index.
        """
        from models import DependencyEdge, Workspace, EntityIndex

        ws = db_session.query(Workspace).filter(Workspace.path == workspace_path).first()
        if not ws:
            return {'built': False, 'reason': 'workspace_not_found'}

        # Clear existing edges
        db_session.query(DependencyEdge).filter(DependencyEdge.workspace_id == ws.id).delete()
        self._forward.clear()
        self._reverse.clear()
        self._entity_forward.clear()
        self._entity_reverse.clear()
        self._all_files.clear()

        root = Path(workspace_path)
        file_edges_added = 0
        entity_edges_added = 0

        # Get all entities for cross-referencing
        all_entities = db_session.query(EntityIndex).filter(EntityIndex.workspace_id == ws.id).all()
        entity_name_map: Dict[str, str] = {}  # entity_name → file_path
        for ent in all_entities:
            entity_name_map[ent.entity_name] = ent.file_path

        # Build file-level import edges
        for fpath in self._walk_code_files(root):
            fpath_str = str(fpath)
            self._all_files.add(fpath_str)

            try:
                content = fpath.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue

            lang = self._detect_lang(fpath)
            imports = self._extract_import_targets(content, fpath_str, lang, root)

            for target in imports:
                if target and target != fpath_str and Path(target).exists():
                    self._forward[fpath_str].add(target)
                    self._reverse[target].add(fpath_str)
                    self._all_files.add(target)

                    db_session.add(DependencyEdge(
                        workspace_id=ws.id,
                        source_file=fpath_str,
                        target_file=target,
                        edge_type='import',
                    ))
                    file_edges_added += 1

            # Build entity-level edges from the content
            entity_refs = self._find_entity_references(content, fpath_str, entity_name_map)
            for ref in entity_refs:
                src_key = f"{fpath_str}::{ref['source_entity']}"
                tgt_key = f"{ref['target_file']}::{ref['target_entity']}"
                self._entity_forward[src_key].add(tgt_key)
                self._entity_reverse[tgt_key].add(src_key)

                db_session.add(DependencyEdge(
                    workspace_id=ws.id,
                    source_file=fpath_str,
                    source_entity=ref['source_entity'],
                    target_file=ref['target_file'],
                    target_entity=ref['target_entity'],
                    edge_type=ref['edge_type'],
                ))
                entity_edges_added += 1

        db_session.commit()
        self._loaded = True

        return {
            'built': True,
            'total_files': len(self._all_files),
            'file_edges': file_edges_added,
            'entity_edges': entity_edges_added,
        }

    def update_file(self, file_path: str, workspace_path: str, db_session) -> Dict[str, Any]:
        """
        Incrementally update edges for a single changed file.
        Removes old edges from this file, re-extracts, adds new edges.
        """
        from models import DependencyEdge, Workspace, EntityIndex

        ws = db_session.query(Workspace).filter(Workspace.path == workspace_path).first()
        if not ws:
            return {'updated': False}

        root = Path(workspace_path)

        # Remove old edges FROM this file
        db_session.query(DependencyEdge).filter(
            DependencyEdge.workspace_id == ws.id,
            DependencyEdge.source_file == file_path,
        ).delete()

        # Clear in-memory edges from this file
        old_targets = self._forward.pop(file_path, set())
        for target in old_targets:
            self._reverse.get(target, set()).discard(file_path)

        # Remove entity edges from this file
        keys_to_remove = [k for k in self._entity_forward if k.startswith(f"{file_path}::")]
        for k in keys_to_remove:
            for tgt in self._entity_forward.pop(k, set()):
                self._entity_reverse.get(tgt, set()).discard(k)

        # Re-extract
        try:
            content = Path(file_path).read_text(encoding='utf-8', errors='ignore')
        except Exception:
            db_session.commit()
            return {'updated': True, 'edges_added': 0}

        lang = self._detect_lang(Path(file_path))
        imports = self._extract_import_targets(content, file_path, lang, root)

        file_edges = 0
        for target in imports:
            if target and target != file_path and Path(target).exists():
                self._forward[file_path].add(target)
                self._reverse[target].add(file_path)

                db_session.add(DependencyEdge(
                    workspace_id=ws.id,
                    source_file=file_path,
                    target_file=target,
                    edge_type='import',
                ))
                file_edges += 1

        # Entity edges
        all_entities = db_session.query(EntityIndex).filter(EntityIndex.workspace_id == ws.id).all()
        entity_name_map = {ent.entity_name: ent.file_path for ent in all_entities}
        entity_refs = self._find_entity_references(content, file_path, entity_name_map)
        entity_edges = 0
        for ref in entity_refs:
            src_key = f"{file_path}::{ref['source_entity']}"
            tgt_key = f"{ref['target_file']}::{ref['target_entity']}"
            self._entity_forward[src_key].add(tgt_key)
            self._entity_reverse[tgt_key].add(src_key)

            db_session.add(DependencyEdge(
                workspace_id=ws.id,
                source_file=file_path,
                source_entity=ref['source_entity'],
                target_file=ref['target_file'],
                target_entity=ref['target_entity'],
                edge_type=ref['edge_type'],
            ))
            entity_edges += 1

        db_session.commit()
        return {'updated': True, 'file_edges': file_edges, 'entity_edges': entity_edges}

    # ══════════════════════════════════════════════
    # Query API
    # ══════════════════════════════════════════════

    def get_dependents(self, file_path: str) -> List[str]:
        """Files that import/depend on this file (upstream propagation)."""
        return list(self._reverse.get(file_path, set()))

    def get_dependencies(self, file_path: str) -> List[str]:
        """Files that this file imports (downstream)."""
        return list(self._forward.get(file_path, set()))

    def get_impact_radius(self, file_path: str, max_depth: int = 4) -> Dict[str, int]:
        """
        BFS from file to find all transitively affected files with depth.
        Returns {affected_file: depth}.
        """
        affected: Dict[str, int] = {}
        queue: deque = deque([(file_path, 0)])
        visited = {file_path}

        while queue:
            current, depth = queue.popleft()
            if depth >= max_depth:
                continue

            for dep in self._reverse.get(current, set()):
                if dep not in visited:
                    visited.add(dep)
                    affected[dep] = depth + 1
                    queue.append((dep, depth + 1))

        return affected

    def detect_circular_dependencies(self) -> List[List[str]]:
        """Find all circular dependency cycles in the file graph (iterative DFS)."""
        cycles: List[List[str]] = []
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        path: List[str] = []

        for start_node in list(self._all_files):
            if start_node in visited:
                continue

            # Iterative DFS using explicit stack
            # Each frame: (node, iterator_over_neighbors, entered)
            # entered=False means we're visiting the node for the first time
            stack = [(start_node, iter(self._forward.get(start_node, set())), False)]

            while stack:
                node, neighbors_iter, entered = stack[-1]

                if not entered:
                    # First visit — mark as visited and on recursion stack
                    if node in visited:
                        stack.pop()
                        continue
                    visited.add(node)
                    rec_stack.add(node)
                    path.append(node)
                    stack[-1] = (node, neighbors_iter, True)

                # Try to advance to the next neighbor
                advanced = False
                for neighbor in neighbors_iter:
                    if neighbor not in visited:
                        stack.append((neighbor, iter(self._forward.get(neighbor, set())), False))
                        advanced = True
                        break
                    elif neighbor in rec_stack:
                        # Found a cycle
                        cycle_start = path.index(neighbor)
                        cycle = path[cycle_start:] + [neighbor]
                        # Normalize: start from smallest
                        min_idx = cycle.index(min(cycle[:-1]))
                        normalized = cycle[min_idx:-1] + cycle[:min_idx] + [cycle[min_idx]]
                        if normalized not in cycles:
                            cycles.append(normalized)
                            if len(cycles) >= 50:
                                return cycles

                if not advanced:
                    # All neighbors exhausted — backtrack
                    path.pop()
                    rec_stack.discard(node)
                    stack.pop()

        return cycles[:50]  # Cap at 50 cycles

    def find_dead_code_files(self) -> List[str]:
        """
        Files that are never imported by anything (potential dead code).
        Excludes: entry points, tests, configs.
        """
        from semantic_indexer import CATEGORY_HINTS

        never_imported = []
        for f in self._all_files:
            if not self._reverse.get(f):
                rel = os.path.basename(f).lower()
                # Don't flag entry points, tests, configs
                if any(k in rel for k in ('main', 'index', 'app', 'server', 'test', 'spec', 'config', 'setup', '__init__', 'manage')):
                    continue
                if CATEGORY_HINTS['test'].search(rel) or CATEGORY_HINTS['config'].search(rel):
                    continue
                never_imported.append(f)

        return never_imported

    def get_most_depended(self, top_n: int = 10) -> List[Dict[str, Any]]:
        """Files with the most reverse dependencies (most critical)."""
        counts = [(f, len(deps)) for f, deps in self._reverse.items() if deps]
        counts.sort(key=lambda x: -x[1])
        return [{'file': f, 'dependents': c} for f, c in counts[:top_n]]

    def get_graph_stats(self) -> Dict[str, Any]:
        """Summary of graph state."""
        return {
            'total_files': len(self._all_files),
            'file_edges': sum(len(v) for v in self._forward.values()),
            'entity_edges': sum(len(v) for v in self._entity_forward.values()),
            'most_depended': self.get_most_depended(5),
            'dead_code_files': len(self.find_dead_code_files()),
            'circular_count': len(self.detect_circular_dependencies()),
        }

    # ══════════════════════════════════════════════
    # Internal helpers
    # ══════════════════════════════════════════════

    SKIP_DIRS = {
        'node_modules', '.git', '__pycache__', '.venv', 'venv',
        'dist', 'build', '.next', '.cache', 'vendor', 'target',
        '.mypy_cache', '.pytest_cache', 'coverage',
    }

    PY_IMPORT = re.compile(r'^\s*(?:from\s+([\w.]+)\s+)?import\s+([\w.,\s]+)', re.MULTILINE)
    TS_IMPORT = re.compile(r'import\s+(?:(?:type\s+)?\{[^}]+\}|[\w]+|\*\s+as\s+\w+)\s+from\s+["\']([^"\']+)["\']', re.MULTILINE)
    REQUIRE = re.compile(r'require\s*\(\s*["\']([^"\']+)["\']\s*\)', re.MULTILINE)

    def _walk_code_files(self, root: Path):
        for fpath in root.rglob('*'):
            if fpath.is_dir():
                continue
            if any(skip in fpath.parts for skip in self.SKIP_DIRS):
                continue
            if fpath.suffix.lower() in ('.py', '.ts', '.tsx', '.js', '.jsx'):
                yield fpath

    def _detect_lang(self, fpath: Path) -> str:
        ext = fpath.suffix.lower()
        return {'.py': 'python', '.ts': 'typescript', '.tsx': 'typescript',
                '.js': 'javascript', '.jsx': 'javascript'}.get(ext, 'unknown')

    def _extract_import_targets(self, content: str, file_path: str, lang: str, root: Path) -> List[str]:
        """Extract resolved file paths from imports."""
        targets = []

        if lang == 'python':
            for m in self.PY_IMPORT.finditer(content):
                module = m.group(1) or m.group(2).split(',')[0].strip()
                resolved = self._resolve_py_module(module, file_path, root)
                if resolved:
                    targets.append(resolved)
        elif lang in ('typescript', 'javascript'):
            for m in self.TS_IMPORT.finditer(content):
                resolved = self._resolve_ts_module(m.group(1), file_path, root)
                if resolved:
                    targets.append(resolved)
            for m in self.REQUIRE.finditer(content):
                resolved = self._resolve_ts_module(m.group(1), file_path, root)
                if resolved:
                    targets.append(resolved)

        return targets

    def _resolve_py_module(self, module: str, source_file: str, root: Path) -> Optional[str]:
        parts = module.split('.')
        dir_path = Path(source_file).parent

        # Try relative
        for i in range(len(parts), 0, -1):
            candidate = dir_path / '/'.join(parts[:i])
            for suffix in ('.py', '/__init__.py'):
                full = Path(str(candidate) + suffix)
                if full.exists():
                    return str(full)

        # Try from root
        for i in range(len(parts), 0, -1):
            candidate = root / '/'.join(parts[:i])
            for suffix in ('.py', '/__init__.py'):
                full = Path(str(candidate) + suffix)
                if full.exists():
                    return str(full)

        return None

    def _resolve_ts_module(self, module: str, source_file: str, root: Path) -> Optional[str]:
        if not module.startswith('.'):
            return None  # Skip node_modules imports
        dir_path = Path(source_file).parent
        candidate = (dir_path / module).resolve()
        for ext in ('', '.ts', '.tsx', '.js', '.jsx', '/index.ts', '/index.js'):
            full = Path(str(candidate) + ext)
            if full.exists():
                return str(full)
        return None

    def _find_entity_references(self, content: str, file_path: str,
                                 entity_name_map: Dict[str, str]) -> List[Dict[str, str]]:
        """
        Find references to known entities in the content.
        e.g., if 'UserModel' exists in entity_name_map and appears in this file,
        create an edge.
        """
        refs = []
        seen = set()

        for entity_name, target_file in entity_name_map.items():
            if target_file == file_path:
                continue
            if len(entity_name) < 3:
                continue

            # Check if the entity name appears in the content (word boundary)
            pattern = r'\b' + re.escape(entity_name) + r'\b'
            if re.search(pattern, content):
                key = (file_path, entity_name, target_file)
                if key not in seen:
                    seen.add(key)
                    refs.append({
                        'source_entity': '',
                        'target_file': target_file,
                        'target_entity': entity_name,
                        'edge_type': 'reference',
                    })

        return refs[:100]  # Cap
