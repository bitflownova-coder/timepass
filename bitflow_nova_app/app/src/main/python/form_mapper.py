# form_mapper.py
# Form & Input Mapping - Attack Surface Discovery

import re
from urllib.parse import urljoin, urlparse

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

# Form classification keywords
LOGIN_KEYWORDS = ['login', 'signin', 'sign-in', 'log-in', 'auth', 'authenticate', 'password']
SEARCH_KEYWORDS = ['search', 'query', 'find', 'q', 'keyword', 'term']
CONTACT_KEYWORDS = ['contact', 'message', 'inquiry', 'feedback', 'support']
UPLOAD_KEYWORDS = ['upload', 'file', 'attach', 'document', 'image']
REGISTER_KEYWORDS = ['register', 'signup', 'sign-up', 'create', 'new-user', 'join']
PAYMENT_KEYWORDS = ['payment', 'checkout', 'card', 'billing', 'purchase', 'order']

# CSRF token field names
CSRF_TOKEN_NAMES = [
    'csrf', 'csrftoken', 'csrf_token', 'csrf-token', '_csrf',
    'authenticity_token', 'token', '_token', 'xsrf', 'xsrf_token',
    '__requestverificationtoken', 'antiforgerytoken', 'anti-forgery-token'
]

# Risky parameter names that may indicate vulnerabilities
RISKY_PARAMS = {
    'injection': ['id', 'user_id', 'uid', 'account', 'query', 'search', 'name', 'email', 'order'],
    'path_traversal': ['file', 'path', 'folder', 'dir', 'document', 'doc', 'page', 'template', 'include'],
    'redirect': ['redirect', 'redirect_uri', 'redirect_url', 'next', 'url', 'return', 'return_to', 'returnTo', 'goto', 'target', 'destination', 'redir', 'continue', 'return_path', 'out', 'view', 'ref', 'callback'],
    'command': ['cmd', 'exec', 'command', 'run', 'execute', 'ping', 'shell'],
    'ssrf': ['url', 'uri', 'link', 'src', 'source', 'dest', 'destination', 'fetch', 'request']
}


def classify_form(form, action_url):
    """Classify a form based on its fields and action"""
    classifications = []
    
    # Get all input types and names
    inputs = form.find_all(['input', 'textarea', 'select', 'button'])
    input_types = [i.get('type', '').lower() for i in inputs if i.name == 'input']
    input_names = [i.get('name', '').lower() for i in inputs]
    buttons = [b.get_text().lower() for b in form.find_all(['button', 'input']) if b.get('type') in ['submit', 'button', None]]
    
    form_text = ' '.join(input_names + buttons + [action_url.lower()])
    
    # Login form
    if 'password' in input_types:
        if any(kw in form_text for kw in LOGIN_KEYWORDS):
            classifications.append('LOGIN')
        elif any(kw in form_text for kw in REGISTER_KEYWORDS):
            classifications.append('REGISTRATION')
        else:
            classifications.append('LOGIN')  # Default for password forms
    
    # Search form
    if any(kw in form_text for kw in SEARCH_KEYWORDS):
        classifications.append('SEARCH')
    
    # Contact form
    if 'textarea' in [i.name for i in inputs]:
        if any(kw in form_text for kw in CONTACT_KEYWORDS):
            classifications.append('CONTACT')
    
    # File upload
    if 'file' in input_types:
        classifications.append('FILE_UPLOAD')
    
    # Payment form
    if any(kw in form_text for kw in PAYMENT_KEYWORDS):
        classifications.append('PAYMENT')
    
    # Default
    if not classifications:
        classifications.append('OTHER')
    
    return classifications


def check_csrf_protection(form):
    """Check if form has CSRF protection"""
    hidden_inputs = form.find_all('input', {'type': 'hidden'})
    
    for input_field in hidden_inputs:
        name = (input_field.get('name') or '').lower()
        if any(csrf in name for csrf in CSRF_TOKEN_NAMES):
            return {
                'protected': True,
                'token_name': input_field.get('name'),
                'token_value_present': bool(input_field.get('value'))
            }
    
    return {
        'protected': False,
        'token_name': None,
        'token_value_present': False
    }


def analyze_input_security(form, form_url):
    """Analyze input fields for security issues"""
    issues = []
    
    # Check for password fields without autocomplete=off
    password_fields = form.find_all('input', {'type': 'password'})
    for pwd in password_fields:
        autocomplete = pwd.get('autocomplete', '').lower()
        if autocomplete not in ['off', 'new-password', 'current-password']:
            issues.append({
                'issue': 'Password field without autocomplete protection',
                'field': pwd.get('name', 'unnamed'),
                'severity': 'Low',
                'recommendation': 'Add autocomplete="off" or autocomplete="new-password"'
            })
    
    # Check if form action is HTTP (not HTTPS)
    action = form.get('action', '')
    if action:
        full_action = urljoin(form_url, action)
        if full_action.startswith('http://'):
            has_sensitive = bool(password_fields) or 'file' in [i.get('type', '') for i in form.find_all('input')]
            if has_sensitive:
                issues.append({
                    'issue': 'Sensitive form submitting to HTTP (not HTTPS)',
                    'severity': 'Critical',
                    'action_url': full_action,
                    'recommendation': 'Use HTTPS for form submission'
                })
    
    # Check for hidden fields that might leak info
    hidden_fields = form.find_all('input', {'type': 'hidden'})
    for hidden in hidden_fields:
        name = (hidden.get('name') or '').lower()
        value = hidden.get('value', '')
        
        # Check for potentially sensitive hidden values
        if any(s in name for s in ['user', 'admin', 'role', 'debug', 'test']):
            issues.append({
                'issue': 'Potentially sensitive hidden field',
                'field': hidden.get('name'),
                'value': value[:50] if value else '',
                'severity': 'Medium',
                'recommendation': 'Review if this field should be hidden or server-side only'
            })
    
    return issues


def extract_parameters(form):
    """Extract all parameters from a form"""
    params = []
    
    for input_field in form.find_all(['input', 'textarea', 'select']):
        name = input_field.get('name')
        if not name:
            continue
            
        param = {
            'name': name,
            'type': input_field.get('type', 'text') if input_field.name == 'input' else input_field.name,
            'required': input_field.has_attr('required'),
            'value': input_field.get('value', ''),
            'placeholder': input_field.get('placeholder', '')
        }
        
        # Check if parameter is risky
        name_lower = name.lower()
        for category, risky_names in RISKY_PARAMS.items():
            if any(r in name_lower for r in risky_names):
                param['risk_category'] = category
                param['risky'] = True
                break
        else:
            param['risky'] = False
        
        params.append(param)
    
    return params


def analyze_form(form, page_url):
    """Analyze a single form element"""
    action = form.get('action', '')
    method = form.get('method', 'GET').upper()
    enctype = form.get('enctype', '')
    
    # Resolve full action URL
    if action:
        full_action = urljoin(page_url, action)
    else:
        full_action = page_url
    
    # Classify the form
    classifications = classify_form(form, full_action)
    
    # Check CSRF protection
    csrf = check_csrf_protection(form)
    
    # Analyze input security
    security_issues = analyze_input_security(form, page_url)
    
    # CSRF vulnerability check for POST forms
    if method == 'POST' and not csrf['protected']:
        security_issues.append({
            'issue': 'POST form without CSRF token',
            'severity': 'High',
            'form_action': full_action,
            'recommendation': 'Add CSRF token to prevent cross-site request forgery'
        })
    
    # Extract parameters
    parameters = extract_parameters(form)
    
    # Risky parameters
    risky_params = [p for p in parameters if p.get('risky')]
    
    return {
        'action': full_action,
        'method': method,
        'enctype': enctype,
        'classifications': classifications,
        'csrf_protected': csrf['protected'],
        'csrf_token_name': csrf['token_name'],
        'parameters': parameters,
        'parameter_count': len(parameters),
        'risky_parameters': risky_params,
        'security_issues': security_issues,
        'has_file_upload': 'multipart/form-data' in enctype or any(p['type'] == 'file' for p in parameters),
        'has_password': any(p['type'] == 'password' for p in parameters)
    }


def map_forms(html_content, page_url):
    """
    Map all forms on a page
    
    Args:
        html_content: HTML content string
        page_url: URL of the page
    
    Returns:
        Dictionary with form analysis results
    """
    if not BeautifulSoup:
        return {'error': 'BeautifulSoup not available', 'forms': []}
    
    results = {
        'page_url': page_url,
        'forms': [],
        'summary': {
            'total_forms': 0,
            'login_forms': 0,
            'search_forms': 0,
            'file_uploads': 0,
            'payment_forms': 0,
            'forms_without_csrf': 0,
            'total_parameters': 0,
            'risky_parameters': 0,
            'security_issues': []
        }
    }
    
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        forms = soup.find_all('form')
        
        for form in forms:
            analysis = analyze_form(form, page_url)
            results['forms'].append(analysis)
            
            # Update summary
            results['summary']['total_forms'] += 1
            
            if 'LOGIN' in analysis['classifications']:
                results['summary']['login_forms'] += 1
            if 'SEARCH' in analysis['classifications']:
                results['summary']['search_forms'] += 1
            if 'FILE_UPLOAD' in analysis['classifications']:
                results['summary']['file_uploads'] += 1
            if 'PAYMENT' in analysis['classifications']:
                results['summary']['payment_forms'] += 1
            if not analysis['csrf_protected'] and analysis['method'] == 'POST':
                results['summary']['forms_without_csrf'] += 1
            
            results['summary']['total_parameters'] += len(analysis['parameters'])
            results['summary']['risky_parameters'] += len(analysis['risky_parameters'])
            results['summary']['security_issues'].extend(analysis['security_issues'])
            
    except Exception as e:
        results['error'] = str(e)
    
    return results


def extract_url_parameters(urls):
    """Extract all unique parameters from a list of URLs"""
    all_params = {}
    
    for url in urls:
        try:
            parsed = urlparse(url)
            query = parsed.query
            if query:
                pairs = query.split('&')
                for pair in pairs:
                    if '=' in pair:
                        key, value = pair.split('=', 1)
                        if key not in all_params:
                            all_params[key] = {
                                'name': key,
                                'occurrences': 0,
                                'example_values': [],
                                'risky': False
                            }
                        all_params[key]['occurrences'] += 1
                        if value and value not in all_params[key]['example_values'][:5]:
                            all_params[key]['example_values'].append(value[:50])
                        
                        # Check if risky
                        key_lower = key.lower()
                        for category, risky_names in RISKY_PARAMS.items():
                            if any(r in key_lower for r in risky_names):
                                all_params[key]['risky'] = True
                                all_params[key]['risk_category'] = category
                                break
        except:
            pass
    
    return list(all_params.values())


def get_form_mapping_summary(all_form_results):
    """Generate summary across all pages"""
    summary = {
        'pages_analyzed': len(all_form_results),
        'total_forms': 0,
        'form_types': {
            'login': 0,
            'registration': 0,
            'search': 0,
            'contact': 0,
            'file_upload': 0,
            'payment': 0,
            'other': 0
        },
        'security_stats': {
            'forms_without_csrf': 0,
            'http_form_actions': 0,
            'password_autocomplete_issues': 0
        },
        'total_parameters': 0,
        'risky_parameters': 0,
        'all_issues': []
    }
    
    for page_result in all_form_results:
        if 'summary' in page_result:
            s = page_result['summary']
            summary['total_forms'] += s.get('total_forms', 0)
            summary['form_types']['login'] += s.get('login_forms', 0)
            summary['form_types']['search'] += s.get('search_forms', 0)
            summary['form_types']['file_upload'] += s.get('file_uploads', 0)
            summary['form_types']['payment'] += s.get('payment_forms', 0)
            summary['security_stats']['forms_without_csrf'] += s.get('forms_without_csrf', 0)
            summary['total_parameters'] += s.get('total_parameters', 0)
            summary['risky_parameters'] += s.get('risky_parameters', 0)
            
            for issue in s.get('security_issues', []):
                summary['all_issues'].append({
                    'page': page_result.get('page_url', ''),
                    **issue
                })
    
    return summary
