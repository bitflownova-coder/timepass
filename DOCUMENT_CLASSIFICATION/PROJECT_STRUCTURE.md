# Project Structure

## Directory Layout

```
document-classification/
│
├── app/                          # Main application package
│   ├── __init__.py               # Flask app factory
│   ├── models/                   # Database models
│   │   ├── __init__.py
│   │   ├── user.py               # User model
│   │   ├── document.py           # Document metadata model
│   │   ├── feedback.py           # User feedback/corrections model
│   │   └── audit_log.py          # Audit logging model
│   │
│   ├── routes/                   # API endpoints
│   │   ├── __init__.py
│   │   ├── auth.py               # Authentication endpoints (login, register, logout)
│   │   ├── upload.py             # File upload endpoints
│   │   ├── classify.py           # Classification endpoints
│   │   ├── search.py             # Search endpoints
│   │   ├── documents.py          # Document management
│   │   └── dashboard.py          # Dashboard data endpoints
│   │
│   ├── utils/                    # Utility modules
│   │   ├── __init__.py
│   │   ├── text_extractor.py     # PDF/Image text extraction
│   │   ├── classifier.py         # ML classification logic
│   │   ├── encryption.py         # AES encryption/decryption
│   │   ├── validators.py         # Input validation
│   │   ├── decorators.py         # Custom decorators (auth, roles)
│   │   └── logger.py             # Audit logging utility
│   │
│   ├── templates/                # HTML templates
│   │   ├── base.html             # Base template
│   │   ├── dashboard.html        # Dashboard page
│   │   ├── upload.html           # Upload page
│   │   ├── search.html           # Search page
│   │   ├── login.html            # Login page
│   │   ├── register.html         # Register page
│   │   └── profile.html          # User profile page
│   │
│   └── static/                   # Static files
│       ├── css/
│       │   └── style.css
│       ├── js/
│       │   ├── upload.js
│       │   ├── search.js
│       │   └── dashboard.js
│       └── images/
│           └── logo.png
│
├── models/                       # Trained ML models
│   ├── tfidf_vectorizer.pkl      # TF-IDF vectorizer
│   ├── logistic_model.pkl        # Trained Logistic Regression model
│   └── training_metadata.json    # Model training info
│
├── data/                         # Data directory
│   ├── training/                 # Training dataset
│   │   ├── Resume/               # Training docs for Resume
│   │   │   ├── resume_1.txt
│   │   │   ├── resume_2.pdf
│   │   │   └── ...
│   │   ├── Bills/                # Training docs for Bills
│   │   ├── Legal/                # Training docs for Legal
│   │   ├── Research_Paper/
│   │   ├── Email/
│   │   └── Notes/
│   │
│   └── uploads/                  # User uploaded files
│       ├── user_1/
│       │   ├── Resume/
│       │   ├── Bills/
│       │   └── ...
│       ├── user_2/
│       └── ...
│
├── tests/                        # Test suite
│   ├── __init__.py
│   ├── test_auth.py              # Authentication tests
│   ├── test_upload.py            # File upload tests
│   ├── test_classifier.py        # ML model tests
│   ├── test_text_extraction.py   # Text extraction tests
│   ├── test_encryption.py        # Encryption tests
│   ├── test_search.py            # Search functionality tests
│   ├── conftest.py               # Pytest fixtures
│   └── test_data/                # Test files
│
├── migrations/                   # Database migrations (Alembic)
│   ├── versions/
│   │   └── *.py
│   ├── env.py
│   ├── script.py.mako
│   └── alembic.ini
│
├── config.py                     # Configuration settings
├── run.py                        # Application entry point
├── requirements.txt              # Python dependencies
├── .env                          # Environment variables (DO NOT COMMIT)
├── .env.example                  # Example environment file
├── .gitignore                    # Git ignore rules
├── setup.py                      # Package setup
├── Dockerfile                    # Docker configuration
├── docker-compose.yml            # Docker compose file
├── nginx.conf                    # Nginx configuration
├── gunicorn.conf.py              # Gunicorn configuration
│
├── docs/                         # Documentation
│   ├── API_DOCUMENTATION.md
│   ├── ARCHITECTURE.md
│   ├── DATABASE_SCHEMA.md
│   ├── DEPLOYMENT.md
│   ├── SECURITY.md
│   └── SETUP_GUIDE.md
│
├── logs/                         # Application logs
│   ├── app.log
│   ├── error.log
│   └── audit.log
│
└── README.md                     # Project README
```

## Key Directories Explained

### `/app`
Core application package containing all business logic:
- **models/**: Database ORM models (User, Document, AuditLog)
- **routes/**: API endpoints organized by functionality
- **utils/**: Reusable utilities (text extraction, ML, encryption)
- **templates/**: HTML templates for web interface
- **static/**: CSS, JavaScript, and images

### `/models`
Trained machine learning models:
- `tfidf_vectorizer.pkl` - TF-IDF feature extraction model
- `logistic_model.pkl` - Trained Logistic Regression classifier
- `training_metadata.json` - Info about model (accuracy, features, etc.)

### `/data`
Application data:
- **training/**: Training dataset organized by category
- **uploads/**: User-uploaded files organized by user_id and category

### `/tests`
Test suite with pytest:
- Unit tests for each module
- Integration tests for API endpoints
- Test fixtures and mock data

### `/migrations`
Database migration scripts using Alembic:
- Version control for database schema
- Reversible migrations

## File Purposes

| File | Purpose |
|------|---------|
| `config.py` | Environment-specific configurations |
| `run.py` | Application entry point |
| `requirements.txt` | Python package dependencies |
| `.env` | Secret keys and credentials (local only) |
| `.env.example` | Template for .env file |
| `.gitignore` | Files to exclude from git |
| `Dockerfile` | Docker container definition |
| `docker-compose.yml` | Multi-container Docker setup |
| `nginx.conf` | Nginx reverse proxy config |
| `gunicorn.conf.py` | Gunicorn server config |

## Development Workflow

```
Source Code
    ↓
Version Control (.git)
    ↓
Testing (/tests)
    ↓
Build (requirements.txt)
    ↓
Deployment (Dockerfile, gunicorn.conf.py)
    ↓
Production Logs (/logs)
```

## Database File Location

SQLite database file location (typically):
```
instance/
└── app.db
```

## Important Notes

1. **Never commit** `.env` file - it contains secrets
2. **Never commit** `/uploads` folder with user data
3. **Never commit** `/logs` folder with sensitive logs
4. **Keep** `.env.example` updated when adding new config keys
5. **Use** `/migrations` for database schema changes
6. **Test** changes thoroughly in `/tests` before deployment
7. **Keep** trained models in `/models` directory

## Git Ignore Example

```
# Virtual environment
venv/
env/

# Python
__pycache__/
*.py[cod]
*.egg-info/
*.egg

# Environment variables
.env
.env.local

# Database
instance/
*.db

# Logs
logs/
*.log

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Uploads
data/uploads/

# Build
dist/
build/
```

## Environment Setup

Initial setup should:
1. Create virtual environment
2. Install dependencies from `requirements.txt`
3. Copy `.env.example` to `.env`
4. Edit `.env` with your values
5. Run migrations
6. Initialize database
7. Train ML models
8. Start development server

---

Last Updated: April 20, 2026
