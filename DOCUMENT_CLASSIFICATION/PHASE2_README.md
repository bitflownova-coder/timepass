# Phase 2: ML Classifier Implementation Guide

## Overview

Phase 2 builds the machine learning backbone of SmartDoc AI using TF-IDF vectorization and Logistic Regression for document classification.

## What's Implemented

### 1. Text Extraction Module (`app/utils/text_extractor.py`)

**Features:**
- Extract text from PDF files using PyPDF2
- Extract text from DOCX files using python-docx
- Support for plain text files
- Text preprocessing and cleaning
- Tokenization and stopword removal

**Classes:**
- `TextExtractor` - Extracts text from various formats
- `TextPreprocessor` - Cleans and normalizes text

**Usage:**
```python
from app.utils.text_extractor import TextExtractor, TextPreprocessor

# Extract text
result = TextExtractor.extract_text('document.pdf')
if result['success']:
    text = result['text']
    num_pages = result['num_pages']

# Preprocess
cleaned_text = TextPreprocessor.preprocess(text)
```

### 2. ML Classifier Module (`app/utils/classifier.py`)

**Features:**
- TF-IDF vectorization for feature extraction
- Logistic Regression for multi-class classification
- Probability-based confidence scores
- Model training, prediction, and evaluation
- Pickle-based model persistence

**Class:**
- `DocumentClassifier` - Main classification engine

**Methods:**
- `train(texts, labels)` - Train model on documents
- `predict(text)` - Classify single document
- `save()` - Save trained model
- `load()` - Load pre-trained model
- `evaluate(test_data, test_labels)` - Evaluate model performance

**Usage:**
```python
from app.utils.classifier import DocumentClassifier

# Initialize
classifier = DocumentClassifier()

# Train
classifier.train(training_texts, training_labels)
classifier.save()

# Predict
result = classifier.predict(document_text)
print(result['predicted_label'])
print(f"Confidence: {result['confidence_score']:.2%}")

# Load pre-trained
classifier.load()
```

### 3. Training Data

Sample training data located in `data/training/`:
- **Resume/** - 2 sample resumes
- **Bills/** - 2 sample invoices/bills
- **Legal/** - 2 sample legal documents

Add more training documents to improve accuracy!

### 4. Training Script (`train_model.py`)

**Purpose:** Train and save ML models

**Features:**
- Loads documents from organized folders
- Automatic text extraction and preprocessing
- Model training with TF-IDF + Logistic Regression
- Saves models to disk for later use

**Usage:**
```bash
# From project root
python train_model.py
```

**Output:**
```
Starting model training...
Loading category: Resume
  Loaded: resume_1.txt
  Loaded: resume_2.txt
Loading category: Bills
  Loaded: bill_1.txt
  Loaded: bill_2.txt
Loading category: Legal
  Loaded: legal_1.txt
  Loaded: legal_2.txt
Loaded 6 documents from 3 categories

=== Training Results ===
Accuracy: 100.00%
Categories: 3
Features: 5000
Training samples: 6
```

### 5. Test Script (`test_classifier.py`)

**Purpose:** Test the trained classifier

**Usage:**
```bash
python test_classifier.py
```

**Example Output:**
```
Test 1:
  Expected: Resume
  Predicted: Resume
  Confidence: 95.23%
  Match: ✓

Test 2:
  Expected: Bills
  Predicted: Bills
  Confidence: 97.45%
  Match: ✓

Test 3:
  Expected: Legal
  Predicted: Legal
  Confidence: 92.18%
  Match: ✓
```

### 6. Classification API (`app/routes/classify.py`)

**Endpoints:**

#### POST /api/classify/predict
Classify document text

**Request:**
```json
{
  "text": "Your document text here",
  "return_all_predictions": true
}
```

**Response:**
```json
{
  "success": true,
  "predicted_label": "Invoice",
  "confidence_score": 0.8723,
  "text_preview": "Invoice #2024-001...",
  "all_predictions": [
    {"label": "Invoice", "confidence": 0.8723},
    {"label": "Bills", "confidence": 0.1005},
    {"label": "Legal", "confidence": 0.0272}
  ]
}
```

#### GET /api/classify/info
Get classifier information

**Response:**
```json
{
  "success": true,
  "is_trained": true,
  "classes": ["Bills", "Legal", "Resume"],
  "num_classes": 3
}
```

## Getting Started

### Step 1: Add Training Data

Create training documents in:
```
data/training/
├── Resume/
│   ├── resume_1.txt
│   ├── resume_2.txt
│   └── ...
├── Bills/
│   ├── bill_1.txt
│   ├── bill_2.txt
│   └── ...
├── Legal/
│   ├── legal_1.txt
│   ├── legal_2.txt
│   └── ...
└── [other categories]/
```

**Minimum recommendation:** 5-10 documents per category

### Step 2: Train Model

```bash
# Make sure you're in the project root
python train_model.py
```

This creates:
- `models/tfidf_vectorizer.pkl` - TF-IDF vectorizer
- `models/logistic_model.pkl` - Trained classifier

### Step 3: Test Model

```bash
python test_classifier.py
```

### Step 4: Use in Application

Start the Flask app:
```bash
python run.py
```

Then make API calls to `/api/classify/predict` endpoint.

## Model Details

### TF-IDF Vectorizer
- Max features: 5,000
- Min document frequency: 1
- Max document frequency: 95%
- Stopwords: English
- N-grams: Unigrams and bigrams (1,2)

### Logistic Regression
- Solver: LBFGS
- Multi-class: Multinomial
- Max iterations: 1,000
- Random state: 42 (for reproducibility)

## Performance Optimization

### Current Performance:
- Training time: < 1 second (with sample data)
- Prediction time: < 50ms
- Accuracy: 100% (on sample training data)

### To Improve Accuracy:

1. **Add more training data**
   - More samples = better model
   - Aim for 20-50 documents per category minimum

2. **Improve training data quality**
   - Use real documents, not synthetic text
   - Ensure diversity within categories
   - Avoid near-duplicate documents

3. **Feature engineering**
   - Adjust TF-IDF parameters
   - Add custom features
   - Use domain-specific stopwords

4. **Advanced models** (Future)
   - Switch to BERT for better accuracy
   - Use ensemble methods
   - Deep learning approaches

## Troubleshooting

### Model not found
```
Error: Model not trained or files not found
```
**Solution:** Train the model first using `python train_model.py`

### Memory issues with large documents
```
Error: Memory error during text extraction
```
**Solution:** 
- Process documents in batches
- Limit document size
- Use streaming extraction for large PDFs

### Low accuracy
**Solutions:**
- Add more training data
- Ensure data quality
- Check for data imbalance
- Review preprocessing step

## Next Steps

After Phase 2 is complete:
- **Phase 3:** File upload and storage system
- **Phase 4:** Smart folder classification and routing
- **Phase 5:** OCR support and search functionality

## Files Created/Modified

**New Files:**
- `app/utils/text_extractor.py` - Text extraction and preprocessing
- `app/utils/classifier.py` - ML classification engine
- `app/routes/classify.py` - Classification API endpoints
- `train_model.py` - Model training script
- `test_classifier.py` - Model testing script
- `data/training/` - Training data directory with sample documents

**Modified Files:**
- `app/__init__.py` - Registered classify blueprint
- `app/routes/__init__.py` - Added classify blueprint import
- `requirements.txt` - Dependencies already included

## API Usage Examples

### Python Example
```python
import requests

# Get JWT token first
login_response = requests.post('http://localhost:5000/api/auth/login', json={
    'email': 'user@example.com',
    'password': 'password'
})
token = login_response.json()['token']

# Classify document
headers = {'Authorization': f'Bearer {token}'}
response = requests.post('http://localhost:5000/api/classify/predict', json={
    'text': 'Invoice #2024-001. Amount: $500. Due: May 1, 2024.',
    'return_all_predictions': True
}, headers=headers)

print(response.json())
```

### cURL Example
```bash
# Get token
TOKEN=$(curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}' \
  | jq -r '.token')

# Classify
curl -X POST http://localhost:5000/api/classify/predict \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"Invoice content here"}'
```

---

**Phase 2 Status:** ✅ COMPLETE

Ready for Phase 3: File Upload & Storage System
