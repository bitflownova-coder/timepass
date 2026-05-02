"""
Copilot Engine - AST-Based Security Scanner
Uses Abstract Syntax Tree parsing to reduce false positives by 
analyzing actual code nodes instead of raw text patterns.
"""
import ast
import os
import re
from pathlib import Path
from typing import Optional


class ASTSecurityScanner:
    """AST-aware security scanner with reduced false positives."""

    # File patterns to treat differently
    TEST_PATTERNS = [
        r'test_.*\.py$', r'.*_test\.py$', r'tests?[/\\]', r'spec[/\\]',
        r'\.test\.(js|ts|jsx|tsx)$', r'\.spec\.(js|ts|jsx|tsx)$',
        r'__tests__[/\\]', r'fixtures?[/\\]', r'mocks?[/\\]',
    ]
    
    # Files that define security patterns (should be ignored for pattern matches)
    SCANNER_PATTERNS = [
        r'scanner', r'detector', r'analyzer', r'validator',
        r'rules?\.py$', r'patterns?\.py$', r'config.*security',
    ]
    
    # Directories to skip
    SKIP_DIRS = {
        'node_modules', '.git', '__pycache__', '.venv', 'venv',
        'env', '.env', 'dist', 'build', '.next', '.cache',
        'site-packages', '.tox', '.mypy_cache', '.pytest_cache',
        'target', 'vendor', 'bin', 'obj',
    }
    
    # Scannable extensions
    SCANNABLE_EXTENSIONS = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go',
        '.rs', '.rb', '.php', '.cs', '.yaml', '.yml', '.json',
    }

    def __init__(self):
        self.findings = []
        self.current_file = ""
        self.is_test_file = False
        self.is_scanner_file = False
        self.lines = []
        
    def _is_test_file(self, file_path: str) -> bool:
        """Check if file is a test file."""
        path_lower = file_path.lower().replace('\\', '/')
        return any(re.search(p, path_lower) for p in self.TEST_PATTERNS)
    
    def _is_scanner_file(self, file_path: str) -> bool:
        """Check if file defines security patterns (to avoid self-flagging)."""
        path_lower = file_path.lower().replace('\\', '/')
        return any(re.search(p, path_lower) for p in self.SCANNER_PATTERNS)
    
    def _add_finding(self, line: int, severity: str, category: str, 
                     issue: str, suggestion: str = "", code: str = ""):
        """Add a finding with test file awareness."""
        # Lower severity for test files
        actual_severity = severity
        if self.is_test_file:
            if severity == 'CRITICAL':
                actual_severity = 'LOW'
            elif severity == 'HIGH':
                actual_severity = 'LOW'
            elif severity == 'MEDIUM':
                actual_severity = 'LOW'
            issue = f"[TEST] {issue}"
        
        self.findings.append({
            'file': self.current_file,
            'line': line,
            'column': 0,
            'severity': actual_severity,
            'category': category,
            'issue': issue,
            'suggestion': suggestion or self._get_suggestion(category),
            'code': code[:120] if code else "",
            'is_test': self.is_test_file,
        })
    
    def scan_file(self, file_path: str) -> list[dict]:
        """Scan a file using AST when possible, fallback to smart regex."""
        if not os.path.isfile(file_path):
            return []
        
        ext = Path(file_path).suffix.lower()
        if ext not in self.SCANNABLE_EXTENSIONS:
            return []
        
        self.findings = []
        self.current_file = file_path
        self.is_test_file = self._is_test_file(file_path)
        self.is_scanner_file = self._is_scanner_file(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                self.lines = content.splitlines()
        except Exception:
            return []
        
        # Use AST for Python files
        if ext == '.py':
            self._scan_python_ast(content)
        else:
            # Smart regex for other files
            self._scan_with_smart_regex(content)
        
        return self.findings
    
    def _scan_python_ast(self, content: str):
        """Scan Python using AST for accurate detection."""
        try:
            tree = ast.parse(content)
        except SyntaxError:
            # Fallback to regex if AST fails
            self._scan_with_smart_regex(content)
            return
        
        # Walk all nodes
        for node in ast.walk(tree):
            self._check_python_node(node)
    
    def _check_python_node(self, node):
        """Check individual AST node for security issues."""
        line = getattr(node, 'lineno', 0)
        code = self.lines[line - 1] if 0 < line <= len(self.lines) else ""
        
        # Skip if inside a string literal (docstring/comment context)
        # AST already handles this - we only get actual code nodes
        
        # Check for dangerous function calls
        if isinstance(node, ast.Call):
            func_name = self._get_call_name(node)
            
            # eval() and exec()
            if func_name == 'eval':
                self._add_finding(line, 'HIGH', 'dangerous_functions',
                    'Use of eval() - code injection risk',
                    'Use ast.literal_eval() for safe parsing or avoid eval entirely',
                    code)
            elif func_name == 'exec':
                self._add_finding(line, 'HIGH', 'dangerous_functions',
                    'Use of exec() - code injection risk',
                    'Avoid exec() - use safer alternatives like importlib',
                    code)
            
            # Dangerous os functions
            elif func_name in ('os.system', 'os.popen'):
                self._add_finding(line, 'HIGH', 'dangerous_functions',
                    f'{func_name}() - shell injection risk',
                    'Use subprocess with shell=False instead',
                    code)
            
            # subprocess with shell=True
            elif func_name.startswith('subprocess.'):
                for keyword in getattr(node, 'keywords', []):
                    if keyword.arg == 'shell':
                        if isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
                            self._add_finding(line, 'HIGH', 'dangerous_functions',
                                'subprocess with shell=True - injection risk',
                                'Use shell=False and pass arguments as a list',
                                code)
            
            # Unsafe deserialization
            elif func_name in ('pickle.load', 'pickle.loads', 'marshal.load', 'marshal.loads'):
                self._add_finding(line, 'HIGH', 'dangerous_functions',
                    f'{func_name}() - unsafe deserialization',
                    'Avoid pickle/marshal with untrusted data - use JSON instead',
                    code)
            
            # yaml.load without safe loader
            elif func_name == 'yaml.load':
                has_loader = any(kw.arg == 'Loader' for kw in getattr(node, 'keywords', []))
                if not has_loader:
                    self._add_finding(line, 'HIGH', 'dangerous_functions',
                        'yaml.load() without safe Loader',
                        'Use yaml.safe_load() or specify Loader=yaml.SafeLoader',
                        code)
        
        # Check for hardcoded secrets in assignments
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    var_name = target.id.lower()
                    if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                        value = node.value.value
                        
                        # Check for secret-like variable names with string values
                        if any(secret in var_name for secret in ['password', 'passwd', 'pwd', 'secret', 
                                'api_key', 'apikey', 'token', 'auth', 'credential']):
                            if len(value) >= 4 and not value.startswith('${') and value not in ('', 'None', 'null', 'undefined'):
                                # Skip if it looks like an env var reference or placeholder
                                if not re.match(r'^(os\.environ|env\[|process\.env|<|{|\[)', value):
                                    self._add_finding(line, 'CRITICAL', 'hardcoded_secrets',
                                        f'Hardcoded {var_name} detected',
                                        'Use environment variables or a secrets manager',
                                        code)
                        
                        # Check for embedded private keys
                        if '-----BEGIN' in value and 'PRIVATE KEY' in value:
                            self._add_finding(line, 'CRITICAL', 'hardcoded_secrets',
                                'Embedded private key detected',
                                'Store private keys in secure files outside the repo',
                                code)
                        
                        # Check for API key patterns
                        if re.search(r'(ghp_|sk-|pk_live_|sk_live_)[A-Za-z0-9]{20,}', value):
                            self._add_finding(line, 'CRITICAL', 'hardcoded_secrets',
                                'API key pattern detected in string',
                                'Use environment variables or a secrets manager',
                                code)
        
        # Check for SQL injection in f-strings (context-aware)
        if isinstance(node, ast.JoinedStr):  # f-string
            fstring_text = self._reconstruct_fstring(node)
            # Only flag if it looks like actual SQL, not log messages
            # Must have SQL keyword AND pattern indicating it's a query
            sql_patterns = [
                r'\bSELECT\s+.+\s+FROM\b',  # SELECT ... FROM
                r'\bINSERT\s+INTO\b',        # INSERT INTO
                r'\bUPDATE\s+\w+\s+SET\b',   # UPDATE table SET
                r'\bDELETE\s+FROM\b',        # DELETE FROM
                r'\bDROP\s+(TABLE|DATABASE)\b',  # DROP TABLE/DATABASE
                r'\bCREATE\s+(TABLE|INDEX)\b',   # CREATE TABLE/INDEX
            ]
            upper_text = fstring_text.upper()
            if any(re.search(p, upper_text) for p in sql_patterns):
                # Extra check: skip if it looks like a log/error message
                skip_indicators = ['logger', 'log.', 'print(', 'error(', 'warning(', 'info(', 'debug(']
                if not any(ind in code.lower() for ind in skip_indicators):
                    self._add_finding(line, 'HIGH', 'sql_injection',
                        'SQL query in f-string - injection risk',
                        'Use parameterized queries with placeholders',
                        code)
        
        # Check for CORS wildcard
        if isinstance(node, ast.Call):
            func_name = self._get_call_name(node)
            if 'cors' in func_name.lower() or func_name == 'CORSMiddleware':
                for keyword in getattr(node, 'keywords', []):
                    if keyword.arg == 'allow_origins':
                        if isinstance(keyword.value, ast.List):
                            for elt in keyword.value.elts:
                                if isinstance(elt, ast.Constant) and elt.value == '*':
                                    self._add_finding(line, 'HIGH', 'auth_issues',
                                        'CORS allows all origins - security risk',
                                        'Specify explicit allowed origins',
                                        code)
        
        # Check for verify=False in requests
        if isinstance(node, ast.Call):
            for keyword in getattr(node, 'keywords', []):
                if keyword.arg == 'verify':
                    if isinstance(keyword.value, ast.Constant) and keyword.value.value is False:
                        self._add_finding(line, 'HIGH', 'auth_issues',
                            'SSL verification disabled',
                            'Enable SSL verification in production',
                            code)
        
        # Check for DEBUG=True
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in ('DEBUG', 'TESTING'):
                    if isinstance(node.value, ast.Constant) and node.value.value is True:
                        if not self.is_test_file:
                            self._add_finding(line, 'MEDIUM', 'auth_issues',
                                f'{target.id}=True in non-test file',
                                'Disable debug/testing mode in production',
                                code)
    
    def _get_call_name(self, node: ast.Call) -> str:
        """Get the full name of a function call."""
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
    
    def _reconstruct_fstring(self, node: ast.JoinedStr) -> str:
        """Reconstruct f-string content for analysis."""
        parts = []
        for value in node.values:
            if isinstance(value, ast.Constant):
                parts.append(str(value.value))
            elif isinstance(value, ast.FormattedValue):
                parts.append('{...}')  # Placeholder for variable
        return ''.join(parts)
    
    def _scan_with_smart_regex(self, content: str):
        """Smart regex scanning for non-Python files."""
        if self.is_scanner_file:
            # Skip most patterns for scanner files to avoid self-flagging
            self._scan_only_real_issues(content)
            return
        
        for i, line in enumerate(self.lines, 1):
            stripped = line.strip()
            
            # Skip obvious comments
            if stripped.startswith(('#', '//', '*', '/*', '*/')):
                continue
            
            # Skip string-only lines that look like patterns/docs
            if self._looks_like_pattern_definition(stripped):
                continue
            
            # Check for dangerous patterns
            self._check_line_patterns(i, line, stripped)
    
    def _looks_like_pattern_definition(self, line: str) -> bool:
        """Detect if line is defining a pattern rather than using it."""
        # Lines that define regex patterns or are pattern descriptions
        indicators = [
            r"^\s*\(r['\"]",  # (r'pattern'
            r"^\s*r['\"].*['\"],\s*$",  # r'pattern',
            r"pattern\s*=",  # pattern =
            r"^\s*#",  # comment
            r"^\s*['\"].*['\"],?\s*$",  # string-only line
            r"description|message|doc|comment",
        ]
        return any(re.search(p, line, re.IGNORECASE) for p in indicators)
    
    def _scan_only_real_issues(self, content: str):
        """Minimal scanning for scanner files - only definite issues."""
        for i, line in enumerate(self.lines, 1):
            # Only check for actual embedded secrets
            # Skip pattern definitions
            if 'r"' in line or "r'" in line or 'pattern' in line.lower():
                continue
            
            # Real private key embedded
            if '-----BEGIN' in line and 'PRIVATE KEY' in line:
                if 'r"' not in line and "r'" not in line:
                    self._add_finding(i, 'CRITICAL', 'hardcoded_secrets',
                        'Embedded private key', '', line)
    
    def _check_line_patterns(self, line_num: int, line: str, stripped: str):
        """Check line for security patterns."""
        code = stripped[:120]
        
        # innerHTML assignment (JavaScript/TypeScript)
        if re.search(r'\.innerHTML\s*=(?!\s*["\']<)', line):
            # Skip if it's a simple static string assignment
            if not re.search(r'\.innerHTML\s*=\s*["\'][^"\']*["\']', line):
                self._add_finding(line_num, 'HIGH', 'dangerous_functions',
                    'innerHTML with dynamic content - XSS risk',
                    'Use textContent or sanitize HTML', code)
        
        # document.write
        if re.search(r'document\.write\s*\(', line):
            self._add_finding(line_num, 'HIGH', 'dangerous_functions',
                'document.write() - security risk',
                'Use DOM manipulation methods instead', code)
        
        # dangerouslySetInnerHTML
        if 'dangerouslySetInnerHTML' in line and 'pattern' not in line.lower():
            self._add_finding(line_num, 'HIGH', 'dangerous_functions',
                'dangerouslySetInnerHTML - XSS risk',
                'Ensure HTML is sanitized or use safe alternatives', code)
        
        # SQL concatenation (non-Python) - require SQL structure patterns
        sql_concat = re.search(
            r'["\`].*?(SELECT\s+.+\s+FROM|INSERT\s+INTO|UPDATE\s+\w+\s+SET|DELETE\s+FROM).*?["\`]\s*\+|'
            r'\+\s*["\`].*?(SELECT\s+.+\s+FROM|INSERT\s+INTO|UPDATE\s+\w+\s+SET|DELETE\s+FROM)',
            line, re.IGNORECASE
        )
        if sql_concat and 'pattern' not in line.lower() and 'r"' not in line:
            # Skip if it's clearly a log message
            if not re.search(r'(log|error|warn|info|debug|console)\s*[\.(]', line.lower()):
                self._add_finding(line_num, 'HIGH', 'sql_injection',
                    'SQL query concatenation - injection risk',
                    'Use parameterized queries', code)
        
        # Template literal SQL - require full SQL pattern
        sql_template_pattern = re.search(
            r'`.*?(SELECT\s+.+\s+FROM|INSERT\s+INTO|UPDATE\s+\w+\s+SET|DELETE\s+FROM).*?\$\{',
            line, re.IGNORECASE
        )
        if sql_template_pattern:
            # Skip clear log/message patterns
            if not re.search(r'(log|error|warn|info|debug|console|message)\s*[\.(]', line.lower()):
                self._add_finding(line_num, 'HIGH', 'sql_injection',
                    'SQL in template literal - injection risk',
                    'Use parameterized queries', code)
    
    def _get_suggestion(self, category: str) -> str:
        """Get fix suggestion for a category."""
        suggestions = {
            'sql_injection': 'Use parameterized queries or an ORM',
            'hardcoded_secrets': 'Use environment variables or a secrets manager',
            'dangerous_functions': 'Use safer alternatives or validate inputs',
            'weak_crypto': 'Use SHA-256 for hashing, AES-256 for encryption',
            'auth_issues': 'Enable security features and strict configs',
            'information_disclosure': 'Remove sensitive data from logs',
        }
        return suggestions.get(category, 'Review and fix the security issue')
    
    def scan_workspace(self, workspace_path: str, max_files: int = 500) -> dict:
        """Scan entire workspace using AST-based analysis."""
        all_findings = []
        files_scanned = 0
        files_with_issues = set()
        
        for root, dirs, files in os.walk(workspace_path):
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]
            
            for fname in files:
                if files_scanned >= max_files:
                    break
                
                file_path = os.path.join(root, fname)
                ext = Path(fname).suffix.lower()
                
                if ext not in self.SCANNABLE_EXTENSIONS:
                    continue
                
                files_scanned += 1
                findings = self.scan_file(file_path)
                
                if findings:
                    files_with_issues.add(file_path)
                    all_findings.extend(findings)
        
        # Sort by severity
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
        all_findings.sort(key=lambda f: severity_order.get(f['severity'], 99))
        
        # Summary
        summary = {
            'critical': sum(1 for f in all_findings if f['severity'] == 'CRITICAL'),
            'high': sum(1 for f in all_findings if f['severity'] == 'HIGH'),
            'medium': sum(1 for f in all_findings if f['severity'] == 'MEDIUM'),
            'low': sum(1 for f in all_findings if f['severity'] == 'LOW'),
        }
        
        return {
            'workspace': workspace_path,
            'files_scanned': files_scanned,
            'files_with_issues': len(files_with_issues),
            'total_findings': len(all_findings),
            'summary': summary,
            'findings': all_findings,
        }
