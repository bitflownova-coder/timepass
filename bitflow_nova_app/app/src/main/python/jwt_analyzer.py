# jwt_analyzer.py
# JWT Token Analysis — Passive detection & security checks (zero extra HTTP requests)
# Analyzes tokens already found during the crawl (headers, cookies, JS files, response bodies)

import re
import json
import base64
from datetime import datetime

# Regex to find JWT-shaped strings: three Base64URL segments separated by dots
JWT_PATTERN = re.compile(
    r'\b(eyJ[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]+\.[A-Za-z0-9_\-]*)\b'
)

# Algorithms considered weak or dangerous
WEAK_ALGORITHMS = {'none', 'none ', 'NONE', 'HS256', 'HS384', 'HS512'}
NONE_ALGORITHMS = {'none', 'none ', 'NONE', ''}

# Sensitive claim keys to flag if present in payload
SENSITIVE_CLAIMS = {
    'password', 'passwd', 'pass', 'secret', 'token', 'key', 'api_key',
    'access_key', 'private_key', 'ssn', 'dob', 'credit_card', 'card_number',
    'cvv', 'internal_ip', 'db_pass', 'db_password', 'connection_string',
}


def _b64_decode(segment: str) -> dict | None:
    """Decode a Base64URL-encoded JWT segment into a dict."""
    try:
        # Pad to multiple of 4
        padded = segment + '=' * (-len(segment) % 4)
        decoded = base64.urlsafe_b64decode(padded).decode('utf-8', errors='replace')
        return json.loads(decoded)
    except Exception:
        return None


def _analyze_token(token: str, source: str) -> dict | None:
    """Decode and analyse a single JWT string. Returns a finding dict or None."""
    parts = token.split('.')
    if len(parts) != 3:
        return None

    header = _b64_decode(parts[0])
    payload = _b64_decode(parts[1])
    if not header or not payload:
        return None

    issues = []
    severity = 'Info'

    # 1. Algorithm check
    alg = header.get('alg', '').strip()
    if alg.lower() == 'none':
        issues.append({'issue': 'alg:none detected — signature verification disabled', 'severity': 'Critical'})
        severity = 'Critical'
    elif alg in ('', None):
        issues.append({'issue': 'Missing alg claim in JWT header', 'severity': 'High'})
        severity = 'High'
    elif alg.startswith('HS'):
        issues.append({
            'issue': f'Symmetric algorithm {alg} — if this JWT is server-to-client, the secret may be brute-forceable',
            'severity': 'Medium',
        })
        if severity not in ('Critical', 'High'):
            severity = 'Medium'

    # 2. Expiry check
    exp = payload.get('exp')
    iat = payload.get('iat')
    if exp is None:
        issues.append({'issue': 'No exp (expiry) claim — token never expires', 'severity': 'High'})
        if severity not in ('Critical',):
            severity = 'High'
    else:
        try:
            exp_dt = datetime.utcfromtimestamp(int(exp))
            now = datetime.utcnow()
            if exp_dt < now:
                issues.append({
                    'issue': f'Token expired at {exp_dt.isoformat()} UTC',
                    'severity': 'Low',
                })
        except Exception:
            pass

    if iat is None:
        issues.append({'issue': 'No iat (issued-at) claim', 'severity': 'Info'})

    # 3. Sensitive data in payload
    found_sensitive = [k for k in payload if k.lower() in SENSITIVE_CLAIMS]
    if found_sensitive:
        issues.append({
            'issue': f'Sensitive claims in payload: {", ".join(found_sensitive)}',
            'severity': 'High',
        })
        if severity not in ('Critical',):
            severity = 'High'

    # 4. Role/privilege claims
    role_claims = ['role', 'roles', 'scope', 'scopes', 'permissions', 'admin', 'is_admin', 'is_superuser']
    found_roles = {k: payload[k] for k in payload if k.lower() in role_claims}
    if found_roles:
        issues.append({
            'issue': f'Role/permission claims present: {list(found_roles.keys())} — verify claim validation is server-side',
            'severity': 'Medium',
        })

    if not issues:
        return None  # No findings, skip

    return {
        'token_preview': token[:40] + '...',
        'source': source,
        'algorithm': alg or 'MISSING',
        'subject': payload.get('sub', ''),
        'issuer': payload.get('iss', ''),
        'expiry': str(datetime.utcfromtimestamp(int(exp)).isoformat()) + ' UTC' if exp else 'NONE',
        'issues': issues,
        'severity': severity,
        'payload_claims': list(payload.keys()),
    }


def analyze_jwts(pages_data: list, extra_sources: dict | None = None) -> dict:
    """
    Scan already-crawled page data for JWTs and analyse them.

    Parameters
    ----------
    pages_data : list[dict]
        Each dict should have 'url', 'html', 'headers' (dict), 'cookies' (list of dicts).
    extra_sources : dict, optional
        Additional named string sources {'source_name': 'content'} to scan.

    Returns
    -------
    dict with findings list, unique_tokens count, and summary.
    """
    findings = []
    seen_tokens = set()

    def scan_text(text: str, source: str):
        for match in JWT_PATTERN.finditer(text or ''):
            token = match.group(1)
            if token in seen_tokens:
                continue
            seen_tokens.add(token)
            finding = _analyze_token(token, source)
            if finding:
                findings.append(finding)

    for page in (pages_data or []):
        url = page.get('url', 'unknown')
        # Scan response body
        scan_text(page.get('html', ''), f'body:{url}')
        # Scan response headers
        for hname, hval in (page.get('headers') or {}).items():
            scan_text(hval, f'header:{hname}:{url}')
        # Scan cookies
        for cookie in (page.get('cookies') or []):
            cval = cookie.get('value', '') if isinstance(cookie, dict) else str(cookie)
            scan_text(cval, f'cookie:{url}')

    for src_name, content in (extra_sources or {}).items():
        scan_text(content, src_name)

    critical = sum(1 for f in findings if f['severity'] == 'Critical')
    high = sum(1 for f in findings if f['severity'] == 'High')

    return {
        'findings': findings,
        'unique_tokens_analyzed': len(seen_tokens),
        'vulnerable_tokens': len(findings),
        'critical': critical,
        'high': high,
        'summary': (
            f"Analyzed {len(seen_tokens)} unique JWTs — "
            f"{len(findings)} with issues ({critical} critical, {high} high)"
        ),
    }
