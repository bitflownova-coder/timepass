import os
import re
from urllib.parse import urlparse, urljoin
import tldextract

def normalize_url(url):
    """Normalizes the URL by removing fragments and query parameters."""
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip('/')

def get_domain(url):
    """Extracts the domain from a URL."""
    extracted = tldextract.extract(url)
    return f"{extracted.domain}.{extracted.suffix}"

def get_safe_filename(url):
    """Generates a safe filename from a URL."""
    parsed = urlparse(url)
    path = parsed.path.strip('/')
    if not path:
        return "index"
    
    # Replace non-alphanumeric characters with underscores
    clean_path = re.sub(r'[^a-zA-Z0-9]', '_', path)
    return clean_path

def ensure_dir_exists(path):
    """Ensures a directory exists."""
    if not os.path.exists(path):
        os.makedirs(path)

def save_text_file(path, content):
    """Saves text content to a file."""
    ensure_dir_exists(os.path.dirname(path))
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)

def save_binary_file(path, content):
    """Saves binary content to a file."""
    ensure_dir_exists(os.path.dirname(path))
    with open(path, 'wb') as f:
        f.write(content)
