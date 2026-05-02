"""
Migrate existing encrypted files from category-based paths to flat storage.

Before:  uploads/{user_id}/{category}/{timestamp}_{hash8}_{filename}.enc
After:   uploads/{user_id}/storage/{doc_id}.enc

Usage:
    # Always run dry-run first to verify zero errors
    python scripts/migrate_flat_storage.py --dry-run

    # Live run (take a backup first!)
    python scripts/migrate_flat_storage.py
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import shutil
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Migrate to flat file storage")
    parser.add_argument('--dry-run', action='store_true',
                        help="Preview changes without touching disk or DB")
    args = parser.parse_args()

    from app import create_app
    from app.models import db
    from app.models.document import Document

    app = create_app()
    with app.app_context():
        upload_root = Path(app.config['UPLOAD_FOLDER'])
        docs = Document.query.filter(Document.deleted_at.is_(None)).order_by(Document.id).all()

        moved = 0
        already_flat = 0
        missing = 0
        errors = 0

        for doc in docs:
            if not doc.file_path:
                print(f"[SKIP ] doc {doc.id:>5}: no file_path in DB")
                missing += 1
                continue

            current = Path(doc.file_path)
            expected = upload_root / str(doc.user_id) / 'storage' / f"{doc.id}.enc"

            # Already at the flat path
            if current == expected:
                print(f"[OK   ] doc {doc.id:>5}: already flat")
                already_flat += 1
                continue

            # Already under a 'storage' dir (partial previous run)
            if 'storage' in current.parts and current.name == f"{doc.id}.enc":
                if str(current) != str(expected):
                    # Wrong user or wrong id — fix the DB record only
                    print(f"[FIXDB] doc {doc.id:>5}: path mismatch, updating DB")
                    if not args.dry_run:
                        doc.file_path = str(expected)
                        doc.filename  = expected.name
                        db.session.commit()
                    moved += 1
                else:
                    already_flat += 1
                continue

            if not current.exists():
                print(f"[WARN ] doc {doc.id:>5}: source file missing: {current}")
                missing += 1
                continue

            print(f"[MOVE ] doc {doc.id:>5}: {current.relative_to(upload_root)} "
                  f"→ {expected.relative_to(upload_root)}")

            if not args.dry_run:
                try:
                    expected.parent.mkdir(parents=True, exist_ok=True)
                    shutil.move(str(current), str(expected))
                    doc.file_path = str(expected)
                    doc.filename  = expected.name
                    db.session.commit()
                    moved += 1
                except Exception as exc:
                    db.session.rollback()
                    print(f"  ERROR: {exc}")
                    errors += 1
            else:
                moved += 1

        print()
        print(f"{'DRY RUN — ' if args.dry_run else ''}Summary:")
        print(f"  Already flat : {already_flat}")
        print(f"  To migrate   : {moved}")
        print(f"  Missing files: {missing}")
        print(f"  Errors       : {errors}")

        if args.dry_run:
            print("\nRe-run without --dry-run to apply changes.")
        elif errors == 0:
            print("\nMigration complete. All paths are now flat.")
        else:
            print(f"\nCompleted with {errors} error(s). Check output above.")


if __name__ == '__main__':
    main()
