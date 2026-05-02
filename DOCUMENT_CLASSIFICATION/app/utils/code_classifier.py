"""
Code Classifier — detect source-code files, their language, and the
project they belong to.

Used by the local indexer to keep code separate from business documents
and to populate the "Code Projects" virtual hierarchy.
"""
from __future__ import annotations

import os
import threading
from pathlib import Path

# ── Extension → language map ────────────────────────────────────────────────
CODE_EXTENSIONS: dict[str, str] = {
    # Python
    '.py': 'Python', '.pyw': 'Python', '.pyi': 'Python',
    # JavaScript / TypeScript
    '.js': 'JavaScript', '.jsx': 'JavaScript', '.mjs': 'JavaScript', '.cjs': 'JavaScript',
    '.ts': 'TypeScript', '.tsx': 'TypeScript',
    # Web frontend
    '.vue': 'Vue', '.svelte': 'Svelte',
    '.html': 'HTML', '.htm': 'HTML',
    '.css': 'CSS', '.scss': 'CSS', '.sass': 'CSS', '.less': 'CSS',
    # JVM
    '.java': 'Java', '.kt': 'Kotlin', '.kts': 'Kotlin',
    '.scala': 'Scala', '.groovy': 'Groovy',
    # Native / systems
    '.c': 'C', '.h': 'C',
    '.cpp': 'C++', '.cc': 'C++', '.cxx': 'C++', '.hpp': 'C++', '.hh': 'C++',
    '.rs': 'Rust', '.go': 'Go', '.zig': 'Zig',
    # .NET
    '.cs': 'C#', '.fs': 'F#', '.vb': 'VisualBasic',
    # Mobile
    '.swift': 'Swift', '.m': 'Objective-C', '.mm': 'Objective-C',
    '.dart': 'Dart',
    # Scripting
    '.rb': 'Ruby', '.php': 'PHP', '.pl': 'Perl', '.lua': 'Lua', '.r': 'R',
    '.sh': 'Shell', '.bash': 'Shell', '.zsh': 'Shell',
    '.ps1': 'PowerShell', '.bat': 'Batch', '.cmd': 'Batch',
    # Data / config
    '.sql': 'SQL', '.json': 'Config', '.yaml': 'Config', '.yml': 'Config',
    '.toml': 'Config', '.ini': 'Config', '.xml': 'Config', '.env': 'Config',
    # Docs in code repos
    '.md': 'Markdown', '.rst': 'Markdown',
    # Build / infra
    '.gradle': 'Build', '.cmake': 'Build', '.mk': 'Build',
}

# Filenames that mark a directory as a project root
PROJECT_MARKER_FILES: set[str] = {
    '.git', 'package.json', 'requirements.txt', 'pyproject.toml',
    'setup.py', 'setup.cfg', 'Pipfile',
    'pom.xml', 'build.gradle', 'build.gradle.kts',
    'Cargo.toml', 'go.mod', 'composer.json', 'Gemfile',
    'mix.exs', 'pubspec.yaml', 'project.clj',
    'Makefile', 'CMakeLists.txt', 'meson.build',
    'Dockerfile',
}

# Filenames matched by suffix to detect projects (e.g. *.csproj, *.sln)
PROJECT_MARKER_SUFFIXES: tuple[str, ...] = (
    '.csproj', '.sln', '.fsproj', '.vbproj', '.vcxproj', '.xcodeproj',
)

# Files we never index (lockfiles, minified bundles, source maps)
SKIP_NAMES: set[str] = {
    'package-lock.json', 'yarn.lock', 'pnpm-lock.yaml',
    'poetry.lock', 'Pipfile.lock', 'composer.lock',
    'Gemfile.lock', 'Cargo.lock', 'go.sum',
}
SKIP_SUFFIXES: tuple[str, ...] = (
    '.min.js', '.min.css', '.bundle.js', '.bundle.css',
    '.map', '.lock',
)

# Files larger than this don't get their body extracted (still indexed by name)
MAX_CODE_BYTES: int = 500_000

# ── Caches (thread-safe; populated during a scan) ──────────────────────────
_root_cache: dict[str, str | None] = {}
_root_lock = threading.Lock()


def is_code_file(file_path: str) -> bool:
    """Return True if the file looks like source code we should index."""
    p = Path(file_path)
    name = p.name
    if name in SKIP_NAMES:
        return False
    lname = name.lower()
    for suf in SKIP_SUFFIXES:
        if lname.endswith(suf):
            return False
    # Extension match
    ext = p.suffix.lower()
    if ext in CODE_EXTENSIONS:
        return True
    # Special-case Dockerfile (no extension)
    if name == 'Dockerfile' or lname.startswith('dockerfile.'):
        return True
    return False


def detect_language(file_path: str) -> str:
    """Return human-readable language label for a code file."""
    p = Path(file_path)
    if p.name == 'Dockerfile' or p.name.lower().startswith('dockerfile.'):
        return 'Docker'
    return CODE_EXTENSIONS.get(p.suffix.lower(), 'Other')


def detect_project_root(file_path: str, max_levels: int = 12) -> Path | None:
    """
    Walk up parent directories looking for a project marker
    (.git/, package.json, pom.xml, etc.).

    Result is cached per parent-directory string so a project with
    thousands of files only triggers a few real FS lookups.
    """
    p = Path(file_path).parent
    # Try cache first
    key = str(p)
    with _root_lock:
        if key in _root_cache:
            cached = _root_cache[key]
            return Path(cached) if cached else None

    # Walk ancestors
    cur = p
    found: Path | None = None
    levels = 0
    while cur and levels < max_levels:
        try:
            entries = set(os.listdir(cur))
        except (OSError, PermissionError):
            break
        # Direct marker file/dir match
        if entries & PROJECT_MARKER_FILES:
            found = cur
            break
        # Suffix-based markers (csproj, sln…)
        if any(any(name.endswith(suf) for suf in PROJECT_MARKER_SUFFIXES)
               for name in entries):
            found = cur
            break
        parent = cur.parent
        if parent == cur:
            break
        cur = parent
        levels += 1

    # Cache decision (also cache None so we don't re-walk for misses)
    with _root_lock:
        _root_cache[key] = str(found) if found else None
    return found


def project_info(file_path: str) -> tuple[str, str | None]:
    """
    Return (project_name, project_root_str) for a code file.

    If no marker is found anywhere up the tree, fall back to using
    the immediate parent directory name as the project name.
    """
    root = detect_project_root(file_path)
    if root is not None:
        return root.name, str(root)
    parent = Path(file_path).parent
    return parent.name or 'Misc', str(parent)


def should_skip_dir(dirname: str) -> bool:
    """
    Directories to never descend into during a scan.
    Caller still applies its own SKIP set; this is the code-specific addition.
    """
    return dirname in {
        'node_modules', '.git', 'dist', 'build', 'target',
        '__pycache__', '.venv', 'venv', 'env',
        'vendor', '.next', '.nuxt', '.gradle', '.mvn',
        'bin', 'obj', 'out', '.idea', '.vscode',
        '.pytest_cache', '.mypy_cache', '.ruff_cache',
        '.cache', '.terraform', '.serverless',
        'coverage', '.nyc_output',
    }


def read_code_text(file_path: str, max_bytes: int = MAX_CODE_BYTES) -> str:
    """Read source code as text. Returns '' if file too big or unreadable."""
    try:
        size = os.path.getsize(file_path)
        if size > max_bytes:
            return ''
        for enc in ('utf-8', 'latin-1', 'cp1252'):
            try:
                with open(file_path, 'r', encoding=enc) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
    except Exception:
        pass
    return ''


def reset_cache() -> None:
    """Clear the project-root cache (call at the start of each full scan)."""
    with _root_lock:
        _root_cache.clear()
