# js_analyzer.py
# JavaScript Static Analysis - Secret Detection, API Discovery, DOM Sinks

import re
import os
from urllib.parse import urljoin, urlparse

try:
    import httpx
except ImportError:
    httpx = None

# Secret patterns database - 25+ patterns
SECRET_PATTERNS = {
    'google_api_key': {
        'pattern': r'AIza[0-9A-Za-z\-_]{35}',
        'severity': 'High',
        'description': 'Google API Key'
    },
    'aws_access_key': {
        'pattern': r'AKIA[0-9A-Z]{16}',
        'severity': 'Critical',
        'description': 'AWS Access Key ID'
    },
    'aws_secret_key': {
        'pattern': r'(?<![A-Za-z0-9/+=])[A-Za-z0-9/+=]{40}(?![A-Za-z0-9/+=])',
        'severity': 'Critical',
        'description': 'Potential AWS Secret Key'
    },
    'stripe_secret': {
        'pattern': r'sk_live_[0-9a-zA-Z]{24,}',
        'severity': 'Critical',
        'description': 'Stripe Secret Key'
    },
    'stripe_publishable': {
        'pattern': r'pk_live_[0-9a-zA-Z]{24,}',
        'severity': 'Medium',
        'description': 'Stripe Publishable Key'
    },
    'github_token': {
        'pattern': r'ghp_[0-9a-zA-Z]{36}',
        'severity': 'Critical',
        'description': 'GitHub Personal Access Token'
    },
    'github_oauth': {
        'pattern': r'gho_[0-9a-zA-Z]{36}',
        'severity': 'Critical',
        'description': 'GitHub OAuth Token'
    },
    'gitlab_token': {
        'pattern': r'glpat-[0-9a-zA-Z\-]{20,}',
        'severity': 'Critical',
        'description': 'GitLab Personal Access Token'
    },
    'slack_token': {
        'pattern': r'xox[baprs]-[0-9a-zA-Z]{10,48}',
        'severity': 'Critical',
        'description': 'Slack Token'
    },
    'slack_webhook': {
        'pattern': r'https://hooks\.slack\.com/services/T[a-zA-Z0-9_]+/B[a-zA-Z0-9_]+/[a-zA-Z0-9_]+',
        'severity': 'High',
        'description': 'Slack Webhook URL'
    },
    'firebase_url': {
        'pattern': r'[a-z0-9\-]+\.firebaseio\.com',
        'severity': 'Medium',
        'description': 'Firebase Database URL'
    },
    'firebase_api_key': {
        'pattern': r'AIza[0-9A-Za-z\-_]{35}',
        'severity': 'High',
        'description': 'Firebase API Key'
    },
    'private_key': {
        'pattern': r'-----BEGIN (RSA|EC|DSA|OPENSSH|PGP) PRIVATE KEY-----',
        'severity': 'Critical',
        'description': 'Private Key'
    },
    'jwt_token': {
        'pattern': r'eyJ[A-Za-z0-9\-_]+\.eyJ[A-Za-z0-9\-_]+\.[A-Za-z0-9\-_.+/=]*',
        'severity': 'High',
        'description': 'JWT Token'
    },
    'basic_auth': {
        'pattern': r'[Bb]asic\s+[A-Za-z0-9+/=]{20,}',
        'severity': 'High',
        'description': 'Basic Auth Credentials'
    },
    'bearer_token': {
        'pattern': r'[Bb]earer\s+[A-Za-z0-9_\-\.]{20,}',
        'severity': 'High',
        'description': 'Bearer Token'
    },
    'twilio_api_key': {
        'pattern': r'SK[0-9a-fA-F]{32}',
        'severity': 'High',
        'description': 'Twilio API Key'
    },
    'sendgrid_api_key': {
        'pattern': r'SG\.[0-9A-Za-z\-_]{22}\.[0-9A-Za-z\-_]{43}',
        'severity': 'Critical',
        'description': 'SendGrid API Key'
    },
    'mailgun_api_key': {
        'pattern': r'key-[0-9a-zA-Z]{32}',
        'severity': 'High',
        'description': 'Mailgun API Key'
    },
    'discord_token': {
        'pattern': r'[MN][A-Za-z\d]{23,}\.[\w-]{6}\.[\w-]{27}',
        'severity': 'Critical',
        'description': 'Discord Bot Token'
    },
    'heroku_api_key': {
        'pattern': r'[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}',
        'severity': 'High',
        'description': 'Heroku API Key (UUID format)'
    },
    'square_access_token': {
        'pattern': r'sq0atp-[0-9A-Za-z\-_]{22}',
        'severity': 'Critical',
        'description': 'Square Access Token'
    },
    'shopify_token': {
        'pattern': r'shpat_[0-9a-fA-F]{32}',
        'severity': 'Critical',
        'description': 'Shopify Access Token'
    },
    'paypal_token': {
        'pattern': r'access_token\$production\$[0-9a-z]{16}\$[0-9a-f]{32}',
        'severity': 'Critical',
        'description': 'PayPal Access Token'
    },
    'telegram_bot_token': {
        'pattern': r'[0-9]{8,10}:[a-zA-Z0-9_-]{35}',
        'severity': 'High',
        'description': 'Telegram Bot Token'
    },
    'password_in_url': {
        'pattern': r'[a-zA-Z]{3,10}://[^/\s:@]+:[^/\s:@]+@[^/\s]+',
        'severity': 'Critical',
        'description': 'Password in URL'
    },
    'generic_secret': {
        'pattern': r'(?i)(api[_-]?key|apikey|secret|password|passwd|pwd|token)["\']?\s*[:=]\s*["\'][a-zA-Z0-9_\-]{16,}["\']',
        'severity': 'High',
        'description': 'Generic Secret/API Key'
    }
}

# API endpoint patterns
API_PATTERNS = [
    r'/api/v[0-9]+/',
    r'/api/',
    r'/v[0-9]+/',
    r'/graphql',
    r'/rest/',
    r'/services/',
    r'\.json\b',
    r'/ajax/',
    r'/xhr/',
]

# WebSocket patterns
WEBSOCKET_PATTERNS = [
    r'wss?://[^\s"\')]+',
]

# SPA Route patterns (React, Vue, Angular)
SPA_ROUTE_PATTERNS = [
    r'path:\s*["\']([^"\']+)["\']',  # React Router
    r'route:\s*["\']([^"\']+)["\']',  # Generic
    r'to:\s*["\']([^"\']+)["\']',     # Link components
    r'navigate\(["\']([^"\']+)["\']',  # Navigation
    r'history\.push\(["\']([^"\']+)["\']',  # React history
    r'\$router\.push\(["\']([^"\']+)["\']',  # Vue router
    r'routerLink=["\']([^"\']+)["\']',  # Angular
]

# Dangerous DOM sinks
DOM_SINKS = {
    'xss_sinks': [
        'innerHTML', 'outerHTML', 'insertAdjacentHTML',
        'document.write', 'document.writeln'
    ],
    'eval_sinks': [
        'eval(', 'setTimeout(', 'setInterval(', 'Function(',
        'execScript('
    ],
    'redirect_sinks': [
        'location.href', 'location.replace', 'location.assign',
        'window.open(', 'location ='
    ],
    'storage_sinks': [
        'localStorage.setItem', 'sessionStorage.setItem',
        'document.cookie'
    ]
}

# Developer comments patterns
DEV_COMMENT_PATTERNS = [
    r'//\s*TODO[:\s].*',
    r'//\s*FIXME[:\s].*',
    r'//\s*HACK[:\s].*',
    r'//\s*BUG[:\s].*',
    r'//\s*XXX[:\s].*',
    r'//\s*DEBUG[:\s].*',
    r'/\*\s*TODO[:\s][^*]*\*/',
    r'/\*\s*FIXME[:\s][^*]*\*/',
]


def download_js_file(url, user_agent='Mozilla/5.0', timeout=10):
    """Download a JavaScript file"""
    if not httpx:
        return None
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True, verify=False) as client:
            response = client.get(url, headers={'User-Agent': user_agent})
            if response.status_code == 200:
                return response.text
    except:
        pass
    return None


def check_source_map(js_url, user_agent='Mozilla/5.0'):
    """Check if source map exists for a JS file"""
    source_maps = []
    map_urls = [
        js_url + '.map',
        js_url.replace('.min.js', '.js.map'),
        js_url.replace('.js', '.js.map'),
    ]
    
    if not httpx:
        return source_maps
        
    for map_url in set(map_urls):
        try:
            with httpx.Client(timeout=5, follow_redirects=True, verify=False) as client:
                response = client.head(map_url, headers={'User-Agent': user_agent})
                if response.status_code == 200:
                    source_maps.append({
                        'url': map_url,
                        'severity': 'High',
                        'issue': 'Source map exposed - original source code accessible'
                    })
        except:
            pass
    return source_maps


def scan_for_secrets(js_content, js_url):
    """Scan JavaScript content for hardcoded secrets"""
    findings = []
    
    for secret_name, config in SECRET_PATTERNS.items():
        try:
            matches = re.findall(config['pattern'], js_content)
            for match in matches:
                # Avoid false positives
                if len(match) < 10:
                    continue
                if match.lower() in ['undefined', 'null', 'true', 'false']:
                    continue
                    
                findings.append({
                    'type': secret_name,
                    'description': config['description'],
                    'severity': config['severity'],
                    'value': match[:50] + '...' if len(match) > 50 else match,
                    'source': js_url
                })
        except:
            pass
    
    return findings


def extract_api_endpoints(js_content, base_url):
    """Extract API endpoints from JavaScript"""
    endpoints = set()
    
    # Extract quoted strings that look like API paths
    url_patterns = [
        r'["\'](/api[^"\']*)["\']',
        r'["\'](/v[0-9]+[^"\']*)["\']',
        r'["\']([^"\']*\.json)["\']',
        r'fetch\(["\']([^"\']+)["\']',
        r'axios\.[a-z]+\(["\']([^"\']+)["\']',
        r'\$\.(?:get|post|ajax)\(["\']([^"\']+)["\']',
        r'XMLHttpRequest.*open\([^,]+,\s*["\']([^"\']+)["\']',
    ]
    
    for pattern in url_patterns:
        try:
            matches = re.findall(pattern, js_content)
            for match in matches:
                if match.startswith('/'):
                    full_url = urljoin(base_url, match)
                    endpoints.add(full_url)
                elif match.startswith('http'):
                    endpoints.add(match)
        except:
            pass
    
    return list(endpoints)


def extract_websocket_endpoints(js_content):
    """Extract WebSocket endpoints"""
    websockets = set()
    
    for pattern in WEBSOCKET_PATTERNS:
        try:
            matches = re.findall(pattern, js_content)
            websockets.update(matches)
        except:
            pass
    
    return list(websockets)


def extract_spa_routes(js_content):
    """Extract SPA routes from JavaScript"""
    routes = set()
    
    for pattern in SPA_ROUTE_PATTERNS:
        try:
            matches = re.findall(pattern, js_content)
            for match in matches:
                if match.startswith('/') and len(match) > 1:
                    routes.add(match)
        except:
            pass
    
    return list(routes)


def detect_dom_sinks(js_content, js_url):
    """Detect potentially dangerous DOM sinks"""
    findings = []
    
    for category, sinks in DOM_SINKS.items():
        for sink in sinks:
            if sink in js_content:
                # Count occurrences
                count = js_content.count(sink)
                findings.append({
                    'sink': sink,
                    'category': category,
                    'count': count,
                    'severity': 'High' if category in ['xss_sinks', 'eval_sinks'] else 'Medium',
                    'source': js_url
                })
    
    return findings


def extract_dev_comments(js_content, js_url):
    """Extract developer comments that might leak info"""
    comments = []
    
    for pattern in DEV_COMMENT_PATTERNS:
        try:
            matches = re.findall(pattern, js_content, re.IGNORECASE)
            for match in matches:
                comments.append({
                    'comment': match[:200],
                    'source': js_url,
                    'severity': 'Low'
                })
        except:
            pass
    
    return comments


def analyze_javascript(js_urls, base_url, user_agent='Mozilla/5.0', output_dir=None):
    """
    Main function to analyze all JavaScript files
    
    Args:
        js_urls: List of JavaScript URLs to analyze
        base_url: Base URL of the site
        user_agent: User agent string
        output_dir: Optional directory to save downloaded JS files
    
    Returns:
        Dictionary with all findings
    """
    results = {
        'scripts_analyzed': 0,
        'secrets': [],
        'api_endpoints': [],
        'websockets': [],
        'spa_routes': [],
        'dom_sinks': [],
        'dev_comments': [],
        'source_maps': [],
        'errors': []
    }
    
    all_endpoints = set()
    all_websockets = set()
    all_routes = set()
    
    for js_url in js_urls:
        try:
            # Download JS file
            js_content = download_js_file(js_url, user_agent)
            if not js_content:
                continue
            
            results['scripts_analyzed'] += 1
            
            # Save JS file if output_dir provided
            if output_dir:
                js_dir = os.path.join(output_dir, 'scripts')
                os.makedirs(js_dir, exist_ok=True)
                filename = urlparse(js_url).path.split('/')[-1] or 'script.js'
                filepath = os.path.join(js_dir, filename)
                try:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(js_content)
                except:
                    pass
            
            # Check for source maps
            source_maps = check_source_map(js_url, user_agent)
            results['source_maps'].extend(source_maps)
            
            # Scan for secrets
            secrets = scan_for_secrets(js_content, js_url)
            results['secrets'].extend(secrets)
            
            # Extract API endpoints
            endpoints = extract_api_endpoints(js_content, base_url)
            all_endpoints.update(endpoints)
            
            # Extract WebSocket endpoints
            websockets = extract_websocket_endpoints(js_content)
            all_websockets.update(websockets)
            
            # Extract SPA routes
            routes = extract_spa_routes(js_content)
            all_routes.update(routes)
            
            # Detect DOM sinks
            dom_sinks = detect_dom_sinks(js_content, js_url)
            results['dom_sinks'].extend(dom_sinks)
            
            # Extract dev comments
            comments = extract_dev_comments(js_content, js_url)
            results['dev_comments'].extend(comments)
            
        except Exception as e:
            results['errors'].append({'url': js_url, 'error': str(e)})
    
    results['api_endpoints'] = list(all_endpoints)
    results['websockets'] = list(all_websockets)
    results['spa_routes'] = list(all_routes)
    
    return results


def get_js_analysis_summary(results):
    """Generate a summary of JS analysis findings"""
    critical = len([s for s in results['secrets'] if s['severity'] == 'Critical'])
    high = len([s for s in results['secrets'] if s['severity'] == 'High'])
    high += len([s for s in results['dom_sinks'] if s['severity'] == 'High'])
    high += len(results['source_maps'])
    
    return {
        'scripts_analyzed': results['scripts_analyzed'],
        'secrets_found': len(results['secrets']),
        'critical_secrets': critical,
        'high_severity': high,
        'api_endpoints': len(results['api_endpoints']),
        'websockets': len(results['websockets']),
        'spa_routes': len(results['spa_routes']),
        'dom_sinks': len(results['dom_sinks']),
        'source_maps_exposed': len(results['source_maps'])
    }
