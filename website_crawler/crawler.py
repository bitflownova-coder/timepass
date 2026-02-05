import os
import requests
import time
import threading
from collections import deque
from playwright.sync_api import sync_playwright
from utils import normalize_url, get_domain, get_safe_filename, save_text_file, save_binary_file
from extractor import Extractor

class Crawler:
    def __init__(self, start_url, output_dir, max_depth=2):
        self.start_url = normalize_url(start_url)
        self.output_dir = output_dir
        self.max_depth = max_depth
        self.domain = get_domain(self.start_url)
        self.visited = set()
        self.queue = deque([(self.start_url, 0)]) # (url, depth)
        self.extractor = Extractor(self.start_url)
        
        # Directories
        self.content_dir = os.path.join(output_dir, "content")
        self.images_dir = os.path.join(output_dir, "images")
        self.docs_dir = os.path.join(output_dir, "documents")
        
        # Control Flags
        self.pause_event = threading.Event()
        self.pause_event.set() # Set to True means "running", False means "paused"
        self.stopped = False
        
        self._init_dirs()

    def _init_dirs(self):
        os.makedirs(self.content_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.docs_dir, exist_ok=True)

    def pause(self):
        self.pause_event.clear()

    def resume(self):
        self.pause_event.set()

    def stop(self):
        self.stopped = True
        self.pause_event.set() # Ensure we don't get stuck in wait()

    def download_asset(self, url, asset_type):
        """Downloads an asset (image or doc)."""
        try:
            filename = os.path.basename(url).split("?")[0]
            if not filename:
                return
            
            # Prevent overwriting or collision
            save_path = os.path.join(self.images_dir if asset_type == 'image' else self.docs_dir, filename)
            
            # Simple check if already exists to skip re-download logic could be added here
            if os.path.exists(save_path):
                return

            response = requests.get(url, stream=True, timeout=10)
            if response.status_code == 200:
                save_binary_file(save_path, response.content)
        except Exception as e:
            # print(f"Failed to download {url}: {e}")
            pass

    def run(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            print(f"Starting crawl at {self.start_url} (Max Depth: {self.max_depth})")

            while self.queue:
                # Check for Stop
                if self.stopped:
                    print("Crawl stopped by user.")
                    break

                # Check for Pause
                self.pause_event.wait() # Blocks if clear() was called

                current_url, depth = self.queue.popleft()
                
                if current_url in self.visited:
                    continue
                
                # Check if depth exceeded
                if depth > self.max_depth:
                    continue
                
                self.visited.add(current_url)
                print(f"Visiting [{depth}]: {current_url}")

                try:
                    # Navigate
                    page.goto(current_url, timeout=60000, wait_until="domcontentloaded")
                    
                    # Extract Content
                    html = page.content()
                    
                    # 1. Text Content
                    markdown = self.extractor.extract_text_content(html)
                    metadata = self.extractor.extract_metadata(html)
                    
                    # Prepend metadata
                    full_content = f"# {metadata['title']}\n\n**Description:** {metadata['description']}\n\n**URL:** {current_url}\n\n---\n\n{markdown}"
                    
                    safe_name = get_safe_filename(current_url)
                    save_text_file(os.path.join(self.content_dir, f"{safe_name}.md"), full_content)

                    # 2. Extract and Download Assets
                    links, assets = self.extractor.extract_links_and_assets(html, current_url)
                    
                    for asset in assets:
                        if self.stopped: break
                        self.download_asset(asset['url'], asset['type'])

                    # 3. Enqueue Links
                    if depth < self.max_depth:
                        for link in links:
                            normalized_link = normalize_url(link)
                            
                            # Domain constraint
                            if get_domain(normalized_link) == self.domain:
                                if normalized_link not in self.visited:
                                    self.queue.append((normalized_link, depth + 1))
                            
                except Exception as e:
                    print(f"Error processing {current_url}: {e}")

            browser.close()
            print("Crawling complete.")
