"""
Copilot Engine - Change Impact Analyzer
Deterministic analysis of code changes to detect breaking impacts
across models, DTOs, routes, services, and dependencies.

Covers:
  - Dependency graph construction (imports, references)
  - Impact radius calculation for file changes
  - Breaking change detection (model/DTO/route)
  - Risk scoring per change
  - Cross-module dependency mapping
"""
import os
import re
import ast
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime


# ──────────────────────────────────────────────────────────────
# Data Structures
# ──────────────────────────────────────────────────────────────

@dataclass
class FileNode:
    """A node in the dependency graph."""
    path: str
    relative_path: str = ""
    language: str = ""
    category: str = ""     # model, dto, route, service, util, config, test, unknown
    exports: List[str] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)          # file paths imported
    imported_symbols: Dict[str, str] = field(default_factory=dict)  # symbol → source file


@dataclass
class ChangeImpact:
    changed_file: str
    category: str
    risk_score: float       # 0.0 – 1.0
    risk_level: str         # LOW, MEDIUM, HIGH, CRITICAL
    affected_files: List[str] = field(default_factory=list)
    breaking_changes: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


# ──────────────────────────────────────────────────────────────
# Dependency Graph Builder
# ──────────────────────────────────────────────────────────────

class DependencyGraph:
    """Builds and queries a file-level dependency graph."""

    SKIP_DIRS = {
        'node_modules', '.git', '__pycache__', '.venv', 'venv',
        'dist', 'build', '.next', '.cache', 'vendor', 'target',
        '.mypy_cache', '.pytest_cache', 'coverage',
    }

    CATEGORY_PATTERNS = {
        'model': re.compile(r'model|entity|schema|prisma', re.IGNORECASE),
        'dto': re.compile(r'dto|input|output|request|response|payload|validator|schema\.ts', re.IGNORECASE),
        'route': re.compile(r'route|controller|endpoint|handler|view|api', re.IGNORECASE),
        'service': re.compile(r'service|usecase|use-case|interactor|provider', re.IGNORECASE),
        'middleware': re.compile(r'middleware|guard|interceptor|pipe|filter', re.IGNORECASE),
        'config': re.compile(r'config|setting|constant|env', re.IGNORECASE),
        'test': re.compile(r'test|spec|__test__|\.test\.|\.spec\.', re.IGNORECASE),
        'migration': re.compile(r'migration', re.IGNORECASE),
        'util': re.compile(r'util|helper|lib|common|shared|tool', re.IGNORECASE),
    }

    # Import patterns
    PY_IMPORT = re.compile(r'^\s*(?:from\s+([\w.]+)\s+)?import\s+([\w.,\s]+)', re.MULTILINE)
    TS_IMPORT = re.compile(r'import\s+(?:\{([^}]+)\}|(\w+))\s+from\s+["\']([^"\']+)["\']', re.MULTILINE)
    JS_REQUIRE = re.compile(r'(?:const|let|var)\s+(?:\{([^}]+)\}|(\w+))\s*=\s*require\s*\(\s*["\']([^"\']+)["\']', re.MULTILINE)

    def __init__(self):
        self.nodes: Dict[str, FileNode] = {}
        self._forward: Dict[str, Set[str]] = {}   # file → files it imports
        self._reverse: Dict[str, Set[str]] = {}   # file → files that import it

    def build(self, workspace_path: str) -> Dict[str, Any]:
        """Build dependency graph for entire workspace."""
        self.nodes.clear()
        self._forward.clear()
        self._reverse.clear()

        root = Path(workspace_path)

        # Phase 1: collect all files
        for fpath in self._walk_files(root):
            rel = str(fpath.relative_to(root))
            node = FileNode(
                path=str(fpath),
                relative_path=rel,
                language=self._detect_lang(fpath),
                category=self._classify_file(rel),
            )
            self.nodes[str(fpath)] = node

        # Phase 2: extract imports and build edges
        for fpath, node in self.nodes.items():
            imports = self._extract_imports(fpath, node.language, root)
            node.imports = imports
            self._forward[fpath] = set(imports)
            for imp in imports:
                if imp not in self._reverse:
                    self._reverse[imp] = set()
                self._reverse[imp].add(fpath)

        return {
            'total_files': len(self.nodes),
            'edges': sum(len(v) for v in self._forward.values()),
            'categories': self._category_counts(),
        }

    def get_dependents(self, file_path: str) -> List[str]:
        """Get files that depend on (import from) the given file."""
        return list(self._reverse.get(file_path, set()))

    def get_dependencies(self, file_path: str) -> List[str]:
        """Get files that the given file imports."""
        return list(self._forward.get(file_path, set()))

    def get_impact_radius(self, file_path: str, max_depth: int = 3) -> Dict[str, int]:
        """BFS from file to find all transitively affected files with depth."""
        affected: Dict[str, int] = {}
        queue = [(file_path, 0)]
        visited = {file_path}

        while queue:
            current, depth = queue.pop(0)
            if depth > max_depth:
                continue

            dependents = self.get_dependents(current)
            for dep in dependents:
                if dep not in visited:
                    visited.add(dep)
                    affected[dep] = depth + 1
                    queue.append((dep, depth + 1))

        return affected

    def get_graph_summary(self) -> Dict[str, Any]:
        """Return structured graph summary."""
        return {
            'total_files': len(self.nodes),
            'categories': self._category_counts(),
            'most_depended_on': self._top_depended(10),
            'most_dependencies': self._top_dependencies(10),
            'isolated_files': [
                n.relative_path for n in self.nodes.values()
                if not self._forward.get(n.path) and not self._reverse.get(n.path)
                and n.category != 'test'
            ][:20],
        }

    def _walk_files(self, root: Path):
        """Walk workspace files."""
        for fpath in root.rglob('*'):
            if fpath.is_dir():
                continue
            if any(skip in fpath.parts for skip in self.SKIP_DIRS):
                continue
            if fpath.suffix.lower() in ('.py', '.ts', '.tsx', '.js', '.jsx', '.go', '.rs'):
                yield fpath

    def _detect_lang(self, fpath: Path) -> str:
        ext = fpath.suffix.lower()
        return {
            '.py': 'python', '.ts': 'typescript', '.tsx': 'typescript',
            '.js': 'javascript', '.jsx': 'javascript',
            '.go': 'go', '.rs': 'rust',
        }.get(ext, 'unknown')

    def _classify_file(self, rel_path: str) -> str:
        """Classify file by its path/name."""
        for cat, pat in self.CATEGORY_PATTERNS.items():
            if pat.search(rel_path):
                return cat
        return 'unknown'

    def _extract_imports(self, file_path: str, language: str, root: Path) -> List[str]:
        """Extract resolved import file paths."""
        try:
            content = Path(file_path).read_text(encoding='utf-8', errors='ignore')
        except Exception:
            return []

        if language == 'python':
            return self._resolve_py_imports(content, file_path, root)
        elif language in ('typescript', 'javascript'):
            return self._resolve_ts_imports(content, file_path, root)
        return []

    def _resolve_py_imports(self, content: str, file_path: str, root: Path) -> List[str]:
        """Resolve Python imports to file paths."""
        resolved = []
        file_dir = Path(file_path).parent

        for match in self.PY_IMPORT.finditer(content):
            module = match.group(1) or match.group(2).split(',')[0].strip()
            if not module:
                continue

            # Try resolving relative to file dir and root
            parts = module.split('.')
            for base in [file_dir, root]:
                candidate = base / '/'.join(parts)
                for ext in ['.py', '/__init__.py']:
                    check = Path(str(candidate) + ext)
                    if check.exists() and str(check) in self.nodes:
                        resolved.append(str(check))
                        break

        return resolved

    def _resolve_ts_imports(self, content: str, file_path: str, root: Path) -> List[str]:
        """Resolve TS/JS imports to file paths."""
        resolved = []
        file_dir = Path(file_path).parent

        for pattern in [self.TS_IMPORT, self.JS_REQUIRE]:
            for match in pattern.finditer(content):
                source = match.group(3)
                if source.startswith('.'):
                    # Relative import
                    base = file_dir / source
                    for ext in ['', '.ts', '.tsx', '.js', '.jsx', '/index.ts', '/index.js']:
                        check = Path(str(base) + ext)
                        if check.exists() and str(check) in self.nodes:
                            resolved.append(str(check))
                            break

        return resolved

    def _category_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for n in self.nodes.values():
            counts[n.category] = counts.get(n.category, 0) + 1
        return counts

    def _top_depended(self, limit: int) -> List[Dict[str, Any]]:
        """Files most imported by others."""
        items = [(f, len(deps)) for f, deps in self._reverse.items() if deps]
        items.sort(key=lambda x: x[1], reverse=True)
        return [
            {'file': self.nodes[f].relative_path if f in self.nodes else f, 'dependents': c}
            for f, c in items[:limit]
        ]

    def _top_dependencies(self, limit: int) -> List[Dict[str, Any]]:
        """Files that import the most."""
        items = [(f, len(deps)) for f, deps in self._forward.items() if deps]
        items.sort(key=lambda x: x[1], reverse=True)
        return [
            {'file': self.nodes[f].relative_path if f in self.nodes else f, 'dependencies': c}
            for f, c in items[:limit]
        ]


# ──────────────────────────────────────────────────────────────
# Change Detector
# ──────────────────────────────────────────────────────────────

class ChangeDetector:
    """Detects what kind of changes occurred in a file."""

    # Patterns for detecting structural changes
    PY_CLASS = re.compile(r'class\s+(\w+)')
    PY_FUNC = re.compile(r'def\s+(\w+)')
    PY_FIELD = re.compile(r'(\w+)\s*[:=]')

    TS_INTERFACE = re.compile(r'(?:export\s+)?interface\s+(\w+)')
    TS_CLASS = re.compile(r'(?:export\s+)?class\s+(\w+)')
    TS_FUNC = re.compile(r'(?:export\s+)?(?:async\s+)?function\s+(\w+)')
    TS_FIELD = re.compile(r'(\w+)\??:\s*\w+')

    def detect_changes(self, old_content: str, new_content: str, language: str) -> Dict[str, Any]:
        """Detect structural changes between old and new content."""
        changes = {
            'added_symbols': [],
            'removed_symbols': [],
            'modified_symbols': [],
            'type_changes': [],
            'field_changes': {
                'added': [],
                'removed': [],
                'modified': [],
            },
        }

        if language == 'python':
            old_symbols = self._extract_py_symbols(old_content)
            new_symbols = self._extract_py_symbols(new_content)
        elif language in ('typescript', 'javascript'):
            old_symbols = self._extract_ts_symbols(old_content)
            new_symbols = self._extract_ts_symbols(new_content)
        else:
            return changes

        old_names = set(old_symbols.keys())
        new_names = set(new_symbols.keys())

        changes['added_symbols'] = list(new_names - old_names)
        changes['removed_symbols'] = list(old_names - new_names)

        # Check for type/signature changes in common symbols
        for name in old_names & new_names:
            if old_symbols[name] != new_symbols[name]:
                changes['modified_symbols'].append({
                    'name': name,
                    'old': old_symbols[name],
                    'new': new_symbols[name],
                })

        return changes

    def _extract_py_symbols(self, content: str) -> Dict[str, str]:
        """Extract classes and functions from Python code."""
        symbols = {}
        for match in self.PY_CLASS.finditer(content):
            symbols[match.group(1)] = 'class'
        for match in self.PY_FUNC.finditer(content):
            symbols[match.group(1)] = 'function'
        return symbols

    def _extract_ts_symbols(self, content: str) -> Dict[str, str]:
        """Extract interfaces, classes, functions from TS/JS."""
        symbols = {}
        for match in self.TS_INTERFACE.finditer(content):
            symbols[match.group(1)] = 'interface'
        for match in self.TS_CLASS.finditer(content):
            symbols[match.group(1)] = 'class'
        for match in self.TS_FUNC.finditer(content):
            symbols[match.group(1)] = 'function'
        return symbols


# ──────────────────────────────────────────────────────────────
# Impact Analyzer (Facade)
# ──────────────────────────────────────────────────────────────

class ImpactAnalyzer:
    """Top-level facade for change impact analysis."""

    # Risk weights by file category
    CATEGORY_RISK = {
        'model': 0.9,
        'dto': 0.8,
        'route': 0.7,
        'service': 0.6,
        'middleware': 0.7,
        'config': 0.8,
        'migration': 0.9,
        'util': 0.4,
        'test': 0.1,
        'unknown': 0.3,
    }

    def __init__(self):
        self.graph = DependencyGraph()
        self.detector = ChangeDetector()
        self._workspace_built: Dict[str, bool] = {}

    def build_graph(self, workspace_path: str) -> Dict[str, Any]:
        """Build or rebuild the dependency graph for a workspace."""
        result = self.graph.build(workspace_path)
        self._workspace_built[workspace_path] = True
        return result

    def analyze_change(self, workspace_path: str, changed_file: str,
                       old_content: str = "", new_content: str = "") -> Dict[str, Any]:
        """Analyze the impact of a file change."""
        # Ensure graph is built
        if not self._workspace_built.get(workspace_path):
            self.graph.build(workspace_path)
            self._workspace_built[workspace_path] = True

        node = self.graph.nodes.get(changed_file)
        category = node.category if node else self._classify_path(changed_file)
        language = node.language if node else 'unknown'

        # Get impact radius
        radius = self.graph.get_impact_radius(changed_file)
        affected_files = list(radius.keys())

        # Detect structural changes
        changes = {}
        if old_content and new_content:
            changes = self.detector.detect_changes(old_content, new_content, language)

        # Calculate risk
        risk_score = self._calculate_risk(category, len(affected_files), changes)
        risk_level = self._risk_level(risk_score)

        # Identify breaking changes
        breaking = self._identify_breaking_changes(category, changes, affected_files)
        warnings = self._generate_warnings(category, changes, affected_files)

        impact = ChangeImpact(
            changed_file=changed_file,
            category=category,
            risk_score=risk_score,
            risk_level=risk_level,
            affected_files=affected_files,
            breaking_changes=breaking,
            warnings=warnings,
            details={
                'changes': changes,
                'impact_radius': radius,
                'affected_categories': self._affected_categories(affected_files),
            },
        )

        return asdict(impact)

    def analyze_multiple_changes(self, workspace_path: str, files: List[str]) -> Dict[str, Any]:
        """Analyze impact of multiple file changes together."""
        if not self._workspace_built.get(workspace_path):
            self.graph.build(workspace_path)
            self._workspace_built[workspace_path] = True

        all_affected: Set[str] = set()
        all_breaking: List[str] = []
        all_warnings: List[str] = []
        max_risk = 0.0

        per_file = []
        for f in files:
            result = self.analyze_change(workspace_path, f)
            per_file.append(result)
            all_affected.update(result['affected_files'])
            all_breaking.extend(result['breaking_changes'])
            all_warnings.extend(result['warnings'])
            max_risk = max(max_risk, result['risk_score'])

        # Cross-file impact: do any changed files affect each other?
        cross_impacts = []
        file_set = set(files)
        for f in files:
            deps = self.graph.get_dependents(f)
            cross = file_set & set(deps)
            if cross:
                cross_impacts.append({
                    'file': f,
                    'affects_changed_files': list(cross),
                })

        return {
            'files_changed': len(files),
            'total_affected': len(all_affected),
            'combined_risk_score': round(max_risk, 2),
            'combined_risk_level': self._risk_level(max_risk),
            'breaking_changes': all_breaking,
            'warnings': all_warnings,
            'cross_file_impacts': cross_impacts,
            'per_file': per_file,
        }

    def get_dependency_map(self, workspace_path: str) -> Dict[str, Any]:
        """Get the full dependency graph summary."""
        if not self._workspace_built.get(workspace_path):
            self.graph.build(workspace_path)
            self._workspace_built[workspace_path] = True

        return self.graph.get_graph_summary()

    def get_file_info(self, workspace_path: str, file_path: str) -> Dict[str, Any]:
        """Get dependency info for a specific file."""
        if not self._workspace_built.get(workspace_path):
            self.graph.build(workspace_path)
            self._workspace_built[workspace_path] = True

        node = self.graph.nodes.get(file_path)
        dependents = self.graph.get_dependents(file_path)
        dependencies = self.graph.get_dependencies(file_path)
        radius = self.graph.get_impact_radius(file_path)

        return {
            'file': file_path,
            'category': node.category if node else 'unknown',
            'language': node.language if node else 'unknown',
            'imports_count': len(dependencies),
            'imported_by_count': len(dependents),
            'impact_radius': len(radius),
            'dependencies': [self.graph.nodes[d].relative_path for d in dependencies if d in self.graph.nodes],
            'dependents': [self.graph.nodes[d].relative_path for d in dependents if d in self.graph.nodes],
            'impact_files': {
                self.graph.nodes[f].relative_path if f in self.graph.nodes else f: depth
                for f, depth in radius.items()
            },
        }

    def _calculate_risk(self, category: str, num_affected: int, changes: Dict) -> float:
        """Calculate risk score 0.0 – 1.0."""
        base = self.CATEGORY_RISK.get(category, 0.3)

        # Amplify based on impact
        if num_affected > 20:
            base = min(base + 0.3, 1.0)
        elif num_affected > 10:
            base = min(base + 0.2, 1.0)
        elif num_affected > 5:
            base = min(base + 0.1, 1.0)

        # Amplify for destructive changes
        if changes:
            removed = len(changes.get('removed_symbols', []))
            modified = len(changes.get('modified_symbols', []))
            if removed > 0:
                base = min(base + 0.2, 1.0)
            if modified > 0:
                base = min(base + 0.1, 1.0)

        return round(base, 2)

    def _risk_level(self, score: float) -> str:
        if score >= 0.8:
            return 'CRITICAL'
        elif score >= 0.6:
            return 'HIGH'
        elif score >= 0.4:
            return 'MEDIUM'
        return 'LOW'

    def _identify_breaking_changes(self, category: str, changes: Dict,
                                    affected_files: List[str]) -> List[str]:
        """Identify potentially breaking changes."""
        breaking = []

        if not changes:
            return breaking

        removed = changes.get('removed_symbols', [])
        if removed:
            for sym in removed:
                breaking.append(f'Symbol "{sym}" removed — {len(affected_files)} files may break')

        if category in ('model', 'dto'):
            removed_fields = changes.get('field_changes', {}).get('removed', [])
            for f in removed_fields:
                breaking.append(f'Field "{f}" removed from {category} — downstream code may fail')

        if category == 'route':
            for sym in removed:
                breaking.append(f'Endpoint handler "{sym}" removed — API consumers affected')

        return breaking

    def _generate_warnings(self, category: str, changes: Dict,
                           affected_files: List[str]) -> List[str]:
        """Generate warnings about the change."""
        warnings = []

        if len(affected_files) > 10:
            warnings.append(f'High impact: {len(affected_files)} files are affected by this change')

        if category == 'model' and changes:
            warnings.append('Model change detected — verify migration and DTO consistency')

        if category == 'config':
            warnings.append('Configuration change — may affect runtime behavior across modules')

        if category == 'middleware':
            warnings.append('Middleware change — may affect request processing for multiple routes')

        return warnings

    def _classify_path(self, file_path: str) -> str:
        """Classify file by path patterns."""
        for cat, pat in DependencyGraph.CATEGORY_PATTERNS.items():
            if pat.search(file_path):
                return cat
        return 'unknown'

    def _affected_categories(self, affected_files: List[str]) -> Dict[str, int]:
        """Count affected files by category."""
        counts: Dict[str, int] = {}
        for f in affected_files:
            node = self.graph.nodes.get(f)
            cat = node.category if node else 'unknown'
            counts[cat] = counts.get(cat, 0) + 1
        return counts
