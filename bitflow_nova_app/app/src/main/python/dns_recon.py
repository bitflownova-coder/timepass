# dns_recon.py
# DNS & WHOIS Reconnaissance - MX, SPF, DKIM, TXT records, WHOIS lookups

import re
import socket
from urllib.parse import urlparse

try:
    import httpx
except ImportError:
    httpx = None

# Common DNS record types to query
DNS_RECORD_TYPES = ['A', 'AAAA', 'MX', 'TXT', 'NS', 'CNAME', 'SOA']

# SPF record analysis
SPF_MECHANISMS = {
    'all': 'Default mechanism',
    '+all': 'DANGEROUS - Allows any sender',
    '-all': 'Strict - Only listed senders',
    '~all': 'Soft fail - Mark as suspicious',
    '?all': 'Neutral - No policy',
    'include:': 'Includes another domain SPF',
    'ip4:': 'Allow specific IPv4',
    'ip6:': 'Allow specific IPv6',
    'a:': 'Allow A record hosts',
    'mx:': 'Allow MX record hosts',
    'redirect=': 'Redirect to another SPF',
}

# DMARC policy values
DMARC_POLICIES = {
    'none': 'No action (monitoring only)',
    'quarantine': 'Mark as spam',
    'reject': 'Reject message',
}


def extract_domain(url):
    """Extract domain from URL"""
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    parsed = urlparse(url)
    return parsed.netloc.split(':')[0]


def resolve_dns_python(domain, record_type='A'):
    """Resolve DNS using Python socket (basic A/AAAA records)"""
    results = []
    try:
        if record_type == 'A':
            # Get IPv4 addresses
            addrs = socket.getaddrinfo(domain, None, socket.AF_INET)
            for addr in addrs:
                ip = addr[4][0]
                if ip not in results:
                    results.append(ip)
        elif record_type == 'AAAA':
            # Get IPv6 addresses
            try:
                addrs = socket.getaddrinfo(domain, None, socket.AF_INET6)
                for addr in addrs:
                    ip = addr[4][0]
                    if ip not in results:
                        results.append(ip)
            except socket.gaierror:
                pass
    except socket.gaierror as e:
        pass
    return results


def query_dns_over_https(domain, record_type='A'):
    """Query DNS using DNS-over-HTTPS (Cloudflare/Google)"""
    if not httpx:
        return []
    
    results = []
    
    # Try Cloudflare DNS-over-HTTPS
    try:
        url = f"https://cloudflare-dns.com/dns-query?name={domain}&type={record_type}"
        headers = {'Accept': 'application/dns-json'}
        
        with httpx.Client(timeout=10, verify=False) as client:
            response = client.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                answers = data.get('Answer', [])
                for answer in answers:
                    record_data = answer.get('data', '')
                    if record_data and record_data not in results:
                        results.append(record_data)
    except Exception as e:
        pass
    
    # Fallback to Google DNS-over-HTTPS
    if not results:
        try:
            url = f"https://dns.google/resolve?name={domain}&type={record_type}"
            with httpx.Client(timeout=10, verify=False) as client:
                response = client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    answers = data.get('Answer', [])
                    for answer in answers:
                        record_data = answer.get('data', '')
                        if record_data and record_data not in results:
                            results.append(record_data)
        except Exception:
            pass
    
    return results


def analyze_spf_record(spf_record):
    """Analyze SPF record for security issues"""
    analysis = {
        'record': spf_record,
        'mechanisms': [],
        'issues': [],
        'score': 100,  # Start with perfect score
    }
    
    spf_lower = spf_record.lower()
    
    # Check for dangerous +all
    if '+all' in spf_lower:
        analysis['issues'].append({
            'severity': 'Critical',
            'issue': 'SPF uses +all which allows ANY sender',
            'recommendation': 'Change +all to -all or ~all'
        })
        analysis['score'] -= 50
    
    # Check for weak ?all (neutral)
    if '?all' in spf_lower:
        analysis['issues'].append({
            'severity': 'Medium',
            'issue': 'SPF uses ?all (neutral) - no enforcement',
            'recommendation': 'Change ?all to -all for strict enforcement'
        })
        analysis['score'] -= 20
    
    # Check for soft fail ~all
    if '~all' in spf_lower and '-all' not in spf_lower:
        analysis['issues'].append({
            'severity': 'Low',
            'issue': 'SPF uses ~all (soft fail) - might be bypassed',
            'recommendation': 'Consider using -all for strict enforcement'
        })
        analysis['score'] -= 10
    
    # Check for missing -all
    if '-all' not in spf_lower and '+all' not in spf_lower and '~all' not in spf_lower and '?all' not in spf_lower:
        analysis['issues'].append({
            'severity': 'Medium',
            'issue': 'SPF record has no default mechanism',
            'recommendation': 'Add -all at the end of SPF record'
        })
        analysis['score'] -= 15
    
    # Parse mechanisms
    parts = spf_record.split()
    for part in parts:
        if part.startswith('include:'):
            analysis['mechanisms'].append({'type': 'include', 'value': part[8:]})
        elif part.startswith('ip4:'):
            analysis['mechanisms'].append({'type': 'ip4', 'value': part[4:]})
        elif part.startswith('ip6:'):
            analysis['mechanisms'].append({'type': 'ip6', 'value': part[4:]})
        elif part.startswith('a:') or part == 'a':
            analysis['mechanisms'].append({'type': 'a', 'value': part})
        elif part.startswith('mx:') or part == 'mx':
            analysis['mechanisms'].append({'type': 'mx', 'value': part})
        elif part.startswith('redirect='):
            analysis['mechanisms'].append({'type': 'redirect', 'value': part[9:]})
    
    # Too many DNS lookups (SPF has 10 lookup limit)
    lookup_count = len([m for m in analysis['mechanisms'] if m['type'] in ['include', 'a', 'mx', 'redirect']])
    if lookup_count > 10:
        analysis['issues'].append({
            'severity': 'High',
            'issue': f'SPF exceeds 10 DNS lookup limit ({lookup_count} lookups)',
            'recommendation': 'Flatten SPF record to reduce lookups'
        })
        analysis['score'] -= 25
    
    return analysis


def analyze_dmarc_record(dmarc_record):
    """Analyze DMARC record for security issues"""
    analysis = {
        'record': dmarc_record,
        'policy': None,
        'subdomain_policy': None,
        'percentage': 100,
        'rua': None,  # Aggregate reports
        'ruf': None,  # Forensic reports
        'issues': [],
        'score': 100,
    }
    
    dmarc_lower = dmarc_record.lower()
    
    # Parse policy
    policy_match = re.search(r'p=(\w+)', dmarc_lower)
    if policy_match:
        analysis['policy'] = policy_match.group(1)
        
        if analysis['policy'] == 'none':
            analysis['issues'].append({
                'severity': 'High',
                'issue': 'DMARC policy is "none" - no enforcement',
                'recommendation': 'Change to p=quarantine or p=reject'
            })
            analysis['score'] -= 30
        elif analysis['policy'] == 'quarantine':
            analysis['issues'].append({
                'severity': 'Low',
                'issue': 'DMARC policy is "quarantine" - emails marked as spam',
                'recommendation': 'Consider p=reject for maximum protection'
            })
            analysis['score'] -= 5
    else:
        analysis['issues'].append({
            'severity': 'Critical',
            'issue': 'DMARC record has no policy defined',
            'recommendation': 'Add p=reject to DMARC record'
        })
        analysis['score'] -= 40
    
    # Parse subdomain policy
    sp_match = re.search(r'sp=(\w+)', dmarc_lower)
    if sp_match:
        analysis['subdomain_policy'] = sp_match.group(1)
    
    # Parse percentage
    pct_match = re.search(r'pct=(\d+)', dmarc_lower)
    if pct_match:
        analysis['percentage'] = int(pct_match.group(1))
        if analysis['percentage'] < 100:
            analysis['issues'].append({
                'severity': 'Medium',
                'issue': f'DMARC only applies to {analysis["percentage"]}% of emails',
                'recommendation': 'Set pct=100 for full enforcement'
            })
            analysis['score'] -= 15
    
    # Parse report addresses
    rua_match = re.search(r'rua=([^;]+)', dmarc_lower)
    if rua_match:
        analysis['rua'] = rua_match.group(1)
    else:
        analysis['issues'].append({
            'severity': 'Low',
            'issue': 'No aggregate report address (rua) configured',
            'recommendation': 'Add rua=mailto:dmarc@yourdomain.com'
        })
        analysis['score'] -= 5
    
    ruf_match = re.search(r'ruf=([^;]+)', dmarc_lower)
    if ruf_match:
        analysis['ruf'] = ruf_match.group(1)
    
    return analysis


def check_dkim_selector(domain, selector='default'):
    """Check for DKIM record with common selectors"""
    selectors_to_try = [
        selector, 'default', 'google', 'selector1', 'selector2',
        'k1', 'k2', 's1', 's2', 'mail', 'email', 'dkim', 'sig1'
    ]
    
    found_selectors = []
    
    for sel in selectors_to_try:
        dkim_domain = f"{sel}._domainkey.{domain}"
        records = query_dns_over_https(dkim_domain, 'TXT')
        
        for record in records:
            if 'v=DKIM1' in record or 'k=rsa' in record:
                found_selectors.append({
                    'selector': sel,
                    'record': record,
                    'domain': dkim_domain
                })
                break
    
    return found_selectors


def query_whois_via_api(domain):
    """Query WHOIS information via public API"""
    if not httpx:
        return None
    
    whois_data = {
        'domain': domain,
        'registrar': None,
        'creation_date': None,
        'expiration_date': None,
        'updated_date': None,
        'name_servers': [],
        'status': [],
        'registrant': None,
        'raw': None,
        'error': None
    }
    
    # Try multiple WHOIS APIs
    apis = [
        f"https://www.whoisxmlapi.com/whoisserver/WhoisService?domainName={domain}&outputFormat=JSON",
        f"https://api.whois.vu/?q={domain}",
    ]
    
    # Use a simple free WHOIS lookup
    try:
        # Try rdap.org (free RDAP lookup)
        rdap_url = f"https://rdap.org/domain/{domain}"
        with httpx.Client(timeout=15, verify=False, follow_redirects=True) as client:
            response = client.get(rdap_url, headers={'Accept': 'application/rdap+json'})
            if response.status_code == 200:
                data = response.json()
                
                # Parse RDAP response
                whois_data['raw'] = data
                
                # Get events (creation, expiration, etc.)
                events = data.get('events', [])
                for event in events:
                    action = event.get('eventAction', '')
                    date = event.get('eventDate', '')
                    if action == 'registration':
                        whois_data['creation_date'] = date
                    elif action == 'expiration':
                        whois_data['expiration_date'] = date
                    elif action == 'last changed':
                        whois_data['updated_date'] = date
                
                # Get nameservers
                nameservers = data.get('nameservers', [])
                for ns in nameservers:
                    ns_name = ns.get('ldhName', '')
                    if ns_name:
                        whois_data['name_servers'].append(ns_name)
                
                # Get status
                status = data.get('status', [])
                whois_data['status'] = status
                
                # Get registrar
                entities = data.get('entities', [])
                for entity in entities:
                    roles = entity.get('roles', [])
                    if 'registrar' in roles:
                        vcard = entity.get('vcardArray', [])
                        if len(vcard) > 1:
                            for item in vcard[1]:
                                if item[0] == 'fn':
                                    whois_data['registrar'] = item[3]
                                    break
                
                return whois_data
                
    except Exception as e:
        whois_data['error'] = str(e)
    
    return whois_data


def get_mx_records(domain):
    """Get MX records with priority"""
    mx_records = []
    records = query_dns_over_https(domain, 'MX')
    
    for record in records:
        # MX records format: "priority hostname"
        parts = record.split()
        if len(parts) >= 2:
            try:
                priority = int(parts[0])
                hostname = parts[1].rstrip('.')
                mx_records.append({
                    'priority': priority,
                    'hostname': hostname,
                    'provider': identify_email_provider(hostname)
                })
            except ValueError:
                mx_records.append({
                    'priority': 0,
                    'hostname': record.rstrip('.'),
                    'provider': identify_email_provider(record)
                })
        else:
            mx_records.append({
                'priority': 0,
                'hostname': record.rstrip('.'),
                'provider': identify_email_provider(record)
            })
    
    # Sort by priority
    mx_records.sort(key=lambda x: x['priority'])
    return mx_records


def identify_email_provider(mx_hostname):
    """Identify email provider from MX hostname"""
    mx_lower = mx_hostname.lower()
    
    providers = {
        'google': ['google.com', 'googlemail.com', 'aspmx.l.google.com'],
        'microsoft': ['outlook.com', 'office365', 'microsoft.com', 'protection.outlook.com'],
        'zoho': ['zoho.com', 'zoho.eu', 'zoho.in'],
        'protonmail': ['protonmail.ch', 'proton.me'],
        'fastmail': ['fastmail.com', 'messagingengine.com'],
        'mailgun': ['mailgun.org'],
        'sendgrid': ['sendgrid.net'],
        'amazon_ses': ['amazonses.com', 'amazonaws.com'],
        'mimecast': ['mimecast.com'],
        'barracuda': ['barracudanetworks.com'],
        'godaddy': ['secureserver.net'],
        'hostgator': ['hostgator.com'],
        'namecheap': ['registrar-servers.com'],
        'cloudflare': ['cloudflare.net'],
    }
    
    for provider, patterns in providers.items():
        for pattern in patterns:
            if pattern in mx_lower:
                return provider
    
    return 'unknown'


def get_ns_records(domain):
    """Get NS records"""
    ns_records = []
    records = query_dns_over_https(domain, 'NS')
    
    for record in records:
        hostname = record.rstrip('.')
        ns_records.append({
            'hostname': hostname,
            'provider': identify_dns_provider(hostname)
        })
    
    return ns_records


def identify_dns_provider(ns_hostname):
    """Identify DNS provider from NS hostname"""
    ns_lower = ns_hostname.lower()
    
    providers = {
        'cloudflare': ['cloudflare.com'],
        'google': ['googledomains.com', 'google.com'],
        'amazon_route53': ['awsdns'],
        'godaddy': ['domaincontrol.com'],
        'namecheap': ['registrar-servers.com'],
        'dnsimple': ['dnsimple.com'],
        'digitalocean': ['digitalocean.com'],
        'azure': ['azure-dns.com', 'azure-dns.net'],
        'ns1': ['nsone.net'],
        'dyn': ['dynect.net'],
        'ultradns': ['ultradns.com', 'ultradns.net'],
        'easydns': ['easydns.com'],
        'hostgator': ['hostgator.com'],
        'bluehost': ['bluehost.com'],
    }
    
    for provider, patterns in providers.items():
        for pattern in patterns:
            if pattern in ns_lower:
                return provider
    
    return 'unknown'


def get_txt_records(domain):
    """Get all TXT records"""
    return query_dns_over_https(domain, 'TXT')


def analyze_email_security(domain):
    """Comprehensive email security analysis"""
    analysis = {
        'domain': domain,
        'mx_records': [],
        'spf': None,
        'dmarc': None,
        'dkim': [],
        'bimi': None,
        'mta_sts': None,
        'issues': [],
        'score': 100,
        'grade': 'A',
    }
    
    # Get MX records
    analysis['mx_records'] = get_mx_records(domain)
    if not analysis['mx_records']:
        analysis['issues'].append({
            'severity': 'High',
            'issue': 'No MX records found - domain cannot receive email',
            'recommendation': 'Add MX records if email is needed'
        })
        analysis['score'] -= 20
    
    # Get TXT records for SPF
    txt_records = get_txt_records(domain)
    for record in txt_records:
        if record.startswith('v=spf1') or 'v=spf1' in record:
            analysis['spf'] = analyze_spf_record(record)
            analysis['score'] = min(analysis['score'], analysis['spf']['score'])
            analysis['issues'].extend(analysis['spf']['issues'])
            break
    
    if not analysis['spf']:
        analysis['issues'].append({
            'severity': 'High',
            'issue': 'No SPF record found - email spoofing possible',
            'recommendation': 'Add SPF record: v=spf1 include:yourmailprovider -all'
        })
        analysis['score'] -= 25
    
    # Get DMARC record
    dmarc_domain = f"_dmarc.{domain}"
    dmarc_records = query_dns_over_https(dmarc_domain, 'TXT')
    for record in dmarc_records:
        if record.startswith('v=DMARC1') or 'v=DMARC1' in record:
            analysis['dmarc'] = analyze_dmarc_record(record)
            analysis['score'] = min(analysis['score'], analysis['dmarc']['score'])
            analysis['issues'].extend(analysis['dmarc']['issues'])
            break
    
    if not analysis['dmarc']:
        analysis['issues'].append({
            'severity': 'High',
            'issue': 'No DMARC record found - no email authentication policy',
            'recommendation': 'Add DMARC record: v=DMARC1; p=reject; rua=mailto:dmarc@yourdomain.com'
        })
        analysis['score'] -= 25
    
    # Check DKIM (common selectors)
    analysis['dkim'] = check_dkim_selector(domain)
    if not analysis['dkim']:
        analysis['issues'].append({
            'severity': 'Medium',
            'issue': 'No DKIM records found with common selectors',
            'recommendation': 'Configure DKIM signing for outgoing emails'
        })
        analysis['score'] -= 15
    
    # Check BIMI (Brand Indicators for Message Identification)
    bimi_domain = f"default._bimi.{domain}"
    bimi_records = query_dns_over_https(bimi_domain, 'TXT')
    for record in bimi_records:
        if 'v=BIMI1' in record:
            analysis['bimi'] = record
            break
    
    # Check MTA-STS
    mta_sts_domain = f"_mta-sts.{domain}"
    mta_sts_records = query_dns_over_https(mta_sts_domain, 'TXT')
    for record in mta_sts_records:
        if 'v=STSv1' in record:
            analysis['mta_sts'] = record
            break
    
    # Calculate grade
    if analysis['score'] >= 90:
        analysis['grade'] = 'A'
    elif analysis['score'] >= 80:
        analysis['grade'] = 'B'
    elif analysis['score'] >= 70:
        analysis['grade'] = 'C'
    elif analysis['score'] >= 60:
        analysis['grade'] = 'D'
    else:
        analysis['grade'] = 'F'
    
    return analysis


def perform_dns_recon(url):
    """Main function - perform full DNS reconnaissance"""
    domain = extract_domain(url)
    
    result = {
        'domain': domain,
        'a_records': [],
        'aaaa_records': [],
        'mx_records': [],
        'ns_records': [],
        'txt_records': [],
        'email_security': None,
        'whois': None,
        'issues': [],
        'summary': {}
    }
    
    try:
        # Basic DNS records
        result['a_records'] = resolve_dns_python(domain, 'A')
        if not result['a_records']:
            result['a_records'] = query_dns_over_https(domain, 'A')
        
        result['aaaa_records'] = query_dns_over_https(domain, 'AAAA')
        result['mx_records'] = get_mx_records(domain)
        result['ns_records'] = get_ns_records(domain)
        result['txt_records'] = get_txt_records(domain)
        
        # Email security analysis
        result['email_security'] = analyze_email_security(domain)
        result['issues'].extend(result['email_security']['issues'])
        
        # WHOIS lookup
        result['whois'] = query_whois_via_api(domain)
        
        # Summary
        result['summary'] = {
            'a_count': len(result['a_records']),
            'aaaa_count': len(result['aaaa_records']),
            'mx_count': len(result['mx_records']),
            'ns_count': len(result['ns_records']),
            'txt_count': len(result['txt_records']),
            'email_grade': result['email_security']['grade'] if result['email_security'] else 'N/A',
            'has_spf': result['email_security']['spf'] is not None if result['email_security'] else False,
            'has_dmarc': result['email_security']['dmarc'] is not None if result['email_security'] else False,
            'has_dkim': len(result['email_security']['dkim']) > 0 if result['email_security'] else False,
            'issue_count': len(result['issues']),
            'email_provider': result['mx_records'][0]['provider'] if result['mx_records'] else 'none',
            'dns_provider': result['ns_records'][0]['provider'] if result['ns_records'] else 'unknown',
        }
        
    except Exception as e:
        result['error'] = str(e)
    
    return result

# Alias for compatibility with import in crawler_engine.py
analyze_dns = perform_dns_recon
