# version_detector.py
# Software Version Detection and CVE Mapping

import re

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

# Version extraction patterns
VERSION_PATTERNS = {
    # CMS
    'wordpress': [
        (r'wp-content', 'WordPress'),
        (r'<meta name="generator" content="WordPress\s*([\d.]+)', 'WordPress'),
        (r'wp-includes/js/wp-embed\.min\.js\?ver=([\d.]+)', 'WordPress'),
    ],
    'drupal': [
        (r'Drupal\s*([\d.]+)', 'Drupal'),
        (r'/misc/drupal\.js', 'Drupal'),
        (r'X-Generator:\s*Drupal\s*([\d.]+)', 'Drupal'),
    ],
    'joomla': [
        (r'Joomla!?\s*([\d.]+)', 'Joomla'),
        (r'/media/jui/', 'Joomla'),
    ],
    'magento': [
        (r'Mage\.Cookies', 'Magento'),
        (r'/static/version[\d]+/', 'Magento'),
    ],
    'shopify': [
        (r'cdn\.shopify\.com', 'Shopify'),
        (r'Shopify\.theme', 'Shopify'),
    ],
    'wix': [
        (r'static\.wixstatic\.com', 'Wix'),
        (r'wix-code-sdk', 'Wix'),
    ],
    'squarespace': [
        (r'static\.squarespace\.com', 'Squarespace'),
        (r'Squarespace', 'Squarespace'),
    ],
    'ghost': [
        (r'ghost\.org', 'Ghost'),
        (r'content="Ghost\s*([\d.]+)', 'Ghost'),
    ],
    
    # Frameworks
    'react': [
        (r'react[\.\-]?([\d.]+)?\.(?:min\.)?js', 'React'),
        (r'__react_devtools', 'React'),
        (r'data-reactroot', 'React'),
    ],
    'angular': [
        (r'angular[\/\.\-]?([\d.]+)?(?:\.min)?\.js', 'Angular'),
        (r'ng-version="([\d.]+)"', 'Angular'),
        (r'ng-app', 'AngularJS'),
    ],
    'vue': [
        (r'vue[\/\.\-]?([\d.]+)?(?:\.min)?\.js', 'Vue.js'),
        (r'data-v-', 'Vue.js'),
    ],
    'jquery': [
        (r'jquery[\/\.\-]([\d.]+)(?:\.min)?\.js', 'jQuery'),
        (r'jQuery v([\d.]+)', 'jQuery'),
    ],
    'bootstrap': [
        (r'bootstrap[\/\.\-]([\d.]+)', 'Bootstrap'),
        (r'Bootstrap v([\d.]+)', 'Bootstrap'),
    ],
    'lodash': [
        (r'lodash[\/\.\-]([\d.]+)', 'Lodash'),
    ],
    'moment': [
        (r'moment[\/\.\-]([\d.]+)', 'Moment.js'),
    ],
    
    # Servers
    'nginx': [
        (r'nginx[\/]?([\d.]+)?', 'Nginx'),
    ],
    'apache': [
        (r'Apache[\/]?([\d.]+)?', 'Apache'),
    ],
    'iis': [
        (r'Microsoft-IIS[\/]([\d.]+)', 'Microsoft IIS'),
    ],
    'express': [
        (r'X-Powered-By:\s*Express', 'Express.js'),
    ],
    
    # Languages
    'php': [
        (r'X-Powered-By:\s*PHP[\/]?([\d.]+)?', 'PHP'),
    ],
    'asp_net': [
        (r'X-AspNet-Version:\s*([\d.]+)', 'ASP.NET'),
        (r'X-Powered-By:\s*ASP\.NET', 'ASP.NET'),
    ],
    
    # Analytics / Marketing
    'google_analytics': [
        (r'google-analytics\.com/analytics\.js', 'Google Analytics'),
        (r'gtag\(|gtm\.js', 'Google Tag Manager'),
        (r'UA-\d+-\d+', 'Google Analytics'),
        (r'G-[A-Z0-9]+', 'Google Analytics 4'),
    ],
    'hotjar': [
        (r'static\.hotjar\.com', 'Hotjar'),
    ],
    'mixpanel': [
        (r'mixpanel\.com', 'Mixpanel'),
    ],
    
    # CDN
    'cloudflare': [
        (r'cloudflare', 'Cloudflare'),
        (r'cf-ray', 'Cloudflare'),
    ],
    'akamai': [
        (r'akamai', 'Akamai'),
    ],
    'fastly': [
        (r'fastly', 'Fastly'),
    ],
}

# Known vulnerable versions (simplified database)
# Format: software -> [(version_range, CVE, severity, description)]
VULNERABILITY_DATABASE = {
    'jquery': [
        ('< 1.9.0', 'CVE-2011-4969', 'Medium', 'XSS vulnerability in jQuery'),
        ('< 1.12.0', 'CVE-2015-9251', 'Medium', 'XSS when ajax content contains script tags'),
        ('< 3.5.0', 'CVE-2020-11022', 'Medium', 'XSS in htmlPrefilter'),
        ('< 3.5.0', 'CVE-2020-11023', 'Medium', 'XSS when passing HTML to manipulation methods'),
    ],
    'angular': [
        ('< 1.6.0', 'CVE-2019-10768', 'High', 'Prototype pollution in angular.merge'),
        ('< 1.6.9', 'CVE-2020-7676', 'Medium', 'XSS in angular.js'),
    ],
    'bootstrap': [
        ('< 3.4.0', 'CVE-2018-14040', 'Medium', 'XSS in collapse data-parent'),
        ('< 3.4.0', 'CVE-2018-14041', 'Medium', 'XSS in tooltip data-container'),
        ('< 3.4.0', 'CVE-2018-14042', 'Medium', 'XSS in data-target attribute'),
    ],
    'wordpress': [
        ('< 5.8.3', 'CVE-2022-21661', 'High', 'SQL Injection via WP_Query'),
        ('< 5.8.3', 'CVE-2022-21662', 'Medium', 'Stored XSS via post slugs'),
        ('< 5.8.3', 'CVE-2022-21664', 'High', 'SQL Injection via WP_Meta_Query'),
    ],
    'drupal': [
        ('< 7.58', 'CVE-2018-7600', 'Critical', 'Drupalgeddon 2 - Remote Code Execution'),
        ('< 8.5.1', 'CVE-2018-7600', 'Critical', 'Drupalgeddon 2 - Remote Code Execution'),
    ],
    'lodash': [
        ('< 4.17.12', 'CVE-2019-10744', 'High', 'Prototype Pollution'),
        ('< 4.17.21', 'CVE-2021-23337', 'High', 'Command Injection'),
    ],
    'moment': [
        ('< 2.29.2', 'CVE-2022-24785', 'High', 'Path Traversal'),
        ('< 2.29.4', 'CVE-2022-31129', 'High', 'ReDoS'),
    ],
    'apache': [
        ('< 2.4.50', 'CVE-2021-41773', 'Critical', 'Path Traversal and RCE'),
        ('< 2.4.51', 'CVE-2021-42013', 'Critical', 'Path Traversal and RCE'),
    ],
    'nginx': [
        ('< 1.17.7', 'CVE-2019-20372', 'Medium', 'HTTP Request Smuggling'),
    ],
    'php': [
        ('< 7.3.29', 'CVE-2021-21702', 'Medium', 'NULL pointer deref in SOAP'),
        ('< 8.0.8', 'CVE-2021-21705', 'Medium', 'SSRF bypass in FILTER_VALIDATE_URL'),
    ],
}


def parse_version(version_str):
    """Parse version string to comparable tuple"""
    if not version_str:
        return None
    try:
        parts = re.findall(r'\d+', version_str)
        return tuple(int(p) for p in parts[:4])
    except:
        return None


def compare_versions(version, condition):
    """Compare version against condition like '< 3.5.0'"""
    match = re.match(r'([<>=!]+)\s*([\d.]+)', condition)
    if not match:
        return False
    
    operator, target = match.groups()
    v1 = parse_version(version)
    v2 = parse_version(target)
    
    if not v1 or not v2:
        return False
    
    # Pad versions to same length
    max_len = max(len(v1), len(v2))
    v1 = v1 + (0,) * (max_len - len(v1))
    v2 = v2 + (0,) * (max_len - len(v2))
    
    if operator == '<':
        return v1 < v2
    elif operator == '<=':
        return v1 <= v2
    elif operator == '>':
        return v1 > v2
    elif operator == '>=':
        return v1 >= v2
    elif operator == '==':
        return v1 == v2
    elif operator == '!=':
        return v1 != v2
    
    return False


def detect_from_html(html_content):
    """Detect technologies from HTML content"""
    detections = []
    
    for tech_key, patterns in VERSION_PATTERNS.items():
        for pattern_tuple in patterns:
            pattern = pattern_tuple[0]
            name = pattern_tuple[1]
            
            match = re.search(pattern, html_content, re.IGNORECASE)
            if match:
                version = None
                if match.groups():
                    version = match.group(1) if match.group(1) else None
                
                # Check if already detected
                existing = next((d for d in detections if d['key'] == tech_key), None)
                if existing:
                    if version and not existing.get('version'):
                        existing['version'] = version
                else:
                    detections.append({
                        'key': tech_key,
                        'name': name,
                        'version': version,
                        'source': 'html',
                        'pattern_matched': pattern[:50]
                    })
    
    return detections


def detect_from_headers(headers):
    """Detect technologies from HTTP headers"""
    detections = []
    
    header_patterns = {
        'Server': [
            (r'nginx[\/]?([\d.]+)?', 'nginx', 'Nginx'),
            (r'Apache[\/]?([\d.]+)?', 'apache', 'Apache'),
            (r'Microsoft-IIS[\/]?([\d.]+)?', 'iis', 'Microsoft IIS'),
            (r'cloudflare', 'cloudflare', 'Cloudflare'),
            (r'AmazonS3', 'aws_s3', 'Amazon S3'),
        ],
        'X-Powered-By': [
            (r'PHP[\/]?([\d.]+)?', 'php', 'PHP'),
            (r'ASP\.NET', 'asp_net', 'ASP.NET'),
            (r'Express', 'express', 'Express.js'),
            (r'Next\.js\s*([\d.]+)?', 'nextjs', 'Next.js'),
        ],
        'X-AspNet-Version': [
            (r'([\d.]+)', 'asp_net', 'ASP.NET'),
        ],
        'X-Generator': [
            (r'Drupal\s*([\d.]+)?', 'drupal', 'Drupal'),
            (r'WordPress\s*([\d.]+)?', 'wordpress', 'WordPress'),
        ],
    }
    
    for header_name, patterns in header_patterns.items():
        header_value = headers.get(header_name, '')
        if not header_value:
            continue
        
        for pattern, key, name in patterns:
            match = re.search(pattern, header_value, re.IGNORECASE)
            if match:
                version = match.group(1) if match.groups() and match.group(1) else None
                detections.append({
                    'key': key,
                    'name': name,
                    'version': version,
                    'source': f'header:{header_name}',
                    'header_value': header_value
                })
    
    return detections


def detect_from_cookies(cookies):
    """Detect technologies from cookie names"""
    cookie_fingerprints = {
        'PHPSESSID': ('php', 'PHP'),
        'ASP.NET_SessionId': ('asp_net', 'ASP.NET'),
        'JSESSIONID': ('java', 'Java/Tomcat'),
        'rack.session': ('ruby', 'Ruby/Rails'),
        'laravel_session': ('laravel', 'Laravel'),
        'connect.sid': ('express', 'Express.js'),
        'CFID': ('coldfusion', 'ColdFusion'),
        'wordpress_logged_in': ('wordpress', 'WordPress'),
        'wp-settings': ('wordpress', 'WordPress'),
        'PrestaShop': ('prestashop', 'PrestaShop'),
    }
    
    detections = []
    for cookie_name, (key, name) in cookie_fingerprints.items():
        if any(cookie_name.lower() in c.lower() for c in cookies):
            detections.append({
                'key': key,
                'name': name,
                'version': None,
                'source': 'cookie',
                'cookie': cookie_name
            })
    
    return detections


def check_vulnerabilities(detections):
    """Check detected software against vulnerability database"""
    vulnerabilities = []
    
    for detection in detections:
        key = detection['key'].lower()
        version = detection.get('version')
        
        if key not in VULNERABILITY_DATABASE:
            continue
        
        for vuln in VULNERABILITY_DATABASE[key]:
            condition, cve, severity, description = vuln
            
            if version:
                if compare_versions(version, condition):
                    vulnerabilities.append({
                        'software': detection['name'],
                        'version': version,
                        'cve': cve,
                        'severity': severity,
                        'description': description,
                        'condition': condition
                    })
            else:
                # No version detected, report as potential
                vulnerabilities.append({
                    'software': detection['name'],
                    'version': 'unknown',
                    'cve': cve,
                    'severity': severity,
                    'description': description,
                    'condition': condition,
                    'status': 'potential'
                })
    
    return vulnerabilities


def generate_technology_stack(detections):
    """Categorize detections into technology stack"""
    stack = {
        'cms': [],
        'frameworks': [],
        'servers': [],
        'languages': [],
        'analytics': [],
        'cdn': [],
        'other': []
    }
    
    categories = {
        'wordpress': 'cms', 'drupal': 'cms', 'joomla': 'cms',
        'magento': 'cms', 'shopify': 'cms', 'wix': 'cms',
        'squarespace': 'cms', 'ghost': 'cms', 'prestashop': 'cms',
        'react': 'frameworks', 'angular': 'frameworks', 'vue': 'frameworks',
        'jquery': 'frameworks', 'bootstrap': 'frameworks', 'lodash': 'frameworks',
        'moment': 'frameworks', 'express': 'frameworks', 'laravel': 'frameworks',
        'nextjs': 'frameworks',
        'nginx': 'servers', 'apache': 'servers', 'iis': 'servers',
        'php': 'languages', 'asp_net': 'languages', 'java': 'languages',
        'ruby': 'languages', 'coldfusion': 'languages',
        'google_analytics': 'analytics', 'hotjar': 'analytics',
        'mixpanel': 'analytics',
        'cloudflare': 'cdn', 'akamai': 'cdn', 'fastly': 'cdn', 'aws_s3': 'cdn',
    }
    
    for detection in detections:
        key = detection['key'].lower()
        category = categories.get(key, 'other')
        
        # Avoid duplicates
        if not any(d['key'] == detection['key'] for d in stack[category]):
            stack[category].append(detection)
    
    return stack


def analyze_versions(html_content, headers=None, cookies=None):
    """
    Perform full version detection analysis
    
    Args:
        html_content: HTML content of the page
        headers: Optional dict of response headers
        cookies: Optional list of cookie names
    
    Returns:
        Dictionary with technology stack & vulnerabilities
    """
    detections = []
    
    # Detect from HTML
    detections.extend(detect_from_html(html_content))
    
    # Detect from headers
    if headers:
        detections.extend(detect_from_headers(headers))
    
    # Detect from cookies
    if cookies:
        detections.extend(detect_from_cookies(cookies))
    
    # Remove duplicates
    seen = set()
    unique_detections = []
    for d in detections:
        key = d['key']
        if key not in seen:
            seen.add(key)
            unique_detections.append(d)
        elif d.get('version'):
            # Update with version if found
            for ud in unique_detections:
                if ud['key'] == key and not ud.get('version'):
                    ud['version'] = d['version']
    
    # Check vulnerabilities
    vulnerabilities = check_vulnerabilities(unique_detections)
    
    # Generate stack
    stack = generate_technology_stack(unique_detections)
    
    return {
        'detections': unique_detections,
        'technology_stack': stack,
        'vulnerabilities': vulnerabilities,
        'summary': {
            'technologies_detected': len(unique_detections),
            'vulnerabilities_found': len(vulnerabilities),
            'critical_vulns': len([v for v in vulnerabilities if v['severity'] == 'Critical']),
            'high_vulns': len([v for v in vulnerabilities if v['severity'] == 'High']),
        }
    }
