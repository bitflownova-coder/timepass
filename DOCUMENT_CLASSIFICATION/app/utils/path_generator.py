"""
Path Generator — Phase 4 (VFS overhaul)

Generates VirtualPath rows for a document by applying each HierarchyTemplate
to the document's structured attributes (doc_type, client_name, doc_year).

One VirtualPath row is created per (document × view_name).
"""
from __future__ import annotations

import re
import logging
from typing import List

logger = logging.getLogger(__name__)

_UNKNOWN = 'Unknown'
_CLEAN_RE = re.compile(r'[<>:"/\\|?*\x00-\x1f]')   # chars illegal in paths


def _safe_segment(value) -> str:
    """Convert an attribute value to a clean path segment string."""
    if value is None:
        return _UNKNOWN
    s = str(value).strip()
    if not s:
        return _UNKNOWN
    s = _CLEAN_RE.sub('', s)
    return s[:80] or _UNKNOWN


def _attr_value(doc, attr_name: str) -> str:
    """Read a named attribute from a Document instance."""
    val = getattr(doc, attr_name, None)
    return _safe_segment(val)


def _attr_value_or_fallback(doc, attr_name: str, doc_type: str | None, attr: str) -> str:
    """
    Read an attribute from the document; return a meaningful fallback label
    (never bare 'Unknown') when the attribute is None or empty.
    """
    from app.utils.hierarchy_rules import get_fallback_label
    val = getattr(doc, attr_name, None)
    if val is None or str(val).strip() == '':
        return get_fallback_label(doc_type, attr)
    s = _CLEAN_RE.sub('', str(val).strip())
    return s[:80] or get_fallback_label(doc_type, attr)


class PathGenerator:
    """
    Generates and persists VirtualPath rows for a document.

    Usage (inside a Flask app context with an active DB session):

        from app.utils.path_generator import PathGenerator
        from app.models.virtual_path import HierarchyTemplate

        templates = HierarchyTemplate.query.filter_by(user_id=None).all()
        PathGenerator.generate_and_save(doc, templates, db)
    """

    @staticmethod
    def build_path(doc, template) -> dict:
        """
        Build a single virtual path dict from a document + template.

        For the 'by_type' view, the doc-type-specific hierarchy rule from
        hierarchy_rules.py overrides the generic template attribute order,
        allowing each document type to have a customised sub-tree layout.
        All other views use the template attributes as-is.

        Returns a dict ready to construct a VirtualPath instance:
            {view_name, path, level1, level2, level3}
        """
        # All views use get_view_rule() for per-doc-type attribute ordering;
        # missing attribute values get meaningful fallback labels (Phase G).
        from app.utils.hierarchy_rules import get_view_rule
        doc_type = getattr(doc, 'doc_type', None)
        rule = get_view_rule(doc_type, template.view_name)
        l1 = _attr_value_or_fallback(doc, rule['l1'], doc_type, rule['l1'])
        l2 = _attr_value_or_fallback(doc, rule['l2'], doc_type, rule['l2']) if rule.get('l2') else None
        l3 = _attr_value_or_fallback(doc, rule['l3'], doc_type, rule['l3']) if rule.get('l3') else None

        # Build slash-joined path from non-None, non-Unknown segments
        segments = [l1]
        if l2:
            segments.append(l2)
        if l3:
            segments.append(l3)

        path = '/'.join(segments)

        return {
            'view_name': template.view_name,
            'path': path,
            'level1': l1,
            'level2': l2,
            'level3': l3,
        }

    @staticmethod
    def generate_and_save(doc, templates: list, db) -> List:
        """
        Create or update VirtualPath rows for the given document.

        - Skips templates where all 3 levels would be 'Unknown'
          (document has no useful attributes).
        - Uses INSERT OR REPLACE semantics via delete+insert to handle
          the unique constraint (document_id, view_name).

        Returns a list of VirtualPath instances that were saved.
        """
        from app.models.virtual_path import VirtualPath

        saved = []
        for template in templates:
            path_data = PathGenerator.build_path(doc, template)

            # Skip if uninformative (all levels are Unknown)
            levels = [path_data['level1'], path_data.get('level2'), path_data.get('level3')]
            if all(v is None or v == _UNKNOWN for v in levels):
                logger.debug(f"Skipping uninformative path for doc={doc.id} view={template.view_name}")
                continue

            # Delete existing row for this (doc, view) if present
            existing = VirtualPath.query.filter_by(
                document_id=doc.id,
                view_name=template.view_name,
            ).first()
            if existing:
                db.session.delete(existing)

            vp = VirtualPath(
                document_id=doc.id,
                user_id=doc.user_id,
                view_name=path_data['view_name'],
                path=path_data['path'],
                level1=path_data['level1'],
                level2=path_data['level2'],
                level3=path_data['level3'],
            )
            db.session.add(vp)
            saved.append(vp)

        return saved
