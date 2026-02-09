# crawler_engine.py
# Website Intelligence Platform - Comprehensive Website Analyzer
# Aggressive scanning, SEO analysis, security checks, performance metrics, OSINT

import os
import uuid
import json
import time
import re
import ssl
import socket
import traceback
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

try:
    from android.util import Log
    def log_e(tag, msg): Log.e(tag, str(msg))
    def log_i(tag, msg): Log.i(tag, str(msg))
except ImportError:
    def log_e(tag, msg): print(f"E/{tag}: {msg}\n{traceback.format_exc()}")
    def log_i(tag, msg): print(f"I/{tag}: {msg}")

try:
    import httpx
    from bs4 import BeautifulSoup
    from markdownify import markdownify as md
    import tldextract
    import csv
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
except ImportError as e:
    print(f"Warning: Some packages not available: {e}")

# Import security modules
SECURITY_MODULES_AVAILABLE = False
SECURITY_MODULES_ERROR = None
try:
    from js_analyzer import analyze_javascript
    from form_mapper import map_forms
    from cookie_auditor import audit_cookies
    from robots_parser import analyze_robots_and_sitemap
    from vuln_scanner import (
        test_cors_misconfiguration, test_http_methods, detect_waf,
        check_clickjacking, check_mixed_content, extract_html_comments,
        trigger_error_pages, check_subdomain_takeover
    )
    from osint_engine import analyze_osint, get_osint_summary
    from version_detector import analyze_versions
    # NEW: Advanced security modules
    from dns_recon import analyze_dns, analyze_email_security
    from ssl_analyzer import analyze_ssl_certificate
    from subdomain_enum import enumerate_subdomains
    from api_discovery import discover_apis
    from param_fuzzer import fuzz_parameters
    from auth_tester import analyze_authentication
    from cloud_scanner import scan_cloud_resources
    from security_headers import analyze_security_headers
    SECURITY_MODULES_AVAILABLE = True
    log_i("CrawlerEngine", "Security modules loaded successfully")
except ImportError as e:
    # SECURITY_MODULES_ERROR = str(e)
    # log_e("CrawlerEngine", f"Security modules not available: {e}")
    # Fallback: Create detailed error for all import failures
    SECURITY_MODULES_ERROR = f"ImportError: {e}"
    log_e("CrawlerEngine", f"ImportError in modules: {e}")
except Exception as e:
    SECURITY_MODULES_ERROR = f"Loader Error: {e}"
    log_e("CrawlerEngine", f"Error loading security modules: {e}")

# In-memory state for active crawls
_active_crawls = {}
_crawl_results = {}

# Patch tldextract cache issue on Android
try:
    if SECURITY_MODULES_AVAILABLE:
        # On Android, home might not be writable for .cache
        # Use temp dir instead
        import tempfile
        import os
        cache_dir = os.path.join(tempfile.gettempdir(), "tldextract.cache")
        # We can't easily globally patch tldextract instance, but we can set env
        os.environ["TLDEXTRACT_CACHE"] = cache_dir
except Exception as e:
    log_e("CrawlerEngine", f"Failed to patch tldextract: {e}")


# Common hidden paths to probe
HIDDEN_PATHS = [
    '/admin', '/administrator', '/wp-admin', '/wp-login.php', '/login', '/signin',
    '/dashboard', '/panel', '/cpanel', '/phpmyadmin',
    '/admin/login', '/administrator/login', '/panel/login', '/user/login', '/auth/login',
    '/admin.php', '/admin.html', '/admin.login', '/login.php', '/login.html',
    '/backup', '/backups', '/bak', '/old', '/archive',
    '/test', '/testing', '/dev', '/development', '/staging', '/demo', '/beta',
    '/api', '/api/v1', '/api/v2', '/graphql', '/rest', '/swaggeer', '/swagger-ui.html',
    '/config', '/settings', '/configuration', '/setup',
    '/.git', '/.git/config', '/.git/HEAD', '/.env', '/.htaccess', '/.htpasswd',
    '/config.php', '/config.json', '/config.yml', '/settings.py',
    '/robots.txt', '/sitemap.xml', '/sitemap_index.xml',
    '/wp-config.php', '/web.config', '/composer.json', '/package.json',
    '/readme.md', '/README.md', '/CHANGELOG.md', '/LICENSE',
    '/uploads', '/images', '/assets', '/static', '/media', '/files',
    '/private', '/secret', '/hidden', '/internal',
    '/.well-known/security.txt', '/security.txt',
    '/error', '/404', '/500', '/debug',
    '/log', '/logs', '/error_log', '/access_log',
    '/server-status', '/nginx_status', '/info.php', '/phpinfo.php',
    '/docker-compose.yml', '/Procfile', '/storage', '/backup.sql', '/dump.sql',
    '/database.sql', '/db.sql', '/users.sql'
]

# Common subdomains to probe
COMMON_SUBDOMAINS = [
    'www', 'mail', 'remote', 'blog', 'webmail', 'server', 'ns1', 'ns2', 'smtp', 'secure',
    'vpn', 'm', 'shop', 'ftp', 'test', 'portal', 'support', 'dev', 'web', 'api', 
    'admin', 'stage', 'staging', 'beta', 'demo', 'app', 'apps', 'store', 'shop',
    'dashboard', 'docs', 'status', 'cdn', 'static', 'auth', 'account', 'login'
]

# Security headers to check
SECURITY_HEADERS = [
    'Content-Security-Policy', 'X-Content-Type-Options', 'X-Frame-Options',
    'X-XSS-Protection', 'Strict-Transport-Security', 'Referrer-Policy',
    'Permissions-Policy', 'Cross-Origin-Opener-Policy', 'Cross-Origin-Resource-Policy',
    'Cross-Origin-Embedder-Policy', 'X-Permitted-Cross-Domain-Policies'
]

# File extensions
DOC_EXTENSIONS = ('.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', 
                  '.txt', '.csv', '.zip', '.rar', '.7z', '.tar', '.gz')
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg', '.ico', '.bmp')
CODE_EXTENSIONS = ('.css', '.js', '.json', '.xml', '.yml', '.yaml')


def get_domain(url):
    """Extract domain from URL"""
    try:
        ext = tldextract.extract(url)
        return f"{ext.domain}.{ext.suffix}"
    except:
        return urlparse(url).netloc


def normalize_url(url):
    """Normalize URL by removing fragments and trailing slashes"""
    parsed = urlparse(url)
    path = parsed.path.rstrip('/') or '/'
    return f"{parsed.scheme}://{parsed.netloc}{path}"


def is_valid_url(url):
    """Check if URL is valid HTTP/HTTPS"""
    try:
        parsed = urlparse(url)
        return parsed.scheme in ('http', 'https') and bool(parsed.netloc)
    except:
        return False


def safe_filename(url):
    """Create a safe filename from URL"""
    parsed = urlparse(url)
    path = parsed.path.strip('/').replace('/', '_') or 'index'
    safe = re.sub(r'[^\w\-_.]', '_', path)
    return safe[:100]


def analyze_seo(html, url):
    """Analyze SEO elements of a page"""
    seo = {
        'url': url,
        'title': None,
        'title_length': 0,
        'meta_description': None,
        'meta_description_length': 0,
        'meta_keywords': None,
        'canonical': None,
        'og_tags': {},
        'twitter_tags': {},
        'headings': {'h1': [], 'h2': [], 'h3': [], 'h4': [], 'h5': [], 'h6': []},
        'images_without_alt': 0,
        'images_total': 0,
        'internal_links': 0,
        'external_links': 0,
        'has_viewport': False,
        'has_lang': False,
        'schema_types': [],
        'issues': []
    }
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        base_domain = get_domain(url)
        
        # Title
        if soup.title and soup.title.string:
            seo['title'] = soup.title.string.strip()
            seo['title_length'] = len(seo['title'])
            if seo['title_length'] < 30:
                seo['issues'].append(f'Title too short (<30 chars): "{seo["title"]}"')
            elif seo['title_length'] > 60:
                seo['issues'].append(f'Title too long (>60 chars): "{seo["title"]}"')
        else:
            seo['issues'].append('Missing title tag')
        
        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            seo['meta_description'] = meta_desc['content']
            seo['meta_description_length'] = len(seo['meta_description'])
            if seo['meta_description_length'] < 70:
                seo['issues'].append(f'Meta description too short: "{seo["meta_description"]}"')
            elif seo['meta_description_length'] > 160:
                seo['issues'].append(f'Meta description too long: "{seo["meta_description"]}"')
        else:
            seo['issues'].append('Missing meta description')
        
        # Meta keywords
        meta_kw = soup.find('meta', attrs={'name': 'keywords'})
        if meta_kw and meta_kw.get('content'):
            seo['meta_keywords'] = meta_kw['content']
        
        # Canonical
        canonical = soup.find('link', attrs={'rel': 'canonical'})
        if canonical and canonical.get('href'):
            seo['canonical'] = canonical['href']
        
        # Open Graph tags
        for og in soup.find_all('meta', attrs={'property': re.compile(r'^og:')}):
            prop = og.get('property', '').replace('og:', '')
            seo['og_tags'][prop] = og.get('content', '')
        
        # Twitter tags
        for tw in soup.find_all('meta', attrs={'name': re.compile(r'^twitter:')}):
            name = tw.get('name', '').replace('twitter:', '')
            seo['twitter_tags'][name] = tw.get('content', '')
        
        # Headings
        for level in range(1, 7):
            tag = f'h{level}'
            for h in soup.find_all(tag):
                text = h.get_text(strip=True)
                if text:
                    seo['headings'][tag].append(text[:100])
        
        if len(seo['headings']['h1']) == 0:
            seo['issues'].append('Missing H1 tag')
        elif len(seo['headings']['h1']) > 1:
            h1_texts = '", "'.join(seo['headings']['h1'][:3])
            more = "..." if len(seo['headings']['h1']) > 3 else ""
            seo['issues'].append(f"Multiple H1 tags ({len(seo['headings']['h1'])}): \"{h1_texts}\"{more}")
        
        # Images
        for img in soup.find_all('img'):
            seo['images_total'] += 1
            if not img.get('alt'):
                seo['images_without_alt'] += 1
        
        if seo['images_without_alt'] > 0:
            seo['issues'].append(f"{seo['images_without_alt']} images without alt text")
        
        # Links
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                continue
            full_url = urljoin(url, href)
            if get_domain(full_url) == base_domain:
                seo['internal_links'] += 1
            else:
                seo['external_links'] += 1
        
        # Viewport
        viewport = soup.find('meta', attrs={'name': 'viewport'})
        seo['has_viewport'] = bool(viewport)
        if not seo['has_viewport']:
            seo['issues'].append('Missing viewport meta tag')
        
        # Language
        html_tag = soup.find('html')
        seo['has_lang'] = bool(html_tag and html_tag.get('lang'))
        if not seo['has_lang']:
            seo['issues'].append('Missing lang attribute')
        
        # Schema.org
        for script in soup.find_all('script', type='application/ld+json'):
            try:
                data = json.loads(script.string)
                if isinstance(data, dict) and '@type' in data:
                    seo['schema_types'].append(data['@type'])
                elif isinstance(data, list):
                    for item in data:
                        if isinstance(item, dict) and '@type' in item:
                            seo['schema_types'].append(item['@type'])
            except:
                pass
                
    except Exception as e:
        seo['issues'].append(f'Analysis error: {str(e)}')
    
    return seo


def analyze_security(response_headers, url):
    """Analyze security headers and configuration"""
    security = {
        'url': url,
        'headers_present': [],
        'headers_missing': [],
        'header_values': {},
        'cookies': [],
        'issues': [],
        'score': 100
    }
    
    try:
        # Check security headers
        for header in SECURITY_HEADERS:
            header_lower = header.lower()
            found = False
            for resp_header in response_headers:
                if resp_header.lower() == header_lower:
                    security['headers_present'].append(header)
                    security['header_values'][header] = response_headers[resp_header]
                    found = True
                    break
            if not found:
                security['headers_missing'].append(header)
                security['score'] -= 5
        
        # Check specific header values
        if 'X-Frame-Options' in security['header_values']:
            val = security['header_values']['X-Frame-Options'].upper()
            if val not in ['DENY', 'SAMEORIGIN']:
                security['issues'].append(f'X-Frame-Options has weak value: "{val}"')
        
        if 'X-Content-Type-Options' in security['header_values']:
            if security['header_values']['X-Content-Type-Options'].lower() != 'nosniff':
                current_val = security['header_values']['X-Content-Type-Options']
                security['issues'].append(f'X-Content-Type-Options should be nosniff (found "{current_val}")')
        
        # Server header (information disclosure)
        if 'Server' in response_headers:
            security['issues'].append(f"Server header exposed: {response_headers['Server']}")
            security['score'] -= 5
        
        if 'X-Powered-By' in response_headers:
            security['issues'].append(f"X-Powered-By exposed: {response_headers['X-Powered-By']}")
            security['score'] -= 5
            
    except Exception as e:
        security['issues'].append(f'Security analysis error: {str(e)}')
    
    security['score'] = max(0, security['score'])
    return security


def analyze_ssl(url):
    """Analyze SSL/TLS certificate"""
    ssl_info = {
        'url': url,
        'has_ssl': False,
        'valid': False,
        'issuer': None,
        'subject': None,
        'expires': None,
        'protocol': None,
        'issues': []
    }
    
    parsed = urlparse(url)
    if parsed.scheme != 'https':
        ssl_info['issues'].append('Site not using HTTPS')
        return ssl_info
    
    try:
        context = ssl.create_default_context()
        with socket.create_connection((parsed.netloc, 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname=parsed.netloc) as ssock:
                ssl_info['has_ssl'] = True
                ssl_info['valid'] = True
                ssl_info['protocol'] = ssock.version()
                
                cert = ssock.getpeercert()
                if cert:
                    # Issuer
                    issuer = dict(x[0] for x in cert.get('issuer', []))
                    ssl_info['issuer'] = issuer.get('organizationName', 'Unknown')
                    
                    # Subject
                    subject = dict(x[0] for x in cert.get('subject', []))
                    ssl_info['subject'] = subject.get('commonName', 'Unknown')
                    
                    # Expiry
                    ssl_info['expires'] = cert.get('notAfter', 'Unknown')
                    
    except ssl.SSLError as e:
        ssl_info['issues'].append(f'SSL Error: {str(e)}')
    except Exception as e:
        ssl_info['issues'].append(f'Connection error: {str(e)}')
    
    return ssl_info


def detect_technology(html, response_headers):
    """Detect technology stack"""
    tech = {
        'server': None,
        'cms': None,
        'frameworks': [],
        'libraries': [],
        'analytics': []
    }
    
    try:
        # Server
        tech['server'] = response_headers.get('Server', response_headers.get('server'))
        
        soup = BeautifulSoup(html, 'html.parser')
        html_lower = html.lower()
        
        # CMS Detection
        if 'wp-content' in html_lower or 'wordpress' in html_lower:
            tech['cms'] = 'WordPress'
        elif 'drupal' in html_lower:
            tech['cms'] = 'Drupal'
        elif 'joomla' in html_lower:
            tech['cms'] = 'Joomla'
        elif 'wix.com' in html_lower:
            tech['cms'] = 'Wix'
        elif 'squarespace' in html_lower:
            tech['cms'] = 'Squarespace'
        elif 'shopify' in html_lower:
            tech['cms'] = 'Shopify'
        
        # Frameworks
        if 'react' in html_lower or '_next' in html_lower:
            tech['frameworks'].append('React')
        if 'vue' in html_lower or '__vue' in html_lower:
            tech['frameworks'].append('Vue.js')
        if 'angular' in html_lower:
            tech['frameworks'].append('Angular')
        if 'bootstrap' in html_lower:
            tech['libraries'].append('Bootstrap')
        if 'tailwind' in html_lower:
            tech['libraries'].append('Tailwind CSS')
        if 'jquery' in html_lower:
            tech['libraries'].append('jQuery')
        
        # Analytics
        if 'google-analytics' in html_lower or 'gtag' in html_lower or 'ga.js' in html_lower:
            tech['analytics'].append('Google Analytics')
        if 'facebook' in html_lower and 'pixel' in html_lower:
            tech['analytics'].append('Facebook Pixel')
        if 'hotjar' in html_lower:
            tech['analytics'].append('Hotjar')
            
    except:
        pass
    
    return tech


def extract_all_assets(html, url):
    """Extract ALL assets from a page"""
    assets = {
        'images': [],
        'documents': [],
        'stylesheets': [],
        'scripts': [],
        'videos': [],
        'audio': [],
        'fonts': [],
        'other': []
    }
    
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Images - ALL of them
        for img in soup.find_all('img', src=True):
            src = urljoin(url, img['src'])
            if is_valid_url(src):
                assets['images'].append({
                    'url': src,
                    'alt': img.get('alt', ''),
                    'title': img.get('title', '')
                })
        
        # Background images in style
        for elem in soup.find_all(style=True):
            style = elem['style']
            urls = re.findall(r'url\(["\']?([^"\'()]+)["\']?\)', style)
            for u in urls:
                full_url = urljoin(url, u)
                if is_valid_url(full_url) and any(full_url.lower().endswith(ext) for ext in IMAGE_EXTENSIONS):
                    assets['images'].append({'url': full_url, 'alt': '', 'title': ''})
        
        # Stylesheets
        for link in soup.find_all('link', rel='stylesheet'):
            href = link.get('href')
            if href:
                full_url = urljoin(url, href)
                if is_valid_url(full_url):
                    assets['stylesheets'].append(full_url)
        
        # Scripts
        for script in soup.find_all('script', src=True):
            src = urljoin(url, script['src'])
            if is_valid_url(src):
                assets['scripts'].append(src)
        
        # Documents & Links
        for a in soup.find_all('a', href=True):
            href = a['href']
            full_url = urljoin(url, href)
            if is_valid_url(full_url):
                ext = os.path.splitext(urlparse(full_url).path)[1].lower()
                if ext in DOC_EXTENSIONS:
                    assets['documents'].append({
                        'url': full_url,
                        'text': a.get_text(strip=True)[:100]
                    })
        
        # Videos
        for video in soup.find_all(['video', 'source']):
            src = video.get('src')
            if src:
                full_url = urljoin(url, src)
                if is_valid_url(full_url):
                    assets['videos'].append(full_url)
        
        # Iframes (embedded content)
        for iframe in soup.find_all('iframe', src=True):
            src = iframe['src']
            if 'youtube' in src or 'vimeo' in src:
                assets['videos'].append(src)
                
    except:
        pass
    
    return assets


def extract_links(html, base_url):
    """Extract all links from HTML"""
    links = set()
    try:
        soup = BeautifulSoup(html, 'html.parser')
        base_domain = get_domain(base_url)
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith(('#', 'javascript:', 'mailto:', 'tel:')):
                continue
            full_url = urljoin(base_url, href)
            normalized = normalize_url(full_url)
            if is_valid_url(normalized) and get_domain(normalized) == base_domain:
                links.add(normalized)
    except:
        pass
    return list(links)


def extract_text_content(html, url):
    """Extract text content and convert to markdown"""
    try:
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'noscript']):
            element.decompose()
        
        title = soup.title.string if soup.title else url
        
        meta_desc = ""
        meta = soup.find('meta', attrs={'name': 'description'})
        if meta:
            meta_desc = meta.get('content', '')
        
        main_content = soup.find('main') or soup.find('article') or soup.find('body')
        if main_content:
            markdown = md(str(main_content), heading_style="ATX")
        else:
            markdown = md(str(soup), heading_style="ATX")
        
        return {
            'title': title or 'Untitled',
            'description': meta_desc,
            'content': markdown
        }
    except Exception as e:
        return {'title': url, 'description': '', 'content': f'Error: {e}'}


def download_file(url, save_path, timeout=30):
    """Download a file from URL"""
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True, verify=False) as client:
            response = client.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            if response.status_code == 200:
                os.makedirs(os.path.dirname(save_path), exist_ok=True)
                with open(save_path, 'wb') as f:
                    f.write(response.content)
                return True
    except:
        pass
    return False


def crawl_page(url, crawl_state):
    """Crawl a single page and perform analysis based on enabled scans"""
    crawl_id = crawl_state['crawl_id']
    output_dir = crawl_state['output_dir']
    visited = crawl_state['visited']
    enabled_scans = crawl_state.get('enabled_scans', set())
    
    # Determine scan mode
    all_categories = {'dns_recon', 'ssl_analysis', 'subdomain_enum', 'api_discovery',
                      'param_fuzzing', 'auth_testing', 'cloud_scanner', 'security_headers'}
    is_full_scan = enabled_scans == all_categories or len(enabled_scans) == 8
    
    if url in visited:
        return {'new_links': [], 'success': False}
    
    visited.add(url)
    result = {
        'url': url,
        'success': False,
        'new_links': [],
        'status_code': None,
        'content_type': None,
        'seo': None,
        'security': None,
        'assets': None,
        'tech': None,
        # NEW: Enhanced security findings
        'js_analysis': None,
        'forms': None,
        'cookies': None,
        'osint': None,
        'versions': None,
        'vulnerabilities': None
    }
    
    # Check if stopped
    if crawl_id in _active_crawls and _active_crawls[crawl_id].get('stop'):
        return result
    
    # Update current URL in results
    if crawl_id in _crawl_results:
        _crawl_results[crawl_id]['current_url'] = url
    
    try:
        user_agent = crawl_state.get('user_agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        with httpx.Client(timeout=30, follow_redirects=True, verify=False) as client:
            headers = {'User-Agent': user_agent}
            start_time = time.time()
            response = client.get(url, headers=headers)
            load_time = int((time.time() - start_time) * 1000) # ms
            
            result['status_code'] = response.status_code
            result['content_type'] = response.headers.get('content-type', '')
            result['load_time'] = load_time
            result['size'] = len(response.content)
            
            if response.status_code != 200:
                return result
            
            # Only process HTML pages fully
            if 'text/html' in result['content_type']:
                html = response.text
                response_headers = dict(response.headers)
                cookie_list = list(response.cookies.keys()) if response.cookies else []
                
                # SEO Analysis
                result['seo'] = analyze_seo(html, url)
                
                # Security Analysis (always runs - basic)
                result['security'] = analyze_security(response_headers, url)
                
                # Technology Detection (always runs - lightweight)
                result['tech'] = detect_technology(html, response_headers)
                
                # Extract Assets (always runs - needed for crawling)
                result['assets'] = extract_all_assets(html, url)
                
                # Enhanced Security Analysis - CONDITIONAL based on scan selections
                if SECURITY_MODULES_AVAILABLE:
                    try:
                        page_vulns = []
                        
                        # JavaScript Analysis (secrets, DOM sinks, APIs) → param_fuzzing
                        if is_full_scan or 'param_fuzzing' in enabled_scans:
                            result['js_analysis'] = analyze_javascript(html, url)
                        
                        # Form Mapping (CSRF, inputs, attack surface) → auth_testing
                        if is_full_scan or 'auth_testing' in enabled_scans:
                            result['forms'] = map_forms(html, url)
                        
                        # Cookie Auditing → security_headers
                        if is_full_scan or 'security_headers' in enabled_scans:
                            result['cookies'] = audit_cookies(response_headers, url)
                        
                        # OSINT (emails, phones, social media) → dns_recon (full mode)
                        if is_full_scan or 'dns_recon' in enabled_scans:
                            result['osint'] = analyze_osint(html, url)
                        
                        # Version Detection & CVE Mapping → api_discovery
                        if is_full_scan or 'api_discovery' in enabled_scans:
                            result['versions'] = analyze_versions(html, response_headers, cookie_list)
                        
                        # Check for mixed content → ssl_analysis
                        if is_full_scan or 'ssl_analysis' in enabled_scans:
                            mixed = check_mixed_content(html, url)
                            if mixed:
                                page_vulns.extend(mixed)
                        
                        # Extract HTML comments (potential info disclosure) → param_fuzzing
                        if is_full_scan or 'param_fuzzing' in enabled_scans:
                            comments = extract_html_comments(html, url)
                            if comments:
                                result['html_comments'] = comments
                        
                        result['page_vulnerabilities'] = page_vulns
                        
                    except Exception as e:
                        log_e("CrawlerEngine", f"Security module error: {e}")
                
                # Extract and save content
                content = extract_text_content(html, url)
                content_dir = os.path.join(output_dir, 'content')
                os.makedirs(content_dir, exist_ok=True)
                
                filename = safe_filename(url) + '.md'
                filepath = os.path.join(content_dir, filename)
                
                full_content = f"# {content['title']}\n\n"
                full_content += f"**URL:** {url}\n\n"
                if content['description']:
                    full_content += f"**Description:** {content['description']}\n\n"
                full_content += "---\n\n"
                full_content += content['content']
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(full_content)
                
                # Save HTML source
                html_dir = os.path.join(output_dir, 'html')
                os.makedirs(html_dir, exist_ok=True)
                html_path = os.path.join(html_dir, safe_filename(url) + '.html')
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html)
                
                # Extract new links
                result['new_links'] = extract_links(html, url)
                
                result['success'] = True
                
                # Update pages crawled
                if crawl_id in _crawl_results:
                    _crawl_results[crawl_id]['pages_crawled'] += 1
                
    except Exception as e:
        result['error'] = str(e)
    
    return result


def probe_hidden_paths(base_url, crawl_state):
    """Probe common hidden paths concurrently"""
    discovered = []
    parsed = urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    user_agent = crawl_state.get('user_agent', 'Mozilla/5.0')
    
    # Generate list of Probe URLs
    probe_urls = set() # Use unique set
    
    # 1. Probes relative to domain root
    for path in HIDDEN_PATHS:
        probe_urls.add(base + path)
        
    # 2. Probes relative to current path (if deep structure)
    path_parts = parsed.path.strip('/').split('/')
    if path_parts and path_parts[0]:
        # Add probes relative to the first path segment (e.g., example.com/app/ -> example.com/app/admin)
        sub_base = f"{base}/{path_parts[0]}"
        for path in HIDDEN_PATHS:
            probe_urls.add(sub_base + path)
            
    # Filter out already visited
    to_check = [u for u in probe_urls if u not in crawl_state['visited']]
    
    def check_url(url):
        try:
            with httpx.Client(timeout=3, follow_redirects=False, verify=False) as client:
                response = client.head(url, headers={'User-Agent': user_agent})
                if response.status_code in [200, 301, 302, 403]:
                    return {
                        'url': url,
                        'status': response.status_code,
                        'path': urlparse(url).path
                    }
        except:
            pass
        return None

    # Run probes concurrently (Fast!)
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(check_url, u): u for u in to_check}
        for future in as_completed(futures):
            result = future.result()
            if result:
                discovered.append(result)
                
    return discovered


def probe_subdomains(base_url, crawl_state):
    """Probe common subdomains concurrently"""
    discovered = []
    user_agent = crawl_state.get('user_agent', 'Mozilla/5.0')
    
    try:
        ext = tldextract.extract(base_url)
        # Handle cases like "co.uk" where domain is "google" and suffix is "co.uk"
        if not ext.domain or not ext.suffix:
            return []
        root_domain = f"{ext.domain}.{ext.suffix}"
    except:
        return []
    
    probe_urls = set()
    for sub in COMMON_SUBDOMAINS:
        # Check both HTTPS and HTTP (prefer HTTPS)
        probe_urls.add(f"https://{sub}.{root_domain}")
        # Only check HTTP if you really want to be thorough, but it doubles requests.
        # Let's stick to HTTPS for speed, unless root was HTTP.
    
    if base_url.startswith('http://'):
         for sub in COMMON_SUBDOMAINS:
            probe_urls.add(f"http://{sub}.{root_domain}")
            
    # Remove potentially visited
    to_check = [u for u in probe_urls if u not in crawl_state['visited']]
    
    def check_subdomain(url):
        try:
            # Short timeout for subdomains as DNS fail is fast usually
            with httpx.Client(timeout=2, follow_redirects=True, verify=False) as client:
                response = client.head(url, headers={'User-Agent': user_agent})
                # If we get a response, the subdomain exists
                if response.status_code < 500: # Accept almost anything that answers
                    return {
                        'url': url,
                        'status': response.status_code,
                        'type': 'subdomain'
                    }
        except:
            pass
        return None

    # Run probes (increased parallelism for speed)
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(check_subdomain, u): u for u in to_check}
        for future in as_completed(futures):
            result = future.result()
            if result:
                discovered.append(result)
                
    return discovered


def start_crawl(url, depth, output_dir, user_agent="Mozilla/5.0", scan_categories="all"):
    """Start a new crawl with comprehensive analysis
    
    Args:
        url: Target URL to crawl
        depth: Maximum crawl depth
        output_dir: Directory to save results
        user_agent: User agent string
        scan_categories: Comma-separated list of scan categories or "all"
                        Options: dns_recon,ssl_analysis,subdomain_enum,api_discovery,
                                 param_fuzzing,auth_testing,cloud_scanner,security_headers
    """
    crawl_id = str(uuid.uuid4())
    
    # Parse scan categories
    if scan_categories == "all" or not scan_categories:
        enabled_scans = {
            'dns_recon', 'ssl_analysis', 'subdomain_enum', 'api_discovery',
            'param_fuzzing', 'auth_testing', 'cloud_scanner', 'security_headers'
        }
    else:
        enabled_scans = set(scan_categories.split(','))
    
    # Normalize URL - auto-add https:// if missing
    url = url.strip()
    if not url.startswith('http://') and not url.startswith('https://'):
        url = 'https://' + url
    
    # Validate URL
    if not is_valid_url(url):
        return json.dumps({'error': f'Invalid URL: {url}'})
    
    # Initialize state
    crawl_output = os.path.join(output_dir, crawl_id)
    os.makedirs(crawl_output, exist_ok=True)
    
    _active_crawls[crawl_id] = {'stop': False, 'enabled_scans': enabled_scans}
    _crawl_results[crawl_id] = {
        'status': 'running',
        'url': url,
        'depth': depth,
        'user_agent': user_agent,
        'enabled_scans': list(enabled_scans),
        'pages_crawled': 0,
        'pages_total': 0,
        'pages_queued': 0,
        'current_url': url,
        'start_time': time.time(),
        'output_dir': crawl_output,
        'hidden_paths': [],
        'subdomains': [],
        'all_pages': [],
        'seo_issues': [],
        'security_issues': [],
        # NEW: Enhanced findings
        'robots_analysis': None,
        'waf_detection': None,
        'cors_findings': None,
        'http_methods': None,
        'secrets_found': [],
        'forms_found': [],
        'cookies_found': [],
        'osint_summary': None,
        'technologies': [],
        'vulnerabilities': [],
        'error_pages': None,
        # Capture initialization errors
        'error': SECURITY_MODULES_ERROR,
        # NEW: Advanced security scan results
        'dns_recon': None,
        'email_security': None,
        'ssl_analysis': None,
        'subdomain_enum': None,
        'api_discovery': None,
        'param_fuzzing': None,
        'auth_testing': None,
        'cloud_scanner': None,
        'security_headers': None
    }
    
    import threading
    
    def run_crawl(start_url=url, max_depth=depth, c_id=crawl_id, c_out=crawl_output, ua=user_agent, scans=enabled_scans):
        log_i("CrawlerEngine", f"Starting crawl {c_id} for {start_url} with UA: {ua}, scans: {scans}")
        try:
            crawl_state = {
                'crawl_id': c_id,
                'output_dir': c_out,
                'visited': set(),
                'to_visit': [(start_url, 0)],
                'max_depth': max_depth,
                'enabled_scans': scans,
                'user_agent': ua
            }
            
            all_results = []
            
            # Initial connectivity check
            _crawl_results[c_id]['current_url'] = 'Checking connectivity...'
            try:
                with httpx.Client(timeout=15, follow_redirects=True, verify=False) as client:
                    response = client.head(start_url, headers={'User-Agent': ua})
                    if response.status_code >= 400:
                        raise Exception(f"Server returned status {response.status_code}")
            except httpx.ConnectError as e:
                log_e("CrawlerEngine", f"ConnectError: {e}")
                raise Exception(f"Cannot connect to {start_url} - check if the website exists")
            except httpx.TimeoutException:
                log_e("CrawlerEngine", f"TimeoutException: {start_url}")
                raise Exception(f"Connection to {start_url} timed out")
            except Exception as e:
                log_e("CrawlerEngine", f"Connectivity Error: {e}")
                raise Exception(f"Failed to reach {start_url}: {str(e)}")
            
            # Check if running in full mode (all 8 categories) or selective mode
            all_categories = {'dns_recon', 'ssl_analysis', 'subdomain_enum', 'api_discovery',
                              'param_fuzzing', 'auth_testing', 'cloud_scanner', 'security_headers'}
            is_full_scan = scans == all_categories or len(scans) == 8
            
            # 1. Probe hidden paths (Concurrent) - only in full scan mode
            if is_full_scan or 'api_discovery' in scans:
                _crawl_results[c_id]['current_url'] = 'Probing hidden paths...'
                hidden = probe_hidden_paths(start_url, crawl_state)
                _crawl_results[c_id]['hidden_paths'] = hidden
                
                # Add discovered hidden paths to queue
                for h in hidden:
                    if h['status'] == 200:
                        crawl_state['to_visit'].append((h['url'], 1))

            # 2. Probe Subdomains - only if subdomain_enum enabled or full scan
            if is_full_scan or 'subdomain_enum' in scans:
                _crawl_results[c_id]['current_url'] = 'Scanning subdomains...'
                subdomains = probe_subdomains(start_url, crawl_state)
                _crawl_results[c_id]['subdomains'] = subdomains
                
                for s in subdomains:
                    if s['status'] < 400:
                        crawl_state['to_visit'].append((s['url'], 0)) 
            
            # ============ PARALLEL BASIC SECURITY SCANS ============
            # Only run basic scans in full mode, OR map to relevant categories
            # Run multiple security checks concurrently for speed
            if SECURITY_MODULES_AVAILABLE:
                _crawl_results[c_id]['current_url'] = 'Running security scans (parallel)...'
                
                basic_scan_tasks = []
                
                # robots_analysis → run in full mode or with api_discovery
                if is_full_scan or 'api_discovery' in scans:
                    def run_robots_analysis():
                        try:
                            return ('robots_analysis', analyze_robots_and_sitemap(start_url))
                        except Exception as e:
                            log_e("CrawlerEngine", f"Robots analysis error: {e}")
                            return ('robots_analysis', None)
                    basic_scan_tasks.append(run_robots_analysis)
                
                # waf_detection → run in full mode only (quick check)
                if is_full_scan:
                    def run_waf_detection():
                        try:
                            return ('waf_detection', detect_waf(start_url))
                        except Exception as e:
                            log_e("CrawlerEngine", f"WAF detection error: {e}")
                            return ('waf_detection', None)
                    basic_scan_tasks.append(run_waf_detection)
                
                # CORS test → run with security_headers
                if is_full_scan or 'security_headers' in scans:
                    def run_cors_test():
                        try:
                            cors_list = test_cors_misconfiguration(start_url)
                            if cors_list:
                                first = cors_list[0]
                                return ('cors_findings', {
                                    'vulnerable': True,
                                    'type': first.get('issue'),
                                    'details': first.get('description'),
                                    'allowed_origin': first.get('origin_tested'),
                                    'allows_credentials': str(first.get('acac', 'false')).lower() == 'true'
                                })
                            return ('cors_findings', {'vulnerable': False})
                        except Exception as e:
                            log_e("CrawlerEngine", f"CORS test error: {e}")
                            return ('cors_findings', None)
                    basic_scan_tasks.append(run_cors_test)
                
                # HTTP methods → run with security_headers
                if is_full_scan or 'security_headers' in scans:
                    def run_http_methods():
                        try:
                            methods_list = test_http_methods(start_url)
                            allowed, dangerous = [], []
                            if methods_list:
                                for m in methods_list:
                                    if 'all_allowed' in m:
                                        allowed = m['all_allowed']
                                        break
                                for m in methods_list:
                                    if m.get('issue', '').endswith('method allowed'):
                                        method_name = m['issue'].split()[0]
                                        if method_name not in dangerous:
                                            dangerous.append(method_name)
                            return ('http_methods', {'allowed_methods': allowed, 'dangerous_methods': dangerous})
                        except Exception as e:
                            log_e("CrawlerEngine", f"HTTP methods test error: {e}")
                            return ('http_methods', None)
                    basic_scan_tasks.append(run_http_methods)
                
                # Error pages → run with param_fuzzing
                if is_full_scan or 'param_fuzzing' in scans:
                    def run_error_pages():
                        try:
                            error_result = trigger_error_pages(start_url)
                            return ('error_pages', {
                                'error_pages': error_result if error_result else [],
                                'info_disclosure': [item.get('issue', '') for item in error_result] if error_result else []
                            })
                        except Exception as e:
                            log_e("CrawlerEngine", f"Error page test error: {e}")
                            return ('error_pages', None)
                    basic_scan_tasks.append(run_error_pages)
                
                # Clickjacking → run with security_headers
                if is_full_scan or 'security_headers' in scans:
                    def run_clickjacking():
                        try:
                            clickjack = check_clickjacking(start_url)
                            if clickjack.get('vulnerable'):
                                return ('clickjacking', {
                                    'type': 'Clickjacking',
                                    'severity': 'Medium',
                                    'url': start_url,
                                    'details': clickjack
                                })
                            return ('clickjacking', None)
                        except Exception as e:
                            log_e("CrawlerEngine", f"Clickjacking test error: {e}")
                            return ('clickjacking', None)
                    basic_scan_tasks.append(run_clickjacking)
                
                # Basic SSL → run with ssl_analysis
                if is_full_scan or 'ssl_analysis' in scans:
                    def run_ssl_analysis_basic():
                        try:
                            return ('ssl', analyze_ssl(start_url))
                        except Exception as e:
                            log_e("CrawlerEngine", f"SSL analysis error: {e}")
                            return ('ssl', None)
                    basic_scan_tasks.append(run_ssl_analysis_basic)
                
                # Execute only the enabled basic scans in parallel
                if basic_scan_tasks:
                    with ThreadPoolExecutor(max_workers=len(basic_scan_tasks)) as executor:
                        futures = [executor.submit(task) for task in basic_scan_tasks]
                        for future in as_completed(futures):
                            try:
                                key, value = future.result()
                                if key == 'clickjacking' and value:
                                    _crawl_results[c_id]['vulnerabilities'].append(value)
                                elif key == 'robots_analysis' and value:
                                    _crawl_results[c_id][key] = value
                                    # Process robots results for queue additions
                                    for sitemap_url in value.get('sitemap_urls', [])[:50]:
                                        if sitemap_url not in crawl_state['visited']:
                                            crawl_state['to_visit'].append((sitemap_url, 1))
                                    for path in value.get('accessible_disallowed', []):
                                        if path['url'] not in crawl_state['visited']:
                                            crawl_state['to_visit'].append((path['url'], 1))
                                elif value is not None:
                                    _crawl_results[c_id][key] = value
                            except Exception as e:
                                log_e("CrawlerEngine", f"Parallel scan error: {e}")
            
            # ============ PARALLEL ADVANCED SECURITY SCANS ============
            # Get enabled scans from crawl state
            enabled = crawl_state.get('enabled_scans', set())
            
            if SECURITY_MODULES_AVAILABLE and enabled:
                _crawl_results[c_id]['current_url'] = 'Running advanced security scans (parallel)...'
                
                advanced_scan_tasks = []
                
                if 'dns_recon' in enabled:
                    def run_dns_recon():
                        try:
                            dns_result = analyze_dns(start_url)
                            email_sec = analyze_email_security(start_url)
                            return [('dns_recon', dns_result), ('email_security', email_sec)]
                        except Exception as e:
                            log_e("CrawlerEngine", f"DNS recon error: {e}")
                            return [('dns_recon', None), ('email_security', None)]
                    advanced_scan_tasks.append(run_dns_recon)
                
                if 'ssl_analysis' in enabled:
                    def run_ssl_detailed():
                        try:
                            return [('ssl_analysis', analyze_ssl_certificate(start_url))]
                        except Exception as e:
                            log_e("CrawlerEngine", f"SSL analysis error: {e}")
                            return [('ssl_analysis', None)]
                    advanced_scan_tasks.append(run_ssl_detailed)
                
                if 'subdomain_enum' in enabled:
                    def run_subdomain_enum():
                        try:
                            return [('subdomain_enum', enumerate_subdomains(start_url, bruteforce=False))]
                        except Exception as e:
                            log_e("CrawlerEngine", f"Subdomain enumeration error: {e}")
                            return [('subdomain_enum', None)]
                    advanced_scan_tasks.append(run_subdomain_enum)
                
                if 'api_discovery' in enabled:
                    def run_api_discovery():
                        try:
                            return [('api_discovery', discover_apis(start_url))]
                        except Exception as e:
                            log_e("CrawlerEngine", f"API discovery error: {e}")
                            return [('api_discovery', None)]
                    advanced_scan_tasks.append(run_api_discovery)
                
                if 'param_fuzzing' in enabled:
                    def run_param_fuzzing():
                        try:
                            return [('param_fuzzing', fuzz_parameters(start_url))]
                        except Exception as e:
                            log_e("CrawlerEngine", f"Parameter fuzzing error: {e}")
                            return [('param_fuzzing', None)]
                    advanced_scan_tasks.append(run_param_fuzzing)
                
                if 'auth_testing' in enabled:
                    def run_auth_testing():
                        try:
                            return [('auth_testing', analyze_authentication(start_url))]
                        except Exception as e:
                            log_e("CrawlerEngine", f"Auth testing error: {e}")
                            return [('auth_testing', None)]
                    advanced_scan_tasks.append(run_auth_testing)
                
                if 'cloud_scanner' in enabled:
                    def run_cloud_scanner():
                        try:
                            with httpx.Client(timeout=10, verify=False) as client:
                                resp = client.get(start_url)
                                page_content = resp.text
                            return [('cloud_scanner', scan_cloud_resources(start_url, page_content))]
                        except Exception as e:
                            log_e("CrawlerEngine", f"Cloud scanner error: {e}")
                            return [('cloud_scanner', None)]
                    advanced_scan_tasks.append(run_cloud_scanner)
                
                if 'security_headers' in enabled:
                    def run_security_headers():
                        try:
                            return [('security_headers', analyze_security_headers(start_url))]
                        except Exception as e:
                            log_e("CrawlerEngine", f"Security headers error: {e}")
                            return [('security_headers', None)]
                    advanced_scan_tasks.append(run_security_headers)
                
                # Execute all enabled advanced scans in parallel
                if advanced_scan_tasks:
                    with ThreadPoolExecutor(max_workers=min(8, len(advanced_scan_tasks))) as executor:
                        futures = [executor.submit(task) for task in advanced_scan_tasks]
                        for future in as_completed(futures):
                            try:
                                results = future.result()
                                for key, value in results:
                                    if value is not None:
                                        _crawl_results[c_id][key] = value
                            except Exception as e:
                                log_e("CrawlerEngine", f"Advanced parallel scan error: {e}")
            
            # ============ END ADVANCED SECURITY SCANS ============
            
            # Main crawl loop with concurrent processing (increased parallelism)
            with ThreadPoolExecutor(max_workers=8) as executor:
                while crawl_state['to_visit']:
                    if _active_crawls.get(c_id, {}).get('stop'):
                        break
                    
                    # Get batch of URLs to process (larger batches for speed)
                    batch = []
                    while crawl_state['to_visit'] and len(batch) < 8:
                        current_url, current_depth = crawl_state['to_visit'].pop(0)
                        if current_url not in crawl_state['visited'] and current_depth <= depth:
                            batch.append((current_url, current_depth))
                    
                    if not batch:
                        break
                    
                    _crawl_results[crawl_id]['pages_queued'] = len(crawl_state['to_visit'])
                    
                    # Submit batch
                    futures = {
                        executor.submit(crawl_page, url, crawl_state): (url, d) 
                        for url, d in batch
                    }
                    
                    for future in as_completed(futures):
                        url, d = futures[future]
                        try:
                            result = future.result()
                            all_results.append(result)
                            
                            # Collect issues
                            if result.get('seo') and result['seo'].get('issues'):
                                for issue in result['seo']['issues']:
                                    _crawl_results[crawl_id]['seo_issues'].append({
                                        'url': url,
                                        'issue': issue
                                    })
                            
                            if result.get('security') and result['security'].get('issues'):
                                for issue in result['security']['issues']:
                                    _crawl_results[crawl_id]['security_issues'].append({
                                        'url': url,
                                        'issue': issue
                                    })
                            
                            # NEW: Collect enhanced security findings
                            # JavaScript secrets
                            if result.get('js_analysis'):
                                js = result['js_analysis']
                                if js.get('secrets'):
                                    _crawl_results[crawl_id]['secrets_found'].extend(js['secrets'])
                                if js.get('vulnerabilities'):
                                    _crawl_results[crawl_id]['vulnerabilities'].extend([
                                        {'type': 'JavaScript', 'url': url, **v} for v in js['vulnerabilities']
                                    ])
                            
                            # Forms
                            if result.get('forms') and result['forms'].get('forms'):
                                _crawl_results[crawl_id]['forms_found'].extend(result['forms']['forms'])
                            
                            # Cookies
                            if result.get('cookies') and result['cookies'].get('cookies'):
                                _crawl_results[crawl_id]['cookies_found'].extend(result['cookies']['cookies'])
                            
                            # Technologies with versions
                            if result.get('versions') and result['versions'].get('detections'):
                                _crawl_results[crawl_id]['technologies'].extend(result['versions']['detections'])
                                if result['versions'].get('vulnerabilities'):
                                    _crawl_results[crawl_id]['vulnerabilities'].extend([
                                        {'type': 'Outdated Software', 'url': url, **v} for v in result['versions']['vulnerabilities']
                                    ])
                            
                            # Page vulnerabilities
                            if result.get('page_vulnerabilities'):
                                _crawl_results[crawl_id]['vulnerabilities'].extend([
                                    {'url': url, **v} for v in result['page_vulnerabilities']
                                ])
                            
                            # Add new links
                            if d < depth:
                                for link in result.get('new_links', []):
                                    if link not in crawl_state['visited']:
                                        crawl_state['to_visit'].append((link, d + 1))
                            
                            _crawl_results[crawl_id]['pages_total'] = len(crawl_state['visited'])
                            
                        except Exception as e:
                            print(f"Error processing {url}: {e}")
            
            # Store all page info
            _crawl_results[crawl_id]['all_pages'] = [
                {
                    'url': r['url'], 
                    'status': r.get('status_code'), 
                    'success': r['success'],
                    'load_time': r.get('load_time'),
                    'size': r.get('size')
                }
                for r in all_results
            ]
            
            # Generate OSINT summary from all pages (only if dns_recon enabled)
            if SECURITY_MODULES_AVAILABLE and (is_full_scan or 'dns_recon' in scans):
                try:
                    osint_results = [r.get('osint') for r in all_results if r.get('osint')]
                    domain = get_domain(start_url)
                    _crawl_results[c_id]['osint_summary'] = get_osint_summary(osint_results, domain)
                except Exception as e:
                    log_e("CrawlerEngine", f"OSINT summary error: {e}")
            
            # NEW: Deduplicate technologies
            seen_tech = set()
            unique_tech = []
            for tech in _crawl_results[c_id].get('technologies', []):
                key = tech.get('key', '')
                if key and key not in seen_tech:
                    seen_tech.add(key)
                    unique_tech.append(tech)
            _crawl_results[c_id]['technologies'] = unique_tech
            
            # Save analysis report
            report_path = os.path.join(c_out, 'analysis_report.json')
            
            # Log the counts for debugging
            log_i("CrawlerEngine", f"Report stats - Forms: {len(_crawl_results[c_id].get('forms_found', []))}, " +
                  f"Cookies: {len(_crawl_results[c_id].get('cookies_found', []))}, " +
                  f"Technologies: {len(_crawl_results[c_id].get('technologies', []))}, " +
                  f"Secrets: {len(_crawl_results[c_id].get('secrets_found', []))}, " +
                  f"Vulnerabilities: {len(_crawl_results[c_id].get('vulnerabilities', []))}, " +
                  f"Security Modules Available: {SECURITY_MODULES_AVAILABLE}")
            
            # Debug: Inject module error into report if available
            if not SECURITY_MODULES_AVAILABLE:
                _crawl_results[c_id]['error'] = f"Security Modules Failed: {SECURITY_MODULES_ERROR}"
                log_e("CrawlerEngine", f"SECURITY MODULES LOAD FAILED: {SECURITY_MODULES_ERROR}")
            
            # Calculate security score
            security_score = 100
            critical_count = 0
            high_count = 0
            medium_count = 0
            
            for vuln in _crawl_results[c_id].get('vulnerabilities', []):
                sev = vuln.get('severity', '').lower()
                if sev == 'critical':
                    security_score -= 25
                    critical_count += 1
                elif sev == 'high':
                    security_score -= 15
                    high_count += 1
                elif sev == 'medium':
                    security_score -= 5
                    medium_count += 1
            
            # Reduce for secrets found
            security_score -= len(_crawl_results[c_id].get('secrets_found', [])) * 20
            
            # SSL issues
            ssl_info = _crawl_results[c_id].get('ssl')
            if ssl_info and not ssl_info.get('valid', True):
                security_score -= 20
            
            # Security headers grade impact
            headers_result = _crawl_results[c_id].get('security_headers')
            if headers_result:
                headers_score = headers_result.get('score', 50)
                security_score = int((security_score + headers_score) / 2)
            
            security_score = max(0, min(100, security_score))
            
            # Determine grade
            if security_score >= 90:
                security_grade = 'A'
            elif security_score >= 80:
                security_grade = 'B'
            elif security_score >= 70:
                security_grade = 'C'
            elif security_score >= 60:
                security_grade = 'D'
            else:
                security_grade = 'F'
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'url': start_url,
                    'pages_crawled': _crawl_results[c_id]['pages_crawled'],
                    'hidden_paths': _crawl_results[c_id]['hidden_paths'],
                    'subdomains': _crawl_results[c_id].get('subdomains', []),
                    'ssl': _crawl_results[c_id].get('ssl'),
                    'seo_issues': _crawl_results[c_id]['seo_issues'],
                    'security_issues': _crawl_results[c_id]['security_issues'],
                    'all_pages': _crawl_results[c_id]['all_pages'],
                    # Enhanced security data
                    'robots_analysis': _crawl_results[c_id].get('robots_analysis'),
                    'waf_detection': _crawl_results[c_id].get('waf_detection'),
                    'cors_findings': _crawl_results[c_id].get('cors_findings'),
                    'http_methods': _crawl_results[c_id].get('http_methods'),
                    'secrets_found': _crawl_results[c_id].get('secrets_found', []),
                    'forms_found': _crawl_results[c_id].get('forms_found', []),
                    'cookies_found': _crawl_results[c_id].get('cookies_found', []),
                    'osint_summary': _crawl_results[c_id].get('osint_summary'),
                    'technologies': _crawl_results[c_id].get('technologies', []),
                    'vulnerabilities': _crawl_results[c_id].get('vulnerabilities', []),
                    'error_pages': _crawl_results[c_id].get('error_pages'),
                    # NEW: Advanced security scan results
                    'dns_recon': _crawl_results[c_id].get('dns_recon'),
                    'email_security': _crawl_results[c_id].get('email_security'),
                    'ssl_analysis': _crawl_results[c_id].get('ssl_analysis'),
                    'subdomain_enum': _crawl_results[c_id].get('subdomain_enum'),
                    'api_discovery': _crawl_results[c_id].get('api_discovery'),
                    'param_fuzzing': _crawl_results[c_id].get('param_fuzzing'),
                    'auth_testing': _crawl_results[c_id].get('auth_testing'),
                    'cloud_scanner': _crawl_results[c_id].get('cloud_scanner'),
                    'security_headers': _crawl_results[c_id].get('security_headers'),
                    'enabled_scans': list(crawl_state.get('enabled_scans', [])),
                    # Security summary
                    'security_score': security_score,
                    'security_grade': security_grade,
                    'critical_vulnerabilities': critical_count,
                    'high_vulnerabilities': high_count,
                    'medium_vulnerabilities': medium_count,
                    'error': _crawl_results[c_id].get('error')
                }, f, indent=2)
            
            if _crawl_results[c_id]['status'] == 'running':
                _crawl_results[c_id]['status'] = 'completed'
                
        except Exception as e:
            error_msg = str(e)
            stack_trace = traceback.format_exc()
            log_e("CrawlerEngine", f"Crawl Failed: {error_msg}\n{stack_trace}")
            _crawl_results[c_id]['status'] = 'failed'
            _crawl_results[c_id]['error'] = error_msg
        finally:
            _crawl_results[c_id]['end_time'] = time.time()
            _crawl_results[c_id]['current_url'] = ''
            if c_id in _active_crawls:
                del _active_crawls[c_id]
    
    thread = threading.Thread(target=run_crawl, daemon=True)
    thread.start()
    
    return crawl_id


def get_status(crawl_id):
    """Get detailed status of a crawl"""
    if crawl_id in _crawl_results:
        result = _crawl_results[crawl_id].copy()
        start = result.get('start_time', 0)
        end = result.get('end_time', time.time())
        result['duration'] = int(end - start)
        
        # Remove large data for status call
        result.pop('all_pages', None)
        result.pop('seo_issues', None)
        result.pop('security_issues', None)
        
        return json.dumps(result)
    return json.dumps({'status': 'not_found'})


def get_diagnostics():
    """Get diagnostic information about crawler capabilities"""
    return json.dumps({
        'security_modules_available': SECURITY_MODULES_AVAILABLE,
        'security_modules_error': SECURITY_MODULES_ERROR,
        'active_crawls': len(_active_crawls),
        'stored_results': len(_crawl_results),
        'modules': {
            'js_analyzer': 'analyze_javascript' in dir(),
            'form_mapper': 'map_forms' in dir(),
            'cookie_auditor': 'audit_cookies' in dir(),
            'osint_engine': 'analyze_osint' in dir(),
            'version_detector': 'analyze_versions' in dir(),
            'vuln_scanner': 'test_cors_misconfiguration' in dir()
        }
    })


def get_analysis_report(crawl_id, output_dir):
    """Get the full analysis report"""
    crawl_output = os.path.join(output_dir, crawl_id)
    report_path = os.path.join(crawl_output, 'analysis_report.json')
    
    if os.path.exists(report_path):
        with open(report_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    # Fallback to in-memory data
    if crawl_id in _crawl_results:
        return json.dumps({
            'url': _crawl_results[crawl_id].get('url'),
            'pages_crawled': _crawl_results[crawl_id].get('pages_crawled', 0),
            'hidden_paths': _crawl_results[crawl_id].get('hidden_paths', []),
            'subdomains': _crawl_results[crawl_id].get('subdomains', []),
            'ssl': _crawl_results[crawl_id].get('ssl'),
            'seo_issues': _crawl_results[crawl_id].get('seo_issues', []),
            'security_issues': _crawl_results[crawl_id].get('security_issues', []),
            'all_pages': _crawl_results[crawl_id].get('all_pages', []),
            # Enhanced security data
            'robots_analysis': _crawl_results[crawl_id].get('robots_analysis'),
            'waf_detection': _crawl_results[crawl_id].get('waf_detection'),
            'cors_findings': _crawl_results[crawl_id].get('cors_findings'),
            'http_methods': _crawl_results[crawl_id].get('http_methods'),
            'secrets_found': _crawl_results[crawl_id].get('secrets_found', []),
            'forms_found': _crawl_results[crawl_id].get('forms_found', []),
            'cookies_found': _crawl_results[crawl_id].get('cookies_found', []),
            'osint_summary': _crawl_results[crawl_id].get('osint_summary'),
            'technologies': _crawl_results[crawl_id].get('technologies', []),
            'vulnerabilities': _crawl_results[crawl_id].get('vulnerabilities', []),
            'error_pages': _crawl_results[crawl_id].get('error_pages'),
            'dns_recon': _crawl_results[crawl_id].get('dns_recon'),
            'email_security': _crawl_results[crawl_id].get('email_security'),
            'ssl_analysis': _crawl_results[crawl_id].get('ssl_analysis'),
            'subdomain_enum': _crawl_results[crawl_id].get('subdomain_enum'),
            'api_discovery': _crawl_results[crawl_id].get('api_discovery'),
            'param_fuzzing': _crawl_results[crawl_id].get('param_fuzzing'),
            'auth_testing': _crawl_results[crawl_id].get('auth_testing'),
            'cloud_scanner': _crawl_results[crawl_id].get('cloud_scanner'),
            'security_headers': _crawl_results[crawl_id].get('security_headers'),
            'enabled_scans': list(_crawl_results[crawl_id].get('enabled_scans', [])),
            'error': _crawl_results[crawl_id].get('error')
        })
    
    return json.dumps({'error': 'Report not found'})


def stop_crawl(crawl_id):
    """Stop a running crawl"""
    if crawl_id in _active_crawls:
        _active_crawls[crawl_id]['stop'] = True
        return json.dumps({'success': True})
    return json.dumps({'success': False, 'error': 'Crawl not found or already stopped'})


def list_crawls():
    """List all crawls"""
    return json.dumps(list(_crawl_results.keys()))


def get_files(crawl_id, output_dir):
    """Get list of files generated by a crawl"""
    crawl_output = os.path.join(output_dir, crawl_id)
    files = {'content': [], 'images': [], 'documents': [], 'html': [], 'stylesheets': [], 'scripts': []}
    
    try:
        for folder in ['content', 'images', 'documents', 'html', 'stylesheets', 'scripts']:
            folder_path = os.path.join(crawl_output, folder)
            if os.path.exists(folder_path):
                files[folder] = os.listdir(folder_path)
    except:
        pass
    
    return json.dumps(files)


def generate_sitemap(crawl_id):
    """Generate sitemap.xml for the crawl"""
    if crawl_id not in _crawl_results:
        return json.dumps({'error': 'Crawl not found'})
    
    data = _crawl_results[crawl_id]
    output_dir = data['output_dir']
    
    try:
        sitemap_path = os.path.join(output_dir, 'sitemap.xml')
        
        # Simple Sitemap XML generation
        xml_content = ['<?xml version="1.0" encoding="UTF-8"?>']
        xml_content.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
        
        for result in data.get('all_pages', []):
            url = result.get('url', '')
            if url:
                xml_content.append(f'  <url><loc>{url}</loc></url>')
        
        xml_content.append('</urlset>')
        
        with open(sitemap_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(xml_content))
            
        return json.dumps({'success': True, 'path': sitemap_path})
    except Exception as e:
        return json.dumps({'error': str(e)})


def export_data(crawl_id, format_type):
    """Export crawl data to CSV or JSON"""
    if crawl_id not in _crawl_results:
        return json.dumps({'error': 'Crawl not found'})
        
    data = _crawl_results[crawl_id]
    output_dir = data['output_dir']
    
    try:
        if format_type.lower() == 'csv':
            path = os.path.join(output_dir, 'crawl_export.csv')
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['URL', 'Title', 'Status', 'Depth', 'Load Time'])
                for p in data.get('all_pages', []):
                    writer.writerow([
                        p.get('url', ''), 
                        p.get('title', ''), 
                        p.get('status', ''), 
                        p.get('depth', ''), 
                        p.get('load_time', 0)
                    ])
            return json.dumps({'success': True, 'path': path})
            
        elif format_type.lower() == 'json':
            path = os.path.join(output_dir, 'crawl_export.json')
            export_obj = {
                'url': data['url'],
                'scanned_at': data['start_time'],
                'pages': data.get('all_pages', []),
                'seo_issues': data.get('seo_issues', []),
                'security_issues': data.get('security_issues', [])
            }
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(export_obj, f, indent=2)
            return json.dumps({'success': True, 'path': path})
            
    except Exception as e:
        return json.dumps({'error': str(e)})
        

def generate_pdf_report(crawl_id):
    """Generate comprehensive PDF report with ALL security findings using ReportLab"""
    if crawl_id not in _crawl_results:
        return json.dumps({'error': 'Crawl not found'})
        
    data = _crawl_results[crawl_id]
    output_dir = data['output_dir']
    pdf_path = os.path.join(output_dir, 'report.pdf')
    
    try:
        doc = SimpleDocTemplate(pdf_path, pagesize=letter, topMargin=36, bottomMargin=36)
        styles = getSampleStyleSheet()
        
        # Custom styles
        styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=styles['Heading2'],
            textColor=colors.darkblue,
            spaceAfter=8
        ))
        styles.add(ParagraphStyle(
            name='SubHeader',
            parent=styles['Heading3'],
            textColor=colors.grey,
            spaceAfter=4
        ))
        styles.add(ParagraphStyle(
            name='Finding',
            parent=styles['BodyText'],
            fontSize=9,
            leftIndent=12
        ))
        styles.add(ParagraphStyle(
            name='Critical',
            parent=styles['BodyText'],
            textColor=colors.red,
            fontSize=9,
            leftIndent=12
        ))
        styles.add(ParagraphStyle(
            name='High',
            parent=styles['BodyText'],
            textColor=colors.orangered,
            fontSize=9,
            leftIndent=12
        ))
        styles.add(ParagraphStyle(
            name='Medium',
            parent=styles['BodyText'],
            textColor=colors.orange,
            fontSize=9,
            leftIndent=12
        ))
        
        story = []
        
        # ============ TITLE ============
        story.append(Paragraph(f"<b>COMPREHENSIVE SECURITY INTELLIGENCE REPORT</b>", styles['Title']))
        story.append(Paragraph(f"Target: {data['url']}", styles['BodyText']))
        story.append(Paragraph(f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}", styles['BodyText']))
        story.append(Spacer(1, 20))
        
        # ============ EXECUTIVE SUMMARY TABLE ============
        secrets_count = len(data.get('secrets_found', []) or [])
        vulns_count = len(data.get('vulnerabilities', []) or [])
        forms_count = len(data.get('forms_found', []) or [])
        cookies_count = len(data.get('cookies_found', []) or [])
        tech_count = len(data.get('technologies', []) or [])
        osint = data.get('osint_summary') or {}
        osint_counts = osint.get('counts') if isinstance(osint, dict) else {} 
        if osint_counts is None:
            osint_counts = {}
        
        summary_data = [
            ['Category', 'Count', 'Category', 'Count'],
            ['Pages Crawled', str(data['pages_crawled']), 'Total URLs', str(data['pages_total'])],
            ['Hidden Paths', str(len(data.get('hidden_paths', []))), 'Subdomains', str(len(data.get('subdomains', [])))],
            ['SEO Issues', str(len(data.get('seo_issues', []))), 'Security Issues', str(len(data.get('security_issues', [])))],
            ['Secrets Leaked', str(secrets_count), 'Vulnerabilities', str(vulns_count)],
            ['Forms Found', str(forms_count), 'Cookies', str(cookies_count)],
            ['Technologies', str(tech_count), 'Emails Found', str(osint_counts.get('emails', 0))],
        ]
        t = Table(summary_data, colWidths=[120, 70, 120, 70])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('ALIGN', (1, 0), (1, -1), 'CENTER'),
            ('ALIGN', (3, 0), (3, -1), 'CENTER'),
        ]))
        story.append(t)
        story.append(Spacer(1, 24))
        
        # ============ SSL/TLS ANALYSIS ============
        ssl_info = data.get('ssl')
        if ssl_info:
            story.append(Paragraph("SSL/TLS CERTIFICATE ANALYSIS", styles['SectionHeader']))
            ssl_data = [
                ['Property', 'Value'],
                ['Valid', 'Yes' if ssl_info.get('valid') else 'No'],
                ['Issuer', ssl_info.get('issuer', 'N/A')[:50]],
                ['Expires', ssl_info.get('expires', 'N/A')],
                ['Days Until Expiry', str(ssl_info.get('days_until_expiry', 'N/A'))],
            ]
            ssl_table = Table(ssl_data, colWidths=[120, 250])
            ssl_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
            ]))
            story.append(ssl_table)
            story.append(Spacer(1, 16))
        
        # ============ WAF/CDN DETECTION ============
        waf = data.get('waf_detection')
        if waf:
            story.append(Paragraph("WAF/CDN DETECTION", styles['SectionHeader']))
            if waf.get('detected'):
                story.append(Paragraph(f"<b>Detected:</b> {waf.get('name', 'Unknown')}", styles['BodyText']))
                if waf.get('confidence'):
                    story.append(Paragraph(f"Confidence: {waf.get('confidence')}", styles['Finding']))
                if waf.get('indicators'):
                    story.append(Paragraph("Indicators:", styles['Finding']))
                    for ind in waf.get('indicators', []):
                        story.append(Paragraph(f"  • {ind}", styles['Finding']))
            else:
                story.append(Paragraph("No WAF/CDN detected", styles['Finding']))
            story.append(Spacer(1, 16))
        
        # ============ CORS FINDINGS ============
        cors = data.get('cors_findings')
        if cors:
            story.append(Paragraph("CORS CONFIGURATION", styles['SectionHeader']))
            if cors.get('vulnerable'):
                story.append(Paragraph(f"<b>⚠️ VULNERABLE - {cors.get('type', 'Misconfiguration')}</b>", styles['Critical']))
                story.append(Paragraph(f"Details: {cors.get('details', 'N/A')}", styles['Finding']))
            else:
                story.append(Paragraph("CORS properly configured", styles['Finding']))
            story.append(Spacer(1, 16))
        
        # ============ HTTP METHODS ============
        http_methods = data.get('http_methods')
        if http_methods:
            story.append(Paragraph("HTTP METHODS ANALYSIS", styles['SectionHeader']))
            allowed = http_methods.get('allowed', [])
            dangerous = http_methods.get('dangerous', [])
            story.append(Paragraph(f"Allowed Methods: {', '.join(allowed) if allowed else 'None detected'}", styles['Finding']))
            if dangerous:
                story.append(Paragraph(f"<b>Dangerous Methods Enabled:</b> {', '.join(dangerous)}", styles['Critical']))
            story.append(Spacer(1, 16))
        
        # ============ ROBOTS.TXT ANALYSIS ============
        robots = data.get('robots_analysis')
        if robots:
            story.append(Paragraph("ROBOTS.TXT ANALYSIS", styles['SectionHeader']))
            story.append(Paragraph(f"Exists: {'Yes' if robots.get('exists') else 'No'}", styles['Finding']))
            disallow = robots.get('disallow_paths', [])
            if disallow:
                story.append(Paragraph(f"Disallowed Paths ({len(disallow)}):", styles['SubHeader']))
                for path in disallow:
                    story.append(Paragraph(f"  • {path}", styles['Finding']))
            sitemaps = robots.get('sitemaps', [])
            if sitemaps:
                story.append(Paragraph(f"Sitemaps ({len(sitemaps)}):", styles['SubHeader']))
                for sitemap in sitemaps:
                    story.append(Paragraph(f"  • {sitemap}", styles['Finding']))
            story.append(Spacer(1, 16))
        
        # ============ SECRETS FOUND (ALL) ============
        secrets = data.get('secrets_found', [])
        if secrets:
            story.append(Paragraph(f"SECRETS LEAKED ({len(secrets)})", styles['SectionHeader']))
            # Group by severity
            critical_secrets = [s for s in secrets if s.get('severity') == 'critical']
            high_secrets = [s for s in secrets if s.get('severity') == 'high']
            other_secrets = [s for s in secrets if s.get('severity') not in ['critical', 'high']]
            
            if critical_secrets:
                story.append(Paragraph(f"CRITICAL ({len(critical_secrets)}):", styles['SubHeader']))
                for secret in critical_secrets:
                    story.append(Paragraph(f"  • [{secret.get('type', 'Unknown')}] {secret.get('file', 'N/A')} - Match: {secret.get('match', '')[:60]}...", styles['Critical']))
            
            if high_secrets:
                story.append(Paragraph(f"HIGH ({len(high_secrets)}):", styles['SubHeader']))
                for secret in high_secrets:
                    story.append(Paragraph(f"  • [{secret.get('type', 'Unknown')}] {secret.get('file', 'N/A')}", styles['High']))
            
            if other_secrets:
                story.append(Paragraph(f"OTHER ({len(other_secrets)}):", styles['SubHeader']))
                for secret in other_secrets:
                    story.append(Paragraph(f"  • [{secret.get('type', 'Unknown')}] {secret.get('file', 'N/A')}", styles['Finding']))
            story.append(Spacer(1, 16))
        
        # ============ VULNERABILITIES (ALL) ============
        vulns = data.get('vulnerabilities', [])
        if vulns:
            story.append(Paragraph(f"VULNERABILITIES ({len(vulns)})", styles['SectionHeader']))
            # Group by severity
            for severity in ['critical', 'high', 'medium', 'low', 'info']:
                sev_vulns = [v for v in vulns if v.get('severity', '').lower() == severity]
                if sev_vulns:
                    style_name = severity.capitalize() if severity in ['critical', 'high', 'medium'] else 'Finding'
                    story.append(Paragraph(f"{severity.upper()} ({len(sev_vulns)}):", styles['SubHeader']))
                    for vuln in sev_vulns:
                        vuln_type = vuln.get('type', 'Unknown')
                        cve = vuln.get('cve', '')
                        desc = vuln.get('description', '')[:80]
                        url = vuln.get('url', '')[:50]
                        text = f"  • {vuln_type}"
                        if cve:
                            text += f" ({cve})"
                        if desc:
                            text += f": {desc}"
                        if url:
                            text += f" @ {url}"
                        story.append(Paragraph(text, styles.get(style_name, styles['Finding'])))
            story.append(Spacer(1, 16))
        
        # ============ TECHNOLOGIES DETECTED (ALL) ============
        tech = data.get('technologies', [])
        if tech:
            story.append(Paragraph(f"TECHNOLOGIES DETECTED ({len(tech)})", styles['SectionHeader']))
            tech_data = [['Name', 'Version', 'Category', 'Confidence']]
            for t_item in tech:
                name = t_item.get('name', 'Unknown')
                version = t_item.get('version', '-')
                category = t_item.get('category', '-')
                confidence = t_item.get('confidence', '-')
                tech_data.append([name, str(version), category, str(confidence)])
            
            tech_table = Table(tech_data, colWidths=[120, 60, 100, 70])
            tech_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ]))
            story.append(tech_table)
            story.append(Spacer(1, 16))
        
        # ============ FORMS FOUND (ALL) ============
        forms = data.get('forms_found', [])
        if forms:
            story.append(Paragraph(f"FORMS DETECTED ({len(forms)})", styles['SectionHeader']))
            for i, form in enumerate(forms, 1):
                action = form.get('action', 'N/A')
                method = form.get('method', 'GET').upper()
                form_type = form.get('type', 'unknown')
                has_csrf = form.get('has_csrf', False)
                fields = form.get('fields', [])
                
                story.append(Paragraph(f"Form #{i}: {form_type.upper()}", styles['SubHeader']))
                story.append(Paragraph(f"  Action: {action} | Method: {method} | CSRF: {'Yes' if has_csrf else 'NO ⚠️'}", styles['Finding']))
                if fields:
                    field_names = [f.get('name', 'unnamed') for f in fields[:10]]
                    story.append(Paragraph(f"  Fields: {', '.join(field_names)}", styles['Finding']))
            story.append(Spacer(1, 16))
        
        # ============ COOKIES ANALYSIS (ALL) ============
        cookies = data.get('cookies_found', [])
        if cookies:
            story.append(Paragraph(f"COOKIES ANALYSIS ({len(cookies)})", styles['SectionHeader']))
            insecure_cookies = [c for c in cookies if c.get('issues')]
            if insecure_cookies:
                story.append(Paragraph(f"Cookies with Issues ({len(insecure_cookies)}):", styles['SubHeader']))
                for cookie in insecure_cookies:
                    name = cookie.get('name', 'Unknown')
                    issues = cookie.get('issues', [])
                    story.append(Paragraph(f"  • {name}: {', '.join(issues)}", styles['High']))
            
            secure_cookies = [c for c in cookies if not c.get('issues')]
            if secure_cookies:
                story.append(Paragraph(f"Secure Cookies ({len(secure_cookies)}):", styles['SubHeader']))
                for cookie in secure_cookies:
                    story.append(Paragraph(f"  • {cookie.get('name', 'Unknown')}", styles['Finding']))
            story.append(Spacer(1, 16))
        
        # ============ HIDDEN PATHS FOUND (ALL) ============
        hidden_paths = data.get('hidden_paths', [])
        if hidden_paths:
            story.append(Paragraph(f"HIDDEN PATHS DISCOVERED ({len(hidden_paths)})", styles['SectionHeader']))
            path_data = [['Path', 'Status', 'Type']]
            for path in hidden_paths:
                url = path.get('url', 'N/A')
                status = path.get('status', 'N/A')
                path_type = path.get('type', 'unknown')
                path_data.append([url[:60], str(status), path_type])
            
            path_table = Table(path_data, colWidths=[250, 50, 80])
            path_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTSIZE', (0, 0), (-1, -1), 8),
            ]))
            story.append(path_table)
            story.append(Spacer(1, 16))
        
        # ============ SUBDOMAINS (ALL) ============
        subdomains = data.get('subdomains', [])
        if subdomains:
            story.append(Paragraph(f"SUBDOMAINS DISCOVERED ({len(subdomains)})", styles['SectionHeader']))
            for sub in subdomains:
                if isinstance(sub, dict):
                    name = sub.get('subdomain', sub.get('name', 'N/A'))
                    source = sub.get('source', 'Unknown')
                    story.append(Paragraph(f"  • {name} (Source: {source})", styles['Finding']))
                else:
                    story.append(Paragraph(f"  • {sub}", styles['Finding']))
            story.append(Spacer(1, 16))
        
        # ============ OSINT DETAILED SUMMARY ============
        if osint and isinstance(osint, dict):
            story.append(Paragraph("OSINT INTELLIGENCE", styles['SectionHeader']))
            
            # Emails
            emails = osint.get('unique_emails') or []
            if emails:
                story.append(Paragraph(f"Email Addresses ({len(emails)}):", styles['SubHeader']))
                for email in emails:
                    story.append(Paragraph(f"  • {email}", styles['Finding']))
            
            # Phones
            phones = osint.get('unique_phones') or []
            if phones:
                story.append(Paragraph(f"Phone Numbers ({len(phones)}):", styles['SubHeader']))
                for phone in phones:
                    story.append(Paragraph(f"  • {phone}", styles['Finding']))
            
            # Social Media
            social = osint.get('social_presence') or {}
            if social:
                story.append(Paragraph(f"Social Media Profiles ({len(social)}):", styles['SubHeader']))
                for platform, urls in social.items():
                    for url in (urls if isinstance(urls, list) else [urls]):
                        story.append(Paragraph(f"  • {platform}: {url}", styles['Finding']))
            
            # Names/Employees
            names = osint.get('unique_names') or []
            if names:
                story.append(Paragraph(f"Names/Employees Found ({len(names)}):", styles['SubHeader']))
                for name in names[:30]:  # Limit names to 30
                    story.append(Paragraph(f"  • {name}", styles['Finding']))
            
            # CT Subdomains
            ct_subdomains = osint.get('ct_subdomains') or []
            if ct_subdomains:
                story.append(Paragraph(f"Certificate Transparency Subdomains ({len(ct_subdomains)}):", styles['SubHeader']))
                for sub in ct_subdomains:
                    if isinstance(sub, dict):
                        story.append(Paragraph(f"  • {sub.get('subdomain', sub)}", styles['Finding']))
                    else:
                        story.append(Paragraph(f"  • {sub}", styles['Finding']))
            
            # Wayback URLs
            wayback = osint.get('wayback_urls') or []
            if wayback:
                story.append(Paragraph(f"Wayback Machine URLs ({len(wayback)}):", styles['SubHeader']))
                for item in wayback:
                    if isinstance(item, dict):
                        story.append(Paragraph(f"  • {item.get('url', str(item))[:80]}", styles['Finding']))
                    else:
                        story.append(Paragraph(f"  • {str(item)[:80]}", styles['Finding']))
            
            # PII Detected
            pii = osint.get('pii_findings') or []
            if pii:
                story.append(Paragraph(f"PII Detected ({len(pii)}):", styles['SubHeader']))
                for p in pii:
                    if isinstance(p, dict):
                        pii_type = p.get('type', 'Unknown')
                        value = p.get('value_masked', p.get('value', 'N/A'))[:40]
                        story.append(Paragraph(f"  • [{pii_type}] {value}", styles['Critical']))
                    else:
                        story.append(Paragraph(f"  • {p}", styles['Finding']))
            
            story.append(Spacer(1, 16))
        
        # ============ ERROR PAGES ANALYSIS ============
        error_pages_data = data.get('error_pages')
        if error_pages_data:
            story.append(Paragraph("ERROR PAGE ANALYSIS", styles['SectionHeader']))
            # Handle new structure: {error_pages: [...], info_disclosure: [...]}
            error_pages_list = error_pages_data.get('error_pages', []) if isinstance(error_pages_data, dict) else error_pages_data
            info_disclosure = error_pages_data.get('info_disclosure', []) if isinstance(error_pages_data, dict) else []
            
            if error_pages_list:
                story.append(Paragraph(f"Found {len(error_pages_list)} error page issues:", styles['Finding']))
                for ep in error_pages_list:
                    if isinstance(ep, dict):
                        issue = ep.get('issue', 'Unknown issue')
                        severity = ep.get('severity', 'Medium')
                        url = ep.get('url', 'N/A')
                        story.append(Paragraph(f"  • [{severity}] {issue}", styles['Critical'] if severity == 'High' else styles['Medium']))
                        story.append(Paragraph(f"    URL: {url}", styles['Normal']))
            elif info_disclosure:
                for disclosure in info_disclosure:
                    story.append(Paragraph(f"  • {disclosure}", styles['Finding']))
            else:
                story.append(Paragraph("No information disclosure found in error pages.", styles['Normal']))
            story.append(Spacer(1, 16))
        
        # ============ SEO ISSUES (ALL) ============
        seo_issues = data.get('seo_issues', [])
        if seo_issues:
            story.append(Paragraph(f"SEO ISSUES ({len(seo_issues)})", styles['SectionHeader']))
            for issue in seo_issues:
                if isinstance(issue, dict):
                    issue_text = issue.get('issue', str(issue))
                    severity = issue.get('severity', 'info')
                    story.append(Paragraph(f"  • [{severity.upper()}] {issue_text}", styles['Finding']))
                else:
                    story.append(Paragraph(f"  • {issue}", styles['Finding']))
            story.append(Spacer(1, 16))
        
        # ============ SECURITY ISSUES (ALL) ============
        security_issues = data.get('security_issues', [])
        if security_issues:
            story.append(Paragraph(f"SECURITY ISSUES ({len(security_issues)})", styles['SectionHeader']))
            for issue in security_issues:
                if isinstance(issue, dict):
                    issue_text = issue.get('issue', str(issue))
                    severity = issue.get('severity', 'info')
                    style_name = 'Critical' if severity == 'critical' else 'High' if severity == 'high' else 'Finding'
                    story.append(Paragraph(f"  • [{severity.upper()}] {issue_text}", styles.get(style_name, styles['Finding'])))
                else:
                    story.append(Paragraph(f"  • {issue}", styles['Finding']))
            story.append(Spacer(1, 16))
        
        # ============ ALL PAGES CRAWLED ============
        all_pages = data.get('all_pages', [])
        if all_pages:
            story.append(Paragraph(f"PAGES CRAWLED ({len(all_pages)})", styles['SectionHeader']))
            pages_data = [['URL', 'Status', 'Time (s)', 'Size (KB)']]
            for page in all_pages:
                url = page.get('url', 'N/A')[:55]
                status = page.get('status', 'N/A')
                load_time = f"{page.get('load_time', 0):.2f}" if page.get('load_time') else '-'
                size = f"{page.get('size', 0) / 1024:.1f}" if page.get('size') else '-'
                pages_data.append([url, str(status), load_time, size])
            
            pages_table = Table(pages_data, colWidths=[250, 50, 50, 50])
            pages_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
            ]))
            story.append(pages_table)
        
        # ============ REPORT FOOTER ============
        story.append(Spacer(1, 30))
        story.append(Paragraph("--- END OF REPORT ---", styles['BodyText']))
        story.append(Paragraph(f"Generated by Bitflow Security Intelligence Platform", styles['BodyText']))
        
        doc.build(story)
        return json.dumps({'success': True, 'path': pdf_path})
        
    except Exception as e:
        log_e("CrawlerEngine", f"PDF generation error: {e}")
        return json.dumps({'error': str(e)})
