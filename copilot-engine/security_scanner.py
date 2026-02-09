"""
Copilot Engine - Security Scanner
Detects security vulnerabilities, hardcoded secrets, dangerous patterns,
and common OWASP issues in source code.
"""
import os
import re
from pathlib import Path
from typing import Optional


class SecurityScanner:
    """Scans source files for security issues."""

    # Pattern categories with severity levels
    PATTERNS = {
        'sql_injection': {
            'severity': 'HIGH',
            'patterns': [
                (r'f["\'].*(?:SELECT|INSERT|UPDATE|DELETE|DROP).*\{', 'SQL injection via f-string'),
                (r'["\'].*(?:SELECT|INSERT|UPDATE|DELETE|DROP).*["\']\s*\+', 'SQL injection via concatenation'),
                (r'\.format\(.*(?:SELECT|INSERT|UPDATE|DELETE)', 'SQL injection via .format()'),
                (r'`.*(?:SELECT|INSERT|UPDATE|DELETE).*\$\{', 'SQL injection via template literal'),
                (r'%s.*(?:SELECT|INSERT|UPDATE|DELETE)', 'SQL injection via %-formatting'),
            ],
        },
        'hardcoded_secrets': {
            'severity': 'CRITICAL',
            'patterns': [
                (r'(?:password|passwd|pwd)\s*=\s*["\'][^"\']{4,}["\']', 'Hardcoded password'),
                (r'(?:api_key|apikey|api_secret)\s*=\s*["\'][^"\']{8,}["\']', 'Hardcoded API key'),
                (r'(?:secret_key|secret)\s*=\s*["\'][^"\']{8,}["\']', 'Hardcoded secret'),
                (r'(?:token|auth_token|access_token)\s*=\s*["\'][^"\']{8,}["\']', 'Hardcoded token'),
                (r'(?:AWS_SECRET|AWS_ACCESS_KEY)\s*=\s*["\']', 'Hardcoded AWS credential'),
                (r'(?:PRIVATE_KEY|private_key)\s*=\s*["\']', 'Hardcoded private key'),
                (r'-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----', 'Embedded private key'),
                (r'(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,}', 'GitHub token detected'),
                (r'sk-[A-Za-z0-9]{40,}', 'OpenAI API key detected'),
            ],
        },
        'dangerous_functions': {
            'severity': 'HIGH',
            'patterns': [
                (r'\beval\s*\(', 'Use of eval() - code injection risk'),
                (r'\bexec\s*\(', 'Use of exec() - code injection risk'),
                (r'subprocess\.(?:call|run|Popen)\(.*shell\s*=\s*True', 'Shell injection risk'),
                (r'os\.system\s*\(', 'os.system() - shell injection risk'),
                (r'os\.popen\s*\(', 'os.popen() - shell injection risk'),
                (r'__import__\s*\(', 'Dynamic import - code injection risk'),
                (r'pickle\.loads?\s*\(', 'Unsafe deserialization (pickle)'),
                (r'yaml\.load\s*\((?!.*Loader)', 'Unsafe YAML loading'),
                (r'marshal\.loads?\s*\(', 'Unsafe deserialization (marshal)'),
                (r'innerHTML\s*=', 'innerHTML - XSS risk'),
                (r'document\.write\s*\(', 'document.write - XSS risk'),
                (r'dangerouslySetInnerHTML', 'React dangerouslySetInnerHTML - XSS risk'),
            ],
        },
        'weak_crypto': {
            'severity': 'MEDIUM',
            'patterns': [
                (r'\bmd5\b', 'MD5 is cryptographically broken'),
                (r'\bsha1\b', 'SHA-1 is cryptographically weak'),
                (r'DES\b', 'DES encryption is obsolete'),
                (r'RC4\b', 'RC4 is broken'),
                (r'random\(\)|Math\.random\(\)', 'Non-cryptographic random for security'),
            ],
        },
        'auth_issues': {
            'severity': 'HIGH',
            'patterns': [
                (r'verify\s*=\s*False', 'SSL verification disabled'),
                (r'jwt\.decode\(.*verify\s*=\s*False', 'JWT verification disabled'),
                (r'(?:CORS|cors).*\*', 'CORS allows all origins'),
                (r'allow_origins\s*=\s*\[\s*["\']?\*', 'CORS wildcard origin'),
                (r'DEBUG\s*=\s*True', 'Debug mode enabled'),
                (r'TESTING\s*=\s*True', 'Testing mode in non-test file'),
            ],
        },
        'information_disclosure': {
            'severity': 'MEDIUM',
            'patterns': [
                (r'console\.log\(.*(?:password|secret|token|key)', 'Sensitive data in console.log'),
                (r'print\(.*(?:password|secret|token|key)', 'Sensitive data in print()'),
                (r'logging\..*(?:password|secret|token|key)', 'Sensitive data in logging'),
                (r'traceback\.print_exc', 'Full traceback exposed'),
                (r'\.stack\b', 'Stack trace exposed'),
            ],
        },
        'path_traversal': {
            'severity': 'HIGH',
            'patterns': [
                (r'open\s*\(.*\+.*\)', 'Possible path traversal in file open'),
                (r'os\.path\.join\s*\(.*request', 'User input in file path'),
                (r'send_file\s*\(.*request', 'User input in send_file'),
            ],
        },
    }

    # File extensions to scan
    SCANNABLE_EXTENSIONS = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go',
        '.rs', '.rb', '.php', '.cs', '.c', '.cpp', '.h',
        '.yaml', '.yml', '.json', '.toml', '.cfg', '.ini',
        '.env', '.sh', '.bash', '.sql',
    }

    # Directories to skip
    SKIP_DIRS = {
        'node_modules', '.git', '__pycache__', '.venv', 'venv',
        'env', '.env', 'dist', 'build', '.next', '.cache',
        'site-packages', '.tox', '.mypy_cache', '.pytest_cache',
        'target', 'vendor', 'bin', 'obj',
    }

    def scan_file(self, file_path: str) -> list[dict]:
        """Scan a single file for security issues."""
        if not os.path.isfile(file_path):
            return []

        ext = Path(file_path).suffix.lower()
        if ext not in self.SCANNABLE_EXTENSIONS:
            return []

        findings = []

        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
        except Exception:
            return []

        for line_num, line in enumerate(lines, 1):
            stripped = line.strip()

            # Skip comments
            if stripped.startswith('#') or stripped.startswith('//') or \
               stripped.startswith('*') or stripped.startswith('/*'):
                continue

            # Skip test files for some patterns
            is_test = 'test' in file_path.lower() or 'spec' in file_path.lower()

            for category, config in self.PATTERNS.items():
                # Skip auth_issues in test files
                if is_test and category == 'auth_issues':
                    continue

                for pattern, description in config['patterns']:
                    if re.search(pattern, line, re.IGNORECASE):
                        findings.append({
                            'file': file_path,
                            'line': line_num,
                            'column': 0,
                            'severity': config['severity'],
                            'category': category,
                            'issue': description,
                            'suggestion': self._get_suggestion(category, description),
                            'pattern': pattern,
                            'code': stripped[:120],
                        })

        return findings

    def scan_workspace(self, workspace_path: str, max_files: int = 500) -> dict:
        """Scan entire workspace for security issues."""
        all_findings = []
        files_scanned = 0
        files_with_issues = set()

        for root, dirs, files in os.walk(workspace_path):
            # Skip excluded directories
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

        # Summary stats
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

    def _get_suggestion(self, category: str, issue: str) -> str:
        """Get fix suggestion for a finding."""
        suggestions = {
            'sql_injection': 'Use parameterized queries or an ORM instead of string concatenation',
            'hardcoded_secrets': 'Use environment variables or a secrets manager (dotenv, vault)',
            'dangerous_functions': 'Use safer alternatives or validate/sanitize all inputs',
            'weak_crypto': 'Use SHA-256/SHA-3 for hashing, AES-256 for encryption, bcrypt for passwords',
            'auth_issues': 'Enable security features and use strict configurations in production',
            'information_disclosure': 'Remove sensitive data from logs and error messages',
            'path_traversal': 'Validate and sanitize file paths, use os.path.realpath() to resolve',
        }
        return suggestions.get(category, 'Review and fix the security issue')
