"""
Generate virtual paths for all existing documents (Phase 4 retroactive).

Usage:
    venv\\Scripts\\python scripts\\generate_virtual_paths.py
    venv\\Scripts\\python scripts\\generate_virtual_paths.py --dry-run
"""
import sys
import argparse
import logging
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app import create_app
from app.models import db, Document
from app.models.virtual_path import HierarchyTemplate, VirtualPath
from app.utils.path_generator import PathGenerator

logging.basicConfig(level=logging.INFO, format='%(levelname)s  %(message)s')
log = logging.getLogger(__name__)


def run(dry_run: bool = False) -> None:
    app = create_app('development')
    with app.app_context():
        templates = HierarchyTemplate.query.filter_by(user_id=None).all()
        if not templates:
            log.error('No HierarchyTemplate rows found. Run the app once to seed them.')
            return

        log.info(f'Templates: {[t.view_name for t in templates]}')

        docs = Document.query.filter_by(deleted_at=None).all()
        log.info(f'Processing {len(docs)} active documents …')

        total_created = 0
        for doc in docs:
            paths = PathGenerator.generate_and_save(doc, templates, db)
            for vp in paths:
                log.info(
                    f'  [{doc.id:>4}] {doc.original_filename[:35]:<35} '
                    f'{vp.view_name:<12} → {vp.path}'
                )
            total_created += len(paths)

        if dry_run:
            db.session.rollback()
            log.info(f'[DRY RUN] Would create {total_created} VirtualPath rows (rolled back)')
        else:
            db.session.commit()
            log.info(f'Done. Created/updated {total_created} VirtualPath rows.')


def main() -> int:
    parser = argparse.ArgumentParser(description='Generate virtual paths for existing documents')
    parser.add_argument('--dry-run', action='store_true', help='Preview without writing')
    args = parser.parse_args()
    run(dry_run=args.dry_run)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
