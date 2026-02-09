# auth_tester.py
# Authentication Testing - Rate limiting, Default credentials, Account enumeration

import re
import time
from urllib.parse import urljoin, urlparse

try:
    import httpx
except ImportError:
    httpx = None

# Common login paths
LOGIN_PATHS = [
    '/login', '/signin', '/sign-in', '/auth', '/authenticate',
    '/admin', '/admin/login', '/administrator', '/user/login',
    '/account/login', '/member/login', '/portal/login',
    '/wp-login.php', '/wp-admin', '/administrator/index.php',
    '/user', '/users/sign_in', '/session/new',
    '/api/auth/login', '/api/login', '/api/v1/auth/login',
    '/oauth/authorize', '/oauth2/authorize', '/connect/authorize',
]

# Default credential database
DEFAULT_CREDENTIALS = [
    # Format: (username, password, description)
    ('admin', 'admin', 'Common default'),
    ('admin', 'password', 'Common default'),
    ('admin', '123456', 'Common default'),
    ('admin', 'admin123', 'Common default'),
    ('administrator', 'administrator', 'Windows default'),
    ('root', 'root', 'Linux default'),
    ('root', 'toor', 'Kali default'),
    ('user', 'user', 'Common default'),
    ('test', 'test', 'Test account'),
    ('demo', 'demo', 'Demo account'),
    ('guest', 'guest', 'Guest account'),
    
    # CMS defaults
    ('admin', 'admin@123', 'CMS default'),
    ('admin', 'password123', 'CMS default'),
    
    # Database defaults
    ('sa', '', 'SQL Server default'),
    ('postgres', 'postgres', 'PostgreSQL default'),
    ('mysql', 'mysql', 'MySQL default'),
    ('oracle', 'oracle', 'Oracle default'),
    
    # Network device defaults
    ('admin', 'admin', 'Router default'),
    ('cisco', 'cisco', 'Cisco default'),
    ('admin', '1234', 'Router default'),
    
    # Web server defaults
    ('tomcat', 'tomcat', 'Tomcat default'),
    ('manager', 'manager', 'Tomcat manager'),
    ('weblogic', 'weblogic', 'WebLogic default'),
    ('admin', 'weblogic', 'WebLogic default'),
]

# Username wordlist for enumeration
COMMON_USERNAMES = [
    'admin', 'administrator', 'root', 'user', 'test', 'guest',
    'demo', 'info', 'support', 'contact', 'sales', 'marketing',
    'dev', 'developer', 'webmaster', 'postmaster', 'hostmaster',
    'admin1', 'user1', 'test1', 'backup', 'temp', 'anonymous',
]

# Common error messages that indicate valid/invalid username
USERNAME_ENUM_PATTERNS = {
    'valid_user': [
        'invalid password',
        'wrong password',
        'password incorrect',
        'incorrect password',
        'authentication failed',
        'login failed for',
    ],
    'invalid_user': [
        'user not found',
        'username not found',
        'no such user',
        'account not found',
        'user does not exist',
        'invalid username',
        'unknown user',
        'no account',
    ],
}

# Rate limiting headers to check
RATE_LIMIT_HEADERS = [
    'x-ratelimit-limit',
    'x-ratelimit-remaining',
    'x-ratelimit-reset',
    'x-rate-limit-limit',
    'x-rate-limit-remaining',
    'retry-after',
    'ratelimit-limit',
    'ratelimit-remaining',
    'ratelimit-reset',
]


def find_login_page(base_url, timeout=10):
    """Find login page on the target"""
    if not httpx:
        return None
    
    with httpx.Client(timeout=timeout, verify=False, follow_redirects=True) as client:
        for path in LOGIN_PATHS:
            url = urljoin(base_url, path)
            try:
                response = client.get(url)
                if response.status_code == 200:
                    # Check if it looks like a login page
                    text = response.text.lower()
                    if any(x in text for x in ['password', 'login', 'sign in', 'username', 'email']):
                        # Try to find form action
                        form_action = find_form_action(response.text, url)
                        return {
                            'url': url,
                            'form_action': form_action or url,
                            'method': 'POST',
                            'has_csrf': 'csrf' in text or '_token' in text,
                        }
            except Exception:
                continue
    
    return None


def find_form_action(html, base_url):
    """Find form action URL in HTML"""
    # Find form with password field
    form_match = re.search(
        r'<form[^>]*action=["\']([^"\']*)["\'][^>]*>.*?type=["\']password["\']',
        html, re.IGNORECASE | re.DOTALL
    )
    
    if not form_match:
        # Try reverse - password field then action
        form_match = re.search(
            r'type=["\']password["\'].*?<form[^>]*action=["\']([^"\']*)["\']',
            html, re.IGNORECASE | re.DOTALL
        )
    
    if not form_match:
        # Just find any form with action
        form_match = re.search(r'<form[^>]*action=["\']([^"\']*)["\']', html, re.IGNORECASE)
    
    if form_match:
        action = form_match.group(1)
        if action:
            return urljoin(base_url, action)
    
    return None


def find_login_fields(html):
    """Detect username and password field names"""
    fields = {
        'username_field': None,
        'password_field': None,
        'other_fields': {},
    }
    
    html_lower = html.lower()
    
    # Common username field patterns
    username_patterns = [
        r'name=["\']([^"\']*(?:user|email|login|account|username)[^"\']*)["\'].*?type=["\'](?:text|email)',
        r'type=["\'](?:text|email)["\'].*?name=["\']([^"\']*(?:user|email|login|account|username)[^"\']*)["\']',
    ]
    
    for pattern in username_patterns:
        match = re.search(pattern, html_lower)
        if match:
            fields['username_field'] = match.group(1)
            break
    
    if not fields['username_field']:
        # Fallback to common names
        for name in ['username', 'user', 'email', 'login', 'user_login', 'log']:
            if f'name="{name}"' in html_lower or f"name='{name}'" in html_lower:
                fields['username_field'] = name
                break
    
    # Password field
    password_patterns = [
        r'name=["\']([^"\']*(?:pass|pwd)[^"\']*)["\'].*?type=["\']password',
        r'type=["\']password["\'].*?name=["\']([^"\']*)["\']',
    ]
    
    for pattern in password_patterns:
        match = re.search(pattern, html_lower)
        if match:
            fields['password_field'] = match.group(1)
            break
    
    if not fields['password_field']:
        for name in ['password', 'pass', 'pwd', 'user_pass', 'passwd']:
            if f'name="{name}"' in html_lower or f"name='{name}'" in html_lower:
                fields['password_field'] = name
                break
    
    # Find CSRF token
    csrf_patterns = [
        r'name=["\']([^"\']*(?:csrf|token|_token|authenticity)[^"\']*)["\'].*?value=["\']([^"\']*)["\']',
        r'value=["\']([^"\']+)["\'].*?name=["\']([^"\']*(?:csrf|token)[^"\']*)["\']',
    ]
    
    for pattern in csrf_patterns:
        match = re.search(pattern, html_lower)
        if match:
            fields['other_fields']['csrf_token'] = {
                'name': match.group(1) if 'csrf' in match.group(1).lower() or 'token' in match.group(1).lower() else match.group(2),
                'value': match.group(2) if len(match.groups()) > 1 else '',
            }
            break
    
    return fields


def test_rate_limiting(url, requests_count=10, delay=0.1, timeout=10):
    """Test if rate limiting is implemented"""
    if not httpx:
        return {'error': 'httpx not available'}
    
    result = {
        'url': url,
        'rate_limited': False,
        'rate_limit_headers': {},
        'blocked_after': None,
        'status_codes': [],
        'response_times': [],
        'issues': [],
    }
    
    with httpx.Client(timeout=timeout, verify=False) as client:
        for i in range(requests_count):
            start_time = time.time()
            try:
                response = client.get(url)
                elapsed = time.time() - start_time
                
                result['status_codes'].append(response.status_code)
                result['response_times'].append(elapsed)
                
                # Check for rate limit headers
                for header in RATE_LIMIT_HEADERS:
                    value = response.headers.get(header)
                    if value:
                        result['rate_limit_headers'][header] = value
                
                # Check if blocked
                if response.status_code == 429:
                    result['rate_limited'] = True
                    result['blocked_after'] = i + 1
                    break
                
                # Check for CAPTCHA or block page
                text_lower = response.text.lower()
                if any(x in text_lower for x in ['captcha', 'rate limit', 'too many requests', 'blocked', 'try again later']):
                    result['rate_limited'] = True
                    result['blocked_after'] = i + 1
                    break
                
            except httpx.TimeoutException:
                result['response_times'].append(timeout)
            except Exception as e:
                pass
            
            time.sleep(delay)
    
    # Analyze results
    if not result['rate_limited'] and not result['rate_limit_headers']:
        result['issues'].append({
            'severity': 'Medium',
            'issue': 'No rate limiting detected',
            'recommendation': 'Implement rate limiting to prevent brute force attacks'
        })
    
    if result['rate_limited']:
        result['issues'].append({
            'severity': 'Info',
            'issue': f'Rate limiting kicks in after {result["blocked_after"]} requests',
            'recommendation': 'Rate limiting is properly implemented'
        })
    
    return result


def test_account_lockout(login_url, username='admin', attempts=5, timeout=10):
    """Test if account lockout is implemented"""
    if not httpx:
        return {'error': 'httpx not available'}
    
    result = {
        'url': login_url,
        'username': username,
        'lockout_detected': False,
        'lockout_after': None,
        'responses': [],
        'issues': [],
    }
    
    with httpx.Client(timeout=timeout, verify=False, follow_redirects=True) as client:
        # First, get the login page to find fields
        try:
            page_response = client.get(login_url)
            fields = find_login_fields(page_response.text)
        except Exception:
            fields = {'username_field': 'username', 'password_field': 'password', 'other_fields': {}}
        
        username_field = fields.get('username_field', 'username')
        password_field = fields.get('password_field', 'password')
        
        for i in range(attempts):
            try:
                # Build login data
                data = {
                    username_field: username,
                    password_field: f'wrongpassword{i}',
                }
                
                # Add CSRF token if found
                if 'csrf_token' in fields.get('other_fields', {}):
                    csrf = fields['other_fields']['csrf_token']
                    data[csrf['name']] = csrf['value']
                
                response = client.post(login_url, data=data)
                
                response_info = {
                    'attempt': i + 1,
                    'status': response.status_code,
                    'length': len(response.content),
                }
                
                text_lower = response.text.lower()
                
                # Check for lockout indicators
                lockout_patterns = [
                    'account locked', 'account has been locked', 'too many attempts',
                    'temporarily locked', 'try again later', 'account suspended',
                    'exceeded maximum', 'locked out',
                ]
                
                for pattern in lockout_patterns:
                    if pattern in text_lower:
                        result['lockout_detected'] = True
                        result['lockout_after'] = i + 1
                        response_info['lockout_hint'] = pattern
                        break
                
                result['responses'].append(response_info)
                
                if result['lockout_detected']:
                    break
                
            except Exception as e:
                result['responses'].append({'attempt': i + 1, 'error': str(e)})
    
    # Analyze results
    if not result['lockout_detected']:
        result['issues'].append({
            'severity': 'High',
            'issue': f'No account lockout after {attempts} failed attempts',
            'recommendation': 'Implement account lockout to prevent brute force attacks'
        })
    else:
        result['issues'].append({
            'severity': 'Info',
            'issue': f'Account lockout detected after {result["lockout_after"]} attempts',
            'recommendation': 'Account lockout is properly implemented'
        })
    
    return result


def test_username_enumeration(login_url, timeout=10):
    """Test for username enumeration vulnerability"""
    if not httpx:
        return {'error': 'httpx not available'}
    
    result = {
        'url': login_url,
        'enumerable': False,
        'method': None,
        'valid_users': [],
        'evidence': [],
        'issues': [],
    }
    
    with httpx.Client(timeout=timeout, verify=False, follow_redirects=True) as client:
        # Get login page fields
        try:
            page_response = client.get(login_url)
            fields = find_login_fields(page_response.text)
        except Exception:
            fields = {'username_field': 'username', 'password_field': 'password', 'other_fields': {}}
        
        username_field = fields.get('username_field', 'username')
        password_field = fields.get('password_field', 'password')
        
        # Test with definitely invalid username
        invalid_username = 'xyzzy_nonexistent_user_12345'
        
        # Response characteristics for comparison
        responses = {}
        
        # Test invalid username
        try:
            data = {username_field: invalid_username, password_field: 'wrongpassword'}
            if 'csrf_token' in fields.get('other_fields', {}):
                csrf = fields['other_fields']['csrf_token']
                data[csrf['name']] = csrf['value']
            
            response = client.post(login_url, data=data)
            responses['invalid'] = {
                'status': response.status_code,
                'length': len(response.content),
                'text': response.text.lower(),
            }
        except Exception:
            return result
        
        # Test common usernames
        for username in COMMON_USERNAMES[:10]:
            try:
                data = {username_field: username, password_field: 'wrongpassword'}
                if 'csrf_token' in fields.get('other_fields', {}):
                    # Refresh CSRF if needed
                    page_response = client.get(login_url)
                    fields = find_login_fields(page_response.text)
                    if 'csrf_token' in fields.get('other_fields', {}):
                        csrf = fields['other_fields']['csrf_token']
                        data[csrf['name']] = csrf['value']
                
                response = client.post(login_url, data=data)
                
                current = {
                    'status': response.status_code,
                    'length': len(response.content),
                    'text': response.text.lower(),
                }
                
                # Compare with invalid username response
                invalid = responses['invalid']
                
                # Different error messages
                for pattern in USERNAME_ENUM_PATTERNS['valid_user']:
                    if pattern in current['text'] and pattern not in invalid['text']:
                        result['enumerable'] = True
                        result['method'] = 'error_message'
                        result['valid_users'].append(username)
                        result['evidence'].append({
                            'username': username,
                            'reason': f'Different error message: "{pattern}"'
                        })
                        break
                
                # Different response length (significant difference)
                if abs(current['length'] - invalid['length']) > 50:
                    if username not in result['valid_users']:
                        result['evidence'].append({
                            'username': username,
                            'reason': f'Response length differs: {current["length"]} vs {invalid["length"]}'
                        })
                
                # Different status code
                if current['status'] != invalid['status']:
                    if username not in result['valid_users']:
                        result['evidence'].append({
                            'username': username,
                            'reason': f'Status code differs: {current["status"]} vs {invalid["status"]}'
                        })
                
            except Exception:
                continue
            
            time.sleep(0.2)  # Rate limit friendly
    
    # Analyze results
    if result['enumerable']:
        result['issues'].append({
            'severity': 'High',
            'issue': 'Username enumeration is possible',
            'recommendation': 'Use generic error messages for login failures'
        })
    
    return result


def test_default_credentials(login_url, credentials=None, timeout=10, max_attempts=10):
    """Test for default credentials"""
    if not httpx:
        return {'error': 'httpx not available'}
    
    if credentials is None:
        credentials = DEFAULT_CREDENTIALS[:max_attempts]
    
    result = {
        'url': login_url,
        'tested': 0,
        'found': [],
        'issues': [],
    }
    
    with httpx.Client(timeout=timeout, verify=False, follow_redirects=True) as client:
        # Get login page fields
        try:
            page_response = client.get(login_url)
            fields = find_login_fields(page_response.text)
            baseline_length = len(page_response.content)
        except Exception:
            return result
        
        username_field = fields.get('username_field', 'username')
        password_field = fields.get('password_field', 'password')
        
        for username, password, description in credentials:
            result['tested'] += 1
            
            try:
                # Refresh page for CSRF
                page_response = client.get(login_url)
                fields = find_login_fields(page_response.text)
                
                data = {username_field: username, password_field: password}
                
                if 'csrf_token' in fields.get('other_fields', {}):
                    csrf = fields['other_fields']['csrf_token']
                    data[csrf['name']] = csrf['value']
                
                response = client.post(login_url, data=data)
                
                # Check for successful login indicators
                text_lower = response.text.lower()
                success_indicators = [
                    'logout', 'sign out', 'log out', 'dashboard', 'welcome',
                    'my account', 'profile', 'settings', 'admin panel',
                ]
                
                failed_indicators = [
                    'invalid', 'incorrect', 'wrong', 'failed', 'error',
                    'denied', 'unauthorized',
                ]
                
                # Check if redirected to different page
                if response.url.path != urlparse(login_url).path:
                    # Redirected - might be successful login
                    if not any(x in text_lower for x in failed_indicators):
                        if any(x in text_lower for x in success_indicators):
                            result['found'].append({
                                'username': username,
                                'password': password,
                                'description': description,
                                'redirect': str(response.url),
                            })
                
                # Check response content
                elif any(x in text_lower for x in success_indicators):
                    if not any(x in text_lower for x in failed_indicators):
                        result['found'].append({
                            'username': username,
                            'password': password,
                            'description': description,
                        })
                
            except Exception:
                continue
            
            time.sleep(0.5)  # Avoid triggering rate limits
    
    # Analyze results
    if result['found']:
        for cred in result['found']:
            result['issues'].append({
                'severity': 'Critical',
                'issue': f'Default credential works: {cred["username"]}:{cred["password"]}',
                'recommendation': 'Change default credentials immediately'
            })
    
    return result


def analyze_authentication(url):
    """Main function - comprehensive authentication analysis"""
    result = {
        'url': url,
        'login_page': None,
        'rate_limiting': None,
        'account_lockout': None,
        'username_enumeration': None,
        'default_credentials': None,
        'issues': [],
        'summary': {}
    }
    
    try:
        # Find login page
        result['login_page'] = find_login_page(url)
        
        if result['login_page']:
            login_url = result['login_page']['url']
            
            # Test rate limiting
            result['rate_limiting'] = test_rate_limiting(login_url, requests_count=10)
            result['issues'].extend(result['rate_limiting'].get('issues', []))
            
            # Test account lockout
            result['account_lockout'] = test_account_lockout(login_url, attempts=5)
            result['issues'].extend(result['account_lockout'].get('issues', []))
            
            # Test username enumeration
            result['username_enumeration'] = test_username_enumeration(login_url)
            result['issues'].extend(result['username_enumeration'].get('issues', []))
            
            # Test default credentials (limited)
            result['default_credentials'] = test_default_credentials(login_url, max_attempts=5)
            result['issues'].extend(result['default_credentials'].get('issues', []))
        
        # Build summary
        result['summary'] = {
            'login_found': result['login_page'] is not None,
            'login_url': result['login_page']['url'] if result['login_page'] else None,
            'has_rate_limiting': result['rate_limiting']['rate_limited'] if result['rate_limiting'] else False,
            'has_lockout': result['account_lockout']['lockout_detected'] if result['account_lockout'] else False,
            'username_enumerable': result['username_enumeration']['enumerable'] if result['username_enumeration'] else False,
            'default_creds_found': len(result['default_credentials']['found']) if result['default_credentials'] else 0,
            'issue_count': len(result['issues']),
            'critical_issues': len([i for i in result['issues'] if i['severity'] == 'Critical']),
        }
        
    except Exception as e:
        result['error'] = str(e)
    
    return result
