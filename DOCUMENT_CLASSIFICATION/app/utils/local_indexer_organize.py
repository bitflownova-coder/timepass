"""
Organize Indexed Files — for the local PC indexer.

Two responsibilities:
1. organize_indexed_file(record, text, user_id, db): runs after a file is
   indexed. Populates business-doc attributes (doc_type, client_name,
   doc_year) for non-code files via lightweight extraction, then generates
   VirtualPath rows so the file shows up in the by_type / by_client /
   by_time / code_projects views.

2. embed_pending(user_id, db, app, task_id, progress, lock): background pass
   that embeds every IndexedFile row whose is_embedded == False. Business
   docs first, code last. Updates `progress[task_id]` so the frontend can
   display the embedding phase.
"""
from __future__ import annotations

import re
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_YEAR_RE = re.compile(r'\b(19[8-9]\d|20\d{2})\b')


def _extract_year(text: str, modified_at) -> str | None:
    """Cheap year extraction: scan the first 4KB; fall back to file mtime."""
    if text:
        m = _YEAR_RE.search(text[:4000])
        if m:
            return m.group(1)
    if modified_at is not None:
        try:
            return str(modified_at.year)
        except Exception:
            pass
    return None


def _doc_type_from_label(label: str | None, ext: str | None) -> str:
    """
    Derive a simple doc_type bucket from the classifier label or extension.
    Avoids running the full AttributeExtractor (slow for thousands of files).
    """
    if label and label != 'Code':
        return label
    # Fallback by extension
    ext = (ext or '').lower()
    if ext in ('.pdf',):
        return 'PDF'
    if ext in ('.docx', '.doc', '.rtf', '.odt'):
        return 'Word Document'
    if ext in ('.xlsx', '.xls', '.csv'):
        return 'Spreadsheet'
    if ext in ('.pptx', '.ppt'):
        return 'Presentation'
    if ext in ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff', '.webp'):
        return 'Image'
    if ext in ('.txt', '.text', '.md'):
        return 'Text'
    return 'Other'


def _client_from_filename(filename: str) -> str | None:
    """
    Very lightweight client-name guess: the first capitalised word group
    in the filename stem (e.g. 'Acme_Invoice_2024.pdf' → 'Acme'). None if
    nothing plausible found.
    """
    stem = Path(filename).stem
    parts = re.split(r'[\s_\-\.]+', stem)
    name_words = [p for p in parts if re.match(r'^[A-Z][a-zA-Z]{1,30}$', p)]
    if name_words:
        return name_words[0]
    return None


def organize_indexed_file(record, text: str, user_id: int, db) -> int:
    """
    Populate doc_type / client_name / doc_year for non-code records,
    then create/update VirtualPath rows for every active hierarchy template.

    Returns the number of VirtualPath rows written.
    """
    from app.models.virtual_path import HierarchyTemplate, VirtualPath

    # Populate business-doc attributes only for non-code files
    if not record.is_code:
        if not record.doc_type:
            record.doc_type = _doc_type_from_label(
                record.predicted_label, record.extension
            )
        if not record.client_name:
            record.client_name = _client_from_filename(record.filename or '')
        if not record.doc_year:
            record.doc_year = _extract_year(text, record.modified_at)

    templates = HierarchyTemplate.query.filter_by(user_id=None).all()
    written = 0

    for tpl in templates:
        is_code_view = tpl.view_name == 'code_projects'

        # Clean separation: code only goes to code view; docs only to business views
        if record.is_code and not is_code_view:
            continue
        if (not record.is_code) and is_code_view:
            continue

        l1 = _segment_value(record, tpl.level1_attr)
        l2 = _segment_value(record, tpl.level2_attr) if tpl.level2_attr else None
        l3 = _segment_value(record, tpl.level3_attr) if tpl.level3_attr else None

        # Skip uninformative paths (every level Unknown)
        levels = [l1, l2, l3]
        meaningful = [v for v in levels if v and v != 'Unknown']
        if not meaningful:
            continue

        path = '/'.join(s for s in [l1, l2, l3] if s)

        existing = VirtualPath.query.filter_by(
            indexed_file_id=record.id,
            view_name=tpl.view_name,
        ).first()
        if existing:
            existing.path = path
            existing.level1 = l1
            existing.level2 = l2
            existing.level3 = l3
        else:
            db.session.add(VirtualPath(
                indexed_file_id=record.id,
                document_id=None,
                user_id=user_id,
                view_name=tpl.view_name,
                path=path,
                level1=l1,
                level2=l2,
                level3=l3,
            ))
        written += 1

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        logger.warning(f"organize_indexed_file commit failed: {e}")
    return written


def _segment_value(record, attr: str) -> str:
    val = getattr(record, attr, None)
    if val is None or str(val).strip() == '':
        return 'Unknown'
    s = str(val).strip()
    s = re.sub(r'[<>:"/\\|?*\x00-\x1f]', '', s)
    return s[:80] or 'Unknown'


# ── Background embedding pass ────────────────────────────────────────────

def embed_pending(user_id: int, db, app, task_id: str,
                  progress: dict, lock) -> None:
    """
    Embed every IndexedFile row that hasn't been embedded yet.
    Business docs are processed first (lower id range typically), then code.
    Embedding is best-effort — failures don't block the scan.
    """
    from app.models.indexed_file import IndexedFile

    try:
        from app.utils.embedder import embed_file
    except Exception as e:
        logger.warning(f"Embedder unavailable, skipping embedding pass: {e}")
        return

    # Two passes: docs first, then code
    for code_pass in (False, True):
        rows = (IndexedFile.query
                .filter_by(user_id=user_id, is_embedded=False, is_deleted=False,
                           is_code=code_pass)
                .order_by(IndexedFile.id)
                .all())
        with lock:
            cur = progress.get(task_id, {})
            cur['embed_total'] = (cur.get('embed_total', 0) + len(rows))

        for rec in rows:
            try:
                embed_file(
                    rec.id, user_id, rec.extracted_text or '',
                    rec.filename, rec.file_path, rec.extension,
                )
                rec.is_embedded = True
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                logger.debug(f"Embed failed for {rec.file_path}: {e}")
            with lock:
                cur = progress.get(task_id, {})
                cur['embed_done'] = cur.get('embed_done', 0) + 1
                cur['current'] = f"Embedding: {rec.filename}"
