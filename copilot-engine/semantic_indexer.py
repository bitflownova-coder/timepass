"""
Copilot Engine - Incremental Semantic Indexer
Maintains a persistent, incrementally-updated index of every
structural entity in the workspace: models, DTOs, routes, services,
functions, classes, types, middleware, enums.

Only re-parses files whose content hash has changed.
Uses Python `ast` for .py files and regex-based extraction for TS/JS.
Stores everything in SQLite via SQLAlchemy.
"""
import os
import ast
import re
import hashlib
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime, timezone
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────
# Entity Descriptors (in-memory, before DB persistence)
# ──────────────────────────────────────────────────────────────

@dataclass
class ExtractedEntity:
    entity_type: str       # model, dto, route, service, function, class, middleware, enum, type_alias
    entity_name: str
    line_start: int
    line_end: int
    signature: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FileParseResult:
    file_path: str
    file_hash: str
    language: str
    entities: List[ExtractedEntity] = field(default_factory=list)
    imports: List[Dict[str, str]] = field(default_factory=list)   # [{module, names, alias, resolved_path}]
    exports: List[str] = field(default_factory=list)


# ──────────────────────────────────────────────────────────────
# File Classifier
# ──────────────────────────────────────────────────────────────

CATEGORY_HINTS = {
    'model':      re.compile(r'model|entity|schema|prisma', re.I),
    'dto':        re.compile(r'dto|input|output|request|response|payload|validator', re.I),
    'route':      re.compile(r'route|controller|endpoint|handler|view|api', re.I),
    'service':    re.compile(r'service|usecase|use[-_]case|interactor|provider', re.I),
    'middleware':  re.compile(r'middleware|guard|interceptor|pipe|filter', re.I),
    'config':     re.compile(r'config|setting|constant|env', re.I),
    'test':       re.compile(r'test|spec|__test__|\.test\.|\.spec\.', re.I),
    'migration':  re.compile(r'migration', re.I),
    'util':       re.compile(r'util|helper|lib|common|shared|tool', re.I),
}

SKIP_DIRS: Set[str] = {
    'node_modules', '.git', '__pycache__', '.venv', 'venv',
    'dist', 'build', '.next', '.cache', 'vendor', 'target',
    '.mypy_cache', '.pytest_cache', 'coverage', 'env',
    'bin', 'obj', '.idea', '.vscode',
}

CODE_EXTENSIONS = {'.py', '.ts', '.tsx', '.js', '.jsx', '.kt', '.kts', '.java'}


def _file_hash(path: str) -> str:
    """SHA-256 of file content."""
    try:
        return hashlib.sha256(Path(path).read_bytes()).hexdigest()
    except Exception:
        return ""


def _classify_file(rel_path: str) -> str:
    for cat, pat in CATEGORY_HINTS.items():
        if pat.search(rel_path):
            return cat
    return "unknown"


def _detect_language(path: str) -> str:
    ext = Path(path).suffix.lower()
    return {
        '.py': 'python', '.ts': 'typescript', '.tsx': 'typescript',
        '.js': 'javascript', '.jsx': 'javascript',
        '.kt': 'kotlin', '.kts': 'kotlin', '.java': 'java',
    }.get(ext, 'unknown')


# ──────────────────────────────────────────────────────────────
# Python AST Extractor
# ──────────────────────────────────────────────────────────────

class PythonExtractor:
    """Extract entities from Python files using the ast module."""

    # Route decorator patterns (FastAPI, Flask, Django)
    ROUTE_DECORATORS = {'get', 'post', 'put', 'delete', 'patch', 'route', 'api_view'}

    def extract(self, file_path: str, content: str) -> FileParseResult:
        file_hash = hashlib.sha256(content.encode()).hexdigest()
        result = FileParseResult(file_path=file_path, file_hash=file_hash, language='python')

        try:
            tree = ast.parse(content, filename=file_path)
        except SyntaxError:
            return result

        for node in ast.walk(tree):
            # ── Imports ──
            if isinstance(node, ast.Import):
                for alias in node.names:
                    result.imports.append({
                        'module': alias.name,
                        'names': [alias.asname or alias.name],
                        'alias': alias.asname,
                        'line': node.lineno,
                    })
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                names = [a.name for a in node.names]
                result.imports.append({
                    'module': module,
                    'names': names,
                    'line': node.lineno,
                })

            # ── Classes ──
            elif isinstance(node, ast.ClassDef):
                entity = self._extract_class(node, file_path)
                result.entities.append(entity)
                result.exports.append(node.name)

            # ── Functions (top-level) ──
            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                # Only top-level functions (not methods inside classes)
                if self._is_top_level(tree, node):
                    entity = self._extract_function(node, file_path)
                    result.entities.append(entity)
                    result.exports.append(node.name)

        return result

    def _extract_class(self, node: ast.ClassDef, file_path: str) -> ExtractedEntity:
        bases = [self._name_of(b) for b in node.bases]
        fields = []
        methods = []

        for item in node.body:
            if isinstance(item, (ast.AnnAssign, ast.Assign)):
                fld = self._extract_field(item)
                if fld:
                    fields.append(fld)
            elif isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods.append({
                    'name': item.name,
                    'args': [a.arg for a in item.args.args if a.arg != 'self'],
                    'returns': self._annotation_str(item.returns),
                    'line': item.lineno,
                    'decorators': [self._name_of(d) for d in item.decorator_list],
                })

        # Determine entity type
        entity_type = 'class'
        file_cat = _classify_file(file_path)
        if file_cat in ('model', 'dto', 'route', 'service', 'middleware'):
            entity_type = file_cat
        elif any(b in ('BaseModel', 'Base', 'Model', 'Document') for b in bases):
            entity_type = 'model'
        elif any('DTO' in b or 'Schema' in b or 'Serializer' in b for b in bases):
            entity_type = 'dto'
        # Check for route decorators on methods
        elif any(
            any(d in self.ROUTE_DECORATORS for d in m.get('decorators', []))
            for m in methods
        ):
            entity_type = 'route'

        return ExtractedEntity(
            entity_type=entity_type,
            entity_name=node.name,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            signature=f"class {node.name}({', '.join(bases)})",
            metadata={
                'bases': bases,
                'fields': fields,
                'methods': [{'name': m['name'], 'args': m['args'], 'returns': m.get('returns')} for m in methods],
                'decorators': [self._name_of(d) for d in node.decorator_list],
            },
        )

    def _extract_function(self, node, file_path: str) -> ExtractedEntity:
        args = [a.arg for a in node.args.args]
        returns = self._annotation_str(node.returns)
        decorators = [self._name_of(d) for d in node.decorator_list]

        entity_type = 'function'
        if any(d in self.ROUTE_DECORATORS for d in decorators):
            entity_type = 'route'
        elif _classify_file(file_path) == 'middleware':
            entity_type = 'middleware'

        # Extract route info from decorators
        route_info = {}
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call) and hasattr(dec, 'args') and dec.args:
                fname = self._name_of(dec)
                if fname in self.ROUTE_DECORATORS:
                    try:
                        route_info['method'] = fname.upper() if fname != 'route' else 'ANY'
                        if isinstance(dec.args[0], ast.Constant):
                            route_info['path'] = dec.args[0].value
                    except Exception:
                        pass

        return ExtractedEntity(
            entity_type=entity_type,
            entity_name=node.name,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            signature=f"def {node.name}({', '.join(args)}) -> {returns}",
            metadata={
                'args': args,
                'returns': returns,
                'decorators': decorators,
                'is_async': isinstance(node, ast.AsyncFunctionDef),
                'route': route_info if route_info else None,
            },
        )

    def _extract_field(self, node) -> Optional[Dict[str, Any]]:
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            return {
                'name': node.target.id,
                'type': self._annotation_str(node.annotation),
                'has_default': node.value is not None,
                'line': node.lineno,
            }
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    return {
                        'name': target.id,
                        'type': 'Any',
                        'has_default': True,
                        'line': node.lineno,
                    }
        return None

    def _annotation_str(self, node) -> str:
        if node is None:
            return 'None'
        return ast.unparse(node)

    def _name_of(self, node) -> str:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._name_of(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
            return self._name_of(node.func)
        return str(getattr(node, 'id', ''))

    def _is_top_level(self, tree: ast.Module, target) -> bool:
        for node in tree.body:
            if node is target:
                return True
        return False


# ──────────────────────────────────────────────────────────────
# TypeScript / JavaScript Regex Extractor
# ──────────────────────────────────────────────────────────────

class TSExtractor:
    """Extract entities from TS/JS files using regex patterns."""

    # Import patterns
    RE_IMPORT = re.compile(
        r'import\s+(?:(?:type\s+)?(?:\{([^}]+)\}|(\w+)|\*\s+as\s+(\w+)))\s+from\s+["\']([^"\']+)["\']',
        re.MULTILINE
    )
    RE_REQUIRE = re.compile(
        r'(?:const|let|var)\s+(?:\{([^}]+)\}|(\w+))\s*=\s*require\s*\(\s*["\']([^"\']+)["\']\s*\)',
        re.MULTILINE
    )

    # Entity patterns
    RE_CLASS = re.compile(
        r'^(?:export\s+)?(?:default\s+)?(?:abstract\s+)?class\s+(\w+)(?:\s+extends\s+(\w+))?(?:\s+implements\s+([\w,\s]+))?',
        re.MULTILINE
    )
    RE_INTERFACE = re.compile(
        r'^(?:export\s+)?interface\s+(\w+)(?:\s+extends\s+([\w,\s]+))?',
        re.MULTILINE
    )
    RE_TYPE_ALIAS = re.compile(
        r'^(?:export\s+)?type\s+(\w+)\s*(?:<[^>]+>)?\s*=',
        re.MULTILINE
    )
    RE_FUNCTION = re.compile(
        r'^(?:export\s+)?(?:default\s+)?(?:async\s+)?function\s+(\w+)\s*(?:<[^>]*>)?\s*\(([^)]*)\)(?:\s*:\s*([^\n{]+))?',
        re.MULTILINE
    )
    RE_CONST_FN = re.compile(
        r'^(?:export\s+)?const\s+(\w+)\s*(?::\s*[^=]+)?\s*=\s*(?:async\s+)?\(?([^)]*)\)?\s*(?::\s*([^\n=>{]+))?\s*=>',
        re.MULTILINE
    )
    RE_ENUM = re.compile(
        r'^(?:export\s+)?(?:const\s+)?enum\s+(\w+)',
        re.MULTILINE
    )

    # Route patterns
    RE_EXPRESS_ROUTE = re.compile(
        r'(?:app|router)\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
        re.MULTILINE
    )
    RE_NEST_DECORATOR = re.compile(
        r'@(Get|Post|Put|Delete|Patch)\s*\(\s*["\']?([^"\')\s]*)',
        re.MULTILINE
    )
    RE_NEXT_API = re.compile(
        r'export\s+(?:default\s+)?(?:async\s+)?function\s+(GET|POST|PUT|DELETE|PATCH|HEAD)',
        re.MULTILINE
    )

    def extract(self, file_path: str, content: str) -> FileParseResult:
        file_hash = hashlib.sha256(content.encode()).hexdigest()
        lang = 'typescript' if Path(file_path).suffix in ('.ts', '.tsx') else 'javascript'
        result = FileParseResult(file_path=file_path, file_hash=file_hash, language=lang)
        lines = content.split('\n')

        # ── Imports ──
        for m in self.RE_IMPORT.finditer(content):
            names_str = m.group(1) or m.group(2) or m.group(3) or ''
            names = [n.strip().split(' as ')[0].strip() for n in names_str.split(',') if n.strip()]
            result.imports.append({
                'module': m.group(4),
                'names': names,
                'line': content[:m.start()].count('\n') + 1,
            })
        for m in self.RE_REQUIRE.finditer(content):
            names_str = m.group(1) or m.group(2) or ''
            names = [n.strip() for n in names_str.split(',') if n.strip()]
            result.imports.append({
                'module': m.group(3),
                'names': names,
                'line': content[:m.start()].count('\n') + 1,
            })

        # ── Classes ──
        for m in self.RE_CLASS.finditer(content):
            line_start = content[:m.start()].count('\n') + 1
            name = m.group(1)
            bases = [m.group(2)] if m.group(2) else []
            implements = [x.strip() for x in (m.group(3) or '').split(',') if x.strip()]
            entity_type = self._classify_entity(name, file_path, 'class')
            fields = self._extract_class_fields(content, m.end(), lines)
            line_end = self._find_block_end(content, m.end(), lines)
            result.entities.append(ExtractedEntity(
                entity_type=entity_type,
                entity_name=name,
                line_start=line_start,
                line_end=line_end,
                signature=m.group(0).strip(),
                metadata={'bases': bases, 'implements': implements, 'fields': fields},
            ))
            result.exports.append(name)

        # ── Interfaces ──
        for m in self.RE_INTERFACE.finditer(content):
            line_start = content[:m.start()].count('\n') + 1
            name = m.group(1)
            extends = [x.strip() for x in (m.group(2) or '').split(',') if x.strip()]
            fields = self._extract_class_fields(content, m.end(), lines)
            entity_type = 'dto' if any(k in name.lower() for k in ('dto', 'input', 'output', 'request', 'response', 'payload')) else 'type_alias'
            line_end = self._find_block_end(content, m.end(), lines)
            result.entities.append(ExtractedEntity(
                entity_type=entity_type,
                entity_name=name,
                line_start=line_start,
                line_end=line_end,
                signature=m.group(0).strip(),
                metadata={'extends': extends, 'fields': fields},
            ))
            result.exports.append(name)

        # ── Type Aliases ──
        for m in self.RE_TYPE_ALIAS.finditer(content):
            line_start = content[:m.start()].count('\n') + 1
            result.entities.append(ExtractedEntity(
                entity_type='type_alias',
                entity_name=m.group(1),
                line_start=line_start,
                line_end=line_start,
                signature=m.group(0).strip(),
            ))
            result.exports.append(m.group(1))

        # ── Enums ──
        for m in self.RE_ENUM.finditer(content):
            line_start = content[:m.start()].count('\n') + 1
            result.entities.append(ExtractedEntity(
                entity_type='enum',
                entity_name=m.group(1),
                line_start=line_start,
                line_end=self._find_block_end(content, m.end(), lines),
                signature=m.group(0).strip(),
            ))
            result.exports.append(m.group(1))

        # ── Functions ──
        for m in self.RE_FUNCTION.finditer(content):
            line_start = content[:m.start()].count('\n') + 1
            name = m.group(1)
            entity_type = self._classify_entity(name, file_path, 'function')
            result.entities.append(ExtractedEntity(
                entity_type=entity_type,
                entity_name=name,
                line_start=line_start,
                line_end=self._find_block_end(content, m.end(), lines),
                signature=m.group(0).strip(),
                metadata={'args': m.group(2), 'returns': (m.group(3) or '').strip()},
            ))
            result.exports.append(name)

        # ── Arrow Functions ──
        for m in self.RE_CONST_FN.finditer(content):
            line_start = content[:m.start()].count('\n') + 1
            name = m.group(1)
            entity_type = self._classify_entity(name, file_path, 'function')
            result.entities.append(ExtractedEntity(
                entity_type=entity_type,
                entity_name=name,
                line_start=line_start,
                line_end=self._find_block_end(content, m.end(), lines),
                signature=m.group(0).strip(),
                metadata={'args': m.group(2), 'returns': (m.group(3) or '').strip()},
            ))
            result.exports.append(name)

        # ── Routes (Express) ──
        for m in self.RE_EXPRESS_ROUTE.finditer(content):
            line_start = content[:m.start()].count('\n') + 1
            result.entities.append(ExtractedEntity(
                entity_type='route',
                entity_name=f"{m.group(1).upper()} {m.group(2)}",
                line_start=line_start,
                line_end=line_start,
                signature=m.group(0).strip(),
                metadata={'method': m.group(1).upper(), 'path': m.group(2)},
            ))

        # ── Routes (NestJS) ──
        for m in self.RE_NEST_DECORATOR.finditer(content):
            line_start = content[:m.start()].count('\n') + 1
            result.entities.append(ExtractedEntity(
                entity_type='route',
                entity_name=f"{m.group(1).upper()} {m.group(2)}",
                line_start=line_start,
                line_end=line_start,
                signature=m.group(0).strip(),
                metadata={'method': m.group(1).upper(), 'path': m.group(2)},
            ))

        # ── Next.js API Routes ──
        for m in self.RE_NEXT_API.finditer(content):
            line_start = content[:m.start()].count('\n') + 1
            result.entities.append(ExtractedEntity(
                entity_type='route',
                entity_name=f"{m.group(1)} {file_path}",
                line_start=line_start,
                line_end=line_start,
                signature=m.group(0).strip(),
                metadata={'method': m.group(1), 'path': file_path},
            ))

        return result

    def _classify_entity(self, name: str, file_path: str, default: str) -> str:
        file_cat = _classify_file(file_path)
        if file_cat in ('model', 'dto', 'route', 'service', 'middleware'):
            return file_cat
        lname = name.lower()
        if any(k in lname for k in ('controller', 'handler', 'router', 'route')):
            return 'route'
        if any(k in lname for k in ('service', 'usecase', 'provider')):
            return 'service'
        if any(k in lname for k in ('dto', 'input', 'output', 'request', 'response')):
            return 'dto'
        if any(k in lname for k in ('model', 'entity', 'schema')):
            return 'model'
        if any(k in lname for k in ('middleware', 'guard', 'interceptor')):
            return 'middleware'
        return default

    def _extract_class_fields(self, content: str, start_pos: int, lines: list) -> List[Dict]:
        """Extract fields from the class/interface body (first-level properties)."""
        fields = []
        brace_count = 0
        started = False
        field_re = re.compile(r'^\s+(?:readonly\s+)?(\w+)(\?)?:\s*(.+?)(?:;|$)')

        i = start_pos
        while i < len(content):
            ch = content[i]
            if ch == '{':
                brace_count += 1
                started = True
            elif ch == '}':
                brace_count -= 1
                if started and brace_count <= 0:
                    break
            i += 1

        if started:
            block = content[start_pos:i]
            for fm in field_re.finditer(block):
                fields.append({
                    'name': fm.group(1),
                    'optional': fm.group(2) == '?',
                    'type': fm.group(3).strip().rstrip(';'),
                })

        return fields[:50]  # Cap at 50

    def _find_block_end(self, content: str, start_pos: int, lines: list) -> int:
        brace_count = 0
        started = False
        i = start_pos
        while i < len(content):
            if content[i] == '{':
                brace_count += 1
                started = True
            elif content[i] == '}':
                brace_count -= 1
                if started and brace_count <= 0:
                    return content[:i].count('\n') + 1
            i += 1
        return content[:start_pos].count('\n') + 1


# ──────────────────────────────────────────────────────────────
# Kotlin / Java Regex Extractor
# ──────────────────────────────────────────────────────────────

class KotlinExtractor:
    """Extract entities from Kotlin/Java files using regex patterns."""

    # Import pattern: import com.bitflow.finance.di.RepositoryModule
    RE_IMPORT = re.compile(
        r'^import\s+([\w.]+(?:\s+as\s+\w+)?)',
        re.MULTILINE
    )

    # Package declaration
    RE_PACKAGE = re.compile(r'^package\s+([\w.]+)', re.MULTILINE)

    # Class variants:
    #   data class Foo(...), abstract class Foo, sealed class Foo,
    #   open class Foo, class Foo : Base(), @Entity data class Foo
    RE_CLASS = re.compile(
        r'^(?:@\w+(?:\([^)]*\))?\s*\n?)*'
        r'(?:(?:public|private|protected|internal)\s+)?'
        r'(?:(?:data|sealed|abstract|open|inner|value|inline)\s+)*'
        r'class\s+(\w+)'
        r'(?:\s*<[^>]+>)?'
        r'(?:\s*(?:@\w+\s+)?(?:(?:private|internal)\s+)?constructor)?'
        r'(?:\s*\([^)]*\))?'
        r'(?:\s*:\s*([^{]+?))?'
        r'(?:\s*\{|\s*$)',
        re.MULTILINE
    )

    # Interface: interface Foo : Bar, sealed interface Foo
    RE_INTERFACE = re.compile(
        r'^(?:(?:public|private|protected|internal)\s+)?'
        r'(?:sealed\s+|fun\s+)?'
        r'interface\s+(\w+)'
        r'(?:\s*<[^>]+>)?'
        r'(?:\s*:\s*([^{]+?))?'
        r'(?:\s*\{|\s*$)',
        re.MULTILINE
    )

    # Object / companion object
    RE_OBJECT = re.compile(
        r'^(?:(?:public|private|protected|internal)\s+)?'
        r'(?:companion\s+)?object\s+(\w+)'
        r'(?:\s*:\s*([^{]+?))?'
        r'(?:\s*\{|\s*$)',
        re.MULTILINE
    )

    # Enum class
    RE_ENUM = re.compile(
        r'^(?:(?:public|private|protected|internal)\s+)?'
        r'enum\s+class\s+(\w+)',
        re.MULTILINE
    )

    # Functions: fun foo(...), suspend fun foo(...), override fun foo(...)
    RE_FUNCTION = re.compile(
        r'^\s*(?:@\w+(?:\([^)]*\))?\s*\n?\s*)*'
        r'(?:(?:public|private|protected|internal|override|open|abstract|suspend|inline|operator|infix|tailrec|external)\s+)*'
        r'fun\s+(?:<[^>]+>\s+)?(\w+)\s*\(([^)]*)\)'
        r'(?:\s*:\s*([^{=]+?))?'
        r'(?:\s*[{=]|\s*$)',
        re.MULTILINE
    )

    # Annotation detector (for classifying entities)
    RE_ANNOTATION_BLOCK = re.compile(
        r'(?:@(\w+)(?:\([^)]*\))?\s*\n?\s*)+(?=(?:(?:public|private|protected|internal)\s+)?(?:(?:data|sealed|abstract|open)\s+)*(?:class|interface|object|enum|fun))',
        re.MULTILINE
    )

    # Single annotation right above a declaration
    RE_SINGLE_ANNOTATION = re.compile(r'@(\w+)')

    # Kotlin composable function
    RE_COMPOSABLE = re.compile(
        r'@Composable\s*\n?\s*(?:(?:public|private|protected|internal)\s+)?fun\s+(\w+)',
        re.MULTILINE
    )

    def extract(self, file_path: str, content: str) -> FileParseResult:
        file_hash = hashlib.sha256(content.encode()).hexdigest()
        lang = 'java' if Path(file_path).suffix == '.java' else 'kotlin'
        result = FileParseResult(file_path=file_path, file_hash=file_hash, language=lang)
        lines = content.split('\n')

        # ── Package ──
        pkg_match = self.RE_PACKAGE.search(content)
        pkg = pkg_match.group(1) if pkg_match else ''

        # ── Imports ──
        for m in self.RE_IMPORT.finditer(content):
            imp = m.group(1).strip()
            names = [imp.split('.')[-1].split(' as ')[0]]
            module = '.'.join(imp.split('.')[:-1])
            result.imports.append({
                'module': module,
                'names': names,
                'line': content[:m.start()].count('\n') + 1,
            })

        # Track seen entity positions to avoid duplicates
        seen_positions = set()

        # ── Classes ──
        for m in self.RE_CLASS.finditer(content):
            line_start = content[:m.start()].count('\n') + 1
            if line_start in seen_positions:
                continue
            seen_positions.add(line_start)
            name = m.group(1)
            supertypes = [s.strip().split('(')[0].strip() for s in (m.group(2) or '').split(',') if s.strip()] if m.group(2) else []
            # Get annotations from preceding lines
            annotations = self._get_annotations_before(content, m.start())
            entity_type = self._classify_kotlin_entity(name, file_path, annotations, 'class')
            # Check for data class
            prefix = content[max(0, m.start()-30):m.start()]
            is_data = 'data ' in prefix or content[m.start():m.end()].startswith('data ')
            line_end = self._find_block_end(content, m.end(), lines)
            result.entities.append(ExtractedEntity(
                entity_type=entity_type,
                entity_name=name,
                line_start=line_start,
                line_end=line_end,
                signature=m.group(0).strip()[:200],
                metadata={
                    'supertypes': supertypes,
                    'annotations': annotations,
                    'data_class': is_data,
                    'package': pkg,
                },
            ))
            result.exports.append(name)

        # ── Interfaces ──
        for m in self.RE_INTERFACE.finditer(content):
            line_start = content[:m.start()].count('\n') + 1
            if line_start in seen_positions:
                continue
            seen_positions.add(line_start)
            name = m.group(1)
            extends = [s.strip() for s in (m.group(2) or '').split(',') if s.strip()]
            annotations = self._get_annotations_before(content, m.start())
            entity_type = self._classify_kotlin_entity(name, file_path, annotations, 'interface')
            line_end = self._find_block_end(content, m.end(), lines)
            result.entities.append(ExtractedEntity(
                entity_type=entity_type,
                entity_name=name,
                line_start=line_start,
                line_end=line_end,
                signature=m.group(0).strip()[:200],
                metadata={'extends': extends, 'annotations': annotations, 'package': pkg},
            ))
            result.exports.append(name)

        # ── Objects ──
        for m in self.RE_OBJECT.finditer(content):
            line_start = content[:m.start()].count('\n') + 1
            if line_start in seen_positions:
                continue
            seen_positions.add(line_start)
            name = m.group(1)
            supers = [s.strip() for s in (m.group(2) or '').split(',') if s.strip()]
            annotations = self._get_annotations_before(content, m.start())
            is_companion = 'companion ' in content[max(0, m.start()-15):m.start()+15]
            line_end = self._find_block_end(content, m.end(), lines)
            result.entities.append(ExtractedEntity(
                entity_type='service' if not is_companion else 'class',
                entity_name=name,
                line_start=line_start,
                line_end=line_end,
                signature=m.group(0).strip()[:200],
                metadata={'supertypes': supers, 'companion': is_companion, 'annotations': annotations, 'package': pkg},
            ))
            result.exports.append(name)

        # ── Enums ──
        for m in self.RE_ENUM.finditer(content):
            line_start = content[:m.start()].count('\n') + 1
            if line_start in seen_positions:
                continue
            seen_positions.add(line_start)
            result.entities.append(ExtractedEntity(
                entity_type='enum',
                entity_name=m.group(1),
                line_start=line_start,
                line_end=self._find_block_end(content, m.end(), lines),
                signature=m.group(0).strip(),
                metadata={'package': pkg},
            ))
            result.exports.append(m.group(1))

        # ── Top-level Functions ──
        for m in self.RE_FUNCTION.finditer(content):
            line_start = content[:m.start()].count('\n') + 1
            if line_start in seen_positions:
                continue
            # Skip functions inside class bodies (indented)
            line_text = lines[line_start - 1] if line_start <= len(lines) else ''
            indent = len(line_text) - len(line_text.lstrip())
            # We capture both top-level and class-level functions for completeness
            name = m.group(1)
            annotations = self._get_annotations_before(content, m.start())
            entity_type = self._classify_kotlin_function(name, file_path, annotations, indent)
            seen_positions.add(line_start)
            result.entities.append(ExtractedEntity(
                entity_type=entity_type,
                entity_name=name,
                line_start=line_start,
                line_end=self._find_block_end(content, m.end(), lines),
                signature=m.group(0).strip()[:200],
                metadata={
                    'args': m.group(2).strip() if m.group(2) else '',
                    'returns': (m.group(3) or '').strip(),
                    'annotations': annotations,
                    'indent': indent,
                    'package': pkg,
                },
            ))
            result.exports.append(name)

        return result

    def _get_annotations_before(self, content: str, pos: int) -> List[str]:
        """Extract annotation names from lines immediately above a declaration."""
        annotations = []
        # Look back up to 200 chars before the match
        lookback = content[max(0, pos - 300):pos]
        # Get last few lines
        recent_lines = lookback.strip().split('\n')[-5:]
        for line in recent_lines:
            stripped = line.strip()
            if stripped.startswith('@'):
                for am in self.RE_SINGLE_ANNOTATION.finditer(stripped):
                    annotations.append(am.group(1))
            elif stripped and not stripped.startswith('//'):
                # Non-annotation, non-comment line means annotations ended
                annotations = []
        return annotations

    def _classify_kotlin_entity(self, name: str, file_path: str, annotations: List[str], default: str) -> str:
        """Classify a Kotlin class/interface based on name, path, and annotations."""
        lname = name.lower()
        # Annotation-based classification
        annotation_set = set(a.lower() for a in annotations)
        if 'entity' in annotation_set:
            return 'model'
        if 'dao' in annotation_set:
            return 'dao'
        if 'hiltviewmodel' in annotation_set:
            return 'service'  # ViewModels are treated as services
        if 'module' in annotation_set or 'installin' in annotation_set:
            return 'middleware'  # DI modules
        if 'composable' in annotation_set:
            return 'route'  # UI screens mapped to route

        # Name-based classification
        file_cat = _classify_file(file_path)
        if file_cat in ('model', 'dto', 'route', 'service', 'middleware'):
            return file_cat
        if any(k in lname for k in ('repository', 'repo')):
            return 'service'
        if any(k in lname for k in ('viewmodel', 'presenter')):
            return 'service'
        if any(k in lname for k in ('dao', 'database')):
            return 'dao'
        if any(k in lname for k in ('entity', 'model')):
            return 'model'
        if any(k in lname for k in ('dto', 'request', 'response', 'state', 'uistate')):
            return 'dto'
        if any(k in lname for k in ('screen', 'composable', 'component', 'view', 'dialog')):
            return 'route'
        if any(k in lname for k in ('module', 'provider', 'factory')):
            return 'middleware'
        if any(k in lname for k in ('worker', 'service', 'usecase', 'interactor')):
            return 'service'
        if any(k in lname for k in ('converter', 'mapper', 'adapter', 'helper', 'util')):
            return 'util'
        return default

    def _classify_kotlin_function(self, name: str, file_path: str, annotations: List[str], indent: int) -> str:
        """Classify a Kotlin function."""
        annotation_set = set(a.lower() for a in annotations)
        if 'composable' in annotation_set:
            return 'route'  # Composable screen/component
        if 'query' in annotation_set or 'insert' in annotation_set or 'update' in annotation_set or 'delete' in annotation_set:
            return 'dao'  # Room DAO method
        if 'provides' in annotation_set or 'binds' in annotation_set:
            return 'middleware'  # DI provider
        if 'get' in annotation_set or 'post' in annotation_set or 'put' in annotation_set:
            return 'route'  # Ktor/Retrofit
        return 'function'

    def _find_block_end(self, content: str, start_pos: int, lines: list) -> int:
        brace_count = 0
        started = False
        i = start_pos
        while i < len(content):
            if content[i] == '{':
                brace_count += 1
                started = True
            elif content[i] == '}':
                brace_count -= 1
                if started and brace_count <= 0:
                    return content[:i].count('\n') + 1
            i += 1
        return content[:start_pos].count('\n') + 1


# ──────────────────────────────────────────────────────────────
# Semantic Indexer (Orchestrator)
# ──────────────────────────────────────────────────────────────

class SemanticIndexer:
    """
    Incrementally indexes a workspace:
      1. Walk all code files
      2. Compare file hash to stored hash
      3. Re-parse only changed files
      4. Upsert entities + imports into DB
    """

    def __init__(self):
        self._py_extractor = PythonExtractor()
        self._ts_extractor = TSExtractor()
        self._kt_extractor = KotlinExtractor()
        self._known_hashes: Dict[str, str] = {}  # file_path → last known hash

    # ── Public API ──

    def full_index(self, workspace_path: str, db_session=None) -> Dict[str, Any]:
        """Full workspace index (used on first run or forced rebuild)."""
        root = Path(workspace_path)
        if not root.exists():
            return {'error': 'Workspace not found', 'indexed': 0}

        files = list(self._walk_files(root))
        results = {
            'total_files': len(files),
            'indexed': 0,
            'skipped': 0,
            'entities_found': 0,
            'by_type': {},
        }

        logger.info(f"📁 Found {len(files)} files to scan")
        progress_interval = max(1, len(files) // 20)  # Log progress every 5%
        
        for i, fpath in enumerate(files, 1):
            parse_result = self._parse_file(str(fpath))
            if parse_result:
                results['indexed'] += 1
                results['entities_found'] += len(parse_result.entities)
                for e in parse_result.entities:
                    results['by_type'][e.entity_type] = results['by_type'].get(e.entity_type, 0) + 1
                self._known_hashes[str(fpath)] = parse_result.file_hash
                # Persist if session provided
                if db_session:
                    self._persist_parse(db_session, parse_result, workspace_path)
            else:
                results['skipped'] += 1
            
            # Progress logging every 5% or every 50 files (whichever is smaller)
            if i % min(progress_interval, 50) == 0 or i == len(files):
                pct = (i / len(files)) * 100
                logger.info(f"   ⏳ Scanning: {i}/{len(files)} files ({pct:.0f}%) - {results['entities_found']} entities found")

        if db_session:
            db_session.commit()

        return results

    def incremental_update(self, file_path: str, workspace_path: str, db_session=None) -> Optional[FileParseResult]:
        """Re-index a single file if its hash changed. Returns None if unchanged."""
        current_hash = _file_hash(file_path)
        if not current_hash:
            return None

        old_hash = self._known_hashes.get(file_path, '')
        if current_hash == old_hash:
            return None  # File unchanged

        parse_result = self._parse_file(file_path)
        if parse_result:
            self._known_hashes[file_path] = parse_result.file_hash
            if db_session:
                self._persist_parse(db_session, parse_result, workspace_path)
                db_session.commit()

        return parse_result

    def get_entities(self, workspace_path: str, entity_type: str = None,
                     db_session=None) -> List[Dict[str, Any]]:
        """Query stored entities, optionally filtered by type."""
        if not db_session:
            return []

        from models import EntityIndex, Workspace
        ws = db_session.query(Workspace).filter(Workspace.path == workspace_path).first()
        if not ws:
            return []

        q = db_session.query(EntityIndex).filter(EntityIndex.workspace_id == ws.id)
        if entity_type:
            q = q.filter(EntityIndex.entity_type == entity_type)

        return [{
            'file_path': e.file_path,
            'entity_type': e.entity_type,
            'entity_name': e.entity_name,
            'line_start': e.line_start,
            'line_end': e.line_end,
            'signature': e.signature,
            'metadata': e.extra_info or {},
        } for e in q.all()]

    def get_file_entities(self, file_path: str, db_session=None) -> List[Dict[str, Any]]:
        """Get all entities in a specific file."""
        if not db_session:
            parse_result = self._parse_file(file_path)
            if not parse_result:
                return []
            return [{
                'entity_type': e.entity_type,
                'entity_name': e.entity_name,
                'line_start': e.line_start,
                'line_end': e.line_end,
                'signature': e.signature,
                'metadata': e.metadata,
            } for e in parse_result.entities]

        from models import EntityIndex
        return [{
            'file_path': e.file_path,
            'entity_type': e.entity_type,
            'entity_name': e.entity_name,
            'line_start': e.line_start,
            'line_end': e.line_end,
            'signature': e.signature,
            'metadata': e.extra_info or {},
        } for e in db_session.query(EntityIndex).filter(EntityIndex.file_path == file_path).all()]

    def build_ast_snapshot(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Build a structured AST snapshot for drift detection."""
        parse_result = self._parse_file(file_path)
        if not parse_result:
            return None

        return {
            'file_path': file_path,
            'file_hash': parse_result.file_hash,
            'language': parse_result.language,
            'entities': [{
                'type': e.entity_type,
                'name': e.entity_name,
                'line_start': e.line_start,
                'line_end': e.line_end,
                'signature': e.signature,
                'metadata': e.metadata,
            } for e in parse_result.entities],
            'imports': parse_result.imports,
            'exports': parse_result.exports,
        }

    # ── Internal ──

    def _parse_file(self, file_path: str) -> Optional[FileParseResult]:
        try:
            content = Path(file_path).read_text(encoding='utf-8', errors='ignore')
        except Exception:
            return None

        lang = _detect_language(file_path)
        if lang == 'python':
            return self._py_extractor.extract(file_path, content)
        elif lang in ('typescript', 'javascript'):
            return self._ts_extractor.extract(file_path, content)
        elif lang in ('kotlin', 'java'):
            return self._kt_extractor.extract(file_path, content)
        return None

    def _walk_files(self, root: Path):
        for fpath in root.rglob('*'):
            if fpath.is_dir():
                continue
            if any(skip in fpath.parts for skip in SKIP_DIRS):
                continue
            if fpath.suffix.lower() in CODE_EXTENSIONS:
                yield fpath

    def _persist_parse(self, db_session, parse_result: FileParseResult, workspace_path: str):
        """Upsert parsed entities into DB."""
        from models import EntityIndex, Workspace

        ws = db_session.query(Workspace).filter(Workspace.path == workspace_path).first()
        if not ws:
            return

        # Delete old entities for this file
        db_session.query(EntityIndex).filter(
            EntityIndex.workspace_id == ws.id,
            EntityIndex.file_path == parse_result.file_path,
        ).delete()

        # Insert new entities
        for entity in parse_result.entities:
            db_session.add(EntityIndex(
                workspace_id=ws.id,
                file_path=parse_result.file_path,
                file_hash=parse_result.file_hash,
                entity_type=entity.entity_type,
                entity_name=entity.entity_name,
                line_start=entity.line_start,
                line_end=entity.line_end,
                signature=entity.signature,
                extra_info=entity.metadata,
                last_parsed=datetime.now(timezone.utc),
            ))
