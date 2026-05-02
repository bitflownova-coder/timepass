"""
Views API — Phase 5 (VFS overhaul)

Endpoints:
    GET /api/views                          — list all available views + hierarchy definitions
    GET /api/views/tree?view=by_type        — full nested tree for a view
    GET /api/views/browse?view=by_type&path=Invoices/ABC Corp
                                            — documents at a specific node
    GET /api/views/paths/<int:doc_id>       — all virtual paths for one document
"""
import logging

from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func

from app.models import db
from app.models.document import Document
from app.models.virtual_path import VirtualPath, HierarchyTemplate

logger = logging.getLogger(__name__)

views_bp = Blueprint('views', __name__, url_prefix='/api/views')


# ── helpers ──────────────────────────────────────────────────────────────────

def _require_view(view_name: str):
    """Return HierarchyTemplate or None if not found."""
    return HierarchyTemplate.query.filter_by(view_name=view_name, user_id=None).first()


def _doc_to_summary(doc: Document) -> dict:
    return {
        'id': doc.id,
        'original_filename': doc.original_filename,
        'doc_type': doc.doc_type,
        'client_name': doc.client_name,
        'doc_year': doc.doc_year,
        'file_size': doc.file_size,
        'mime_type': doc.mime_type,
        'uploaded_at': doc.uploaded_at.isoformat() if doc.uploaded_at else None,
        'tags': doc.get_tags_list(),
        'source': 'document',
    }


def _indexed_to_summary(rec) -> dict:
    """Mirror _doc_to_summary for IndexedFile rows so the UI can show them too."""
    return {
        'id':                rec.id,
        'original_filename': rec.filename,
        'doc_type':          rec.doc_type,
        'client_name':       rec.client_name,
        'doc_year':          rec.doc_year,
        'file_size':         rec.file_size,
        'mime_type':         None,
        'uploaded_at':       rec.indexed_at.isoformat() if rec.indexed_at else None,
        'tags':              [],
        'source':            'indexed',
        'file_path':         rec.file_path,
        'is_code':           bool(rec.is_code),
        'project_name':      rec.project_name,
        'language':          rec.language,
        'extension':         rec.extension,
    }


# ── GET /api/views ────────────────────────────────────────────────────────────

@views_bp.route('', methods=['GET'])
@jwt_required()
def list_views():
    """
    Return all available hierarchy views + their level definitions.

    Response:
        {success, views: [{view_name, display_name, level1_attr, level2_attr, level3_attr}]}
    """
    try:
        templates = HierarchyTemplate.query.filter_by(user_id=None).order_by(HierarchyTemplate.id).all()
        return {
            'success': True,
            'views': [t.to_dict() for t in templates],
        }, 200
    except Exception as e:
        logger.error(f"list_views error: {e}")
        return {'success': False, 'error': str(e)}, 500


# ── GET /api/views/tree ───────────────────────────────────────────────────────

@views_bp.route('/tree', methods=['GET'])
@jwt_required()
def get_tree():
    """
    Return a nested tree for the requested view.

    Query params:
        view  (required) — e.g. 'by_type', 'by_client', 'by_time'

    Response:
        {success, view_name, tree: [{label, path, count, children: [{...}]}]}

    Tree shape (3 levels):
        level1
          level2
            level3  (leaf — has doc_count)
    """
    user_id = int(get_jwt_identity())
    view_name = request.args.get('view', '').strip()

    if not view_name:
        return {'success': False, 'error': "'view' query parameter is required"}, 400

    template = _require_view(view_name)
    if not template:
        return {'success': False, 'error': f"Unknown view: {view_name!r}"}, 404

    try:
        rows = (
            db.session.query(
                VirtualPath.level1,
                VirtualPath.level2,
                VirtualPath.level3,
                func.count(VirtualPath.id).label('cnt'),
            )
            .filter_by(user_id=user_id, view_name=view_name)
            .group_by(VirtualPath.level1, VirtualPath.level2, VirtualPath.level3)
            .order_by(VirtualPath.level1, VirtualPath.level2, VirtualPath.level3)
            .all()
        )

        # Build nested dict: {l1: {l2: {l3: count}}}
        tree_map: dict = {}
        for l1, l2, l3, cnt in rows:
            l1 = l1 or 'Unknown'
            l2 = l2 or 'Unknown'
            l3 = str(l3) if l3 is not None else 'Unknown'
            tree_map.setdefault(l1, {}).setdefault(l2, {})[l3] = cnt

        # Convert to list structure
        tree = []
        for l1_label, l2_map in sorted(tree_map.items()):
            l1_count = sum(
                cnt for l2_inner in l2_map.values() for cnt in l2_inner.values()
            )
            l1_node = {
                'label': l1_label,
                'path': l1_label,
                'count': l1_count,
                'children': [],
            }
            for l2_label, l3_map in sorted(l2_map.items()):
                l2_count = sum(l3_map.values())
                l2_path = f"{l1_label}/{l2_label}"
                l2_node = {
                    'label': l2_label,
                    'path': l2_path,
                    'count': l2_count,
                    'children': [],
                }
                for l3_label, cnt in sorted(l3_map.items()):
                    l3_path = f"{l2_path}/{l3_label}"
                    l2_node['children'].append({
                        'label': l3_label,
                        'path': l3_path,
                        'count': cnt,
                        'children': [],
                    })
                l1_node['children'].append(l2_node)
            tree.append(l1_node)

        return {
            'success': True,
            'view_name': view_name,
            'display_name': template.display_name,
            'level1_attr': template.level1_attr,
            'level2_attr': template.level2_attr,
            'level3_attr': template.level3_attr,
            'tree': tree,
        }, 200

    except Exception as e:
        logger.error(f"get_tree error ({view_name}): {e}")
        return {'success': False, 'error': str(e)}, 500


# ── GET /api/views/browse ─────────────────────────────────────────────────────

@views_bp.route('/browse', methods=['GET'])
@jwt_required()
def browse():
    """
    Return documents at a specific node in a view.

    Query params:
        view   (required) — e.g. 'by_type'
        path   (required) — slash-joined path, e.g. 'Invoices/ABC Corp/2024'
                            Can be 1, 2, or 3 levels deep.
        page   (optional, default 1)
        per_page (optional, default 20, max 100)

    Response:
        {success, view_name, path, total, page, per_page, documents: [...]}
    """
    user_id = int(get_jwt_identity())
    view_name = request.args.get('view', '').strip()
    path = request.args.get('path', '').strip()
    page = max(1, int(request.args.get('page', 1)))
    per_page = min(100, max(1, int(request.args.get('per_page', 20))))

    if not view_name:
        return {'success': False, 'error': "'view' parameter is required"}, 400
    if not path:
        return {'success': False, 'error': "'path' parameter is required"}, 400

    template = _require_view(view_name)
    if not template:
        return {'success': False, 'error': f"Unknown view: {view_name!r}"}, 404

    try:
        segments = [s.strip() for s in path.split('/') if s.strip()]
        depth = len(segments)

        # Build filter based on depth (1, 2, or 3 levels)
        q = VirtualPath.query.filter_by(user_id=user_id, view_name=view_name)
        if depth >= 1:
            q = q.filter(VirtualPath.level1 == segments[0])
        if depth >= 2:
            q = q.filter(VirtualPath.level2 == segments[1])
        if depth >= 3:
            q = q.filter(VirtualPath.level3 == segments[2])

        total = q.count()
        vp_rows = q.offset((page - 1) * per_page).limit(per_page).all()

        doc_ids = [vp.document_id for vp in vp_rows if vp.document_id]
        idx_ids = [vp.indexed_file_id for vp in vp_rows if vp.indexed_file_id]

        doc_map = {}
        if doc_ids:
            docs = Document.query.filter(
                Document.id.in_(doc_ids),
                Document.deleted_at.is_(None),
            ).all()
            doc_map = {d.id: d for d in docs}

        idx_map = {}
        if idx_ids:
            from app.models.indexed_file import IndexedFile
            idx_rows = IndexedFile.query.filter(
                IndexedFile.id.in_(idx_ids),
                IndexedFile.is_deleted == False,
            ).all()
            idx_map = {r.id: r for r in idx_rows}

        result = []
        for vp in vp_rows:
            if vp.document_id and vp.document_id in doc_map:
                result.append(_doc_to_summary(doc_map[vp.document_id]))
            elif vp.indexed_file_id and vp.indexed_file_id in idx_map:
                result.append(_indexed_to_summary(idx_map[vp.indexed_file_id]))

        return {
            'success': True,
            'view_name': view_name,
            'path': path,
            'total': total,
            'page': page,
            'per_page': per_page,
            'documents': result,
        }, 200

    except Exception as e:
        logger.error(f"browse error ({view_name}, {path}): {e}")
        return {'success': False, 'error': str(e)}, 500


# ── GET /api/views/paths/<doc_id> ─────────────────────────────────────────────

@views_bp.route('/paths/<int:doc_id>', methods=['GET'])
@jwt_required()
def doc_paths(doc_id: int):
    """
    Return all virtual paths for a single document.

    Response:
        {success, document_id, paths: [{view_name, display_name, path, level1, level2, level3}]}
    """
    user_id = int(get_jwt_identity())

    doc = Document.query.filter_by(id=doc_id, user_id=user_id, deleted_at=None).first()
    if not doc:
        return {'success': False, 'error': 'Document not found'}, 404

    try:
        vp_rows = VirtualPath.query.filter_by(document_id=doc_id, user_id=user_id).all()

        # Enrich with display_name from templates
        template_map = {
            t.view_name: t.display_name
            for t in HierarchyTemplate.query.filter_by(user_id=None).all()
        }

        paths = []
        for vp in vp_rows:
            paths.append({
                'view_name': vp.view_name,
                'display_name': template_map.get(vp.view_name, vp.view_name),
                'path': vp.path,
                'level1': vp.level1,
                'level2': vp.level2,
                'level3': vp.level3,
            })

        return {
            'success': True,
            'document_id': doc_id,
            'original_filename': doc.original_filename,
            'paths': paths,
        }, 200

    except Exception as e:
        logger.error(f"doc_paths error (doc={doc_id}): {e}")
        return {'success': False, 'error': str(e)}, 500


# ── POST /api/views/templates ─────────────────────────────────────────────────

@views_bp.route('/templates', methods=['POST'])
@jwt_required()
def create_template():
    """
    Create a new global hierarchy template (view).

    Body (JSON):
        {
          "view_name":    "by_vendor",        # snake_case, unique identifier
          "display_name": "By Vendor",        # human-readable label
          "level1_attr":  "doc_type",         # Document attribute name
          "level2_attr":  "client_name",      # optional
          "level3_attr":  "doc_year"          # optional
        }

    Response (201):
        {success, template: {...}}
    """
    from flask import request as req
    data = req.get_json(silent=True) or {}

    view_name    = (data.get('view_name') or '').strip()
    display_name = (data.get('display_name') or '').strip()
    l1 = (data.get('level1_attr') or '').strip()
    l2 = (data.get('level2_attr') or '').strip() or None
    l3 = (data.get('level3_attr') or '').strip() or None

    if not view_name or not display_name or not l1:
        return {'success': False,
                'error': 'view_name, display_name, and level1_attr are required'}, 400

    _VALID_ATTRS = {'doc_type', 'client_name', 'doc_year', 'predicted_label', 'user_folder'}
    for attr_val, label in [(l1, 'level1_attr'), (l2, 'level2_attr'), (l3, 'level3_attr')]:
        if attr_val and attr_val not in _VALID_ATTRS:
            return {'success': False,
                    'error': f"Invalid attribute for {label}: {attr_val!r}. "
                             f"Allowed: {sorted(_VALID_ATTRS)}"}, 400

    if HierarchyTemplate.query.filter_by(view_name=view_name, user_id=None).first():
        return {'success': False, 'error': f"View {view_name!r} already exists"}, 409

    try:
        template = HierarchyTemplate(
            view_name=view_name,
            display_name=display_name,
            level1_attr=l1,
            level2_attr=l2,
            level3_attr=l3,
            user_id=None,
        )
        db.session.add(template)
        db.session.commit()

        logger.info(f"Created view template: {view_name}")
        return {'success': True, 'template': template.to_dict()}, 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"create_template error: {e}")
        return {'success': False, 'error': str(e)}, 500


# ── DELETE /api/views/templates/<view_name> ───────────────────────────────────

@views_bp.route('/templates/<string:view_name>', methods=['DELETE'])
@jwt_required()
def delete_template(view_name: str):
    """
    Delete a hierarchy template (view) and all VirtualPath rows for it.

    The three built-in views (by_type, by_client, by_time) cannot be deleted.

    Response (200):
        {success, deleted_view: view_name, paths_removed: N}
    """
    _PROTECTED = {'by_type', 'by_client', 'by_time'}
    if view_name in _PROTECTED:
        return {'success': False,
                'error': f"Built-in view {view_name!r} cannot be deleted"}, 403

    template = HierarchyTemplate.query.filter_by(view_name=view_name, user_id=None).first()
    if not template:
        return {'success': False, 'error': f"View {view_name!r} not found"}, 404

    try:
        paths_removed = VirtualPath.query.filter_by(view_name=view_name).delete()
        db.session.delete(template)
        db.session.commit()

        logger.info(f"Deleted view template: {view_name} ({paths_removed} paths removed)")
        return {
            'success': True,
            'deleted_view': view_name,
            'paths_removed': paths_removed,
        }, 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"delete_template error ({view_name}): {e}")
        return {'success': False, 'error': str(e)}, 500

