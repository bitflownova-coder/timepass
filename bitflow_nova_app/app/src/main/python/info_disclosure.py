# info_disclosure.py
# Information Disclosure Scanner — sensitive files, debug pages, source maps, security.txt

from urllib.parse import urljoin

try:
    import httpx
except ImportError:
    httpx = None

try:
    from http_client import make_client, VERIFY_SSL, PROBE_TIMEOUT
except ImportError:
    def make_client(timeout=8, **kw):
        import httpx
        return httpx.Client(timeout=timeout, follow_redirects=False, verify=False)
    VERIFY_SSL = False
    PROBE_TIMEOUT = 8

# Sensitive paths to probe and what they indicate
SENSITIVE_PATHS = [
    # Environment & Config files
    ('/.env',                   'Environment variables file',              'Critical'),
    ('/.env.local',             'Local environment variables file',        'Critical'),
    ('/.env.production',        'Production environment variables file',   'Critical'),
    ('/.env.staging',           'Staging environment variables file',      'High'),
    ('/config.php',             'PHP configuration file',                  'High'),
    ('/wp-config.php',          'WordPress configuration (DB credentials)','Critical'),
    ('/config.json',            'JSON configuration file',                 'High'),
    ('/config.yml',             'YAML configuration file',                 'High'),
    ('/settings.py',            'Python settings file',                    'High'),
    ('/database.yml',           'Database configuration file',             'High'),
    ('/credentials.json',       'Credentials file',                        'Critical'),
    ('/secrets.json',           'Secrets file',                            'Critical'),

    # VCS artifacts
    ('/.git/config',            'Git repository config (may expose remote URL / creds)', 'High'),
    ('/.git/HEAD',              'Git HEAD file (confirms .git exposure)',   'High'),
    ('/.gitignore',             'Git ignore file (reveals file structure)', 'Low'),
    ('/.svn/entries',           'SVN repository entries',                  'High'),
    ('/.hg/hgrc',               'Mercurial config',                        'High'),

    # PHP debugging / info
    ('/phpinfo.php',            'PHP info page (full server config)',       'High'),
    ('/info.php',               'PHP info page variant',                   'High'),
    ('/php_info.php',           'PHP info page variant',                   'High'),
    ('/test.php',               'PHP test page',                           'Medium'),

    # Server status / monitoring
    ('/server-status',          'Apache server status (mod_status)',        'Medium'),
    ('/server-info',            'Apache server info',                      'Medium'),
    ('/.well-known/security.txt', 'Security contact disclosure',           'Info'),
    ('/health',                 'Health check endpoint',                   'Info'),
    ('/actuator',               'Spring Boot Actuator (sensitive metrics)','High'),
    ('/actuator/env',           'Spring Boot env variables',               'Critical'),
    ('/actuator/heapdump',      'JVM heap dump',                           'Critical'),
    ('/metrics',                'Application metrics',                     'Low'),
    ('/debug',                  'Debug endpoint',                          'Medium'),
    ('/console',                'Admin/debug console',                     'High'),
    ('/elmah.axd',              '.NET ELMAH error log',                    'High'),
    ('/trace.axd',              '.NET trace page',                         'High'),

    # Backup & Archive files
    ('/backup.zip',             'Backup archive',                          'Critical'),
    ('/backup.sql',             'Database backup',                         'Critical'),
    ('/dump.sql',               'Database dump',                           'Critical'),
    ('/db.sql',                 'Database file',                           'Critical'),

    # Package management (can reveal dependencies & versions)
    ('/package.json',           'Node.js package manifest',                'Low'),
    ('/composer.json',          'PHP Composer manifest',                   'Low'),
    ('/Gemfile',                'Ruby Gemfile',                            'Low'),
    ('/requirements.txt',       'Python requirements',                     'Low'),
]

# Source map extensions — flag .js.map files served publicly
SOURCE_MAP_SUFFIXES = ['.js.map', '.css.map', '.map']

# SQL error patterns in HTML that indicate error disclosure
SQL_ERROR_PATTERNS = [
    r'SQL syntax.*MySQL',
    r'Warning.*mysql_',
    r'MySqlException',
    r'ORA-\d{5}',
    r'PG::\w+Error',
    r'PostgreSQL.*ERROR',
    r'SQLSTATE\[',
    r'Microsoft.*ODBC.*SQL Server',
    r'Unclosed quotation mark',
    r'SqlException',
    r'Traceback \(most recent call last\)',  # Python stack trace
    r'ActiveRecord::',                        # Rails
]

import re
SQL_ERROR_RE = re.compile('|'.join(SQL_ERROR_PATTERNS), re.IGNORECASE)


def scan_info_disclosure(base_url, all_pages=None):
    """
    Probe for sensitive files/paths and check existing crawled pages for
    SQL error and stack trace disclosures.

    Parameters
    ----------
    base_url : str
        Root URL to probe.
    all_pages : list[dict], optional
        Already-crawled pages to check for error disclosures.

    Returns
    -------
    dict with findings list, security_txt content if found, and summary.
    """
    if not httpx:
        return {'error': 'httpx not available', 'findings': []}

    findings = []
    security_txt = None

    with make_client(timeout=PROBE_TIMEOUT, follow_redirects=False, verify=VERIFY_SSL, rate_limit=True) as client:
        for path, description, severity in SENSITIVE_PATHS:
            url = urljoin(base_url, path)
            try:
                r = client.get(url)
                if r.status_code in (200, 206):
                    finding = {
                        'url': url,
                        'path': path,
                        'description': description,
                        'severity': severity,
                        'status_code': r.status_code,
                        'content_type': r.headers.get('content-type', ''),
                        'size_bytes': len(r.content),
                        'type': 'Sensitive File Exposed',
                    }

                    # For security.txt capture content safely
                    if path == '/.well-known/security.txt':
                        security_txt = r.text[:2000]
                        finding['severity'] = 'Info'
                        finding['content_preview'] = security_txt[:500]

                    # For .env files, redact values but note presence of keys
                    elif path.endswith('.env') or 'env' in path:
                        keys = [line.split('=')[0] for line in r.text.splitlines()
                                if '=' in line and not line.startswith('#')]
                        finding['env_keys_found'] = keys[:20]

                    findings.append(finding)

                elif r.status_code == 403:
                    # 403 = exists but forbidden — less severe but worth noting
                    if severity in ('Critical', 'High'):
                        findings.append({
                            'url': url,
                            'path': path,
                            'description': f'{description} (Access Forbidden — file exists)',
                            'severity': 'Low',
                            'status_code': 403,
                            'type': 'Sensitive Path (Forbidden)',
                        })

            except Exception:
                pass

    # Check crawled pages for source map leaks
    if all_pages:
        for page in all_pages:
            page_url = page.get('url', '')
            for suffix in SOURCE_MAP_SUFFIXES:
                if page_url.endswith(suffix):
                    findings.append({
                        'url': page_url,
                        'path': page_url,
                        'description': 'Source map file publicly accessible (reveals original source code)',
                        'severity': 'Medium',
                        'type': 'Source Map Exposed',
                    })

        # Check for SQL errors / stack traces in existing page content
        for page in all_pages:
            html = page.get('html', '') or ''
            if SQL_ERROR_RE.search(html[:10000]):
                match = SQL_ERROR_RE.search(html[:10000])
                findings.append({
                    'url': page.get('url', 'unknown'),
                    'path': '',
                    'description': f'Error disclosure: {match.group()[:80]}',
                    'severity': 'High',
                    'type': 'Error Information Disclosure',
                })

    critical = sum(1 for f in findings if f.get('severity') == 'Critical')
    high = sum(1 for f in findings if f.get('severity') == 'High')

    return {
        'findings': findings,
        'security_txt': security_txt,
        'total_issues': len(findings),
        'critical': critical,
        'high': high,
        'summary': (
            f"Found {len(findings)} information disclosure issues "
            f"({critical} critical, {high} high)"
        ),
    }
