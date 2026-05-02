"""
Folder Routes - Smart folder routing, confirmation workflow, feedback/retrain
"""
import io
import logging
import zipfile
from flask import Blueprint, request, current_app, send_file
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.models import db
from app.models.document import Document
from app.models.audit_log import AuditLog
from app.utils.text_extractor import TextPreprocessor
from app.utils.classifier import DocumentClassifier
# FolderRouter is for the UI suggestion tooltip only — it has no effect on VirtualPaths or storage routing.
from app.utils.folder_router import FolderRouter, DECISION_AUTO, DECISION_SUGGEST, DECISION_UNSURE
from app.utils.retraining import RetrainingService
from app.utils.validators import sanitize_input
from app.utils.file_storage import FileStorage
from app.utils.rbac import require_role
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

folders_bp = Blueprint('folders', __name__, url_prefix='/api/folders')

# Module-level singletons (lazy init)
_classifier: DocumentClassifier | None = None
_router: FolderRouter | None = None
_retrainer: RetrainingService | None = None


def _get_classifier() -> DocumentClassifier:
    global _classifier
    if _classifier is None:
        _classifier = DocumentClassifier()
        _classifier.load()
    return _classifier


def _get_router() -> FolderRouter:
    global _router
    if _router is None:
        _router = FolderRouter(
            high_threshold=current_app.config.get('CONFIDENCE_THRESHOLD', 0.80),
            medium_threshold=current_app.config.get('MEDIUM_CONFIDENCE_THRESHOLD', 0.60),
            cosine_threshold=current_app.config.get('COSINE_SIMILARITY_THRESHOLD', 0.70),
        )
    return _router


def _get_retrainer() -> RetrainingService:
    global _retrainer
    if _retrainer is None:
        _retrainer = RetrainingService(
            model_path=current_app.config.get('CLASSIFIER_MODEL_PATH',
                                               'models/logistic_model.pkl'),
            vectorizer_path=current_app.config.get('TFIDF_MODEL_PATH',
                                                    'models/tfidf_vectorizer.pkl'),
        )
    return _retrainer


def _get_storage() -> FileStorage:
    return FileStorage(
        upload_root=current_app.config['UPLOAD_FOLDER'],
        encryption_key=current_app.config['ENCRYPTION_KEY'],
    )


def _existing_folders(user_id: int) -> list[str]:
    """Return distinct user_folder values for a user (excluding deleted docs)."""
    rows = (
        db.session.query(Document.user_folder)
        .filter_by(user_id=user_id, deleted_at=None)
        .filter(Document.user_folder.isnot(None))
        .distinct()
        .all()
    )
    return [r[0] for r in rows]


def _log_audit(user_id, action, resource_type, resource_id, status, detail, ip):
    try:
        entry = AuditLog(
            user_id=user_id, action=action,
            resource_type=resource_type, resource_id=resource_id,
            resource_name=detail, status=status, ip_address=ip,
        )
        db.session.add(entry)
        db.session.commit()
    except Exception as e:
        logger.warning(f"Audit log failed: {e}")


# ============================================================
# POST /api/folders/suggest
# ============================================================

@folders_bp.route('/suggest', methods=['POST'])
@jwt_required()
def suggest_folder():
    """
    Given raw document text, return a routing decision with folder suggestions.

    Request JSON:
        text (str, required) - document text to classify
        document_id (int, optional) - if already stored, used for context

    Response:
        {success, decision, primary_folder, primary_confidence, primary_score,
         alternatives: [{folder, confidence, score, is_new}],
         needs_confirmation, message}
    """
    user_id = int(get_jwt_identity())
    data = request.get_json() or {}

    text = sanitize_input(data.get('text', '').strip())
    if not text or len(text) < 10:
        return {'success': False, 'error': 'Document text too short (min 10 chars)'}, 400

    processed = TextPreprocessor.preprocess(text)
    if not processed:
        return {'success': False, 'error': 'Could not preprocess text'}, 400

    classifier  = _get_classifier()
    router      = _get_router()
    folders     = _existing_folders(user_id)

    predicted_label  = 'Uncategorized'
    confidence_score = 0.0
    all_predictions  = []

    if classifier.is_trained:
        pred = classifier.predict(processed, return_probabilities=True)
        if pred.get('success'):
            predicted_label  = pred['predicted_label']
            confidence_score = pred['confidence_score']
            all_predictions  = pred.get('all_predictions', [])

    decision = router.route(
        document_text=processed,
        predicted_label=predicted_label,
        confidence_score=confidence_score,
        existing_folders=folders,
        all_predictions=all_predictions,
    )

    return {
        'success': True,
        'decision': decision.decision,
        'primary_folder': decision.primary_folder,
        'primary_confidence': round(decision.primary_confidence, 4),
        'primary_score': round(decision.primary_score, 4),
        'alternatives': [
            {
                'folder': a.folder,
                'confidence': round(a.confidence, 4),
                'score': round(a.score, 4),
                'is_new': a.is_new,
            }
            for a in decision.alternatives
        ],
        'needs_confirmation': decision.needs_confirmation,
        'message': decision.message,
        'existing_folders': folders,
    }, 200


# ============================================================
# POST /api/folders/confirm/<doc_id>
# ============================================================

@folders_bp.route('/confirm/<int:doc_id>', methods=['POST'])
@jwt_required()
def confirm_folder(doc_id: int):
    """
    User confirms (or overrides) the folder suggestion for an uploaded document.

    Request JSON:
        folder (str, required) - chosen folder name

    Moves the encrypted file on disk and updates the DB record.
    """
    user_id = int(get_jwt_identity())
    ip = request.remote_addr or '0.0.0.0'

    doc = Document.query.filter_by(id=doc_id, user_id=user_id,
                                   deleted_at=None).first()
    if not doc:
        return {'success': False, 'error': 'Document not found'}, 404

    data = request.get_json() or {}
    folder = sanitize_input(data.get('folder', '').strip())
    if not folder:
        return {'success': False, 'error': 'folder is required'}, 400

    try:
        storage = _get_storage()

        if folder != doc.user_folder:
            # Phase B: storage is flat — files never move on disk.
            # Only update the DB label and rebuild virtual paths.
            doc.user_folder     = folder
            doc.predicted_label = folder

            # Rebuild virtual paths to reflect the new label
            try:
                from app.utils.path_generator import PathGenerator
                from app.models.virtual_path import HierarchyTemplate
                templates = HierarchyTemplate.query.filter_by(user_id=None).all()
                PathGenerator.generate_and_save(doc, templates, db)
            except Exception as vp_err:
                logger.warning(f"VPath rebuild on confirm failed: {vp_err}")

        db.session.commit()
        _log_audit(user_id, 'folder_confirm', 'document', doc_id, 'success',
                   f'Placed in "{folder}"', ip)

        return {
            'success': True,
            'document_id': doc_id,
            'folder': folder,
            'message': f'Document moved to "{folder}"',
        }, 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"confirm_folder error: {e}")
        return {'success': False, 'error': 'Could not confirm folder'}, 500


# ============================================================
# POST /api/folders/feedback/<doc_id>
# ============================================================

@folders_bp.route('/feedback/<int:doc_id>', methods=['POST'])
@jwt_required()
def submit_feedback(doc_id: int):
    """
    Submit a correction for a document's predicted label.

    Request JSON:
        corrected_label (str, required) - what the document actually is
        feedback_text   (str, optional) - free-text comment

    The correction is stored in the Feedback table and used during retraining.
    """
    user_id = int(get_jwt_identity())
    ip = request.remote_addr or '0.0.0.0'

    doc = Document.query.filter_by(id=doc_id, user_id=user_id,
                                   deleted_at=None).first()
    if not doc:
        return {'success': False, 'error': 'Document not found'}, 404

    data = request.get_json() or {}
    corrected_label = sanitize_input(data.get('corrected_label', '').strip())
    feedback_text   = sanitize_input(data.get('feedback_text', '').strip()) or None

    if not corrected_label:
        return {'success': False, 'error': 'corrected_label is required'}, 400

    retrainer = _get_retrainer()
    result = retrainer.record_correction(
        document_id=doc_id,
        user_id=user_id,
        predicted_label=doc.predicted_label or 'Unknown',
        corrected_label=corrected_label,
        feedback_text=feedback_text,
    )

    if not result.get('success'):
        return {'success': False, 'error': result.get('error')}, 500

    _log_audit(user_id, 'feedback', 'document', doc_id, 'success',
               f'Corrected to "{corrected_label}"', ip)

    return {
        'success': True,
        'feedback_id': result['feedback_id'],
        'corrected_label': corrected_label,
        'message': 'Feedback recorded. Thank you!',
    }, 201


# ============================================================
# POST /api/folders/retrain  (admin-only trigger)
# ============================================================

@folders_bp.route('/retrain', methods=['POST'])
@jwt_required()
@require_role('admin')
def trigger_retrain():
    """
    Trigger model retraining using all stored documents + corrections.
    Requires admin role.
    """
    retrainer = _get_retrainer()
    result = retrainer.retrain()

    # Reload the in-memory classifier so next request uses new model
    global _classifier
    _classifier = None

    if not result.get('success'):
        return {'success': False, 'error': result.get('error')}, 500

    return {
        'success': True,
        'accuracy': round(result['accuracy'], 4),
        'num_samples': result['num_samples'],
        'classes': result['classes'],
        'message': 'Model retrained successfully',
    }, 200


# ============================================================
# GET /api/folders/stats
# ============================================================

@folders_bp.route('/stats', methods=['GET'])
@jwt_required()
def feedback_stats():
    """Return feedback/correction statistics for the current user."""
    user_id = int(get_jwt_identity())

    from app.models.audit_log import Feedback
    total_docs = Document.query.filter_by(user_id=user_id, deleted_at=None).count()
    corrections = Feedback.query.filter_by(user_id=user_id).count()
    folders = _existing_folders(user_id)

    return {
        'success': True,
        'total_documents': total_docs,
        'total_corrections': corrections,
        'folders': folders,
        'folder_count': len(folders),
    }, 200


# ============================================================
# GET /api/folders/<name>/download  →  ZIP of all files in folder
# ============================================================

@folders_bp.route('/<path:folder_name>/download', methods=['GET'])
@jwt_required()
def download_folder(folder_name: str):
    """Return a ZIP archive of all files in the named folder for the current user."""
    user_id = int(get_jwt_identity())
    folder_name = sanitize_input(folder_name)

    docs = Document.query.filter_by(user_id=user_id, deleted_at=None).filter(
        (Document.user_folder == folder_name) | (Document.predicted_label == folder_name)
    ).all()

    if not docs:
        return {'success': False, 'error': 'Folder not found or empty'}, 404

    storage = FileStorage(
        upload_root=current_app.config['UPLOAD_FOLDER'],
        encryption_key=current_app.config['ENCRYPTION_KEY'],
    )

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as zf:
        seen_names: dict[str, int] = {}
        for doc in docs:
            enc_path = storage.user_folder(user_id, doc.user_folder or doc.predicted_label) / doc.filename
            data = storage.encryption.decrypt_to_bytes(str(enc_path))
            if data is None:
                continue  # skip unreadable files

            # Deduplicate filenames inside the ZIP
            name = doc.original_filename
            if name in seen_names:
                seen_names[name] += 1
                stem, _, ext = name.rpartition('.')
                name = f"{stem}_{seen_names[name]}.{ext}" if ext else f"{name}_{seen_names[name]}"
            else:
                seen_names[name] = 0

            zf.writestr(name, data)

    buf.seek(0)
    safe_name = folder_name.replace(' ', '_')
    return send_file(
        buf,
        mimetype='application/zip',
        as_attachment=True,
        download_name=f'{safe_name}.zip',
    )
