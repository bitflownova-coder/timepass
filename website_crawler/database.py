import sqlite3
import json
import threading
import time

class DatabaseManager:
    def __init__(self, db_path="crawler.db"):
        self.db_path = db_path
        # SQLite connection must be thread-local if used in multiple threads, 
        # but for async we might need a different approach or just open/close per op.
        # For simplicity in this hybrid app, we'll use a lock and open fresh connections 
        # or use check_same_thread=False with a lock.
        self.lock = threading.Lock()
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path, check_same_thread=False)

    def _init_db(self):
        with self.lock:
            conn = self._get_conn()
            cursor = conn.cursor()
            
            # Crawls Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS crawls (
                    id TEXT PRIMARY KEY,
                    start_url TEXT,
                    max_depth INTEGER,
                    status TEXT,
                    created_at REAL,
                    config JSON
                )
            ''')
            
            # Queue Table
            # Status: pending, processing, completed, failed
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS queue (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    crawl_id TEXT,
                    url TEXT,
                    depth INTEGER,
                    status TEXT DEFAULT 'pending',
                    FOREIGN KEY(crawl_id) REFERENCES crawls(id)
                )
            ''')
            
            # Visited Table (Active set for each crawl)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS visited (
                    crawl_id TEXT,
                    url TEXT,
                    PRIMARY KEY (crawl_id, url)
                )
            ''')
            
            conn.commit()
            conn.close()

    def create_crawl(self, crawl_id, url, depth, config=None):
        with self.lock:
            conn = self._get_conn()
            conn.execute(
                "INSERT INTO crawls (id, start_url, max_depth, status, created_at, config) VALUES (?, ?, ?, ?, ?, ?)",
                (crawl_id, url, depth, 'pending', time.time(), json.dumps(config or {}))
            )
            # Add start URL to queue
            conn.execute(
                "INSERT INTO queue (crawl_id, url, depth, status) VALUES (?, ?, ?, ?)",
                (crawl_id, url, 0, 'pending')
            )
            conn.commit()
            conn.close()

    def get_crawl_status(self, crawl_id):
        with self.lock:
            conn = self._get_conn()
            cursor = conn.execute("SELECT status, config FROM crawls WHERE id = ?", (crawl_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return {'status': row[0], 'config': json.loads(row[1])}
            return None

    def get_crawl(self, crawl_id):
        with self.lock:
            conn = self._get_conn()
            cursor = conn.execute("SELECT id, start_url, max_depth, status, created_at, config FROM crawls WHERE id = ?", (crawl_id,))
            row = cursor.fetchone()
            conn.close()
            if row:
                return {
                    'id': row[0],
                    'url': row[1],
                    'depth': row[2],
                    'status': row[3],
                    'timestamp': row[4],
                    'config': json.loads(row[5])
                }
            return None

    def update_crawl_status(self, crawl_id, status):
        with self.lock:
            conn = self._get_conn()
            conn.execute("UPDATE crawls SET status = ? WHERE id = ?", (status, crawl_id))
            conn.commit()
            conn.close()

    def get_all_crawls(self):
        with self.lock:
            conn = self._get_conn()
            cursor = conn.execute("SELECT id, start_url, max_depth, status, created_at FROM crawls ORDER BY created_at DESC")
            rows = cursor.fetchall()
            conn.close()
            
            crawls = {}
            for r in rows:
                crawls[r[0]] = {
                    'id': r[0],
                    'url': r[1],
                    'depth': r[2],
                    'status': r[3],
                    'timestamp': r[4]
                }
            return crawls

    # Queue Operations
    def get_next_url(self, crawl_id):
        """Get next pending URL and mark it as processing."""
        with self.lock:
            conn = self._get_conn()
            # Find one pending
            cursor = conn.execute(
                "SELECT id, url, depth FROM queue WHERE crawl_id = ? AND status = 'pending' LIMIT 1", 
                (crawl_id,)
            )
            row = cursor.fetchone()
            
            if row:
                queue_id, url, depth = row
                conn.execute("UPDATE queue SET status = 'processing' WHERE id = ?", (queue_id,))
                conn.commit()
                conn.close()
                return {'url': url, 'depth': depth, 'id': queue_id}
            
            conn.close()
            return None

    def mark_url_complete(self, queue_id, success=True):
        status = 'completed' if success else 'failed'
        with self.lock:
            conn = self._get_conn()
            conn.execute("UPDATE queue SET status = ? WHERE id = ?", (status, queue_id))
            conn.commit()
            conn.close()

    def add_url_to_queue(self, crawl_id, url, depth):
        with self.lock:
            conn = self._get_conn()
            
            # Check if already visited or already in queue
            # (Optimization: In a massive crawler, we'd use a Bloom filter or similar, 
            # but for this scale, a DB check is fine)
            
            # Check visited
            res_visited = conn.execute("SELECT 1 FROM visited WHERE crawl_id = ? AND url = ?", (crawl_id, url)).fetchone()
            
            # Check queue (any status)
            res_queue = conn.execute("SELECT 1 FROM queue WHERE crawl_id = ? AND url = ?", (crawl_id, url)).fetchone()
            
            if not res_visited and not res_queue:
                conn.execute(
                    "INSERT INTO queue (crawl_id, url, depth, status) VALUES (?, ?, ?, ?)", 
                    (crawl_id, url, depth, 'pending')
                )
                conn.commit()
                return True
            
            conn.close()
            return False

    def mark_visited(self, crawl_id, url):
        with self.lock:
            conn = self._get_conn()
            conn.execute("INSERT OR IGNORE INTO visited (crawl_id, url) VALUES (?, ?)", (crawl_id, url))
            conn.commit()
            conn.close()

    def get_pending_count(self, crawl_id):
        with self.lock:
            conn = self._get_conn()
            res = conn.execute("SELECT COUNT(*) FROM queue WHERE crawl_id = ? AND status = 'pending'", (crawl_id,)).fetchone()
            conn.close()
            return res[0]
