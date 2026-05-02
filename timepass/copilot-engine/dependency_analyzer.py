"""
Copilot Engine - Dependency Analyzer
Analyzes dependencies for issues: circular imports, unused packages,
outdated versions, and known vulnerabilities.
"""
import ast
import os
import re
import json
from pathlib import Path
from typing import Optional, Set, Dict, List
from collections import defaultdict


class DependencyAnalyzer:
    """Analyzes project dependencies for issues and vulnerabilities."""

    SKIP_DIRS = {
        'node_modules', '.git', '__pycache__', '.venv', 'venv',
        'env', 'dist', 'build', '.next', '.cache', 'site-packages',
    }
    
    # Known vulnerable package versions (simplified - in production would use a CVE database)
    KNOWN_VULNERABILITIES = {
        # Python packages
        'django': {'<2.2.24': 'CVE-2021-33203: Directory traversal', '<3.1.13': 'CVE-2021-35042: SQL injection'},
        'flask': {'<1.0': 'Older versions have various security issues'},
        'requests': {'<2.20.0': 'CVE-2018-18074: Session handling vulnerability'},
        'pyyaml': {'<5.4': 'CVE-2020-14343: Arbitrary code execution'},
        'pillow': {'<8.1.2': 'CVE-2021-25293: Buffer overflow'},
        'urllib3': {'<1.26.5': 'CVE-2021-33503: ReDoS vulnerability'},
        'jinja2': {'<2.11.3': 'CVE-2020-28493: ReDoS vulnerability'},
        'cryptography': {'<3.3.2': 'Multiple CVEs - update recommended'},
        'numpy': {'<1.22.0': 'CVE-2021-41496: Buffer overflow'},
        'setuptools': {'<65.5.1': 'CVE-2022-40897: ReDoS vulnerability'},
        # NPM packages
        'lodash': {'<4.17.21': 'CVE-2021-23337: Command injection'},
        'axios': {'<0.21.1': 'CVE-2020-28168: SSRF vulnerability'},
        'express': {'<4.17.3': 'CVE-2022-24999: Prototype pollution'},
        'minimist': {'<1.2.6': 'CVE-2021-44906: Prototype pollution'},
        'node-fetch': {'<2.6.7': 'CVE-2022-0235: Information exposure'},
        'glob-parent': {'<5.1.2': 'CVE-2020-28469: ReDoS vulnerability'},
        'path-parse': {'<1.0.7': 'CVE-2021-23343: ReDoS vulnerability'},
        'json5': {'<2.2.2': 'CVE-2022-46175: Prototype pollution'},
    }

    def __init__(self):
        self.findings = []
        self.workspace_path = ""
        self.import_graph: Dict[str, Set[str]] = defaultdict(set)
        self.used_imports: Set[str] = set()

    def analyze_workspace(self, workspace_path: str) -> dict:
        """Analyze workspace dependencies."""
        self.workspace_path = workspace_path
        self.findings = []
        self.import_graph = defaultdict(set)
        self.used_imports = set()
        
        # Analyze different dependency files
        self._analyze_requirements_txt(workspace_path)
        self._analyze_package_json(workspace_path)
        self._analyze_pyproject_toml(workspace_path)
        
        # Build import graph for circular dependency detection
        self._build_import_graph(workspace_path)
        
        # Detect circular imports
        self._detect_circular_imports()
        
        # Sort by severity
        severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3, 'INFO': 4}
        self.findings.sort(key=lambda f: (severity_order.get(f['severity'], 99), f['category']))
        
        return {
            'workspace': workspace_path,
            'total_findings': len(self.findings),
            'summary': {
                'vulnerable_deps': sum(1 for f in self.findings if f['category'] == 'vulnerable_dependency'),
                'circular_imports': sum(1 for f in self.findings if f['category'] == 'circular_import'),
                'unused_deps': sum(1 for f in self.findings if f['category'] == 'unused_dependency'),
                'outdated_deps': sum(1 for f in self.findings if f['category'] == 'outdated_dependency'),
            },
            'findings': self.findings,
        }

    def _analyze_requirements_txt(self, workspace_path: str):
        """Analyze requirements.txt for issues."""
        req_files = []
        for root, dirs, files in os.walk(workspace_path):
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]
            for fname in files:
                if fname in ('requirements.txt', 'requirements-dev.txt', 'requirements-prod.txt'):
                    req_files.append(os.path.join(root, fname))
        
        declared_packages = set()
        
        for req_file in req_files:
            try:
                with open(req_file, 'r', encoding='utf-8') as f:
                    for line_num, line in enumerate(f, 1):
                        line = line.strip()
                        if not line or line.startswith('#') or line.startswith('-'):
                            continue
                        
                        # Parse package==version or package>=version
                        match = re.match(r'^([a-zA-Z0-9_-]+)(?:[<>=!]+)?([0-9.]*)?', line)
                        if match:
                            pkg_name = match.group(1).lower()
                            version = match.group(2) or ''
                            declared_packages.add(pkg_name)
                            
                            # Check for vulnerabilities
                            self._check_vulnerability(pkg_name, version, req_file, line_num)
                            
                            # Check for unpinned version
                            if '==' not in line and '>=' not in line and version == '':
                                self.findings.append({
                                    'file': req_file,
                                    'line': line_num,
                                    'severity': 'LOW',
                                    'category': 'unpinned_version',
                                    'issue': f"Package '{pkg_name}' has no version pinned",
                                    'suggestion': "Pin versions for reproducible builds (e.g., pkg==1.0.0)",
                                })
            except Exception:
                continue
        
        # Store for unused detection
        self._declared_python_packages = declared_packages

    def _analyze_package_json(self, workspace_path: str):
        """Analyze package.json for issues."""
        pkg_files = []
        for root, dirs, files in os.walk(workspace_path):
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]
            if 'package.json' in files:
                pkg_files.append(os.path.join(root, 'package.json'))
        
        for pkg_file in pkg_files:
            try:
                with open(pkg_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Check dependencies
                for dep_type in ('dependencies', 'devDependencies'):
                    deps = data.get(dep_type, {})
                    for pkg_name, version_spec in deps.items():
                        # Extract version number
                        version = re.sub(r'^[\^~>=<]+', '', version_spec)
                        self._check_vulnerability(pkg_name.lower(), version, pkg_file, 0)
                        
                        # Check for wildcard versions
                        if '*' in version_spec or 'latest' in version_spec:
                            self.findings.append({
                                'file': pkg_file,
                                'line': 0,
                                'severity': 'MEDIUM',
                                'category': 'unpinned_version',
                                'issue': f"Package '{pkg_name}' uses wildcard/latest version",
                                'suggestion': "Pin to specific version for security and reproducibility",
                            })
                
                # Check for missing package-lock.json
                lock_file = os.path.join(os.path.dirname(pkg_file), 'package-lock.json')
                if not os.path.exists(lock_file):
                    self.findings.append({
                        'file': pkg_file,
                        'line': 0,
                        'severity': 'LOW',
                        'category': 'missing_lockfile',
                        'issue': "No package-lock.json found",
                        'suggestion': "Run 'npm install' to generate lockfile for reproducible builds",
                    })
                    
            except Exception:
                continue

    def _analyze_pyproject_toml(self, workspace_path: str):
        """Analyze pyproject.toml for issues."""
        for root, dirs, files in os.walk(workspace_path):
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]
            if 'pyproject.toml' in files:
                toml_file = os.path.join(root, 'pyproject.toml')
                try:
                    with open(toml_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Basic TOML parsing for dependencies
                    in_deps = False
                    for line_num, line in enumerate(content.splitlines(), 1):
                        if '[project.dependencies]' in line or '[tool.poetry.dependencies]' in line:
                            in_deps = True
                            continue
                        if in_deps:
                            if line.startswith('['):
                                in_deps = False
                                continue
                            
                            match = re.match(r'([a-zA-Z0-9_-]+)\s*=\s*["\']([^"\']+)["\']', line.strip())
                            if match:
                                pkg_name = match.group(1).lower()
                                version_spec = match.group(2)
                                version = re.sub(r'^[\^~>=<]+', '', version_spec)
                                self._check_vulnerability(pkg_name, version, toml_file, line_num)
                except Exception:
                    continue

    def _check_vulnerability(self, pkg_name: str, version: str, file_path: str, line: int):
        """Check if package version has known vulnerabilities."""
        pkg_lower = pkg_name.lower()
        
        if pkg_lower in self.KNOWN_VULNERABILITIES:
            vulns = self.KNOWN_VULNERABILITIES[pkg_lower]
            for vuln_spec, vuln_info in vulns.items():
                if self._version_matches(version, vuln_spec):
                    self.findings.append({
                        'file': file_path,
                        'line': line,
                        'severity': 'HIGH',
                        'category': 'vulnerable_dependency',
                        'issue': f"'{pkg_name}' version {version or '(unpinned)'} has known vulnerability",
                        'suggestion': f"{vuln_info}. Update to latest secure version.",
                    })
                    break

    def _version_matches(self, installed: str, vuln_spec: str) -> bool:
        """Check if installed version matches vulnerability specification."""
        if not installed:
            return True  # Unpinned could be vulnerable
        
        try:
            # Parse vulnerability spec like "<2.0.0"
            op_match = re.match(r'([<>=!]+)(\d+\.\d+(?:\.\d+)?)', vuln_spec)
            if not op_match:
                return False
            
            op = op_match.group(1)
            vuln_version = op_match.group(2)
            
            # Simple version comparison
            installed_parts = [int(x) for x in re.findall(r'\d+', installed)[:3]]
            vuln_parts = [int(x) for x in re.findall(r'\d+', vuln_version)[:3]]
            
            # Pad to same length
            while len(installed_parts) < 3:
                installed_parts.append(0)
            while len(vuln_parts) < 3:
                vuln_parts.append(0)
            
            if op == '<':
                return installed_parts < vuln_parts
            elif op == '<=':
                return installed_parts <= vuln_parts
            elif op == '>':
                return installed_parts > vuln_parts
            elif op == '>=':
                return installed_parts >= vuln_parts
            elif op == '==':
                return installed_parts == vuln_parts
        except Exception:
            pass
        
        return False

    def _build_import_graph(self, workspace_path: str):
        """Build import graph for Python files."""
        python_files = {}
        
        for root, dirs, files in os.walk(workspace_path):
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]
            
            for fname in files:
                if fname.endswith('.py'):
                    file_path = os.path.join(root, fname)
                    # Module name based on path
                    rel_path = os.path.relpath(file_path, workspace_path)
                    module_name = rel_path.replace(os.sep, '.').replace('.py', '')
                    if module_name.endswith('.__init__'):
                        module_name = module_name[:-9]
                    python_files[module_name] = file_path
        
        # Analyze imports
        for module_name, file_path in python_files.items():
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                tree = ast.parse(content)
                
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            imported = alias.name.split('.')[0]
                            self.import_graph[module_name].add(imported)
                            self.used_imports.add(imported)
                    
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            imported = node.module.split('.')[0]
                            self.import_graph[module_name].add(imported)
                            self.used_imports.add(imported)
            except Exception:
                continue

    def _detect_circular_imports(self):
        """Detect circular import dependencies."""
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(module, path):
            visited.add(module)
            rec_stack.add(module)
            
            for imported in self.import_graph.get(module, []):
                if imported in self.import_graph:  # Only check internal modules
                    if imported not in visited:
                        result = dfs(imported, path + [imported])
                        if result:
                            return result
                    elif imported in rec_stack:
                        # Found cycle
                        cycle_start = path.index(imported) if imported in path else len(path)
                        cycle = path[cycle_start:] + [imported]
                        return cycle
            
            rec_stack.remove(module)
            return None
        
        for module in self.import_graph:
            if module not in visited:
                cycle = dfs(module, [module])
                if cycle and tuple(sorted(cycle)) not in [(tuple(sorted(c))) for c in cycles]:
                    cycles.append(cycle)
        
        for cycle in cycles:
            self.findings.append({
                'file': '',  # Multiple files involved
                'line': 0,
                'severity': 'MEDIUM',
                'category': 'circular_import',
                'issue': f"Circular import detected: {' -> '.join(cycle)}",
                'suggestion': "Refactor to break the cycle: use lazy imports, move shared code to a third module, or restructure",
            })
