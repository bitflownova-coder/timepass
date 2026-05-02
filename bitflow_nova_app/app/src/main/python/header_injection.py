# header_injection.py
# CRLF Injection & Host Header Injection Detection

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
        return httpx.Client(timeout=timeout, follow_redirects=True, verify=False)
    VERIFY_SSL = False

# CRLF payloads to inject in URL query parameters
CRLF_PAYLOADS = [
    '%0d%0aX-Injected-Header: crlf-test',       # Standard CRLF
    '%0aX-Injected-Header: lf-test',             # LF only
    '%0d%0a%20X-Injected-Header: crlf-space',    # With space
    '%E5%98%8D%E5%98%8AX-Injected-Header: utf',  # UTF-8 encoded CRLF
    '\r\nX-Injected-Header: raw-crlf',
]

INJECTION_MARKER = 'X-Injected-Header'


def test_crlf_injection(base_url):
    """
    Test for CRLF injection vulnerabilities by injecting CRLF sequences
    into URL parameters and checking if the injected header appears in the response.
    """
    if not httpx:
        return {'error': 'httpx not available', 'crlf_findings': [], 'host_header_findings': []}

    crlf_findings = []
    host_header_findings = []

    parsed = urlparse(base_url)

    # 1. CRLF Injection — test path and query string
    test_targets = [
        base_url,
        urljoin(base_url, '/login'),
        urljoin(base_url, '/redirect'),
        urljoin(base_url, '/search'),
    ]

    for target in test_targets:
        for payload in CRLF_PAYLOADS:
            try:
                # Inject in query parameter (param=VALUE)
                test_url = f"{target}?q={payload}"
                with make_client(timeout=8, follow_redirects=False, verify=VERIFY_SSL, rate_limit=True) as client:
                    r = client.get(test_url)

                # Check if the injected header appears in the response
                if INJECTION_MARKER.lower() in str(r.headers).lower():
                    crlf_findings.append({
                        'url': target,
                        'payload': payload,
                        'injected_header': INJECTION_MARKER,
                        'severity': 'High',
                        'type': 'CRLF Injection',
                        'description': 'Server reflected CRLF-injected header in response',
                    })
                    break  # One confirmed per URL is enough

                # Also check response body for reflection
                if INJECTION_MARKER in r.text[:4000]:
                    crlf_findings.append({
                        'url': target,
                        'payload': payload,
                        'injected_header': INJECTION_MARKER,
                        'severity': 'Medium',
                        'type': 'CRLF Injection (body reflection)',
                        'description': 'CRLF payload reflected in response body',
                    })
                    break

            except Exception:
                pass

    # 2. Host Header Injection
    try:
        evil_host = 'evil.attacker-test.com'
        with make_client(timeout=8, follow_redirects=True, verify=VERIFY_SSL, rate_limit=True) as client:
            r = client.get(base_url, headers={'Host': evil_host})

        # Check if evil host appears in the response (location header, body links, etc.)
        body_sample = r.text[:8000]
        location = r.headers.get('location', '')
        if evil_host in body_sample or evil_host in location:
            host_header_findings.append({
                'url': base_url,
                'injected_host': evil_host,
                'severity': 'High',
                'type': 'Host Header Injection',
                'description': 'Injected Host header value reflected in response — possible cache poisoning or password reset poisoning',
                'reflected_in': 'location header' if evil_host in location else 'response body',
            })
    except Exception:
        pass

    # 3. X-Forwarded-Host injection
    try:
        with make_client(timeout=8, follow_redirects=True, verify=VERIFY_SSL, rate_limit=True) as client:
            r = client.get(base_url, headers={'X-Forwarded-Host': 'attacker-xfh.com'})
        if 'attacker-xfh.com' in r.text[:8000]:
            host_header_findings.append({
                'url': base_url,
                'injected_host': 'attacker-xfh.com',
                'severity': 'Medium',
                'type': 'X-Forwarded-Host Injection',
                'description': 'X-Forwarded-Host value reflected in response — possible cache poisoning vector',
                'reflected_in': 'response body',
            })
    except Exception:
        pass

    return {
        'crlf_findings': crlf_findings,
        'host_header_findings': host_header_findings,
        'total_issues': len(crlf_findings) + len(host_header_findings),
        'summary': (
            f"CRLF: {len(crlf_findings)} issues, "
            f"Host Header: {len(host_header_findings)} issues"
        ),
    }
