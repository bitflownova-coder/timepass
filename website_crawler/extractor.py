from bs4 import BeautifulSoup
from markdownify import markdownify as md
from urllib.parse import urljoin
import os

class Extractor:
    def __init__(self, base_url):
        self.base_url = base_url

    def extract_text_content(self, html):
        """
        Extracts structured text content from HTML and converts it to Markdown.
        Includes titles, headers, paragraphs, lists, and tables.
        """
        soup = BeautifulSoup(html, 'html.parser')

        # Remove unwanted elements
        for script in soup(["script", "style", "nav", "footer", "iframe", "noscript"]):
            script.extract()

        # Convert to Markdown
        # heading_style="ATX" ensures # for headers
        markdown_content = md(str(soup), heading_style="ATX")
        
        # Post-processing cleanup (optional, to remove excessive newlines)
        markdown_content = "\n".join([line for line in markdown_content.splitlines() if line.strip()])
        
        return markdown_content

    def extract_metadata(self, html):
        """Extracts page title and description."""
        soup = BeautifulSoup(html, 'html.parser')
        
        title = "No Title"
        if soup.title and soup.title.string:
            title = soup.title.string
        
        meta_desc = soup.find("meta", attrs={"name": "description"})
        description = meta_desc.get("content", "") if meta_desc else ""
        
        return {
            "title": str(title).strip(),
            "description": str(description).strip()
        }

    def extract_links_and_assets(self, html, current_url):
        """
        Extracts internal links for crawling and assets (images, docs) for downloading.
        """
        soup = BeautifulSoup(html, 'html.parser')
        internal_links = set()
        assets = []

        # Extract Links
        for a in soup.find_all('a', href=True):
            href = a['href']
            full_url = urljoin(current_url, href)
            # We will filter domains in the crawler, just return full URL here
            internal_links.add(full_url)

        # Extract Images
        for img in soup.find_all('img', src=True):
            src = img['src']
            full_url = urljoin(current_url, src)
            assets.append({"type": "image", "url": full_url})

        # Extract Documents (based on common extensions)
        doc_extensions = ['.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt', '.txt', '.zip', '.csv']
        for a in soup.find_all('a', href=True):
            href = a['href']
            full_url = urljoin(current_url, href)
            ext = os.path.splitext(full_url)[1].lower()
            if ext in doc_extensions:
                assets.append({"type": "document", "url": full_url})

        return internal_links, assets
