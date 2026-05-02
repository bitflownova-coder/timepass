"""
Migration: Populate knowledge model attributes on existing Document rows.

Adds doc_type, client_name, doc_year by back-filling from:
  - doc_type    ← predicted_label (or user_folder)
  - client_name ← entity_keywords field (parses "person:Name" prefix)
                  falls back to user_folder if it looks like a person name
  - doc_year    ← scans extracted_text for a 4-digit year, else uses uploaded_at year

Also creates the new SQLite columns if they don't exist yet (SQLite doesn't
support IF NOT EXISTS on ALTER TABLE, so we probe the schema first).

Usage:
    venv\\Scripts\\python scripts\\migrate_to_knowledge_model.py
    venv\\Scripts\\python scripts\\migrate_to_knowledge_model.py --dry-run
"""
import sys
import re
import argparse
import logging
from pathlib import Path

# ── project root on sys.path ─────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import create_app
from app.models import db, Document

logging.basicConfig(level=logging.INFO, format='%(levelname)s  %(message)s')
log = logging.getLogger(__name__)

# Titles / noise that should not be treated as person names
_NAME_BLOCKLIST = {
    'resume', 'invoice', 'certificate', 'report', 'document', 'agreement',
    'contract', 'statement', 'letter', 'application', 'form', 'receipt',
    'policy', 'record', 'general', 'misc', 'various', 'other', 'unknown',
    'bitflow', 'gallery', 'photos', 'images', 'documents',
    'invoices', 'receipts', 'certificates', 'payslips', 'medical', 'bank',
    'academic', 'training', 'legal', 'contracts', 'insurance', 'tax',
    'technical', 'marketing', 'financial', 'purchase', 'meeting', 'project',
    'research', 'property', 'identity', 'hr', 'reports', 'statements',
}

_YEAR_RE = re.compile(r'\b(19[5-9]\d|20[0-2]\d)\b')


def _derive_doc_type(doc: Document) -> str | None:
    """doc_type = predicted_label, else user_folder, else None."""
    return doc.predicted_label or doc.user_folder or None


def _derive_client_name(doc: Document) -> str | None:
    """
    Parse entity_keywords like "person:Rahul Kumar, org:Bitflow"
    and return the first person name found.
    Falls back to user_folder if it looks like a 2+ word proper name.
    """
    kw = doc.entity_keywords or ''
    for chunk in kw.split(','):
        chunk = chunk.strip()
        if chunk.startswith('person:'):
            name = chunk[len('person:'):].strip()
            if name and name.lower() not in _NAME_BLOCKLIST:
                return name

    # Fallback: user_folder that looks like a person name (Title Case, 2+ words, no blocklist)
    folder = doc.user_folder or ''
    parts = folder.split()
    if (
        len(parts) >= 2
        and all(re.match(r'^[A-Za-z]{2,20}$', p) for p in parts)
        and all(p.lower() not in _NAME_BLOCKLIST for p in parts)
        and folder[0].isupper()
    ):
        return folder

    return None


def _derive_doc_year(doc: Document) -> int | None:
    """Scan extracted_text for a 4-digit year; fallback to upload year."""
    text = doc.extracted_text or ''
    m = _YEAR_RE.search(text[:5000])
    if m:
        return int(m.group(1))
    if doc.uploaded_at:
        return doc.uploaded_at.year
    return None


def run(dry_run: bool = False) -> None:
    app = create_app('development')
    with app.app_context():
        # ── Ensure new columns exist in SQLite ───────────────────────────────
        from sqlalchemy import text, inspect
        inspector = inspect(db.engine)
        existing_cols = {col['name'] for col in inspector.get_columns('document')}

        # Schema changes are always applied — adding columns is non-destructive
        with db.engine.connect() as conn:
            for col, typedef in [
                ('doc_type',        'VARCHAR(100)'),
                ('client_name',     'VARCHAR(255)'),
                ('doc_year',        'INTEGER'),
                ('entity_keywords', 'VARCHAR(500)'),
            ]:
                if col not in existing_cols:
                    log.info(f'Adding column: document.{col}')
                    conn.execute(text(f'ALTER TABLE document ADD COLUMN {col} {typedef}'))
            conn.commit()

        # ── Back-fill attributes on existing documents ───────────────────────
        docs = Document.query.filter_by(deleted_at=None).all()
        log.info(f'Processing {len(docs)} active documents …')

        updated = skipped = 0
        for doc in docs:
            doc_type = _derive_doc_type(doc)
            client_name = _derive_client_name(doc)
            doc_year = _derive_doc_year(doc)

            needs_update = (
                doc.doc_type != doc_type
                or doc.client_name != client_name
                or doc.doc_year != doc_year
            )

            log.info(
                f'  [{doc.id:>4}] {doc.original_filename[:40]:<40} '
                f'type={doc_type!r:20} client={client_name!r:25} year={doc_year}'
            )

            if needs_update:
                updated += 1
                if not dry_run:
                    doc.doc_type = doc_type
                    doc.client_name = client_name
                    doc.doc_year = doc_year
            else:
                skipped += 1

        if not dry_run:
            db.session.commit()
            log.info(f'Done. Updated={updated}  Already OK={skipped}')
        else:
            log.info(f'[DRY RUN] Would update={updated}  Would skip={skipped}')


def main() -> int:
    parser = argparse.ArgumentParser(description='Migrate Document rows to knowledge model attributes')
    parser.add_argument('--dry-run', action='store_true', help='Preview changes without writing to DB')
    args = parser.parse_args()
    run(dry_run=args.dry_run)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
