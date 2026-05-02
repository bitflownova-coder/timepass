"""
Reprocessor — Phase E (VFS Architecture Refinement)

Re-extracts text and attributes from an already-stored encrypted document,
updates Document model fields, and rebuilds VirtualPath rows.

Used by:
  - POST /api/documents/<id>/reprocess  (API endpoint)
  - scripts/watch_folder.py             (on file-modification events)

Typical call:
    result = Reprocessor.reprocess(doc_id, db)
    # result = {success, doc_id, changes: {field: {old, new}}}
"""
from __future__ import annotations

import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


class Reprocessor:
    """
    Stateless reprocessing pipeline for a single document.
    Must be called inside a Flask app context.
    """

    @staticmethod
    def reprocess(
        doc_id: int,
        db,
        classifier=None,       # optional: pre-loaded Classifier instance
        force: bool = False,   # if True, skip the "nothing changed" short-circuit
    ) -> dict:
        """
        Re-extract, re-classify, and rebuild virtual paths for one document.

        Args:
            doc_id:     Document.id to reprocess.
            db:         The SQLAlchemy db instance (from app.models).
            classifier: Optional pre-loaded Classifier; one is created if None.
            force:      Re-run even when attributes appear unchanged.

        Returns:
            dict: {success, doc_id, changes: {field: {old, new}}}
        """
        from app.models.document import Document
        from app.models.virtual_path import HierarchyTemplate
        from app.utils.file_storage import FileStorage
        from app.utils.text_extractor import TextExtractor, TextPreprocessor
        from app.utils.entity_extractor import EntityExtractor
        from app.utils.attribute_extractor import AttributeExtractor
        from app.utils.path_generator import PathGenerator

        _RETRY_DELAYS = [0.5, 1.0, 2.0]
        last_error: str = ''

        for attempt, delay in enumerate([0] + _RETRY_DELAYS):
            if delay:
                time.sleep(delay)
            try:
                result = Reprocessor._run_pipeline(
                    doc_id, db, classifier, force,
                    Document, HierarchyTemplate, FileStorage,
                    TextExtractor, TextPreprocessor, EntityExtractor,
                    AttributeExtractor, PathGenerator,
                )
                return result
            except (FileNotFoundError, KeyError) as e:
                logger.warning(f"Reprocessor non-retriable error (doc={doc_id}, attempt={attempt}): {e}")
                return {'success': False, 'error': str(e)}
            except Exception as e:
                last_error = str(e)
                logger.warning(f"Reprocessor transient error (doc={doc_id}, attempt={attempt}): {e}")

        logger.error(f"Reprocessor failed after {len(_RETRY_DELAYS)+1} attempts (doc={doc_id}): {last_error}")
        return {'success': False, 'error': last_error}

    @staticmethod
    def _run_pipeline(
        doc_id, db, classifier, force,
        Document, HierarchyTemplate, FileStorage,
        TextExtractor, TextPreprocessor, EntityExtractor,
        AttributeExtractor, PathGenerator,
    ) -> dict:
        """Single attempt of the reprocessing pipeline."""
        # ── 1. Load Document ─────────────────────────────────────────────────
        doc = Document.query.filter_by(id=doc_id, deleted_at=None).first()
        if not doc:
            return {'success': False, 'error': f"Document {doc_id} not found"}

        if not doc.file_path or not Path(doc.file_path).exists():
            return {'success': False, 'error': f"File not found: {doc.file_path}"}

        # ── 2. Decrypt to temp file ──────────────────────────────────────────
        storage = FileStorage()
        tmp_fd, tmp_path = tempfile.mkstemp(suffix='_reprocess')
        os.close(tmp_fd)

        try:
            dec = storage.encryption.decrypt_file(doc.file_path, tmp_path)
            if not dec or not dec.get('success'):
                return {'success': False,
                        'error': f"Decryption failed: {(dec or {}).get('error', 'unknown')}"}

            # ── 3. Re-extract text ───────────────────────────────────────────
            extraction = TextExtractor.extract_text(tmp_path) or {}
            raw_text = extraction.get('text', '') or ''
            if raw_text:
                raw_text = TextPreprocessor.clean(raw_text)

            # ── 4. Re-run entity extraction ──────────────────────────────────
            entities = EntityExtractor.extract(raw_text) if raw_text else {}

            # ── 5. Re-run attribute extraction ───────────────────────────────
            if classifier is None:
                from app.utils.classifier import Classifier
                classifier = Classifier()

            attrs = AttributeExtractor.extract(
                filename=doc.original_filename,
                raw_text=raw_text,
                entities=entities,
                classifier=classifier,
                user_id=doc.user_id,
                db=db,
            )

            # ── 6. Detect changes ────────────────────────────────────────────
            changes: dict = {}
            for field, new_val in [
                ('doc_type',    attrs.doc_type),
                ('client_name', attrs.client_name),
                ('doc_year',    attrs.doc_year),
            ]:
                old_val = getattr(doc, field)
                if old_val != new_val:
                    changes[field] = {'old': old_val, 'new': new_val}

            if not changes and not force:
                return {'success': True, 'doc_id': doc_id, 'changes': {}, 'message': 'no change'}

            # ── 7. Update Document fields ────────────────────────────────────
            doc.doc_type    = attrs.doc_type
            doc.client_name = attrs.client_name
            doc.doc_year    = attrs.doc_year

            if raw_text:
                doc.extracted_text = raw_text[:10000]
                doc.text_preview   = raw_text[:500]

            # ── 8. Rebuild VirtualPaths ──────────────────────────────────────
            templates = HierarchyTemplate.query.filter_by(user_id=None).all()
            PathGenerator.generate_and_save(doc, templates, db)

            db.session.commit()
            logger.info(f"Reprocessed doc {doc_id}: {changes}")
            return {'success': True, 'doc_id': doc_id, 'changes': changes}

        except Exception as e:
            db.session.rollback()
            logger.error(f"Reprocessor error (doc={doc_id}): {e}")
            return {'success': False, 'error': str(e)}
        finally:
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
