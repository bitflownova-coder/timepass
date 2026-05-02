# redirect_tester.py
# Open Redirect Detection - test common redirect parameters for external URL injection

import re
from urllib.parse import urljoin, urlparse, urlencode, parse_qs, urlunparse

try:
    import httpx
except ImportError:
    httpx = None

try:
    from http_client import make_client, VERIFY_SSL
except ImportError:
    def make_client(timeout=10, **kw):
        import httpx
        return httpx.Client(timeout=timeout, follow_redirects=False, verify=False)
    VERIFY_SSL = False

# Redirect parameter names commonly found in web applications
REDIRECT_PARAMS = [
    'url', 'next', 'redirect', 'redirect_uri', 'redirect_url', 'return',
    'return_url', 'return_to', 'returnurl', 'returnto', 'goto', 'dest',
    'destination', 'rurl', 'target', 'link', 'to', 'from', 'out',
    'continue', 'page', 'view', 'path', 'callback', 'forward',
]

# Canary domain — not actually malicious, just detectable as external
CANARY_URL = 'https://canary.example.com/redirect-test'
CANARY_DOMAIN = 'canary.example.com'


def test_open_redirects(base_url, discovered_params=None):
    """
    Test the target for open redirect vulnerabilities.

    Parameters
    ----------
    base_url : str
        Root URL of the target.
    discovered_params : list[dict], optional
        Parameters already found by param_fuzzer (each dict has 'url', 'param', 'method').

    Returns
    -------
    dict with findings list and summary statistics.
    """
    if not httpx:
        return {'error': 'httpx not available', 'findings': [], 'tested': 0}

    findings = []
    tested = 0
    tested_combos = set()

    parsed = urlparse(base_url)
    target_domain = parsed.netloc

    def probe(url, param, method='GET'):
        nonlocal tested
        key = (url, param)
        if key in tested_combos:
            return
        tested_combos.add(key)
        tested += 1

        payloads = [
            CANARY_URL,
            f'//{CANARY_DOMAIN}',                    # Protocol-relative
            f'https://{CANARY_DOMAIN}',
            f'https://{CANARY_DOMAIN}%2F%2E%2E',     # Encoded variant
            f'https://%09{CANARY_DOMAIN}',            # Tab bypass
        ]
        for payload in payloads:
            try:
                test_url = _inject_param(url, param, payload, method)
                with make_client(timeout=8, follow_redirects=False, verify=VERIFY_SSL, rate_limit=True) as client:
                    if method == 'GET':
                        r = client.get(test_url)
                    else:
                        r = client.post(url, data={param: payload})

                # Check for redirect to our canary
                if r.status_code in (301, 302, 303, 307, 308):
                    location = r.headers.get('location', '')
                    if CANARY_DOMAIN in location or location.startswith(payload):
                        findings.append({
                            'url': url,
                            'param': param,
                            'method': method,
                            'payload': payload,
                            'redirect_to': location,
                            'status_code': r.status_code,
                            'severity': 'High',
                            'type': 'Open Redirect',
                        })
                        return  # One confirmed per param is enough

                # Check JS-based redirect in body
                body = r.text[:8000]
                if CANARY_DOMAIN in body:
                    findings.append({
                        'url': url,
                        'param': param,
                        'method': method,
                        'payload': payload,
                        'redirect_to': 'JavaScript-based redirect (body)',
                        'status_code': r.status_code,
                        'severity': 'Medium',
                        'type': 'Open Redirect (JS)',
                    })
                    return

            except Exception:
                pass

    # 1. Test base URL with all redirect param names
    for param in REDIRECT_PARAMS:
        probe(base_url, param)

    # 2. Test discovered params from param_fuzzer
    if discovered_params:
        for item in discovered_params[:30]:  # cap at 30
            if item.get('param') in REDIRECT_PARAMS:
                probe(item.get('url', base_url), item['param'], item.get('method', 'GET'))

    # 3. Test common redirect endpoint paths
    redirect_paths = ['/login', '/signin', '/logout', '/redirect', '/go', '/out', '/link']
    for path in redirect_paths:
        redirect_url = urljoin(base_url, path)
        for param in ['url', 'next', 'return', 'redirect']:
            probe(redirect_url, param)

    return {
        'findings': findings,
        'tested_params': tested,
        'vulnerable_count': len(findings),
        'summary': f"Tested {tested} redirect param combinations, found {len(findings)} potential open redirects",
    }


def _inject_param(url, param, value, method='GET'):
    """Inject a parameter into a URL."""
    parsed = urlparse(url)
    existing = parse_qs(parsed.query, keep_blank_values=True)
    existing[param] = [value]
    new_query = urlencode(existing, doseq=True)
    new_parsed = parsed._replace(query=new_query)
    return urlunparse(new_parsed)
