"""
Search Routes - Full-text keyword search across documents
"""
import re
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import or_
from app.models import db
from app.models.document import Document
from app.utils.validators import sanitize_input

logger = logging.getLogger(__name__)

search_bp = Blueprint('search', __name__, url_prefix='/api/search')


def _parse_nl_time(q: str):
    """
    Extract time constraints from a natural-language query.
    Returns (clean_q, date_from, date_to) where dates are datetime or None.
    Handles phrases like:
      '2hr ago', 'last 3 hours', 'yesterday', 'last week',
      'uploaded today', 'past 2 days', 'last month'
    """
    now = datetime.utcnow()
    date_from = None
    date_to = None

    # Patterns to strip from the query
    time_pattern = re.compile(
        r'\b('
        r'(\d+)\s*(?:hr|hour|hrs|hours)\s*ago'            # "2hr ago", "3 hours ago"
        r'|last\s+(\d+)\s*(?:hr|hour|hrs|hours)'          # "last 3 hours"
        r'|past\s+(\d+)\s*(?:hr|hour|hrs|hours)'          # "past 2 hours"
        r'|(\d+)\s*(?:min|mins|minute|minutes)\s*ago'     # "30 mins ago"
        r'|last\s+(\d+)\s*(?:day|days)'                   # "last 3 days"
        r'|past\s+(\d+)\s*(?:day|days)'                   # "past 2 days"
        r'|(\d+)\s*(?:day|days)\s*ago'                    # "2 days ago"
        r'|yesterday'                                      # "yesterday"
        r'|today'                                          # "today"
        r'|last\s+week'                                    # "last week"
        r'|last\s+month'                                   # "last month"
        r'|this\s+week'                                    # "this week"
        r'|this\s+month'                                   # "this month"
        r'|recent(?:ly)?'                                  # "recently"
        r')',
        re.IGNORECASE
    )

    def _process_match(m):
        nonlocal date_from, date_to
        txt = m.group(0).lower().strip()

        if re.match(r'(\d+)\s*(?:hr|hour|hrs|hours)\s*ago', txt):
            n = int(re.search(r'\d+', txt).group())
            date_from = now - timedelta(hours=n)
        elif re.match(r'last\s+(\d+)\s*(?:hr|hour|hrs|hours)', txt):
            n = int(re.search(r'\d+', txt).group())
            date_from = now - timedelta(hours=n)
        elif re.match(r'past\s+(\d+)\s*(?:hr|hour|hrs|hours)', txt):
            n = int(re.search(r'\d+', txt).group())
            date_from = now - timedelta(hours=n)
        elif re.match(r'(\d+)\s*(?:min|mins|minute|minutes)\s*ago', txt):
            n = int(re.search(r'\d+', txt).group())
            date_from = now - timedelta(minutes=n)
        elif re.match(r'last\s+(\d+)\s*(?:day|days)', txt):
            n = int(re.search(r'\d+', txt).group())
            date_from = now - timedelta(days=n)
        elif re.match(r'past\s+(\d+)\s*(?:day|days)', txt):
            n = int(re.search(r'\d+', txt).group())
            date_from = now - timedelta(days=n)
        elif re.match(r'(\d+)\s*(?:day|days)\s*ago', txt):
            n = int(re.search(r'\d+', txt).group())
            date_from = now - timedelta(days=n)
        elif txt == 'yesterday':
            date_from = (now - timedelta(days=1)).replace(hour=0, minute=0, second=0)
            date_to   = (now - timedelta(days=1)).replace(hour=23, minute=59, second=59)
        elif txt == 'today':
            date_from = now.replace(hour=0, minute=0, second=0)
        elif txt in ('last week', 'this week'):
            date_from = now - timedelta(weeks=1)
        elif txt in ('last month', 'this month'):
            date_from = now - timedelta(days=30)
        elif txt.startswith('recent'):
            date_from = now - timedelta(days=7)

    for m in time_pattern.finditer(q):
        _process_match(m)

    clean_q = time_pattern.sub('', q)
    # Remove filler words left after stripping time phrases
    clean_q = re.sub(
        r'\b(give\s+me|show\s+me|find|search|that\s+i|i\s+have|uploaded?|upload|file|files|which|was|were|the|a|an)\b',
        ' ', clean_q, flags=re.IGNORECASE
    )
    clean_q = re.sub(r'\s{2,}', ' ', clean_q).strip()

    return clean_q, date_from, date_to


@search_bp.route('', methods=['GET'])
@jwt_required()
def search_documents():
    """
    Full-text search with natural-language time parsing.

    Query params:
        q          (str)  - search term; supports phrases like "2hr ago", "yesterday"
        category   (str)  - filter by predicted_label
        date_from  (str)  - ISO date  YYYY-MM-DD (ignored if NL time found in q)
        date_to    (str)  - ISO date  YYYY-MM-DD
        page       (int)  - default 1
        per_page   (int)  - default 20, max 100
    """
    user_id = int(get_jwt_identity())

    raw_q      = sanitize_input(request.args.get('q', '').strip())
    category   = sanitize_input(request.args.get('category', '').strip())
    date_from  = request.args.get('date_from', '').strip()
    date_to    = request.args.get('date_to', '').strip()
    page       = max(1, request.args.get('page', 1, type=int))
    per_page   = min(100, max(1, request.args.get('per_page', 20, type=int)))

    # ---- natural language time parsing ----
    nl_date_from = None
    nl_date_to   = None
    q = raw_q
    if raw_q:
        q, nl_date_from, nl_date_to = _parse_nl_time(raw_q)

    # NL-parsed dates override explicit date params
    if nl_date_from:
        dt_from = nl_date_from
    elif date_from:
        try:
            dt_from = datetime.fromisoformat(date_from)
        except ValueError:
            dt_from = None
    else:
        dt_from = None

    if nl_date_to:
        dt_to = nl_date_to
    elif date_to:
        try:
            dt_to = datetime.fromisoformat(date_to)
        except ValueError:
            dt_to = None
    else:
        dt_to = None

    try:
        query = Document.query.filter_by(user_id=user_id, deleted_at=None)

        # ---- keyword search ----
        if q:
            term = f'%{q}%'
            query = query.filter(
                or_(
                    Document.original_filename.ilike(term),
                    Document.extracted_text.ilike(term),
                    Document.tags.ilike(term),
                    Document.predicted_label.ilike(term),
                    Document.text_preview.ilike(term),
                )
            )

        # ---- category filter ----
        if category:
            query = query.filter(Document.predicted_label.ilike(f'%{category}%'))

        # ---- date filters ----
        if dt_from:
            query = query.filter(Document.uploaded_at >= dt_from)
        if dt_to:
            query = query.filter(Document.uploaded_at <= dt_to)

        # If only time constraint (no keyword left), return all docs in window
        # This handles "give me files uploaded 2hr ago" → q becomes empty
        if not q and not category and dt_from is None and dt_to is None and not raw_q:
            return {'success': True, 'query': '', 'results': [], 'pagination': {
                'page': 1, 'per_page': per_page, 'total': 0, 'pages': 0,
                'has_next': False, 'has_prev': False}}, 200

        query = query.order_by(Document.uploaded_at.desc())
        paginated = query.paginate(page=page, per_page=per_page, error_out=False)

        return {
            'success': True,
            'query': raw_q,
            'interpreted_as': {
                'keywords': q or None,
                'date_from': dt_from.isoformat() if dt_from else None,
                'date_to': dt_to.isoformat() if dt_to else None,
            },
            'results': [d.to_dict() for d in paginated.items],
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': paginated.total,
                'pages': paginated.pages,
                'has_next': paginated.has_next,
                'has_prev': paginated.has_prev,
            },
        }, 200

    except Exception as e:
        logger.error(f"Search error: {e}")
        return {'success': False, 'error': 'Search failed'}, 500


@search_bp.route('/suggestions', methods=['GET'])
@jwt_required()
def get_suggestions():
    """
    Return autocomplete suggestions for a partial query.

    Query params:
        q (str) - partial search term (min 2 chars)
    """
    user_id = int(get_jwt_identity())
    q = sanitize_input(request.args.get('q', '').strip())

    if len(q) < 2:
        return {'success': True, 'suggestions': []}, 200

    try:
        term = f'%{q}%'
        rows = (
            Document.query
            .filter_by(user_id=user_id, deleted_at=None)
            .filter(Document.original_filename.ilike(term))
            .with_entities(Document.original_filename)
            .limit(10)
            .all()
        )
        suggestions = [r[0] for r in rows]
        return {'success': True, 'suggestions': suggestions}, 200

    except Exception as e:
        logger.error(f"Suggestions error: {e}")
        return {'success': False, 'error': 'Could not fetch suggestions'}, 500
