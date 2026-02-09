# ssl_analyzer.py
# SSL/TLS Certificate Analysis - Ciphers, Expiry, Chain, CT Logs

import ssl
import socket
import hashlib
from datetime import datetime, timedelta
from urllib.parse import urlparse

try:
    import httpx
except ImportError:
    httpx = None

# Weak cipher suites to flag
WEAK_CIPHERS = [
    'RC4', 'DES', '3DES', 'MD5', 'NULL', 'EXPORT', 'anon',
    'RC2', 'IDEA', 'SEED', 'CAMELLIA128'
]

# Deprecated TLS versions
DEPRECATED_TLS = ['SSLv2', 'SSLv3', 'TLSv1.0', 'TLSv1.1']

# Certificate key size recommendations
MIN_RSA_BITS = 2048
MIN_EC_BITS = 256

# Certificate transparency log servers
CT_LOG_SERVERS = [
    'https://crt.sh/?q={}&output=json',
]


def extract_domain(url):
    """Extract domain from URL"""
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    parsed = urlparse(url)
    return parsed.netloc.split(':')[0]


def get_certificate_info(hostname, port=443, timeout=10):
    """Get SSL certificate information"""
    cert_info = {
        'hostname': hostname,
        'port': port,
        'valid': False,
        'issuer': {},
        'subject': {},
        'serial_number': None,
        'version': None,
        'not_before': None,
        'not_after': None,
        'days_until_expiry': None,
        'expired': False,
        'self_signed': False,
        'san': [],  # Subject Alternative Names
        'signature_algorithm': None,
        'public_key': {},
        'fingerprints': {},
        'chain': [],
        'issues': [],
        'score': 100,
        'grade': 'A',
        'error': None
    }
    
    try:
        # Create SSL context
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE  # We'll do our own validation
        
        # Connect and get certificate
        with socket.create_connection((hostname, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                # Get peer certificate
                cert_binary = ssock.getpeercert(binary_form=True)
                cert = ssock.getpeercert()
                
                if not cert:
                    cert_info['error'] = 'No certificate returned'
                    return cert_info
                
                cert_info['valid'] = True
                
                # Parse issuer
                issuer = dict(x[0] for x in cert.get('issuer', []))
                cert_info['issuer'] = {
                    'common_name': issuer.get('commonName', ''),
                    'organization': issuer.get('organizationName', ''),
                    'country': issuer.get('countryName', ''),
                }
                
                # Parse subject
                subject = dict(x[0] for x in cert.get('subject', []))
                cert_info['subject'] = {
                    'common_name': subject.get('commonName', ''),
                    'organization': subject.get('organizationName', ''),
                    'country': subject.get('countryName', ''),
                }
                
                # Check for self-signed
                if cert_info['issuer']['common_name'] == cert_info['subject']['common_name']:
                    cert_info['self_signed'] = True
                    cert_info['issues'].append({
                        'severity': 'High',
                        'issue': 'Self-signed certificate',
                        'recommendation': 'Use a certificate from a trusted CA'
                    })
                    cert_info['score'] -= 30
                
                # Serial number
                cert_info['serial_number'] = cert.get('serialNumber', '')
                
                # Version
                cert_info['version'] = cert.get('version', 0) + 1  # X.509 version
                
                # Validity dates
                not_before = cert.get('notBefore', '')
                not_after = cert.get('notAfter', '')
                
                if not_before:
                    try:
                        cert_info['not_before'] = datetime.strptime(
                            not_before, '%b %d %H:%M:%S %Y %Z'
                        ).isoformat()
                    except ValueError:
                        cert_info['not_before'] = not_before
                
                if not_after:
                    try:
                        expiry = datetime.strptime(not_after, '%b %d %H:%M:%S %Y %Z')
                        cert_info['not_after'] = expiry.isoformat()
                        
                        # Calculate days until expiry
                        now = datetime.utcnow()
                        days_left = (expiry - now).days
                        cert_info['days_until_expiry'] = days_left
                        
                        if days_left < 0:
                            cert_info['expired'] = True
                            cert_info['issues'].append({
                                'severity': 'Critical',
                                'issue': f'Certificate EXPIRED {abs(days_left)} days ago',
                                'recommendation': 'Renew certificate immediately'
                            })
                            cert_info['score'] -= 50
                        elif days_left < 7:
                            cert_info['issues'].append({
                                'severity': 'Critical',
                                'issue': f'Certificate expires in {days_left} days',
                                'recommendation': 'Renew certificate immediately'
                            })
                            cert_info['score'] -= 30
                        elif days_left < 30:
                            cert_info['issues'].append({
                                'severity': 'High',
                                'issue': f'Certificate expires in {days_left} days',
                                'recommendation': 'Renew certificate soon'
                            })
                            cert_info['score'] -= 15
                        elif days_left < 90:
                            cert_info['issues'].append({
                                'severity': 'Medium',
                                'issue': f'Certificate expires in {days_left} days',
                                'recommendation': 'Plan certificate renewal'
                            })
                            cert_info['score'] -= 5
                    except ValueError:
                        cert_info['not_after'] = not_after
                
                # Subject Alternative Names (SAN)
                san = cert.get('subjectAltName', [])
                cert_info['san'] = [name for _, name in san]
                
                # Check if hostname matches
                hostname_valid = False
                check_names = [cert_info['subject']['common_name']] + cert_info['san']
                for name in check_names:
                    if name == hostname:
                        hostname_valid = True
                        break
                    # Wildcard matching
                    if name.startswith('*.') and hostname.endswith(name[1:]):
                        hostname_valid = True
                        break
                
                if not hostname_valid:
                    cert_info['issues'].append({
                        'severity': 'Critical',
                        'issue': f'Hostname {hostname} not in certificate',
                        'recommendation': 'Certificate should include the domain name'
                    })
                    cert_info['score'] -= 40
                
                # Calculate fingerprints
                cert_info['fingerprints'] = {
                    'sha256': hashlib.sha256(cert_binary).hexdigest(),
                    'sha1': hashlib.sha1(cert_binary).hexdigest(),
                    'md5': hashlib.md5(cert_binary).hexdigest(),
                }
                
                # Get cipher info
                cipher = ssock.cipher()
                if cipher:
                    cert_info['cipher'] = {
                        'name': cipher[0],
                        'protocol': cipher[1],
                        'bits': cipher[2]
                    }
                    
                    # Check for weak ciphers
                    cipher_name = cipher[0].upper()
                    for weak in WEAK_CIPHERS:
                        if weak in cipher_name:
                            cert_info['issues'].append({
                                'severity': 'High',
                                'issue': f'Weak cipher in use: {cipher[0]}',
                                'recommendation': 'Configure server to use strong ciphers only'
                            })
                            cert_info['score'] -= 20
                            break
                
                # Get TLS version
                tls_version = ssock.version()
                cert_info['tls_version'] = tls_version
                
                if tls_version in DEPRECATED_TLS or 'SSL' in tls_version:
                    cert_info['issues'].append({
                        'severity': 'High',
                        'issue': f'Deprecated TLS version: {tls_version}',
                        'recommendation': 'Upgrade to TLS 1.2 or TLS 1.3'
                    })
                    cert_info['score'] -= 25
                
    except ssl.SSLError as e:
        cert_info['error'] = f'SSL Error: {str(e)}'
    except socket.timeout:
        cert_info['error'] = 'Connection timeout'
    except socket.gaierror as e:
        cert_info['error'] = f'DNS Error: {str(e)}'
    except ConnectionRefusedError:
        cert_info['error'] = 'Connection refused'
    except Exception as e:
        cert_info['error'] = str(e)
    
    # Calculate grade
    if cert_info['score'] >= 90:
        cert_info['grade'] = 'A'
    elif cert_info['score'] >= 80:
        cert_info['grade'] = 'B'
    elif cert_info['score'] >= 70:
        cert_info['grade'] = 'C'
    elif cert_info['score'] >= 60:
        cert_info['grade'] = 'D'
    else:
        cert_info['grade'] = 'F'
    
    return cert_info


def check_tls_versions(hostname, port=443, timeout=5):
    """Check which TLS versions are supported"""
    supported = {
        'SSLv2': False,
        'SSLv3': False,
        'TLSv1.0': False,
        'TLSv1.1': False,
        'TLSv1.2': False,
        'TLSv1.3': False,
    }
    
    version_map = {
        'TLSv1.0': ssl.TLSVersion.TLSv1,
        'TLSv1.1': ssl.TLSVersion.TLSv1_1,
        'TLSv1.2': ssl.TLSVersion.TLSv1_2,
    }
    
    # Check TLS 1.3 support (Python 3.7+)
    if hasattr(ssl.TLSVersion, 'TLSv1_3'):
        version_map['TLSv1.3'] = ssl.TLSVersion.TLSv1_3
    
    for version_name, version_const in version_map.items():
        try:
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.minimum_version = version_const
            context.maximum_version = version_const
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            with socket.create_connection((hostname, port), timeout=timeout) as sock:
                with context.wrap_socket(sock, server_hostname=hostname):
                    supported[version_name] = True
        except Exception:
            pass
    
    return supported


def query_certificate_transparency(domain, limit=100):
    """Query Certificate Transparency logs via crt.sh"""
    if not httpx:
        return []
    
    certificates = []
    
    try:
        url = f"https://crt.sh/?q={domain}&output=json"
        with httpx.Client(timeout=30, verify=False) as client:
            response = client.get(url)
            if response.status_code == 200:
                data = response.json()
                
                seen_ids = set()
                for cert in data[:limit]:
                    cert_id = cert.get('id')
                    if cert_id in seen_ids:
                        continue
                    seen_ids.add(cert_id)
                    
                    certificates.append({
                        'id': cert_id,
                        'common_name': cert.get('common_name', ''),
                        'name_value': cert.get('name_value', ''),
                        'issuer_name': cert.get('issuer_name', ''),
                        'not_before': cert.get('not_before', ''),
                        'not_after': cert.get('not_after', ''),
                        'serial_number': cert.get('serial_number', ''),
                    })
    except Exception as e:
        pass
    
    return certificates


def check_ocsp_stapling(hostname, port=443, timeout=10):
    """Check if OCSP stapling is enabled"""
    try:
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        with socket.create_connection((hostname, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                # OCSP response is part of the handshake if stapling is enabled
                # We can't directly check this in Python without lower-level access
                # But we can infer from certificate chain
                return {
                    'supported': 'unknown',
                    'note': 'OCSP stapling check requires server configuration verification'
                }
    except Exception as e:
        return {'supported': False, 'error': str(e)}


def check_hsts_preload(hostname):
    """Check if domain is in HSTS preload list"""
    if not httpx:
        return {'preloaded': False, 'error': 'httpx not available'}
    
    try:
        # Check hstspreload.org
        url = f"https://hstspreload.org/api/v2/status?domain={hostname}"
        with httpx.Client(timeout=10, verify=False) as client:
            response = client.get(url)
            if response.status_code == 200:
                data = response.json()
                return {
                    'preloaded': data.get('status') == 'preloaded',
                    'status': data.get('status', 'unknown'),
                    'bulk_status': data.get('bulk', {})
                }
    except Exception as e:
        return {'preloaded': False, 'error': str(e)}
    
    return {'preloaded': False}


def analyze_ssl_certificate(url):
    """Main function - comprehensive SSL/TLS analysis"""
    hostname = extract_domain(url)
    
    result = {
        'hostname': hostname,
        'certificate': None,
        'tls_versions': {},
        'certificate_transparency': [],
        'hsts_preload': None,
        'issues': [],
        'recommendations': [],
        'summary': {},
        'grade': 'N/A',
        'score': 0
    }
    
    try:
        # Get certificate info
        result['certificate'] = get_certificate_info(hostname)
        result['issues'].extend(result['certificate'].get('issues', []))
        result['score'] = result['certificate'].get('score', 0)
        result['grade'] = result['certificate'].get('grade', 'N/A')
        
        # Check TLS versions
        result['tls_versions'] = check_tls_versions(hostname)
        
        # Flag deprecated TLS versions
        for version, supported in result['tls_versions'].items():
            if supported and version in DEPRECATED_TLS:
                result['issues'].append({
                    'severity': 'High' if version in ['SSLv2', 'SSLv3'] else 'Medium',
                    'issue': f'Deprecated {version} is supported',
                    'recommendation': 'Disable support for deprecated TLS versions'
                })
                result['score'] -= 10
        
        # Check if TLS 1.3 is supported
        if not result['tls_versions'].get('TLSv1.3', False):
            result['recommendations'].append({
                'priority': 'Low',
                'recommendation': 'Enable TLS 1.3 for improved performance and security'
            })
        
        # Query Certificate Transparency logs
        result['certificate_transparency'] = query_certificate_transparency(hostname, limit=20)
        
        # Check HSTS preload
        result['hsts_preload'] = check_hsts_preload(hostname)
        
        # Build summary
        cert = result['certificate']
        result['summary'] = {
            'valid': cert.get('valid', False),
            'expired': cert.get('expired', False),
            'days_until_expiry': cert.get('days_until_expiry'),
            'self_signed': cert.get('self_signed', False),
            'tls_version': cert.get('tls_version', 'Unknown'),
            'cipher': cert.get('cipher', {}).get('name', 'Unknown'),
            'issuer': cert.get('issuer', {}).get('organization', 'Unknown'),
            'san_count': len(cert.get('san', [])),
            'ct_certificates': len(result['certificate_transparency']),
            'hsts_preloaded': result['hsts_preload'].get('preloaded', False) if result['hsts_preload'] else False,
            'tls13_supported': result['tls_versions'].get('TLSv1.3', False),
            'deprecated_tls': any(result['tls_versions'].get(v, False) for v in DEPRECATED_TLS),
            'issue_count': len(result['issues']),
            'grade': result['grade'],
            'score': result['score'],
        }
        
    except Exception as e:
        result['error'] = str(e)
    
    return result
