"""
Context Builder - Builds structured prompts for AI assistants
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import re

from config import settings
from error_parser import ParsedError

logger = logging.getLogger(__name__)


@dataclass
class ProjectContext:
    """Project-level context"""
    name: str
    path: str
    language: str
    framework: Optional[str] = None
    package_manager: Optional[str] = None
    dependencies: Dict[str, str] = field(default_factory=dict)
    scripts: Dict[str, str] = field(default_factory=dict)


@dataclass
class FileContext:
    """Single file context"""
    path: str
    relative_path: str
    language: str
    content: Optional[str] = None
    imports: List[str] = field(default_factory=list)
    exports: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)


@dataclass
class DatabaseContext:
    """Database schema context"""
    db_type: str  # postgres, mysql, sqlite, mongodb
    tables: Dict[str, List[Dict]] = field(default_factory=dict)  # table -> columns
    relationships: List[Dict] = field(default_factory=list)


@dataclass
class ErrorContext:
    """Error context for debugging"""
    error: ParsedError
    code_context: Optional[str] = None
    related_code: Dict[str, str] = field(default_factory=dict)


@dataclass 
class BuiltContext:
    """Final built context for AI"""
    prompt: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    token_estimate: int = 0


class ContextBuilder:
    """Builds rich context for AI prompts"""
    
    # Language detection
    LANGUAGE_EXTENSIONS = {
        '.py': 'python',
        '.js': 'javascript', 
        '.ts': 'typescript',
        '.jsx': 'javascript',
        '.tsx': 'typescript',
        '.java': 'java',
        '.go': 'go',
        '.rs': 'rust',
        '.cpp': 'cpp',
        '.c': 'c',
        '.cs': 'csharp',
        '.rb': 'ruby',
        '.php': 'php',
        '.swift': 'swift',
        '.kt': 'kotlin',
    }
    
    # Framework detection patterns
    FRAMEWORK_PATTERNS = {
        'react': ['react', 'react-dom', 'useState', 'useEffect'],
        'vue': ['vue', 'createApp', 'defineComponent'],
        'angular': ['@angular/core', 'NgModule', 'Component'],
        'express': ['express', 'app.get', 'app.post'],
        'fastapi': ['fastapi', 'FastAPI', '@app.get'],
        'django': ['django', 'models.Model', 'views'],
        'flask': ['flask', 'Flask', '@app.route'],
        'spring': ['springframework', '@RestController'],
        'nextjs': ['next', 'getServerSideProps', 'getStaticProps'],
    }
    
    def __init__(self, workspace_path: str = None):
        self.workspace_path = Path(workspace_path) if workspace_path else None
    
    def detect_language(self, file_path: str) -> str:
        """Detect language from file extension"""
        ext = Path(file_path).suffix.lower()
        return self.LANGUAGE_EXTENSIONS.get(ext, 'unknown')
    
    def detect_framework(self, workspace_path: str) -> Optional[str]:
        """Detect framework from project files"""
        path = Path(workspace_path)
        
        # Check package.json
        pkg_json = path / 'package.json'
        if pkg_json.exists():
            try:
                pkg = json.loads(pkg_json.read_text())
                deps = {**pkg.get('dependencies', {}), **pkg.get('devDependencies', {})}
                
                for framework, patterns in self.FRAMEWORK_PATTERNS.items():
                    if any(p in deps for p in patterns):
                        return framework
            except Exception:
                pass
        
        # Check requirements.txt / pyproject.toml
        req_txt = path / 'requirements.txt'
        if req_txt.exists():
            try:
                content = req_txt.read_text().lower()
                for framework, patterns in self.FRAMEWORK_PATTERNS.items():
                    if any(p.lower() in content for p in patterns):
                        return framework
            except Exception:
                pass
        
        return None
    
    def get_project_context(self, workspace_path: str) -> ProjectContext:
        """Build project-level context"""
        path = Path(workspace_path)
        name = path.name
        
        # Detect primary language
        language = "unknown"
        framework = self.detect_framework(workspace_path)
        package_manager = None
        dependencies = {}
        scripts = {}
        
        # Check for Node.js project
        pkg_json = path / 'package.json'
        if pkg_json.exists():
            try:
                pkg = json.loads(pkg_json.read_text())
                language = "javascript"
                if (path / 'tsconfig.json').exists():
                    language = "typescript"
                dependencies = {**pkg.get('dependencies', {})}
                scripts = pkg.get('scripts', {})
                package_manager = "npm"
                if (path / 'yarn.lock').exists():
                    package_manager = "yarn"
                elif (path / 'pnpm-lock.yaml').exists():
                    package_manager = "pnpm"
            except Exception:
                pass
        
        # Check for Python project
        elif (path / 'requirements.txt').exists() or (path / 'pyproject.toml').exists():
            language = "python"
            package_manager = "pip"
            if (path / 'poetry.lock').exists():
                package_manager = "poetry"
        
        # Check for Go project
        elif (path / 'go.mod').exists():
            language = "go"
            package_manager = "go mod"
        
        # Check for Rust project
        elif (path / 'Cargo.toml').exists():
            language = "rust"
            package_manager = "cargo"
        
        return ProjectContext(
            name=name,
            path=str(path),
            language=language,
            framework=framework,
            package_manager=package_manager,
            dependencies=dependencies,
            scripts=scripts
        )
    
    def get_file_context(self, file_path: str, include_content: bool = True) -> FileContext:
        """Build file context"""
        path = Path(file_path)
        language = self.detect_language(file_path)
        
        relative_path = str(path)
        if self.workspace_path and path.is_relative_to(self.workspace_path):
            relative_path = str(path.relative_to(self.workspace_path))
        
        content = None
        imports = []
        exports = []
        functions = []
        classes = []
        
        if include_content and path.exists():
            try:
                content = path.read_text()
                imports, exports, functions, classes = self._extract_symbols(content, language)
            except Exception:
                pass
        
        return FileContext(
            path=str(path),
            relative_path=relative_path,
            language=language,
            content=content,
            imports=imports,
            exports=exports,
            functions=functions,
            classes=classes
        )
    
    def _extract_symbols(self, content: str, language: str) -> tuple:
        """Extract imports, exports, functions, classes from code"""
        imports = []
        exports = []
        functions = []
        classes = []
        
        if language == 'python':
            # Python imports
            imports = re.findall(r'^(?:from\s+(\S+)\s+)?import\s+(.+)$', content, re.MULTILINE)
            imports = [f"{i[0]}.{i[1]}" if i[0] else i[1] for i in imports]
            
            # Python functions
            functions = re.findall(r'^def\s+(\w+)\s*\(', content, re.MULTILINE)
            
            # Python classes
            classes = re.findall(r'^class\s+(\w+)', content, re.MULTILINE)
        
        elif language in ('javascript', 'typescript'):
            # JS/TS imports
            imports = re.findall(r"import\s+.*?from\s+['\"](.+?)['\"]", content)
            imports += re.findall(r"require\(['\"](.+?)['\"]\)", content)
            
            # JS/TS exports
            exports = re.findall(r"export\s+(?:default\s+)?(?:class|function|const|let|var)\s+(\w+)", content)
            
            # JS/TS functions
            functions = re.findall(r"(?:function|const|let|var)\s+(\w+)\s*(?:=\s*(?:async\s*)?\(|=\s*(?:async\s+)?function|\()", content)
            
            # JS/TS classes
            classes = re.findall(r"class\s+(\w+)", content)
        
        return imports[:20], exports[:20], functions[:30], classes[:20]
    
    def build_error_context(self, error: ParsedError, workspace_path: str = None) -> ErrorContext:
        """Build context for error debugging"""
        from error_parser import error_parser
        
        code_context = None
        related_code = {}
        
        if error.file_path and error.line_number:
            code_context = error_parser.get_context(error.file_path, error.line_number)
        
        # Get code from related files
        for file_path in error.related_files[:3]:
            try:
                path = Path(file_path)
                if path.exists():
                    related_code[file_path] = path.read_text()[:2000]  # First 2000 chars
            except Exception:
                pass
        
        return ErrorContext(
            error=error,
            code_context=code_context,
            related_code=related_code
        )
    
    def build_prompt(
        self,
        task: str,
        current_file: Optional[FileContext] = None,
        project: Optional[ProjectContext] = None,
        error: Optional[ErrorContext] = None,
        additional_files: List[FileContext] = None,
        db_schema: Optional[DatabaseContext] = None,
        custom_context: str = None
    ) -> BuiltContext:
        """Build a structured prompt for AI"""
        
        sections = []
        
        # Project context
        if project:
            sections.append(f"""## Project Information
- Name: {project.name}
- Language: {project.language}
- Framework: {project.framework or 'None detected'}
- Package Manager: {project.package_manager or 'Unknown'}""")
        
        # Current file
        if current_file:
            sections.append(f"""## Current File
- Path: {current_file.relative_path}
- Language: {current_file.language}

### Imports
{chr(10).join(f'- {i}' for i in current_file.imports[:10]) or 'None'}

### Code
```{current_file.language}
{current_file.content[:3000] if current_file.content else 'Content not available'}
```""")
        
        # Error context
        if error:
            sections.append(f"""## Error Information
- Type: {error.error.error_type}
- Message: {error.error.message}
- File: {error.error.file_path or 'Unknown'}
- Line: {error.error.line_number or 'Unknown'}

### Stack Trace
```
{error.error.raw_output[:1500]}
```

### Code at Error Location
```
{error.code_context or 'Not available'}
```

### Suggestions
{chr(10).join(f'- {s}' for s in error.error.suggestions) or 'None'}""")
        
        # Additional files
        if additional_files:
            files_section = "## Related Files\n"
            for f in additional_files[:3]:
                files_section += f"""
### {f.relative_path}
```{f.language}
{f.content[:1500] if f.content else 'Content not available'}
```
"""
            sections.append(files_section)
        
        # Database schema
        if db_schema:
            tables_desc = []
            for table, columns in db_schema.tables.items():
                cols = ', '.join(f"{c['name']} ({c['type']})" for c in columns)
                tables_desc.append(f"- {table}: {cols}")
            
            sections.append(f"""## Database Schema
Type: {db_schema.db_type}

### Tables
{chr(10).join(tables_desc)}""")
        
        # Custom context
        if custom_context:
            sections.append(f"## Additional Context\n{custom_context}")
        
        # Task
        sections.append(f"## Task\n{task}")
        
        prompt = "\n\n".join(sections)
        
        # Estimate tokens (rough: ~4 chars per token)
        token_estimate = len(prompt) // 4
        
        # Truncate if needed
        if token_estimate > settings.max_prompt_tokens:
            ratio = settings.max_prompt_tokens / token_estimate
            prompt = prompt[:int(len(prompt) * ratio * 0.9)]
            token_estimate = settings.max_prompt_tokens
        
        return BuiltContext(
            prompt=prompt,
            metadata={
                'project': project.name if project else None,
                'current_file': current_file.relative_path if current_file else None,
                'has_error': error is not None,
                'timestamp': datetime.now(timezone.utc).isoformat()
            },
            token_estimate=token_estimate
        )
    
    def build_debug_prompt(self, error: ParsedError, workspace_path: str) -> BuiltContext:
        """Convenience method for debugging prompts"""
        project = self.get_project_context(workspace_path)
        error_ctx = self.build_error_context(error, workspace_path)
        
        current_file = None
        if error.file_path:
            current_file = self.get_file_context(error.file_path)
        
        additional_files = []
        for path in error.related_files[:2]:
            if path != error.file_path:
                additional_files.append(self.get_file_context(path))
        
        return self.build_prompt(
            task="Debug this error and suggest a fix. Explain the root cause and provide corrected code.",
            current_file=current_file,
            project=project,
            error=error_ctx,
            additional_files=additional_files
        )


# Global context builder
context_builder = ContextBuilder()
