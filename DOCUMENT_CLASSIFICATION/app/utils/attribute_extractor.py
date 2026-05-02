"""
Attribute Extractor — Phase 3 (VFS overhaul)

Wraps the existing rule engine, entity extractor, and ML classifier to produce
a structured AttributeSet (doc_type, client_name, year, confidence) instead of
a raw folder string.

Backward compatibility: AttributeSet.doc_type == the old predicted_label value.
The upload pipeline stores doc_type in BOTH predicted_label/user_folder (old)
AND doc_type/client_name/doc_year (new).
"""
from __future__ import annotations

import re
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

_YEAR_RE = re.compile(r'\b(19[5-9]\d|20[0-2]\d)\b')

# Attribute names that map to Document columns
ATTR_DOC_TYPE    = 'doc_type'
ATTR_CLIENT_NAME = 'client_name'
ATTR_DOC_YEAR    = 'doc_year'


@dataclass
class AttributeSet:
    """Structured attributes extracted from a document."""
    doc_type:    str            = 'General'
    client_name: Optional[str] = None
    doc_year:    Optional[int] = None
    confidence:  float          = 0.0
    all_predictions: list       = field(default_factory=list)


class AttributeExtractor:
    """
    Unified attribute extraction pipeline.

    Usage:
        attrs = AttributeExtractor.extract(
            filename   = original_filename,
            raw_text   = extracted_text,
            entities   = {'persons': [...], 'orgs': [...]},
            classifier = classifier_instance_or_None,
            user_id    = user_id,
            db         = db,           # SQLAlchemy db (for existing-folder checks)
            manual_category = '' ,     # user override
        )
    """

    @staticmethod
    def extract(
        filename: str,
        raw_text: str,
        entities: dict,
        classifier=None,
        user_id: int = 0,
        db=None,
        manual_category: str = '',
    ) -> AttributeSet:
        """
        Returns an AttributeSet with all attributes populated.
        """
        # ── Manual override ──────────────────────────────────────────────────
        if manual_category:
            year = AttributeExtractor._extract_year(raw_text)
            from app.utils.entity_resolver import EntityResolver
            resolved = EntityResolver.multi_source_extract(filename, raw_text, entities, user_id=user_id, db=db)
            client = resolved['name']
            return AttributeSet(
                doc_type=manual_category,
                client_name=client,
                doc_year=year,
                confidence=1.0,
            )

        # ── Extract client name via multi-source entity resolution ────────────
        from app.utils.entity_resolver import EntityResolver
        resolved = EntityResolver.multi_source_extract(filename, raw_text, entities, user_id=user_id, db=db)
        client = resolved['name']  # None when confidence < 0.50

        # ── Extract year ─────────────────────────────────────────────────────
        year = AttributeExtractor._extract_year(raw_text)

        # ── Determine doc_type via existing priority pipeline ─────────────────
        # Import here to avoid circular imports; these functions live in upload.py
        # but we call the same logic via the shared utility functions.
        from app.routes.upload import (
            _has_bitflow,
            _extract_person_name,
            _match_existing_person_folder,
            _match_existing_keyword_folder,
            _extract_name_hint,
            _derive_folder_from_content,
            _PERSONAL_MARKERS,
        )

        doc_type = 'General'
        confidence = 0.0
        all_predictions: list = []

        if _has_bitflow(filename, raw_text):
            doc_type = 'Bitflow'
            confidence = 0.95
        else:
            person_name = _extract_person_name(filename, raw_text)
            # EntityResolver already extracted client; only fall back to
            # person_name when entity resolver returned None.
            if not client and person_name:
                client = person_name

            matched_folder = None
            if db and user_id and person_name:
                matched_folder = _match_existing_person_folder(user_id, person_name)

            if person_name:
                doc_type = matched_folder or person_name
                confidence = 0.9
            else:
                keyword_folder = None
                if db and user_id:
                    keyword_folder = _match_existing_keyword_folder(user_id, filename, raw_text)

                if keyword_folder:
                    doc_type = keyword_folder
                    confidence = 0.9
                else:
                    name_hint = _extract_name_hint(filename)
                    matched_hint = None
                    if db and user_id and name_hint:
                        matched_hint = _match_existing_person_folder(user_id, name_hint)

                    raw_lower = (raw_text or '').lower()
                    filename_lower = filename.lower()
                    has_marker = any(m in filename_lower for m in _PERSONAL_MARKERS)
                    name_in_text = bool(name_hint and name_hint.lower() in raw_lower)

                    if matched_hint:
                        doc_type = matched_hint
                        confidence = 0.85
                    elif name_hint and has_marker and name_in_text:
                        doc_type = name_hint
                        confidence = 0.8
                    else:
                        doc_type = _derive_folder_from_content(filename, raw_text)
                        confidence = 0.85

                        # ML fallback
                        if classifier and raw_text:
                            try:
                                from app.utils.text_extractor import TextPreprocessor
                                processed = TextPreprocessor.preprocess(raw_text)
                                if processed and classifier.is_trained:
                                    pred = classifier.predict(processed, return_probabilities=True)
                                    if pred.get('success') and pred['confidence_score'] >= 0.75:
                                        doc_type = pred['predicted_label']
                                        confidence = pred['confidence_score']
                                        all_predictions = pred.get('all_predictions', [])
                            except Exception as clf_err:
                                logger.warning(f"Classifier error in AttributeExtractor: {clf_err}")

        return AttributeSet(
            doc_type=doc_type,
            client_name=client or None,
            doc_year=year,
            confidence=confidence,
            all_predictions=all_predictions,
        )

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_client(entities: dict) -> Optional[str]:
        """Return the first valid PERSON entity, else None."""
        if not entities:
            return None
        persons = entities.get('persons', [])
        if persons:
            name = persons[0].strip()
            if name:
                return name
        return None

    @staticmethod
    def _extract_year(raw_text: str) -> int:
        """Return first 4-digit year found in text, else current year."""
        m = _YEAR_RE.search((raw_text or '')[:5000])
        if m:
            return int(m.group(1))
        return datetime.utcnow().year
