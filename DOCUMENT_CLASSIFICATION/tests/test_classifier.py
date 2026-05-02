"""
Tests for ML Classifier utilities
"""
import pytest
from app.utils.text_extractor import TextPreprocessor
from app.utils.classifier import DocumentClassifier
from app.utils.folder_router import FolderRouter, DECISION_AUTO, DECISION_SUGGEST, DECISION_UNSURE


# ─────────────────────────────────────────────────
# TextPreprocessor
# ─────────────────────────────────────────────────

class TestTextPreprocessor:

    def test_clean_removes_urls(self):
        out = TextPreprocessor.clean_text('Visit https://example.com for details')
        assert 'http' not in out
        assert 'example' not in out

    def test_clean_removes_emails(self):
        out = TextPreprocessor.clean_text('Email us at support@company.com')
        assert '@' not in out

    def test_clean_lowercases(self):
        out = TextPreprocessor.clean_text('HELLO WORLD')
        assert out == out.lower()

    def test_preprocess_returns_string(self):
        result = TextPreprocessor.preprocess('Invoice payment due amount $500')
        assert isinstance(result, str)
        assert len(result) > 0

    def test_preprocess_removes_stopwords(self):
        result = TextPreprocessor.preprocess('this is a test document')
        # Common stopwords like 'this', 'is', 'a' should be removed
        tokens = result.split()
        assert 'this' not in tokens
        assert 'is'   not in tokens

    def test_preprocess_empty_string(self):
        result = TextPreprocessor.preprocess('')
        assert result == ''


# ─────────────────────────────────────────────────
# DocumentClassifier
# ─────────────────────────────────────────────────

class TestDocumentClassifier:

    @pytest.fixture
    def trained_classifier(self):
        clf = DocumentClassifier(
            model_path='/tmp/test_model.pkl',
            vectorizer_path='/tmp/test_vectorizer.pkl',
        )
        texts = [
            'invoice payment amount due billing',
            'invoice receipt payment total cost',
            'resume experience skills education python',
            'curriculum vitae work experience software engineer',
            'agreement contract terms conditions legal',
            'legal contract service agreement payment terms',
        ]
        labels = ['Bills', 'Bills', 'Resume', 'Resume', 'Legal', 'Legal']
        clf.train(texts, labels)
        return clf

    def test_train_returns_success(self, trained_classifier):
        assert trained_classifier.is_trained is True

    def test_predict_returns_label(self, trained_classifier):
        result = trained_classifier.predict('invoice payment amount due')
        assert result['success'] is True
        assert result['predicted_label'] in ['Bills', 'Resume', 'Legal']
        assert 0.0 <= result['confidence_score'] <= 1.0

    def test_predict_bills(self, trained_classifier):
        result = trained_classifier.predict('invoice total amount payment due billing')
        assert result['success'] is True
        assert result['predicted_label'] == 'Bills'

    def test_predict_resume(self, trained_classifier):
        result = trained_classifier.predict('resume experience education skills python java')
        assert result['success'] is True
        assert result['predicted_label'] == 'Resume'

    def test_predict_with_probabilities(self, trained_classifier):
        result = trained_classifier.predict('contract legal agreement', return_probabilities=True)
        assert result['success'] is True
        assert 'all_predictions' in result
        assert len(result['all_predictions']) == 3

    def test_predict_untrained_raises_error(self):
        clf = DocumentClassifier()
        result = clf.predict('some text')
        assert result['success'] is False
        assert 'error' in result

    def test_save_and_load(self, trained_classifier, tmp_path):
        model_p  = str(tmp_path / 'model.pkl')
        vec_p    = str(tmp_path / 'vec.pkl')
        trained_classifier.model_path     = model_p
        trained_classifier.vectorizer_path = vec_p
        trained_classifier.save()

        new_clf = DocumentClassifier(model_path=model_p, vectorizer_path=vec_p)
        load_res = new_clf.load()
        assert load_res['success'] is True
        assert new_clf.is_trained is True

        pred = new_clf.predict('invoice payment billing')
        assert pred['success'] is True


# ─────────────────────────────────────────────────
# FolderRouter
# ─────────────────────────────────────────────────

class TestFolderRouter:

    @pytest.fixture
    def router(self):
        return FolderRouter(high_threshold=0.80, medium_threshold=0.60)

    def test_auto_decision_high_confidence(self, router):
        decision = router.route(
            document_text='invoice payment amount due',
            predicted_label='Bills',
            confidence_score=0.92,
            existing_folders=['Bills', 'Resume', 'Legal'],
        )
        assert decision.decision == DECISION_AUTO
        assert decision.needs_confirmation is False

    def test_suggest_decision_medium_confidence(self, router):
        decision = router.route(
            document_text='invoice payment',
            predicted_label='Bills',
            confidence_score=0.70,
            existing_folders=['Bills', 'Resume'],
        )
        assert decision.decision == DECISION_SUGGEST
        assert decision.needs_confirmation is True

    def test_unsure_decision_low_confidence(self, router):
        decision = router.route(
            document_text='document text here',
            predicted_label='Unknown',
            confidence_score=0.40,
            existing_folders=['Bills', 'Resume'],
        )
        assert decision.decision == DECISION_UNSURE
        assert decision.needs_confirmation is True

    def test_no_existing_folders_creates_new(self, router):
        decision = router.route(
            document_text='invoice payment',
            predicted_label='Bills',
            confidence_score=0.90,
            existing_folders=[],
        )
        assert decision.primary_folder == 'Bills'

    def test_alternatives_populated(self, router):
        decision = router.route(
            document_text='invoice payment',
            predicted_label='Bills',
            confidence_score=0.70,
            existing_folders=['Bills', 'Resume', 'Legal'],
            all_predictions=[
                {'label': 'Bills',  'confidence': 0.70},
                {'label': 'Legal',  'confidence': 0.20},
                {'label': 'Resume', 'confidence': 0.10},
            ]
        )
        assert isinstance(decision.alternatives, list)
