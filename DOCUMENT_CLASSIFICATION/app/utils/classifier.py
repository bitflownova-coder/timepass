"""
ML Classifier Module - TF-IDF and Logistic Regression based classification
"""
import pickle
import numpy as np
from pathlib import Path
import logging
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

logger = logging.getLogger(__name__)


class DocumentClassifier:
    """Document classification using TF-IDF and Logistic Regression"""
    
    def __init__(self, model_path='models/logistic_model.pkl', 
                 vectorizer_path='models/tfidf_vectorizer.pkl'):
        """
        Initialize classifier
        
        Args:
            model_path (str): Path to save/load model
            vectorizer_path (str): Path to save/load vectorizer
        """
        self.model_path = Path(model_path)
        self.vectorizer_path = Path(vectorizer_path)
        self.model = None
        self.vectorizer = None
        self.classes = None
        self.is_trained = False
    
    def train(self, training_data, training_labels):
        """
        Train classifier on training data
        
        Args:
            training_data (list): List of document texts
            training_labels (list): List of corresponding labels
        
        Returns:
            dict: Training metrics
        """
        try:
            logger.info("Starting model training...")
            
            # Create TF-IDF vectorizer
            self.vectorizer = TfidfVectorizer(
                max_features=5000,
                min_df=1,
                max_df=0.95,
                stop_words='english',
                ngram_range=(1, 2),
                lowercase=True
            )
            
            # Transform training data
            X_train = self.vectorizer.fit_transform(training_data)
            y_train = np.array(training_labels)
            
            # Store classes
            self.classes = np.unique(y_train)
            
            # Train Logistic Regression
            self.model = LogisticRegression(
                max_iter=1000,
                random_state=42,
                multi_class='multinomial',
                solver='lbfgs'
            )
            self.model.fit(X_train, y_train)
            
            # Calculate accuracy
            train_predictions = self.model.predict(X_train)
            accuracy = accuracy_score(y_train, train_predictions)
            
            self.is_trained = True
            
            logger.info(f"Model training completed. Accuracy: {accuracy:.2%}")
            
            return {
                'success': True,
                'accuracy': accuracy,
                'num_classes': len(self.classes),
                'classes': list(self.classes),
                'num_features': X_train.shape[1]
            }
        
        except Exception as e:
            logger.error(f"Training failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def predict(self, text, return_probabilities=False):
        """
        Predict document category
        
        Args:
            text (str): Document text to classify
            return_probabilities (bool): Return all class probabilities
        
        Returns:
            dict: {
                'predicted_label': str,
                'confidence_score': float,
                'all_predictions': list (if return_probabilities=True)
            }
        """
        try:
            if not self.is_trained or self.model is None or self.vectorizer is None:
                return {
                    'success': False,
                    'error': 'Model not trained'
                }
            
            # Transform text
            X = self.vectorizer.transform([text])
            
            # Get prediction and probabilities
            prediction = self.model.predict(X)[0]
            probabilities = self.model.predict_proba(X)[0]
            confidence = float(np.max(probabilities))
            
            result = {
                'success': True,
                'predicted_label': prediction,
                'confidence_score': confidence
            }
            
            if return_probabilities:
                # Get all predictions sorted by confidence
                all_predictions = sorted(
                    zip(self.classes, probabilities),
                    key=lambda x: x[1],
                    reverse=True
                )
                result['all_predictions'] = [
                    {
                        'label': label,
                        'confidence': float(conf)
                    }
                    for label, conf in all_predictions
                ]
            
            return result
        
        except Exception as e:
            logger.error(f"Prediction failed: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def save(self):
        """Save trained model and vectorizer"""
        try:
            # Create models directory
            self.model_path.parent.mkdir(parents=True, exist_ok=True)
            self.vectorizer_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save model
            with open(self.model_path, 'wb') as f:
                pickle.dump(self.model, f)
            
            # Save vectorizer
            with open(self.vectorizer_path, 'wb') as f:
                pickle.dump(self.vectorizer, f)
            
            logger.info(f"Model saved to {self.model_path}")
            logger.info(f"Vectorizer saved to {self.vectorizer_path}")
            
            return {'success': True, 'message': 'Models saved successfully'}
        
        except Exception as e:
            logger.error(f"Failed to save models: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def load(self):
        """Load trained model and vectorizer"""
        try:
            if not self.model_path.exists() or not self.vectorizer_path.exists():
                logger.warning("Model files not found")
                return {'success': False, 'error': 'Model files not found'}
            
            # Load model
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            
            # Load vectorizer
            with open(self.vectorizer_path, 'rb') as f:
                self.vectorizer = pickle.load(f)
            
            # Get classes from model
            self.classes = self.model.classes_
            self.is_trained = True
            
            logger.info("Models loaded successfully")
            return {'success': True, 'message': 'Models loaded successfully'}
        
        except Exception as e:
            logger.error(f"Failed to load models: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def evaluate(self, test_data, test_labels):
        """
        Evaluate model on test data
        
        Args:
            test_data (list): List of test documents
            test_labels (list): List of test labels
        
        Returns:
            dict: Evaluation metrics
        """
        try:
            if not self.is_trained:
                return {'success': False, 'error': 'Model not trained'}
            
            # Transform test data
            X_test = self.vectorizer.transform(test_data)
            y_test = np.array(test_labels)
            
            # Get predictions
            predictions = self.model.predict(X_test)
            
            # Calculate metrics
            accuracy = accuracy_score(y_test, predictions)
            
            # Get classification report
            report = classification_report(
                y_test, predictions,
                output_dict=True
            )
            
            # Get confusion matrix
            conf_matrix = confusion_matrix(y_test, predictions)
            
            return {
                'success': True,
                'accuracy': float(accuracy),
                'classification_report': report,
                'confusion_matrix': conf_matrix.tolist()
            }
        
        except Exception as e:
            logger.error(f"Evaluation failed: {str(e)}")
            return {'success': False, 'error': str(e)}
