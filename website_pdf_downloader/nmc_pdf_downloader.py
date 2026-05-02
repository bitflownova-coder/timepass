"""
NMC Website PDF Downloader
Downloads all PDFs from https://www.nmc.org.in/ organized by page and heading
"""

import os
import re
import requests
from requests.exceptions import Timeout, ConnectionError, RequestException
from socket import timeout as SocketTimeout
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, unquote
import time
from collections import defaultdict
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
import urllib3

# Disable SSL warnings (NMC website has certificate issues)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('download_log.txt', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class NMCPDFDownloader:
    def __init__(self, base_url="https://www.nmc.org.in/", output_dir="NMC_PDFs"):
        self.base_url = base_url
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.session.verify = False  # Disable SSL verification for NMC website
        self.visited_urls = set()
        self.pdf_links = defaultdict(lambda: defaultdict(list))  # {page: {heading: [pdfs]}}
        self.downloaded_pdfs = set()
        self.failed_downloads = []
        
    def sanitize_filename(self, filename):
        """Remove invalid characters from filename"""
        # Remove invalid characters for Windows filenames
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        # Remove multiple spaces/underscores
        filename = re.sub(r'[_\s]+', '_', filename)
        # Limit filename length
        if len(filename) > 200:
            filename = filename[:200]
        return filename.strip('_')
    
    def sanitize_folder_name(self, name):
        """Sanitize folder name"""
        # Remove invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            name = name.replace(char, '_')
        name = re.sub(r'[_\s]+', '_', name)
        if len(name) > 100:
            name = name[:100]
        return name.strip('_') or "General"
    
    def get_page_name(self, url):
        """Extract a readable page name from URL"""
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        if not path:
            return "Home"
        # Get the last part of the path
        parts = path.split('/')
        page_name = parts[-1] if parts[-1] else parts[-2] if len(parts) > 1 else "Home"
        # Clean up the name
        page_name = page_name.replace('-', ' ').replace('_', ' ').title()
        return self.sanitize_folder_name(page_name)
    
    def extract_pdf_name(self, url, link_text=""):
        """Extract a meaningful name for the PDF"""
        # Try to get name from URL
        parsed = urlparse(url)
        if 'getDocument' in url:
            # Extract from path parameter
            path_match = re.search(r'path=([^&]+)', url)
            if path_match:
                path = unquote(path_match.group(1))
                filename = os.path.basename(path)
                name = os.path.splitext(filename)[0]
                return self.sanitize_filename(name)
        
        # Get from URL path
        filename = os.path.basename(parsed.path)
        if filename.endswith('.pdf'):
            name = os.path.splitext(filename)[0]
            if name:
                return self.sanitize_filename(unquote(name))
        
        # Use link text if available
        if link_text:
            return self.sanitize_filename(link_text[:100])
        
        return self.sanitize_filename(f"document_{hash(url) % 10000}")
    
    def find_current_heading(self, element):
        """Find the nearest heading above the element"""
        # Look for previous headings
        for tag in ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            # Check previous siblings
            prev = element.find_previous(tag)
            if prev:
                text = prev.get_text(strip=True)
                if text:
                    return self.sanitize_folder_name(text[:80])
        return "General"
    
    def extract_pdfs_from_content(self, soup, url, page_name):
        """Extract PDF links from parsed HTML content"""
        pdf_data = []
        
        # Find all links
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(url, href)
            
            # Check if it's a PDF link
            is_pdf = (
                href.lower().endswith('.pdf') or
                'getDocument' in href or
                '/Documents/' in href and '.pdf' in href.lower() or
                'download' in href.lower() and '.pdf' in href.lower() or
                '/uploads/' in href and '.pdf' in href.lower() or
                '/wp-content/' in href and '.pdf' in href.lower()
            )
            
            if is_pdf:
                link_text = link.get_text(strip=True)
                heading = self.find_current_heading(link)
                pdf_name = self.extract_pdf_name(full_url, link_text)
                
                pdf_info = {
                    'url': full_url,
                    'name': pdf_name,
                    'link_text': link_text,
                    'page': page_name,
                    'heading': heading,
                    'source_url': url
                }
                pdf_data.append(pdf_info)
                self.pdf_links[page_name][heading].append(pdf_info)
        
        # Also check for direct PDF embeds (object, embed tags)
        for obj in soup.find_all(['object', 'embed']):
            data_url = obj.get('data') or obj.get('src')
            if data_url and '.pdf' in data_url.lower():
                full_url = urljoin(url, data_url)
                pdf_name = self.extract_pdf_name(full_url, "Embedded PDF")
                heading = self.find_current_heading(obj)
                
                pdf_info = {
                    'url': full_url,
                    'name': pdf_name,
                    'link_text': 'Embedded PDF',
                    'page': page_name,
                    'heading': heading,
                    'source_url': url
                }
                pdf_data.append(pdf_info)
                self.pdf_links[page_name][heading].append(pdf_info)
        
        return pdf_data
    
    def get_pdfs_from_iframe(self, iframe_url, parent_url, page_name):
        """Extract PDFs from iframe content"""
        pdf_data = []
        
        try:
            # Check if iframe URL is a direct PDF
            if '.pdf' in iframe_url.lower():
                pdf_name = self.extract_pdf_name(iframe_url, "Iframe PDF")
                pdf_info = {
                    'url': iframe_url,
                    'name': pdf_name,
                    'link_text': 'Iframe PDF',
                    'page': page_name,
                    'heading': 'Iframe_Content',
                    'source_url': parent_url
                }
                pdf_data.append(pdf_info)
                self.pdf_links[page_name]['Iframe_Content'].append(pdf_info)
                return pdf_data
            
            # Otherwise fetch iframe content and extract PDFs
            response = self.session.get(iframe_url, timeout=30)
            if response.status_code == 200:
                iframe_soup = BeautifulSoup(response.content, 'html.parser')
                pdf_data.extend(self.extract_pdfs_from_content(iframe_soup, iframe_url, page_name))
                
        except Exception as e:
            logger.debug(f"Could not process iframe {iframe_url}: {e}")
        
        return pdf_data
    
    def get_pdf_links_from_page(self, url, retries=3):
        """Extract all PDF links from a single page"""
        if url in self.visited_urls:
            return []
        
        self.visited_urls.add(url)
        pdf_data = []
        
        for attempt in range(retries):
            try:
                logger.info(f"Scanning page: {url}")
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                break  # Success, exit retry loop
            except (Timeout, ConnectionError, RequestException, TimeoutError, SocketTimeout, OSError) as e:
                if attempt < retries - 1:
                    logger.warning(f"Timeout/connection error on {url}, retrying ({attempt + 1}/{retries})...")
                    time.sleep(2)  # Wait before retry
                    continue
                else:
                    logger.error(f"Failed after {retries} attempts: {url}")
                    return []
            except Exception as e:
                logger.error(f"Error scanning {url}: {e}")
                return []
        
        try:
            
            page_name = self.get_page_name(url)
            
            # Extract PDFs from main page content
            pdf_data.extend(self.extract_pdfs_from_content(soup, url, page_name))
            
            # Find and process iframes
            for iframe in soup.find_all('iframe'):
                iframe_src = iframe.get('src')
                if iframe_src:
                    iframe_url = urljoin(url, iframe_src)
                    # Only process internal iframes or PDF iframes
                    if iframe_url.startswith(self.base_url) or '.pdf' in iframe_url.lower():
                        logger.debug(f"Processing iframe: {iframe_url}")
                        pdf_data.extend(self.get_pdfs_from_iframe(iframe_url, url, page_name))
            
            # Also look for PDF viewers (Google Docs viewer, etc.)
            for link in soup.find_all(['a', 'iframe', 'embed', 'object'], src=True):
                src = link.get('src', '')
                # Extract PDF from Google Docs viewer URLs
                if 'docs.google.com/viewer' in src or 'drive.google.com' in src:
                    pdf_match = re.search(r'url=([^&]+)', src)
                    if pdf_match:
                        pdf_url = unquote(pdf_match.group(1))
                        if '.pdf' in pdf_url.lower():
                            pdf_name = self.extract_pdf_name(pdf_url, "Google Viewer PDF")
                            pdf_info = {
                                'url': pdf_url,
                                'name': pdf_name,
                                'link_text': 'Google Viewer PDF',
                                'page': page_name,
                                'heading': 'Embedded_Viewer',
                                'source_url': url
                            }
                            pdf_data.append(pdf_info)
                            self.pdf_links[page_name]['Embedded_Viewer'].append(pdf_info)
                    
        except Exception as e:
            logger.error(f"Error processing page content {url}: {e}")
        
        return pdf_data
    
    def get_all_internal_links(self, url, retries=3):
        """Get all internal links from a page"""
        internal_links = set()
        
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                break  # Success
            except (Timeout, ConnectionError, RequestException, TimeoutError, SocketTimeout, OSError) as e:
                if attempt < retries - 1:
                    logger.debug(f"Retry getting links from {url}...")
                    time.sleep(2)
                    continue
                else:
                    logger.error(f"Failed to get links from {url} after {retries} attempts")
                    return internal_links
            except Exception as e:
                logger.error(f"Error getting links from {url}: {e}")
                return internal_links
        
        try:
            
            for link in soup.find_all('a', href=True):
                href = link['href']
                full_url = urljoin(url, href)
                
                # Check if it's an internal link
                if full_url.startswith(self.base_url):
                    # Skip non-page links
                    if not any(ext in full_url.lower() for ext in ['.pdf', '.jpg', '.png', '.gif', '.jpeg', 'javascript:', '#']):
                        internal_links.add(full_url)
                        
        except Exception as e:
            logger.error(f"Error getting links from {url}: {e}")
        
        return internal_links
    
    def crawl_website(self, max_pages=100):
        """Crawl the website to find all PDF links"""
        logger.info("Starting website crawl...")
        to_visit = {self.base_url}
        visited = set()
        
        while to_visit and len(visited) < max_pages:
            url = to_visit.pop()
            if url in visited:
                continue
            
            visited.add(url)
            
            # Get PDF links from this page
            self.get_pdf_links_from_page(url)
            
            # Get more internal links to crawl
            new_links = self.get_all_internal_links(url)
            to_visit.update(new_links - visited)
            
            time.sleep(0.5)  # Be polite to the server
        
        logger.info(f"Crawled {len(visited)} pages")
        return self.pdf_links
    
    def download_pdf(self, pdf_info):
        """Download a single PDF"""
        url = pdf_info['url']
        
        if url in self.downloaded_pdfs:
            return None
        
        # Create folder structure: output_dir/page_name/heading/
        page_folder = os.path.join(self.output_dir, pdf_info['page'])
        heading_folder = os.path.join(page_folder, pdf_info['heading'])
        os.makedirs(heading_folder, exist_ok=True)
        
        # Generate unique filename
        base_name = pdf_info['name']
        filename = f"{base_name}.pdf"
        filepath = os.path.join(heading_folder, filename)
        
        # Handle duplicates
        counter = 1
        while os.path.exists(filepath):
            filename = f"{base_name}_{counter}.pdf"
            filepath = os.path.join(heading_folder, filename)
            counter += 1
        
        try:
            logger.info(f"Downloading: {pdf_info['name']}")
            response = self.session.get(url, timeout=60, stream=True)
            response.raise_for_status()
            
            # Check if it's actually a PDF
            content_type = response.headers.get('Content-Type', '')
            if 'pdf' not in content_type.lower() and not url.lower().endswith('.pdf'):
                # Try to detect from content
                first_bytes = response.content[:5]
                if first_bytes != b'%PDF-':
                    logger.warning(f"Skipping non-PDF: {url}")
                    return None
            
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            self.downloaded_pdfs.add(url)
            logger.info(f"Downloaded: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to download {url}: {e}")
            self.failed_downloads.append({'url': url, 'error': str(e), 'info': pdf_info})
            return None
    
    def download_all_pdfs(self, max_workers=5):
        """Download all found PDFs"""
        # Collect all PDFs
        all_pdfs = []
        for page, headings in self.pdf_links.items():
            for heading, pdfs in headings.items():
                all_pdfs.extend(pdfs)
        
        # Remove duplicates by URL
        unique_pdfs = {}
        for pdf in all_pdfs:
            if pdf['url'] not in unique_pdfs:
                unique_pdfs[pdf['url']] = pdf
        
        pdfs_to_download = list(unique_pdfs.values())
        total = len(pdfs_to_download)
        logger.info(f"Found {total} unique PDFs to download")
        
        downloaded = 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {executor.submit(self.download_pdf, pdf): pdf for pdf in pdfs_to_download}
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    downloaded += 1
                    logger.info(f"Progress: {downloaded}/{total}")
                time.sleep(0.3)  # Be polite to the server
        
        return downloaded
    
    def save_index(self):
        """Save an index of all PDFs found"""
        index_path = os.path.join(self.output_dir, "pdf_index.json")
        
        # Convert defaultdict to regular dict for JSON
        index_data = {
            'total_pdfs': sum(len(pdfs) for headings in self.pdf_links.values() for pdfs in headings.values()),
            'pages': {}
        }
        
        for page, headings in self.pdf_links.items():
            index_data['pages'][page] = {}
            for heading, pdfs in headings.items():
                index_data['pages'][page][heading] = [
                    {
                        'name': pdf['name'],
                        'url': pdf['url'],
                        'link_text': pdf['link_text']
                    } for pdf in pdfs
                ]
        
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Index saved to: {index_path}")
        
        # Also save a readable text summary
        summary_path = os.path.join(self.output_dir, "pdf_summary.txt")
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write("NMC Website PDF Download Summary\n")
            f.write("=" * 50 + "\n\n")
            
            for page, headings in sorted(self.pdf_links.items()):
                f.write(f"\n📁 {page}\n")
                f.write("-" * 40 + "\n")
                
                for heading, pdfs in sorted(headings.items()):
                    f.write(f"\n  📂 {heading}\n")
                    for pdf in pdfs:
                        f.write(f"    📄 {pdf['name']}\n")
                        if pdf['link_text']:
                            f.write(f"       Text: {pdf['link_text'][:100]}\n")
        
        logger.info(f"Summary saved to: {summary_path}")
    
    def run(self, max_pages=100, download=True):
        """Main method to crawl and download"""
        print("\n" + "=" * 60)
        print("NMC Website PDF Downloader")
        print("=" * 60 + "\n")
        
        # Create output directory
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Crawl website
        print("Step 1: Crawling website for PDF links...")
        self.crawl_website(max_pages=max_pages)
        
        # Save index
        print("\nStep 2: Saving PDF index...")
        self.save_index()
        
        if download:
            # Download PDFs
            print("\nStep 3: Downloading PDFs...")
            downloaded = self.download_all_pdfs()
            print(f"\nDownloaded {downloaded} PDFs")
            
            if self.failed_downloads:
                print(f"Failed: {len(self.failed_downloads)} PDFs")
                failed_path = os.path.join(self.output_dir, "failed_downloads.json")
                with open(failed_path, 'w', encoding='utf-8') as f:
                    json.dump(self.failed_downloads, f, indent=2, ensure_ascii=False)
                print(f"Failed downloads saved to: {failed_path}")
        
        print("\n" + "=" * 60)
        print("DONE!")
        print(f"PDFs saved to: {os.path.abspath(self.output_dir)}")
        print("=" * 60 + "\n")


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Download PDFs from NMC website')
    parser.add_argument('--output', '-o', default='NMC_PDFs', help='Output directory')
    parser.add_argument('--max-pages', '-m', type=int, default=400, help='Maximum pages to crawl (default: 400)')
    parser.add_argument('--scan-only', '-s', action='store_true', help='Only scan, do not download')
    
    args = parser.parse_args()
    
    downloader = NMCPDFDownloader(output_dir=args.output)
    downloader.run(max_pages=args.max_pages, download=not args.scan_only)


if __name__ == "__main__":
    main()
