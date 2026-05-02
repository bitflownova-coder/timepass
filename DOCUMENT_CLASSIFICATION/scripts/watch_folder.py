import argparse
import hashlib
import json
import os
import threading
import time
from pathlib import Path

import requests
from dotenv import load_dotenv
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


def _load_env():
    load_dotenv()


def _split_list(value: str, sep: str = ';') -> list[str]:
    if not value:
        return []
    return [v.strip() for v in value.split(sep) if v.strip()]


def _is_hidden(path: Path) -> bool:
    return any(part.startswith('.') for part in path.parts)


def _allowed_ext(path: Path, exts: set[str]) -> bool:
    return path.suffix.lower().lstrip('.') in exts


def _compute_hash(path: Path) -> str:
    sha = hashlib.sha256()
    with path.open('rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            sha.update(chunk)
    return sha.hexdigest()


def _wait_ready(path: Path, timeout: float = 10.0) -> bool:
    start = time.time()
    last_size = -1
    while time.time() - start < timeout:
        try:
            size = path.stat().st_size
        except FileNotFoundError:
            return False
        if size == last_size:
            return True
        last_size = size
        time.sleep(0.5)
    return False


class UploadClient:
    def __init__(self, api_base: str, email: str | None, password: str | None,
                 token: str | None):
        self.api_base = api_base.rstrip('/')
        self.email = email
        self.password = password
        self.token = token

    def _login(self) -> bool:
        if not self.email or not self.password:
            return False
        try:
            resp = requests.post(
                f"{self.api_base}/api/auth/login",
                json={"email": self.email, "password": self.password},
                timeout=15,
            )
            if resp.ok:
                data = resp.json()
                self.token = data.get('token')
                return bool(self.token)
        except Exception:
            return False
        return False

    def _auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}"} if self.token else {}

    def upload(self, path: Path) -> tuple[bool, str, int | None]:
        """Upload a new file. Returns (success, message, doc_id)."""
        if not self.token and not self._login():
            return False, "Login failed", None
        try:
            with path.open('rb') as f:
                resp = requests.post(
                    f"{self.api_base}/api/upload",
                    files={"file": (path.name, f)},
                    headers=self._auth_headers(),
                    timeout=60,
                )
            if resp.status_code in (200, 201):
                doc_id = None
                try:
                    doc_id = resp.json().get('document', {}).get('id')
                except Exception:
                    pass
                return True, resp.text, doc_id
            if resp.status_code == 401:
                if self._login():
                    return self.upload(path)
            return False, resp.text, None
        except Exception as exc:
            return False, str(exc), None

    def reprocess(self, doc_id: int) -> tuple[bool, str]:
        """Ask the server to re-extract and re-classify an existing document."""
        if not self.token and not self._login():
            return False, "Login failed"
        try:
            resp = requests.post(
                f"{self.api_base}/api/documents/{doc_id}/reprocess",
                json={"force": True},
                headers=self._auth_headers(),
                timeout=60,
            )
            if resp.status_code == 200:
                return True, resp.text
            if resp.status_code == 401:
                if self._login():
                    return self.reprocess(doc_id)
            return False, resp.text
        except Exception as exc:
            return False, str(exc)


class Watcher:
    def __init__(self, client: UploadClient, exts: set[str], cache_path: Path):
        self.client = client
        self.exts = exts
        self.cache_path = cache_path
        self.cache = self._load_cache()
        self.recent: dict[str, float] = {}
        self._retry_queue: list[dict] = []  # [{path_or_doc_id, retries, next_attempt_ts, action}]

    def _load_cache(self) -> dict:
        if not self.cache_path.exists():
            return {"hashes": {}}
        try:
            return json.loads(self.cache_path.read_text(encoding='utf-8'))
        except Exception:
            return {"hashes": {}}

    def _save_cache(self):
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(json.dumps(self.cache, indent=2), encoding='utf-8')

    def _seen_recently(self, path: Path) -> bool:
        key = str(path)
        now = time.time()
        last = self.recent.get(key, 0)
        if now - last < 5:
            return True
        self.recent[key] = now
        return False

    def _flush_retry_queue(self):
        """Attempt pending retries whose next_attempt_ts is due."""
        now = time.time()
        still_pending = []
        for item in self._retry_queue:
            if now < item['next_attempt_ts']:
                still_pending.append(item)
                continue
            action = item.get('action', 'upload')
            retries = item['retries']
            if action == 'upload':
                path = Path(item['path'])
                ok, msg, doc_id = self.client.upload(path)
                if ok:
                    print(f"[retry-ok] upload {path.name} after {retries} retries")
                    file_hash = _compute_hash(path)
                    entry = {"path": str(path), "uploaded_at": time.strftime('%Y-%m-%dT%H:%M:%S')}
                    if doc_id is not None:
                        entry["doc_id"] = doc_id
                    self.cache.setdefault("hashes", {})[file_hash] = entry
                    self._save_cache()
                else:
                    if retries < 3:
                        delay = [30, 60, 120][retries]
                        item['retries'] += 1
                        item['next_attempt_ts'] = now + delay
                        still_pending.append(item)
                    else:
                        print(f"[retry-drop] upload {item['path']} failed after 3 retries")
            elif action == 'reprocess':
                doc_id = item['doc_id']
                ok, msg = self.client.reprocess(doc_id)
                if ok:
                    print(f"[retry-ok] reprocess doc {doc_id} after {retries} retries")
                else:
                    if retries < 3:
                        delay = [30, 60, 120][retries]
                        item['retries'] += 1
                        item['next_attempt_ts'] = now + delay
                        still_pending.append(item)
                    else:
                        print(f"[retry-drop] reprocess doc {doc_id} failed after 3 retries")
        self._retry_queue = still_pending

    def handle(self, path: Path):
        self._flush_retry_queue()
        if _is_hidden(path):
            return
        if path.name.startswith('~$') or path.name.endswith('.tmp'):
            return
        if not _allowed_ext(path, self.exts):
            return
        if self._seen_recently(path):
            return
        if not _wait_ready(path):
            return

        file_hash = _compute_hash(path)
        if file_hash in self.cache.get("hashes", {}):
            return

        ok, msg, doc_id = self.client.upload(path)
        if ok:
            entry = {
                "path": str(path),
                "uploaded_at": time.strftime('%Y-%m-%dT%H:%M:%S'),
            }
            if doc_id is not None:
                entry["doc_id"] = doc_id
            self.cache.setdefault("hashes", {})[file_hash] = entry
            self._save_cache()
        else:
            print(f"Upload failed: {path} -> {msg}")
            self._retry_queue.append({
                'action': 'upload',
                'path': str(path),
                'retries': 1,
                'next_attempt_ts': time.time() + 30,
            })

    def handle_modified(self, path: Path):
        """Called when an existing watched file is modified.

        Computes the new hash, checks if content actually changed,
        and if so calls reprocess on the API using the cached doc_id.
        """
        if _is_hidden(path):
            return
        if path.name.startswith('~$') or path.name.endswith('.tmp'):
            return
        if not _allowed_ext(path, self.exts):
            return
        if self._seen_recently(path):
            return
        if not _wait_ready(path):
            return

        new_hash = _compute_hash(path)
        hashes = self.cache.get("hashes", {})

        # Find the old cache entry for this path (reverse lookup by path)
        old_hash = None
        for h, meta in hashes.items():
            if meta.get("path") == str(path):
                old_hash = h
                break

        if old_hash is None:
            # Never uploaded before — treat as new
            self.handle(path)
            return

        if new_hash == old_hash:
            return  # content unchanged

        old_entry = hashes[old_hash]
        doc_id = old_entry.get("doc_id")
        if not doc_id:
            print(f"[modified] {path.name}: hash changed but no doc_id in cache — re-uploading")
            del hashes[old_hash]
            self._save_cache()
            self.handle(path)
            return

        print(f"[modified] {path.name}: hash changed → reprocessing doc {doc_id}")
        ok, msg = self.client.reprocess(doc_id)
        if ok:
            # Update cache to track the new hash
            del hashes[old_hash]
            hashes[new_hash] = {
                "path": str(path),
                "uploaded_at": old_entry.get("uploaded_at"),
                "reprocessed_at": time.strftime('%Y-%m-%dT%H:%M:%S'),
                "doc_id": doc_id,
            }
            self._save_cache()
        else:
            print(f"Reprocess failed: {path} -> {msg}")
            self._retry_queue.append({
                'action': 'reprocess',
                'doc_id': doc_id,
                'retries': 1,
                'next_attempt_ts': time.time() + 30,
            })


class Handler(FileSystemEventHandler):
    def __init__(self, watcher: Watcher):
        self.watcher = watcher

    def on_created(self, event):
        if event.is_directory:
            return
        self.watcher.handle(Path(event.src_path))

    def on_moved(self, event):
        if event.is_directory:
            return
        self.watcher.handle(Path(event.dest_path))

    def on_modified(self, event):
        if event.is_directory:
            return
        self.watcher.handle_modified(Path(event.src_path))


def _scan_existing(paths: list[Path], watcher: Watcher):
    for root in paths:
        for p in root.rglob('*'):
            if p.is_file():
                watcher.handle(p)


def main() -> int:
    _load_env()

    parser = argparse.ArgumentParser(description="Watch a folder and auto-upload files")
    parser.add_argument("--dir", action="append", help="Directory to watch")
    parser.add_argument("--api", default=os.getenv("WATCH_API", "http://localhost:5000"))
    parser.add_argument("--email", default=os.getenv("WATCH_EMAIL"))
    parser.add_argument("--password", default=os.getenv("WATCH_PASSWORD"))
    parser.add_argument("--token", default=os.getenv("WATCH_TOKEN"))
    parser.add_argument("--exts", default=os.getenv("WATCH_EXTS", "pdf,docx,doc,txt,jpg,jpeg,png,gif,bmp,webp"))
    parser.add_argument("--scan-existing", action="store_true")
    parser.add_argument("--recursive", action="store_true")
    parser.add_argument("--auto-discover", action="store_true",
                        help="Automatically add ~/Downloads, ~/Desktop, ~/Documents to watch list")
    parser.add_argument("--scan-interval", type=int, default=0, metavar="SECONDS",
                        help="Periodically re-scan watch directories every N seconds (0 = disabled)")
    args = parser.parse_args()

    dirs = args.dir or _split_list(os.getenv("WATCH_DIRS", ""))

    # ── --auto-discover: add well-known OS folders ────────────────────────────
    if args.auto_discover:
        home = Path.home()
        auto_dirs = [home / "Downloads", home / "Desktop", home / "Documents"]
        for d in auto_dirs:
            if d.exists() and str(d) not in dirs:
                dirs.append(str(d))
                print(f"[auto-discover] Added {d}")

    if not dirs:
        print("No watch directory provided. Use --dir, WATCH_DIRS, or --auto-discover.")
        return 1

    exts = {e.strip().lower() for e in args.exts.split(',') if e.strip()}
    client = UploadClient(args.api, args.email, args.password, args.token)

    cache_path = Path('data') / 'watcher_cache.json'
    watcher = Watcher(client, exts, cache_path)

    watch_paths = [Path(d).expanduser().resolve() for d in dirs]
    handler = Handler(watcher)
    observer = Observer()

    for p in watch_paths:
        if not p.exists():
            print(f"Watch path missing: {p}")
            continue
        observer.schedule(handler, str(p), recursive=args.recursive)

    if args.scan_existing:
        _scan_existing(watch_paths, watcher)

    # ── --scan-interval: periodic rescan via threading.Timer ─────────────────
    _rescan_timer: list[threading.Timer] = []

    def _schedule_rescan():
        if args.scan_interval and args.scan_interval > 0:
            t = threading.Timer(args.scan_interval, _do_rescan)
            t.daemon = True
            t.start()
            _rescan_timer.clear()
            _rescan_timer.append(t)

    def _do_rescan():
        print(f"[rescan] Periodic scan triggered (interval={args.scan_interval}s)")
        _scan_existing(watch_paths, watcher)
        _schedule_rescan()

    _schedule_rescan()

    observer.start()
    print("Watching:")
    for p in watch_paths:
        print(f"- {p}")

    # ── Token expiry pre-emptive refresh (every 20 min) ───────────────────────
    _TOKEN_REFRESH_INTERVAL = 20 * 60  # seconds
    _last_refresh = time.time()

    try:
        while True:
            time.sleep(1)
            # Pre-emptively refresh token before it expires
            if (client.email and client.password
                    and time.time() - _last_refresh > _TOKEN_REFRESH_INTERVAL):
                if client._login():
                    _last_refresh = time.time()
                    print("[token] Token refreshed pre-emptively")
    except KeyboardInterrupt:
        observer.stop()
        for t in _rescan_timer:
            t.cancel()
    observer.join()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
