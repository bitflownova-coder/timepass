# System Architecture

## High-Level Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend Layer                           │
│  (React / HTML + CSS + JS)                                      │
│  - File Upload UI (Drag & Drop)                                 │
│  - Dashboard & Charts                                           │
│  - Search Interface                                             │
└────────────────────────┬────────────────────────────────────────┘
                         │ HTTP/HTTPS
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                     Nginx Reverse Proxy                          │
│  - Load Balancing                                               │
│  - SSL/TLS Termination                                          │
│  - Static File Serving                                          │
│  - Request Routing                                              │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Application Layer                             │
│                    (Flask + WSGI)                               │
│                                                                 │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │              API Routes & Endpoints                      │  │
│  │  - Authentication & JWT                                  │  │
│  │  - File Upload & Management                              │  │
│  │  - Classification & Predictions                          │  │
│  │  - Search & Filtering                                    │  │
│  │  - Dashboard & Analytics                                 │  │
│  └──────────────────────────────────────────────────────────┘  │
│                         │                                        │
│         ┌───────────────┼───────────────┬──────────────┐        │
│         ↓               ↓               ↓              ↓        │
│  ┌────────────┐ ┌──────────────┐ ┌────────────┐ ┌─────────┐  │
│  │Text        │ │Classifier    │ │Encryption │ │Validator│  │
│  │Extraction  │ │& Matching    │ │& Security │ │& Logging│  │
│  │- PyPDF2    │ │- TF-IDF      │ │- AES      │ │- Audit  │  │
│  │- OCR       │ │- Cosine Sim  │ │- Hashing  │ │- Logs   │  │
│  └────────────┘ └──────────────┘ └────────────┘ └─────────┘  │
└─────────────────────────────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         ↓               ↓               ↓
┌─────────────────┐ ┌─────────────┐ ┌──────────────┐
│  SQLite DB      │ │File Storage │ │ML Models     │
│  - Users        │ │- Encrypted  │ │- TF-IDF      │
│  - Documents    │ │  Files      │ │- Logistic Reg│
│  - Audit Logs   │ │- Metadata   │ │- Vectorizer  │
│  - Feedback     │ │             │ │              │
└─────────────────┘ └─────────────┘ └──────────────┘
```

---

## Component Architecture

### 1. Frontend Layer

**Technology:** React or HTML/CSS/JavaScript

**Responsibilities:**
- File upload interface with drag-drop
- Real-time feedback on classification
- Dashboard with statistics and charts
- Search interface with filters
- User authentication UI

**Key Components:**
```
Frontend/
├── Upload Component
│   ├── File Input
│   ├── Progress Bar
│   └── Confirmation Modal
├── Dashboard Component
│   ├── Statistics Card
│   ├── Charts
│   └── Recent Documents
├── Search Component
│   ├── Search Bar
│   ├── Filters
│   └── Results Table
└── Auth Component
    ├── Login Form
    └── Register Form
```

---

### 2. API Layer (Flask)

**Technology:** Flask + Flask-RESTful

**Responsibilities:**
- Handle HTTP requests/responses
- Authentication and authorization
- Request validation
- Response formatting
- Error handling

**Route Structure:**
```
/api/
├── /auth
│   ├── POST /register
│   ├── POST /login
│   └── POST /logout
├── /upload
│   ├── POST /
│   └── POST /{id}/confirm
├── /documents
│   ├── GET /
│   ├── GET /{id}
│   ├── PATCH /{id}
│   └── DELETE /{id}
├── /classify
│   └── POST /
├── /search
│   └── GET /
└── /dashboard
    ├── GET /stats
    └── GET /charts
```

---

### 3. Business Logic Layer

#### a) Text Extraction Module
```python
text_extractor.py
├── extract_from_pdf()
├── extract_from_docx()
├── extract_from_image()
└── preprocess_text()
```

**Process:**
```
File Upload
    ↓
Detect File Type
    ↓
Select Appropriate Extractor
    ├── PDF → PyPDF2/pdfplumber
    ├── DOCX → python-docx
    └── Image → Tesseract OCR
    ↓
Extract Raw Text
    ↓
Text Preprocessing
├── Remove special characters
├── Convert to lowercase
├── Tokenization
└── Stop word removal
    ↓
Clean Text for Classification
```

#### b) Classification Module
```python
classifier.py
├── load_models()
├── predict()
├── get_confidence_scores()
├── suggest_folder()
└── train_classifier()
```

**Classification Pipeline:**
```
Cleaned Text
    ↓
TF-IDF Vectorization
├── Convert text → numerical features
├── TF-IDF weights for term importance
└── Feature vector
    ↓
Logistic Regression Prediction
├── Calculate probabilities for each class
├── Return top prediction
└── Extract confidence scores
    ↓
Decision Logic
├── IF confidence > 80%:
│   └── Auto-suggest folder
├── ELSE IF confidence 60-80%:
│   └── Ask user
└── ELSE:
    └── Ask user to create folder
    ↓
Folder Matching (Cosine Similarity)
├── TF-IDF vectors of prediction
├── TF-IDF vectors of folder names
├── Calculate similarity
└── Find best match
    ↓
Classification Result
{
    "predicted_label": "Invoice",
    "confidence": 0.92,
    "suggested_folder": "Bills",
    "similar_folders": ["Bills", "Payments"]
}
```

#### c) Encryption Module
```python
encryption.py
├── encrypt_file()
├── decrypt_file()
├── generate_key()
└── hash_password()
```

**Encryption Flow:**
```
File → AES-256 Encryption → Encrypted File
        ↓
        Key derivation from password
        (using bcrypt/Argon2)

Access Request → Key Generation → Decrypt → Original File
```

#### d) Validation Module
```python
validators.py
├── validate_file_type()
├── validate_file_size()
├── validate_user_input()
└── sanitize_input()
```

---

### 4. Data Layer

#### a) Database (SQLite + SQLAlchemy ORM)

**Connection:**
```python
# SQLAlchemy manages connections
engine = create_engine('sqlite:///app.db')
session = Session(engine)
```

**Models:**
- User
- Document
- Feedback
- AuditLog
- FileMetadata

#### b) File Storage

**Structure:**
```
data/uploads/
└── {user_id}/
    ├── Resume/
    │   ├── resume_enc_abc123.bin
    │   └── resume_enc_def456.bin
    ├── Bills/
    │   └── bill_enc_ghi789.bin
    └── Legal/
        └── contract_enc_jkl012.bin
```

**Security:**
- Files encrypted with AES-256
- Filename encrypted/hashed
- Metadata stored in DB
- Access controlled per user

#### c) ML Models Storage

```
models/
├── tfidf_vectorizer.pkl
│   └── Serialized TF-IDF vectorizer
├── logistic_model.pkl
│   └── Trained Logistic Regression model
└── training_metadata.json
    └── Model info and metrics
```

---

### 5. Security Layer

**Authentication Flow:**
```
1. User provides email + password
    ↓
2. Hash password with bcrypt
    ↓
3. Compare with stored hash
    ↓
4. If match:
   - Generate JWT token
   - Set expiration (24 hours)
   - Return token
    ↓
5. For each request:
   - Extract token from header
   - Decode JWT
   - Verify signature
   - Check expiration
   - Grant/deny access
```

**Authorization Flow:**
```
Request with JWT
    ↓
Decode & Extract User ID
    ↓
Check User Role (Admin/User)
    ↓
Check Resource Ownership
    ├── If User: Only access own files
    └── If Admin: Access all files
    ↓
Grant/Deny Access
```

---

## Data Flow Diagrams

### File Upload Flow

```
User Browser
    ↓
[Drag & Drop File]
    ↓
Frontend validates file
    ↓
POST /api/upload (JWT token)
    ↓
Backend Authentication
    ├── Decode JWT
    ├── Verify user
    └── Check permissions
    ↓
File Validation
├── Check file type (PDF/DOCX/JPG)
├── Check file size (<50MB)
└── Calculate hash (SHA256)
    ↓
Duplicate Check
├── Look up file hash in DB
├── If found: Notify user
└── If not: Continue
    ↓
Text Extraction
├── Detect file type
├── Extract text
└── Preprocess
    ↓
Classification
├── TF-IDF vectorization
├── Logistic Regression prediction
├── Get confidence score
└── Suggest folder
    ↓
Encryption
├── Generate encryption key
├── Encrypt file with AES-256
└── Save encrypted file to storage
    ↓
Database Operations
├── Save document metadata
├── Save audit log
└── Update user storage
    ↓
Response to User
{
    "predicted_label": "Invoice",
    "confidence": 0.92,
    "suggested_folder": "Bills",
    "action": "confirm_placement"
}
    ↓
User Confirmation
├── Accepts suggestion
├── Or chooses different folder
└── Or creates new folder
    ↓
File Moved to Final Location
    ↓
Update database with final folder
    ↓
Complete
```

### Search Flow

```
User enters search query
    ↓
Frontend sends: GET /api/search?q=invoice&category=Bills
    ↓
Backend receives request
    ↓
Validate & authenticate user
    ↓
Parse query parameters
├── Keyword: "invoice"
├── Category: "Bills"
├── Date range: optional
└── Limit: 20
    ↓
Query Database
├── SELECT * FROM document
├── WHERE user_id = current_user
├── AND extracted_text LIKE "%invoice%"
├── AND user_folder = "Bills"
└── LIMIT 20
    ↓
Process Results
├── Decrypt file previews
├── Calculate relevance scores
└── Rank by relevance
    ↓
Return Results
```

---

## ML Pipeline Details

### Model Training Phase

```
Training Data Collection
├── Resume documents
├── Invoice documents
├── Legal documents
└── Other categories

    ↓

Data Preprocessing
├── Text extraction
├── Lowercasing
├── Punctuation removal
├── Tokenization
├── Stop word removal

    ↓

Feature Extraction (TF-IDF)
├── Term Frequency calculation
├── Inverse Document Frequency calculation
├── TF-IDF score = TF × IDF

    ↓

Train Test Split
├── 80% Training data
└── 20% Test data

    ↓

Model Training (Logistic Regression)
├── Initialize model
├── Fit on training data
├── Learn decision boundaries

    ↓

Model Evaluation
├── Test on test data
├── Calculate accuracy, precision, recall
├── Generate confusion matrix

    ↓

Save Models
├── Pickle TF-IDF vectorizer
└── Pickle trained model
```

### Prediction Phase

```
New Document
    ↓
Text Extraction & Preprocessing
    ↓
Load Vectorizer (from pickle)
    ↓
Transform text to TF-IDF vector
    ↓
Load Trained Model (from pickle)
    ↓
Make Prediction
├── Calculate probability for each class
├── Return top prediction
└── Get confidence score

    ↓

Decision Logic (Confidence Threshold)
├── If confidence >= 0.8:
│   → Auto-suggest folder
├── Elif confidence >= 0.6:
│   → Ask user to confirm
└── Else:
    → Ask user to choose folder

    ↓

Folder Matching
├── Calculate TF-IDF for predicted label
├── Calculate TF-IDF for each existing folder name
├── Compute cosine similarity
├── Find closest match

    ↓

Return Result
```

---

## Deployment Architecture

### Development Environment
```
Developer Machine
├── Python interpreter
├── Virtual environment
├── Flask dev server (port 5000)
├── SQLite database
└── Local file storage
```

### Production Environment
```
┌─────────────────────────────────────┐
│         Internet / Users            │
└────────────────┬────────────────────┘
                 │ HTTPS (443)
                 ↓
        ┌─────────────────┐
        │    Nginx        │
        │  Reverse Proxy  │
        │  Load Balancer  │
        └────────┬────────┘
                 │ HTTP (8000)
        ┌────────┴────────────┐
        ↓                     ↓
    ┌─────────┐         ┌─────────┐
    │Gunicorn │         │Gunicorn │
    │Worker 1 │         │Worker 2 │
    └────┬────┘         └────┬────┘
         └────────┬──────────┘
                  ↓
          ┌──────────────────┐
          │  SQLite Database │
          │   (Persistent)   │
          └──────────────────┘
          
          ┌──────────────────┐
          │  File Storage    │
          │  (Encrypted)     │
          └──────────────────┘
          
          ┌──────────────────┐
          │   Backup System  │
          │  (S3 or local)   │
          └──────────────────┘
```

---

## Scalability Considerations

### Horizontal Scaling

```
Current:
Nginx → Single Gunicorn → SQLite

Future:
                    ┌─────────────────────────┐
                    │       Nginx             │
                    │   Load Balancer         │
                    └────────┬────────────────┘
                             │
                ┌────────────┼────────────┐
                ↓            ↓            ↓
            ┌────────┐  ┌────────┐  ┌────────┐
            │Gunicorn│  │Gunicorn│  │Gunicorn│
            │ Pool   │  │ Pool   │  │ Pool   │
            └────┬───┘  └────┬───┘  └────┬───┘
                 └──────┬─────┴──────┬────┘
                        ↓            ↓
                   ┌─────────────────────┐
                   │   PostgreSQL        │
                   │  (Replicated)       │
                   └─────────────────────┘
                   
                   ┌─────────────────────┐
                   │   S3 Object Store   │
                   │  (File Storage)     │
                   └─────────────────────┘
```

### Caching Layer

```
    ┌──────────────┐
    │   Redis      │
    │   Cache      │
    └──────────────┘
           │
    ┌──────┴──────┐
    ↓             ↓
  Users      Documents
  Sessions   Classifications
```

---

## Technology Stack Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| Frontend | React/HTML | User interface |
| Proxy | Nginx | Load balancing, SSL termination |
| API | Flask | Web framework |
| ORM | SQLAlchemy | Database abstraction |
| Database | SQLite | Data persistence |
| ML | scikit-learn | Classification |
| Text | PyPDF2 | PDF extraction |
| OCR | Tesseract | Image text extraction |
| Encryption | cryptography | Data security |
| Auth | PyJWT | Token-based auth |
| Server | Gunicorn | WSGI app server |
| Testing | pytest | Unit testing |
| Deployment | Docker | Containerization |

---

## Security Architecture

```
┌────────────────────────────────────────┐
│         TLS/SSL Encryption             │
└────────────────────────────────────────┘
            ↓
┌────────────────────────────────────────┐
│    JWT Authentication Layer            │
│  - Token generation                    │
│  - Token validation                    │
│  - Expiration handling                 │
└────────────────────────────────────────┘
            ↓
┌────────────────────────────────────────┐
│    Authorization Layer (RBAC)          │
│  - User role checking                  │
│  - Resource permission checking        │
│  - Admin/User access control           │
└────────────────────────────────────────┘
            ↓
┌────────────────────────────────────────┐
│    Input Validation & Sanitization     │
│  - File type validation                │
│  - Size validation                     │
│  - SQL injection prevention            │
├────────────────────────────────────────┤
│    Application Logic                   │
├────────────────────────────────────────┤
│    Database                            │
│  - Parameterized queries               │
│  - Prepared statements                 │
└────────────────────────────────────────┘
            ↓
┌────────────────────────────────────────┐
│    File Encryption (AES-256)           │
│  - Encrypted at rest                   │
│  - Encrypted during transfer           │
│  - Key derivation from password        │
└────────────────────────────────────────┘
            ↓
┌────────────────────────────────────────┐
│    Audit Logging                       │
│  - All actions logged                  │
│  - Timestamp recorded                  │
│  - User tracked                        │
└────────────────────────────────────────┘
```

---

Last Updated: April 20, 2026
