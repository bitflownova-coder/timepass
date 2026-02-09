"""
Copilot Engine - Prompt Optimizer
Builds structured, optimized prompts for AI assistants with full project context.
Enhances the base context_builder with optimized templates and token management.
"""
import os
import json
from pathlib import Path
from typing import Optional


class PromptOptimizer:
    """Builds optimized prompts for AI code assistants."""

    # Token budget allocation (approximate)
    TOKEN_BUDGET = {
        'system_context': 200,
        'project_info': 300,
        'file_context': 500,
        'error_context': 400,
        'task_description': 200,
        'code_snippet': 1000,
        'related_files': 500,
        'conventions': 200,
    }

    PROMPT_TEMPLATES = {
        'debug': """## Debug Context

**Error**: {error_type}: {error_message}
**File**: {file_path}:{line_number}
**Language**: {language}

### Project Info
- Framework: {framework}
- Key dependencies: {dependencies}

### Code Context
```{language}
{code_context}
```

### Error Details
{error_details}

### Suggestions
{suggestions}

### Task
Fix this error. Explain the root cause and provide corrected code.""",

        'analyze': """## Code Analysis Context

**File**: {file_path}
**Language**: {language}
**Framework**: {framework}

### Project Structure
{project_structure}

### Code to Analyze
```{language}
{code_context}
```

### Task
{task}""",

        'improve': """## Code Improvement Context

**File**: {file_path}
**Language**: {language}

### Current Code
```{language}
{code_context}
```

### Conventions
{conventions}

### Task
{task}

Focus on: readability, performance, error handling, and best practices.""",

        'test': """## Test Generation Context

**File**: {file_path}
**Language**: {language}
**Framework**: {framework}

### Code Under Test
```{language}
{code_context}
```

### Existing Tests
{existing_tests}

### Task
Generate comprehensive unit tests covering:
1. Happy path
2. Edge cases
3. Error cases
4. Boundary conditions""",

        'general': """## Development Context

**Workspace**: {workspace_name}
**Language**: {language}
**Framework**: {framework}

### Project Structure
{project_structure}

### Current File
{file_path}
```{language}
{code_context}
```

### Task
{task}""",
    }

    def optimize(self, workspace_path: str, task: str,
                 current_file: Optional[str] = None,
                 error_text: Optional[str] = None,
                 code_snippet: Optional[str] = None) -> dict:
        """Build an optimized prompt with full context."""

        # Detect project info
        project_info = self._detect_project(workspace_path)

        # Determine template
        template_name = self._choose_template(task, error_text)
        template = self.PROMPT_TEMPLATES[template_name]

        # Build context parts
        context = {
            'workspace_name': os.path.basename(workspace_path),
            'language': project_info.get('language', 'unknown'),
            'framework': project_info.get('framework', 'N/A'),
            'dependencies': ', '.join(project_info.get('dependencies', [])[:10]),
            'file_path': current_file or 'N/A',
            'line_number': '',
            'error_type': '',
            'error_message': '',
            'error_details': '',
            'suggestions': '',
            'code_context': '',
            'project_structure': '',
            'task': task,
            'conventions': '',
            'existing_tests': 'No tests found',
        }

        # Add file context
        if current_file and os.path.isfile(current_file):
            context['code_context'] = self._read_file_context(current_file, code_snippet)

        # Add project structure
        context['project_structure'] = self._get_project_structure(workspace_path)

        # Add error context
        if error_text:
            error_info = self._parse_error_info(error_text)
            context.update(error_info)

        # Add conventions
        context['conventions'] = self._detect_conventions(workspace_path, project_info)

        # Build prompt
        try:
            prompt = template.format(**context)
        except KeyError:
            prompt = self.PROMPT_TEMPLATES['general'].format(**context)

        # Estimate tokens
        token_estimate = len(prompt.split()) * 1.3

        return {
            'prompt': prompt,
            'token_estimate': int(token_estimate),
            'template_used': template_name,
            'metadata': {
                'project': project_info.get('framework', project_info.get('language')),
                'current_file': current_file,
                'has_error': error_text is not None,
                'task': task[:100],
            },
        }

    def _choose_template(self, task: str, error_text: Optional[str]) -> str:
        """Choose the best prompt template based on context."""
        task_lower = task.lower()

        if error_text or 'fix' in task_lower or 'bug' in task_lower or 'error' in task_lower:
            return 'debug'
        elif 'test' in task_lower or 'spec' in task_lower:
            return 'test'
        elif 'improve' in task_lower or 'refactor' in task_lower or 'clean' in task_lower:
            return 'improve'
        elif 'analyze' in task_lower or 'review' in task_lower or 'audit' in task_lower:
            return 'analyze'
        else:
            return 'general'

    def _detect_project(self, workspace_path: str) -> dict:
        """Detect project language, framework, and dependencies."""
        info = {
            'language': 'unknown',
            'framework': None,
            'dependencies': [],
        }

        # Python project
        req_path = os.path.join(workspace_path, 'requirements.txt')
        if os.path.isfile(req_path):
            info['language'] = 'python'
            try:
                with open(req_path, 'r') as f:
                    deps = [l.strip().split('==')[0].split('>=')[0].split('<=')[0]
                            for l in f if l.strip() and not l.startswith('#')]
                    info['dependencies'] = deps[:20]

                    # Detect framework
                    dep_lower = [d.lower() for d in deps]
                    if 'fastapi' in dep_lower:
                        info['framework'] = 'FastAPI'
                    elif 'flask' in dep_lower:
                        info['framework'] = 'Flask'
                    elif 'django' in dep_lower:
                        info['framework'] = 'Django'
                    elif 'PyQt6' in deps or 'PyQt5' in deps:
                        info['framework'] = 'PyQt'
            except Exception:
                pass

        # Setup.py / pyproject.toml
        if os.path.isfile(os.path.join(workspace_path, 'pyproject.toml')):
            info['language'] = 'python'

        # Node.js project
        pkg_path = os.path.join(workspace_path, 'package.json')
        if os.path.isfile(pkg_path):
            info['language'] = 'javascript'
            try:
                with open(pkg_path, 'r') as f:
                    pkg = json.load(f)
                    all_deps = {}
                    all_deps.update(pkg.get('dependencies', {}))
                    all_deps.update(pkg.get('devDependencies', {}))
                    info['dependencies'] = list(all_deps.keys())[:20]

                    # Detect framework
                    if 'react' in all_deps:
                        info['framework'] = 'React'
                    if 'next' in all_deps:
                        info['framework'] = 'Next.js'
                    if 'vue' in all_deps:
                        info['framework'] = 'Vue.js'
                    if 'express' in all_deps:
                        info['framework'] = 'Express'
                    if '@nestjs/core' in all_deps:
                        info['framework'] = 'NestJS'

                    # Detect TypeScript
                    if 'typescript' in all_deps:
                        info['language'] = 'typescript'
            except Exception:
                pass

        # Go project
        if os.path.isfile(os.path.join(workspace_path, 'go.mod')):
            info['language'] = 'go'
            info['framework'] = 'Go'

        # Rust project
        if os.path.isfile(os.path.join(workspace_path, 'Cargo.toml')):
            info['language'] = 'rust'
            info['framework'] = 'Rust'

        # Java project
        if os.path.isfile(os.path.join(workspace_path, 'build.gradle')) or \
           os.path.isfile(os.path.join(workspace_path, 'build.gradle.kts')) or \
           os.path.isfile(os.path.join(workspace_path, 'pom.xml')):
            info['language'] = 'java'

        return info

    def _read_file_context(self, file_path: str, snippet: Optional[str] = None) -> str:
        """Read relevant code context from a file."""
        if snippet:
            return snippet

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # Limit to ~500 lines or ~15KB
            lines = content.split('\n')
            if len(lines) > 500:
                # Take first 200 and last 200
                lines = lines[:200] + [f'\n... ({len(lines) - 400} lines omitted) ...\n'] + lines[-200:]

            return '\n'.join(lines)[:15000]
        except Exception:
            return '# Could not read file'

    def _get_project_structure(self, workspace_path: str, max_depth: int = 3) -> str:
        """Get a concise project structure listing."""
        lines = []
        skip_dirs = {'node_modules', '.git', '__pycache__', '.venv', 'venv',
                     'dist', 'build', '.next', '.cache', 'target', '.mypy_cache',
                     '.pytest_cache', '.tox', 'env', 'vendor', '.gradle'}

        def walk(path: str, prefix: str = '', depth: int = 0):
            if depth >= max_depth:
                return
            try:
                entries = sorted(os.listdir(path))
            except PermissionError:
                return

            dirs = [e for e in entries if os.path.isdir(os.path.join(path, e)) and e not in skip_dirs and not e.startswith('.')]
            files = [e for e in entries if os.path.isfile(os.path.join(path, e)) and not e.startswith('.')]

            # Show up to 15 files per dir
            for f in files[:15]:
                lines.append(f'{prefix}{f}')
            if len(files) > 15:
                lines.append(f'{prefix}... ({len(files) - 15} more files)')

            for d in dirs[:10]:
                lines.append(f'{prefix}{d}/')
                walk(os.path.join(path, d), prefix + '  ', depth + 1)

        walk(workspace_path)
        return '\n'.join(lines[:60])

    def _parse_error_info(self, error_text: str) -> dict:
        """Parse error text for template variables."""
        import re

        info = {
            'error_type': 'Error',
            'error_message': error_text[:200],
            'error_details': error_text,
        }

        # Extract error type
        type_match = re.search(r'(\w+Error|\w+Exception|\w+Warning)', error_text)
        if type_match:
            info['error_type'] = type_match.group(1)

        # Extract file and line
        file_match = re.search(r'(?:File\s+["\']|at\s+)([^"\':\s]+)', error_text)
        if file_match:
            info['file_path'] = file_match.group(1)

        line_match = re.search(r'line\s+(\d+)', error_text, re.IGNORECASE)
        if line_match:
            info['line_number'] = line_match.group(1)

        # Extract message
        msg_match = re.search(r'(?:Error|Exception):\s*(.+?)(?:\n|$)', error_text)
        if msg_match:
            info['error_message'] = msg_match.group(1).strip()

        # Build suggestions based on known patterns
        suggestions = []
        if 'ImportError' in error_text or 'ModuleNotFoundError' in error_text:
            suggestions.append('Install the missing package or check import path')
        if 'TypeError' in error_text:
            suggestions.append('Check argument types and function signatures')
        if 'AttributeError' in error_text:
            suggestions.append('Verify the object type and attribute exists')
        if 'KeyError' in error_text:
            suggestions.append('Use .get() with default or check key exists first')
        if 'NameError' in error_text:
            suggestions.append('Check variable is defined before use or fix typo')
        if 'IndexError' in error_text:
            suggestions.append('Check list length before accessing index')
        if 'SyntaxError' in error_text:
            suggestions.append('Fix syntax: check brackets, colons, indentation')

        info['suggestions'] = '\n'.join(f'- {s}' for s in suggestions) if suggestions else 'No automatic suggestions'

        return info

    def _detect_conventions(self, workspace_path: str, project_info: dict) -> str:
        """Detect project coding conventions."""
        conventions = []

        # Check for linting configs
        config_files = {
            '.eslintrc': 'ESLint (JavaScript/TypeScript linting)',
            '.eslintrc.js': 'ESLint',
            '.eslintrc.json': 'ESLint',
            '.prettierrc': 'Prettier (code formatting)',
            '.prettierrc.json': 'Prettier',
            'prettier.config.js': 'Prettier',
            '.flake8': 'Flake8 (Python linting)',
            'setup.cfg': 'Python project config',
            'pyproject.toml': 'Python project config (PEP 518)',
            '.editorconfig': 'EditorConfig (indent/whitespace)',
            'tslint.json': 'TSLint (deprecated, use ESLint)',
            '.stylelintrc': 'Stylelint (CSS linting)',
            'biome.json': 'Biome (JS/TS formatter & linter)',
            'rustfmt.toml': 'Rustfmt (Rust formatting)',
            '.golangci.yml': 'GolangCI-Lint',
        }

        for filename, desc in config_files.items():
            if os.path.isfile(os.path.join(workspace_path, filename)):
                conventions.append(f'- {desc} configured')

        # Check for TypeScript
        if os.path.isfile(os.path.join(workspace_path, 'tsconfig.json')):
            conventions.append('- TypeScript with strict typing')

        if not conventions:
            conventions.append('- No specific conventions detected')

        return '\n'.join(conventions)
