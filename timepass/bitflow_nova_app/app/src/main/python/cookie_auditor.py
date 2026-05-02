# cookie_auditor.py
# Cookie Security Audit - Analyze cookies for security flags and risks

import re
from urllib.parse import urlparse
from datetime import datetime, timedelta

# Session cookie name patterns
SESSION_COOKIE_PATTERNS = [
    r'^PHPSESSID$',
    r'^JSESSIONID$',
    r'^ASP\.NET_SessionId$',
    r'^connect\.sid$',
    r'^session$',
    r'^sessionid$',
    r'^sid$',
    r'^_session$',
    r'^auth_token$',
    r'^access_token$',
    r'^login$',
    r'^logged_in$',
    r'^user_session$',
    r'^_user_session$',
    r'^remember_token$',
    r'^auth$',
    r'^laravel_session$',
    r'^django_session$',
    r'^rack\.session$',
    r'^_rails_session$',
    r'^express\.sid$',
    r'^ci_session$',
]

# Tracking/Analytics cookie patterns
TRACKING_COOKIE_PATTERNS = [
    r'^_ga$',          # Google Analytics
    r'^_gid$',         # Google Analytics
    r'^_gat$',         # Google Analytics
    r'^__utm',         # Google Analytics UTM
    r'^_fbp$',         # Facebook Pixel
    r'^_fbc$',         # Facebook Click
    r'^fr$',           # Facebook
    r'^_gcl_',         # Google Ads
    r'^_mkto_',        # Marketo
    r'^hubspot',       # HubSpot
    r'^__hssc$',       # HubSpot
    r'^__hstc$',       # HubSpot
    r'^__hsfp$',       # HubSpot
    r'^_uetsid$',      # Bing Ads
    r'^_uetvid$',      # Bing Ads
    r'^ajs_',          # Segment
    r'^amplitude_',    # Amplitude
    r'^mp_',           # Mixpanel
    r'^intercom',      # Intercom
    r'^drift',         # Drift
]

# Preference/Functionality cookie patterns
PREFERENCE_COOKIE_PATTERNS = [
    r'lang',
    r'locale',
    r'currency',
    r'theme',
    r'dark_mode',
    r'consent',
    r'cookie_consent',
    r'gdpr',
    r'preference',
]


def parse_cookie_header(set_cookie_header):
    """Parse a Set-Cookie header into components"""
    cookie = {
        'name': None,
        'value': None,
        'path': '/',
        'domain': None,
        'expires': None,
        'max_age': None,
        'secure': False,
        'httponly': False,
        'samesite': None,
        'raw': set_cookie_header
    }
    
    if not set_cookie_header:
        return None
    
    # Split by semicolon
    parts = set_cookie_header.split(';')
    
    # First part is name=value
    if parts:
        first_part = parts[0].strip()
        if '=' in first_part:
            name, value = first_part.split('=', 1)
            cookie['name'] = name.strip()
            cookie['value'] = value.strip()
    
    # Parse attributes
    for part in parts[1:]:
        part = part.strip()
        if '=' in part:
            key, val = part.split('=', 1)
            key = key.strip().lower()
            val = val.strip()
            
            if key == 'path':
                cookie['path'] = val
            elif key == 'domain':
                cookie['domain'] = val
            elif key == 'expires':
                cookie['expires'] = val
            elif key == 'max-age':
                try:
                    cookie['max_age'] = int(val)
                except:
                    pass
            elif key == 'samesite':
                cookie['samesite'] = val.lower()
        else:
            key = part.lower()
            if key == 'secure':
                cookie['secure'] = True
            elif key == 'httponly':
                cookie['httponly'] = True
    
    return cookie if cookie['name'] else None


def classify_cookie(cookie_name):
    """Classify a cookie by its name"""
    classifications = []
    
    # Check session patterns
    for pattern in SESSION_COOKIE_PATTERNS:
        if re.match(pattern, cookie_name, re.IGNORECASE):
            classifications.append('SESSION')
            break
    
    # Check tracking patterns
    for pattern in TRACKING_COOKIE_PATTERNS:
        if re.match(pattern, cookie_name, re.IGNORECASE):
            classifications.append('TRACKING')
            break
    
    # Check preference patterns
    for pattern in PREFERENCE_COOKIE_PATTERNS:
        if re.search(pattern, cookie_name, re.IGNORECASE):
            classifications.append('PREFERENCE')
            break
    
    if not classifications:
        classifications.append('UNKNOWN')
    
    return classifications


def audit_cookie(cookie, is_https=True):
    """Audit a single cookie for security issues"""
    issues = []
    classifications = classify_cookie(cookie['name'])
    is_session = 'SESSION' in classifications
    
    # Critical: Session cookie without Secure flag
    if not cookie['secure']:
        severity = 'High' if is_session else 'Medium'
        issues.append({
            'issue': 'Missing Secure flag',
            'severity': severity,
            'description': 'Cookie can be transmitted over HTTP, vulnerable to interception',
            'recommendation': 'Add Secure flag to prevent transmission over unencrypted connections'
        })
    
    # Critical: Session cookie without HttpOnly flag
    if not cookie['httponly']:
        severity = 'High' if is_session else 'Low'
        issues.append({
            'issue': 'Missing HttpOnly flag',
            'severity': severity,
            'description': 'Cookie accessible via JavaScript, vulnerable to XSS attacks',
            'recommendation': 'Add HttpOnly flag to prevent JavaScript access'
        })
    
    # Medium: Missing SameSite attribute
    if not cookie['samesite']:
        severity = 'Medium' if is_session else 'Low'
        issues.append({
            'issue': 'Missing SameSite attribute',
            'severity': severity,
            'description': 'Cookie may be sent with cross-site requests, CSRF vulnerability',
            'recommendation': 'Add SameSite=Strict or SameSite=Lax'
        })
    elif cookie['samesite'] == 'none':
        if not cookie['secure']:
            issues.append({
                'issue': 'SameSite=None without Secure flag',
                'severity': 'High',
                'description': 'SameSite=None requires Secure flag',
                'recommendation': 'Add Secure flag when using SameSite=None'
            })
    
    # Medium: Long expiry for session cookies
    if is_session and cookie['max_age']:
        # More than 24 hours
        if cookie['max_age'] > 86400:
            days = cookie['max_age'] // 86400
            issues.append({
                'issue': f'Long session expiry ({days} days)',
                'severity': 'Medium',
                'description': 'Session cookies should have shorter lifetimes',
                'recommendation': 'Consider reducing session timeout for security'
            })
    
    # Info: Overly permissive path
    if cookie['path'] == '/' and is_session:
        # This is actually common, but worth noting
        pass  # Not adding as an issue, it's standard practice
    
    # Info: Domain scope
    if cookie['domain'] and cookie['domain'].startswith('.'):
        issues.append({
            'issue': 'Cookie scoped to all subdomains',
            'severity': 'Low',
            'description': f'Cookie shared across all subdomains of {cookie["domain"]}',
            'recommendation': 'Consider limiting cookie scope if subdomains are not trusted'
        })
    
    return {
        'name': cookie['name'],
        'value_length': len(cookie['value']) if cookie['value'] else 0,
        'classifications': classifications,
        'secure': cookie['secure'],
        'httponly': cookie['httponly'],
        'samesite': cookie['samesite'],
        'path': cookie['path'],
        'domain': cookie['domain'],
        'max_age': cookie['max_age'],
        'expires': cookie['expires'],
        'issues': issues,
        'issue_count': len(issues)
    }


def audit_cookies(response_headers, url):
    """
    Audit all cookies from response headers
    
    Args:
        response_headers: Dictionary of response headers
        url: URL of the response
    
    Returns:
        Dictionary with cookie audit results
    """
    results = {
        'url': url,
        'cookies': [],
        'summary': {
            'total_cookies': 0,
            'session_cookies': 0,
            'tracking_cookies': 0,
            'secure_cookies': 0,
            'httponly_cookies': 0,
            'samesite_cookies': 0,
            'critical_issues': 0,
            'high_issues': 0,
            'medium_issues': 0,
            'low_issues': 0
        },
        'all_issues': []
    }
    
    is_https = url.startswith('https://')
    
    # Get Set-Cookie headers (could be multiple)
    set_cookies = []
    
    # Handle both string and list cases
    for key, value in response_headers.items():
        if key.lower() == 'set-cookie':
            if isinstance(value, list):
                set_cookies.extend(value)
            else:
                set_cookies.append(value)
    
    for set_cookie in set_cookies:
        cookie = parse_cookie_header(set_cookie)
        if not cookie:
            continue
        
        audit = audit_cookie(cookie, is_https)
        results['cookies'].append(audit)
        
        # Update summary
        results['summary']['total_cookies'] += 1
        
        if 'SESSION' in audit['classifications']:
            results['summary']['session_cookies'] += 1
        if 'TRACKING' in audit['classifications']:
            results['summary']['tracking_cookies'] += 1
        if audit['secure']:
            results['summary']['secure_cookies'] += 1
        if audit['httponly']:
            results['summary']['httponly_cookies'] += 1
        if audit['samesite']:
            results['summary']['samesite_cookies'] += 1
        
        # Count issues by severity
        for issue in audit['issues']:
            severity = issue['severity']
            if severity == 'Critical':
                results['summary']['critical_issues'] += 1
            elif severity == 'High':
                results['summary']['high_issues'] += 1
            elif severity == 'Medium':
                results['summary']['medium_issues'] += 1
            elif severity == 'Low':
                results['summary']['low_issues'] += 1
            
            results['all_issues'].append({
                'cookie': audit['name'],
                **issue
            })
    
    return results


def get_cookie_audit_summary(all_cookie_results):
    """Generate summary across all pages"""
    summary = {
        'pages_with_cookies': 0,
        'total_unique_cookies': set(),
        'session_cookies': set(),
        'tracking_cookies': set(),
        'security_score': 100,
        'issues_by_severity': {
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0
        },
        'all_issues': []
    }
    
    for page_result in all_cookie_results:
        if page_result['summary']['total_cookies'] > 0:
            summary['pages_with_cookies'] += 1
        
        for cookie in page_result['cookies']:
            summary['total_unique_cookies'].add(cookie['name'])
            
            if 'SESSION' in cookie['classifications']:
                summary['session_cookies'].add(cookie['name'])
            if 'TRACKING' in cookie['classifications']:
                summary['tracking_cookies'].add(cookie['name'])
        
        summary['issues_by_severity']['critical'] += page_result['summary']['critical_issues']
        summary['issues_by_severity']['high'] += page_result['summary']['high_issues']
        summary['issues_by_severity']['medium'] += page_result['summary']['medium_issues']
        summary['issues_by_severity']['low'] += page_result['summary']['low_issues']
        
        summary['all_issues'].extend(page_result['all_issues'])
    
    # Calculate score
    summary['security_score'] -= summary['issues_by_severity']['critical'] * 25
    summary['security_score'] -= summary['issues_by_severity']['high'] * 15
    summary['security_score'] -= summary['issues_by_severity']['medium'] * 5
    summary['security_score'] -= summary['issues_by_severity']['low'] * 2
    summary['security_score'] = max(0, summary['security_score'])
    
    # Convert sets to counts for JSON serialization
    summary['total_unique_cookies'] = len(summary['total_unique_cookies'])
    summary['session_cookies'] = len(summary['session_cookies'])
    summary['tracking_cookies'] = len(summary['tracking_cookies'])
    
    return summary
