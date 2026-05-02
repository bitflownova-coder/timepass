# graphql_tester.py
# GraphQL Security Testing — Introspection, depth limits, auth bypass checks

import json
from urllib.parse import urljoin

try:
    import httpx
except ImportError:
    httpx = None

try:
    from http_client import make_client, VERIFY_SSL
except ImportError:
    def make_client(timeout=15, **kw):
        import httpx
        return httpx.Client(timeout=timeout, follow_redirects=True, verify=False)
    VERIFY_SSL = False

# Standard introspection query
INTROSPECTION_QUERY = {
    'query': '''
    {
      __schema {
        queryType { name }
        mutationType { name }
        subscriptionType { name }
        types {
          name
          kind
          fields(includeDeprecated: true) {
            name
            type { name kind ofType { name kind } }
          }
        }
      }
    }
    '''
}

# Deep nested query to test depth limiting
DEPTH_BOMB_QUERY = {
    'query': '{ __typename { __typename { __typename { __typename { __typename { __typename { __typename { __typename { __typename { __typename } } } } } } } } } }'
}

# Mutation probe (no side effects — just checks if mutations are accessible)
MUTATION_PROBE = {
    'query': '{ __schema { mutationType { name fields { name } } } }'
}

# Common GraphQL endpoint paths
GRAPHQL_PATHS = [
    '/graphql',
    '/api/graphql',
    '/v1/graphql',
    '/v2/graphql',
    '/query',
    '/gql',
    '/graph',
    '/graphiql',
    '/playground',
]


def _post_graphql(client, url, query_body):
    """POST a GraphQL query and return (response, json_data or None)."""
    try:
        r = client.post(url, json=query_body,
                        headers={'Content-Type': 'application/json', 'Accept': 'application/json'})
        try:
            data = r.json()
        except Exception:
            data = None
        return r, data
    except Exception as e:
        return None, None


def test_graphql_endpoints(base_url, api_endpoints=None):
    """
    Test GraphQL endpoints for security misconfigurations.

    Parameters
    ----------
    base_url : str
        Root URL of the target.
    api_endpoints : list[str], optional
        Already-discovered API paths from api_discovery module.

    Returns
    -------
    dict with findings list and per-endpoint results.
    """
    if not httpx:
        return {'error': 'httpx not available', 'findings': [], 'endpoints_tested': []}

    findings = []
    endpoints_tested = []

    # Gather candidate endpoints
    candidates = set()
    for path in GRAPHQL_PATHS:
        candidates.add(urljoin(base_url, path))
    if api_endpoints:
        for ep in api_endpoints:
            if 'graphql' in ep.lower() or 'gql' in ep.lower():
                candidates.add(ep)

    with make_client(timeout=12, follow_redirects=True, verify=VERIFY_SSL, rate_limit=True) as client:
        for endpoint in candidates:
            endpoint_result = {
                'url': endpoint,
                'introspection_enabled': False,
                'depth_limiting': None,
                'mutations_exposed': False,
                'auth_required': False,
                'issues': [],
            }

            # 1. Introspection test
            r, data = _post_graphql(client, endpoint, INTROSPECTION_QUERY)
            if r is None:
                continue  # Endpoint unreachable

            if r.status_code in (200, 201) and data and '__schema' in str(data):
                endpoint_result['introspection_enabled'] = True
                findings.append({
                    'url': endpoint,
                    'type': 'GraphQL Introspection Enabled',
                    'severity': 'Medium',
                    'description': (
                        'GraphQL introspection is enabled. Attackers can enumerate '
                        'all types, queries, mutations, and fields.'
                    ),
                })

                # Extract type/mutation info
                schema = data.get('data', {}).get('__schema', {})
                types = [t['name'] for t in schema.get('types', [])
                         if not t['name'].startswith('__')]
                endpoint_result['type_count'] = len(types)
                endpoint_result['types_preview'] = types[:10]

                mut_type = schema.get('mutationType')
                if mut_type:
                    endpoint_result['mutations_exposed'] = True
                    findings.append({
                        'url': endpoint,
                        'type': 'GraphQL Mutations Exposed',
                        'severity': 'High',
                        'description': (
                            f'Mutations are available via introspection. '
                            f'Verify all mutations require authentication and authorization.'
                        ),
                    })

            elif r.status_code in (401, 403):
                endpoint_result['auth_required'] = True

            # 2. Depth bomb test
            r_depth, data_depth = _post_graphql(client, endpoint, DEPTH_BOMB_QUERY)
            if r_depth and r_depth.status_code == 200 and data_depth:
                if 'errors' not in data_depth or not data_depth['errors']:
                    endpoint_result['depth_limiting'] = False
                    findings.append({
                        'url': endpoint,
                        'type': 'GraphQL Depth Limiting Not Enforced',
                        'severity': 'Medium',
                        'description': (
                            'No query depth limit detected. Deeply nested queries could '
                            'be used for DoS attacks against the server.'
                        ),
                    })
                else:
                    endpoint_result['depth_limiting'] = True

            endpoints_tested.append(endpoint_result)

    return {
        'findings': findings,
        'endpoints_tested': endpoints_tested,
        'vulnerable_count': len(findings),
        'summary': f"Tested {len(endpoints_tested)} GraphQL endpoints, found {len(findings)} issues",
    }
