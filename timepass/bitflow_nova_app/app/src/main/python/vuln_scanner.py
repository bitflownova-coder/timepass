# vuln_scanner.py
# Vulnerability Detection - CORS, HTTP Methods, Headers, Error Analysis

import re
from urllib.parse import urlparse, urljoin, parse_qs
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import httpx
except ImportError:
    httpx = None

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

# WAF/CDN detection signatures
WAF_SIGNATURES = {
    'cloudflare': {
        'headers': ['cf-ray', 'cf-cache-status', 'cf-request-id'],
        'cookies': ['__cfduid', 'cf_clearance'],
        'server': ['cloudflare']
    },
    'akamai': {
        'headers': ['x-akamai-request-id', 'akamai-origin-hop'],
        'server': ['akamaighost', 'akamai']
    },
    'aws_cloudfront': {
        'headers': ['x-amz-cf-id', 'x-amz-cf-pop'],
        'server': ['cloudfront']
    },
    'aws_waf': {
        'headers': ['x-amzn-requestid'],
        'server': []
    },
    'sucuri': {
        'headers': ['x-sucuri-id', 'x-sucuri-cache'],
        'server': ['sucuri']
    },
    'imperva': {
        'headers': ['x-iinfo'],
        'cookies': ['incap_ses', 'visid_incap']
    },
    'f5_bigip': {
        'headers': ['x-wa-info'],
        'cookies': ['bigipserver', 'ts']
    },
    'modsecurity': {
        'server': ['mod_security', 'modsecurity'],
        'headers': []
    },
    'wordfence': {
        'headers': ['x-wordfence-protection'],
        'cookies': ['wfvt_']
    },
    'fastly': {
        'headers': ['x-fastly-request-id', 'fastly-stats'],
        'server': ['fastly']
    }
}

# HTTP methods to test
DANGEROUS_METHODS = ['TRACE', 'PUT', 'DELETE', 'PATCH', 'OPTIONS', 'CONNECT']

# Open redirect parameters
REDIRECT_PARAMS = [
    'redirect', 'redirect_uri', 'redirect_url', 'next', 'url', 'return',
    'return_to', 'returnTo', 'goto', 'target', 'destination', 'redir',
    'continue', 'return_path', 'out', 'view', 'ref', 'callback', 'to',
    'forward', 'location', 'uri', 'u', 'r'
]

# Subdomain takeover fingerprints
TAKEOVER_FINGERPRINTS = {
    'heroku': ['no such app', 'there is no app configured at that hostname'],
    'github_pages': ["there isn't a github pages site here", 'is not a github pages site'],
    'aws_s3': ['nosuchbucket', 'the specified bucket does not exist'],
    'shopify': ['sorry, this shop is currently unavailable'],
    'tumblr': ["there's nothing here", 'whatever you were looking for'],
    'wordpress': ['do you want to register'],
    'azure': ['404 web site not found', 'the resource you are looking for has been removed'],
    'bitbucket': ['repository not found'],
    'ghost': ['the thing you were looking for is no longer here'],
    'pantheon': ['404 - unknown site'],
    'zendesk': ['help center closed'],
    'surge': ['project not found'],
    'readme': ['project not found'],
    'cargo': ['404 not found'],
}


def test_cors_misconfiguration(url, user_agent='Mozilla/5.0'):
    """Test for CORS misconfigurations"""
    findings = []
    
    if not httpx:
        return findings
    
    parsed = urlparse(url)
    base_domain = parsed.netloc
    
    # Test origins
    test_origins = [
        'https://evil.com',
        'null',
        f'https://subdomain.{base_domain}',
        f'https://{base_domain}.evil.com',
        f'https://evil{base_domain}',
    ]
    
    for origin in test_origins:
        try:
            with httpx.Client(timeout=5, follow_redirects=True, verify=False) as client:
                headers = {
                    'User-Agent': user_agent,
                    'Origin': origin
                }
                response = client.get(url, headers=headers)
                
                acao = response.headers.get('access-control-allow-origin', '')
                acac = response.headers.get('access-control-allow-credentials', '').lower()
                
                if acao:
                    # Wildcard with credentials
                    if acao == '*' and acac == 'true':
                        findings.append({
                            'issue': 'CORS allows any origin with credentials',
                            'severity': 'Critical',
                            'origin_tested': origin,
                            'acao': acao,
                            'acac': acac,
                            'description': 'Any website can make authenticated requests'
                        })
                    # Origin reflection
                    elif acao == origin and origin not in ['null', f'https://{base_domain}']:
                        findings.append({
                            'issue': f'CORS reflects untrusted origin: {origin}',
                            'severity': 'Critical' if acac == 'true' else 'High',
                            'origin_tested': origin,
                            'acao': acao,
                            'acac': acac,
                            'description': 'Server reflects attacker-controlled origin'
                        })
                    # Null origin
                    elif acao == 'null':
                        findings.append({
                            'issue': 'CORS allows null origin',
                            'severity': 'High',
                            'origin_tested': origin,
                            'acao': acao,
                            'description': 'Sandboxed iframes can make requests'
                        })
                    # Wildcard
                    elif acao == '*':
                        findings.append({
                            'issue': 'CORS allows any origin (wildcard)',
                            'severity': 'Medium',
                            'origin_tested': origin,
                            'acao': acao,
                            'description': 'Any website can read responses'
                        })
                        break  # No need to test more
        except:
            pass
    
    return findings


def test_http_methods(url, user_agent='Mozilla/5.0'):
    """Test for dangerous HTTP methods"""
    findings = []
    
    if not httpx:
        return findings
    
    # First, check OPTIONS to see allowed methods
    try:
        with httpx.Client(timeout=5, follow_redirects=False, verify=False) as client:
            response = client.options(url, headers={'User-Agent': user_agent})
            allowed = response.headers.get('allow', '')
            
            if allowed:
                methods = [m.strip().upper() for m in allowed.split(',')]
                for method in methods:
                    if method in DANGEROUS_METHODS:
                        severity = 'Critical' if method in ['PUT', 'DELETE'] else 'High' if method == 'TRACE' else 'Medium'
                        findings.append({
                            'issue': f'{method} method allowed',
                            'severity': severity,
                            'url': url,
                            'all_allowed': methods,
                            'description': get_method_risk_description(method)
                        })
    except:
        pass
    
    # Test TRACE specifically
    try:
        with httpx.Client(timeout=5, follow_redirects=False, verify=False) as client:
            response = client.request('TRACE', url, headers={'User-Agent': user_agent})
            if response.status_code == 200:
                findings.append({
                    'issue': 'TRACE method enabled',
                    'severity': 'High',
                    'url': url,
                    'status': 200,
                    'description': 'Cross-Site Tracing (XST) possible'
                })
    except:
        pass
    
    return findings


def get_method_risk_description(method):
    """Get risk description for HTTP method"""
    descriptions = {
        'TRACE': 'Cross-Site Tracing (XST) - can expose credentials',
        'PUT': 'Arbitrary file upload possible',
        'DELETE': 'Arbitrary file deletion possible',
        'PATCH': 'Unauthorized data modification possible',
        'OPTIONS': 'Information disclosure about allowed methods',
        'CONNECT': 'May allow proxy tunneling'
    }
    return descriptions.get(method, 'Potentially dangerous method')



def detect_waf(url_or_headers, cookies=None):
    """
    Detect WAF/CDN from URL or Headers
    Args:
        url_or_headers: URL string OR headers dict
        cookies: Cookies dict (optional, used if headers passed)
    """
    detected = []
    headers_lower = {}
    
    # helper to analyze headers
    def analyze_headers(headers, cookie_dict=None):
        results = []
        h_lower = {k.lower(): v for k, v in headers.items()}
        server = h_lower.get('server', '').lower()
        c_str = str(cookie_dict).lower() if cookie_dict else ""
        
        for waf_name, signatures in WAF_SIGNATURES.items():
            score = 0
            for header in signatures.get('headers', []):
                if header.lower() in h_lower: score += 2
            for s in signatures.get('server', []):
                if s.lower() in server: score += 3
            if cookie_dict:
                for cookie in signatures.get('cookies', []):
                    if cookie.lower() in c_str: score += 2
            
            if score >= 2:
                results.append({
                    'waf': waf_name.replace('_', ' ').title(),
                    'confidence': 'High' if score >= 4 else 'Medium',
                    'indicators': [f"Score: {score}"] # Format as list of strings
                })
        return results

    if isinstance(url_or_headers, dict):
        # Called with headers (legacy/internal)
        return analyze_headers(url_or_headers, cookies)
    else:
        # Called with URL (crawler_engine)
        url = url_or_headers
        if not httpx: return {'detected': False}
        try:
            with httpx.Client(timeout=5, follow_redirects=True, verify=False) as client:
                resp = client.HEAD(url) # HEAD might be enough for WAF headers
                # frequent false negatives with HEAD for some WAFs, but faster. 
                # Let's use GET but stream to avoid body download? 
                # Actually HEAD is standard for WAF check usually.
                
                # If HEAD fails or gives little info, GET
                if not resp.headers.get('server'):
                     resp = client.get(url)
                
                matches = analyze_headers(resp.headers, resp.cookies)
                if matches:
                    # Return best match formatted for Crawler
                    best = matches[0]
                    return {
                        'detected': True,
                        'name': best['waf'],
                        'confidence': best['confidence'],
                        'indicators': best['indicators']
                    }
        except:
            pass
        return {'detected': False}


def check_clickjacking(url_or_headers, url_context=None):
    """
    Check for clickjacking
    Args:
        url_or_headers: URL string OR headers dict
        url_context: URL string (only if headers passed)
    """
    issues = []
    
    def analyze(headers, target_url):
        found = []
        h_lower = {k.lower(): v for k, v in headers.items()}
        x_frame = h_lower.get('x-frame-options', '').upper()
        csp = h_lower.get('content-security-policy', '')
        
        has_xfo = bool(x_frame)
        has_csp_frame = 'frame-ancestors' in csp.lower()
        
        if not has_xfo and not has_csp_frame:
            found.append({
                'issue': 'Clickjacking protection missing',
                'severity': 'Medium',
                'url': target_url,
                'details': 'Page can be embedded in iframes',
                'vulnerable': True
            })
        elif x_frame not in ['DENY', 'SAMEORIGIN'] and x_frame:
            found.append({
                'issue': f'Weak X-Frame-Options: {x_frame}',
                'severity': 'Low',
                'url': target_url,
                'details': 'Non-standard X-Frame-Options value',
                'vulnerable': True
            })
        return found

    if isinstance(url_or_headers, dict):
        # Legacy call with headers
        # return list of issues
        return analyze(url_or_headers, url_context)
    else:
        # Called with URL from crawler_engine
        # Return dict {vulnerable: bool}
        url = url_or_headers
        if not httpx: return {'vulnerable': False}
        try:
            with httpx.Client(timeout=5, verify=False) as client:
                resp = client.get(url)
                findings = analyze(resp.headers, url)
                if findings:
                    return {'vulnerable': True, 'details': findings}
        except:
            pass
        return {'vulnerable': False}

# Alias for backwards compatibility if needed internally
test_clickjacking = check_clickjacking



def check_mixed_content(html_content, page_url):
    """Check for mixed content (HTTPS loading HTTP resources)"""
    issues = []
    
    if not page_url.startswith('https://'):
        return issues  # Only relevant for HTTPS pages
    
    if not BeautifulSoup:
        return issues
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Check scripts
        for script in soup.find_all('script', src=True):
            src = script['src']
            if src.startswith('http://'):
                issues.append({
                    'issue': 'Mixed content: HTTP script on HTTPS page',
                    'severity': 'High',
                    'resource': src,
                    'type': 'script'
                })
        
        # Check stylesheets
        for link in soup.find_all('link', href=True):
            if link.get('rel') == ['stylesheet'] and link['href'].startswith('http://'):
                issues.append({
                    'issue': 'Mixed content: HTTP stylesheet',
                    'severity': 'Medium',
                    'resource': link['href'],
                    'type': 'stylesheet'
                })
        
        # Check iframes
        for iframe in soup.find_all('iframe', src=True):
            if iframe['src'].startswith('http://'):
                issues.append({
                    'issue': 'Mixed content: HTTP iframe',
                    'severity': 'High',
                    'resource': iframe['src'],
                    'type': 'iframe'
                })
        
        # Check images (lower severity)
        for img in soup.find_all('img', src=True):
            if img['src'].startswith('http://'):
                issues.append({
                    'issue': 'Mixed content: HTTP image',
                    'severity': 'Low',
                    'resource': img['src'],
                    'type': 'image'
                })
                
    except:
        pass
    
    return issues


def extract_html_comments(html_content, url):
    """Extract HTML comments that might contain sensitive info"""
    findings = []
    
    # Find HTML comments
    comments = re.findall(r'<!--(.*?)-->', html_content, re.DOTALL)
    
    sensitive_patterns = [
        (r'\b(?:password|passwd|pwd)\s*[:=]', 'Password reference'),
        (r'\b(?:username|user)\s*[:=]', 'Username reference'),
        (r'\b(?:api[_-]?key|apikey)\s*[:=]', 'API key reference'),
        (r'\b(?:secret|token)\s*[:=]', 'Secret/token reference'),
        (r'\b(?:TODO|FIXME|HACK|XXX|BUG)\b', 'Developer note'),
        (r'\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b', 'IP address'),
        (r'/(?:home|var|etc|usr)/[\w/]+', 'File path'),
        (r'[a-zA-Z]:\\[\w\\]+', 'Windows path'),
        (r'\b(?:admin|root|superuser)\b', 'Privileged user reference'),
        (r'(?:debug|test|staging)\s*[:=]\s*true', 'Debug mode reference'),
    ]
    
    for comment in comments:
        comment = comment.strip()
        if len(comment) < 3:
            continue
        
        for pattern, desc in sensitive_patterns:
            if re.search(pattern, comment, re.IGNORECASE):
                findings.append({
                    'issue': f'Sensitive HTML comment: {desc}',
                    'severity': 'Medium' if 'password' in pattern.lower() or 'api' in pattern.lower() else 'Low',
                    'content': comment[:200] + ('...' if len(comment) > 200 else ''),
                    'url': url
                })
                break
    
    return findings


def extract_meta_info(html_content, url):
    """Extract meta tags that reveal information"""
    findings = []
    
    if not BeautifulSoup:
        return findings
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Generator meta tag
        generator = soup.find('meta', attrs={'name': 'generator'})
        if generator and generator.get('content'):
            findings.append({
                'type': 'generator',
                'value': generator['content'],
                'severity': 'Info',
                'url': url
            })
        
        # Author meta tag
        author = soup.find('meta', attrs={'name': 'author'})
        if author and author.get('content'):
            findings.append({
                'type': 'author',
                'value': author['content'],
                'severity': 'Info',
                'url': url
            })
        
        # Copyright
        for meta in soup.find_all('meta'):
            name = (meta.get('name') or '').lower()
            content = meta.get('content', '')
            if name in ['copyright', 'owner', 'creator', 'publisher'] and content:
                findings.append({
                    'type': name,
                    'value': content,
                    'severity': 'Info',
                    'url': url
                })
    except:
        pass
    
    return findings


def trigger_error_pages(base_url, user_agent='Mozilla/5.0'):
    """Trigger error pages to check for information disclosure"""
    findings = []
    
    if not httpx:
        return findings
    
    error_triggers = [
        ('/nonexistent_page_xyz123', '404'),
        ("/?id=1'", '500/SQL'),
        ('/%00', '500/null'),
        ('/?<script>', '500/XSS'),
    ]
    
    for path, error_type in error_triggers:
        try:
            url = urljoin(base_url, path)
            with httpx.Client(timeout=5, follow_redirects=True, verify=False) as client:
                response = client.get(url, headers={'User-Agent': user_agent})
                body = response.text.lower()
                
                # Check for verbose error info
                disclosure_patterns = [
                    (r'stack trace', 'Stack trace exposed'),
                    (r'traceback', 'Python traceback exposed'),
                    (r'exception', 'Exception details exposed'),
                    (r'at\s+\w+\.\w+\(', 'Java stack trace exposed'),
                    (r'line\s+\d+', 'Line numbers exposed'),
                    (r'/(?:var|home|usr)/[\w/]+\.(?:php|py|rb|js)', 'File paths exposed'),
                    (r'sql syntax', 'SQL error exposed'),
                    (r'mysql_', 'MySQL function exposed'),
                    (r'pg_', 'PostgreSQL function exposed'),
                    (r'ora-\d{5}', 'Oracle error exposed'),
                    (r'debug\s*=\s*true', 'Debug mode enabled'),
                ]
                
                for pattern, desc in disclosure_patterns:
                    if re.search(pattern, body, re.IGNORECASE):
                        findings.append({
                            'issue': f'Information disclosure in error page: {desc}',
                            'severity': 'High' if 'sql' in pattern.lower() or 'stack' in pattern.lower() else 'Medium',
                            'trigger': path,
                            'status': response.status_code,
                            'url': url
                        })
                        break
        except:
            pass
    
    return findings


def find_open_redirect_params(urls):
    """Find URLs with potential open redirect parameters"""
    findings = []
    
    for url in urls:
        try:
            parsed = urlparse(url)
            params = parse_qs(parsed.query)
            
            for param in params:
                if param.lower() in REDIRECT_PARAMS:
                    findings.append({
                        'issue': f'Potential open redirect parameter: {param}',
                        'severity': 'Medium',
                        'url': url,
                        'parameter': param,
                        'description': 'Parameter may allow redirection to external sites'
                    })
        except:
            pass
    
    return findings


def check_subdomain_takeover(subdomain_results, user_agent='Mozilla/5.0'):
    """Check discovered subdomains for takeover vulnerabilities"""
    findings = []
    
    if not httpx:
        return findings
    
    for subdomain in subdomain_results:
        url = subdomain.get('url', '')
        if not url:
            continue
        
        try:
            with httpx.Client(timeout=5, follow_redirects=True, verify=False) as client:
                response = client.get(url, headers={'User-Agent': user_agent})
                body = response.text.lower()
                
                for service, fingerprints in TAKEOVER_FINGERPRINTS.items():
                    for fingerprint in fingerprints:
                        if fingerprint.lower() in body:
                            findings.append({
                                'issue': f'Potential subdomain takeover: {service}',
                                'severity': 'Critical',
                                'url': url,
                                'service': service,
                                'fingerprint': fingerprint,
                                'description': 'Subdomain may be claimable by attacker'
                            })
                            break
        except:
            pass
    
    return findings


def run_vulnerability_scan(url, html_content, response_headers, user_agent='Mozilla/5.0'):
    """
    Run comprehensive vulnerability scan on a page
    
    Args:
        url: URL of the page
        html_content: HTML content
        response_headers: Response headers dictionary
        user_agent: User agent string
    
    Returns:
        Dictionary with all vulnerability findings
    """
    results = {
        'url': url,
        'cors': [],
        'http_methods': [],
        'waf_detected': [],
        'clickjacking': [],
        'mixed_content': [],
        'html_comments': [],
        'meta_info': [],
        'error_disclosure': [],
        'summary': {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'info': 0
        }
    }
    
    # CORS testing
    results['cors'] = test_cors_misconfiguration(url, user_agent)
    
    # HTTP methods
    results['http_methods'] = test_http_methods(url, user_agent)
    
    # WAF detection
    results['waf_detected'] = detect_waf(response_headers)
    
    # Clickjacking
    results['clickjacking'] = test_clickjacking(response_headers, url)
    
    # Mixed content
    if html_content:
        results['mixed_content'] = check_mixed_content(html_content, url)
        results['html_comments'] = extract_html_comments(html_content, url)
        results['meta_info'] = extract_meta_info(html_content, url)
    
    # Error page analysis (only for base URL to avoid excessive requests)
    parsed = urlparse(url)
    if parsed.path in ['/', '']:
        results['error_disclosure'] = trigger_error_pages(url, user_agent)
    
    # Count by severity
    all_findings = (
        results['cors'] + results['http_methods'] + 
        results['clickjacking'] + results['mixed_content'] +
        results['html_comments'] + results['error_disclosure']
    )
    
    for finding in all_findings:
        severity = finding.get('severity', 'Info').lower()
        if severity == 'critical':
            results['summary']['critical'] += 1
        elif severity == 'high':
            results['summary']['high'] += 1
        elif severity == 'medium':
            results['summary']['medium'] += 1
        elif severity == 'low':
            results['summary']['low'] += 1
        else:
            results['summary']['info'] += 1
    
    return results


def get_vulnerability_summary(all_scan_results):
    """Generate summary across all vulnerability scans"""
    summary = {
        'pages_scanned': len(all_scan_results),
        'total_findings': 0,
        'by_severity': {'critical': 0, 'high': 0, 'medium': 0, 'low': 0, 'info': 0},
        'by_type': {
            'cors': 0,
            'http_methods': 0,
            'clickjacking': 0,
            'mixed_content': 0,
            'html_comments': 0,
            'error_disclosure': 0
        },
        'waf_detected': None,
        'all_critical': [],
        'all_high': []
    }
    
    for result in all_scan_results:
        s = result.get('summary', {})
        summary['by_severity']['critical'] += s.get('critical', 0)
        summary['by_severity']['high'] += s.get('high', 0)
        summary['by_severity']['medium'] += s.get('medium', 0)
        summary['by_severity']['low'] += s.get('low', 0)
        summary['by_severity']['info'] += s.get('info', 0)
        
        summary['by_type']['cors'] += len(result.get('cors', []))
        summary['by_type']['http_methods'] += len(result.get('http_methods', []))
        summary['by_type']['clickjacking'] += len(result.get('clickjacking', []))
        summary['by_type']['mixed_content'] += len(result.get('mixed_content', []))
        summary['by_type']['html_comments'] += len(result.get('html_comments', []))
        summary['by_type']['error_disclosure'] += len(result.get('error_disclosure', []))
        
        # Get WAF info (take first detected)
        if result.get('waf_detected') and not summary['waf_detected']:
            summary['waf_detected'] = result['waf_detected']
        
        # Collect critical/high findings
        for finding in result.get('cors', []) + result.get('http_methods', []) + result.get('error_disclosure', []):
            if finding.get('severity') == 'Critical':
                summary['all_critical'].append({'url': result['url'], **finding})
            elif finding.get('severity') == 'High':
                summary['all_high'].append({'url': result['url'], **finding})
    
    summary['total_findings'] = sum(summary['by_severity'].values())
    
    return summary
