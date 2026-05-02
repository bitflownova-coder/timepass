"""
Local File Indexer — Phase A
Scans folders on THIS PC, extracts text, stores metadata in SQLite.
Files are NEVER moved, copied, or encrypted — only indexed.
"""
import os
import hashlib
import logging
import threading
from datetime import datetime
from pathlib import Path

from app.utils.code_classifier import (
    CODE_EXTENSIONS, is_code_file, detect_language, project_info,
    read_code_text, should_skip_dir, reset_cache as reset_code_cache,
)

logger = logging.getLogger(__name__)

# File types we can extract text from (business docs + all code extensions)
SUPPORTED_EXTENSIONS = {
    '.pdf', '.docx', '.doc', '.txt', '.text', '.md',
    '.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp',
    '.xlsx', '.xls', '.csv', '.pptx', '.ppt',
    '.rtf', '.odt',
} | set(CODE_EXTENSIONS.keys())

# Folders to always skip
SKIP_FOLDERS = {
    'node_modules', '.git', '__pycache__', '.venv', 'venv',
    '$Recycle.Bin', 'System Volume Information', 'Windows',
    'ProgramData', 'AppData', '.idea', '.vs', 'dist', 'build',
    'target', 'vendor', '.next', '.nuxt', '.gradle', '.mvn',
    'bin', 'obj', 'out', '.pytest_cache', '.mypy_cache',
    '.ruff_cache', '.cache', '.terraform', 'coverage',
    # Additional system / non-user dirs
    'Program Files', 'Program Files (x86)', 'Recovery',
    '$WinREAgent', 'MSOCache', 'PerfLogs', 'boot',
    'drivers', 'WinSxS', 'SysWOW64', 'System32',
}

# Max file size to attempt text extraction (50 MB)
MAX_EXTRACT_SIZE = 50 * 1024 * 1024


def _file_hash(path: str) -> str:
    """SHA-256 of first 256 KB — fast, good enough for change detection."""
    h = hashlib.sha256()
    try:
        with open(path, 'rb') as f:
            h.update(f.read(256 * 1024))
    except Exception:
        pass
    return h.hexdigest()


def _extract_text(file_path: str) -> tuple[str, int | None]:
    """
    Extract text from a local file. Returns (text, page_count).
    Never raises — always returns ('', None) on failure.
    """
    ext = Path(file_path).suffix.lower()
    try:
        if ext == '.pdf':
            try:
                import pdfplumber
                text_parts = []
                pages = 0
                with pdfplumber.open(file_path) as pdf:
                    pages = len(pdf.pages)
                    for page in pdf.pages[:100]:  # cap at 100 pages
                        t = page.extract_text()
                        if t:
                            text_parts.append(t)
                return '\n'.join(text_parts), pages
            except Exception:
                import PyPDF2
                text_parts = []
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    pages = len(reader.pages)
                    for page in reader.pages[:100]:
                        t = page.extract_text()
                        if t:
                            text_parts.append(t)
                return '\n'.join(text_parts), pages

        elif ext in ('.docx',):
            from docx import Document as DocxDoc
            doc = DocxDoc(file_path)
            return '\n'.join(p.text for p in doc.paragraphs), None

        elif ext in ('.txt', '.text', '.md', '.csv', '.rtf'):
            for enc in ('utf-8', 'latin-1', 'cp1252'):
                try:
                    with open(file_path, 'r', encoding=enc) as f:
                        return f.read(500_000), None  # cap at 500 KB chars
                except UnicodeDecodeError:
                    continue
            return '', None

        elif ext in ('.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp', '.gif'):
            try:
                import pytesseract
                from PIL import Image
                img = Image.open(file_path)
                return pytesseract.image_to_string(img), None
            except Exception:
                return '', None

        elif ext in ('.xlsx', '.xls'):
            try:
                import openpyxl
                wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
                parts = []
                for ws in wb.worksheets:
                    for row in ws.iter_rows(values_only=True):
                        parts.append(' '.join(str(c) for c in row if c is not None))
                return '\n'.join(parts), None
            except Exception:
                return '', None

    except Exception as e:
        logger.debug(f"Text extraction failed for {file_path}: {e}")
    return '', None


def _classify(text: str, filename: str):
    """Quick TF-IDF classification. Returns (label, confidence) or (None, None)."""
    try:
        from app.utils.classifier import DocumentClassifier
        clf = DocumentClassifier()
        if not clf.is_trained():
            return None, None
        label, conf, _ = clf.predict(text or filename)
        return label, conf
    except Exception:
        return None, None


# ─────────────────────────────────────────────────────────────────
# Core indexing functions
# ─────────────────────────────────────────────────────────────────

def index_file(file_path: str, user_id: int, db, force: bool = False) -> dict:
    """
    Index a single file. Skips if already indexed with same hash (unless force=True).
    Returns a result dict with keys: status, id, error.
    """
    from app.models.indexed_file import IndexedFile

    file_path = os.path.abspath(file_path)
    p = Path(file_path)

    if not p.exists() or not p.is_file():
        return {'status': 'skipped', 'reason': 'not a file'}

    ext = p.suffix.lower()
    if ext not in SUPPORTED_EXTENSIONS:
        return {'status': 'skipped', 'reason': 'unsupported type'}

    file_size = p.stat().st_size
    if file_size > MAX_EXTRACT_SIZE:
        return {'status': 'skipped', 'reason': 'too large'}

    mtime = datetime.utcfromtimestamp(p.stat().st_mtime)
    current_hash = _file_hash(file_path)

    # Check existing record
    existing = IndexedFile.query.filter_by(user_id=user_id, file_path=file_path).first()
    if existing and not force:
        if existing.file_hash == current_hash:
            # Update last_seen, mark not deleted
            existing.last_seen_at = datetime.utcnow()
            existing.is_deleted = False
            db.session.commit()
            return {'status': 'unchanged', 'id': existing.id}
        # Hash changed — re-index
        record = existing
    else:
        record = existing or IndexedFile(user_id=user_id, file_path=file_path)

    # ── Branch: code file vs business document ─────────────────────────
    code_file = is_code_file(file_path)

    if code_file:
        # Fast text read, no PDF/OCR libs, no DocumentClassifier.
        text = read_code_text(file_path)
        pages = None
        label, conf = 'Code', None
        proj_name, proj_root = project_info(file_path)
        record.is_code      = True
        record.project_name = proj_name
        record.project_root = proj_root
        record.language     = detect_language(file_path)
        record.client_name  = None
        record.doc_type     = None
        record.doc_year     = None
    else:
        text, pages = _extract_text(file_path)
        label, conf = _classify(text, p.name)
        record.is_code      = False
        record.project_name = None
        record.project_root = None
        record.language     = None

    record.user_id        = user_id
    record.file_path      = file_path
    record.filename       = p.name
    record.extension      = ext
    record.folder_path    = str(p.parent)
    record.file_size      = file_size
    record.file_hash      = current_hash
    record.modified_at    = mtime
    record.indexed_at     = datetime.utcnow()
    record.last_seen_at   = datetime.utcnow()
    record.extracted_text = text[:200_000] if text else ''   # cap at 200 K chars
    record.text_preview   = (text or '')[:500]
    record.page_count     = pages
    record.predicted_label   = label
    record.confidence_score  = conf
    record.index_status   = 'indexed'
    record.error_message  = None
    record.is_deleted     = False
    record.is_embedded    = False  # background pass will set True later

    if not existing:
        db.session.add(record)

    try:
        db.session.commit()
        _upsert_fts(record.id, p.name, text or '', db)
        # Auto-organize: classify business docs + generate VirtualPath rows
        try:
            from app.utils.local_indexer_organize import organize_indexed_file
            organize_indexed_file(record, text or '', user_id, db)
        except Exception as _e:
            logger.debug(f"Organize skipped for {file_path}: {_e}")
        return {'status': 'indexed', 'id': record.id}
    except Exception as e:
        db.session.rollback()
        logger.error(f"DB commit failed for {file_path}: {e}")
        return {'status': 'error', 'error': str(e)}


def _upsert_fts(record_id: int, filename: str, text: str, db):
    """Insert/replace row in FTS5 virtual table."""
    try:
        conn = db.engine.raw_connection()
        cur = conn.cursor()
        cur.execute('DELETE FROM file_fts WHERE rowid=?', (record_id,))
        cur.execute(
            'INSERT INTO file_fts(rowid, filename, body) VALUES (?,?,?)',
            (record_id, filename, text[:500_000])
        )
        conn.commit()
        conn.close()
    except Exception as e:
        logger.warning(f"FTS upsert failed for id={record_id}: {e}")


def scan_folder(folder_path: str, user_id: int, db,
                recursive: bool = True,
                progress_cb=None) -> dict:
    """
    Walk a folder and index every supported file.
    progress_cb(done, total, current_path) — called after each file.
    Returns summary dict.
    """
    from app.models.indexed_file import WatchedFolder

    folder_path = os.path.abspath(folder_path)
    if not os.path.isdir(folder_path):
        return {'success': False, 'error': 'Not a directory'}

    # Collect all files first so we know total count
    all_files = []
    walk = os.walk(folder_path) if recursive else [(folder_path, [], os.listdir(folder_path))]
    for root, dirs, files in walk:
        # Prune skip folders in-place so os.walk won't descend
        dirs[:] = [d for d in dirs if d not in SKIP_FOLDERS and not d.startswith('.')]
        for fname in files:
            fpath = os.path.join(root, fname)
            if Path(fpath).suffix.lower() in SUPPORTED_EXTENSIONS:
                all_files.append(fpath)

    stats = {'indexed': 0, 'unchanged': 0, 'skipped': 0, 'error': 0, 'total': len(all_files)}

    for i, fpath in enumerate(all_files):
        result = index_file(fpath, user_id, db)
        stats[result.get('status', 'error')] = stats.get(result.get('status', 'error'), 0) + 1
        if progress_cb:
            progress_cb(i + 1, len(all_files), fpath)

    # Update WatchedFolder record
    wf = WatchedFolder.query.filter_by(user_id=user_id, folder_path=folder_path).first()
    if wf:
        wf.last_scan_at = datetime.utcnow()
        wf.file_count   = stats['indexed'] + stats['unchanged']
        try:
            db.session.commit()
        except Exception:
            db.session.rollback()

    return {'success': True, **stats}


def scan_folder_async(folder_path: str, user_id: int, app, task_id: str):
    """
    Run scan_folder in a background thread via Flask app context.
    Progress stored in _scan_progress dict keyed by task_id.
    """
    from app.models import db as _db

    _scan_progress[task_id] = {'status': 'running', 'done': 0, 'total': 0, 'current': ''}

    def _run():
        with app.app_context():
            def cb(done, total, path):
                _scan_progress[task_id].update(done=done, total=total, current=path)

            result = scan_folder(folder_path, user_id, _db, progress_cb=cb)
            _scan_progress[task_id].update(status='done', result=result)

    t = threading.Thread(target=_run, daemon=True)
    t.start()


def get_all_drives() -> list:
    """Return all accessible root drive paths on this machine."""
    import string
    drives = []
    for letter in string.ascii_uppercase:
        root = f"{letter}:\\"
        if os.path.exists(root):
            drives.append(root)
    return drives


def scan_pc_async(user_id: int, app, task_id: str):
    """
    Scan every accessible drive on this PC in a background thread.
    Phases: discovery → indexing (parallel) → embedding (background) → done.
    Progress stored in _scan_progress keyed by task_id.
    """
    from app.models import db as _db
    from concurrent.futures import ThreadPoolExecutor, as_completed

    _scan_progress[task_id] = {
        'status': 'running', 'done': 0, 'total': 0,
        'current': 'Discovering drives…', 'phase': 'discovery',
        'indexed': 0, 'unchanged': 0, 'skipped': 0, 'error': 0,
    }
    progress_lock = threading.Lock()

    # Worker count — overridable via env var
    try:
        worker_count = int(os.environ.get('INDEX_WORKERS', '0')) or \
            min(8, max(4, (os.cpu_count() or 4) - 1))
    except ValueError:
        worker_count = 4

    def _run():
        with app.app_context():
            reset_code_cache()
            drives = get_all_drives()
            _scan_progress[task_id]['current'] = \
                f"Found {len(drives)} drive(s): {', '.join(drives)} — collecting files…"

            # ── Phase 1: collect all matching file paths ──────────────
            all_files = []
            for drive in drives:
                try:
                    for root, dirs, files in os.walk(drive):
                        dirs[:] = [
                            d for d in dirs
                            if d not in SKIP_FOLDERS and not d.startswith('.')
                        ]
                        for fname in files:
                            fpath = os.path.join(root, fname)
                            if Path(fpath).suffix.lower() in SUPPORTED_EXTENSIONS \
                               or fname == 'Dockerfile':
                                all_files.append(fpath)
                        with progress_lock:
                            _scan_progress[task_id]['current'] = f"Collecting: {root}"
                except Exception as e:
                    logger.warning(f"PC scan — skipped {drive}: {e}")

            total = len(all_files)
            with progress_lock:
                _scan_progress[task_id].update(
                    total=total, phase='indexing',
                    current=f"Found {total:,} files — indexing with {worker_count} workers…",
                )

            # ── Phase 2: index in parallel ─────────────────────────────
            def _worker(fpath: str) -> dict:
                # Each worker needs its own app context for thread-local
                # SQLAlchemy session. Flask-SQLAlchemy's scoped_session
                # gives one session per thread, which is what we want.
                with app.app_context():
                    try:
                        result = index_file(fpath, user_id, _db)
                    except Exception as e:
                        logger.error(f"Worker error on {fpath}: {e}")
                        result = {'status': 'error', 'error': str(e)}
                    finally:
                        try:
                            _db.session.remove()
                        except Exception:
                            pass
                return {'path': fpath, **result}

            done_count = 0
            with ThreadPoolExecutor(max_workers=worker_count) as pool:
                futures = {pool.submit(_worker, f): f for f in all_files}
                for fut in as_completed(futures):
                    res = fut.result()
                    done_count += 1
                    key = res.get('status', 'error')
                    with progress_lock:
                        prog = _scan_progress[task_id]
                        prog[key] = prog.get(key, 0) + 1
                        prog['done'] = done_count
                        prog['current'] = res.get('path', '')

            stats = {
                'indexed':   _scan_progress[task_id].get('indexed', 0),
                'unchanged': _scan_progress[task_id].get('unchanged', 0),
                'skipped':   _scan_progress[task_id].get('skipped', 0),
                'error':     _scan_progress[task_id].get('error', 0),
                'total':     total,
            }

            # ── Phase 3: background embedding (best-effort) ────────────
            with progress_lock:
                _scan_progress[task_id].update(
                    phase='embedding',
                    current='Building AI search index in background…',
                    embed_done=0, embed_total=0,
                )
            try:
                from app.utils.local_indexer_organize import embed_pending
                embed_pending(user_id, _db, app, task_id, _scan_progress, progress_lock)
            except Exception as e:
                logger.error(f"Embedding pass failed: {e}")

            with progress_lock:
                _scan_progress[task_id].update(status='done', result=stats, phase='done')

    t = threading.Thread(target=_run, daemon=True)
    t.start()


# In-memory scan progress store
_scan_progress: dict = {}


def get_scan_progress(task_id: str) -> dict:
    return _scan_progress.get(task_id, {'status': 'not_found'})


# ─────────────────────────────────────────────────────────────────
# FTS5 keyword search
# ─────────────────────────────────────────────────────────────────

def fts_search(query: str, user_id: int, db,
               ext_filter: str = None,
               folder_filter: str = None,
               limit: int = 50, offset: int = 0) -> list[dict]:
    """
    Full-text search using SQLite FTS5.
    Returns list of result dicts with snippet + file info.
    """
    from app.models.indexed_file import IndexedFile

    if not query or not query.strip():
        return []

    # Sanitise FTS query — escape special chars
    safe_q = query.strip().replace('"', '""')

    try:
        conn = db.engine.raw_connection()
        cur = conn.cursor()

        # FTS5 query with snippet
        sql = '''
            SELECT f.rowid,
                   snippet(file_fts, 1, "<mark>", "</mark>", "…", 20) AS snippet
            FROM file_fts f
            WHERE file_fts MATCH ?
            ORDER BY rank
            LIMIT ? OFFSET ?
        '''
        cur.execute(sql, (safe_q, limit, offset))
        rows = cur.fetchall()
        conn.close()
    except Exception as e:
        logger.error(f"FTS search error: {e}")
        return []

    if not rows:
        return []

    ids = [r[0] for r in rows]
    snippets = {r[0]: r[1] for r in rows}

    # Fetch full records
    records = IndexedFile.query.filter(
        IndexedFile.id.in_(ids),
        IndexedFile.user_id == user_id,
        IndexedFile.is_deleted == False,
    ).all()
    rec_map = {r.id: r for r in records}

    results = []
    for rid in ids:
        rec = rec_map.get(rid)
        if not rec:
            continue
        if ext_filter and rec.extension != ext_filter.lower():
            continue
        if folder_filter and folder_filter.lower() not in (rec.folder_path or '').lower():
            continue
        d = rec.to_dict()
        d['snippet'] = snippets.get(rid, '')
        results.append(d)

    return results


def ensure_fts_table(db):
    """Create the FTS5 virtual table if it doesn't exist (called at app startup)."""
    try:
        conn = db.engine.raw_connection()
        conn.execute('''
            CREATE VIRTUAL TABLE IF NOT EXISTS file_fts
            USING fts5(filename, body, content='', tokenize='porter ascii')
        ''')
        conn.commit()
        conn.close()
        logger.info("FTS5 table ready")
    except Exception as e:
        logger.error(f"FTS5 table creation failed: {e}")


def ensure_columns(db):
    """
    Lightweight SQLite migration: add columns introduced after initial install.
    Uses PRAGMA table_info to check what's already present, then ALTER TABLE
    ADD COLUMN for anything missing. Idempotent.
    """
    migrations = {
        'indexed_file': [
            ('client_name',     'VARCHAR(255)'),
            ('doc_type',        'VARCHAR(100)'),
            ('doc_year',        'VARCHAR(10)'),
            ('attributes_json', 'TEXT'),
            ('is_code',         'BOOLEAN DEFAULT 0'),
            ('project_name',    'VARCHAR(255)'),
            ('project_root',    'VARCHAR(1024)'),
            ('language',        'VARCHAR(50)'),
            ('is_embedded',     'BOOLEAN DEFAULT 0'),
        ],
        'virtual_path': [
            ('indexed_file_id', 'INTEGER REFERENCES indexed_file(id) ON DELETE CASCADE'),
        ],
    }
    try:
        conn = db.engine.raw_connection()
        cur = conn.cursor()
        for table, cols in migrations.items():
            existing = {row[1] for row in cur.execute(f'PRAGMA table_info({table})')}
            for name, decl in cols:
                if name not in existing:
                    try:
                        cur.execute(f'ALTER TABLE {table} ADD COLUMN {name} {decl}')
                        logger.info(f"Migrated: added {table}.{name}")
                    except Exception as e:
                        logger.warning(f"ALTER {table}.{name} failed: {e}")

        # Make virtual_path.document_id nullable (was NOT NULL originally).
        # SQLite can't ALTER constraints, so recreate the table preserving data.
        try:
            cols_info = list(cur.execute('PRAGMA table_info(virtual_path)'))
            doc_col = next((c for c in cols_info if c[1] == 'document_id'), None)
            # c[3] = notnull (1 if NOT NULL)
            if doc_col and doc_col[3] == 1:
                logger.info("Recreating virtual_path table to relax document_id NOT NULL")
                cur.execute('ALTER TABLE virtual_path RENAME TO virtual_path_old')
                # New schema (matches model)
                cur.execute('''
                    CREATE TABLE virtual_path (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        document_id INTEGER REFERENCES document(id) ON DELETE CASCADE,
                        indexed_file_id INTEGER REFERENCES indexed_file(id) ON DELETE CASCADE,
                        user_id INTEGER NOT NULL REFERENCES user(id),
                        view_name VARCHAR(64) NOT NULL,
                        path VARCHAR(760) NOT NULL,
                        level1 VARCHAR(255) NOT NULL,
                        level2 VARCHAR(255),
                        level3 VARCHAR(255),
                        created_at DATETIME NOT NULL
                    )
                ''')
                cur.execute('''
                    INSERT INTO virtual_path
                        (id, document_id, user_id, view_name, path, level1, level2, level3, created_at)
                    SELECT id, document_id, user_id, view_name, path, level1, level2, level3, created_at
                    FROM virtual_path_old
                ''')
                cur.execute('DROP TABLE virtual_path_old')
                # Recreate indexes
                cur.execute('CREATE UNIQUE INDEX uq_virtual_path_doc_view ON virtual_path(document_id, view_name)')
                cur.execute('CREATE UNIQUE INDEX uq_virtual_path_indexed_view ON virtual_path(indexed_file_id, view_name)')
                cur.execute('CREATE INDEX ix_virtual_path_user_view ON virtual_path(user_id, view_name)')
                cur.execute('CREATE INDEX ix_virtual_path_user_view_l1 ON virtual_path(user_id, view_name, level1)')
                cur.execute('CREATE INDEX ix_virtual_path_user_view_l1_l2 ON virtual_path(user_id, view_name, level1, level2)')
                cur.execute('CREATE INDEX ix_virtual_path_indexed_file ON virtual_path(indexed_file_id)')
                cur.execute('CREATE INDEX ix_virtual_path_document_id ON virtual_path(document_id)')
                cur.execute('CREATE INDEX ix_virtual_path_user_id ON virtual_path(user_id)')
        except Exception as e:
            logger.warning(f"virtual_path recreate skipped: {e}")

        conn.commit()
        conn.close()
    except Exception as e:
        logger.error(f"ensure_columns failed: {e}")
