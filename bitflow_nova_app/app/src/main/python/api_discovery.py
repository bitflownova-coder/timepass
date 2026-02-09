# api_discovery.py
# API Endpoint Discovery - Swagger/OpenAPI, GraphQL Introspection, REST detection

import re
import json
from urllib.parse import urljoin, urlparse

try:
    import httpx
except ImportError:
    httpx = None

# Common API documentation paths
SWAGGER_PATHS = [
    '/swagger.json',
    '/swagger/v1/swagger.json',
    '/swagger/v2/swagger.json',
    '/swagger-ui.html',
    '/swagger-ui/',
    '/swagger-ui/index.html',
    '/swagger/index.html',
    '/api-docs',
    '/api-docs.json',
    '/api/swagger.json',
    '/api/v1/swagger.json',
    '/api/v2/swagger.json',
    '/v1/swagger.json',
    '/v2/swagger.json',
    '/v3/swagger.json',
    '/docs',
    '/docs/',
    '/documentation',
    '/redoc',
    '/redoc/',
    '/rapidoc',
]

OPENAPI_PATHS = [
    '/openapi.json',
    '/openapi.yaml',
    '/openapi/v3/api-docs',
    '/api/openapi.json',
    '/api/openapi.yaml',
    '/v3/api-docs',
    '/api/v3/api-docs',
]

GRAPHQL_PATHS = [
    '/graphql',
    '/graphql/',
    '/api/graphql',
    '/v1/graphql',
    '/gql',
    '/query',
    '/graphiql',
    '/graphql/console',
    '/playground',
    '/graphql-playground',
    '/__graphql',
]

# Common REST API paths
REST_PATHS = [
    '/api',
    '/api/',
    '/api/v1',
    '/api/v1/',
    '/api/v2',
    '/api/v2/',
    '/api/v3',
    '/rest',
    '/rest/',
    '/rest/v1',
    '/rest/v2',
    '/services',
    '/ws',
    '/json',
    '/xml',
    '/rpc',
    '/jsonrpc',
]

# GraphQL introspection query
GRAPHQL_INTROSPECTION_QUERY = '''
query IntrospectionQuery {
  __schema {
    queryType { name }
    mutationType { name }
    subscriptionType { name }
    types {
      kind
      name
      description
      fields(includeDeprecated: true) {
        name
        description
        args {
          name
          description
          type {
            kind
            name
            ofType {
              kind
              name
            }
          }
        }
        type {
          kind
          name
          ofType {
            kind
            name
          }
        }
        isDeprecated
        deprecationReason
      }
    }
    directives {
      name
      description
    }
  }
}
'''

# Simplified introspection for basic info
GRAPHQL_SIMPLE_INTROSPECTION = '''
{
  __schema {
    queryType { name }
    mutationType { name }
    types {
      name
      kind
    }
  }
}
'''


def check_url_exists(url, timeout=10):
    """Check if URL exists and return response info"""
    if not httpx:
        return None
    
    try:
        with httpx.Client(timeout=timeout, verify=False, follow_redirects=True) as client:
            response = client.get(url)
            if response.status_code in [200, 201, 301, 302, 401, 403]:
                content_type = response.headers.get('content-type', '').lower()
                return {
                    'url': url,
                    'status': response.status_code,
                    'content_type': content_type,
                    'size': len(response.content),
                    'headers': dict(response.headers),
                }
    except Exception:
        pass
    return None


def discover_swagger(base_url, timeout=10):
    """Discover Swagger/OpenAPI documentation"""
    if not httpx:
        return []
    
    findings = []
    
    all_paths = SWAGGER_PATHS + OPENAPI_PATHS
    
    for path in all_paths:
        url = urljoin(base_url, path)
        result = check_url_exists(url, timeout)
        
        if result and result['status'] == 200:
            # Try to parse as JSON
            spec = None
            try:
                with httpx.Client(timeout=timeout, verify=False) as client:
                    response = client.get(url)
                    if 'json' in result['content_type'] or path.endswith('.json'):
                        spec = response.json()
            except Exception:
                pass
            
            finding = {
                'type': 'swagger' if 'swagger' in path else 'openapi',
                'url': url,
                'status': result['status'],
                'content_type': result['content_type'],
                'spec': None,
                'endpoints': [],
                'info': {},
                'security': [],
            }
            
            if spec:
                finding['spec'] = True
                
                # Parse OpenAPI/Swagger spec
                parsed = parse_openapi_spec(spec)
                finding['endpoints'] = parsed.get('endpoints', [])
                finding['info'] = parsed.get('info', {})
                finding['security'] = parsed.get('security', [])
                finding['version'] = parsed.get('version', 'Unknown')
            
            findings.append(finding)
    
    return findings


def parse_openapi_spec(spec):
    """Parse OpenAPI/Swagger specification"""
    result = {
        'version': spec.get('openapi') or spec.get('swagger', 'Unknown'),
        'info': spec.get('info', {}),
        'endpoints': [],
        'security': [],
        'servers': [],
    }
    
    # Get servers (OpenAPI 3.x)
    servers = spec.get('servers', [])
    result['servers'] = [s.get('url', '') for s in servers]
    
    # Get host (Swagger 2.x)
    if 'host' in spec:
        base_path = spec.get('basePath', '')
        schemes = spec.get('schemes', ['https'])
        for scheme in schemes:
            result['servers'].append(f"{scheme}://{spec['host']}{base_path}")
    
    # Parse paths
    paths = spec.get('paths', {})
    for path, methods in paths.items():
        for method, details in methods.items():
            if method.lower() in ['get', 'post', 'put', 'delete', 'patch', 'options', 'head']:
                endpoint = {
                    'path': path,
                    'method': method.upper(),
                    'summary': details.get('summary', ''),
                    'description': details.get('description', ''),
                    'parameters': [],
                    'security': details.get('security', []),
                    'tags': details.get('tags', []),
                    'deprecated': details.get('deprecated', False),
                }
                
                # Parse parameters
                params = details.get('parameters', [])
                for param in params:
                    endpoint['parameters'].append({
                        'name': param.get('name', ''),
                        'in': param.get('in', ''),  # query, path, header, body
                        'required': param.get('required', False),
                        'type': param.get('type') or param.get('schema', {}).get('type', ''),
                    })
                
                # Check request body (OpenAPI 3.x)
                request_body = details.get('requestBody', {})
                if request_body:
                    content = request_body.get('content', {})
                    for content_type, schema_info in content.items():
                        endpoint['parameters'].append({
                            'name': 'body',
                            'in': 'body',
                            'required': request_body.get('required', False),
                            'content_type': content_type,
                        })
                
                result['endpoints'].append(endpoint)
    
    # Parse security definitions
    security_defs = spec.get('securityDefinitions') or spec.get('components', {}).get('securitySchemes', {})
    for name, definition in security_defs.items():
        result['security'].append({
            'name': name,
            'type': definition.get('type', ''),
            'scheme': definition.get('scheme', ''),
            'in': definition.get('in', ''),
        })
    
    return result


def discover_graphql(base_url, timeout=15):
    """Discover and introspect GraphQL endpoints"""
    if not httpx:
        return []
    
    findings = []
    
    for path in GRAPHQL_PATHS:
        url = urljoin(base_url, path)
        
        # Try OPTIONS/GET first to check if endpoint exists
        try:
            with httpx.Client(timeout=timeout, verify=False) as client:
                # Try GET with introspection
                response = client.get(url, params={'query': GRAPHQL_SIMPLE_INTROSPECTION})
                
                if response.status_code in [200, 400]:  # 400 might mean valid endpoint, bad query
                    finding = {
                        'type': 'graphql',
                        'url': url,
                        'status': response.status_code,
                        'introspection_enabled': False,
                        'schema': None,
                        'types': [],
                        'queries': [],
                        'mutations': [],
                        'issues': [],
                    }
                    
                    # Try introspection via POST
                    introspection_result = introspect_graphql(url, client)
                    if introspection_result:
                        finding['introspection_enabled'] = True
                        finding['schema'] = introspection_result
                        finding['types'] = introspection_result.get('types', [])
                        finding['queries'] = introspection_result.get('queries', [])
                        finding['mutations'] = introspection_result.get('mutations', [])
                        finding['issues'].append({
                            'severity': 'Medium',
                            'issue': 'GraphQL introspection is enabled',
                            'recommendation': 'Disable introspection in production'
                        })
                    
                    # Check for GraphiQL/Playground
                    if 'graphiql' in response.text.lower() or 'playground' in response.text.lower():
                        finding['issues'].append({
                            'severity': 'Low',
                            'issue': 'GraphQL IDE (GraphiQL/Playground) is accessible',
                            'recommendation': 'Disable GraphQL IDE in production'
                        })
                    
                    findings.append(finding)
                    break  # Found GraphQL endpoint
                    
        except Exception:
            pass
    
    return findings


def introspect_graphql(url, client=None):
    """Perform GraphQL introspection query"""
    if not httpx:
        return None
    
    should_close = False
    if client is None:
        client = httpx.Client(timeout=15, verify=False)
        should_close = True
    
    try:
        # Try POST with JSON body
        response = client.post(
            url,
            json={'query': GRAPHQL_INTROSPECTION_QUERY},
            headers={'Content-Type': 'application/json'}
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and '__schema' in data['data']:
                schema = data['data']['__schema']
                
                result = {
                    'query_type': schema.get('queryType', {}).get('name'),
                    'mutation_type': schema.get('mutationType', {}).get('name') if schema.get('mutationType') else None,
                    'subscription_type': schema.get('subscriptionType', {}).get('name') if schema.get('subscriptionType') else None,
                    'types': [],
                    'queries': [],
                    'mutations': [],
                }
                
                # Parse types
                for t in schema.get('types', []):
                    if t['name'].startswith('__'):  # Skip introspection types
                        continue
                    
                    type_info = {
                        'name': t['name'],
                        'kind': t['kind'],
                        'description': t.get('description', ''),
                        'fields': [],
                    }
                    
                    for field in t.get('fields', []) or []:
                        type_info['fields'].append({
                            'name': field['name'],
                            'type': get_graphql_type_name(field.get('type', {})),
                            'args': [a['name'] for a in field.get('args', [])],
                            'deprecated': field.get('isDeprecated', False),
                        })
                    
                    result['types'].append(type_info)
                    
                    # Categorize queries and mutations
                    if t['name'] == result['query_type']:
                        for field in t.get('fields', []) or []:
                            result['queries'].append({
                                'name': field['name'],
                                'args': [{'name': a['name'], 'type': get_graphql_type_name(a.get('type', {}))} for a in field.get('args', [])],
                                'return_type': get_graphql_type_name(field.get('type', {})),
                            })
                    
                    if t['name'] == result['mutation_type']:
                        for field in t.get('fields', []) or []:
                            result['mutations'].append({
                                'name': field['name'],
                                'args': [{'name': a['name'], 'type': get_graphql_type_name(a.get('type', {}))} for a in field.get('args', [])],
                                'return_type': get_graphql_type_name(field.get('type', {})),
                            })
                
                return result
                
    except Exception:
        pass
    finally:
        if should_close:
            client.close()
    
    return None


def get_graphql_type_name(type_obj):
    """Extract type name from GraphQL type object"""
    if not type_obj:
        return 'Unknown'
    
    kind = type_obj.get('kind', '')
    name = type_obj.get('name', '')
    
    if name:
        return name
    
    of_type = type_obj.get('ofType', {})
    if of_type:
        inner = get_graphql_type_name(of_type)
        if kind == 'NON_NULL':
            return f"{inner}!"
        elif kind == 'LIST':
            return f"[{inner}]"
        return inner
    
    return kind


def discover_rest_endpoints(base_url, timeout=10):
    """Discover REST API endpoints"""
    if not httpx:
        return []
    
    findings = []
    
    for path in REST_PATHS:
        url = urljoin(base_url, path)
        result = check_url_exists(url, timeout)
        
        if result and result['status'] in [200, 401, 403]:
            finding = {
                'type': 'rest',
                'url': url,
                'status': result['status'],
                'content_type': result['content_type'],
                'authentication_required': result['status'] in [401, 403],
            }
            
            # Try to detect API response
            is_api = (
                'application/json' in result['content_type'] or
                'application/xml' in result['content_type'] or
                'text/json' in result['content_type']
            )
            finding['is_api_response'] = is_api
            
            findings.append(finding)
    
    return findings


def discover_websocket(base_url, timeout=5):
    """Discover WebSocket endpoints"""
    if not httpx:
        return []
    
    findings = []
    ws_paths = ['/ws', '/websocket', '/socket', '/socket.io', '/sockjs', '/realtime', '/live']
    
    for path in ws_paths:
        url = urljoin(base_url, path)
        result = check_url_exists(url, timeout)
        
        if result:
            # Check for WebSocket upgrade headers
            upgrade = result['headers'].get('upgrade', '').lower()
            connection = result['headers'].get('connection', '').lower()
            
            if 'websocket' in upgrade or result['status'] == 101:
                findings.append({
                    'type': 'websocket',
                    'url': url.replace('http://', 'ws://').replace('https://', 'wss://'),
                    'status': result['status'],
                    'upgrade': upgrade,
                })
            elif result['status'] in [200, 400, 426]:  # 426 = Upgrade Required
                findings.append({
                    'type': 'potential_websocket',
                    'url': url,
                    'status': result['status'],
                    'note': 'Endpoint exists, might support WebSocket upgrade'
                })
    
    return findings


def analyze_api_security(api_findings):
    """Analyze API findings for security issues"""
    issues = []
    
    for finding in api_findings:
        if finding['type'] == 'swagger' or finding['type'] == 'openapi':
            # Check for public API docs
            if finding['status'] == 200:
                issues.append({
                    'severity': 'Medium',
                    'issue': f"API documentation publicly accessible: {finding['url']}",
                    'recommendation': 'Consider restricting API docs access in production'
                })
            
            # Check for missing security definitions
            if not finding.get('security'):
                issues.append({
                    'severity': 'High',
                    'issue': 'No security schemes defined in API specification',
                    'recommendation': 'Define authentication/authorization in API spec'
                })
            
            # Check for deprecated endpoints
            deprecated = [e for e in finding.get('endpoints', []) if e.get('deprecated')]
            if deprecated:
                issues.append({
                    'severity': 'Low',
                    'issue': f"{len(deprecated)} deprecated endpoint(s) still documented",
                    'recommendation': 'Remove deprecated endpoints from production'
                })
        
        elif finding['type'] == 'graphql':
            issues.extend(finding.get('issues', []))
            
            # Check for sensitive operations
            mutations = finding.get('mutations', [])
            sensitive_patterns = ['delete', 'remove', 'admin', 'user', 'password', 'token']
            for mutation in mutations:
                name_lower = mutation['name'].lower()
                for pattern in sensitive_patterns:
                    if pattern in name_lower:
                        issues.append({
                            'severity': 'Medium',
                            'issue': f"Potentially sensitive mutation exposed: {mutation['name']}",
                            'recommendation': 'Ensure proper authorization on sensitive operations'
                        })
                        break
        
        elif finding['type'] == 'rest':
            if not finding.get('authentication_required'):
                issues.append({
                    'severity': 'Medium',
                    'issue': f"REST endpoint accessible without auth: {finding['url']}",
                    'recommendation': 'Consider adding authentication'
                })
    
    return issues


def discover_api_endpoints(url):
    """Main function - discover all API endpoints"""
    result = {
        'base_url': url,
        'swagger': [],
        'graphql': [],
        'rest': [],
        'websocket': [],
        'issues': [],
        'summary': {}
    }
    
    try:
        # Discover Swagger/OpenAPI
        result['swagger'] = discover_swagger(url)
        
        # Discover GraphQL
        result['graphql'] = discover_graphql(url)
        
        # Discover REST endpoints
        result['rest'] = discover_rest_endpoints(url)
        
        # Discover WebSocket endpoints
        result['websocket'] = discover_websocket(url)
        
        # Analyze security
        all_findings = result['swagger'] + result['graphql'] + result['rest']
        result['issues'] = analyze_api_security(all_findings)
        
        # Count total endpoints discovered
        total_endpoints = 0
        for swagger in result['swagger']:
            total_endpoints += len(swagger.get('endpoints', []))
        for graphql in result['graphql']:
            total_endpoints += len(graphql.get('queries', []))
            total_endpoints += len(graphql.get('mutations', []))
        total_endpoints += len(result['rest'])
        
        # Build summary
        result['summary'] = {
            'swagger_docs': len(result['swagger']),
            'graphql_endpoints': len(result['graphql']),
            'rest_endpoints': len(result['rest']),
            'websocket_endpoints': len(result['websocket']),
            'total_endpoints': total_endpoints,
            'issues_found': len(result['issues']),
            'has_introspection': any(g.get('introspection_enabled') for g in result['graphql']),
            'has_public_docs': any(s.get('status') == 200 for s in result['swagger']),
        }
        
    except Exception as e:
        result['error'] = str(e)
    
    return result

# Alias for compatibility with import in crawler_engine.py
discover_apis = discover_api_endpoints
