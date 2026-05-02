"""
Embedder — Phase C
Semantic (vector) search using ChromaDB + ChromaDB's built-in ONNX MiniLM model.
No PyTorch required. Model cached at C:\\Users\\<user>\\.cache\\chroma\\onnx_models\\.
Files are chunked into overlapping windows before embedding so long documents
are retrievable by any section.
"""
import os
import logging

logger = logging.getLogger(__name__)

# Persistent ChromaDB storage alongside the project
_BASE_DIR   = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CHROMA_PATH = os.path.join(_BASE_DIR, 'data', 'chroma')

# ~400 chars ≈ 100 tokens; 80-char overlap keeps context across boundaries
CHUNK_SIZE    = 400
CHUNK_OVERLAP = 80

# ── Lazy singletons ───────────────────────────────────────────
_client     = None
_ef         = None
_collection = None


def _get_ef():
    global _ef
    if _ef is None:
        from chromadb.utils.embedding_functions import ONNXMiniLM_L6_V2
        _ef = ONNXMiniLM_L6_V2()
    return _ef


def _get_client():
    global _client
    if _client is None:
        import chromadb
        os.makedirs(CHROMA_PATH, exist_ok=True)
        _client = chromadb.PersistentClient(path=CHROMA_PATH)
    return _client


def _get_collection():
    global _collection
    if _collection is None:
        client = _get_client()
        _collection = client.get_or_create_collection(
            name='documents',
            embedding_function=_get_ef(),
            metadata={'hnsw:space': 'cosine'},
        )
    return _collection


# ── Chunking ─────────────────────────────────────────────────

def _chunk_text(text: str) -> list[str]:
    """Split text into overlapping character windows. Caps at 200 chunks."""
    if not text or not text.strip():
        return []
    chunks = []
    start  = 0
    length = len(text)
    while start < length and len(chunks) < 200:
        chunks.append(text[start: start + CHUNK_SIZE])
        start += CHUNK_SIZE - CHUNK_OVERLAP
    return chunks


# ── Public API ───────────────────────────────────────────────

def embed_file(record_id: int, user_id: int, text: str,
               filename: str, file_path: str = '', extension: str = '') -> bool:
    """
    Embed all text chunks of a file and upsert them into ChromaDB.
    Deletes existing chunks for the same record_id first (handles re-index).
    Returns True on success, False if there is no usable text or an error occurs.
    """
    if not text or not text.strip():
        return False
    try:
        col    = _get_collection()
        chunks = _chunk_text(text)
        if not chunks:
            return False

        # Remove stale chunks for this file
        col.delete(where={'record_id': record_id})

        ids       = [f"{record_id}__c{i}" for i in range(len(chunks))]
        metadatas = [
            {
                'record_id': record_id,
                'user_id':   user_id,
                'filename':  filename[:200],
                'file_path': file_path[:500],
                'extension': extension,
                'chunk_idx': i,
            }
            for i in range(len(chunks))
        ]
        col.add(documents=chunks, ids=ids, metadatas=metadatas)
        return True
    except Exception as e:
        logger.error(f"embed_file failed for record_id={record_id}: {e}")
        return False


def delete_embedding(record_id: int):
    """Remove all chunks for a file from ChromaDB (call when file is deleted from index)."""
    try:
        col = _get_collection()
        col.delete(where={'record_id': record_id})
    except Exception as e:
        logger.warning(f"delete_embedding failed for record_id={record_id}: {e}")


def semantic_search(query: str, user_id: int, top_k: int = 20,
                    ext_filter: str = None,
                    folder_filter: str = None) -> list[dict]:
    """
    Cosine-similarity search against embedded chunks.
    Returns list of dicts: record_id, filename, file_path, extension,
                           chunk_idx, chunk_text, score (0-1, higher=better).
    Deduplicated by record_id — only the best-matching chunk per file is returned.
    """
    if not query or not query.strip():
        return []
    try:
        col = _get_collection()
        if col.count() == 0:
            return []

        where = {'user_id': user_id}
        if ext_filter:
            ext_filter = ext_filter if ext_filter.startswith('.') else '.' + ext_filter
            where['extension'] = ext_filter

        results = col.query(
            query_texts=[query],
            n_results=min(top_k * 4, 200),   # over-fetch, then dedup by file
            where=where,
            include=['documents', 'metadatas', 'distances'],
        )

        docs      = results['documents'][0]
        metas     = results['metadatas'][0]
        distances = results['distances'][0]

        seen: dict = {}   # record_id → best hit
        for doc, meta, dist in zip(docs, metas, distances):
            rid = meta['record_id']
            if folder_filter and folder_filter.lower() not in meta.get('file_path', '').lower():
                continue
            score = round(1.0 - float(dist), 4)   # cosine distance → similarity
            if rid not in seen or score > seen[rid]['score']:
                seen[rid] = {
                    'record_id': rid,
                    'filename':  meta['filename'],
                    'file_path': meta['file_path'],
                    'extension': meta['extension'],
                    'chunk_idx': meta['chunk_idx'],
                    'chunk_text': doc,
                    'score':     score,
                }

        ranked = sorted(seen.values(), key=lambda x: x['score'], reverse=True)[:top_k]
        return ranked

    except Exception as e:
        logger.error(f"semantic_search error: {e}")
        return []


def embed_status() -> dict:
    """Return total number of chunks and unique files currently embedded."""
    try:
        col = _get_collection()
        total_chunks = col.count()
        return {'total_chunks': total_chunks, 'ready': True}
    except Exception as e:
        return {'total_chunks': 0, 'ready': False, 'error': str(e)}
