# robots_parser.py
# robots.txt & Sitemap Intelligence - Extract hidden paths and map URLs

import re
import xml.etree.ElementTree as ET
from urllib.parse import urljoin, urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import httpx
except ImportError:
    httpx = None


def fetch_robots_txt(base_url, user_agent='Mozilla/5.0', timeout=10):
    """Fetch robots.txt from a website"""
    if not httpx:
        return None
    
    robots_url = urljoin(base_url, '/robots.txt')
    
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True, verify=False) as client:
            response = client.get(robots_url, headers={'User-Agent': user_agent})
            if response.status_code == 200:
                return {
                    'url': robots_url,
                    'content': response.text,
                    'status': 200
                }
            else:
                return {
                    'url': robots_url,
                    'content': None,
                    'status': response.status_code
                }
    except Exception as e:
        return {
            'url': robots_url,
            'content': None,
            'status': 'error',
            'error': str(e)
        }


def parse_robots_txt(robots_content):
    """Parse robots.txt content"""
    result = {
        'user_agents': {},
        'sitemaps': [],
        'disallow_all': [],  # Paths disallowed for all bots
        'allow_all': [],
        'crawl_delay': None,
        'interesting_paths': []  # Paths that might be sensitive
    }
    
    if not robots_content:
        return result
    
    current_ua = '*'
    
    for line in robots_content.split('\n'):
        line = line.strip()
        
        # Skip comments and empty lines
        if not line or line.startswith('#'):
            continue
        
        # Parse directive
        if ':' in line:
            directive, value = line.split(':', 1)
            directive = directive.strip().lower()
            value = value.strip()
            
            if directive == 'user-agent':
                current_ua = value
                if current_ua not in result['user_agents']:
                    result['user_agents'][current_ua] = {
                        'disallow': [],
                        'allow': [],
                        'crawl_delay': None
                    }
            
            elif directive == 'disallow':
                if value:
                    if current_ua not in result['user_agents']:
                        result['user_agents'][current_ua] = {'disallow': [], 'allow': [], 'crawl_delay': None}
                    result['user_agents'][current_ua]['disallow'].append(value)
                    
                    if current_ua == '*':
                        result['disallow_all'].append(value)
                    
                    # Check for interesting/sensitive paths
                    sensitive_patterns = [
                        r'/admin', r'/private', r'/backup', r'/config',
                        r'/api', r'/internal', r'/dev', r'/staging',
                        r'/test', r'/debug', r'/secret', r'/hidden',
                        r'/beta', r'/dashboard', r'/panel', r'/wp-admin'
                    ]
                    for pattern in sensitive_patterns:
                        if re.search(pattern, value, re.IGNORECASE):
                            result['interesting_paths'].append({
                                'path': value,
                                'reason': f'Matches sensitive pattern: {pattern}',
                                'severity': 'Medium'
                            })
                            break
            
            elif directive == 'allow':
                if value:
                    if current_ua not in result['user_agents']:
                        result['user_agents'][current_ua] = {'disallow': [], 'allow': [], 'crawl_delay': None}
                    result['user_agents'][current_ua]['allow'].append(value)
                    
                    if current_ua == '*':
                        result['allow_all'].append(value)
            
            elif directive == 'sitemap':
                if value:
                    result['sitemaps'].append(value)
            
            elif directive == 'crawl-delay':
                try:
                    delay = float(value)
                    if current_ua not in result['user_agents']:
                        result['user_agents'][current_ua] = {'disallow': [], 'allow': [], 'crawl_delay': None}
                    result['user_agents'][current_ua]['crawl_delay'] = delay
                    if current_ua == '*':
                        result['crawl_delay'] = delay
                except:
                    pass
    
    return result


def fetch_sitemap(sitemap_url, user_agent='Mozilla/5.0', timeout=15):
    """Fetch a sitemap"""
    if not httpx:
        return None
    
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True, verify=False) as client:
            response = client.get(sitemap_url, headers={'User-Agent': user_agent})
            if response.status_code == 200:
                return {
                    'url': sitemap_url,
                    'content': response.text,
                    'status': 200
                }
    except:
        pass
    
    return None


def parse_sitemap(sitemap_content, sitemap_url):
    """Parse sitemap XML content"""
    result = {
        'urls': [],
        'nested_sitemaps': [],
        'error': None
    }
    
    if not sitemap_content:
        return result
    
    try:
        # Remove namespace for easier parsing
        content = re.sub(r'\s+xmlns[^"]*"[^"]*"', '', sitemap_content)
        
        root = ET.fromstring(content)
        
        # Check if this is a sitemap index
        for sitemap in root.findall('.//sitemap'):
            loc = sitemap.find('loc')
            if loc is not None and loc.text:
                result['nested_sitemaps'].append(loc.text)
        
        # Get URLs
        for url in root.findall('.//url'):
            loc = url.find('loc')
            if loc is not None and loc.text:
                url_info = {'loc': loc.text}
                
                lastmod = url.find('lastmod')
                if lastmod is not None and lastmod.text:
                    url_info['lastmod'] = lastmod.text
                
                priority = url.find('priority')
                if priority is not None and priority.text:
                    url_info['priority'] = priority.text
                
                changefreq = url.find('changefreq')
                if changefreq is not None and changefreq.text:
                    url_info['changefreq'] = changefreq.text
                
                result['urls'].append(url_info)
                
    except ET.ParseError as e:
        result['error'] = f'XML parse error: {str(e)}'
    except Exception as e:
        result['error'] = str(e)
    
    return result


def probe_disallowed_paths(base_url, disallowed_paths, user_agent='Mozilla/5.0'):
    """Probe disallowed paths to check if they're actually protected"""
    findings = []
    
    if not httpx:
        return findings
    
    def check_path(path):
        full_url = urljoin(base_url, path)
        try:
            with httpx.Client(timeout=5, follow_redirects=False, verify=False) as client:
                response = client.head(full_url, headers={'User-Agent': user_agent})
                
                # Interesting responses
                if response.status_code == 200:
                    return {
                        'path': path,
                        'url': full_url,
                        'status': 200,
                        'severity': 'High',
                        'issue': 'Disallowed path accessible (200 OK)',
                        'description': 'Path blocked in robots.txt but publicly accessible'
                    }
                elif response.status_code in [301, 302]:
                    location = response.headers.get('location', '')
                    return {
                        'path': path,
                        'url': full_url,
                        'status': response.status_code,
                        'severity': 'Medium',
                        'issue': f'Disallowed path redirects ({response.status_code})',
                        'redirect_to': location
                    }
                elif response.status_code == 403:
                    return {
                        'path': path,
                        'url': full_url,
                        'status': 403,
                        'severity': 'Low',
                        'issue': 'Disallowed path returns 403 (protected)',
                        'description': 'Path exists but access is forbidden'
                    }
        except:
            pass
        return None
    
    # Probe concurrently
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(check_path, path): path for path in disallowed_paths[:30]}  # Limit to 30
        for future in as_completed(futures):
            result = future.result()
            if result:
                findings.append(result)
    
    return findings


def analyze_robots_and_sitemap(base_url, user_agent='Mozilla/5.0', max_sitemap_urls=500):
    """
    Complete analysis of robots.txt and sitemaps
    
    Args:
        base_url: Base URL of the site
        user_agent: User agent string
        max_sitemap_urls: Maximum URLs to extract from sitemaps
    
    Returns:
        Dictionary with analysis results
    """
    results = {
        'robots_txt': {
            'found': False,
            'url': None,
            'content': None,
            'parsed': None
        },
        'sitemaps': [],
        'all_sitemap_urls': [],
        'disallowed_probes': [],
        'interesting_findings': [],
        'summary': {
            'robots_found': False,
            'sitemaps_found': 0,
            'total_urls_in_sitemaps': 0,
            'disallowed_paths': 0,
            'accessible_disallowed': 0,
            'interesting_paths': 0
        }
    }
    
    # Fetch robots.txt
    robots = fetch_robots_txt(base_url, user_agent)
    if robots and robots.get('content'):
        results['robots_txt']['found'] = True
        results['robots_txt']['url'] = robots['url']
        results['robots_txt']['content'] = robots['content']
        
        parsed = parse_robots_txt(robots['content'])
        results['robots_txt']['parsed'] = parsed
        results['summary']['robots_found'] = True
        results['summary']['disallowed_paths'] = len(parsed.get('disallow_all', []))
        results['summary']['interesting_paths'] = len(parsed.get('interesting_paths', []))
        
        # Add interesting paths to findings
        results['interesting_findings'].extend(parsed.get('interesting_paths', []))
        
        # Probe disallowed paths
        disallowed = parsed.get('disallow_all', [])
        if disallowed:
            probes = probe_disallowed_paths(base_url, disallowed, user_agent)
            results['disallowed_probes'] = probes
            results['summary']['accessible_disallowed'] = len([p for p in probes if p['status'] == 200])
        
        # Get sitemaps from robots.txt
        sitemap_urls = parsed.get('sitemaps', [])
    else:
        # Try common sitemap locations
        sitemap_urls = [
            urljoin(base_url, '/sitemap.xml'),
            urljoin(base_url, '/sitemap_index.xml'),
            urljoin(base_url, '/sitemap/sitemap.xml'),
        ]
    
    # Parse sitemaps (with recursion for sitemap indexes)
    all_urls = []
    processed_sitemaps = set()
    sitemaps_to_process = list(sitemap_urls)
    
    while sitemaps_to_process and len(all_urls) < max_sitemap_urls:
        sitemap_url = sitemaps_to_process.pop(0)
        
        if sitemap_url in processed_sitemaps:
            continue
        processed_sitemaps.add(sitemap_url)
        
        sitemap_data = fetch_sitemap(sitemap_url, user_agent)
        if sitemap_data and sitemap_data.get('content'):
            parsed_sitemap = parse_sitemap(sitemap_data['content'], sitemap_url)
            
            results['sitemaps'].append({
                'url': sitemap_url,
                'urls_count': len(parsed_sitemap['urls']),
                'nested_count': len(parsed_sitemap['nested_sitemaps']),
                'error': parsed_sitemap.get('error')
            })
            
            # Add URLs
            for url_info in parsed_sitemap['urls']:
                if len(all_urls) < max_sitemap_urls:
                    all_urls.append(url_info)
            
            # Add nested sitemaps to queue
            for nested in parsed_sitemap['nested_sitemaps']:
                if nested not in processed_sitemaps:
                    sitemaps_to_process.append(nested)
    
    results['all_sitemap_urls'] = all_urls
    results['summary']['sitemaps_found'] = len(results['sitemaps'])
    results['summary']['total_urls_in_sitemaps'] = len(all_urls)
    
    return results


def find_orphan_pages(sitemap_urls, crawled_urls):
    """Find pages in sitemap that weren't found during crawling"""
    sitemap_set = set(url['loc'] if isinstance(url, dict) else url for url in sitemap_urls)
    crawled_set = set(crawled_urls)
    
    orphans = sitemap_set - crawled_set
    
    return [{
        'url': url,
        'issue': 'Orphan page - in sitemap but not linked from site',
        'severity': 'Low'
    } for url in orphans]


def get_robots_sitemap_summary(results):
    """Generate summary for robots.txt and sitemap analysis"""
    summary = {
        'robots_txt_found': results['robots_txt']['found'],
        'crawl_delay': results['robots_txt']['parsed'].get('crawl_delay') if results['robots_txt']['parsed'] else None,
        'sitemaps_found': results['summary']['sitemaps_found'],
        'urls_in_sitemaps': results['summary']['total_urls_in_sitemaps'],
        'disallowed_paths': results['summary']['disallowed_paths'],
        'accessible_disallowed_paths': results['summary']['accessible_disallowed'],
        'security_issues': []
    }
    
    # Add accessible disallowed paths as security issues
    for probe in results['disallowed_probes']:
        if probe['status'] == 200:
            summary['security_issues'].append({
                'issue': f"Sensitive path {probe['path']} accessible despite robots.txt block",
                'severity': probe['severity'],
                'url': probe['url']
            })
    
    return summary
