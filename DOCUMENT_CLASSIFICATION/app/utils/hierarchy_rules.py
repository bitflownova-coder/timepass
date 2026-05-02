"""
Hierarchy Rules — Phase D + G (VFS Architecture Refinement)

Provides:
    get_rule(doc_type)                         → {l1, l2, l3}  (by_type view)
    get_view_rule(doc_type, view_name)         → {l1, l2, l3}  (any view)
    get_fallback_label(doc_type, attr)         → str           (instead of "Unknown")

All three views (by_type / by_client / by_time) get per-doc-type attribute
order overrides.  Missing attribute values get meaningful fallback labels
instead of the generic "Unknown".
"""
from __future__ import annotations

# ─────────────────────────────────────────────────────────────────────────────
# Per-view, per-doc-type attribute order rules
# Keys: (lowercase doc_type, view_name) → {l1, l2, l3}
# Fallback chain: specific key → ('_default', view_name) → absolute default
# ─────────────────────────────────────────────────────────────────────────────

VIEW_RULES: dict[tuple[str, str], dict] = {

    # ══════════════════════════════════════════════════════════════════════
    # by_type  —  L1 always doc_type; L2/L3 vary by domain
    # ══════════════════════════════════════════════════════════════════════
    ('invoices',           'by_type'): {'l1': 'doc_type', 'l2': 'client_name', 'l3': 'doc_year'},
    ('invoice',            'by_type'): {'l1': 'doc_type', 'l2': 'client_name', 'l3': 'doc_year'},
    ('receipts',           'by_type'): {'l1': 'doc_type', 'l2': 'client_name', 'l3': 'doc_year'},
    ('purchase orders',    'by_type'): {'l1': 'doc_type', 'l2': 'client_name', 'l3': 'doc_year'},
    ('financial reports',  'by_type'): {'l1': 'doc_type', 'l2': 'doc_year',    'l3': 'client_name'},
    ('bank statements',    'by_type'): {'l1': 'doc_type', 'l2': 'client_name', 'l3': 'doc_year'},
    ('billing',            'by_type'): {'l1': 'doc_type', 'l2': 'client_name', 'l3': 'doc_year'},
    ('tax documents',      'by_type'): {'l1': 'doc_type', 'l2': 'doc_year',    'l3': 'client_name'},
    ('tax',                'by_type'): {'l1': 'doc_type', 'l2': 'doc_year',    'l3': 'client_name'},
    ('resume',             'by_type'): {'l1': 'doc_type', 'l2': 'client_name', 'l3': 'doc_year'},
    ('offer letters',      'by_type'): {'l1': 'doc_type', 'l2': 'client_name', 'l3': 'doc_year'},
    ('payslips',           'by_type'): {'l1': 'doc_type', 'l2': 'client_name', 'l3': 'doc_year'},
    ('certificates',       'by_type'): {'l1': 'doc_type', 'l2': 'client_name', 'l3': 'doc_year'},
    ('identity documents', 'by_type'): {'l1': 'doc_type', 'l2': 'client_name', 'l3': 'doc_year'},
    ('contracts',          'by_type'): {'l1': 'doc_type', 'l2': 'client_name', 'l3': 'doc_year'},
    ('legal documents',    'by_type'): {'l1': 'doc_type', 'l2': 'client_name', 'l3': 'doc_year'},
    ('agreements',         'by_type'): {'l1': 'doc_type', 'l2': 'client_name', 'l3': 'doc_year'},
    ('property documents', 'by_type'): {'l1': 'doc_type', 'l2': 'client_name', 'l3': 'doc_year'},
    ('academic',           'by_type'): {'l1': 'doc_type', 'l2': 'client_name', 'l3': 'doc_year'},
    ('medical',            'by_type'): {'l1': 'doc_type', 'l2': 'client_name', 'l3': 'doc_year'},
    ('insurance',          'by_type'): {'l1': 'doc_type', 'l2': 'client_name', 'l3': 'doc_year'},
    ('training',           'by_type'): {'l1': 'doc_type', 'l2': 'client_name', 'l3': 'doc_year'},
    ('bitflow',            'by_type'): {'l1': 'doc_type', 'l2': 'doc_year',    'l3': 'client_name'},
    ('_default',           'by_type'): {'l1': 'doc_type', 'l2': 'client_name', 'l3': 'doc_year'},

    # ══════════════════════════════════════════════════════════════════════
    # by_client  —  L1 always client_name; L2/L3 vary
    # ══════════════════════════════════════════════════════════════════════
    ('invoices',           'by_client'): {'l1': 'client_name', 'l2': 'doc_type',   'l3': 'doc_year'},
    ('tax documents',      'by_client'): {'l1': 'client_name', 'l2': 'doc_year',   'l3': 'doc_type'},
    ('tax',                'by_client'): {'l1': 'client_name', 'l2': 'doc_year',   'l3': 'doc_type'},
    ('financial reports',  'by_client'): {'l1': 'client_name', 'l2': 'doc_year',   'l3': 'doc_type'},
    ('bank statements',    'by_client'): {'l1': 'client_name', 'l2': 'doc_year',   'l3': 'doc_type'},
    ('identity documents', 'by_client'): {'l1': 'client_name', 'l2': 'doc_type',   'l3': 'doc_year'},
    ('bitflow',            'by_client'): {'l1': 'client_name', 'l2': 'doc_year',   'l3': 'doc_type'},
    ('_default',           'by_client'): {'l1': 'client_name', 'l2': 'doc_type',   'l3': 'doc_year'},

    # ══════════════════════════════════════════════════════════════════════
    # by_time  —  L1 always doc_year; L2/L3 vary
    # ══════════════════════════════════════════════════════════════════════
    ('invoices',           'by_time'): {'l1': 'doc_year', 'l2': 'client_name', 'l3': 'doc_type'},
    ('tax documents',      'by_time'): {'l1': 'doc_year', 'l2': 'doc_type',    'l3': 'client_name'},
    ('tax',                'by_time'): {'l1': 'doc_year', 'l2': 'doc_type',    'l3': 'client_name'},
    ('financial reports',  'by_time'): {'l1': 'doc_year', 'l2': 'doc_type',    'l3': 'client_name'},
    ('bank statements',    'by_time'): {'l1': 'doc_year', 'l2': 'client_name', 'l3': 'doc_type'},
    ('resume',             'by_time'): {'l1': 'doc_year', 'l2': 'client_name', 'l3': 'doc_type'},
    ('certificates',       'by_time'): {'l1': 'doc_year', 'l2': 'client_name', 'l3': 'doc_type'},
    ('bitflow',            'by_time'): {'l1': 'doc_year', 'l2': 'doc_type',    'l3': 'client_name'},
    ('_default',           'by_time'): {'l1': 'doc_year', 'l2': 'doc_type',    'l3': 'client_name'},
}

# ─────────────────────────────────────────────────────────────────────────────
# Fallback labels: meaningful strings shown when an attribute is missing/None
# Key: (lowercase doc_type, attribute_name) → fallback label string
# ─────────────────────────────────────────────────────────────────────────────

FALLBACK_LABELS: dict[tuple[str, str], str] = {
    # client_name fallbacks
    ('invoices',           'client_name'): 'No Client',
    ('invoice',            'client_name'): 'No Client',
    ('receipts',           'client_name'): 'No Client',
    ('purchase orders',    'client_name'): 'No Client',
    ('contracts',          'client_name'): 'No Party',
    ('agreements',         'client_name'): 'No Party',
    ('legal documents',    'client_name'): 'No Party',
    ('property documents', 'client_name'): 'No Party',
    ('resume',             'client_name'): 'Unknown Candidate',
    ('offer letters',      'client_name'): 'Unknown Candidate',
    ('payslips',           'client_name'): 'Unknown Employee',
    ('certificates',       'client_name'): 'Unknown Recipient',
    ('identity documents', 'client_name'): 'Personal',
    ('medical',            'client_name'): 'Personal',
    ('insurance',          'client_name'): 'Personal',
    ('academic',           'client_name'): 'Unknown Student',
    ('bank statements',    'client_name'): 'Personal',
    ('tax documents',      'client_name'): 'Personal',
    ('tax',                'client_name'): 'Personal',
    ('financial reports',  'client_name'): 'Unattributed',
    ('bitflow',            'client_name'): 'Internal',
    ('_default',           'client_name'): 'No Client',

    # doc_year fallbacks
    ('tax documents',      'doc_year'): 'Undated',
    ('tax',                'doc_year'): 'Undated',
    ('financial reports',  'doc_year'): 'Undated',
    ('bank statements',    'doc_year'): 'Undated',
    ('invoices',           'doc_year'): 'Undated',
    ('receipts',           'doc_year'): 'Undated',
    ('contracts',          'doc_year'): 'Undated',
    ('agreements',         'doc_year'): 'Undated',
    ('_default',           'doc_year'): 'Undated',

    # doc_type fallbacks (rare — doc_type should always be set)
    ('_default',           'doc_type'): 'General',
}


def get_view_rule(doc_type: str | None, view_name: str) -> dict:
    """
    Return the hierarchy attribute rule for a (doc_type, view_name) pair.

    Lookup order:
        1. (lowercase doc_type, view_name)  — specific
        2. ('_default', view_name)           — view-level default
        3. hard-coded absolute default       — doc_type / client_name / doc_year

    Returns:
        dict with keys: l1, l2, l3  (Document attribute names)
    """
    key = (doc_type.strip().lower() if doc_type else '_default', view_name)
    if key in VIEW_RULES:
        return VIEW_RULES[key]
    default_key = ('_default', view_name)
    return VIEW_RULES.get(default_key, {'l1': 'doc_type', 'l2': 'client_name', 'l3': 'doc_year'})


def get_rule(doc_type: str | None) -> dict:
    """Backward-compat: return by_type rule for a doc_type."""
    return get_view_rule(doc_type, 'by_type')


def get_fallback_label(doc_type: str | None, attr: str) -> str:
    """
    Return a meaningful label for a missing/empty attribute value.

    Args:
        doc_type: Document.doc_type (may be None)
        attr:     Attribute name, e.g. 'client_name', 'doc_year', 'doc_type'

    Returns:
        Human-readable fallback string, never 'Unknown'
    """
    key = (doc_type.strip().lower() if doc_type else '_default', attr)
    if key in FALLBACK_LABELS:
        return FALLBACK_LABELS[key]
    default_key = ('_default', attr)
    return FALLBACK_LABELS.get(default_key, 'Unknown')
