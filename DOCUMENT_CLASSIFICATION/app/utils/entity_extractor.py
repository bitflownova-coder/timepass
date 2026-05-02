"""
Entity Extraction - spaCy PERSON/ORG extraction with graceful fallback
"""
import logging
import re
from typing import List, Dict

logger = logging.getLogger(__name__)

try:
    import spacy
    _SPACY_AVAILABLE = True
except ImportError:
    spacy = None
    _SPACY_AVAILABLE = False

_NLP = None

# Common organization suffixes/terms to avoid mislabeling as person names
_ORG_STOP = {
    'pvt', 'ltd', 'llp', 'inc', 'corp', 'company', 'co', 'private', 'limited',
    'group', 'solutions', 'technologies', 'systems', 'services', 'international',
}


def _clean_entity(text: str) -> str:
    text = re.sub(r'\s+', ' ', text or '').strip()
    text = re.sub(r"^[\W_]+|[\W_]+$", '', text)
    return text


def _load_nlp():
    global _NLP
    if _NLP is not None:
        return _NLP
    if not _SPACY_AVAILABLE:
        return None
    try:
        _NLP = spacy.load('en_core_web_sm', disable=['parser', 'lemmatizer'])
    except Exception as exc:
        logger.warning(f"spaCy model not available: {exc}")
        _NLP = None
    return _NLP


class EntityExtractor:
    """Extract PERSON and ORG entities using spaCy if available."""

    @staticmethod
    def is_available() -> bool:
        return _load_nlp() is not None

    @staticmethod
    def extract(text: str, max_chars: int = 5000) -> Dict[str, List[str]]:
        nlp = _load_nlp()
        if not nlp:
            return {"persons": [], "orgs": []}

        sample = (text or '')[:max_chars]
        if not sample.strip():
            return {"persons": [], "orgs": []}

        doc = nlp(sample)
        persons: List[str] = []
        orgs: List[str] = []

        for ent in doc.ents:
            cleaned = _clean_entity(ent.text)
            if not cleaned:
                continue
            if ent.label_ == 'PERSON':
                persons.append(cleaned)
            elif ent.label_ == 'ORG':
                orgs.append(cleaned)

        # Deduplicate, preserve order
        def _dedupe(items: List[str]) -> List[str]:
            seen = set()
            out = []
            for item in items:
                key = item.lower()
                if key in seen:
                    continue
                seen.add(key)
                out.append(item)
            return out

        persons = _dedupe(persons)
        orgs = _dedupe(orgs)

        # Filter obvious org words from person list
        filtered_persons = []
        for p in persons:
            parts = [w.lower() for w in p.split()]
            if any(w in _ORG_STOP for w in parts):
                continue
            filtered_persons.append(p)

        return {"persons": filtered_persons, "orgs": orgs}
