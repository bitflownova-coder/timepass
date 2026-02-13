"""
Copilot Engine - Dead Code Detector
Detects unused imports, functions, variables, and API endpoints.
"""
import ast
import os
import re
from pathlib import Path
from typing import Optional
from collections import defaultdict


class DeadCodeDetector:
    """Detects dead code: unused imports, functions, variables, and endpoints."""

    SKIP_DIRS = {
        'node_modules', '.git', '__pycache__', '.venv', 'venv',
        'env', 'dist', 'build', '.next', '.cache', 'site-packages',
    }
    
    # Common framework entry points that are called externally
    FRAMEWORK_ENTRY_POINTS = {
        # Django
        'get', 'post', 'put', 'delete', 'patch', 'head', 'options',
        'setUp', 'tearDown', 'setUpClass', 'tearDownClass',
        '__init__', '__str__', '__repr__', '__enter__', '__exit__',
        '__call__', '__getitem__', '__setitem__', '__len__',
        # Flask/FastAPI decorators mark these as used
        'index', 'home', 'login', 'logout', 'register',
        # Pytest
        'test_', 'fixture',
    }
    
    # Names that are typically exported/used externally
    EXPORTED_PATTERNS = [
        r'^[A-Z][A-Z_]+$',  # Constants like MAX_SIZE
        r'^[A-Z][a-zA-Z]+$',  # Classes like MyClass
        r'^__.*__$',  # Dunder methods
    ]

    def __init__(self):
        self.findings = []
        self.workspace_path = ""
        
        # Cross-file tracking
        self.all_imports = {}  # file -> list of imports
        self.all_functions = {}  # file -> {name: line}
        self.all_classes = {}  # file -> {name: line}
        self.all_calls = defaultdict(set)  # name -> set of files calling it
        self.all_api_endpoints = []  # list of {path, method, file, line}
        self.all_api_calls = []  # list of {url, method, file, line}

    def analyze_workspace(self, workspace_path: str, max_files: int = 500) -> dict:
        """Analyze entire workspace for dead code."""
        self.workspace_path = workspace_path
        self.findings = []
        
        # Reset tracking
        self.all_imports = {}
        self.all_functions = {}
        self.all_classes = {}
        self.all_calls = defaultdict(set)
        self.all_api_endpoints = []
        self.all_api_calls = []
        
        # Phase 1: Collect all definitions and usages
        files_analyzed = 0
        for root, dirs, files in os.walk(workspace_path):
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]
            
            for fname in files:
                if files_analyzed >= max_files:
                    break
                
                file_path = os.path.join(root, fname)
                ext = Path(fname).suffix.lower()
                
                if ext == '.py':
                    self._analyze_python_file(file_path)
                    files_analyzed += 1
                elif ext in ('.js', '.ts', '.jsx', '.tsx'):
                    self._analyze_js_file(file_path)
                    files_analyzed += 1
        
        # Phase 2: Find dead code
        self._detect_unused_imports()
        self._detect_unused_functions()
        self._detect_dead_endpoints()
        
        # Sort by severity
        severity_order = {'HIGH': 0, 'MEDIUM': 1, 'LOW': 2, 'INFO': 3}
        self.findings.sort(key=lambda f: (severity_order.get(f['severity'], 99), f['file']))
        
        return {
            'workspace': workspace_path,
            'total_findings': len(self.findings),
            'summary': {
                'unused_imports': sum(1 for f in self.findings if f['category'] == 'unused_import'),
                'unused_functions': sum(1 for f in self.findings if f['category'] == 'unused_function'),
                'dead_endpoints': sum(1 for f in self.findings if f['category'] == 'dead_endpoint'),
            },
            'findings': self.findings,
        }

    def _analyze_python_file(self, file_path: str):
        """Analyze Python file for definitions and usages."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            tree = ast.parse(content)
        except (SyntaxError, Exception):
            return
        
        imports = []
        functions = {}
        classes = {}
        calls = set()
        
        # Collect imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imports.append({
                        'name': name,
                        'full_name': alias.name,
                        'line': node.lineno,
                        'used': False,
                    })
            
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    imports.append({
                        'name': name,
                        'full_name': f"{module}.{alias.name}",
                        'line': node.lineno,
                        'used': False,
                    })
            
            # Collect function definitions
            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                # Check for decorators that indicate usage
                is_decorated_endpoint = any(
                    isinstance(d, ast.Call) or isinstance(d, ast.Attribute)
                    for d in node.decorator_list
                )
                functions[node.name] = {
                    'line': node.lineno,
                    'is_endpoint': is_decorated_endpoint,
                    'decorators': [self._get_decorator_name(d) for d in node.decorator_list],
                }
                
                # Record API endpoints
                for deco in node.decorator_list:
                    endpoint_info = self._extract_endpoint_from_decorator(deco, file_path, node.lineno)
                    if endpoint_info:
                        self.all_api_endpoints.append(endpoint_info)
            
            # Collect class definitions
            elif isinstance(node, ast.ClassDef):
                classes[node.name] = {'line': node.lineno}
            
            # Collect function calls
            elif isinstance(node, ast.Call):
                call_name = self._get_call_name(node)
                if call_name:
                    calls.add(call_name)
                    self.all_calls[call_name].add(file_path)
            
            # Collect name references (for import usage)
            elif isinstance(node, ast.Name):
                calls.add(node.id)
                self.all_calls[node.id].add(file_path)
            
            elif isinstance(node, ast.Attribute):
                calls.add(node.attr)
                self.all_calls[node.attr].add(file_path)
        
        # Check import usage within this file
        for imp in imports:
            name_parts = imp['name'].split('.')
            if any(part in calls for part in name_parts):
                imp['used'] = True
            elif imp['full_name'].split('.')[-1] in calls:
                imp['used'] = True
        
        self.all_imports[file_path] = imports
        self.all_functions[file_path] = functions
        self.all_classes[file_path] = classes
        
        # Detect API calls (fetch/axios/requests)
        self._detect_api_calls(content, file_path)

    def _analyze_js_file(self, file_path: str):
        """Analyze JavaScript/TypeScript file (basic regex-based)."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            return
        
        imports = []
        functions = {}
        
        # Collect imports
        # import { foo } from 'bar'
        for match in re.finditer(r'import\s+\{([^}]+)\}\s+from\s+[\'"]([^\'"]+)[\'"]', content):
            names = [n.strip().split(' as ')[-1].strip() for n in match.group(1).split(',')]
            line = content[:match.start()].count('\n') + 1
            for name in names:
                if name:
                    imports.append({'name': name, 'line': line, 'used': False})
        
        # import foo from 'bar'
        for match in re.finditer(r'import\s+(\w+)\s+from\s+[\'"]([^\'"]+)[\'"]', content):
            name = match.group(1)
            line = content[:match.start()].count('\n') + 1
            imports.append({'name': name, 'line': line, 'used': False})
        
        # Collect function definitions
        for match in re.finditer(r'(?:function|const|let|var)\s+(\w+)\s*[=:]?\s*(?:async\s*)?\(?', content):
            name = match.group(1)
            line = content[:match.start()].count('\n') + 1
            functions[name] = {'line': line, 'is_endpoint': False}
        
        # Check usage
        for imp in imports:
            pattern = r'\b' + re.escape(imp['name']) + r'\b'
            occurrences = len(re.findall(pattern, content))
            if occurrences > 1:  # More than just the import
                imp['used'] = True
        
        self.all_imports[file_path] = imports
        self.all_functions[file_path] = functions
        
        # Detect API calls
        self._detect_api_calls(content, file_path)

    def _detect_api_calls(self, content: str, file_path: str):
        """Detect API calls in code."""
        lines = content.splitlines()
        
        # Python requests
        for match in re.finditer(r'requests\.(get|post|put|delete|patch)\s*\(\s*[\'"]([^\'"]+)[\'"]', content):
            line = content[:match.start()].count('\n') + 1
            self.all_api_calls.append({
                'method': match.group(1).upper(),
                'url': match.group(2),
                'file': file_path,
                'line': line,
            })
        
        # fetch() calls
        for match in re.finditer(r'fetch\s*\(\s*[\'"`]([^\'"]+)[\'"`](?:.*method:\s*[\'"](\w+)[\'"])?', content):
            line = content[:match.start()].count('\n') + 1
            self.all_api_calls.append({
                'method': (match.group(2) or 'GET').upper(),
                'url': match.group(1),
                'file': file_path,
                'line': line,
            })
        
        # axios calls
        for match in re.finditer(r'axios\.(get|post|put|delete|patch)\s*\(\s*[\'"]([^\'"]+)[\'"]', content):
            line = content[:match.start()].count('\n') + 1
            self.all_api_calls.append({
                'method': match.group(1).upper(),
                'url': match.group(2),
                'file': file_path,
                'line': line,
            })

    def _extract_endpoint_from_decorator(self, decorator, file_path: str, line: int) -> Optional[dict]:
        """Extract API endpoint info from decorator."""
        deco_name = self._get_decorator_name(decorator)
        
        # Flask/FastAPI style: @app.get('/path') or @router.post('/path')
        if isinstance(decorator, ast.Call):
            method_match = re.search(r'\.(get|post|put|delete|patch|options|head)$', deco_name, re.I)
            if method_match:
                method = method_match.group(1).upper()
                # Get path from first argument
                if decorator.args and isinstance(decorator.args[0], ast.Constant):
                    path = decorator.args[0].value
                    return {
                        'method': method,
                        'path': path,
                        'file': file_path,
                        'line': line,
                    }
            
            # @app.route('/path', methods=['GET', 'POST'])
            if 'route' in deco_name.lower():
                if decorator.args and isinstance(decorator.args[0], ast.Constant):
                    path = decorator.args[0].value
                    methods = ['GET']
                    for kw in decorator.keywords:
                        if kw.arg == 'methods' and isinstance(kw.value, ast.List):
                            methods = [
                                elt.value for elt in kw.value.elts 
                                if isinstance(elt, ast.Constant)
                            ]
                    for method in methods:
                        return {
                            'method': method.upper(),
                            'path': path,
                            'file': file_path,
                            'line': line,
                        }
        return None

    def _get_decorator_name(self, decorator) -> str:
        """Get decorator name."""
        if isinstance(decorator, ast.Name):
            return decorator.id
        elif isinstance(decorator, ast.Attribute):
            parts = []
            current = decorator
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return '.'.join(reversed(parts))
        elif isinstance(decorator, ast.Call):
            return self._get_decorator_name(decorator.func)
        return ""

    def _get_call_name(self, node: ast.Call) -> str:
        """Get function call name."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            return node.func.attr
        return ""

    def _detect_unused_imports(self):
        """Detect imports that are never used."""
        for file_path, imports in self.all_imports.items():
            for imp in imports:
                if not imp['used']:
                    # Skip __all__ style exports
                    if imp['name'].startswith('_'):
                        continue
                    
                    self.findings.append({
                        'file': file_path,
                        'line': imp['line'],
                        'severity': 'LOW',
                        'category': 'unused_import',
                        'issue': f"Unused import: {imp['name']}",
                        'suggestion': f"Remove unused import '{imp['name']}' or use it",
                    })

    def _detect_unused_functions(self):
        """Detect functions that are never called."""
        for file_path, functions in self.all_functions.items():
            for func_name, info in functions.items():
                # Skip framework entry points
                if func_name.lower() in self.FRAMEWORK_ENTRY_POINTS:
                    continue
                if any(func_name.startswith(p) for p in ['test_', '__']):
                    continue
                if any(re.match(p, func_name) for p in self.EXPORTED_PATTERNS):
                    continue
                
                # Skip decorated endpoints
                if info.get('is_endpoint'):
                    continue
                if any('route' in d.lower() or d.endswith(('get', 'post', 'put', 'delete', 'patch')) 
                       for d in info.get('decorators', [])):
                    continue
                
                # Check if called anywhere
                if func_name not in self.all_calls:
                    self.findings.append({
                        'file': file_path,
                        'line': info['line'],
                        'severity': 'MEDIUM',
                        'category': 'unused_function',
                        'issue': f"Function '{func_name}' appears to be unused",
                        'suggestion': f"Remove unused function or add caller",
                    })
                elif len(self.all_calls[func_name]) == 1 and file_path in self.all_calls[func_name]:
                    # Only called from its own file - might be internal helper
                    pass  # Could add INFO level warning

    def _detect_dead_endpoints(self):
        """Detect API endpoints that have no callers."""
        if not self.all_api_endpoints or not self.all_api_calls:
            return
        
        # Normalize endpoint paths
        defined_endpoints = set()
        endpoint_info = {}
        for ep in self.all_api_endpoints:
            key = f"{ep['method']} {ep['path']}"
            defined_endpoints.add(key)
            endpoint_info[key] = ep
        
        # Normalize called URLs
        called_endpoints = set()
        for call in self.all_api_calls:
            # Extract path from URL
            url = call['url']
            path = url.split('?')[0]  # Remove query string
            # Handle relative vs absolute URLs
            if '://' in path:
                path = '/' + '/'.join(path.split('/')[3:])
            key = f"{call['method']} {path}"
            called_endpoints.add(key)
        
        # Find dead endpoints
        for key in defined_endpoints:
            if key not in called_endpoints:
                ep = endpoint_info[key]
                self.findings.append({
                    'file': ep['file'],
                    'line': ep['line'],
                    'severity': 'INFO',
                    'category': 'dead_endpoint',
                    'issue': f"API endpoint '{key}' has no callers in codebase",
                    'suggestion': "Verify endpoint is needed or remove it",
                })
