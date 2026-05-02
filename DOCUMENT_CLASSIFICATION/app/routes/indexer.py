"""
Indexer Routes — Phase A
Endpoints for folder management, scanning, search, file-open tracking.
"""
import uuid
import os
from flask import Blueprint, request, current_app
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models import db
from app.models.indexed_file import IndexedFile, FileOpen, WatchedFolder
from app.utils.local_indexer import (
    scan_folder_async, get_scan_progress,
    fts_search, index_file, scan_pc_async, get_all_drives,
)
from app.utils.validators import sanitize_input

indexer_bp = Blueprint('indexer', __name__, url_prefix='/api/index')


# ── Watched Folders ────────────────────────────────────────────

@indexer_bp.route('/folders', methods=['GET'])
@jwt_required()
def list_folders():
    user_id = int(get_jwt_identity())
    folders = WatchedFolder.query.filter_by(user_id=user_id).order_by(WatchedFolder.added_at.desc()).all()
    return {'success': True, 'folders': [
        {
            'id':           f.id,
            'folder_path':  f.folder_path,
            'recursive':    f.recursive,
            'added_at':     f.added_at.isoformat() if f.added_at else None,
            'last_scan_at': f.last_scan_at.isoformat() if f.last_scan_at else None,
            'file_count':   f.file_count,
        } for f in folders
    ]}, 200


@indexer_bp.route('/folders', methods=['POST'])
@jwt_required()
def add_folder():
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    folder_path = sanitize_input((data.get('folder_path') or '').strip())
    recursive   = bool(data.get('recursive', True))

    if not folder_path:
        return {'success': False, 'error': 'folder_path is required'}, 400
    folder_path = os.path.abspath(folder_path)
    if not os.path.isdir(folder_path):
        return {'success': False, 'error': 'Path does not exist or is not a folder'}, 400

    existing = WatchedFolder.query.filter_by(user_id=user_id, folder_path=folder_path).first()
    if existing:
        return {'success': False, 'error': 'Folder already being watched'}, 409

    wf = WatchedFolder(user_id=user_id, folder_path=folder_path, recursive=recursive)
    db.session.add(wf)
    db.session.commit()
    return {'success': True, 'id': wf.id, 'folder_path': folder_path}, 201


@indexer_bp.route('/folders/<int:folder_id>', methods=['DELETE'])
@jwt_required()
def remove_folder(folder_id):
    user_id = int(get_jwt_identity())
    wf = WatchedFolder.query.filter_by(id=folder_id, user_id=user_id).first_or_404()
    db.session.delete(wf)
    db.session.commit()
    return {'success': True}, 200


# ── Scanning ───────────────────────────────────────────────────

@indexer_bp.route('/scan', methods=['POST'])
@jwt_required()
def start_scan():
    """Start an async folder scan. Returns task_id to poll progress."""
    user_id = int(get_jwt_identity())
    data = request.get_json(silent=True) or {}
    folder_path = sanitize_input((data.get('folder_path') or '').strip())

    if not folder_path:
        return {'success': False, 'error': 'folder_path is required'}, 400
    folder_path = os.path.abspath(folder_path)
    if not os.path.isdir(folder_path):
        return {'success': False, 'error': 'Path is not a directory'}, 400

    task_id = str(uuid.uuid4())
    app = current_app._get_current_object()
    scan_folder_async(folder_path, user_id, app, task_id)
    return {'success': True, 'task_id': task_id}, 202


@indexer_bp.route('/scan/<task_id>', methods=['GET'])
@jwt_required()
def scan_progress(task_id):
    progress = get_scan_progress(task_id)
    return {'success': True, **progress}, 200


# ── Whole-PC scan ──────────────────────────────────────────────

@indexer_bp.route('/scan-pc', methods=['POST'])
@jwt_required()
def start_scan_pc():
    """
    Start a full-PC scan in the background.
    Detects every accessible drive, walks all user-relevant folders,
    and indexes every supported document/image.
    Returns a task_id — poll /scan/<task_id> for progress.
    """
    user_id = int(get_jwt_identity())
    task_id = str(uuid.uuid4())
    app = current_app._get_current_object()

    drives = get_all_drives()
    scan_pc_async(user_id, app, task_id)
    return {
        'success': True,
        'task_id': task_id,
        'drives': drives,
        'message': f"Started scanning {len(drives)} drive(s): {', '.join(drives)}",
    }, 202


# ── Search ─────────────────────────────────────────────────────

@indexer_bp.route('/search', methods=['GET'])
@jwt_required()
def search():
    user_id = int(get_jwt_identity())
    query   = sanitize_input(request.args.get('q', '').strip())
    ext     = request.args.get('ext', '').strip().lower() or None
    folder  = request.args.get('folder', '').strip() or None
    limit   = min(int(request.args.get('limit', 50)), 200)
    offset  = int(request.args.get('offset', 0))

    if not query:
        return {'success': False, 'error': 'q is required'}, 400

    results = fts_search(query, user_id, db,
                         ext_filter=ext,
                         folder_filter=folder,
                         limit=limit, offset=offset)
    return {'success': True, 'query': query, 'count': len(results), 'results': results}, 200


# ── File listing / detail ──────────────────────────────────────

@indexer_bp.route('/files', methods=['GET'])
@jwt_required()
def list_files():
    user_id  = int(get_jwt_identity())
    folder   = request.args.get('folder', '').strip() or None
    ext      = request.args.get('ext', '').strip().lower() or None
    label    = request.args.get('label', '').strip() or None
    sort     = request.args.get('sort', 'indexed_at')
    page     = max(1, int(request.args.get('page', 1)))
    per_page = min(int(request.args.get('per_page', 50)), 200)

    ALLOWED_SORT = {'indexed_at', 'filename', 'file_size', 'modified_at', 'predicted_label'}
    if sort not in ALLOWED_SORT:
        sort = 'indexed_at'

    q = IndexedFile.query.filter_by(user_id=user_id, is_deleted=False)
    if folder:
        q = q.filter(IndexedFile.folder_path.ilike(f'%{folder}%'))
    if ext:
        q = q.filter_by(extension=ext if ext.startswith('.') else '.' + ext)
    if label:
        q = q.filter_by(predicted_label=label)

    total = q.count()
    items = q.order_by(getattr(IndexedFile, sort).desc()).offset((page - 1) * per_page).limit(per_page).all()

    return {
        'success': True,
        'total': total,
        'page': page,
        'per_page': per_page,
        'files': [f.to_dict() for f in items],
    }, 200


@indexer_bp.route('/files/<int:file_id>', methods=['GET'])
@jwt_required()
def get_file(file_id):
    user_id = int(get_jwt_identity())
    f = IndexedFile.query.filter_by(id=file_id, user_id=user_id, is_deleted=False).first_or_404()
    d = f.to_dict()
    d['extracted_text'] = (f.extracted_text or '')[:5000]  # first 5000 chars in detail view
    return {'success': True, 'file': d}, 200


# ── File open tracking ─────────────────────────────────────────

@indexer_bp.route('/files/<int:file_id>/open', methods=['POST'])
@jwt_required()
def record_open(file_id):
    """Call this when user opens/views a file — records it for Read Later history."""
    user_id = int(get_jwt_identity())
    f = IndexedFile.query.filter_by(id=file_id, user_id=user_id, is_deleted=False).first_or_404()
    data = request.get_json(silent=True) or {}
    duration = data.get('duration_secs')

    fo = FileOpen(user_id=user_id, indexed_file_id=file_id,
                  duration_secs=int(duration) if duration else None)
    db.session.add(fo)
    db.session.commit()

    # Return the OS path so the browser can open it via shell (if desktop app) or show it
    return {'success': True, 'file_path': f.file_path}, 200


@indexer_bp.route('/recently-opened', methods=['GET'])
@jwt_required()
def recently_opened():
    """Return last 50 distinct files opened — for 'Continue Reading' panel."""
    user_id  = int(get_jwt_identity())
    limit    = min(int(request.args.get('limit', 20)), 100)

    # Latest open per file
    from sqlalchemy import func
    sub = (
        db.session.query(
            FileOpen.indexed_file_id,
            func.max(FileOpen.opened_at).label('last_opened'),
            func.count(FileOpen.id).label('open_count'),
        )
        .filter_by(user_id=user_id)
        .group_by(FileOpen.indexed_file_id)
        .order_by(func.max(FileOpen.opened_at).desc())
        .limit(limit)
        .subquery()
    )

    rows = (
        db.session.query(IndexedFile, sub.c.last_opened, sub.c.open_count)
        .join(sub, IndexedFile.id == sub.c.indexed_file_id)
        .filter(IndexedFile.is_deleted == False)
        .all()
    )

    results = []
    for rec, last_opened, open_count in rows:
        d = rec.to_dict()
        d['last_opened'] = last_opened.isoformat() if last_opened else None
        d['open_count']  = open_count
        results.append(d)

    return {'success': True, 'files': results}, 200


# ── Semantic Search ────────────────────────────────────────────

@indexer_bp.route('/semantic-search', methods=['GET'])
@jwt_required()
def semantic_search_route():
    """Vector similarity search using ChromaDB + ONNX MiniLM embeddings."""
    user_id = int(get_jwt_identity())
    query   = sanitize_input(request.args.get('q', '').strip())
    ext     = request.args.get('ext', '').strip().lower() or None
    folder  = request.args.get('folder', '').strip() or None
    top_k   = min(int(request.args.get('limit', 20)), 50)

    if not query:
        return {'success': False, 'error': 'q is required'}, 400

    from app.utils.embedder import semantic_search as sem_search
    raw = sem_search(query, user_id, top_k=top_k, ext_filter=ext, folder_filter=folder)

    if not raw:
        return {'success': True, 'query': query, 'count': 0, 'results': [],
                'hint': 'No results. Make sure you have scanned folders first.'}, 200

    # Enrich with full DB records
    ids     = [r['record_id'] for r in raw]
    records = {r.id: r for r in IndexedFile.query.filter(
        IndexedFile.id.in_(ids),
        IndexedFile.user_id == user_id,
        IndexedFile.is_deleted == False,
    ).all()}

    results = []
    for r in raw:
        rec = records.get(r['record_id'])
        if not rec:
            continue
        d = rec.to_dict()
        d['chunk_text']  = r['chunk_text']
        d['score']       = r['score']
        d['search_type'] = 'semantic'
        results.append(d)

    return {'success': True, 'query': query, 'count': len(results), 'results': results}, 200


@indexer_bp.route('/embed-status', methods=['GET'])
@jwt_required()
def embed_status_route():
    """Return ChromaDB embedding stats."""
    from app.utils.embedder import embed_status
    return {'success': True, **embed_status()}, 200


# ── RAG Q&A ────────────────────────────────────────────────────

@indexer_bp.route('/ask', methods=['POST'])
@jwt_required()
def ask():
    """
    Retrieval-Augmented Q&A (retrieval-only, Phase D).
    Embeds the question, retrieves top-K relevant chunks from ChromaDB,
    groups them by source file, and returns them as citations.
    Phase E will pass these chunks to Ollama to synthesise a natural language answer.
    """
    user_id = int(get_jwt_identity())
    data    = request.get_json(silent=True) or {}
    question = sanitize_input((data.get('question') or '').strip())
    top_k    = min(int(data.get('top_k', 5)), 10)   # max 10 source files

    if not question:
        return {'success': False, 'error': 'question is required'}, 400
    if len(question) > 1000:
        return {'success': False, 'error': 'question too long (max 1000 chars)'}, 400

    from app.utils.embedder import semantic_search as sem_search, embed_status

    # Check embeddings exist
    status = embed_status()
    if not status.get('ready') or status.get('total_chunks', 0) == 0:
        return {
            'success': False,
            'error':   'No embeddings found. Please scan your folders first (File Indexer → Scan).',
        }, 400

    # Retrieve top chunks
    raw_hits = sem_search(question, user_id, top_k=top_k * 3)   # over-fetch then dedup
    if not raw_hits:
        return {
            'success': True,
            'question': question,
            'sources':  [],
            'answer_hint': 'No relevant documents found. Try scanning more folders or rephrasing.',
        }, 200

    # Enrich with DB records, group multiple chunks per file
    ids = [r['record_id'] for r in raw_hits]
    records = {r.id: r for r in IndexedFile.query.filter(
        IndexedFile.id.in_(ids),
        IndexedFile.user_id == user_id,
        IndexedFile.is_deleted == False,
    ).all()}

    seen_ids  = set()
    sources   = []
    all_chunks = []

    for hit in raw_hits:
        rid = hit['record_id']
        rec = records.get(rid)
        if not rec:
            continue
        all_chunks.append({
            'record_id': rid,
            'chunk_text': hit['chunk_text'],
            'score':      hit['score'],
        })
        if rid not in seen_ids:
            seen_ids.add(rid)
            sources.append({
                'id':             rec.id,
                'filename':       rec.filename,
                'file_path':      rec.file_path,
                'folder_path':    rec.folder_path,
                'extension':      rec.extension,
                'predicted_label': rec.predicted_label,
                'file_size':      rec.file_size,
                'score':          hit['score'],
                'excerpts':       [],   # filled below
            })
            if len(sources) >= top_k:
                break

    # Attach up to 3 best excerpts per source file
    for src in sources:
        rid = src['id']
        chunks_for_file = [c for c in all_chunks if c['record_id'] == rid]
        chunks_for_file.sort(key=lambda x: x['score'], reverse=True)
        src['excerpts'] = [c['chunk_text'] for c in chunks_for_file[:3]]

    return {
        'success':   True,
        'question':  question,
        'sources':   sources,
        'answer_hint': None,   # Phase E: Ollama will fill this with a generated answer
    }, 200


# ── Stats ──────────────────────────────────────────────────────

@indexer_bp.route('/stats', methods=['GET'])
@jwt_required()
def stats():
    user_id = int(get_jwt_identity())

    total   = IndexedFile.query.filter_by(user_id=user_id, is_deleted=False).count()
    by_type = (
        db.session.query(IndexedFile.extension, db.func.count())
        .filter_by(user_id=user_id, is_deleted=False)
        .group_by(IndexedFile.extension)
        .order_by(db.func.count().desc())
        .all()
    )
    by_label = (
        db.session.query(IndexedFile.predicted_label, db.func.count())
        .filter_by(user_id=user_id, is_deleted=False)
        .filter(IndexedFile.predicted_label.isnot(None))
        .group_by(IndexedFile.predicted_label)
        .order_by(db.func.count().desc())
        .all()
    )
    folders = WatchedFolder.query.filter_by(user_id=user_id).count()

    return {
        'success': True,
        'total_files': total,
        'watched_folders': folders,
        'by_extension': {ext: cnt for ext, cnt in by_type},
        'by_label': {lbl: cnt for lbl, cnt in by_label},
    }, 200


# ── Ollama status ──────────────────────────────────────────────

@indexer_bp.route('/ollama-status', methods=['GET'])
@jwt_required()
def ollama_status():
    """Check whether Ollama is running locally and which models are installed."""
    from app.utils.ollama_client import check_ollama
    return {'success': True, **check_ollama()}, 200


# ── Ollama streaming answer ────────────────────────────────────

@indexer_bp.route('/ask-stream', methods=['POST'])
@jwt_required()
def ask_stream():
    """
    Phase E: RAG + Ollama streaming.
    1. Retrieves top-K chunks (same as /ask)
    2. Builds a RAG prompt
    3. Streams Ollama's token-by-token response as Server-Sent Events (SSE)
    4. Sends a final SSE event with the source citations JSON

    SSE format:
      data: {"type":"token","text":"..."}
      data: {"type":"sources","sources":[...]}
      data: {"type":"done"}
      data: {"type":"error","message":"..."}
    """
    from flask import Response, stream_with_context
    from app.utils.embedder import semantic_search as sem_search, embed_status
    from app.utils.ollama_client import stream_answer, check_ollama, OllamaError

    user_id  = int(get_jwt_identity())
    data     = request.get_json(silent=True) or {}
    question = sanitize_input((data.get('question') or '').strip())
    top_k    = min(int(data.get('top_k', 5)), 10)
    model    = sanitize_input((data.get('model') or '').strip()) or None

    if not question:
        return {'success': False, 'error': 'question is required'}, 400
    if len(question) > 1000:
        return {'success': False, 'error': 'question too long (max 1000 chars)'}, 400

    # Check Ollama first (fast)
    ollama = check_ollama()
    if not ollama['running']:
        return {
            'success': False,
            'error':   'Ollama is not running. Start it with: ollama serve',
        }, 503

    if not ollama['models']:
        return {
            'success': False,
            'error':   'No Ollama models installed. Run: ollama pull llama3.2',
        }, 503

    # Retrieve sources (same logic as /ask)
    status = embed_status()
    if not status.get('ready') or status.get('total_chunks', 0) == 0:
        return {
            'success': False,
            'error':   'No embeddings found. Please scan your folders first.',
        }, 400

    raw_hits = sem_search(question, user_id, top_k=top_k * 3)
    if not raw_hits:
        return {
            'success': True,
            'sources': [],
            'answer_hint': 'No relevant documents found.',
        }, 200

    ids = [r['record_id'] for r in raw_hits]
    records = {r.id: r for r in IndexedFile.query.filter(
        IndexedFile.id.in_(ids),
        IndexedFile.user_id == user_id,
        IndexedFile.is_deleted == False,
    ).all()}

    seen_ids = set()
    sources  = []
    all_chunks = []

    for hit in raw_hits:
        rid = hit['record_id']
        rec = records.get(rid)
        if not rec:
            continue
        all_chunks.append({'record_id': rid, 'chunk_text': hit['chunk_text'], 'score': hit['score']})
        if rid not in seen_ids:
            seen_ids.add(rid)
            sources.append({
                'id': rec.id, 'filename': rec.filename,
                'file_path': rec.file_path, 'folder_path': rec.folder_path,
                'extension': rec.extension, 'predicted_label': rec.predicted_label,
                'file_size': rec.file_size, 'score': hit['score'], 'excerpts': [],
            })
            if len(sources) >= top_k:
                break

    for src in sources:
        rid = src['id']
        chunks_for_file = sorted(
            [c for c in all_chunks if c['record_id'] == rid],
            key=lambda x: x['score'], reverse=True,
        )
        src['excerpts'] = [c['chunk_text'] for c in chunks_for_file[:3]]

    # Stream SSE
    def generate():
        import json as _json
        # Send sources first so frontend can render cards immediately
        yield f"data: {_json.dumps({'type': 'sources', 'sources': sources})}\n\n"
        try:
            for token in stream_answer(question, sources, model=model):
                yield f"data: {_json.dumps({'type': 'token', 'text': token})}\n\n"
        except OllamaError as e:
            yield f"data: {_json.dumps({'type': 'error', 'message': str(e)})}\n\n"
            return
        yield f"data: {_json.dumps({'type': 'done'})}\n\n"

    return Response(
        stream_with_context(generate()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control':   'no-cache',
            'X-Accel-Buffering': 'no',
        },
    )
