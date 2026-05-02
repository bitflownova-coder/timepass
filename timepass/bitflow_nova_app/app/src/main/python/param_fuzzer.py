# param_fuzzer.py
# Parameter Discovery - Fuzzing for hidden GET/POST parameters

import re
from urllib.parse import urljoin, urlparse, parse_qs, urlencode

try:
    import httpx
except ImportError:
    httpx = None

# Common parameter names to fuzz
COMMON_PARAMS = [
    # Authentication & Authorization
    'id', 'user_id', 'uid', 'userid', 'user', 'username', 'login', 'email',
    'password', 'pass', 'pwd', 'passwd', 'secret', 'token', 'auth', 'api_key',
    'apikey', 'key', 'access_token', 'refresh_token', 'session', 'sid',
    'jwt', 'bearer', 'oauth_token',
    
    # Common identifiers
    'id', 'ID', 'Id', 'item_id', 'product_id', 'order_id', 'customer_id',
    'account_id', 'acc', 'account', 'pid', 'oid', 'cid', 'ref', 'reference',
    'uuid', 'guid', 'hash', 'code', 'slug',
    
    # Pagination & Filtering
    'page', 'p', 'pg', 'pagenum', 'page_num', 'offset', 'start', 'limit',
    'count', 'size', 'per_page', 'perpage', 'items', 'max', 'num',
    'sort', 'order', 'orderby', 'order_by', 'sortby', 'sort_by', 'dir',
    'asc', 'desc', 'filter', 'filters', 'search', 'q', 'query', 'keyword',
    
    # Actions & Operations
    'action', 'act', 'do', 'cmd', 'command', 'op', 'operation', 'func',
    'function', 'method', 'mode', 'type', 'task', 'step', 'state', 'status',
    
    # Content & Data
    'data', 'content', 'body', 'text', 'message', 'msg', 'comment', 'note',
    'title', 'name', 'description', 'desc', 'value', 'val', 'input', 'output',
    
    # Files & Paths
    'file', 'filename', 'filepath', 'path', 'dir', 'directory', 'folder',
    'doc', 'document', 'image', 'img', 'photo', 'video', 'media', 'attachment',
    'download', 'upload', 'url', 'uri', 'link', 'src', 'source', 'dest',
    'destination', 'target', 'template', 'view', 'layout', 'include',
    
    # URLs & Redirects
    'redirect', 'redirect_uri', 'redirect_url', 'return', 'return_url',
    'returnto', 'return_to', 'goto', 'next', 'continue', 'back', 'callback',
    'callback_url', 'forward', 'redir', 'location',
    
    # Debug & Admin
    'debug', 'test', 'admin', 'administrator', 'root', 'dev', 'development',
    'preview', 'draft', 'internal', 'verbose', 'trace', 'log', 'logging',
    
    # Format & Response
    'format', 'fmt', 'output', 'response', 'encoding', 'charset', 'lang',
    'language', 'locale', 'json', 'xml', 'html', 'raw', 'pretty',
    
    # Security related
    'csrf', 'csrf_token', 'xsrf', 'nonce', 'captcha', '_token', '__token',
    'authenticity_token', 'verify', 'signature', 'sig', 'sign', 'checksum',
    
    # Hidden/Debug parameters
    '_', '__', 'hidden', 'private', 'restricted', 'bypass', 'override',
    'force', 'skip', 'ignore', 'disable', 'enable', 'flag', 'flags',
]

# Sensitive parameter patterns
SENSITIVE_PATTERNS = [
    r'.*password.*', r'.*passwd.*', r'.*pwd.*', r'.*secret.*',
    r'.*token.*', r'.*key.*', r'.*auth.*', r'.*credential.*',
    r'.*session.*', r'.*cookie.*', r'.*admin.*', r'.*root.*',
    r'.*debug.*', r'.*test.*', r'.*bypass.*', r'.*override.*',
]

# Test values for different parameter types
TEST_VALUES = {
    'numeric': ['1', '0', '-1', '999999', '2147483647'],
    'string': ['test', 'admin', 'debug', "test'test", '${7*7}'],
    'boolean': ['true', 'false', '1', '0', 'yes', 'no'],
    'special': ['null', 'undefined', 'none', '[]', '{}', '../'],
}


def classify_parameter(name):
    """Classify parameter based on name"""
    name_lower = name.lower()
    
    if any(x in name_lower for x in ['id', 'num', 'count', 'page', 'limit', 'offset', 'size']):
        return 'numeric'
    elif any(x in name_lower for x in ['debug', 'test', 'enable', 'disable', 'flag', 'active']):
        return 'boolean'
    elif any(x in name_lower for x in ['url', 'redirect', 'path', 'file', 'uri']):
        return 'url'
    else:
        return 'string'


def is_sensitive_param(name):
    """Check if parameter name looks sensitive"""
    name_lower = name.lower()
    for pattern in SENSITIVE_PATTERNS:
        if re.match(pattern, name_lower):
            return True
    return False


def get_baseline_response(url, timeout=10):
    """Get baseline response for comparison"""
    if not httpx:
        return None
    
    try:
        with httpx.Client(timeout=timeout, verify=False, follow_redirects=True) as client:
            response = client.get(url)
            return {
                'status': response.status_code,
                'length': len(response.content),
                'headers': dict(response.headers),
                'word_count': len(response.text.split()),
                'text_sample': response.text[:500],
            }
    except Exception:
        return None


def compare_responses(baseline, current):
    """Compare two responses to detect differences"""
    if not baseline or not current:
        return {'is_different': False}
    
    differences = {
        'is_different': False,
        'status_changed': baseline['status'] != current['status'],
        'size_changed': abs(baseline['length'] - current['length']) > 50,
        'word_count_changed': abs(baseline.get('word_count', 0) - current.get('word_count', 0)) > 10,
    }
    
    # Consider response different if status changed or significant size difference
    if differences['status_changed'] or differences['size_changed']:
        differences['is_different'] = True
    
    return differences


def fuzz_url_parameters(url, params_to_test=None, timeout=10):
    """Fuzz URL with different parameter names and values"""
    if not httpx:
        return {'error': 'httpx not available'}
    
    if params_to_test is None:
        params_to_test = COMMON_PARAMS
    
    results = {
        'url': url,
        'discovered_params': [],
        'reflected_params': [],
        'sensitive_params': [],
        'hidden_params': [],
        'debug_params': [],
        'issues': [],
    }
    
    # Get baseline response
    baseline = get_baseline_response(url, timeout)
    if not baseline:
        return results
    
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
    existing_params = parse_qs(parsed.query)
    
    with httpx.Client(timeout=timeout, verify=False, follow_redirects=True) as client:
        for param in params_to_test:
            if param in existing_params:
                continue
            
            # Get test value based on parameter type
            param_type = classify_parameter(param)
            test_value = TEST_VALUES[param_type][0] if param_type in TEST_VALUES else 'test123'
            
            # Add canary value for reflection detection
            canary = f"xyzzy{param}canary"
            
            # Build test URL
            test_params = dict(existing_params)
            test_params[param] = [canary]
            query_string = urlencode(test_params, doseq=True)
            test_url = f"{base_url}?{query_string}" if query_string else base_url
            
            try:
                response = client.get(test_url)
                current = {
                    'status': response.status_code,
                    'length': len(response.content),
                    'word_count': len(response.text.split()),
                    'text': response.text,
                }
                
                # Check for differences
                diff = compare_responses(baseline, current)
                
                param_info = {
                    'name': param,
                    'type': param_type,
                    'status': current['status'],
                    'response_different': diff['is_different'],
                    'reflected': canary in current['text'],
                    'is_sensitive': is_sensitive_param(param),
                }
                
                # Parameter affects response
                if diff['is_different']:
                    results['discovered_params'].append(param_info)
                    
                    # Check for debug/hidden functionality
                    if any(x in param.lower() for x in ['debug', 'test', 'admin', 'bypass', 'hidden']):
                        results['debug_params'].append(param_info)
                        results['issues'].append({
                            'severity': 'High',
                            'issue': f'Hidden/debug parameter discovered: {param}',
                            'recommendation': 'Remove debug parameters in production'
                        })
                
                # Reflection detected (potential XSS)
                if canary in current['text']:
                    results['reflected_params'].append(param_info)
                    results['issues'].append({
                        'severity': 'Medium',
                        'issue': f'Parameter "{param}" is reflected in response',
                        'recommendation': 'Ensure proper output encoding'
                    })
                
                # Sensitive parameter discovered
                if param_info['is_sensitive'] and diff['is_different']:
                    results['sensitive_params'].append(param_info)
                    results['issues'].append({
                        'severity': 'High',
                        'issue': f'Sensitive parameter discovered: {param}',
                        'recommendation': 'Review access controls for this parameter'
                    })
                    
            except Exception:
                continue
    
    return results


def fuzz_post_parameters(url, params_to_test=None, timeout=10):
    """Fuzz POST parameters"""
    if not httpx:
        return {'error': 'httpx not available'}
    
    if params_to_test is None:
        params_to_test = COMMON_PARAMS[:50]  # Limit for POST
    
    results = {
        'url': url,
        'discovered_params': [],
        'reflected_params': [],
        'sensitive_params': [],
        'issues': [],
    }
    
    # Get baseline (empty POST)
    with httpx.Client(timeout=timeout, verify=False, follow_redirects=True) as client:
        try:
            baseline_response = client.post(url, data={})
            baseline = {
                'status': baseline_response.status_code,
                'length': len(baseline_response.content),
                'text': baseline_response.text,
            }
        except Exception:
            return results
        
        for param in params_to_test:
            param_type = classify_parameter(param)
            canary = f"xyzzy{param}canary"
            
            try:
                response = client.post(url, data={param: canary})
                current = {
                    'status': response.status_code,
                    'length': len(response.content),
                    'text': response.text,
                }
                
                diff = compare_responses(baseline, current)
                
                param_info = {
                    'name': param,
                    'type': param_type,
                    'method': 'POST',
                    'status': current['status'],
                    'response_different': diff['is_different'],
                    'reflected': canary in current['text'],
                    'is_sensitive': is_sensitive_param(param),
                }
                
                if diff['is_different'] or canary in current['text']:
                    results['discovered_params'].append(param_info)
                    
                    if canary in current['text']:
                        results['reflected_params'].append(param_info)
                    
                    if param_info['is_sensitive']:
                        results['sensitive_params'].append(param_info)
                        
            except Exception:
                continue
    
    return results


def analyze_existing_params(url, found_params=None):
    """Analyze existing parameters in URLs for issues"""
    issues = []
    
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    
    for param_name, values in params.items():
        # Check for sensitive data in URL
        if is_sensitive_param(param_name):
            issues.append({
                'severity': 'Medium',
                'param': param_name,
                'issue': f'Potentially sensitive parameter in URL: {param_name}',
                'recommendation': 'Consider using POST for sensitive data'
            })
        
        # Check for potential SQL injection patterns
        for value in values:
            if any(x in value for x in ["'", '"', '--', ';', 'OR 1=1', 'UNION']):
                issues.append({
                    'severity': 'High',
                    'param': param_name,
                    'issue': f'Suspicious value in parameter: {param_name}',
                    'value': value[:50],
                    'recommendation': 'Review for SQL injection'
                })
            
            # Check for path traversal
            if '../' in value or '..\\' in value:
                issues.append({
                    'severity': 'High',
                    'param': param_name,
                    'issue': f'Path traversal pattern in parameter: {param_name}',
                    'recommendation': 'Review for path traversal vulnerability'
                })
            
            # Check for SSRF-like URLs
            if value.startswith(('http://', 'https://', 'file://', 'ftp://')):
                issues.append({
                    'severity': 'Medium',
                    'param': param_name,
                    'issue': f'URL value in parameter: {param_name}',
                    'recommendation': 'Review for SSRF vulnerability'
                })
    
    return issues


def discover_parameters(url, deep_scan=False):
    """Main function - comprehensive parameter discovery"""
    result = {
        'url': url,
        'get_params': {},
        'post_params': {},
        'existing_params_analysis': [],
        'discovered': [],
        'reflected': [],
        'sensitive': [],
        'debug': [],
        'issues': [],
        'summary': {}
    }
    
    try:
        # Analyze existing parameters
        result['existing_params_analysis'] = analyze_existing_params(url)
        result['issues'].extend(result['existing_params_analysis'])
        
        # Fuzz GET parameters
        params_count = 100 if deep_scan else 50
        get_results = fuzz_url_parameters(url, COMMON_PARAMS[:params_count])
        result['get_params'] = get_results
        
        result['discovered'].extend(get_results.get('discovered_params', []))
        result['reflected'].extend(get_results.get('reflected_params', []))
        result['sensitive'].extend(get_results.get('sensitive_params', []))
        result['debug'].extend(get_results.get('debug_params', []))
        result['issues'].extend(get_results.get('issues', []))
        
        # Fuzz POST parameters (if deep scan)
        if deep_scan:
            post_results = fuzz_post_parameters(url, COMMON_PARAMS[:30])
            result['post_params'] = post_results
            
            result['discovered'].extend(post_results.get('discovered_params', []))
            result['reflected'].extend(post_results.get('reflected_params', []))
            result['sensitive'].extend(post_results.get('sensitive_params', []))
            result['issues'].extend(post_results.get('issues', []))
        
        # Build summary
        result['summary'] = {
            'get_discovered': len(get_results.get('discovered_params', [])),
            'get_reflected': len(get_results.get('reflected_params', [])),
            'post_discovered': len(result['post_params'].get('discovered_params', [])) if deep_scan else 0,
            'total_discovered': len(result['discovered']),
            'total_reflected': len(result['reflected']),
            'sensitive_found': len(result['sensitive']),
            'debug_found': len(result['debug']),
            'issues_found': len(result['issues']),
        }
        
    except Exception as e:
        result['error'] = str(e)
    
    return result

# Alias for compatibility with import in crawler_engine.py
fuzz_parameters = discover_parameters
