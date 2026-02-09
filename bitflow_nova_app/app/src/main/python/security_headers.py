# security_headers.py
# Security Headers Scoring - CSP, HSTS, X-Frame-Options, grades A-F

import re
from urllib.parse import urlparse

try:
    import httpx
except ImportError:
    httpx = None

# Security headers to check and their weights
SECURITY_HEADERS = {
    'strict-transport-security': {
        'weight': 25,
        'name': 'HSTS (HTTP Strict Transport Security)',
        'description': 'Enforces secure HTTPS connections',
    },
    'content-security-policy': {
        'weight': 25,
        'name': 'CSP (Content Security Policy)',
        'description': 'Prevents XSS and data injection attacks',
    },
    'x-frame-options': {
        'weight': 15,
        'name': 'X-Frame-Options',
        'description': 'Prevents clickjacking attacks',
    },
    'x-content-type-options': {
        'weight': 10,
        'name': 'X-Content-Type-Options',
        'description': 'Prevents MIME-type sniffing',
    },
    'x-xss-protection': {
        'weight': 5,
        'name': 'X-XSS-Protection',
        'description': 'Legacy XSS filter (deprecated but still useful)',
    },
    'referrer-policy': {
        'weight': 10,
        'name': 'Referrer-Policy',
        'description': 'Controls referrer information leakage',
    },
    'permissions-policy': {
        'weight': 10,
        'name': 'Permissions-Policy',
        'description': 'Controls browser features and APIs',
    },
}

# Deprecated/dangerous headers
DEPRECATED_HEADERS = {
    'x-powered-by': {
        'penalty': 5,
        'reason': 'Reveals server technology',
    },
    'server': {
        'penalty': 3,
        'reason': 'Reveals server software (when detailed)',
    },
    'x-aspnet-version': {
        'penalty': 5,
        'reason': 'Reveals ASP.NET version',
    },
    'x-aspnetmvc-version': {
        'penalty': 5,
        'reason': 'Reveals ASP.NET MVC version',
    },
}

# CSP directive analysis
CSP_DIRECTIVES = {
    'default-src': {'critical': True, 'description': 'Default policy for loading resources'},
    'script-src': {'critical': True, 'description': 'Controls script execution'},
    'style-src': {'critical': False, 'description': 'Controls stylesheet loading'},
    'img-src': {'critical': False, 'description': 'Controls image loading'},
    'connect-src': {'critical': False, 'description': 'Controls AJAX/WebSocket connections'},
    'font-src': {'critical': False, 'description': 'Controls font loading'},
    'object-src': {'critical': True, 'description': 'Controls plugin content'},
    'media-src': {'critical': False, 'description': 'Controls audio/video'},
    'frame-src': {'critical': True, 'description': 'Controls iframe sources'},
    'frame-ancestors': {'critical': True, 'description': 'Controls framing (clickjacking)'},
    'base-uri': {'critical': True, 'description': 'Controls base element'},
    'form-action': {'critical': True, 'description': 'Controls form submissions'},
    'upgrade-insecure-requests': {'critical': False, 'description': 'Upgrades HTTP to HTTPS'},
    'block-all-mixed-content': {'critical': False, 'description': 'Blocks mixed content'},
}

# Unsafe CSP values
UNSAFE_CSP_VALUES = {
    "'unsafe-inline'": {'severity': 'High', 'description': 'Allows inline scripts/styles'},
    "'unsafe-eval'": {'severity': 'Critical', 'description': 'Allows eval() and similar'},
    "'unsafe-hashes'": {'severity': 'Medium', 'description': 'Allows specific inline handlers'},
    '*': {'severity': 'High', 'description': 'Allows any source'},
    'data:': {'severity': 'Medium', 'description': 'Allows data: URLs'},
    'blob:': {'severity': 'Medium', 'description': 'Allows blob: URLs'},
}


def get_headers(url, timeout=10):
    """Fetch headers from URL"""
    if not httpx:
        return None
    
    try:
        with httpx.Client(timeout=timeout, verify=False, follow_redirects=True) as client:
            response = client.get(url)
            return {
                'url': str(response.url),
                'status': response.status_code,
                'headers': dict(response.headers),
            }
    except Exception as e:
        return {'error': str(e)}


def analyze_hsts(value):
    """Analyze HSTS header"""
    analysis = {
        'present': True,
        'max_age': None,
        'include_subdomains': False,
        'preload': False,
        'issues': [],
        'score': 100,
    }
    
    value_lower = value.lower()
    
    # Parse max-age
    max_age_match = re.search(r'max-age=(\d+)', value_lower)
    if max_age_match:
        analysis['max_age'] = int(max_age_match.group(1))
        
        # Check if max-age is too short
        if analysis['max_age'] < 86400:  # Less than 1 day
            analysis['issues'].append({
                'severity': 'High',
                'issue': 'HSTS max-age is too short (< 1 day)',
                'recommendation': 'Set max-age to at least 31536000 (1 year)'
            })
            analysis['score'] -= 30
        elif analysis['max_age'] < 2592000:  # Less than 30 days
            analysis['issues'].append({
                'severity': 'Medium',
                'issue': 'HSTS max-age is short (< 30 days)',
                'recommendation': 'Set max-age to at least 31536000 (1 year)'
            })
            analysis['score'] -= 15
    else:
        analysis['issues'].append({
            'severity': 'High',
            'issue': 'HSTS missing max-age directive',
            'recommendation': 'Add max-age=31536000'
        })
        analysis['score'] -= 40
    
    # Check includeSubDomains
    if 'includesubdomains' in value_lower:
        analysis['include_subdomains'] = True
    else:
        analysis['issues'].append({
            'severity': 'Low',
            'issue': 'HSTS does not include subdomains',
            'recommendation': 'Consider adding includeSubDomains'
        })
        analysis['score'] -= 10
    
    # Check preload
    if 'preload' in value_lower:
        analysis['preload'] = True
    
    return analysis


def analyze_csp(value):
    """Analyze CSP header"""
    analysis = {
        'present': True,
        'directives': {},
        'issues': [],
        'warnings': [],
        'score': 100,
    }
    
    # Parse directives
    parts = value.split(';')
    for part in parts:
        part = part.strip()
        if not part:
            continue
        
        tokens = part.split()
        if tokens:
            directive = tokens[0].lower()
            values = tokens[1:] if len(tokens) > 1 else []
            analysis['directives'][directive] = values
    
    # Check for critical directives
    for directive, info in CSP_DIRECTIVES.items():
        if info['critical'] and directive not in analysis['directives']:
            # Check if covered by default-src
            if directive != 'default-src' and 'default-src' in analysis['directives']:
                continue
            analysis['issues'].append({
                'severity': 'Medium',
                'issue': f'Missing critical CSP directive: {directive}',
                'recommendation': f'Add {directive} to your CSP'
            })
            analysis['score'] -= 10
    
    # Check for unsafe values
    for directive, values in analysis['directives'].items():
        for unsafe, info in UNSAFE_CSP_VALUES.items():
            if unsafe in values:
                analysis['issues'].append({
                    'severity': info['severity'],
                    'issue': f'CSP contains {unsafe} in {directive}',
                    'recommendation': f'Remove {unsafe} and use nonces or hashes instead'
                })
                if info['severity'] == 'Critical':
                    analysis['score'] -= 25
                elif info['severity'] == 'High':
                    analysis['score'] -= 15
                else:
                    analysis['score'] -= 5
    
    # Check for report-uri or report-to
    if 'report-uri' not in analysis['directives'] and 'report-to' not in analysis['directives']:
        analysis['warnings'].append({
            'severity': 'Info',
            'issue': 'CSP has no reporting configured',
            'recommendation': 'Consider adding report-uri or report-to for violation monitoring'
        })
    
    # Check script-src specifically
    if 'script-src' in analysis['directives']:
        script_values = analysis['directives']['script-src']
        if "'strict-dynamic'" in script_values:
            analysis['warnings'].append({
                'severity': 'Info',
                'issue': 'CSP uses strict-dynamic (good for modern browsers)',
                'recommendation': 'Ensure fallbacks for older browsers'
            })
    
    return analysis


def analyze_x_frame_options(value):
    """Analyze X-Frame-Options header"""
    analysis = {
        'present': True,
        'value': value.upper(),
        'issues': [],
        'score': 100,
    }
    
    value_upper = value.upper().strip()
    
    if value_upper == 'DENY':
        # Best option
        pass
    elif value_upper == 'SAMEORIGIN':
        # Good option
        analysis['issues'].append({
            'severity': 'Info',
            'issue': 'X-Frame-Options allows same-origin framing',
            'recommendation': 'Use DENY if framing is not needed'
        })
    elif value_upper.startswith('ALLOW-FROM'):
        analysis['issues'].append({
            'severity': 'Medium',
            'issue': 'ALLOW-FROM is deprecated and not widely supported',
            'recommendation': 'Use CSP frame-ancestors instead'
        })
        analysis['score'] -= 15
    else:
        analysis['issues'].append({
            'severity': 'High',
            'issue': f'Invalid X-Frame-Options value: {value}',
            'recommendation': 'Use DENY or SAMEORIGIN'
        })
        analysis['score'] -= 30
    
    return analysis


def analyze_x_content_type_options(value):
    """Analyze X-Content-Type-Options header"""
    analysis = {
        'present': True,
        'value': value,
        'issues': [],
        'score': 100,
    }
    
    if value.lower().strip() != 'nosniff':
        analysis['issues'].append({
            'severity': 'Medium',
            'issue': f'Invalid X-Content-Type-Options value: {value}',
            'recommendation': 'Use nosniff'
        })
        analysis['score'] -= 50
    
    return analysis


def analyze_referrer_policy(value):
    """Analyze Referrer-Policy header"""
    analysis = {
        'present': True,
        'value': value,
        'issues': [],
        'score': 100,
    }
    
    safe_policies = [
        'no-referrer',
        'no-referrer-when-downgrade',
        'origin',
        'origin-when-cross-origin',
        'same-origin',
        'strict-origin',
        'strict-origin-when-cross-origin',
    ]
    
    unsafe_policies = [
        'unsafe-url',
    ]
    
    value_lower = value.lower().strip()
    
    if value_lower in unsafe_policies:
        analysis['issues'].append({
            'severity': 'High',
            'issue': 'Referrer-Policy uses unsafe-url which leaks full URL',
            'recommendation': 'Use strict-origin-when-cross-origin or more restrictive policy'
        })
        analysis['score'] -= 40
    elif value_lower not in safe_policies:
        analysis['issues'].append({
            'severity': 'Medium',
            'issue': f'Unknown Referrer-Policy value: {value}',
            'recommendation': 'Use strict-origin-when-cross-origin'
        })
        analysis['score'] -= 20
    
    return analysis


def analyze_permissions_policy(value):
    """Analyze Permissions-Policy header"""
    analysis = {
        'present': True,
        'features': {},
        'issues': [],
        'score': 100,
    }
    
    # Parse permissions
    parts = value.split(',')
    for part in parts:
        part = part.strip()
        if '=' in part:
            feature, allowed = part.split('=', 1)
            analysis['features'][feature.strip()] = allowed.strip()
    
    # Check for dangerous permissions
    dangerous_features = ['camera', 'microphone', 'geolocation', 'usb', 'payment']
    for feature in dangerous_features:
        if feature in analysis['features']:
            allowed = analysis['features'][feature]
            if allowed == '*' or allowed == '("*")':
                analysis['issues'].append({
                    'severity': 'Medium',
                    'issue': f'Permissions-Policy allows {feature} from any origin',
                    'recommendation': f'Restrict {feature} to self only if not needed elsewhere'
                })
                analysis['score'] -= 5
    
    return analysis


def check_deprecated_headers(headers):
    """Check for deprecated or information-leaking headers"""
    issues = []
    penalty = 0
    
    for header, info in DEPRECATED_HEADERS.items():
        if header in headers:
            value = headers[header]
            # Server header with version info is more concerning
            if header == 'server':
                if any(c.isdigit() for c in value):  # Contains version numbers
                    issues.append({
                        'severity': 'Medium',
                        'header': header,
                        'value': value,
                        'issue': f'Server header reveals version: {value}',
                        'recommendation': 'Remove version information from Server header'
                    })
                    penalty += info['penalty']
            else:
                issues.append({
                    'severity': 'Low',
                    'header': header,
                    'value': value,
                    'issue': f'{info["reason"]}: {value}',
                    'recommendation': f'Remove {header} header'
                })
                penalty += info['penalty']
    
    return issues, penalty


def calculate_grade(score):
    """Calculate letter grade from score"""
    if score >= 90:
        return 'A'
    elif score >= 80:
        return 'B'
    elif score >= 70:
        return 'C'
    elif score >= 60:
        return 'D'
    elif score >= 50:
        return 'E'
    else:
        return 'F'


def analyze_security_headers(url):
    """Main function - comprehensive security headers analysis"""
    result = {
        'url': url,
        'headers': {},
        'present_headers': [],
        'missing_headers': [],
        'deprecated_headers': [],
        'header_analysis': {},
        'issues': [],
        'recommendations': [],
        'score': 0,
        'max_score': 100,
        'grade': 'F',
        'summary': {}
    }
    
    # Fetch headers
    response = get_headers(url)
    if not response or 'error' in response:
        result['error'] = response.get('error', 'Failed to fetch headers')
        return result
    
    headers = {k.lower(): v for k, v in response['headers'].items()}
    result['headers'] = headers
    result['final_url'] = response['url']
    
    score = 0
    max_score = 0
    
    # Check each security header
    for header, info in SECURITY_HEADERS.items():
        max_score += info['weight']
        
        if header in headers:
            result['present_headers'].append({
                'name': header,
                'display_name': info['name'],
                'value': headers[header],
                'description': info['description'],
            })
            
            # Analyze specific headers
            header_score = info['weight']
            if header == 'strict-transport-security':
                analysis = analyze_hsts(headers[header])
                result['header_analysis'][header] = analysis
                header_score = info['weight'] * (analysis['score'] / 100)
                result['issues'].extend(analysis['issues'])
            elif header == 'content-security-policy':
                analysis = analyze_csp(headers[header])
                result['header_analysis'][header] = analysis
                header_score = info['weight'] * (analysis['score'] / 100)
                result['issues'].extend(analysis['issues'])
            elif header == 'x-frame-options':
                analysis = analyze_x_frame_options(headers[header])
                result['header_analysis'][header] = analysis
                header_score = info['weight'] * (analysis['score'] / 100)
                result['issues'].extend(analysis['issues'])
            elif header == 'x-content-type-options':
                analysis = analyze_x_content_type_options(headers[header])
                result['header_analysis'][header] = analysis
                header_score = info['weight'] * (analysis['score'] / 100)
                result['issues'].extend(analysis['issues'])
            elif header == 'referrer-policy':
                analysis = analyze_referrer_policy(headers[header])
                result['header_analysis'][header] = analysis
                header_score = info['weight'] * (analysis['score'] / 100)
                result['issues'].extend(analysis['issues'])
            elif header == 'permissions-policy':
                analysis = analyze_permissions_policy(headers[header])
                result['header_analysis'][header] = analysis
                header_score = info['weight'] * (analysis['score'] / 100)
                result['issues'].extend(analysis['issues'])
            
            score += header_score
        else:
            result['missing_headers'].append({
                'name': header,
                'display_name': info['name'],
                'description': info['description'],
                'weight': info['weight'],
            })
            result['recommendations'].append({
                'priority': 'High' if info['weight'] >= 20 else 'Medium',
                'header': header,
                'recommendation': f'Add {info["name"]} header'
            })
    
    # Check for deprecated headers
    deprecated_issues, penalty = check_deprecated_headers(headers)
    result['deprecated_headers'] = deprecated_issues
    result['issues'].extend([{'severity': i['severity'], 'issue': i['issue'], 'recommendation': i['recommendation']} for i in deprecated_issues])
    score = max(0, score - penalty)
    
    # Calculate final score (normalized to 100)
    result['score'] = round((score / max_score) * 100) if max_score > 0 else 0
    result['max_score'] = 100
    result['grade'] = calculate_grade(result['score'])
    
    # Build summary
    result['summary'] = {
        'present_count': len(result['present_headers']),
        'missing_count': len(result['missing_headers']),
        'deprecated_count': len(result['deprecated_headers']),
        'issue_count': len(result['issues']),
        'has_hsts': 'strict-transport-security' in headers,
        'has_csp': 'content-security-policy' in headers,
        'has_xfo': 'x-frame-options' in headers,
        'has_xcto': 'x-content-type-options' in headers,
        'has_referrer': 'referrer-policy' in headers,
        'has_permissions': 'permissions-policy' in headers,
        'score': result['score'],
        'grade': result['grade'],
    }
    
    return result


def get_header_recommendations(analysis_result):
    """Generate header implementation recommendations"""
    recommendations = []
    
    for missing in analysis_result.get('missing_headers', []):
        header = missing['name']
        
        if header == 'strict-transport-security':
            recommendations.append({
                'header': 'Strict-Transport-Security',
                'value': 'max-age=31536000; includeSubDomains; preload',
                'priority': 'Critical',
            })
        elif header == 'content-security-policy':
            recommendations.append({
                'header': 'Content-Security-Policy',
                'value': "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
                'priority': 'Critical',
            })
        elif header == 'x-frame-options':
            recommendations.append({
                'header': 'X-Frame-Options',
                'value': 'DENY',
                'priority': 'High',
            })
        elif header == 'x-content-type-options':
            recommendations.append({
                'header': 'X-Content-Type-Options',
                'value': 'nosniff',
                'priority': 'High',
            })
        elif header == 'referrer-policy':
            recommendations.append({
                'header': 'Referrer-Policy',
                'value': 'strict-origin-when-cross-origin',
                'priority': 'Medium',
            })
        elif header == 'permissions-policy':
            recommendations.append({
                'header': 'Permissions-Policy',
                'value': 'camera=(), microphone=(), geolocation=()',
                'priority': 'Medium',
            })
    
    return recommendations
