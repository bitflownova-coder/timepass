"""
Copilot Engine - Runtime Error Predictor
Predicts potential runtime errors: null access, bounds checks,
missing async/await, division by zero, type mismatches.
"""
import ast
import os
import re
from pathlib import Path
from typing import Optional, Set


class RuntimeErrorPredictor:
    """Predicts potential runtime errors through static analysis."""

    SKIP_DIRS = {
        'node_modules', '.git', '__pycache__', '.venv', 'venv',
        'env', 'dist', 'build', '.next', '.cache', 'site-packages',
    }

    def __init__(self):
        self.findings = []
        self.workspace_path = ""

    def analyze_workspace(self, workspace_path: str, max_files: int = 500) -> dict:
        """Analyze workspace for potential runtime errors."""
        self.workspace_path = workspace_path
        self.findings = []
        
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
        
        # Sort by severity
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        self.findings.sort(key=lambda f: (severity_order.get(f['severity'], 99), f['file']))
        
        return {
            'workspace': workspace_path,
            'files_analyzed': files_analyzed,
            'total_findings': len(self.findings),
            'summary': {
                'null_access': sum(1 for f in self.findings if f['category'] == 'null_access'),
                'bounds_check': sum(1 for f in self.findings if f['category'] == 'bounds_check'),
                'async_issues': sum(1 for f in self.findings if f['category'] == 'async_issues'),
                'division_zero': sum(1 for f in self.findings if f['category'] == 'division_zero'),
                'type_mismatch': sum(1 for f in self.findings if f['category'] == 'type_mismatch'),
            },
            'findings': self.findings,
        }

    def _analyze_python_file(self, file_path: str):
        """Analyze Python file for potential runtime errors."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.splitlines()
            tree = ast.parse(content)
        except (SyntaxError, Exception):
            return
        
        # Track variables that might be None
        possibly_none: Set[str] = set()
        awaited_vars: Set[str] = set()
        
        class ErrorPredictor(ast.NodeVisitor):
            def __init__(self, parent):
                self.parent = parent
                self.in_try = False
                self.checked_vars = set()  # Variables we've checked for None
            
            def visit_Assign(self, node):
                # Track assignments that might be None
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        var_name = target.id
                        
                        # Check if assigned from function that might return None
                        if isinstance(node.value, ast.Call):
                            call_name = self.parent._get_call_name(node.value)
                            # Common functions that return None/Optional
                            if call_name in ('get', 'find', 'search', 'match', 
                                           'dict.get', 're.search', 're.match',
                                           'list.pop', 'find_one', 'first'):
                                possibly_none.add(var_name)
                        
                        # result = await something
                        if isinstance(node.value, ast.Await):
                            awaited_vars.add(var_name)
                        
                        # x = y.get('key')
                        if isinstance(node.value, ast.Call):
                            if isinstance(node.value.func, ast.Attribute):
                                if node.value.func.attr == 'get':
                                    possibly_none.add(var_name)
                
                self.generic_visit(node)
            
            def visit_If(self, node):
                # Track None checks: if x is not None, if x:
                if isinstance(node.test, ast.Compare):
                    for comparator in node.test.comparators:
                        if isinstance(comparator, ast.Constant) and comparator.value is None:
                            if isinstance(node.test.left, ast.Name):
                                self.checked_vars.add(node.test.left.id)
                
                if isinstance(node.test, ast.Name):
                    self.checked_vars.add(node.test.id)
                
                self.generic_visit(node)
            
            def visit_Attribute(self, node):
                # Check for attribute access on possibly-None variable
                if isinstance(node.value, ast.Name):
                    var_name = node.value.id
                    if var_name in possibly_none and var_name not in self.checked_vars:
                        self.parent.findings.append({
                            'file': file_path,
                            'line': node.lineno,
                            'severity': 'MEDIUM',
                            'category': 'null_access',
                            'issue': f"Accessing '{node.attr}' on '{var_name}' which might be None",
                            'suggestion': f"Check if '{var_name}' is None before accessing attributes",
                        })
                
                self.generic_visit(node)
            
            def visit_Subscript(self, node):
                # Check for index access without bounds check
                if isinstance(node.slice, ast.Constant):
                    if isinstance(node.slice.value, int) and node.slice.value != 0:
                        # Accessing specific index > 0 without length check
                        if isinstance(node.value, ast.Name):
                            self.parent.findings.append({
                                'file': file_path,
                                'line': node.lineno,
                                'severity': 'LOW',
                                'category': 'bounds_check',
                                'issue': f"Index [{node.slice.value}] access without bounds check",
                                'suggestion': "Verify list/array length before accessing specific indices",
                            })
                
                self.generic_visit(node)
            
            def visit_BinOp(self, node):
                # Check for division by potential zero
                if isinstance(node.op, (ast.Div, ast.FloorDiv, ast.Mod)):
                    if isinstance(node.right, ast.Name):
                        # Division by variable - might be zero
                        self.parent.findings.append({
                            'file': file_path,
                            'line': node.lineno,
                            'severity': 'LOW',
                            'category': 'division_zero',
                            'issue': f"Division by '{node.right.id}' which might be zero",
                            'suggestion': "Check for zero before division or use try/except",
                        })
                    elif isinstance(node.right, ast.Constant) and node.right.value == 0:
                        self.parent.findings.append({
                            'file': file_path,
                            'line': node.lineno,
                            'severity': 'CRITICAL',
                            'category': 'division_zero',
                            'issue': "Division by zero - will raise ZeroDivisionError",
                            'suggestion': "Remove or guard against division by zero",
                        })
                
                self.generic_visit(node)
            
            def visit_Call(self, node):
                call_name = self.parent._get_call_name(node)
                
                # Check for missing await on async functions
                # This is detected by looking for coroutine results not being awaited
                
                # Check for list operations that might fail
                if call_name in ('list.remove', 'dict.pop', 'set.remove'):
                    self.parent.findings.append({
                        'file': file_path,
                        'line': node.lineno,
                        'severity': 'LOW',
                        'category': 'type_mismatch',
                        'issue': f"'{call_name}' raises KeyError/ValueError if element not found",
                        'suggestion': f"Use 'in' check first or use {call_name.split('.')[0]}.get/discard",
                    })
                
                # int() on potentially non-numeric string
                if call_name == 'int':
                    if node.args and isinstance(node.args[0], ast.Name):
                        self.parent.findings.append({
                            'file': file_path,
                            'line': node.lineno,
                            'severity': 'LOW',
                            'category': 'type_mismatch',
                            'issue': f"int() on variable might raise ValueError",
                            'suggestion': "Wrap in try/except or validate input first",
                        })
                
                self.generic_visit(node)
            
            def visit_Try(self, node):
                self.in_try = True
                self.generic_visit(node)
                self.in_try = False
        
        visitor = ErrorPredictor(self)
        visitor.visit(tree)

    def _analyze_js_file(self, file_path: str):
        """Analyze JavaScript/TypeScript file for potential runtime errors."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.splitlines()
        except Exception:
            return
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Skip comments
            if stripped.startswith('//') or stripped.startswith('/*'):
                continue
            
            # Potential null/undefined access patterns
            # obj.deeply.nested.value without optional chaining
            deep_access = re.search(r'(\w+)\.(\w+)\.(\w+)(?!\?)', line)
            if deep_access and '?.' not in line:
                # Check if there's a guard
                var = deep_access.group(1)
                if not re.search(rf'if\s*\(\s*{var}\s*[&|)]', '\n'.join(lines[max(0, i-3):i])):
                    self.findings.append({
                        'file': file_path,
                        'line': i,
                        'severity': 'LOW',
                        'category': 'null_access',
                        'issue': f"Deep property access '{deep_access.group(0)}' without null check",
                        'suggestion': "Use optional chaining (?.) or check for null/undefined",
                    })
            
            # Missing await on async function call
            # const result = asyncFunc() without await
            async_no_await = re.search(r'(?:const|let|var)\s+\w+\s*=\s*(?!await)(\w+)\s*\(', line)
            if async_no_await:
                func_name = async_no_await.group(1)
                # Look for async function definition
                if re.search(rf'async\s+(?:function\s+)?{func_name}', content):
                    self.findings.append({
                        'file': file_path,
                        'line': i,
                        'severity': 'MEDIUM',
                        'category': 'async_issues',
                        'issue': f"Async function '{func_name}' called without await",
                        'suggestion': "Add 'await' before the async function call",
                    })
            
            # .then() without .catch()
            if '.then(' in line and '.catch(' not in line:
                # Check next few lines
                next_lines = '\n'.join(lines[i:min(i+3, len(lines))])
                if '.catch(' not in next_lines:
                    self.findings.append({
                        'file': file_path,
                        'line': i,
                        'severity': 'MEDIUM',
                        'category': 'async_issues',
                        'issue': "Promise .then() without .catch() - unhandled rejection",
                        'suggestion': "Add .catch() or use try/catch with async/await",
                    })
            
            # Division by variable without check
            div_match = re.search(r'/\s*(\w+)(?!\s*[=>/])', line)
            if div_match and div_match.group(1) not in ('div', 'span', 'script', 'style', '2', '10', '100'):
                var = div_match.group(1)
                # Check if there's a guard  
                if not re.search(rf'{var}\s*(!==?|===?)\s*0', '\n'.join(lines[max(0, i-3):i+1])):
                    if var[0].islower():  # Likely a variable
                        self.findings.append({
                            'file': file_path,
                            'line': i,
                            'severity': 'LOW',
                            'category': 'division_zero',
                            'issue': f"Division by '{var}' without zero check",
                            'suggestion': "Check for zero before division",
                        })
            
            # Array index access without length check
            index_access = re.search(r'(\w+)\[(\d+)\]', line)
            if index_access:
                arr = index_access.group(1)
                idx = int(index_access.group(2))
                if idx > 0:  # [0] is usually safe
                    # Check for length check
                    if not re.search(rf'{arr}\.length', '\n'.join(lines[max(0, i-5):i])):
                        self.findings.append({
                            'file': file_path,
                            'line': i,
                            'severity': 'LOW',
                            'category': 'bounds_check',
                            'issue': f"Array access [{idx}] without length check",
                            'suggestion': f"Verify {arr}.length > {idx} before accessing",
                        })
            
            # JSON.parse without try/catch
            if 'JSON.parse(' in line:
                # Check if we're in a try block
                in_try = any('try' in lines[j] for j in range(max(0, i-10), i))
                if not in_try:
                    self.findings.append({
                        'file': file_path,
                        'line': i,
                        'severity': 'MEDIUM',
                        'category': 'type_mismatch',
                        'issue': "JSON.parse() without try/catch - may throw on invalid JSON",
                        'suggestion': "Wrap JSON.parse in try/catch block",
                    })
            
            # parseInt/parseFloat without validation
            parse_match = re.search(r'(?:parseInt|parseFloat)\s*\(\s*(\w+)', line)
            if parse_match:
                var = parse_match.group(1)
                if not re.search(r'isNaN|typeof', '\n'.join(lines[max(0, i-3):i+2])):
                    self.findings.append({
                        'file': file_path,
                        'line': i,
                        'severity': 'LOW',
                        'category': 'type_mismatch',
                        'issue': f"parseInt/parseFloat on '{var}' without NaN check",
                        'suggestion': "Check isNaN() after parsing or validate input type",
                    })

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
