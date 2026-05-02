# subdomain_enum.py
# Subdomain Enumeration - crt.sh, DNS brute force, common subdomain discovery

import re
import socket
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import httpx
except ImportError:
    httpx = None

# Common subdomains to check
COMMON_SUBDOMAINS = [
    # Development & Staging
    'dev', 'develop', 'development', 'staging', 'stage', 'stg',
    'test', 'testing', 'qa', 'uat', 'sandbox', 'demo', 'preview',
    'beta', 'alpha', 'canary', 'rc', 'release',
    
    # Production variants
    'www', 'www1', 'www2', 'www3', 'web', 'web1', 'web2',
    'app', 'apps', 'application', 'portal', 'dashboard',
    
    # API & Services
    'api', 'api1', 'api2', 'api-v1', 'api-v2', 'rest', 'graphql',
    'ws', 'websocket', 'socket', 'realtime', 'stream',
    'service', 'services', 'svc', 'gateway', 'proxy',
    
    # Infrastructure
    'mail', 'email', 'smtp', 'imap', 'pop', 'pop3', 'mx', 'webmail',
    'ftp', 'sftp', 'files', 'file', 'storage', 'cdn', 'static', 'assets',
    'media', 'images', 'img', 'video', 'videos',
    
    # Admin & Management
    'admin', 'administrator', 'adm', 'manage', 'manager', 'management',
    'panel', 'cpanel', 'whm', 'plesk', 'console', 'control',
    'cms', 'backend', 'backoffice', 'internal', 'intranet',
    
    # Security & Auth
    'auth', 'login', 'signin', 'sso', 'oauth', 'identity', 'id',
    'secure', 'ssl', 'vpn', 'remote', 'rdp',
    
    # Database & Cache
    'db', 'database', 'mysql', 'postgres', 'mongo', 'redis', 'cache',
    'sql', 'data', 'datastore', 'warehouse',
    
    # Monitoring & Logging
    'monitor', 'monitoring', 'status', 'health', 'logs', 'log',
    'metrics', 'grafana', 'kibana', 'elastic', 'prometheus',
    'sentry', 'newrelic', 'datadog',
    
    # CI/CD & DevOps
    'git', 'gitlab', 'github', 'bitbucket', 'svn', 'repo', 'repos',
    'jenkins', 'ci', 'cd', 'build', 'deploy', 'releases',
    'docker', 'k8s', 'kubernetes', 'rancher', 'container',
    
    # Cloud Services
    'aws', 's3', 'ec2', 'azure', 'gcp', 'cloud', 'paas',
    'heroku', 'digitalocean', 'linode', 'vultr',
    
    # Communication
    'chat', 'im', 'message', 'messaging', 'slack', 'teams',
    'forum', 'community', 'support', 'help', 'helpdesk', 'ticket',
    'blog', 'news', 'press', 'docs', 'documentation', 'wiki',
    
    # E-commerce
    'shop', 'store', 'cart', 'checkout', 'pay', 'payment', 'billing',
    'order', 'orders', 'invoice', 'invoices',
    
    # Mobile
    'mobile', 'm', 'android', 'ios', 'app-api',
    
    # Geographic
    'us', 'eu', 'uk', 'de', 'fr', 'jp', 'cn', 'au', 'ca', 'in',
    'asia', 'europe', 'na', 'apac',
    
    # Numbered
    'srv1', 'srv2', 'server1', 'server2', 'node1', 'node2',
    'host1', 'host2', 'ns1', 'ns2', 'dns1', 'dns2',
    
    # Misc
    'old', 'new', 'legacy', 'archive', 'backup', 'bak', 'temp', 'tmp',
    'origin', 'edge', 'lb', 'loadbalancer', 'cluster',
]

# Extended list for deep enumeration
EXTENDED_SUBDOMAINS = COMMON_SUBDOMAINS + [
    # More development
    'dev1', 'dev2', 'dev3', 'test1', 'test2', 'stage1', 'stage2',
    'preprod', 'pre-prod', 'pre-production', 'postprod',
    'local', 'localhost', 'devops', 'integration', 'int',
    
    # More infrastructure
    'proxy1', 'proxy2', 'gateway1', 'gateway2', 'router', 'firewall',
    'nat', 'bastion', 'jump', 'jumpbox', 'ssh',
    
    # Legacy systems
    'legacy1', 'legacy2', 'old1', 'old2', 'v1', 'v2', 'v3',
    'classic', 'lite', 'pro', 'enterprise', 'business',
    
    # Hidden/Internal
    'hidden', 'private', 'secret', 'confidential', 'restricted',
    'corp', 'corporate', 'employee', 'staff', 'hr',
]


def extract_domain(url):
    """Extract root domain from URL"""
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    parsed = urlparse(url)
    hostname = parsed.netloc.split(':')[0]
    
    # Get root domain (handle subdomains)
    parts = hostname.split('.')
    if len(parts) >= 2:
        # Handle common TLDs like co.uk, com.au, etc.
        if len(parts) >= 3 and parts[-2] in ['co', 'com', 'org', 'net', 'gov', 'edu', 'ac']:
            return '.'.join(parts[-3:])
        return '.'.join(parts[-2:])
    return hostname


def query_crt_sh(domain, timeout=30):
    """Query crt.sh Certificate Transparency logs for subdomains"""
    if not httpx:
        return []
    
    subdomains = set()
    
    try:
        url = f"https://crt.sh/?q=%.{domain}&output=json"
        with httpx.Client(timeout=timeout, verify=False) as client:
            response = client.get(url)
            if response.status_code == 200:
                try:
                    data = response.json()
                    for cert in data:
                        # Get common_name
                        cn = cert.get('common_name', '')
                        if cn and domain in cn:
                            # Clean up wildcards and whitespace
                            cn = cn.replace('*.', '').strip().lower()
                            if cn.endswith(domain):
                                subdomains.add(cn)
                        
                        # Get name_value (can contain multiple domains)
                        nv = cert.get('name_value', '')
                        if nv:
                            for name in nv.split('\n'):
                                name = name.replace('*.', '').strip().lower()
                                if name and domain in name and name.endswith(domain):
                                    subdomains.add(name)
                except Exception:
                    pass
    except Exception as e:
        pass
    
    return list(subdomains)


def query_hackertarget(domain, timeout=15):
    """Query HackerTarget API for subdomains"""
    if not httpx:
        return []
    
    subdomains = set()
    
    try:
        url = f"https://api.hackertarget.com/hostsearch/?q={domain}"
        with httpx.Client(timeout=timeout, verify=False) as client:
            response = client.get(url)
            if response.status_code == 200 and 'error' not in response.text.lower():
                lines = response.text.strip().split('\n')
                for line in lines:
                    if ',' in line:
                        subdomain = line.split(',')[0].strip().lower()
                        if subdomain and domain in subdomain:
                            subdomains.add(subdomain)
    except Exception:
        pass
    
    return list(subdomains)


def query_threatcrowd(domain, timeout=15):
    """Query ThreatCrowd API for subdomains"""
    if not httpx:
        return []
    
    subdomains = set()
    
    try:
        url = f"https://www.threatcrowd.org/searchApi/v2/domain/report/?domain={domain}"
        with httpx.Client(timeout=timeout, verify=False) as client:
            response = client.get(url)
            if response.status_code == 200:
                data = response.json()
                subs = data.get('subdomains', [])
                for sub in subs:
                    sub = sub.strip().lower()
                    if sub and domain in sub:
                        subdomains.add(sub)
    except Exception:
        pass
    
    return list(subdomains)


def query_alienvault(domain, timeout=15):
    """Query AlienVault OTX for subdomains"""
    if not httpx:
        return []
    
    subdomains = set()
    
    try:
        url = f"https://otx.alienvault.com/api/v1/indicators/domain/{domain}/passive_dns"
        with httpx.Client(timeout=timeout, verify=False) as client:
            response = client.get(url)
            if response.status_code == 200:
                data = response.json()
                records = data.get('passive_dns', [])
                for record in records:
                    hostname = record.get('hostname', '').strip().lower()
                    if hostname and domain in hostname:
                        subdomains.add(hostname)
    except Exception:
        pass
    
    return list(subdomains)


def resolve_subdomain(subdomain, timeout=3):
    """Check if a subdomain resolves"""
    try:
        socket.setdefaulttimeout(timeout)
        result = socket.gethostbyname(subdomain)
        return {'subdomain': subdomain, 'ip': result, 'alive': True}
    except socket.gaierror:
        return {'subdomain': subdomain, 'ip': None, 'alive': False}
    except socket.timeout:
        return {'subdomain': subdomain, 'ip': None, 'alive': False, 'timeout': True}
    except Exception:
        return {'subdomain': subdomain, 'ip': None, 'alive': False}


def bruteforce_subdomains(domain, wordlist=None, max_workers=20, timeout=3):
    """Brute force subdomains using wordlist"""
    if wordlist is None:
        wordlist = COMMON_SUBDOMAINS
    
    alive_subdomains = []
    
    # Generate subdomain list
    candidates = [f"{word}.{domain}" for word in wordlist]
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(resolve_subdomain, sub, timeout): sub for sub in candidates}
        
        for future in as_completed(futures):
            result = future.result()
            if result['alive']:
                alive_subdomains.append(result)
    
    return alive_subdomains


def check_subdomain_http(subdomain, timeout=5):
    """Check if subdomain responds to HTTP/HTTPS"""
    if not httpx:
        return None
    
    result = {
        'subdomain': subdomain,
        'http': False,
        'https': False,
        'http_status': None,
        'https_status': None,
        'title': None,
        'server': None,
        'technologies': [],
    }
    
    with httpx.Client(timeout=timeout, verify=False, follow_redirects=True) as client:
        # Try HTTPS first
        try:
            response = client.get(f"https://{subdomain}")
            result['https'] = True
            result['https_status'] = response.status_code
            result['server'] = response.headers.get('server', '')
            
            # Extract title
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', response.text, re.I)
            if title_match:
                result['title'] = title_match.group(1).strip()[:100]
            
            # Detect technologies
            result['technologies'] = detect_technologies(response)
            
        except Exception:
            pass
        
        # Try HTTP
        try:
            response = client.get(f"http://{subdomain}")
            result['http'] = True
            result['http_status'] = response.status_code
            
            if not result['server']:
                result['server'] = response.headers.get('server', '')
            
            if not result['title']:
                title_match = re.search(r'<title[^>]*>([^<]+)</title>', response.text, re.I)
                if title_match:
                    result['title'] = title_match.group(1).strip()[:100]
            
            if not result['technologies']:
                result['technologies'] = detect_technologies(response)
                
        except Exception:
            pass
    
    return result if (result['http'] or result['https']) else None


def detect_technologies(response):
    """Basic technology detection from HTTP response"""
    technologies = []
    headers = response.headers
    body = response.text[:5000].lower() if hasattr(response, 'text') else ''
    
    # Server header
    server = headers.get('server', '').lower()
    if 'nginx' in server:
        technologies.append('nginx')
    if 'apache' in server:
        technologies.append('Apache')
    if 'iis' in server:
        technologies.append('IIS')
    if 'cloudflare' in server:
        technologies.append('Cloudflare')
    
    # X-Powered-By
    powered_by = headers.get('x-powered-by', '').lower()
    if 'php' in powered_by:
        technologies.append('PHP')
    if 'asp.net' in powered_by:
        technologies.append('ASP.NET')
    if 'express' in powered_by:
        technologies.append('Express')
    
    # Body detection
    if 'wp-content' in body or 'wordpress' in body:
        technologies.append('WordPress')
    if 'drupal' in body:
        technologies.append('Drupal')
    if 'joomla' in body:
        technologies.append('Joomla')
    if 'react' in body or 'reactjs' in body:
        technologies.append('React')
    if 'angular' in body:
        technologies.append('Angular')
    if 'vue' in body or 'vuejs' in body:
        technologies.append('Vue.js')
    
    return list(set(technologies))


def categorize_subdomain(subdomain, domain):
    """Categorize subdomain based on name patterns"""
    prefix = subdomain.replace(f'.{domain}', '').lower()
    
    categories = {
        'Development': ['dev', 'develop', 'development', 'test', 'testing', 'qa', 'uat', 'sandbox', 'staging', 'stage', 'stg', 'beta', 'alpha', 'demo'],
        'API': ['api', 'rest', 'graphql', 'ws', 'websocket', 'service', 'services', 'gateway'],
        'Admin': ['admin', 'administrator', 'panel', 'cpanel', 'whm', 'console', 'manage', 'backend', 'cms'],
        'Mail': ['mail', 'email', 'smtp', 'imap', 'pop', 'webmail', 'mx'],
        'Infrastructure': ['cdn', 'static', 'assets', 'media', 'images', 'files', 'storage', 'ftp'],
        'Database': ['db', 'database', 'mysql', 'postgres', 'mongo', 'redis', 'sql'],
        'Monitoring': ['monitor', 'status', 'health', 'logs', 'metrics', 'grafana', 'kibana'],
        'CI/CD': ['git', 'gitlab', 'jenkins', 'ci', 'build', 'deploy'],
        'Security': ['auth', 'login', 'sso', 'vpn', 'secure'],
        'Production': ['www', 'web', 'app', 'portal', 'dashboard'],
    }
    
    for category, keywords in categories.items():
        for keyword in keywords:
            if keyword in prefix:
                return category
    
    return 'Other'


def identify_subdomain_risks(subdomain_info):
    """Identify security risks in discovered subdomains"""
    risks = []
    subdomain = subdomain_info['subdomain'].lower()
    
    # Development/Staging exposed
    dev_keywords = ['dev', 'test', 'staging', 'stage', 'stg', 'qa', 'uat', 'sandbox', 'beta', 'alpha', 'demo', 'preprod']
    for kw in dev_keywords:
        if kw in subdomain:
            risks.append({
                'severity': 'High',
                'issue': f'Development/Staging environment exposed: {subdomain}',
                'recommendation': 'Restrict access to development environments'
            })
            break
    
    # Admin panels exposed
    admin_keywords = ['admin', 'administrator', 'panel', 'cpanel', 'whm', 'console', 'backend']
    for kw in admin_keywords:
        if kw in subdomain:
            risks.append({
                'severity': 'Medium',
                'issue': f'Admin panel potentially exposed: {subdomain}',
                'recommendation': 'Restrict admin panel access to internal networks'
            })
            break
    
    # Database interfaces exposed
    db_keywords = ['db', 'database', 'mysql', 'postgres', 'phpmyadmin', 'mongo', 'redis']
    for kw in db_keywords:
        if kw in subdomain:
            risks.append({
                'severity': 'Critical',
                'issue': f'Database interface potentially exposed: {subdomain}',
                'recommendation': 'Database interfaces should never be publicly accessible'
            })
            break
    
    # Git/CI exposed
    ci_keywords = ['git', 'gitlab', 'jenkins', 'ci', 'deploy', 'build']
    for kw in ci_keywords:
        if kw in subdomain:
            risks.append({
                'severity': 'High',
                'issue': f'CI/CD or source control exposed: {subdomain}',
                'recommendation': 'Restrict CI/CD systems to internal access'
            })
            break
    
    return risks


def enumerate_subdomains(url, deep_scan=False, bruteforce=True, max_results=200):
    """Main function - enumerate subdomains for a domain"""
    domain = extract_domain(url)
    
    result = {
        'domain': domain,
        'subdomains': [],
        'alive_subdomains': [],
        'http_info': [],
        'risks': [],
        'summary': {},
        'sources': [],
    }
    
    all_subdomains = set()
    
    # Query passive sources
    try:
        # crt.sh (Certificate Transparency)
        crt_results = query_crt_sh(domain)
        all_subdomains.update(crt_results)
        if crt_results:
            result['sources'].append({'source': 'crt.sh', 'count': len(crt_results)})
    except Exception:
        pass
    
    try:
        # HackerTarget
        ht_results = query_hackertarget(domain)
        all_subdomains.update(ht_results)
        if ht_results:
            result['sources'].append({'source': 'HackerTarget', 'count': len(ht_results)})
    except Exception:
        pass
    
    try:
        # AlienVault OTX
        av_results = query_alienvault(domain)
        all_subdomains.update(av_results)
        if av_results:
            result['sources'].append({'source': 'AlienVault', 'count': len(av_results)})
    except Exception:
        pass
    
    # Brute force common subdomains
    if bruteforce:
        wordlist = EXTENDED_SUBDOMAINS if deep_scan else COMMON_SUBDOMAINS
        brute_results = bruteforce_subdomains(domain, wordlist=wordlist, max_workers=15)
        for item in brute_results:
            all_subdomains.add(item['subdomain'])
        if brute_results:
            result['sources'].append({'source': 'Bruteforce', 'count': len(brute_results)})
            result['alive_subdomains'].extend(brute_results)
    
    # Remove duplicates and limit
    result['subdomains'] = sorted(list(all_subdomains))[:max_results]
    
    # Verify subdomains that weren't already verified by bruteforce
    verified_subs = {item['subdomain'] for item in result['alive_subdomains']}
    unverified = [s for s in result['subdomains'] if s not in verified_subs]
    
    # Resolve unverified subdomains
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(resolve_subdomain, sub): sub for sub in unverified[:100]}
        for future in as_completed(futures):
            res = future.result()
            if res['alive']:
                result['alive_subdomains'].append(res)
    
    # Check HTTP for alive subdomains
    alive_list = [item['subdomain'] for item in result['alive_subdomains'][:50]]
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(check_subdomain_http, sub): sub for sub in alive_list}
        for future in as_completed(futures):
            http_result = future.result()
            if http_result:
                result['http_info'].append(http_result)
    
    # Categorize and identify risks
    for sub_info in result['alive_subdomains']:
        sub_info['category'] = categorize_subdomain(sub_info['subdomain'], domain)
        risks = identify_subdomain_risks(sub_info)
        result['risks'].extend(risks)
    
    # Build summary
    categories = {}
    for sub_info in result['alive_subdomains']:
        cat = sub_info.get('category', 'Other')
        categories[cat] = categories.get(cat, 0) + 1
    
    result['summary'] = {
        'total_found': len(result['subdomains']),
        'alive': len(result['alive_subdomains']),
        'with_http': len(result['http_info']),
        'risk_count': len(result['risks']),
        'high_risk': len([r for r in result['risks'] if r['severity'] in ['Critical', 'High']]),
        'categories': categories,
        'sources_used': len(result['sources']),
    }
    
    return result
