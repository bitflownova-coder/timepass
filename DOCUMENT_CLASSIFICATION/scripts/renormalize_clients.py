"""
Re-normalize client_name values and rebuild VirtualPaths for all documents.

Applies EntityResolver.normalize_name() to existing Document.client_name
values (strips legal suffixes, title prefixes, collapses whitespace),
then rebuilds all VirtualPath rows to reflect the corrected names.

Usage:
    python scripts/renormalize_clients.py --dry-run
    python scripts/renormalize_clients.py
    python scripts/renormalize_clients.py --canonicalize
    python scripts/renormalize_clients.py --canonicalize --dry-run
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse


def main():
    parser = argparse.ArgumentParser(description="Re-normalize client names + rebuild virtual paths")
    parser.add_argument('--dry-run', action='store_true',
                        help="Preview changes without writing to DB")
    parser.add_argument('--canonicalize', action='store_true',
                        help="Fuzzy-merge near-duplicate client names using EntityCanonicalizer")
    args = parser.parse_args()

    from app import create_app
    from app.models import db
    from app.models.document import Document
    from app.models.virtual_path import HierarchyTemplate
    from app.utils.entity_resolver import normalize_name, EntityCanonicalizer
    from app.utils.path_generator import PathGenerator

    app = create_app()
    with app.app_context():
        docs = Document.query.filter(Document.deleted_at.is_(None)).all()
        templates = HierarchyTemplate.query.filter_by(user_id=None).all()

        changed = 0
        unchanged = 0
        rebuilt = 0

        for doc in docs:
            if not doc.client_name:
                unchanged += 1
                continue

            normalized = normalize_name(doc.client_name)
            if normalized == doc.client_name:
                unchanged += 1
                continue

            print(f"[NORM ] doc {doc.id:>5}: {doc.client_name!r:30s} → {normalized!r}")

            if not args.dry_run:
                doc.client_name = normalized
                db.session.add(doc)

            changed += 1

        if not args.dry_run and changed:
            db.session.commit()

        # ── Canonicalization pass (--canonicalize) ────────────────────────────
        canonicalized = 0
        if args.canonicalize:
            print("\nRunning canonicalization pass…")
            # Reload docs so normalization changes are visible in the session
            docs = Document.query.filter(Document.deleted_at.is_(None)).all()
            for doc in docs:
                if not doc.client_name:
                    continue
                canonical = EntityCanonicalizer.canonicalize(
                    doc.client_name, doc.user_id, db
                )
                if canonical != doc.client_name:
                    print(f"[CANON] doc {doc.id:>5}: {doc.client_name!r:30s} → {canonical!r}")
                    if not args.dry_run:
                        doc.client_name = canonical
                        db.session.add(doc)
                    canonicalized += 1
            if not args.dry_run and canonicalized:
                db.session.commit()

        # Rebuild VirtualPaths for ALL docs (picks up both normalization
        # changes and any hierarchy-rule changes from Phase D)
        if not args.dry_run:
            print(f"\nRebuilding VirtualPaths for {len(docs)} documents…")
            for doc in docs:
                PathGenerator.generate_and_save(doc, templates, db)
                rebuilt += 1
            db.session.commit()
            print(f"Rebuilt {rebuilt} document path sets.")

        print()
        print(f"{'DRY RUN — ' if args.dry_run else ''}Summary:")
        print(f"  client_name normalised : {changed}")
        print(f"  client_name canonicalized: {canonicalized}")
        print(f"  unchanged              : {unchanged}")
        if not args.dry_run:
            print(f"  VirtualPaths rebuilt   : {rebuilt}")
        else:
            print("  (no DB changes — re-run without --dry-run to apply)")


if __name__ == '__main__':
    main()
