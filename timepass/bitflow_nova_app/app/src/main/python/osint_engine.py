# osint_engine.py
# OSINT Gathering - Emails, Phones, Social Links, PII Detection

import re
from urllib.parse import urlparse

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None

try:
    import httpx
except ImportError:
    httpx = None

# Social media patterns
SOCIAL_PLATFORMS = {
    'facebook': [
        r'https?://(?:www\.)?facebook\.com/[\w\.\-]+',
        r'https?://(?:www\.)?fb\.com/[\w\.\-]+'
    ],
    'twitter': [
        r'https?://(?:www\.)?twitter\.com/[\w]+',
        r'https?://(?:www\.)?x\.com/[\w]+'
    ],
    'linkedin': [
        r'https?://(?:www\.)?linkedin\.com/(?:company|in)/[\w\-]+'
    ],
    'instagram': [
        r'https?://(?:www\.)?instagram\.com/[\w\.]+'
    ],
    'youtube': [
        r'https?://(?:www\.)?youtube\.com/(?:c/|channel/|user/|@)[\w\-]+'
    ],
    'github': [
        r'https?://(?:www\.)?github\.com/[\w\-]+'
    ],
    'gitlab': [
        r'https?://(?:www\.)?gitlab\.com/[\w\-]+'
    ],
    'pinterest': [
        r'https?://(?:www\.)?pinterest\.com/[\w]+'
    ],
    'tiktok': [
        r'https?://(?:www\.)?tiktok\.com/@[\w\.]+'
    ],
    'discord': [
        r'https?://(?:www\.)?discord\.(?:gg|com/invite)/[\w]+'
    ],
    'telegram': [
        r'https?://(?:www\.)?t\.me/[\w]+'
    ],
    'medium': [
        r'https?://(?:www\.)?medium\.com/@?[\w\-]+'
    ],
    'reddit': [
        r'https?://(?:www\.)?reddit\.com/(?:r|user)/[\w]+'
    ],
    'twitch': [
        r'https?://(?:www\.)?twitch\.tv/[\w]+'
    ],
    'slack': [
        r'https?://[\w\-]+\.slack\.com'
    ],
    'whatsapp': [
        r'https?://(?:api\.)?whatsapp\.com/[\w\?=&]+'
    ]
}

# Email regex patterns
EMAIL_PATTERNS = [
    r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}',
]

# Phone patterns (various formats)
PHONE_PATTERNS = {
    'us': r'(?:\+1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
    'uk': r'(?:\+44[-.\s]?)?(?:\(0\)[-.\s]?)?\d{2,4}[-.\s]?\d{3,4}[-.\s]?\d{3,4}',
    'international': r'\+\d{1,3}[-.\s]?\d{1,4}[-.\s]?\d{1,4}[-.\s]?\d{1,9}',
    'generic': r'(?:tel:|phone:)?\s*[\d\-\.\s\(\)]{10,}'
}

# Address patterns
ADDRESS_PATTERNS = [
    # US address
    r'\d{1,5}\s+[\w\s]+(?:street|st|avenue|ave|road|rd|boulevard|blvd|drive|dr|lane|ln|court|ct|way|circle|cir)[,.\s]+[\w\s]+[,.\s]+[A-Z]{2}\s+\d{5}(?:-\d{4})?',
    # Generic with zip
    r'\d{1,5}\s+[\w\s]{5,50}[,.\s]+\d{5,6}'
]

# PII patterns
PII_PATTERNS = {
    'ssn': {
        'pattern': r'\b\d{3}-\d{2}-\d{4}\b',
        'severity': 'Critical',
        'description': 'Social Security Number'
    },
    'credit_card': {
        'pattern': r'\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|6(?:011|5[0-9]{2})[0-9]{12})\b',
        'severity': 'Critical',
        'description': 'Credit Card Number'
    },
    'passport': {
        'pattern': r'\b[A-Z]{1,2}\d{6,9}\b',
        'severity': 'High',
        'description': 'Potential Passport Number'
    },
    'date_of_birth': {
        'pattern': r'\b(?:DOB|Date of Birth|Birthday)[:\s]*\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}\b',
        'severity': 'Medium',
        'description': 'Date of Birth'
    }
}

# Name patterns (for employee discovery)
NAME_PATTERNS = [
    r'\b(?:By|Author|Written by|Posted by|Contact)[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b',
    r'<meta\s+name=["\']author["\']\s+content=["\']([^"\']+)["\']',
]


def extract_emails(text, source_url=''):
    """Extract email addresses from text"""
    emails = set()
    
    for pattern in EMAIL_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for email in matches:
            email = email.lower().strip()
            # Filter out obviously fake emails
            if not any(fake in email for fake in ['example.com', 'test.com', 'localhost', 'domain.com']):
                emails.add(email)
    
    return [{
        'email': email,
        'source': source_url,
        'type': 'extracted'
    } for email in emails]


def extract_phones(text, source_url=''):
    """Extract phone numbers from text"""
    phones = set()
    
    for region, pattern in PHONE_PATTERNS.items():
        matches = re.findall(pattern, text)
        for phone in matches:
            # Clean up the phone number
            cleaned = re.sub(r'[^\d+]', '', phone)
            if len(cleaned) >= 10:
                phones.add((phone.strip(), region))
    
    return [{
        'phone': phone,
        'format': region,
        'source': source_url,
        'type': 'extracted'
    } for phone, region in phones]


def extract_social_links(html_content, source_url=''):
    """Extract social media links"""
    social = {}
    
    for platform, patterns in SOCIAL_PLATFORMS.items():
        links = set()
        for pattern in patterns:
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            links.update(matches)
        if links:
            social[platform] = list(links)
    
    results = []
    for platform, links in social.items():
        for link in links:
            results.append({
                'platform': platform,
                'url': link,
                'source': source_url
            })
    
    return results


def extract_addresses(text, source_url=''):
    """Extract physical addresses"""
    addresses = []
    
    for pattern in ADDRESS_PATTERNS:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for addr in matches:
            addresses.append({
                'address': addr.strip(),
                'source': source_url
            })
    
    return addresses


def detect_pii(text, source_url=''):
    """Detect PII (Personally Identifiable Information)"""
    findings = []
    
    for pii_type, config in PII_PATTERNS.items():
        matches = re.findall(config['pattern'], text, re.IGNORECASE)
        for match in matches:
            # Validate credit cards with Luhn algorithm
            if pii_type == 'credit_card':
                if not luhn_check(re.sub(r'\D', '', match)):
                    continue
            
            findings.append({
                'type': pii_type,
                'severity': config['severity'],
                'description': config['description'],
                'value_masked': mask_pii(match, pii_type),
                'source': source_url
            })
    
    return findings


def luhn_check(card_number):
    """Luhn algorithm for credit card validation"""
    try:
        digits = [int(d) for d in card_number]
        odd_digits = digits[-1::-2]
        even_digits = digits[-2::-2]
        checksum = sum(odd_digits)
        for d in even_digits:
            checksum += sum([int(x) for x in str(d * 2)])
        return checksum % 10 == 0
    except:
        return False


def mask_pii(value, pii_type):
    """Mask sensitive PII for safe display"""
    if pii_type == 'credit_card':
        return f"****-****-****-{value[-4:]}"
    elif pii_type == 'ssn':
        return f"***-**-{value[-4:]}"
    elif pii_type == 'passport':
        return f"{value[:2]}*****{value[-2:]}"
    else:
        return f"{value[:2]}...{value[-2:]}" if len(value) > 4 else '****'


def extract_names(html_content, source_url=''):
    """Extract potential employee/author names"""
    names = set()
    
    if BeautifulSoup:
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Author meta tag
            author = soup.find('meta', attrs={'name': 'author'})
            if author and author.get('content'):
                names.add(author['content'])
            
            # Common author class names
            author_classes = ['author', 'byline', 'author-name', 'writer', 'posted-by']
            for cls in author_classes:
                for elem in soup.find_all(class_=re.compile(cls, re.I)):
                    text = elem.get_text(strip=True)
                    if text and len(text) < 100:
                        # Check if it looks like a name
                        if re.match(r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+$', text):
                            names.add(text)
        except:
            pass
    
    # Regex extraction as fallback
    for pattern in NAME_PATTERNS:
        matches = re.findall(pattern, html_content)
        for match in matches:
            if isinstance(match, tuple):
                match = match[0]
            if match and len(match) < 100:
                names.add(match)
    
    return [{
        'name': name,
        'source': source_url,
        'type': 'potential_employee'
    } for name in names]


def query_wayback_machine(domain, limit=10):
    """Query Wayback Machine for historical URLs"""
    results = []
    
    if not httpx:
        return results
    
    try:
        api_url = f"https://web.archive.org/cdx/search/cdx?url={domain}/*&output=json&limit={limit}&fl=original,timestamp,statuscode"
        
        with httpx.Client(timeout=15) as client:
            response = client.get(api_url)
            if response.status_code == 200:
                data = response.json()
                # Skip header row
                for row in data[1:]:
                    results.append({
                        'url': row[0],
                        'timestamp': row[1],
                        'status': row[2],
                        'archive_url': f"https://web.archive.org/web/{row[1]}/{row[0]}"
                    })
    except:
        pass
    
    return results


def query_certificate_transparency(domain):
    """Query crt.sh for certificate transparency logs"""
    results = []
    
    if not httpx:
        return results
    
    try:
        api_url = f"https://crt.sh/?q=%.{domain}&output=json"
        
        with httpx.Client(timeout=20) as client:
            response = client.get(api_url)
            if response.status_code == 200:
                data = response.json()
                seen = set()
                for cert in data[:50]:  # Limit results
                    name = cert.get('name_value', '')
                    if name and name not in seen:
                        seen.add(name)
                        results.append({
                            'subdomain': name,
                            'issuer': cert.get('issuer_name', ''),
                            'not_before': cert.get('not_before', ''),
                            'not_after': cert.get('not_after', '')
                        })
    except:
        pass
    
    return results


def analyze_osint(html_content, page_url, full_text=None):
    """
    Perform OSINT analysis on a page
    
    Args:
        html_content: HTML content
        page_url: URL of the page
        full_text: Optional plain text content
    
    Returns:
        Dictionary with OSINT findings
    """
    text = full_text or html_content
    
    results = {
        'page_url': page_url,
        'emails': extract_emails(text, page_url),
        'phones': extract_phones(text, page_url),
        'social_links': extract_social_links(html_content, page_url),
        'addresses': extract_addresses(text, page_url),
        'names': extract_names(html_content, page_url),
        'pii': detect_pii(text, page_url),
        'summary': {}
    }
    
    results['summary'] = {
        'emails_found': len(results['emails']),
        'phones_found': len(results['phones']),
        'social_platforms': len(set(s['platform'] for s in results['social_links'])),
        'addresses_found': len(results['addresses']),
        'names_found': len(results['names']),
        'pii_leaked': len(results['pii'])
    }
    
    return results


def get_osint_summary(all_osint_results, domain=None):
    """Generate OSINT summary across all pages"""
    summary = {
        'pages_analyzed': len(all_osint_results),
        'unique_emails': set(),
        'unique_phones': set(),
        'social_presence': {},
        'unique_addresses': set(),
        'unique_names': set(),
        'pii_findings': [],
        'wayback_urls': [],
        'ct_subdomains': []
    }
    
    for result in all_osint_results:
        for email in result.get('emails', []):
            summary['unique_emails'].add(email['email'])
        
        for phone in result.get('phones', []):
            summary['unique_phones'].add(phone['phone'])
        
        for social in result.get('social_links', []):
            platform = social['platform']
            if platform not in summary['social_presence']:
                summary['social_presence'][platform] = set()
            summary['social_presence'][platform].add(social['url'])
        
        for addr in result.get('addresses', []):
            summary['unique_addresses'].add(addr['address'])
        
        for name in result.get('names', []):
            summary['unique_names'].add(name['name'])
        
        summary['pii_findings'].extend(result.get('pii', []))
    
    # Query external sources if domain provided
    if domain:
        summary['wayback_urls'] = query_wayback_machine(domain)
        summary['ct_subdomains'] = query_certificate_transparency(domain)
    
    # Convert sets for JSON serialization
    summary['unique_emails'] = list(summary['unique_emails'])
    summary['unique_phones'] = list(summary['unique_phones'])
    summary['unique_addresses'] = list(summary['unique_addresses'])
    summary['unique_names'] = list(summary['unique_names'])
    
    # Convert social sets to lists
    for platform in summary['social_presence']:
        summary['social_presence'][platform] = list(summary['social_presence'][platform])
    
    # Add counts
    summary['counts'] = {
        'emails': len(summary['unique_emails']),
        'phones': len(summary['unique_phones']),
        'social_platforms': len(summary['social_presence']),
        'addresses': len(summary['unique_addresses']),
        'names': len(summary['unique_names']),
        'pii': len(summary['pii_findings']),
        'wayback': len(summary['wayback_urls']),
        'ct_subdomains': len(summary['ct_subdomains'])
    }
    
    return summary
