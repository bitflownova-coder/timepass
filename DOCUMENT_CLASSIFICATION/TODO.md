================================================================================
                    DOCUMENT CLASSIFICATION PROJECT
                        PHASE-WISE TODO LIST
================================================================================

PROJECT NAME: SmartDoc AI / AutoFile AI / IntelliDocs / DocSort AI
PROJECT GOAL: Automatic document classification and folder organization

================================================================================
PHASE 1: PROJECT SETUP & CORE INFRASTRUCTURE (Week 1)
================================================================================

- [x] Create basic project structure and dependencies
  - [x] Initialize Python project with virtual environment
  - [x] Create folder structure (app, models, utils, templates, static)
  - [x] Create requirements.txt with dependencies
  
- [x] Set up Flask backend with authentication (JWT)
  - [x] Install Flask and required packages
  - [x] Create Flask app factory
  - [x] Implement JWT token generation and validation
  - [x] Create login/register endpoints
  
- [x] Set up SQLite database and user model
  - [x] Create database schema with SQLAlchemy
  - [x] Design User model (id, email, password, role, created_at)
  - [x] Implement user registration and login
  - [x] Add password hashing with bcrypt

================================================================================
PHASE 2: BUILD ML CLASSIFIER - TF-IDF + LOGISTIC REGRESSION (Week 2)
================================================================================

- [x] Create training dataset with categories
  - [x] Define categories (Resume, Bills, Legal, Research Paper, Email, Notes)
  - [x] Create sample documents for each category
  - [x] Store dataset in data/training/ folder
  
- [x] Implement text extraction from PDFs (PyPDF)
  - [x] Install PyPDF2 or pdfplumber
  - [x] Create text_extractor.py module
  - [x] Test extraction with sample PDFs
  
- [x] Train TF-IDF vectorizer and Logistic Regression model
  - [x] Load training data
  - [x] Build TF-IDF vectorizer
  - [x] Train Logistic Regression classifier
  - [x] Save model to models/ folder (pickle)
  
- [x] Add confidence scores to predictions
  - [x] Extract probability scores from model
  - [x] Return label + confidence (e.g., "Invoice: 87%")
  - [x] Create prediction API endpoint

================================================================================
PHASE 3: BUILD FILE UPLOAD & STORAGE SYSTEM (Week 3)
================================================================================

- [x] Create file upload API endpoint with validation
  - [x] Create /api/upload endpoint
  - [x] Add file type validation (PDF, DOCX, DOC, TXT, JPG/PNG/GIF/WEBP)
  - [x] Implement file size limits
  - [x] Require user authentication
  
- [x] Implement file encryption (AES) before storage
  - [x] Install cryptography library
  - [x] Create encryption utility module
  - [x] Encrypt files before saving to disk
  - [x] Implement decryption for file retrieval
  
- [x] Set up user-specific folder structure
  - [x] Create uploads/{user_id}/ directory per user
  - [x] Store files under: uploads/{user_id}/{category}/
  - [x] Prevent cross-user access
  
- [x] Implement duplicate detection system
  - [x] Calculate file hash (MD5/SHA256)
  - [x] Check if file already exists in database
  - [x] Alert user if duplicate detected

================================================================================
PHASE 4: IMPLEMENT SMART FOLDER CLASSIFICATION & ROUTING (Week 4)
================================================================================

- [x] Build folder matching using cosine similarity
  - [x] Create TF-IDF vectors from predicted label
  - [x] Create TF-IDF vectors from existing folder names
  - [x] Calculate cosine similarity scores
  - [x] Return best matching folder
  
- [x] Create decision logic with confidence thresholds
  - [x] IF confidence > 80% AND similarity high → auto-suggest folder
  - [x] ELSE IF medium confidence → ask user to choose
  - [x] ELSE → ask user to create new folder
  
- [x] Implement user confirmation workflow
  - [x] Display AI prediction with confidence score
  - [x] Show suggested folder
  - [x] Allow user to accept/reject/choose alternative
  - [x] Allow user to create new folder
  
- [x] Build learning system to store user corrections
  - [x] Save user's folder choice in database
  - [x] Create feedback table (file_id, predicted_label, user_choice)
  - [x] Use corrections to retrain model later

================================================================================
PHASE 5: ADD ADVANCED FEATURES (OCR, SEARCH, METADATA) (Week 4-5)
================================================================================

- [x] Integrate OCR (Tesseract/EasyOCR) for scanned images
  - [x] Install pytesseract or easyocr
  - [x] Implement image-to-text conversion
  - [x] Add OCR preprocessing (gray scale, deskew)
  - [x] Test with scanned PDFs
  
- [x] Build keyword search functionality
  - [x] Create search index of all documents
  - [x] Implement keyword matching
  - [x] Add search API endpoint
  - [x] Support filtering by date, category, etc.
  
- [x] Create document metadata storage and retrieval
  - [x] Store metadata (filename, category, tags, upload_date, size)
  - [x] Create metadata API endpoints
  - [x] Display metadata in UI
  
- [x] Implement audit logging (who, what, when)
  - [x] Create audit log table
  - [x] Log: file uploads, downloads, access, modifications
  - [x] Create audit log viewer endpoint

================================================================================
PHASE 6: BUILD FRONTEND & DASHBOARD (Week 5)
================================================================================

- [x] Create drag & drop file upload UI
  - [x] Design upload interface (HTML/CSS/JS)
  - [x] Implement drag-drop functionality
  - [x] Show upload progress
  - [x] Display upload status
  
- [x] Build dashboard with file statistics and graphs
  - [x] Count files per category
  - [x] Create pie/bar charts
  - [x] Show total storage used
  - [x] Display recent uploads
  
- [x] Implement multi-label tagging interface
  - [x] Add tag selection UI
  - [x] Allow multiple tags per document
  - [x] Save tags to database
  
- [x] Create search interface with filters
  - [x] Search by keyword
  - [x] Filter by category, date range, tags
  - [x] Display search results
  - [x] Add sorting options

================================================================================
PHASE 7: SECURITY & OPTIMIZATION (Week 5)
================================================================================

- [x] Implement Role-Based Access Control (RBAC)
  - [x] Create role types (Admin, User, Viewer)
  - [x] Restrict admin functions to admins only
  - [x] Ensure users only see their own files
  - [x] Implement permission checks on all endpoints
  
- [x] Add rate limiting and input validation
  - [x] Implement Flask-Limiter for API rate limiting
  - [x] Add input validation for all endpoints
  - [x] Sanitize user inputs
  - [x] Validate file types and sizes
  
- [ ] Set up HTTPS/SSL for secure transmission
  - [x] Generate SSL certificates (self-signed script)
  - [x] Configure Flask for HTTPS
  - [x] Add security headers
  
- [ ] Implement backup & recovery system
  - [x] Create automated backup script
  - [x] Schedule daily backups (Windows task script)
  - [x] Store backups securely
  - [ ] Test recovery procedure

================================================================================
PHASE 8: TESTING, DOCUMENTATION & DEPLOYMENT (Week 5)
================================================================================

- [ ] Write unit and integration tests
  - [ ] Test text extraction
  - [x] Test ML model predictions
  - [ ] Test file upload and storage
  - [ ] Test API endpoints
  - [ ] Achieve >80% code coverage
  
- [x] Create API documentation
  - [x] Document all endpoints
  - [x] Include request/response examples
  - [x] Add error codes and messages
  - [x] Create README.md with setup instructions
  
- [ ] Deploy to production server
  - [ ] Set up production environment
  - [ ] Configure database for production
  - [ ] Set up environment variables
  - [ ] Deploy to cloud/server
  
- [x] Set up monitoring and logging
  - [x] Configure logging system
  - [x] Set up error tracking (Sentry)
  - [x] Monitor API performance
  - [x] Track system health

================================================================================
PHASE 9: FILE ORGANISER PDF GAPS (Critical)
================================================================================

- [x] File monitoring engine (watchdog) for auto-detect changes
- [x] spaCy entity extraction (ORG + PERSON)
- [ ] Time extraction from document content (month/year)
- [ ] Multi-dimensional VFS views (By Type / By Client / By Time)
- [ ] Hierarchy engine (multi-level virtual paths)
- [ ] "By Client" view and client-based grouping
- [ ] One file → multiple virtual paths (no duplication)
- [ ] Vector embeddings + semantic index (sentence-transformers)
- [ ] Sync & update engine for modified files
- [ ] Multi-level folder tree UI
- [ ] Inline file quick-preview panel

================================================================================
ADDITIONAL FEATURES (Optional/Future)
================================================================================

- [ ] Two-Factor Authentication (2FA)
- [ ] Document watermarking
- [ ] Tamper detection (hash verification)
- [ ] Multi-language support
- [ ] Smart folder suggestions (AI-powered)
- [ ] Upgrade to BERT for better accuracy
- [ ] Document summarization
- [ ] Email integration
- [ ] Webhook support for 3rd party apps

================================================================================
TECH STACK SUMMARY
================================================================================

Backend:        Python 3.9+, Flask, Flask-RESTful
Authentication: JWT (PyJWT), bcrypt
Database:       SQLite with SQLAlchemy ORM
ML/NLP:         scikit-learn, TF-IDF, Logistic Regression
Text Extract:   PyPDF2 or pdfplumber
OCR:            pytesseract or EasyOCR
Encryption:     cryptography (AES)
Frontend:       React OR simple HTML/CSS/JavaScript
Testing:        pytest, pytest-cov
Deployment:     Gunicorn, Nginx, Docker (optional)

================================================================================
SUCCESS METRICS
================================================================================

- Accuracy: >85% on test documents
- Response time: <2 seconds for classification
- Uptime: 99.9%
- Security: All security features implemented
- UI/UX: User-friendly and intuitive

================================================================================
START DATE: April 20, 2026
ESTIMATED COMPLETION: ~5 weeks
STATUS: IN PROGRESS

================================================================================
