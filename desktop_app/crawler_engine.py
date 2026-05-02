# crawler_engine.py
# Website Intelligence Platform - Comprehensive Website Analyzer
# Aggressive scanning, SEO analysis, security checks, performance metrics

import os
import uuid
import json
import time
import re
import ssl
import socket
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import defaultdict

try:
    from android.util import Log
    def log_e(tag, msg): Log.e(tag, str(msg))
    def log_i(tag, msg): Log.i(tag, str(msg))
except ImportError:
    import traceback
    def log_e(tag, msg): print(f"E/{tag}: {msg}\n{traceback.format_exc()}")
    def log_i(tag, msg): print(f"I/{tag}: {msg}")

try:
    import httpx
    from bs4 import BeautifulSoup
    from markdownify import markdownify as md
    import tldextract
except ImportError as e:
    print(f"Warning: Some packages not available: {e}")

# In-memory state for active crawls
_active_crawls = {}
_crawl_results = {}

# Common hidden paths to probe
HIDDEN_PATHS = [
    '/admin', '/administrator', '/wp-admin', '/wp-login.php', '/login', '/signin',
    '/dashboard', '/panel', '/cpanel', '/phpmyadmin',
    '/backup', '/backups', '/bak', '/old', '/archive',
    '/test', '/testing', '/dev', '/development', '/staging', '/demo', '/beta',
    '/api', '/api/v1', '/api/v2', '/graphql', '/rest',
    '/config', '/settings', '/configuration', '/setup',
    '/.git', '/.git/config', '/.env', '/.htaccess', '/.htpasswd',
    '/config.php', '/config.json', '/config.yml', '/settings.py',
    '/robots.txt', '/sitemap.xml', '/sitemap_index.xml',
    '/wp-config.php', '/web.config', '/composer.json', '/package.json',
    '/readme.md', '/README.md', '/CHANGELOG.md', '/LICENSE',
    '/uploads', '/images', '/assets', '/static', '/media', '/files',
    '/private', '/secret', '/hidden', '/internal',
    '/.well-known/security.txt', '/security.txt',
    '/error', '/404', '/500', '/debug',
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
    """Crawl a single page and perform all analysis"""
    crawl_id = crawl_state['crawl_id']
    output_dir = crawl_state['output_dir']
    visited = crawl_state['visited']
    
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
        'tech': None
    }
    
    # Check if stopped
    if crawl_id in _active_crawls and _active_crawls[crawl_id].get('stop'):
        return result
    
    # Update current URL in results
    if crawl_id in _crawl_results:
        _crawl_results[crawl_id]['current_url'] = url
    
    try:
        with httpx.Client(timeout=30, follow_redirects=True, verify=False) as client:
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
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
                
                # SEO Analysis
                result['seo'] = analyze_seo(html, url)
                
                # Security Analysis
                result['security'] = analyze_security(dict(response.headers), url)
                
                # Technology Detection
                result['tech'] = detect_technology(html, dict(response.headers))
                
                # Extract Assets
                result['assets'] = extract_all_assets(html, url)
                
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
    """Probe common hidden paths"""
    discovered = []
    parsed = urlparse(base_url)
    base = f"{parsed.scheme}://{parsed.netloc}"
    
    for path in HIDDEN_PATHS:
        url = base + path
        if url in crawl_state['visited']:
            continue
        
        try:
            with httpx.Client(timeout=10, follow_redirects=False, verify=False) as client:
                response = client.head(url, headers={'User-Agent': 'Mozilla/5.0'})
                if response.status_code in [200, 301, 302, 403]:
                    discovered.append({
                        'url': url,
                        'status': response.status_code,
                        'path': path
                    })
        except:
            pass
    
    return discovered


def start_crawl(url, depth, output_dir):
    """Start a new crawl with comprehensive analysis"""
    crawl_id = str(uuid.uuid4())
    
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
    
    _active_crawls[crawl_id] = {'stop': False}
    _crawl_results[crawl_id] = {
        'status': 'running',
        'url': url,
        'depth': depth,
        'pages_crawled': 0,
        'pages_total': 0,
        'pages_queued': 0,
        'current_url': url,
        'start_time': time.time(),
        'output_dir': crawl_output,
        'hidden_paths': [],
        'all_pages': [],
        'seo_issues': [],
        'security_issues': []
    }
    
    import threading
    
    def run_crawl(start_url=url, max_depth=depth, c_id=crawl_id, c_out=crawl_output):
        log_i("CrawlerEngine", f"Starting crawl {c_id} for {start_url}")
        try:
            crawl_state = {
                'crawl_id': c_id,
                'output_dir': c_out,
                'visited': set(),
                'to_visit': [(start_url, 0)],
                'max_depth': max_depth
            }
            
            all_results = []
            
            # Initial connectivity check
            _crawl_results[c_id]['current_url'] = 'Checking connectivity...'
            try:
                with httpx.Client(timeout=15, follow_redirects=True, verify=False) as client:
                    response = client.head(start_url, headers={'User-Agent': 'Mozilla/5.0'})
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
            
            # First, probe hidden paths
            _crawl_results[c_id]['current_url'] = 'Probing hidden paths...'
            hidden = probe_hidden_paths(start_url, crawl_state)
            _crawl_results[c_id]['hidden_paths'] = hidden
            
            # Add discovered hidden paths to queue
            for h in hidden:
                if h['status'] == 200:
                    crawl_state['to_visit'].append((h['url'], 1))
            
            # SSL Analysis (once for the domain)
            ssl_info = analyze_ssl(start_url)
            _crawl_results[c_id]['ssl'] = ssl_info
            
            # Main crawl loop with concurrent processing
            with ThreadPoolExecutor(max_workers=3) as executor:
                while crawl_state['to_visit']:
                    if _active_crawls.get(c_id, {}).get('stop'):
                        break
                    
                    # Get batch of URLs to process
                    batch = []
                    while crawl_state['to_visit'] and len(batch) < 3:
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
            
            # Save analysis report
            report_path = os.path.join(c_out, 'analysis_report.json')
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump({
                    'url': start_url,
                    'pages_crawled': _crawl_results[c_id]['pages_crawled'],
                    'hidden_paths': _crawl_results[c_id]['hidden_paths'],
                    'ssl': _crawl_results[c_id].get('ssl'),
                    'seo_issues': _crawl_results[c_id]['seo_issues'],
                    'security_issues': _crawl_results[c_id]['security_issues'],
                    'all_pages': _crawl_results[c_id]['all_pages']
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
            'ssl': _crawl_results[crawl_id].get('ssl'),
            'seo_issues': _crawl_results[crawl_id].get('seo_issues', []),
            'security_issues': _crawl_results[crawl_id].get('security_issues', []),
            'all_pages': _crawl_results[crawl_id].get('all_pages', [])
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
