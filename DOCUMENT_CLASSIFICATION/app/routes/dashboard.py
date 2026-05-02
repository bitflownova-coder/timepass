"""
Dashboard Routes - Statistics and activity feed for the user dashboard
"""
import logging
from datetime import datetime, timedelta
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from app.models import db
from app.models.document import Document
from app.models.audit_log import AuditLog

logger = logging.getLogger(__name__)

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')


@dashboard_bp.route('/stats', methods=['GET'])
@jwt_required()
def get_stats():
    """
    Return summary statistics for the current user.

    Response:
        {total_documents, total_size_bytes, categories: [{name, count}],
         documents_this_week, documents_this_month, storage_used_mb}
    """
    user_id = int(get_jwt_identity())

    try:
        base = Document.query.filter_by(user_id=user_id, deleted_at=None)

        total_docs  = base.count()
        total_bytes = db.session.query(
            func.sum(Document.file_size)
        ).filter_by(user_id=user_id, deleted_at=None).scalar() or 0

        # Per-category counts
        category_rows = (
            db.session.query(Document.predicted_label, func.count(Document.id))
            .filter_by(user_id=user_id, deleted_at=None)
            .filter(Document.predicted_label.isnot(None))
            .group_by(Document.predicted_label)
            .order_by(func.count(Document.id).desc())
            .all()
        )
        categories = [{'name': row[0], 'count': row[1]} for row in category_rows]

        # Time-window counts
        now = datetime.utcnow()
        week_ago  = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        docs_this_week  = base.filter(Document.uploaded_at >= week_ago).count()
        docs_this_month = base.filter(Document.uploaded_at >= month_ago).count()

        # Confidence distribution
        high_conf   = base.filter(Document.confidence_score >= 0.80).count()
        medium_conf = base.filter(
            Document.confidence_score >= 0.60,
            Document.confidence_score < 0.80
        ).count()
        low_conf = base.filter(Document.confidence_score < 0.60).count()

        return {
            'success': True,
            'total_documents': total_docs,
            'total_size_bytes': total_bytes,
            'storage_used_mb': round(total_bytes / (1024 * 1024), 2),
            'categories': categories,
            'documents_this_week': docs_this_week,
            'documents_this_month': docs_this_month,
            'confidence': {
                'high': high_conf,
                'medium': medium_conf,
                'low': low_conf,
            },
        }, 200

    except Exception as e:
        logger.error(f"Stats error: {e}")
        return {'success': False, 'error': 'Could not fetch stats'}, 500


@dashboard_bp.route('/recent', methods=['GET'])
@jwt_required()
def get_recent():
    """
    Return the most recently uploaded documents.

    Query params:
        limit (int) - default 10, max 50
    """
    user_id = int(get_jwt_identity())
    limit = min(50, max(1, request.args.get('limit', 10, type=int)))

    try:
        docs = (
            Document.query
            .filter_by(user_id=user_id, deleted_at=None)
            .order_by(Document.uploaded_at.desc())
            .limit(limit)
            .all()
        )
        return {
            'success': True,
            'documents': [d.to_dict() for d in docs],
        }, 200

    except Exception as e:
        logger.error(f"Recent docs error: {e}")
        return {'success': False, 'error': 'Could not fetch recent documents'}, 500


@dashboard_bp.route('/activity', methods=['GET'])
@jwt_required()
def get_activity():
    """
    Return recent audit-log activity for the current user.

    Query params:
        limit (int) - default 20, max 100
    """
    user_id = int(get_jwt_identity())
    limit = min(100, max(1, request.args.get('limit', 20, type=int)))

    try:
        logs = (
            AuditLog.query
            .filter_by(user_id=user_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .all()
        )
        return {
            'success': True,
            'activity': [l.to_dict() for l in logs],
        }, 200

    except Exception as e:
        logger.error(f"Activity error: {e}")
        return {'success': False, 'error': 'Could not fetch activity'}, 500


@dashboard_bp.route('/chart/uploads', methods=['GET'])
@jwt_required()
def uploads_over_time():
    """
    Returns daily upload counts for the last N days (default 30).

    Query params:
        days (int) - default 30, max 365
    """
    user_id = int(get_jwt_identity())
    days = min(365, max(7, request.args.get('days', 30, type=int)))

    try:
        since = datetime.utcnow() - timedelta(days=days)
        rows = (
            db.session.query(
                func.date(Document.uploaded_at).label('day'),
                func.count(Document.id).label('count'),
            )
            .filter(
                Document.user_id == user_id,
                Document.deleted_at.is_(None),
                Document.uploaded_at >= since,
            )
            .group_by(func.date(Document.uploaded_at))
            .order_by(func.date(Document.uploaded_at))
            .all()
        )

        chart_data = [{'date': str(row.day), 'count': row.count} for row in rows]

        return {
            'success': True,
            'days': days,
            'data': chart_data,
        }, 200

    except Exception as e:
        logger.error(f"Chart data error: {e}")
        return {'success': False, 'error': 'Could not fetch chart data'}, 500
