# cloud_scanner.py
# Cloud Bucket Scanner - S3, Azure Blob, GCP Storage exposure detection

import re
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed

try:
    import httpx
except ImportError:
    httpx = None

# S3 bucket URL patterns
S3_PATTERNS = [
    r'https?://([a-zA-Z0-9\-\.]+)\.s3\.amazonaws\.com',
    r'https?://([a-zA-Z0-9\-\.]+)\.s3-([a-z0-9\-]+)\.amazonaws\.com',
    r'https?://s3\.amazonaws\.com/([a-zA-Z0-9\-\.]+)',
    r'https?://s3-([a-z0-9\-]+)\.amazonaws\.com/([a-zA-Z0-9\-\.]+)',
    r'https?://([a-zA-Z0-9\-\.]+)\.s3\.([a-z0-9\-]+)\.amazonaws\.com',
    r'arn:aws:s3:::([a-zA-Z0-9\-\.]+)',
]

# Azure Blob patterns
AZURE_PATTERNS = [
    r'https?://([a-zA-Z0-9\-]+)\.blob\.core\.windows\.net/([a-zA-Z0-9\-]+)',
    r'https?://([a-zA-Z0-9\-]+)\.blob\.core\.windows\.net',
    r'https?://([a-zA-Z0-9\-]+)\.file\.core\.windows\.net',
    r'https?://([a-zA-Z0-9\-]+)\.table\.core\.windows\.net',
    r'https?://([a-zA-Z0-9\-]+)\.queue\.core\.windows\.net',
    r'https?://([a-zA-Z0-9\-]+)\.dfs\.core\.windows\.net',
]

# GCP Storage patterns
GCP_PATTERNS = [
    r'https?://storage\.googleapis\.com/([a-zA-Z0-9\-\.]+)',
    r'https?://([a-zA-Z0-9\-\.]+)\.storage\.googleapis\.com',
    r'https?://storage\.cloud\.google\.com/([a-zA-Z0-9\-\.]+)',
    r'gs://([a-zA-Z0-9\-\.]+)',
]

# DigitalOcean Spaces patterns
DO_PATTERNS = [
    r'https?://([a-zA-Z0-9\-]+)\.([a-z0-9]+)\.digitaloceanspaces\.com',
    r'https?://([a-z0-9]+)\.digitaloceanspaces\.com/([a-zA-Z0-9\-]+)',
]

# Common bucket name patterns to generate
BUCKET_NAME_PATTERNS = [
    '{domain}',
    '{domain}-backup',
    '{domain}-backups',
    '{domain}-assets',
    '{domain}-static',
    '{domain}-media',
    '{domain}-uploads',
    '{domain}-files',
    '{domain}-data',
    '{domain}-logs',
    '{domain}-dev',
    '{domain}-staging',
    '{domain}-prod',
    '{domain}-production',
    '{domain}-test',
    '{domain}-storage',
    '{domain}-cdn',
    '{domain}-images',
    '{domain}-public',
    '{domain}-private',
    'backup-{domain}',
    'backups-{domain}',
    'assets-{domain}',
    'static-{domain}',
    'media-{domain}',
    'uploads-{domain}',
    'files-{domain}',
    'data-{domain}',
    'www-{domain}',
    'web-{domain}',
    'app-{domain}',
    'api-{domain}',
]


def extract_domain_name(url):
    """Extract clean domain name for bucket generation"""
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    parsed = urlparse(url)
    hostname = parsed.netloc.split(':')[0]
    
    # Remove www and TLD
    parts = hostname.split('.')
    if parts[0] == 'www':
        parts = parts[1:]
    
    # Get main domain name (without TLD)
    if len(parts) >= 2:
        return parts[0]
    return hostname


def find_buckets_in_content(content):
    """Find cloud bucket references in HTML/JS content"""
    buckets = {
        's3': [],
        'azure': [],
        'gcp': [],
        'digitalocean': [],
    }
    
    # S3 buckets
    for pattern in S3_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                bucket = match[0] if match[0] else match[1] if len(match) > 1 else None
            else:
                bucket = match
            if bucket and bucket not in buckets['s3']:
                buckets['s3'].append(bucket)
    
    # Azure blobs
    for pattern in AZURE_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                storage_account = match[0]
                container = match[1] if len(match) > 1 else None
                bucket_id = f"{storage_account}/{container}" if container else storage_account
            else:
                bucket_id = match
            if bucket_id and bucket_id not in buckets['azure']:
                buckets['azure'].append(bucket_id)
    
    # GCP buckets
    for pattern in GCP_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            bucket = match if isinstance(match, str) else match[0] if match else None
            if bucket and bucket not in buckets['gcp']:
                buckets['gcp'].append(bucket)
    
    # DigitalOcean Spaces
    for pattern in DO_PATTERNS:
        matches = re.findall(pattern, content, re.IGNORECASE)
        for match in matches:
            if isinstance(match, tuple):
                bucket = f"{match[0]}.{match[1]}" if len(match) > 1 else match[0]
            else:
                bucket = match
            if bucket and bucket not in buckets['digitalocean']:
                buckets['digitalocean'].append(bucket)
    
    return buckets


def check_s3_bucket(bucket_name, timeout=10):
    """Check S3 bucket for public access"""
    if not httpx:
        return None
    
    result = {
        'bucket': bucket_name,
        'provider': 's3',
        'exists': False,
        'public_read': False,
        'public_list': False,
        'url': f"https://{bucket_name}.s3.amazonaws.com",
        'issues': [],
    }
    
    urls_to_try = [
        f"https://{bucket_name}.s3.amazonaws.com",
        f"https://s3.amazonaws.com/{bucket_name}",
    ]
    
    with httpx.Client(timeout=timeout, verify=False) as client:
        for url in urls_to_try:
            try:
                response = client.get(url)
                
                if response.status_code == 200:
                    result['exists'] = True
                    result['url'] = url
                    
                    # Check if listing is enabled
                    if '<ListBucketResult' in response.text or '<Contents>' in response.text:
                        result['public_list'] = True
                        result['issues'].append({
                            'severity': 'Critical',
                            'issue': f'S3 bucket allows public listing: {bucket_name}',
                            'recommendation': 'Disable public bucket listing immediately'
                        })
                    
                    result['public_read'] = True
                    result['issues'].append({
                        'severity': 'High',
                        'issue': f'S3 bucket is publicly accessible: {bucket_name}',
                        'recommendation': 'Review bucket permissions and restrict access'
                    })
                    break
                    
                elif response.status_code == 403:
                    result['exists'] = True
                    result['url'] = url
                    # Bucket exists but access denied - still exposed
                    break
                    
                elif response.status_code == 404:
                    # Bucket doesn't exist
                    pass
                    
            except Exception:
                continue
    
    return result if result['exists'] else None


def check_azure_blob(storage_account, container=None, timeout=10):
    """Check Azure Blob Storage for public access"""
    if not httpx:
        return None
    
    result = {
        'bucket': f"{storage_account}/{container}" if container else storage_account,
        'provider': 'azure',
        'exists': False,
        'public_read': False,
        'public_list': False,
        'url': None,
        'issues': [],
    }
    
    if container:
        urls_to_try = [
            f"https://{storage_account}.blob.core.windows.net/{container}?restype=container&comp=list",
            f"https://{storage_account}.blob.core.windows.net/{container}",
        ]
    else:
        urls_to_try = [
            f"https://{storage_account}.blob.core.windows.net/$root?restype=container&comp=list",
        ]
    
    with httpx.Client(timeout=timeout, verify=False) as client:
        for url in urls_to_try:
            try:
                response = client.get(url)
                
                if response.status_code == 200:
                    result['exists'] = True
                    result['url'] = url.split('?')[0]
                    
                    # Check if listing is enabled
                    if '<EnumerationResults' in response.text or '<Blobs>' in response.text:
                        result['public_list'] = True
                        result['issues'].append({
                            'severity': 'Critical',
                            'issue': f'Azure container allows public listing: {result["bucket"]}',
                            'recommendation': 'Disable public container listing'
                        })
                    
                    result['public_read'] = True
                    result['issues'].append({
                        'severity': 'High',
                        'issue': f'Azure storage is publicly accessible: {result["bucket"]}',
                        'recommendation': 'Review storage permissions'
                    })
                    break
                    
                elif response.status_code in [403, 404]:
                    # Exists but not publicly accessible
                    result['exists'] = True if response.status_code == 403 else False
                    break
                    
            except Exception:
                continue
    
    return result if result['exists'] else None


def check_gcp_bucket(bucket_name, timeout=10):
    """Check GCP Storage bucket for public access"""
    if not httpx:
        return None
    
    result = {
        'bucket': bucket_name,
        'provider': 'gcp',
        'exists': False,
        'public_read': False,
        'public_list': False,
        'url': f"https://storage.googleapis.com/{bucket_name}",
        'issues': [],
    }
    
    urls_to_try = [
        f"https://storage.googleapis.com/{bucket_name}",
        f"https://{bucket_name}.storage.googleapis.com",
    ]
    
    with httpx.Client(timeout=timeout, verify=False) as client:
        for url in urls_to_try:
            try:
                response = client.get(url)
                
                if response.status_code == 200:
                    result['exists'] = True
                    result['url'] = url
                    
                    # Check if listing
                    if '<ListBucketResult' in response.text or '<Contents>' in response.text:
                        result['public_list'] = True
                        result['issues'].append({
                            'severity': 'Critical',
                            'issue': f'GCP bucket allows public listing: {bucket_name}',
                            'recommendation': 'Disable public bucket listing'
                        })
                    
                    result['public_read'] = True
                    result['issues'].append({
                        'severity': 'High',
                        'issue': f'GCP bucket is publicly accessible: {bucket_name}',
                        'recommendation': 'Review bucket permissions'
                    })
                    break
                    
                elif response.status_code == 403:
                    result['exists'] = True
                    break
                    
            except Exception:
                continue
    
    return result if result['exists'] else None


def check_do_space(space_name, region, timeout=10):
    """Check DigitalOcean Space for public access"""
    if not httpx:
        return None
    
    result = {
        'bucket': f"{space_name}.{region}",
        'provider': 'digitalocean',
        'exists': False,
        'public_read': False,
        'public_list': False,
        'url': f"https://{space_name}.{region}.digitaloceanspaces.com",
        'issues': [],
    }
    
    try:
        with httpx.Client(timeout=timeout, verify=False) as client:
            response = client.get(result['url'])
            
            if response.status_code == 200:
                result['exists'] = True
                
                if '<ListBucketResult' in response.text:
                    result['public_list'] = True
                    result['issues'].append({
                        'severity': 'Critical',
                        'issue': f'DO Space allows public listing: {result["bucket"]}',
                        'recommendation': 'Disable public listing'
                    })
                
                result['public_read'] = True
                result['issues'].append({
                    'severity': 'High',
                    'issue': f'DO Space is publicly accessible: {result["bucket"]}',
                    'recommendation': 'Review Space permissions'
                })
                
            elif response.status_code == 403:
                result['exists'] = True
                
    except Exception:
        pass
    
    return result if result['exists'] else None


def generate_bucket_names(domain):
    """Generate potential bucket names based on domain"""
    domain_name = extract_domain_name(domain)
    
    buckets = []
    for pattern in BUCKET_NAME_PATTERNS:
        bucket_name = pattern.format(domain=domain_name)
        buckets.append(bucket_name)
        # Also try with dots replaced by dashes
        buckets.append(bucket_name.replace('.', '-'))
    
    # Remove duplicates while preserving order
    seen = set()
    unique_buckets = []
    for b in buckets:
        if b not in seen:
            seen.add(b)
            unique_buckets.append(b)
    
    return unique_buckets


def brute_force_buckets(domain, providers=None, max_workers=10, timeout=10):
    """Brute force common bucket names"""
    if providers is None:
        providers = ['s3', 'gcp']  # Azure requires container name
    
    bucket_names = generate_bucket_names(domain)
    found_buckets = []
    
    def check_bucket(bucket_name, provider):
        if provider == 's3':
            return check_s3_bucket(bucket_name, timeout)
        elif provider == 'gcp':
            return check_gcp_bucket(bucket_name, timeout)
        return None
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = []
        for bucket_name in bucket_names:
            for provider in providers:
                futures.append(executor.submit(check_bucket, bucket_name, provider))
        
        for future in as_completed(futures):
            result = future.result()
            if result:
                found_buckets.append(result)
    
    return found_buckets


def scan_cloud_resources(url, content=None, brute_force=True):
    """Main function - scan for cloud storage exposure"""
    result = {
        'url': url,
        'found_buckets': [],
        'referenced_buckets': {'s3': [], 'azure': [], 'gcp': [], 'digitalocean': []},
        'exposed_buckets': [],
        'issues': [],
        'summary': {}
    }
    
    # If content provided, search for bucket references
    if content:
        result['referenced_buckets'] = find_buckets_in_content(content)
        
        # Check each referenced bucket
        for bucket in result['referenced_buckets']['s3']:
            bucket_result = check_s3_bucket(bucket)
            if bucket_result:
                result['found_buckets'].append(bucket_result)
                if bucket_result['public_read']:
                    result['exposed_buckets'].append(bucket_result)
                    result['issues'].extend(bucket_result.get('issues', []))
        
        for bucket in result['referenced_buckets']['gcp']:
            bucket_result = check_gcp_bucket(bucket)
            if bucket_result:
                result['found_buckets'].append(bucket_result)
                if bucket_result['public_read']:
                    result['exposed_buckets'].append(bucket_result)
                    result['issues'].extend(bucket_result.get('issues', []))
        
        for bucket_id in result['referenced_buckets']['azure']:
            parts = bucket_id.split('/')
            storage_account = parts[0]
            container = parts[1] if len(parts) > 1 else None
            bucket_result = check_azure_blob(storage_account, container)
            if bucket_result:
                result['found_buckets'].append(bucket_result)
                if bucket_result['public_read']:
                    result['exposed_buckets'].append(bucket_result)
                    result['issues'].extend(bucket_result.get('issues', []))
    
    # Brute force common bucket names
    if brute_force:
        brute_results = brute_force_buckets(url, max_workers=15)
        for bucket_result in brute_results:
            # Avoid duplicates
            bucket_id = bucket_result['bucket']
            if not any(b['bucket'] == bucket_id for b in result['found_buckets']):
                result['found_buckets'].append(bucket_result)
                if bucket_result['public_read']:
                    result['exposed_buckets'].append(bucket_result)
                    result['issues'].extend(bucket_result.get('issues', []))
    
    # Build summary
    result['summary'] = {
        'buckets_found': len(result['found_buckets']),
        'buckets_exposed': len(result['exposed_buckets']),
        'buckets_with_listing': len([b for b in result['exposed_buckets'] if b.get('public_list')]),
        's3_count': len([b for b in result['found_buckets'] if b['provider'] == 's3']),
        'azure_count': len([b for b in result['found_buckets'] if b['provider'] == 'azure']),
        'gcp_count': len([b for b in result['found_buckets'] if b['provider'] == 'gcp']),
        'do_count': len([b for b in result['found_buckets'] if b['provider'] == 'digitalocean']),
        'critical_issues': len([i for i in result['issues'] if i['severity'] == 'Critical']),
        'issue_count': len(result['issues']),
    }
    
    return result
