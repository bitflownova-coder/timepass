"""
Copilot Engine - API Detector
Automatically detects API endpoints from source code across frameworks:
Flask, FastAPI, Django, Express, etc.
"""
import os
import re
from pathlib import Path
from typing import Optional


class APIDetector:
    """Detects API route definitions from source code."""

    # Framework-specific endpoint patterns
    FRAMEWORK_PATTERNS = {
        'flask': {
            'language': 'python',
            'patterns': [
                # @app.route('/path', methods=['GET'])
                (r'@\w+\.route\s*\(\s*["\']([^"\']+)["\'](?:.*methods\s*=\s*\[([^\]]+)\])?', 'route'),
                # @app.get('/path')
                (r'@\w+\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']', 'method_decorator'),
            ],
        },
        'fastapi': {
            'language': 'python',
            'patterns': [
                # @app.get('/path')
                (r'@\w+\.(get|post|put|delete|patch|options|head)\s*\(\s*["\']([^"\']+)["\']', 'method_decorator'),
                # @router.get('/path')
                (r'@router\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']', 'router_decorator'),
                # APIRouter(prefix='/api')
                (r'APIRouter\s*\(.*prefix\s*=\s*["\']([^"\']+)["\']', 'router_prefix'),
            ],
        },
        'django': {
            'language': 'python',
            'patterns': [
                # path('url/', view)
                (r'path\s*\(\s*["\']([^"\']+)["\']', 'urlpattern'),
                # re_path(r'^url/', view)
                (r're_path\s*\(\s*r?["\']([^"\']+)["\']', 'urlpattern_regex'),
                # url(r'^url/', view)
                (r'url\s*\(\s*r?["\']([^"\']+)["\']', 'urlpattern_legacy'),
            ],
        },
        'express': {
            'language': 'javascript',
            'patterns': [
                # app.get('/path', handler)
                (r'\w+\.(get|post|put|delete|patch|all|use)\s*\(\s*["\']([^"\']+)["\']', 'route'),
                # router.get('/path', handler)
                (r'router\.(get|post|put|delete|patch|all|use)\s*\(\s*["\']([^"\']+)["\']', 'router'),
            ],
        },
        'nest': {
            'language': 'typescript',
            'patterns': [
                # @Get('/path')
                (r'@(Get|Post|Put|Delete|Patch|All)\s*\(\s*["\']([^"\']*)["\']?\s*\)', 'decorator'),
                # @Controller('/path')
                (r'@Controller\s*\(\s*["\']([^"\']+)["\']', 'controller'),
            ],
        },
        'go_http': {
            'language': 'go',
            'patterns': [
                # http.HandleFunc("/path", handler)
                (r'\.HandleFunc\s*\(\s*["\']([^"\']+)["\']', 'handlefunc'),
                # r.GET("/path", handler) - gin, chi, echo
                (r'\.\s*(GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s*\(\s*["\']([^"\']+)["\']', 'method'),
                # e.GET("/path", handler) - echo
                (r'\w+\.(GET|POST|PUT|DELETE|PATCH)\s*\(\s*["\']([^"\']+)["\']', 'method'),
            ],
        },
    }

    # Extensions to scan per language
    LANGUAGE_EXTENSIONS = {
        'python': {'.py'},
        'javascript': {'.js', '.mjs', '.cjs'},
        'typescript': {'.ts', '.tsx'},
        'go': {'.go'},
    }

    SKIP_DIRS = {
        'node_modules', '.git', '__pycache__', '.venv', 'venv',
        'dist', 'build', '.next', '.cache', 'vendor', 'target',
    }

    def detect_endpoints(self, workspace_path: str) -> dict:
        """Detect all API endpoints in a workspace."""
        endpoints = []
        frameworks_detected = set()
        files_scanned = 0

        for root, dirs, files in os.walk(workspace_path):
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]

            for fname in files:
                file_path = os.path.join(root, fname)
                ext = Path(fname).suffix.lower()

                # Check each framework's language
                for fw_name, fw_config in self.FRAMEWORK_PATTERNS.items():
                    lang = fw_config['language']
                    if ext not in self.LANGUAGE_EXTENSIONS.get(lang, set()):
                        continue

                    files_scanned += 1
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            lines = content.split('\n')
                    except Exception:
                        continue

                    for pattern, pattern_type in fw_config['patterns']:
                        for i, line in enumerate(lines, 1):
                            match = re.search(pattern, line, re.IGNORECASE)
                            if match:
                                frameworks_detected.add(fw_name)
                                endpoint = self._extract_endpoint(
                                    match, pattern_type, fw_name,
                                    file_path, i, line
                                )
                                if endpoint:
                                    endpoints.append(endpoint)

        # Deduplicate and sort
        seen = set()
        unique = []
        for ep in endpoints:
            key = f"{ep['method']}:{ep['route']}"
            if key not in seen:
                seen.add(key)
                unique.append(ep)

        unique.sort(key=lambda e: e['route'])

        return {
            'workspace': workspace_path,
            'frameworks': list(frameworks_detected),
            'total_endpoints': len(unique),
            'files_scanned': files_scanned,
            'endpoints': unique,
        }

    def validate_api_call(self, workspace_path: str, method: str, route: str) -> dict:
        """Validate if an API call matches defined endpoints."""
        detection = self.detect_endpoints(workspace_path)
        endpoints = detection['endpoints']

        matches = []
        for ep in endpoints:
            if self._routes_match(ep['route'], route):
                if ep['method'].upper() == method.upper() or ep['method'] == 'ALL':
                    matches.append({
                        'endpoint': ep,
                        'match_type': 'exact',
                    })
                else:
                    matches.append({
                        'endpoint': ep,
                        'match_type': 'route_only',
                        'warning': f"Route exists but expects {ep['method']}, not {method}",
                    })

        if not matches:
            # Try partial matches
            for ep in endpoints:
                if route.startswith(ep['route']) or ep['route'].startswith(route):
                    matches.append({
                        'endpoint': ep,
                        'match_type': 'partial',
                        'warning': f"Partial match: {ep['route']}",
                    })

        return {
            'method': method,
            'route': route,
            'valid': any(m['match_type'] == 'exact' for m in matches),
            'matches': matches,
            'suggestion': self._get_suggestion(method, route, matches, endpoints),
        }

    def _extract_endpoint(self, match: re.Match, pattern_type: str,
                          framework: str, file_path: str, line: int,
                          line_text: str) -> Optional[dict]:
        """Extract endpoint details from a regex match."""
        groups = match.groups()

        if pattern_type == 'route':
            route = groups[0]
            methods = groups[1] if len(groups) > 1 and groups[1] else 'GET'
            if isinstance(methods, str) and ',' in methods:
                methods = methods.replace("'", "").replace('"', '').strip()
            method = methods.split(',')[0].strip().upper() if methods else 'GET'

        elif pattern_type in ('method_decorator', 'router_decorator', 'method', 'router'):
            method = groups[0].upper()
            route = groups[1] if len(groups) > 1 else '/'

        elif pattern_type in ('handlefunc', 'urlpattern', 'urlpattern_regex', 'urlpattern_legacy'):
            route = groups[0]
            method = 'ANY'

        elif pattern_type == 'controller':
            return None  # Just prefix, not a full endpoint

        elif pattern_type == 'decorator':
            method = groups[0].upper()
            route = groups[1] if len(groups) > 1 and groups[1] else '/'

        elif pattern_type == 'router_prefix':
            return None  # Prefix only

        else:
            return None

        return {
            'method': method,
            'route': route,
            'framework': framework,
            'file': file_path,
            'line': line,
            'pattern_type': pattern_type,
        }

    def _routes_match(self, defined_route: str, requested_route: str) -> bool:
        """Check if a defined route matches a requested route."""
        # Exact match
        if defined_route == requested_route:
            return True

        # Normalize trailing slashes
        d = defined_route.rstrip('/')
        r = requested_route.rstrip('/')
        if d == r:
            return True

        # Check path parameter patterns
        # /users/{id} matches /users/123
        param_pattern = re.sub(r'\{[^}]+\}', r'[^/]+', d)
        param_pattern = re.sub(r':\w+', r'[^/]+', param_pattern)
        param_pattern = re.sub(r'<\w+(?::\w+)?>', r'[^/]+', param_pattern)

        if re.fullmatch(param_pattern, r):
            return True

        return False

    def _get_suggestion(self, method: str, route: str, matches: list, endpoints: list) -> Optional[str]:
        """Get suggestion for invalid API calls."""
        if matches:
            m = matches[0]
            if m['match_type'] == 'route_only':
                return f"Use {m['endpoint']['method']} instead of {method}"
            elif m['match_type'] == 'partial':
                return f"Did you mean {m['endpoint']['route']}?"
        else:
            # Find similar routes
            similar = []
            for ep in endpoints:
                if any(part in ep['route'] for part in route.split('/') if part):
                    similar.append(f"{ep['method']} {ep['route']}")
            if similar:
                return f"Similar endpoints: {', '.join(similar[:3])}"
            return 'No matching endpoint found in the codebase'
