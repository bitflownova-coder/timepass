"""
Copilot Engine - Copilot Style Issue Detector
Detects issues commonly introduced during AI-assisted coding:
TODOs, NotImplementedError, magic numbers, hardcoded values,
console.log in production, copy-paste code, etc.
"""
import ast
import os
import re
from pathlib import Path
from typing import Optional, Dict, List, Set
from collections import defaultdict
import hashlib


class CopilotStyleDetector:
    """Detects issues commonly introduced during AI-assisted coding."""

    SKIP_DIRS = {
        'node_modules', '.git', '__pycache__', '.venv', 'venv',
        'env', 'dist', 'build', '.next', '.cache', 'site-packages',
    }
    
    TEST_PATTERNS = [
        r'test_.*\.py$', r'.*_test\.py$', r'tests?[/\\]',
        r'\.test\.(js|ts|jsx|tsx)$', r'\.spec\.(js|ts|jsx|tsx)$',
    ]
    
    # URLs that are okay to hardcode
    ALLOWED_URL_PATTERNS = [
        r'localhost', r'127\.0\.0\.1', r'example\.com', r'placeholder',
        r'schema\.org', r'w3\.org', r'xmlns', r'github\.com/.*#', r'#',
        r'\.test$', r'\.local$',
    ]

    def __init__(self):
        self.findings = []
        self.workspace_path = ""
        self.code_blocks: Dict[str, List[dict]] = defaultdict(list)  # hash -> locations

    def analyze_workspace(self, workspace_path: str, max_files: int = 500) -> dict:
        """Analyze workspace for copilot-style issues."""
        self.workspace_path = workspace_path
        self.findings = []
        self.code_blocks = defaultdict(list)
        
        files_analyzed = 0
        
        for root, dirs, files in os.walk(workspace_path):
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]
            
            for fname in files:
                if files_analyzed >= max_files:
                    break
                
                file_path = os.path.join(root, fname)
                ext = Path(fname).suffix.lower()
                
                if ext in ('.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs'):
                    self._analyze_file(file_path, ext)
                    files_analyzed += 1
        
        # Detect duplicated code blocks
        self._detect_duplicates()
        
        # Sort by severity
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3, 'INFO': 4}
        self.findings.sort(key=lambda f: (severity_order.get(f['severity'], 99), f['file']))
        
        return {
            'workspace': workspace_path,
            'files_analyzed': files_analyzed,
            'total_findings': len(self.findings),
            'summary': {
                'todos': sum(1 for f in self.findings if f['category'] == 'todo_fixme'),
                'not_implemented': sum(1 for f in self.findings if f['category'] == 'not_implemented'),
                'magic_numbers': sum(1 for f in self.findings if f['category'] == 'magic_number'),
                'hardcoded_values': sum(1 for f in self.findings if f['category'] == 'hardcoded_value'),
                'debug_code': sum(1 for f in self.findings if f['category'] == 'debug_code'),
                'duplicated_code': sum(1 for f in self.findings if f['category'] == 'duplicated_code'),
            },
            'findings': self.findings,
        }

    def _is_test_file(self, file_path: str) -> bool:
        """Check if file is a test file."""
        path_lower = file_path.lower().replace('\\', '/')
        return any(re.search(p, path_lower) for p in self.TEST_PATTERNS)

    def _analyze_file(self, file_path: str, ext: str):
        """Analyze a file for copilot-style issues."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                lines = content.splitlines()
        except Exception:
            return
        
        is_test = self._is_test_file(file_path)
        
        # Python-specific AST analysis
        if ext == '.py':
            self._analyze_python_ast(file_path, content, is_test)
        
        # Line-by-line analysis for all files
        self._analyze_lines(file_path, lines, ext, is_test)
        
        # Collect code blocks for duplicate detection
        self._collect_code_blocks(file_path, lines)

    def _analyze_python_ast(self, file_path: str, content: str, is_test: bool):
        """Analyze Python file using AST."""
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return
        
        for node in ast.walk(tree):
            # NotImplementedError / pass in non-test code
            if isinstance(node, ast.Raise):
                if isinstance(node.exc, ast.Call):
                    if isinstance(node.exc.func, ast.Name):
                        if node.exc.func.id == 'NotImplementedError':
                            if not is_test:
                                self.findings.append({
                                    'file': file_path,
                                    'line': node.lineno,
                                    'severity': 'MEDIUM',
                                    'category': 'not_implemented',
                                    'issue': "NotImplementedError in production code",
                                    'suggestion': "Implement the functionality or remove the stub",
                                })
            
            # Empty function with just 'pass' or '...'
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                body = node.body
                if len(body) == 1:
                    first = body[0]
                    if isinstance(first, ast.Pass):
                        if not is_test:
                            self.findings.append({
                                'file': file_path,
                                'line': node.lineno,
                                'severity': 'LOW',
                                'category': 'not_implemented',
                                'issue': f"Empty function '{node.name}' with just 'pass'",
                                'suggestion': "Implement the function or add a docstring explaining why it's empty",
                            })
                    elif isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                        if first.value.value == ...:  # Ellipsis
                            if not is_test:
                                self.findings.append({
                                    'file': file_path,
                                    'line': node.lineno,
                                    'severity': 'LOW',
                                    'category': 'not_implemented',
                                    'issue': f"Stub function '{node.name}' with ellipsis (...)",
                                    'suggestion': "Implement the function",
                                })

    def _analyze_lines(self, file_path: str, lines: list, ext: str, is_test: bool):
        """Analyze file line by line."""
        in_multiline_comment = False
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Track multiline comments
            if '"""' in line or "'''" in line:
                count = line.count('"""') + line.count("'''")
                if count == 1:
                    in_multiline_comment = not in_multiline_comment
                continue
            
            if in_multiline_comment:
                continue
            
            # Skip single line comments for some checks
            is_comment = stripped.startswith(('#', '//', '*', '/*'))
            
            # TODO/FIXME detection
            todo_match = re.search(r'\b(TODO|FIXME|HACK|XXX|BUG)\b[:\s]*(.{0,50})', line, re.IGNORECASE)
            if todo_match:
                tag = todo_match.group(1).upper()
                message = todo_match.group(2).strip()
                severity = 'LOW' if tag == 'TODO' else 'MEDIUM'
                self.findings.append({
                    'file': file_path,
                    'line': i,
                    'severity': severity,
                    'category': 'todo_fixme',
                    'issue': f"{tag}: {message[:50]}..." if len(message) > 50 else f"{tag}: {message}" if message else tag,
                    'suggestion': "Address the TODO/FIXME or create a tracking issue",
                })
            
            if is_comment:
                continue
            
            # Console.log / print debug statements (not in test files)
            if not is_test:
                debug_patterns = [
                    (r'\bconsole\.(log|debug|info)\s*\(', 'console.log'),
                    (r'\bconsole\.warn\s*\(.*debug', 'console.warn with debug'),
                    (r'print\s*\(\s*["\']debug', 'print debug statement'),
                    (r'print\s*\(.*#\s*debug', 'print with debug comment'),
                    (r'\blogger\.(debug|info)\s*\(.*DEBUG', 'debug logging'),
                ]
                for pattern, name in debug_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        self.findings.append({
                            'file': file_path,
                            'line': i,
                            'severity': 'LOW',
                            'category': 'debug_code',
                            'issue': f"Debug code: {name}",
                            'suggestion': "Remove debug statements before deploying to production",
                        })
                        break
                
                # Standalone print() in Python (not in test)
                if ext == '.py' and re.match(r'\s*print\s*\([^)]*\)\s*$', line):
                    # Allow if it's clearly a user-facing message
                    if not re.search(r'"(Error|Warning|Info|Usage|Help):', line):
                        pass  # Too many false positives, skip for now
            
            # Magic numbers
            magic_match = re.search(r'(?<![.\w])(\d{2,}(?:\.\d+)?)\b', line)
            if magic_match and not is_test:
                number = magic_match.group(1)
                # Skip common acceptable values
                skip_numbers = {'100', '200', '201', '204', '301', '302', '400', '401', '403', '404', '500', 
                               '1000', '1024', '2048', '4096', '8080', '3000', '5000', '8000', '443', '80',
                               '10', '60', '24', '365', '12', '30', '31', '360', '180', '90', '45'}
                if number not in skip_numbers:
                    # Skip if it's a version, port assignment, or in a constant definition
                    if not re.search(r'(version|port|=\s*\d|PORT|VERSION|SIZE|MAX|MIN|TIMEOUT|_ID)', line, re.IGNORECASE):
                        # Skip if in array index or similar
                        if not re.search(r'\[\d+\]', line):
                            self.findings.append({
                                'file': file_path,
                                'line': i,
                                'severity': 'INFO',
                                'category': 'magic_number',
                                'issue': f"Magic number: {number}",
                                'suggestion': "Extract to a named constant for clarity",
                            })
            
            # Hardcoded URLs/IPs (not in test files, not in comments)
            if not is_test:
                # URL pattern
                url_match = re.search(r'https?://([^\s"\')>\]]+)', line)
                if url_match:
                    url = url_match.group(0)
                    # Check if it's an allowed URL
                    if not any(re.search(p, url, re.IGNORECASE) for p in self.ALLOWED_URL_PATTERNS):
                        self.findings.append({
                            'file': file_path,
                            'line': i,
                            'severity': 'LOW',
                            'category': 'hardcoded_value',
                            'issue': f"Hardcoded URL: {url[:50]}...",
                            'suggestion': "Use environment variable or config for URLs",
                        })
                
                # IP address pattern (not localhost)
                ip_match = re.search(r'\b(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})\b', line)
                if ip_match:
                    ip = ip_match.group(1)
                    if ip not in ('127.0.0.1', '0.0.0.0', '255.255.255.255', '255.255.255.0'):
                        self.findings.append({
                            'file': file_path,
                            'line': i,
                            'severity': 'LOW',
                            'category': 'hardcoded_value',
                            'issue': f"Hardcoded IP address: {ip}",
                            'suggestion': "Use environment variable or config for IP addresses",
                        })
            
            # Commented-out code detection (basic)
            if is_comment and len(stripped) > 5:
                code_indicators = [
                    r'^\s*#\s*(if|for|while|def|class|return|import|from)\b',
                    r'^\s*//\s*(if|for|while|function|class|return|import|const|let|var)\b',
                    r'^\s*#.*[=;{}\[\]()]',
                    r'^\s*//.*[=;{}\[\]()]',
                ]
                for pattern in code_indicators:
                    if re.search(pattern, line):
                        self.findings.append({
                            'file': file_path,
                            'line': i,
                            'severity': 'INFO',
                            'category': 'commented_code',
                            'issue': "Commented-out code detected",
                            'suggestion': "Remove commented code or document why it's kept",
                        })
                        break

    def _collect_code_blocks(self, file_path: str, lines: list):
        """Collect code blocks for duplicate detection."""
        # Use sliding window of 5 lines
        window_size = 5
        min_line_length = 20  # Ignore trivial lines
        
        for i in range(len(lines) - window_size + 1):
            block = lines[i:i + window_size]
            
            # Skip if block contains mostly short/empty lines
            meaningful_lines = [l for l in block if len(l.strip()) > min_line_length]
            if len(meaningful_lines) < 3:
                continue
            
            # Skip if block is all comments
            if all(l.strip().startswith(('#', '//', '*', '/*')) for l in block):
                continue
            
            # Normalize and hash
            normalized = '\n'.join(l.strip() for l in block)
            block_hash = hashlib.md5(normalized.encode()).hexdigest()
            
            self.code_blocks[block_hash].append({
                'file': file_path,
                'line': i + 1,
                'code': block[0].strip()[:50],
            })

    def _detect_duplicates(self):
        """Detect duplicated code blocks."""
        reported_files = set()
        
        for block_hash, locations in self.code_blocks.items():
            if len(locations) >= 3:  # At least 3 duplicates
                # Group by file to avoid reporting same file multiple times
                files = set(loc['file'] for loc in locations)
                if len(files) >= 2:  # Duplicates across files
                    key = frozenset(files)
                    if key not in reported_files:
                        reported_files.add(key)
                        
                        # Report first occurrence
                        first = locations[0]
                        self.findings.append({
                            'file': first['file'],
                            'line': first['line'],
                            'severity': 'LOW',
                            'category': 'duplicated_code',
                            'issue': f"Code block duplicated {len(locations)} times across {len(files)} files",
                            'suggestion': "Extract to a shared function or module",
                        })
