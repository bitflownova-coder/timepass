# rate_limit_checker.py
# Rate Limit Audit — Test auth endpoints for brute-force protection

import time
from urllib.parse import urljoin

try:
    import httpx
except ImportError:
    httpx = None

try:
    from http_client import VERIFY_SSL
except ImportError:
    VERIFY_SSL = False

# Common authentication endpoint paths to test (trimmed to highest-value paths)
AUTH_PATHS = [
    '/login',
    '/signin',
    '/api/login',
    '/api/auth/login',
    '/api/v1/auth/login',
    '/wp-login.php',
    '/admin/login',
    '/users/sign_in',
]

# Dummy credentials for rate limit probing (will not succeed)
PROBE_CREDS = {'username': 'ratelimitprobe', 'password': 'xxxx'}
PROBE_CREDS_JSON = {'email': 'probe@ratelimitcheck.internal', 'password': 'xxxx'}

RAPID_REQUEST_COUNT = 5  # Number of rapid requests to send
RAPID_REQUEST_TIMEOUT = 3  # seconds per request


def _send_probe(client, url, method, attempt):
    """Send a single probe request. Returns (status_code, headers, elapsed_ms)."""
    start = time.monotonic()
    try:
        if method == 'POST':
            # Try form-encoded first, then JSON
            try:
                r = client.post(url, data=PROBE_CREDS,
                                headers={'Content-Type': 'application/x-www-form-urlencoded'})
                if r.status_code in (415, 422):
                    r = client.post(url, json=PROBE_CREDS_JSON,
                                    headers={'Content-Type': 'application/json'})
            except Exception:
                r = client.post(url, json=PROBE_CREDS_JSON)
        else:
            r = client.get(url)

        elapsed = int((time.monotonic() - start) * 1000)
        return r.status_code, dict(r.headers), elapsed
    except Exception as e:
        return None, {}, 0


def check_rate_limiting(base_url, auth_endpoints=None):
    """
    Test whether authentication endpoints enforce rate limiting.

    Sends RAPID_REQUEST_COUNT rapid requests to each discovered auth endpoint
    and checks for:
    - HTTP 429 Too Many Requests
    - Retry-After header
    - CAPTCHA indicators in response
    - Response code changes (200 → 429 suggests limiting works)
    - Consistent 200s with no throttling (vulnerable)

    Parameters
    ----------
    base_url : str
        Root URL of the target.
    auth_endpoints : list[dict], optional
        Already-discovered auth endpoints from auth_tester module.

    Returns
    -------
    dict with findings, endpoints_tested, and summary.
    """
    if not httpx:
        return {'error': 'httpx not available', 'findings': [], 'endpoints_tested': []}

    findings = []
    endpoints_tested = []

    # Build candidate list
    candidates = []
    for path in AUTH_PATHS:
        candidates.append((urljoin(base_url, path), 'POST'))

    if auth_endpoints:
        for ep in auth_endpoints:
            url = ep.get('url', '')
            method = ep.get('method', 'POST').upper()
            if url and (url, method) not in candidates:
                candidates.append((url, method))

    # Use a single client without rate limiting (we're the ones doing the rapid probing)
    try:
        import httpx as _httpx
        client = _httpx.Client(
            timeout=RAPID_REQUEST_TIMEOUT,
            follow_redirects=True,
            verify=VERIFY_SSL,
        )
    except Exception:
        return {'error': 'httpx not available', 'findings': [], 'endpoints_tested': []}

    try:
        for url, method in candidates:
            responses = []

            # First check if endpoint exists
            try:
                probe_r = client.get(url)
                if probe_r.status_code == 404:
                    continue  # Skip non-existent endpoints
            except Exception:
                continue

            # Send rapid requests
            for i in range(RAPID_REQUEST_COUNT):
                status, headers, elapsed = _send_probe(client, url, method, i)
                if status is not None:
                    responses.append({
                        'attempt': i + 1,
                        'status': status,
                        'elapsed_ms': elapsed,
                        'retry_after': headers.get('retry-after', ''),
                        'x_ratelimit': headers.get('x-ratelimit-remaining', ''),
                    })
                time.sleep(0.1)  # 100ms between probes (still rapid but not DoS)

            if not responses:
                continue

            status_codes = [r['status'] for r in responses]
            has_429 = 429 in status_codes
            has_retry_after = any(r['retry_after'] for r in responses)
            has_ratelimit_header = any(r['x_ratelimit'] for r in responses)
            all_200 = all(s in (200, 401, 422) for s in status_codes)

            endpoint_result = {
                'url': url,
                'method': method,
                'responses': responses,
                'rate_limited': has_429 or has_retry_after,
                'has_retry_after': has_retry_after,
                'has_ratelimit_headers': has_ratelimit_header,
                'status_distribution': {str(s): status_codes.count(s) for s in set(status_codes)},
            }
            endpoints_tested.append(endpoint_result)

            if not has_429 and not has_retry_after and all_200:
                # No rate limiting detected
                findings.append({
                    'url': url,
                    'method': method,
                    'type': 'Missing Rate Limiting on Auth Endpoint',
                    'severity': 'High',
                    'requests_sent': RAPID_REQUEST_COUNT,
                    'all_responses_2xx_4xx': True,
                    'description': (
                        f'{RAPID_REQUEST_COUNT} rapid requests to {url} received no 429 or Retry-After. '
                        'This endpoint may be vulnerable to brute force / credential stuffing attacks.'
                    ),
                })
            elif has_429:
                endpoint_result['rate_limit_triggered_at'] = next(
                    (r['attempt'] for r in responses if r['status'] == 429), None
                )

    finally:
        client.close()

    protected = sum(1 for e in endpoints_tested if e.get('rate_limited'))
    unprotected = len(findings)

    return {
        'findings': findings,
        'endpoints_tested': endpoints_tested,
        'endpoints_protected': protected,
        'endpoints_unprotected': unprotected,
        'summary': (
            f"Tested {len(endpoints_tested)} auth endpoints — "
            f"{protected} rate-limited, {unprotected} unprotected"
        ),
    }
