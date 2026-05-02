"""
Model Training Script - Train and save ML model
"""
import os
from pathlib import Path
import logging
from app.utils.text_extractor import TextExtractor, TextPreprocessor
from app.utils.classifier import DocumentClassifier

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_training_data(training_folder='data/training'):
    """
    Load training data from organized folders
    
    Args:
        training_folder (str): Path to training data folder
    
    Returns:
        tuple: (texts, labels)
    """
    texts = []
    labels = []
    
    training_path = Path(training_folder)
    
    if not training_path.exists():
        logger.warning(f"Training folder not found: {training_folder}")
        return [], []
    
    # Iterate through category folders
    for category_folder in training_path.iterdir():
        if not category_folder.is_dir():
            continue
        
        category_label = category_folder.name
        logger.info(f"Loading category: {category_label}")
        
        # Load all files in category
        for file_path in category_folder.glob('*'):
            if file_path.is_file():
                try:
                    # Extract text
                    result = TextExtractor.extract_text(str(file_path))
                    
                    if result['success'] and result['text']:
                        # Preprocess
                        processed_text = TextPreprocessor.preprocess(result['text'])
                        
                        if processed_text:  # Only add if text exists after preprocessing
                            texts.append(processed_text)
                            labels.append(category_label)
                            logger.info(f"  Loaded: {file_path.name}")
                
                except Exception as e:
                    logger.error(f"Error loading {file_path}: {str(e)}")
    
    logger.info(f"Loaded {len(texts)} documents from {len(set(labels))} categories")
    logger.info(f"Categories: {set(labels)}")
    
    return texts, labels


def train_model(training_folder='data/training', 
                model_path='models/logistic_model.pkl',
                vectorizer_path='models/tfidf_vectorizer.pkl'):
    """
    Train and save ML model
    
    Args:
        training_folder (str): Path to training data
        model_path (str): Path to save model
        vectorizer_path (str): Path to save vectorizer
    
    Returns:
        dict: Training results
    """
    logger.info("Starting model training...")
    
    # Load training data
    texts, labels = load_training_data(training_folder)
    
    if not texts or not labels:
        logger.error("No training data found!")
        return {'success': False, 'error': 'No training data'}
    
    # Initialize classifier
    classifier = DocumentClassifier(model_path, vectorizer_path)
    
    # Train
    training_results = classifier.train(texts, labels)
    
    if not training_results.get('success'):
        logger.error("Training failed!")
        return training_results
    
    # Save model
    save_results = classifier.save()
    
    if not save_results.get('success'):
        logger.error("Failed to save model!")
        return save_results
    
    logger.info("Model training completed successfully!")
    
    return {
        'success': True,
        'training': training_results,
        'saved': save_results,
        'texts_loaded': len(texts),
        'unique_categories': len(set(labels))
    }


if __name__ == '__main__':
    # Train model
    results = train_model()
    
    if results.get('success'):
        logger.info("\n=== Training Results ===")
        logger.info(f"Accuracy: {results['training']['accuracy']:.2%}")
        logger.info(f"Categories: {results['training']['num_classes']}")
        logger.info(f"Features: {results['training']['num_features']}")
        logger.info(f"Training samples: {results['texts_loaded']}")
    else:
        logger.error(f"Training failed: {results.get('error')}")
