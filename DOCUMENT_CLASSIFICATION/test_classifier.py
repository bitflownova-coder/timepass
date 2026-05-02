"""
Classifier Test - Test the trained model
"""
import logging
from app.utils.text_extractor import TextPreprocessor
from app.utils.classifier import DocumentClassifier

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_classifier():
    """Test the trained classifier"""
    
    logger.info("Loading trained model...")
    classifier = DocumentClassifier()
    
    result = classifier.load()
    if not result.get('success'):
        logger.error(f"Failed to load model: {result.get('error')}")
        return
    
    logger.info("Model loaded successfully!")
    
    # Test documents
    test_documents = [
        {
            'text': 'I have 5 years of experience in software engineering. Skilled in Python and Java. Education: BS Computer Science.',
            'expected': 'Resume'
        },
        {
            'text': 'Invoice #2024-001. Amount Due: $500. Payment Terms: Net 30. Please remit payment to the account specified.',
            'expected': 'Bills'
        },
        {
            'text': 'SERVICE AGREEMENT. This agreement between Provider and Client. Terms: 12 months. Payment: $5000 per month. Termination with 30 days notice.',
            'expected': 'Legal'
        }
    ]
    
    logger.info("\n=== Testing Classifier ===\n")
    
    for i, doc in enumerate(test_documents, 1):
        text = doc['text']
        expected = doc['expected']
        
        # Preprocess
        processed_text = TextPreprocessor.preprocess(text)
        
        # Predict
        prediction = classifier.predict(processed_text, return_probabilities=True)
        
        if prediction.get('success'):
            predicted_label = prediction['predicted_label']
            confidence = prediction['confidence_score']
            
            logger.info(f"Test {i}:")
            logger.info(f"  Expected: {expected}")
            logger.info(f"  Predicted: {predicted_label}")
            logger.info(f"  Confidence: {confidence:.2%}")
            logger.info(f"  Match: {'✓' if predicted_label == expected else '✗'}")
            
            if prediction.get('all_predictions'):
                logger.info("  All predictions:")
                for pred in prediction['all_predictions']:
                    logger.info(f"    - {pred['label']}: {pred['confidence']:.2%}")
        else:
            logger.error(f"Prediction failed: {prediction.get('error')}")
        
        logger.info()


if __name__ == '__main__':
    test_classifier()
