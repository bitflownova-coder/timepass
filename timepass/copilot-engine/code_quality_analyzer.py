"""
Copilot Engine - Code Quality Analyzer
Detects code quality issues: complexity, function length, nesting depth,
missing error handling, code smells, and more.
"""
import ast
import os
import re
from pathlib import Path
from typing import Optional


class CodeQualityAnalyzer:
    """Analyzes code for quality issues and maintainability problems."""

    SKIP_DIRS = {
        'node_modules', '.git', '__pycache__', '.venv', 'venv',
        'env', 'dist', 'build', '.next', '.cache', 'site-packages',
    }
    
    # Thresholds
    MAX_FUNCTION_LINES = 50
    MAX_PARAMETERS = 5
    MAX_NESTING_DEPTH = 4
    MAX_CYCLOMATIC_COMPLEXITY = 10
    MAX_RETURNS = 5
    MAX_BRANCHES = 10
    MAX_FILE_LINES = 500
    MAX_CLASS_METHODS = 20

    def __init__(self):
        self.findings = []
        self.workspace_path = ""
        self.metrics = {}

    def analyze_workspace(self, workspace_path: str, max_files: int = 500) -> dict:
        """Analyze workspace for code quality issues."""
        self.workspace_path = workspace_path
        self.findings = []
        self.metrics = {}
        
        files_analyzed = 0
        total_lines = 0
        total_functions = 0
        total_classes = 0
        
        for root, dirs, files in os.walk(workspace_path):
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]
            
            for fname in files:
                if files_analyzed >= max_files:
                    break
                
                file_path = os.path.join(root, fname)
                ext = Path(fname).suffix.lower()
                
                if ext == '.py':
                    file_metrics = self._analyze_python_file(file_path)
                    if file_metrics:
                        total_lines += file_metrics.get('lines', 0)
                        total_functions += file_metrics.get('function_count', 0)
                        total_classes += file_metrics.get('class_count', 0)
                    files_analyzed += 1
                elif ext in ('.js', '.ts', '.jsx', '.tsx'):
                    file_metrics = self._analyze_js_file(file_path)
                    if file_metrics:
                        total_lines += file_metrics.get('lines', 0)
                        total_functions += file_metrics.get('function_count', 0)
                    files_analyzed += 1
        
        # Sort by severity
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3, 'INFO': 4}
        self.findings.sort(key=lambda f: (severity_order.get(f['severity'], 99), f['file']))
        
        return {
            'workspace': workspace_path,
            'files_analyzed': files_analyzed,
            'total_findings': len(self.findings),
            'metrics': {
                'total_lines': total_lines,
                'total_functions': total_functions,
                'total_classes': total_classes,
            },
            'summary': {
                'high_complexity': sum(1 for f in self.findings if f['category'] == 'complexity'),
                'long_functions': sum(1 for f in self.findings if f['category'] == 'function_length'),
                'deep_nesting': sum(1 for f in self.findings if f['category'] == 'nesting_depth'),
                'many_parameters': sum(1 for f in self.findings if f['category'] == 'too_many_params'),
                'missing_error_handling': sum(1 for f in self.findings if f['category'] == 'error_handling'),
            },
            'findings': self.findings,
        }

    def _analyze_python_file(self, file_path: str) -> Optional[dict]:
        """Analyze Python file for quality issues."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.splitlines()
            tree = ast.parse(content)
        except (SyntaxError, Exception):
            return None
        
        file_metrics = {
            'lines': len(lines),
            'function_count': 0,
            'class_count': 0,
        }
        
        # Check file length
        if len(lines) > self.MAX_FILE_LINES:
            self.findings.append({
                'file': file_path,
                'line': 1,
                'severity': 'LOW',
                'category': 'file_length',
                'issue': f"File has {len(lines)} lines (exceeds {self.MAX_FILE_LINES})",
                'suggestion': "Consider splitting into smaller modules",
            })
        
        # Analyze functions and classes
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                file_metrics['function_count'] += 1
                self._analyze_python_function(node, file_path, lines)
            
            elif isinstance(node, ast.ClassDef):
                file_metrics['class_count'] += 1
                self._analyze_python_class(node, file_path)
        
        return file_metrics

    def _analyze_python_function(self, node, file_path: str, lines: list):
        """Analyze a Python function for quality issues."""
        func_name = node.name
        start_line = node.lineno
        end_line = node.end_lineno or start_line
        func_lines = end_line - start_line + 1
        
        # Function length
        if func_lines > self.MAX_FUNCTION_LINES:
            self.findings.append({
                'file': file_path,
                'line': start_line,
                'severity': 'MEDIUM',
                'category': 'function_length',
                'issue': f"Function '{func_name}' has {func_lines} lines (max: {self.MAX_FUNCTION_LINES})",
                'suggestion': "Break into smaller functions with single responsibilities",
            })
        
        # Parameter count
        args = node.args
        param_count = len(args.args) + len(args.kwonlyargs)
        if args.vararg:
            param_count += 1
        if args.kwarg:
            param_count += 1
        
        # Exclude 'self' and 'cls'
        if args.args and args.args[0].arg in ('self', 'cls'):
            param_count -= 1
        
        if param_count > self.MAX_PARAMETERS:
            self.findings.append({
                'file': file_path,
                'line': start_line,
                'severity': 'MEDIUM',
                'category': 'too_many_params',
                'issue': f"Function '{func_name}' has {param_count} parameters (max: {self.MAX_PARAMETERS})",
                'suggestion': "Use a data class or dict for grouped parameters",
            })
        
        # Cyclomatic complexity
        complexity = self._calculate_complexity(node)
        if complexity > self.MAX_CYCLOMATIC_COMPLEXITY:
            self.findings.append({
                'file': file_path,
                'line': start_line,
                'severity': 'HIGH',
                'category': 'complexity',
                'issue': f"Function '{func_name}' has complexity {complexity} (max: {self.MAX_CYCLOMATIC_COMPLEXITY})",
                'suggestion': "Simplify logic, extract helper functions, use early returns",
            })
        
        # Nesting depth
        max_depth = self._calculate_nesting_depth(node)
        if max_depth > self.MAX_NESTING_DEPTH:
            self.findings.append({
                'file': file_path,
                'line': start_line,
                'severity': 'MEDIUM',
                'category': 'nesting_depth',
                'issue': f"Function '{func_name}' has nesting depth {max_depth} (max: {self.MAX_NESTING_DEPTH})",
                'suggestion': "Use early returns, extract nested logic to functions",
            })
        
        # Missing error handling for risky operations
        self._check_missing_error_handling(node, file_path, func_name)
        
        # Multiple returns
        return_count = sum(1 for n in ast.walk(node) if isinstance(n, ast.Return))
        if return_count > self.MAX_RETURNS:
            self.findings.append({
                'file': file_path,
                'line': start_line,
                'severity': 'LOW',
                'category': 'multiple_returns',
                'issue': f"Function '{func_name}' has {return_count} return statements",
                'suggestion': "Consider restructuring to reduce exit points",
            })

    def _analyze_python_class(self, node: ast.ClassDef, file_path: str):
        """Analyze a Python class for quality issues."""
        class_name = node.name
        method_count = sum(1 for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))
        
        if method_count > self.MAX_CLASS_METHODS:
            self.findings.append({
                'file': file_path,
                'line': node.lineno,
                'severity': 'MEDIUM',
                'category': 'class_size',
                'issue': f"Class '{class_name}' has {method_count} methods (max: {self.MAX_CLASS_METHODS})",
                'suggestion': "Consider splitting into smaller classes (Single Responsibility)",
            })

    def _calculate_complexity(self, node) -> int:
        """Calculate cyclomatic complexity of a function."""
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            # Decision points
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.Assert):
                complexity += 1
            elif isinstance(child, ast.comprehension):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
            elif isinstance(child, ast.IfExp):  # Ternary
                complexity += 1
            elif isinstance(child, ast.Match):  # Python 3.10+
                complexity += 1
            elif isinstance(child, ast.match_case):
                complexity += 1
        
        return complexity

    def _calculate_nesting_depth(self, node, current_depth: int = 0) -> int:
        """Calculate maximum nesting depth in a function."""
        max_depth = current_depth
        
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.AsyncFor,
                                  ast.With, ast.AsyncWith, ast.Try)):
                child_depth = self._calculate_nesting_depth(child, current_depth + 1)
                max_depth = max(max_depth, child_depth)
            else:
                child_depth = self._calculate_nesting_depth(child, current_depth)
                max_depth = max(max_depth, child_depth)
        
        return max_depth

    def _check_missing_error_handling(self, node, file_path: str, func_name: str):
        """Check for risky operations without error handling."""
        risky_ops = {
            'open': 'File operations should be in try/except or use context manager',
            'json.load': 'JSON parsing can fail - wrap in try/except',
            'json.loads': 'JSON parsing can fail - wrap in try/except',
            'requests.get': 'HTTP requests can fail - handle exceptions',
            'requests.post': 'HTTP requests can fail - handle exceptions',
            'connect': 'Database connections can fail - handle exceptions',
            'execute': 'Database queries can fail - handle exceptions',
        }
        
        # Find operations in function
        has_try = any(isinstance(n, ast.Try) for n in ast.walk(node))
        has_context_manager = any(isinstance(n, (ast.With, ast.AsyncWith)) for n in ast.walk(node))
        
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                call_name = self._get_call_name(child)
                if call_name in risky_ops:
                    # Check if it's inside a try or with block
                    if not has_try and not has_context_manager:
                        self.findings.append({
                            'file': file_path,
                            'line': child.lineno,
                            'severity': 'MEDIUM',
                            'category': 'error_handling',
                            'issue': f"'{call_name}' without error handling in '{func_name}'",
                            'suggestion': risky_ops[call_name],
                        })
                        break  # One warning per function

    def _get_call_name(self, node: ast.Call) -> str:
        """Get function call name."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        elif isinstance(node.func, ast.Attribute):
            parts = []
            current = node.func
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
            return '.'.join(reversed(parts))
        return ""

    def _analyze_js_file(self, file_path: str) -> Optional[dict]:
        """Analyze JavaScript/TypeScript file for quality issues (regex-based)."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.splitlines()
        except Exception:
            return None
        
        file_metrics = {
            'lines': len(lines),
            'function_count': 0,
        }
        
        # File length check
        if len(lines) > self.MAX_FILE_LINES:
            self.findings.append({
                'file': file_path,
                'line': 1,
                'severity': 'LOW',
                'category': 'file_length',
                'issue': f"File has {len(lines)} lines (exceeds {self.MAX_FILE_LINES})",
                'suggestion': "Consider splitting into smaller modules",
            })
        
        # Find functions and analyze
        func_pattern = r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>|(?:async\s+)?(\w+)\s*\([^)]*\)\s*\{)'
        
        for match in re.finditer(r'(?:function\s+(\w+)\s*\(([^)]*)\)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\(([^)]*)\)\s*=>)', content):
            func_name = match.group(1) or match.group(3)
            params = match.group(2) or match.group(4) or ''
            line = content[:match.start()].count('\n') + 1
            
            file_metrics['function_count'] += 1
            
            # Parameter count
            if params.strip():
                param_count = len([p for p in params.split(',') if p.strip()])
                if param_count > self.MAX_PARAMETERS:
                    self.findings.append({
                        'file': file_path,
                        'line': line,
                        'severity': 'MEDIUM',
                        'category': 'too_many_params',
                        'issue': f"Function '{func_name}' has {param_count} parameters (max: {self.MAX_PARAMETERS})",
                        'suggestion': "Use an options object for grouped parameters",
                    })
        
        # Check for deep nesting (simple brace counting)
        self._check_js_nesting(file_path, lines)
        
        return file_metrics

    def _check_js_nesting(self, file_path: str, lines: list):
        """Check JavaScript for deep nesting using brace tracking."""
        max_depth = 0
        current_depth = 0
        max_depth_line = 1
        
        for i, line in enumerate(lines, 1):
            # Skip strings (very basic)
            code = re.sub(r'["\'][^"\']*["\']', '', line)
            code = re.sub(r'//.*$', '', code)
            
            opens = code.count('{')
            closes = code.count('}')
            
            current_depth += opens
            if current_depth > max_depth:
                max_depth = current_depth
                max_depth_line = i
            current_depth -= closes
            current_depth = max(0, current_depth)
        
        if max_depth > self.MAX_NESTING_DEPTH + 2:  # Allow some extra for JS (class/function wrapper)
            self.findings.append({
                'file': file_path,
                'line': max_depth_line,
                'severity': 'MEDIUM',
                'category': 'nesting_depth',
                'issue': f"Deep nesting detected (depth: {max_depth})",
                'suggestion': "Reduce nesting with early returns and extracted functions",
            })
