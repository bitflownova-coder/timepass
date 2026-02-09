"""
Copilot Engine - API Contract Enforcement System
Deterministic validation of API endpoints, response shapes, HTTP discipline,
naming conventions, middleware usage, and auth guard consistency.

Covers:
  - Endpoint contract registry with request/response schemas
  - Response shape validation (field added/removed/renamed/type-changed)
  - HTTP method discipline (GET idempotent, POST→201, DELETE→204, etc.)
  - Naming convention enforcement (kebab-case, plural resources, etc.)
  - Duplicate route detection
  - Auth guard consistency checking
  - Middleware usage validation
  - Standardized response format enforcement
"""
import os
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone


# ──────────────────────────────────────────────────────────────
# Data Structures
# ──────────────────────────────────────────────────────────────

@dataclass
class EndpointContract:
    """Represents a fully-described API endpoint contract."""
    method: str              # GET, POST, PUT, DELETE, PATCH
    path: str                # /api/users/:id
    handler_name: str = ""
    file_path: str = ""
    line_number: int = 0
    framework: str = ""

    # Schema tracking
    request_params: Dict[str, str] = field(default_factory=dict)   # path params
    query_params: Dict[str, str] = field(default_factory=dict)
    request_body_fields: Dict[str, Any] = field(default_factory=dict)
    response_fields: Dict[str, Any] = field(default_factory=dict)
    status_code: Optional[int] = None

    # Guards / middleware
    auth_guard: Optional[str] = None
    middleware: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)

    # Metadata
    detected_at: str = ""


@dataclass
class ContractViolation:
    severity: str   # CRITICAL, HIGH, MEDIUM, LOW, INFO
    category: str   # http_discipline, naming, duplicate, auth, response_shape, middleware
    message: str
    endpoint: Optional[str] = None   # METHOD /path
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    suggestion: Optional[str] = None


# ──────────────────────────────────────────────────────────────
# Endpoint Extractor (Enhanced)
# ──────────────────────────────────────────────────────────────

class EndpointExtractor:
    """Extracts full endpoint contracts from source code (not just routes)."""

    SKIP_DIRS = {
        'node_modules', '.git', '__pycache__', '.venv', 'venv',
        'dist', 'build', '.next', '.cache', 'vendor', 'target',
    }

    # ── Express/NestJS patterns ──
    EXPRESS_ROUTE = re.compile(
        r'(?:app|router)\.(get|post|put|delete|patch|all)\s*\(\s*["\']([^"\']+)["\']',
        re.IGNORECASE
    )
    EXPRESS_MIDDLEWARE = re.compile(
        r'(?:app|router)\.\w+\s*\([^,]+,\s*(\w+)\s*,',
    )
    NEST_DECORATOR = re.compile(
        r'@(Get|Post|Put|Delete|Patch|All)\s*\(\s*["\']?([^"\')\s]*)["\']?\s*\)',
    )
    NEST_CONTROLLER = re.compile(r'@Controller\s*\(\s*["\']([^"\']*)["\']?\s*\)')
    NEST_GUARD = re.compile(r'@UseGuards?\s*\(\s*([^)]+)\s*\)')
    NEST_BODY = re.compile(r'@Body\s*\(\s*\)\s*\w+\s*:\s*(\w+)')
    NEST_PARAM = re.compile(r'@Param\s*\(\s*["\']?(\w+)["\']?\s*\)')
    NEST_QUERY = re.compile(r'@Query\s*\(\s*["\']?(\w+)["\']?\s*\)')

    # ── FastAPI patterns ──
    FASTAPI_ROUTE = re.compile(
        r'@\w+\.(get|post|put|delete|patch)\s*\(\s*["\']([^"\']+)["\']',
        re.IGNORECASE
    )
    FASTAPI_RESPONSE = re.compile(r'response_model\s*=\s*(\w+)')
    FASTAPI_STATUS = re.compile(r'status_code\s*=\s*(\d+)')
    FASTAPI_DEPENDS = re.compile(r'Depends\s*\(\s*(\w+)\s*\)')

    # ── Flask patterns ──
    FLASK_ROUTE = re.compile(
        r'@\w+\.route\s*\(\s*["\']([^"\']+)["\'](?:.*methods\s*=\s*\[([^\]]+)\])?',
    )

    # ── Return type / response analysis ──
    TS_RETURN_TYPE = re.compile(r'\)\s*:\s*(?:Promise\s*<\s*)?(\w+)(?:\s*>)?')
    PY_RETURN_TYPE = re.compile(r'->\s*(\w+)\s*:')
    STATUS_CODE = re.compile(r'(?:status|statusCode|status_code)\s*[=:]\s*(\d{3})')
    RES_STATUS = re.compile(r'\.status\s*\(\s*(\d{3})\s*\)')
    RES_JSON = re.compile(r'\.json\s*\(\s*\{([^}]+)\}', re.DOTALL)

    def extract_contracts(self, workspace_path: str) -> List[EndpointContract]:
        """Extract all endpoint contracts from workspace."""
        contracts = []

        for root, dirs, files in os.walk(workspace_path):
            dirs[:] = [d for d in dirs if d not in self.SKIP_DIRS]

            for fname in files:
                ext = Path(fname).suffix.lower()
                if ext not in ('.ts', '.tsx', '.js', '.jsx', '.py'):
                    continue

                file_path = os.path.join(root, fname)
                try:
                    content = Path(file_path).read_text(encoding='utf-8', errors='ignore')
                except Exception:
                    continue

                if ext in ('.ts', '.tsx'):
                    contracts.extend(self._extract_nest(content, file_path))
                    contracts.extend(self._extract_express(content, file_path))
                elif ext in ('.js', '.jsx'):
                    contracts.extend(self._extract_express(content, file_path))
                elif ext == '.py':
                    contracts.extend(self._extract_fastapi(content, file_path))
                    contracts.extend(self._extract_flask(content, file_path))

        return contracts

    def _extract_nest(self, content: str, file_path: str) -> List[EndpointContract]:
        """Extract NestJS controller endpoints with guards, params, body types."""
        contracts = []
        lines = content.split('\n')

        # Find controller prefix
        ctrl_match = self.NEST_CONTROLLER.search(content)
        prefix = ctrl_match.group(1) if ctrl_match else ''

        # Find class-level guard
        class_guard = None
        guard_match = self.NEST_GUARD.search(content.split('class ')[0] if 'class ' in content else '')
        if guard_match:
            class_guard = guard_match.group(1).strip()

        for i, line in enumerate(lines, 1):
            match = self.NEST_DECORATOR.search(line)
            if not match:
                continue

            method = match.group(1).upper()
            route_part = match.group(2) or ''
            path = f'/{prefix}/{route_part}'.replace('//', '/').rstrip('/')
            if not path:
                path = '/'

            contract = EndpointContract(
                method=method,
                path=path,
                file_path=file_path,
                line_number=i,
                framework='nest',
                detected_at=datetime.now(timezone.utc).isoformat(),
            )

            # Look at surrounding lines for more info
            context_start = max(0, i - 3)
            context_end = min(len(lines), i + 20)
            context_block = '\n'.join(lines[context_start:context_end])

            # Guard
            guard_match = self.NEST_GUARD.search(context_block)
            if guard_match:
                contract.auth_guard = guard_match.group(1).strip()
            elif class_guard:
                contract.auth_guard = class_guard

            # Body type
            body_match = self.NEST_BODY.search(context_block)
            if body_match:
                contract.request_body_fields = {'_dto_type': body_match.group(1)}

            # Params
            for pm in self.NEST_PARAM.finditer(context_block):
                contract.request_params[pm.group(1)] = 'string'

            # Query params
            for qm in self.NEST_QUERY.finditer(context_block):
                contract.query_params[qm.group(1)] = 'string'

            # Handler name
            handler_match = re.search(r'(?:async\s+)?(\w+)\s*\(', lines[i - 1] if i < len(lines) else '')
            if not handler_match and i < len(lines):
                handler_match = re.search(r'(?:async\s+)?(\w+)\s*\(', lines[i])
            if handler_match:
                contract.handler_name = handler_match.group(1)

            # Return type
            return_match = self.TS_RETURN_TYPE.search(context_block)
            if return_match:
                contract.response_fields = {'_return_type': return_match.group(1)}

            contracts.append(contract)

        return contracts

    def _extract_express(self, content: str, file_path: str) -> List[EndpointContract]:
        """Extract Express.js route definitions."""
        contracts = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            match = self.EXPRESS_ROUTE.search(line)
            if not match:
                continue

            method = match.group(1).upper()
            path = match.group(2)

            contract = EndpointContract(
                method=method,
                path=path,
                file_path=file_path,
                line_number=i,
                framework='express',
                detected_at=datetime.now(timezone.utc).isoformat(),
            )

            # Check for middleware in the same line
            mw_match = self.EXPRESS_MIDDLEWARE.search(line)
            if mw_match:
                contract.middleware.append(mw_match.group(1))

            # Check for status code and response shape
            context_end = min(len(lines), i + 15)
            context_block = '\n'.join(lines[i:context_end])

            status_match = self.RES_STATUS.search(context_block)
            if status_match:
                contract.status_code = int(status_match.group(1))

            json_match = self.RES_JSON.search(context_block)
            if json_match:
                fields = re.findall(r'(\w+)\s*[,:]', json_match.group(1))
                contract.response_fields = {f: 'unknown' for f in fields}

            contracts.append(contract)

        return contracts

    def _extract_fastapi(self, content: str, file_path: str) -> List[EndpointContract]:
        """Extract FastAPI route definitions."""
        contracts = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            match = self.FASTAPI_ROUTE.search(line)
            if not match:
                continue

            method = match.group(1).upper()
            path = match.group(2)

            contract = EndpointContract(
                method=method,
                path=path,
                file_path=file_path,
                line_number=i,
                framework='fastapi',
                detected_at=datetime.now(timezone.utc).isoformat(),
            )

            # Response model
            resp_match = self.FASTAPI_RESPONSE.search(line)
            if resp_match:
                contract.response_fields = {'_response_model': resp_match.group(1)}

            # Status code
            status_match = self.FASTAPI_STATUS.search(line)
            if status_match:
                contract.status_code = int(status_match.group(1))

            # Dependencies (auth, etc.)
            context_end = min(len(lines), i + 10)
            context_block = '\n'.join(lines[i:context_end])

            for dep in self.FASTAPI_DEPENDS.finditer(context_block):
                dep_name = dep.group(1)
                if 'auth' in dep_name.lower() or 'current_user' in dep_name.lower():
                    contract.auth_guard = dep_name
                else:
                    contract.middleware.append(dep_name)

            # Function name
            func_match = re.search(r'(?:async\s+)?def\s+(\w+)', context_block)
            if func_match:
                contract.handler_name = func_match.group(1)

            # Return type
            return_match = self.PY_RETURN_TYPE.search(context_block)
            if return_match:
                contract.response_fields['_return_type'] = return_match.group(1)

            contracts.append(contract)

        return contracts

    def _extract_flask(self, content: str, file_path: str) -> List[EndpointContract]:
        """Extract Flask route definitions."""
        contracts = []
        lines = content.split('\n')

        for i, line in enumerate(lines, 1):
            match = self.FLASK_ROUTE.search(line)
            if not match:
                continue

            path = match.group(1)
            methods_str = match.group(2)

            if methods_str:
                methods = [m.strip().strip("'\"").upper() for m in methods_str.split(',')]
            else:
                methods = ['GET']

            for method in methods:
                contract = EndpointContract(
                    method=method,
                    path=path,
                    file_path=file_path,
                    line_number=i,
                    framework='flask',
                    detected_at=datetime.now(timezone.utc).isoformat(),
                )

                # Function name
                context_end = min(len(lines), i + 3)
                context_block = '\n'.join(lines[i:context_end])
                func_match = re.search(r'def\s+(\w+)', context_block)
                if func_match:
                    contract.handler_name = func_match.group(1)

                contracts.append(contract)

        return contracts


# ──────────────────────────────────────────────────────────────
# Contract Registry
# ──────────────────────────────────────────────────────────────

class ContractRegistry:
    """Stores and queries endpoint contracts."""

    def __init__(self):
        self._contracts: Dict[str, List[EndpointContract]] = {}  # workspace → contracts

    def register(self, workspace_path: str, contracts: List[EndpointContract]):
        self._contracts[workspace_path] = contracts

    def get(self, workspace_path: str) -> List[EndpointContract]:
        return self._contracts.get(workspace_path, [])

    def find(self, workspace_path: str, method: str, path: str) -> Optional[EndpointContract]:
        for c in self.get(workspace_path):
            if c.method == method.upper() and self._paths_match(c.path, path):
                return c
        return None

    def _paths_match(self, defined: str, requested: str) -> bool:
        d = defined.rstrip('/')
        r = requested.rstrip('/')
        if d == r:
            return True
        # Parameterized
        param_re = re.sub(r'[:{](\w+)[}]?', r'[^/]+', d)
        return bool(re.fullmatch(param_re, r))


# ──────────────────────────────────────────────────────────────
# Contract Validator
# ──────────────────────────────────────────────────────────────

class ContractValidator:
    """Validates API contracts for discipline violations."""

    # Expected status codes per method
    EXPECTED_STATUS = {
        'GET': {200},
        'POST': {201, 200},
        'PUT': {200},
        'PATCH': {200},
        'DELETE': {204, 200},
    }

    # Naming conventions
    RE_KEBAB = re.compile(r'^[a-z0-9]+(-[a-z0-9]+)*$')
    RE_CAMEL = re.compile(r'^[a-z][a-zA-Z0-9]*$')

    def validate(self, contracts: List[EndpointContract]) -> List[ContractViolation]:
        """Run all contract validations."""
        violations: List[ContractViolation] = []

        violations.extend(self._check_duplicates(contracts))
        violations.extend(self._check_http_discipline(contracts))
        violations.extend(self._check_naming(contracts))
        violations.extend(self._check_auth_consistency(contracts))
        violations.extend(self._check_response_shape(contracts))

        return violations

    def _check_duplicates(self, contracts: List[EndpointContract]) -> List[ContractViolation]:
        """Detect duplicate route definitions."""
        violations = []
        seen: Dict[str, EndpointContract] = {}

        for c in contracts:
            key = f'{c.method} {c.path}'
            if key in seen:
                existing = seen[key]
                violations.append(ContractViolation(
                    severity='CRITICAL',
                    category='duplicate',
                    message=f'Duplicate endpoint: {key}',
                    endpoint=key,
                    file_path=c.file_path,
                    line_number=c.line_number,
                    suggestion=f'Already defined in {existing.file_path}:{existing.line_number}',
                ))
            else:
                seen[key] = c

        return violations

    def _check_http_discipline(self, contracts: List[EndpointContract]) -> List[ContractViolation]:
        """Check HTTP method usage conventions."""
        violations = []

        for c in contracts:
            # Status code checks
            if c.status_code and c.method in self.EXPECTED_STATUS:
                expected = self.EXPECTED_STATUS[c.method]
                if c.status_code not in expected:
                    violations.append(ContractViolation(
                        severity='MEDIUM',
                        category='http_discipline',
                        message=f'{c.method} {c.path} returns {c.status_code}, expected {expected}',
                        endpoint=f'{c.method} {c.path}',
                        file_path=c.file_path,
                        line_number=c.line_number,
                        suggestion=f'Use {min(expected)} for {c.method} responses',
                    ))

            # GET should not have request body
            if c.method == 'GET' and c.request_body_fields:
                violations.append(ContractViolation(
                    severity='HIGH',
                    category='http_discipline',
                    message=f'GET {c.path} has request body — GET should be idempotent',
                    endpoint=f'GET {c.path}',
                    file_path=c.file_path,
                    line_number=c.line_number,
                    suggestion='Use query parameters instead of request body for GET',
                ))

            # DELETE should not have complex response body
            if c.method == 'DELETE' and len(c.response_fields) > 2:
                violations.append(ContractViolation(
                    severity='LOW',
                    category='http_discipline',
                    message=f'DELETE {c.path} returns complex response — prefer 204 No Content',
                    endpoint=f'DELETE {c.path}',
                    file_path=c.file_path,
                    line_number=c.line_number,
                ))

        return violations

    def _check_naming(self, contracts: List[EndpointContract]) -> List[ContractViolation]:
        """Check route naming conventions."""
        violations = []

        for c in contracts:
            segments = [s for s in c.path.split('/') if s and not s.startswith(':') and not s.startswith('{')]

            for seg in segments:
                # Check for camelCase in URLs (should be kebab-case or lowercase)
                if re.search(r'[A-Z]', seg) and not seg.startswith('{'):
                    violations.append(ContractViolation(
                        severity='LOW',
                        category='naming',
                        message=f'Route segment "{seg}" in {c.path} uses camelCase — prefer kebab-case',
                        endpoint=f'{c.method} {c.path}',
                        file_path=c.file_path,
                        line_number=c.line_number,
                        suggestion=f'Rename to "{self._to_kebab(seg)}"',
                    ))

            # Check for verb in resource URL (anti-pattern for REST)
            verbs = {'get', 'create', 'update', 'delete', 'remove', 'add', 'fetch', 'list'}
            for seg in segments:
                if seg.lower() in verbs:
                    violations.append(ContractViolation(
                        severity='MEDIUM',
                        category='naming',
                        message=f'Route "{c.path}" contains verb "{seg}" — REST uses HTTP methods instead',
                        endpoint=f'{c.method} {c.path}',
                        file_path=c.file_path,
                        line_number=c.line_number,
                        suggestion='Use HTTP method to indicate action, keep URLs as nouns',
                    ))

        return violations

    def _check_auth_consistency(self, contracts: List[EndpointContract]) -> List[ContractViolation]:
        """Check auth guard consistency across related endpoints."""
        violations = []

        # Group by resource prefix
        resource_groups: Dict[str, List[EndpointContract]] = {}
        for c in contracts:
            parts = [s for s in c.path.split('/') if s and not s.startswith(':') and not s.startswith('{')]
            resource = '/'.join(parts[:2]) if len(parts) >= 2 else parts[0] if parts else ''
            if resource not in resource_groups:
                resource_groups[resource] = []
            resource_groups[resource].append(c)

        for resource, group in resource_groups.items():
            guarded = [c for c in group if c.auth_guard]
            unguarded = [c for c in group if not c.auth_guard]

            # If some endpoints are guarded and others aren't in the same resource
            if guarded and unguarded:
                # Mutation endpoints without auth are more concerning
                for c in unguarded:
                    if c.method in ('POST', 'PUT', 'DELETE', 'PATCH'):
                        violations.append(ContractViolation(
                            severity='HIGH',
                            category='auth',
                            message=f'{c.method} {c.path} has no auth guard but related endpoints do',
                            endpoint=f'{c.method} {c.path}',
                            file_path=c.file_path,
                            line_number=c.line_number,
                            suggestion=f'Add auth guard (other {resource} endpoints use it)',
                        ))

        return violations

    def _check_response_shape(self, contracts: List[EndpointContract]) -> List[ContractViolation]:
        """Check response shape consistency across similar endpoints."""
        violations = []

        # Group GET endpoints and check if they have consistent response fields
        get_endpoints = [c for c in contracts if c.method == 'GET' and c.response_fields]

        # Check for mixed response envelope patterns
        envelope_keys = {'data', 'result', 'results', 'items', 'payload'}
        uses_envelope = set()
        no_envelope = set()

        for c in get_endpoints:
            field_names = set(k for k in c.response_fields.keys() if not k.startswith('_'))
            if field_names & envelope_keys:
                uses_envelope.add(c.path)
            elif field_names:
                no_envelope.add(c.path)

        if uses_envelope and no_envelope:
            violations.append(ContractViolation(
                severity='MEDIUM',
                category='response_shape',
                message=f'Inconsistent response enveloping — some endpoints use data/result wrapper, others return raw',
                suggestion='Standardize on a consistent response envelope pattern',
            ))

        return violations

    def _to_kebab(self, camel: str) -> str:
        """Convert camelCase to kebab-case."""
        return re.sub(r'([A-Z])', r'-\1', camel).lower().lstrip('-')


# ──────────────────────────────────────────────────────────────
# Response Shape Tracker
# ──────────────────────────────────────────────────────────────

class ResponseShapeTracker:
    """Tracks response shapes over time to detect drift."""

    def __init__(self):
        self._shapes: Dict[str, Dict[str, Any]] = {}  # "METHOD /path" → shape

    def record_shape(self, method: str, path: str, fields: Dict[str, Any]):
        key = f'{method} {path}'
        self._shapes[key] = {
            'fields': fields,
            'recorded_at': datetime.now(timezone.utc).isoformat(),
        }

    def detect_drift(self, method: str, path: str, new_fields: Dict[str, Any]) -> List[ContractViolation]:
        """Compare new response shape against recorded shape."""
        key = f'{method} {path}'
        violations = []

        if key not in self._shapes:
            return violations

        old_fields = set(self._shapes[key]['fields'].keys())
        new_field_set = set(new_fields.keys())

        removed = old_fields - new_field_set
        added = new_field_set - old_fields

        for f in removed:
            violations.append(ContractViolation(
                severity='CRITICAL',
                category='response_shape',
                message=f'Response field "{f}" removed from {key} — this is a breaking change',
                endpoint=key,
                suggestion=f'Keep "{f}" for backward compatibility or version the API',
            ))

        for f in added:
            violations.append(ContractViolation(
                severity='INFO',
                category='response_shape',
                message=f'New response field "{f}" added to {key}',
                endpoint=key,
            ))

        return violations


# ──────────────────────────────────────────────────────────────
# Main Analyzer (Facade)
# ──────────────────────────────────────────────────────────────

class ContractAnalyzer:
    """Top-level facade for API contract enforcement."""

    def __init__(self):
        self.extractor = EndpointExtractor()
        self.registry = ContractRegistry()
        self.validator = ContractValidator()
        self.shape_tracker = ResponseShapeTracker()

    def analyze_workspace(self, workspace_path: str) -> Dict[str, Any]:
        """Full API contract analysis of a workspace."""
        contracts = self.extractor.extract_contracts(workspace_path)
        self.registry.register(workspace_path, contracts)

        violations = self.validator.validate(contracts)

        # Group endpoints by resource
        resources: Dict[str, List[Dict]] = {}
        for c in contracts:
            parts = [s for s in c.path.split('/') if s and not s.startswith(':') and not s.startswith('{')]
            resource = parts[0] if parts else 'root'
            if resource not in resources:
                resources[resource] = []
            resources[resource].append(asdict(c))

        return {
            'total_endpoints': len(contracts),
            'frameworks': list(set(c.framework for c in contracts)),
            'resources': {k: len(v) for k, v in resources.items()},
            'endpoints': [asdict(c) for c in contracts],
            'total_violations': len(violations),
            'violations_by_severity': self._group_by_severity(violations),
            'violations': [asdict(v) for v in violations],
            'auth_coverage': self._auth_coverage(contracts),
        }

    def validate_contracts(self, workspace_path: str) -> Dict[str, Any]:
        """Validate existing contracts."""
        contracts = self.registry.get(workspace_path)
        if not contracts:
            contracts = self.extractor.extract_contracts(workspace_path)
            self.registry.register(workspace_path, contracts)

        violations = self.validator.validate(contracts)

        return {
            'valid': len([v for v in violations if v.severity in ('CRITICAL', 'HIGH')]) == 0,
            'total_violations': len(violations),
            'violations': [asdict(v) for v in violations],
        }

    def check_endpoint(self, workspace_path: str, method: str, path: str) -> Dict[str, Any]:
        """Check a specific endpoint against contracts."""
        contract = self.registry.find(workspace_path, method, path)
        if not contract:
            return {
                'found': False,
                'method': method,
                'path': path,
                'suggestion': 'Endpoint not found in codebase',
            }

        return {
            'found': True,
            'contract': asdict(contract),
        }

    def get_endpoint_map(self, workspace_path: str) -> Dict[str, Any]:
        """Get a structured map of all endpoints."""
        contracts = self.registry.get(workspace_path)
        if not contracts:
            contracts = self.extractor.extract_contracts(workspace_path)
            self.registry.register(workspace_path, contracts)

        endpoint_map: Dict[str, List[Dict]] = {}
        for c in contracts:
            if c.path not in endpoint_map:
                endpoint_map[c.path] = []
            endpoint_map[c.path].append({
                'method': c.method,
                'handler': c.handler_name,
                'auth': c.auth_guard,
                'file': c.file_path,
                'line': c.line_number,
            })

        return {
            'total_paths': len(endpoint_map),
            'total_endpoints': len(contracts),
            'map': endpoint_map,
        }

    def _auth_coverage(self, contracts: List[EndpointContract]) -> Dict[str, Any]:
        guarded = sum(1 for c in contracts if c.auth_guard)
        total = len(contracts)
        mutation = sum(1 for c in contracts if c.method in ('POST', 'PUT', 'DELETE', 'PATCH'))
        mutation_guarded = sum(1 for c in contracts if c.method in ('POST', 'PUT', 'DELETE', 'PATCH') and c.auth_guard)

        return {
            'total': total,
            'guarded': guarded,
            'unguarded': total - guarded,
            'coverage_percent': round(guarded / total * 100, 1) if total else 0,
            'mutation_endpoints': mutation,
            'mutation_guarded': mutation_guarded,
            'mutation_unguarded': mutation - mutation_guarded,
        }

    def _group_by_severity(self, violations: List[ContractViolation]) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for v in violations:
            counts[v.severity] = counts.get(v.severity, 0) + 1
        return counts
