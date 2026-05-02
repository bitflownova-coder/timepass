"""
Retraining Service - collects user corrections and periodically retrains the model.
"""
import logging
from datetime import datetime
from app.models import db
from app.models.audit_log import Feedback
from app.models.document import Document
from app.utils.text_extractor import TextPreprocessor
from app.utils.classifier import DocumentClassifier

logger = logging.getLogger(__name__)


class RetrainingService:
    """
    Manages the feedback → retrain pipeline:
    1. Record user corrections as Feedback rows
    2. Aggregate training data (original documents + corrections)
    3. Retrain and save the classifier
    """

    def __init__(self,
                 model_path: str = 'models/logistic_model.pkl',
                 vectorizer_path: str = 'models/tfidf_vectorizer.pkl',
                 min_samples_per_class: int = 2):
        self.model_path = model_path
        self.vectorizer_path = vectorizer_path
        self.min_samples_per_class = min_samples_per_class

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def record_correction(self, document_id: int, user_id: int,
                          predicted_label: str, corrected_label: str,
                          feedback_text: str | None = None) -> dict:
        """
        Persist a user correction for a document.

        Returns:
            dict: {success, feedback_id}
        """
        try:
            # Avoid duplicate feedback for the same doc/user
            existing = Feedback.query.filter_by(
                document_id=document_id, user_id=user_id
            ).first()

            if existing:
                existing.corrected_label = corrected_label
                existing.predicted_label = predicted_label
                existing.feedback_text   = feedback_text
                existing.created_at      = datetime.utcnow()
                db.session.commit()
                return {'success': True, 'feedback_id': existing.id,
                        'updated': True}

            fb = Feedback(
                document_id=document_id,
                user_id=user_id,
                predicted_label=predicted_label,
                corrected_label=corrected_label,
                feedback_text=feedback_text,
                is_useful=True,
            )
            db.session.add(fb)
            db.session.commit()

            # Update the document's user_folder to the corrected label
            doc = Document.query.get(document_id)
            if doc:
                doc.user_folder = corrected_label
                db.session.commit()

            return {'success': True, 'feedback_id': fb.id, 'updated': False}

        except Exception as e:
            db.session.rollback()
            logger.error(f"record_correction error: {e}")
            return {'success': False, 'error': str(e)}

    def retrain(self) -> dict:
        """
        Retrain the classifier using all documents + user corrections.

        Corrections override the original predicted label so the model
        learns from mistakes.

        Returns:
            dict: {success, accuracy, num_samples, classes}
        """
        try:
            texts: list[str] = []
            labels: list[str] = []

            # Load all non-deleted documents that have extracted text
            documents = (
                Document.query
                .filter(Document.deleted_at.is_(None),
                        Document.extracted_text.isnot(None))
                .all()
            )

            if not documents:
                return {'success': False, 'error': 'No documents available for training'}

            # Build correction lookup: document_id → corrected_label
            corrections: dict[int, str] = {}
            feedbacks = Feedback.query.filter(
                Feedback.corrected_label.isnot(None)
            ).all()
            for fb in feedbacks:
                corrections[fb.document_id] = fb.corrected_label

            for doc in documents:
                raw_text = doc.extracted_text or ''
                processed = TextPreprocessor.preprocess(raw_text)
                if not processed:
                    continue
                # Use correction if available, else AI label, else user_folder
                label = (corrections.get(doc.id)
                         or doc.predicted_label
                         or doc.user_folder)
                if not label:
                    continue
                texts.append(processed)
                labels.append(label)

            if not texts:
                return {'success': False,
                        'error': 'No usable training samples after preprocessing'}

            # Enforce min samples per class
            from collections import Counter
            counts = Counter(labels)
            valid_classes = {c for c, n in counts.items()
                             if n >= self.min_samples_per_class}
            if not valid_classes:
                return {'success': False,
                        'error': (f'No class has >= {self.min_samples_per_class} samples. '
                                  f'Counts: {dict(counts)}')}

            filtered = [(t, l) for t, l in zip(texts, labels) if l in valid_classes]
            texts, labels = zip(*filtered)  # type: ignore

            classifier = DocumentClassifier(self.model_path, self.vectorizer_path)
            result = classifier.train(list(texts), list(labels))

            if not result.get('success'):
                return result

            save_result = classifier.save()
            if not save_result.get('success'):
                return save_result

            logger.info(f"Retrain complete. Accuracy={result['accuracy']:.2%}, "
                        f"samples={len(texts)}, classes={result['classes']}")

            return {
                'success': True,
                'accuracy': result['accuracy'],
                'num_samples': len(texts),
                'classes': result['classes'],
                'num_features': result['num_features'],
            }

        except Exception as e:
            logger.error(f"retrain error: {e}")
            return {'success': False, 'error': str(e)}

    def stats(self) -> dict:
        """Return feedback statistics."""
        try:
            total  = Feedback.query.count()
            useful = Feedback.query.filter_by(is_useful=True).count()
            corrections = Feedback.query.filter(
                Feedback.corrected_label.isnot(None)
            ).count()
            return {
                'success': True,
                'total_feedback': total,
                'useful': useful,
                'corrections': corrections,
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
