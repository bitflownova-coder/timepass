"""
Classification Routes - API endpoints for document classification
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.utils.text_extractor import TextPreprocessor
from app.utils.classifier import DocumentClassifier
import logging

logger = logging.getLogger(__name__)

classify_bp = Blueprint('classify', __name__, url_prefix='/api/classify')

# Initialize classifier (loaded on first use)
_classifier = None


def get_classifier():
    """Get or initialize classifier"""
    global _classifier
    if _classifier is None:
        _classifier = DocumentClassifier()
        _classifier.load()
    return _classifier


@classify_bp.route('/predict', methods=['POST'])
@jwt_required()
def predict():
    """
    Classify document text
    
    Request JSON:
    {
        "text": "document text here",
        "return_all_predictions": true (optional)
    }
    """
    try:
        current_user_id = get_jwt_identity()
        data = request.get_json()
        
        if not data:
            return {
                'success': False,
                'error': 'Request body is required'
            }, 400
        
        text = data.get('text', '').strip()
        return_all = data.get('return_all_predictions', False)
        
        if not text:
            return {
                'success': False,
                'error': 'Document text is required'
            }, 400
        
        if len(text) < 10:
            return {
                'success': False,
                'error': 'Document text is too short (minimum 10 characters)'
            }, 400
        
        # Get classifier
        classifier = get_classifier()
        
        if not classifier.is_trained:
            return {
                'success': False,
                'error': 'Classification model not trained yet'
            }, 503
        
        # Preprocess text
        processed_text = TextPreprocessor.preprocess(text)
        
        if not processed_text:
            return {
                'success': False,
                'error': 'Could not process document text'
            }, 400
        
        # Predict
        prediction = classifier.predict(processed_text, return_probabilities=return_all)
        
        if not prediction.get('success'):
            return {
                'success': False,
                'error': prediction.get('error', 'Classification failed')
            }, 500
        
        # Format response
        response = {
            'success': True,
            'predicted_label': prediction['predicted_label'],
            'confidence_score': round(prediction['confidence_score'], 4),
            'text_preview': text[:200] + ('...' if len(text) > 200 else '')
        }
        
        if return_all and prediction.get('all_predictions'):
            response['all_predictions'] = [
                {
                    'label': p['label'],
                    'confidence': round(p['confidence'], 4)
                }
                for p in prediction['all_predictions']
            ]
        
        return response, 200
    
    except Exception as e:
        logger.error(f"Classification error: {str(e)}")
        return {
            'success': False,
            'error': 'An error occurred during classification'
        }, 500


@classify_bp.route('/info', methods=['GET'])
@jwt_required()
def get_classifier_info():
    """Get classifier information"""
    try:
        classifier = get_classifier()
        
        if not classifier.is_trained:
            return {
                'success': False,
                'error': 'Model not trained'
            }, 503
        
        return {
            'success': True,
            'is_trained': classifier.is_trained,
            'classes': list(classifier.classes) if classifier.classes is not None else [],
            'num_classes': len(classifier.classes) if classifier.classes is not None else 0
        }, 200
    
    except Exception as e:
        logger.error(f"Error getting classifier info: {str(e)}")
        return {
            'success': False,
            'error': 'An error occurred'
        }, 500
