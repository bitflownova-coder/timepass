# sqli_detector.py
# SQL Injection Detection — passive error pattern matching + light active probing

import re
import time
from urllib.parse import urljoin, urlparse, urlencode, parse_qs, urlunparse
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import httpx
except ImportError:
    httpx = None

try:
    from http_client import make_client, VERIFY_SSL
except ImportError:
    def make_client(timeout=12, **kw):
        import httpx
        return httpx.Client(timeout=timeout, follow_redirects=True, verify=False)
    VERIFY_SSL = False

# SQL error patterns by database engine
SQL_ERROR_PATTERNS = {
    'MySQL': [
        r"you have an error in your sql syntax",
        r"warning: mysql_",
        r"mysql_num_rows\(\)",
        r"mysqli_",
        r"supplied argument is not a valid mysql",
        r"mysql_fetch_array\(\)",
        r"MySQL server version for the right syntax",
    ],
    'PostgreSQL': [
        r"pg::syntaxerror",
        r"postgresql.*error",
        r"pgerror",
        r"invalid input syntax for",
        r"unterminated quoted string at",
        r"syntax error at or near",
    ],
    'MSSQL': [
        r"microsoft.*odbc.*sql server",
        r"microsoft.*jet database engine",
        r"unclosed quotation mark",
        r"sqlexception",
        r"sqlserver.*error",
        r"\[microsoft\]\[odbc",
    ],
    'Oracle': [
        r"ora-\d{5}",
        r"oracle.*driver",
        r"oracle.*error",
        r"quoted string not properly terminated",
        r"pl\/sql.*numeric or value error",
    ],
    'SQLite': [
        r"sqlite3::exception",
        r"sqlite.*error",
        r"unrecognized token",
    ],
    'Generic': [
        r"sql syntax",
        r"syntax error.*sql",
        r"invalid sql",
        r"sqlstate\[",
        r"database error",
        r"db query failed",
        r"odbc.*error",
    ],
}

# Compile all patterns (case-insensitive)
_ALL_PATTERNS = [(db, re.compile('|'.join(pats), re.IGNORECASE))
                 for db, pats in SQL_ERROR_PATTERNS.items()]

# Light active payloads — minimal, non-destructive
ACTIVE_PAYLOADS = [
    ("'",              "Single quote — basic syntax probe"),
    ('"',              "Double quote — basic syntax probe"),
    ("' OR '1'='1",    "Classic OR injection"),
    ("1 AND 1=2--",    "Boolean false probe"),
]

# Time-based probe (only used if initial probes suggest injection point)
TIME_PAYLOAD = ("'; WAITFOR DELAY '0:0:3'--", "MSSQL time-based", 3)

MAX_PARAMS_TO_TEST = 15  # Cap to avoid too many requests


def _get_baseline_time(client, url, method='GET', data=None):
    """Measure baseline response time for a request."""
    try:
        start = time.monotonic()
        if method == 'POST':
            r = client.post(url, data=data or {})
        else:
            r = client.get(url)
        elapsed = time.monotonic() - start
        return elapsed, r.status_code
    except Exception:
        return None, None


def _check_sql_errors(text):
    """Return (db_engine, matched_pattern) if SQL errors found, else None."""
    for db, pattern in _ALL_PATTERNS:
        m = pattern.search(text[:20000])
        if m:
            return db, m.group()[:80]
    return None, None


def _inject_param(url, param_name, value):
    """Return URL with param_name set to value."""
    parsed = urlparse(url)
    params = parse_qs(parsed.query, keep_blank_values=True)
    params[param_name] = [value]
    return urlunparse(parsed._replace(query=urlencode(params, doseq=True)))


def detect_sqli(base_url, discovered_params=None, all_pages=None):
    """
    Detect SQL injection vulnerabilities.

    Strategy:
    1. Passive: check already-crawled page content for SQL error patterns.
    2. Light active: inject minimal payloads into discovered URL parameters;
       check response for SQL errors.

    Parameters
    ----------
    base_url : str
        Root URL.
    discovered_params : list[dict], optional
        Parameters from param_fuzzer. Each: {'url', 'param', 'method', 'value'}.
    all_pages : list[dict], optional
        Crawled pages with 'url' and 'html'.

    Returns
    -------
    dict with findings, passive_hits, active_hits, tested count.
    """
    if not httpx:
        return {'error': 'httpx not available', 'findings': []}

    findings = []
    passive_hits = 0
    active_hits = 0
    tested_params = 0
    seen_urls = set()

    # 1. Passive scan — SQL errors in existing page responses
    for page in (all_pages or []):
        html = page.get('html', '') or ''
        db, snippet = _check_sql_errors(html)
        if db:
            passive_hits += 1
            findings.append({
                'url': page.get('url', 'unknown'),
                'param': None,
                'type': 'SQL Error Disclosure (Passive)',
                'db_engine': db,
                'snippet': snippet,
                'severity': 'High',
                'method': 'Passive',
                'description': f'{db} error visible in page — SQL injection may already be triggerable',
            })

    # 2. Active — test discovered parameters
    params_to_test = (discovered_params or [])[:MAX_PARAMS_TO_TEST]

    with make_client(timeout=12, follow_redirects=True, verify=VERIFY_SSL, rate_limit=True) as client:
        for item in params_to_test:
            url = item.get('url', base_url)
            param = item.get('param', '')
            method = item.get('method', 'GET').upper()
            if not param:
                continue

            tested_params += 1
            baseline_time, _ = _get_baseline_time(
                client, _inject_param(url, param, 'test') if method == 'GET' else url,
                method, {param: 'test'} if method == 'POST' else None
            )

            for payload, desc in ACTIVE_PAYLOADS:
                try:
                    if method == 'GET':
                        test_url = _inject_param(url, param, payload)
                        r = client.get(test_url)
                    else:
                        r = client.post(url, data={param: payload})

                    db, snippet = _check_sql_errors(r.text)
                    if db:
                        active_hits += 1
                        finding = {
                            'url': url,
                            'param': param,
                            'method': method,
                            'payload': payload,
                            'payload_description': desc,
                            'type': 'SQL Injection (Error-based)',
                            'db_engine': db,
                            'snippet': snippet,
                            'severity': 'Critical',
                            'description': (
                                f'{db} SQL error triggered with payload "{payload}" on '
                                f'parameter "{param}" — likely injectable'
                            ),
                        }
                        findings.append(finding)
                        break  # One confirmed per param

                    # Time-based: only if baseline is known and payload differs significantly
                    if baseline_time and method == 'GET' and db is None:
                        # Only test MSSQL time-based payload once per param
                        pass  # Time-based omitted to keep requests minimal

                except Exception:
                    pass

    critical = sum(1 for f in findings if f.get('severity') == 'Critical')
    return {
        'findings': findings,
        'passive_hits': passive_hits,
        'active_hits': active_hits,
        'params_tested': tested_params,
        'critical': critical,
        'summary': (
            f"Tested {tested_params} params + {len(all_pages or [])} pages passively. "
            f"Found {len(findings)} SQLi indicators ({critical} critical)"
        ),
    }
