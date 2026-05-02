"""
Entity Resolver — Phase C (VFS Architecture Refinement)

Provides:
    normalize_name(raw)            → str   (strips legal suffixes/titles)
    EntityResolver.multi_source_extract(...)  → {name, confidence, source}

Priority order for client-name extraction:
    1. spaCy PERSON entities        → confidence 0.85
    2. Filename name-hint regex     → confidence 0.65
    3. Metadata author field        → confidence 0.50
    4. < 0.50 threshold             → returns None
"""
from __future__ import annotations

import re
from typing import Optional

# ── Normalisation patterns ─────────────────────────────────────────────────

# Legal/corporate suffixes to strip from company/person names
_LEGAL_SUFFIX_RE = re.compile(
    r'\b('
    r'pvt\.?\s*ltd\.?|private\s+limited|pvt\.?\s*limited|'
    r'pvt|ltd|llp|inc|corp|co\.?|limited|private'
    r')\b[\s.,]*$',
    re.IGNORECASE,
)

# Honorific title prefixes to strip before returning a person name
_TITLE_PREFIX_RE = re.compile(
    r'^(mr\.?|mrs\.?|ms\.?|miss|dr\.?|prof\.?|sir|master)\s+',
    re.IGNORECASE,
)

# Words that are document/place keywords, not valid name components
_NAME_BLOCKLIST = {
    'resume', 'invoice', 'certificate', 'report', 'document', 'agreement',
    'contract', 'statement', 'letter', 'application', 'form', 'receipt',
    'policy', 'record', 'notice', 'order', 'proposal', 'schedule', 'summary',
    'minutes', 'agenda', 'memo', 'notification', 'guideline', 'manual',
    'handbook', 'brochure', 'catalog', 'presentation', 'slides', 'sheet',
    'draft', 'final', 'copy', 'original', 'scan', 'scanned', 'updated',
    'revised', 'signed', 'unsigned', 'new', 'old', 'latest', 'internship',
    'offer', 'appointment', 'joining', 'training', 'experience', 'employment',
    'work', 'job', 'position', 'role', 'designation', 'founder', 'assessment',
    'evaluation', 'bitflow',
    'legal', 'contract', 'agreement', 'clause', 'terms', 'condition',
    'liability', 'arbitration', 'jurisdiction', 'compliance', 'affidavit',
    'billing', 'payment', 'balance', 'account', 'salary', 'payroll',
    'insurance', 'premium', 'property', 'lease', 'mortgage',
    'general', 'other', 'misc', 'miscellaneous', 'various', 'combined',
    'company', 'organization', 'department', 'division', 'branch', 'office',
    'school', 'college', 'university', 'institute', 'hospital', 'clinic',
    'government', 'ministry', 'national', 'international', 'private', 'limited',
    'pvt', 'ltd', 'llp', 'inc', 'corp', 'india', 'delhi', 'mumbai', 'bangalore',
    'the', 'and', 'for', 'from', 'with', 'our',
    'file', 'scan', 'img', 'pdf', 'doc', 'docx', 'jpg', 'png', 'image', 'photo',
    'screenshot', 'download', 'upload', 'backup', 'temp', 'test', 'sample',
    'january', 'february', 'march', 'april', 'may', 'june', 'july', 'august',
    'september', 'october', 'november', 'december',
    'jan', 'feb', 'mar', 'apr', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec',
    'mr', 'mrs', 'ms', 'miss', 'dr', 'prof', 'sir', 'master',
}

# Minimum confidence to return a non-None name
_MIN_CONFIDENCE = 0.50


def normalize_name(raw: str) -> str:
    """
    Normalize a person or organization name:
      - Strip legal suffixes (Pvt Ltd, LLP, Inc …)
      - Strip honorific prefixes (Mr., Dr., Prof. …)
      - Collapse whitespace and title-case the result.

    >>> normalize_name("ABC Pvt. Ltd.")
    'Abc'
    >>> normalize_name("dr. john smith")
    'John Smith'
    """
    if not raw:
        return raw
    s = _LEGAL_SUFFIX_RE.sub('', raw).strip(' .,')
    s = _TITLE_PREFIX_RE.sub('', s).strip()
    s = ' '.join(s.split())          # collapse internal whitespace
    return s.title() if s else raw


class EntityResolver:
    """
    Multi-source person/client-name extractor with confidence tiers.

    Priority (highest first):
        1. spaCy PERSON entities from EntityExtractor  → 0.85
        2. Name-like tokens from the file's stem        → 0.65
        3. Document metadata author field               → 0.50

    A result below _MIN_CONFIDENCE (0.50) returns name=None.
    """

    @staticmethod
    def multi_source_extract(
        filename: str,
        raw_text: str,
        entities: dict,
        metadata_author: Optional[str] = None,
        user_id: int = 0,
        db=None,
    ) -> dict:
        """
        Args:
            filename:        Original filename (with extension).
            raw_text:        Plain text extracted from the document.
            entities:        Dict from EntityExtractor.extract() → {persons, orgs}.
            metadata_author: PDF/DOCX author metadata string, if available.
            user_id:         Owning user ID — passed to EntityCanonicalizer.
            db:              SQLAlchemy db object — passed to EntityCanonicalizer.

        Returns:
            dict: {name: str|None, confidence: float, source: str}
        """
        def _canon(n):
            if n and user_id and db is not None:
                return EntityCanonicalizer.canonicalize(n, user_id, db)
            return n

        # ── Source 1: spaCy PERSON (most reliable) ──────────────────────────
        persons = (entities or {}).get('persons', [])
        for raw in persons:
            name = normalize_name(raw.strip())
            if name and name.lower() not in _NAME_BLOCKLIST and len(name) > 2:
                return {'name': _canon(name), 'confidence': 0.85, 'source': 'spacy'}

        # ── Source 2: Filename name-hint ────────────────────────────────────
        stem = filename.rsplit('.', 1)[0] if '.' in filename else filename
        stem_clean = re.sub(r'[_\-]+', ' ', stem).strip()
        parts = [
            p for p in stem_clean.split()
            if re.match(r'^[A-Za-z]{2,20}$', p)
            and p.lower() not in _NAME_BLOCKLIST
        ]
        if len(parts) >= 2:
            name = normalize_name(' '.join(parts[:2]))
            if name and len(name) > 3:
                return {'name': _canon(name), 'confidence': 0.65, 'source': 'filename'}

        # ── Source 3: Metadata author ────────────────────────────────────────
        if metadata_author:
            name = normalize_name(metadata_author.strip())
            if name and name.lower() not in _NAME_BLOCKLIST and len(name) > 2:
                return {'name': _canon(name), 'confidence': 0.50, 'source': 'metadata'}

        # Below threshold → no client name
        return {'name': None, 'confidence': 0.0, 'source': 'none'}


class EntityCanonicalizer:
    """
    Fuzzy-match a raw client name against existing client_name values for a user.
    Prevents near-duplicate names (e.g. "Acme Corp" vs "Acme Corporation") from
    creating separate VFS branches.
    """

    _RATIO_THRESHOLD = 0.82

    @staticmethod
    def canonicalize(raw_name: str, user_id: int, db) -> str:
        """
        Normalize raw_name, then fuzzy-match against existing client_name values
        for the given user.  Returns the existing canonical string if the best
        difflib ratio exceeds _RATIO_THRESHOLD; otherwise returns the normalized
        form of raw_name.

        Args:
            raw_name:  Raw extracted name string.
            user_id:   ID of the owning user (used to scope DB query).
            db:        SQLAlchemy session / db object (must have .session).

        Returns:
            str: Canonical client name.
        """
        import difflib
        from app.models.document import Document

        normalized = normalize_name(raw_name)
        if not normalized or not user_id or db is None:
            return normalized

        existing = (
            db.session.query(Document.client_name)
            .filter_by(user_id=user_id, deleted_at=None)
            .filter(Document.client_name.isnot(None))
            .distinct()
            .all()
        )

        best_ratio = 0.0
        best_canonical = normalized
        for (name,) in existing:
            if not name:
                continue
            ratio = difflib.SequenceMatcher(
                None, normalized.lower(), name.lower()
            ).ratio()
            if ratio > best_ratio:
                best_ratio = ratio
                best_canonical = name

        return best_canonical if best_ratio > EntityCanonicalizer._RATIO_THRESHOLD else normalized
