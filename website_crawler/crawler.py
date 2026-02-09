import os
import asyncio
import re
import random
import time
import httpx
from playwright.async_api import async_playwright
from fake_useragent import UserAgent
from database import DatabaseManager
from extractor import Extractor
from utils import normalize_url, get_domain, get_safe_filename, save_text_file, save_binary_file

class AsyncCrawler:
    def __init__(self, crawl_id, output_dir, db_manager: DatabaseManager, config=None):
        self.crawl_id = crawl_id
        self.output_dir = output_dir
        self.db = db_manager
        self.config = config or {}
        
        # Config Extraction
        self.max_depth = self.config.get('depth', 2)
        self.concurrency = self.config.get('concurrency', 3)
        self.delay = self.config.get('delay', 1)  # Seconds between requests per worker
        self.proxy = self.config.get('proxy', None)
        self.allow_regex = self.config.get('allow_regex', None)
        self.deny_regex = self.config.get('deny_regex', None)
        self.user_agent_strategy = self.config.get('user_agent_strategy', 'random')
        
        # State
        self.running = False
        self.paused_event = asyncio.Event()
        self.paused_event.set()
        self.stop_signal = False
        
        # Directories
        self.content_dir = os.path.join(output_dir, "content")
        self.images_dir = os.path.join(output_dir, "images")
        self.docs_dir = os.path.join(output_dir, "documents")
        self._init_dirs()
        
        self.ua = UserAgent()

    def _init_dirs(self):
        os.makedirs(self.content_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)
        os.makedirs(self.docs_dir, exist_ok=True)

    def _get_user_agent(self):
        if self.user_agent_strategy == 'random':
            return self.ua.random
        return "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"

    def _is_url_allowed(self, url):
        if self.allow_regex and not re.search(self.allow_regex, url):
            return False
        if self.deny_regex and re.search(self.deny_regex, url):
            return False
        return True

    async def _download_asset(self, url, asset_type):
        try:
            filename = os.path.basename(url.split("?")[0])
            if not filename: return
            
            # Basic validation
            if len(filename) > 100: filename = filename[:100] # truncate
            
            save_path = os.path.join(self.images_dir if asset_type == 'image' else self.docs_dir, filename)
            if os.path.exists(save_path): return

            async with httpx.AsyncClient() as client:
                resp = await client.get(url, timeout=10)
                if resp.status_code == 200:
                    # Offload file writing to blocking thread to keep loop happy
                    await asyncio.to_thread(save_binary_file, save_path, resp.content)
        except Exception:
            pass # Ignore asset failures

    async def process_page(self, context, queue_item):
        queue_id = queue_item['id']
        url = queue_item['url']
        depth = queue_item['depth']
        
        try:
            print(f"[{self.crawl_id}] Processing: {url}")
            page = await context.new_page()
            
            # Goto
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # Extract
            content = await page.content()
            extractor = Extractor(url)
            
            # 1. Text
            # Run CPU-bound extraction in thread
            markdown = await asyncio.to_thread(extractor.extract_text_content, content)
            metadata = await asyncio.to_thread(extractor.extract_metadata, content)
            
            full_content = f"# {metadata['title']}\n\n**Description:** {metadata['description']}\n\n**URL:** {url}\n\n---\n\n{markdown}"
            safe_name = get_safe_filename(url)
            await asyncio.to_thread(save_text_file, os.path.join(self.content_dir, f"{safe_name}.md"), full_content)

            # 2. Assets & Links
            links, assets = await asyncio.to_thread(extractor.extract_links_and_assets, content, url)
            
            # Download assets (fire and forget or parallel await)
            # We'll spawn tasks for assets so we don't block the page processing too much
            for asset in assets:
                 asyncio.create_task(self._download_asset(asset['url'], asset['type']))

            # 3. Add Links to Queue
            if depth < self.max_depth:
                current_domain = get_domain(url)
                for link in links:
                    normalized = normalize_url(link)
                    if get_domain(normalized) == current_domain:
                        if self._is_url_allowed(normalized):
                            self.db.add_url_to_queue(self.crawl_id, normalized, depth + 1)
            
            await page.close()
            self.db.mark_url_complete(queue_id, success=True)
            self.db.mark_visited(self.crawl_id, url)
            
        except Exception as e:
            print(f"Error processing {url}: {e}")
            self.db.mark_url_complete(queue_id, success=False)
            if 'page' in locals(): await page.close()

    async def run(self):
        print(f"[{self.crawl_id}] Async Crawler Started")
        
        async with async_playwright() as p:
            # Launch Browser
            config_options = {"headless": True}
            if self.proxy:
               config_options["proxy"] = {"server": self.proxy} 
            
            browser = await p.chromium.launch(**config_options)
            
            # Create Context with User Agent
            context = await browser.new_context(user_agent=self._get_user_agent())
            
            # Main Loop
            try:
                active_tasks = set()
                
                while True:
                    if self.stop_signal:
                        break
                    
                    await self.paused_event.wait()
                    
                    # Fill concurrency slots
                    while len(active_tasks) < self.concurrency:
                        item = self.db.get_next_url(self.crawl_id)
                        if not item:
                            # Queue empty? Check if tasks running.
                            if not active_tasks:
                                # REALLY empty? Double check pending count just in case
                                if self.db.get_pending_count(self.crawl_id) == 0:
                                    self.stop_signal = True # Finished
                                break
                            break # Wait for tasks to finish to potentially spawn new links
                        
                        # Create task
                        task = asyncio.create_task(self.process_page(context, item))
                        active_tasks.add(task)
                        task.add_done_callback(active_tasks.discard)
                        
                        # Apply Politeness Delay between dispatching new page loads
                        await asyncio.sleep(self.delay)
                        
                    if self.stop_signal:
                        break
                        
                    # Wait for at least one task to complete or small sleep
                    if active_tasks:
                         # Wait either for a task to finish OR for 1 second check
                        done, pending = await asyncio.wait(active_tasks, timeout=1, return_when=asyncio.FIRST_COMPLETED)
                    else:
                        await asyncio.sleep(1) # Idle wait

            finally:
                await browser.close()
                timestamp = time.time()
                status = 'stopped' if self.stop_signal and self.db.get_pending_count(self.crawl_id) > 0 else 'completed'
                self.db.update_crawl_status(self.crawl_id, status)
                print(f"[{self.crawl_id}] Crawler finished with status: {status}")

    # Control Methods called from other threads
    def pause(self):
        self.paused_event.clear()

    def resume(self):
        self.paused_event.set()

    def stop(self):
        self.stop_signal = True
        self.paused_event.set() # Unblock wait
