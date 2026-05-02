# SmartDoc AI

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.3-000000?logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.3-F7931E?logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![Docker](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)](docker-compose.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**SmartDoc AI** is a self-hosted document classification and intelligent filing system. Upload a PDF, image, or Office document and the system extracts the text, runs it through a trained TF-IDF + Logistic Regression pipeline, and suggests the best-matching folder — with a confidence score and a confirmation step so you stay in control.

Built for teams and individuals who deal with large volumes of unstructured documents and need a reliable, auditable way to keep them organized.

---

## Features

| Capability | Detail |
|---|---|
| **ML Classification** | TF-IDF vectorizer + Logistic Regression, with per-class confidence scores |
| **Smart Folder Routing** | Cosine similarity matching against your existing folder hierarchy |
| **OCR** | Scanned PDFs and images handled via Tesseract / EasyOCR |
| **File Encryption** | AES-256 encryption for every stored file |
| **Duplicate Detection** | SHA-256 hash check before storage |
| **Keyword Search** | Full-text search with category, date, and tag filters |
| **Audit Log** | Immutable record of every upload, download, and modification |
| **RBAC** | Admin and User roles; users only see their own files |
| **Rate Limiting** | Per-IP request throttling via Flask-Limiter |
| **Docker** | Single-command deployment with `docker compose up` |

---

## Project Structure

```
ai_file_organiser/
├── app/
│   ├── __init__.py              # Application factory
│   ├── models/
│   │   ├── user.py              # User model + authentication
│   │   ├── document.py          # Document & metadata models
│   │   ├── audit_log.py         # Audit event model
│   │   └── virtual_path.py      # Folder hierarchy model
│   ├── routes/
│   │   ├── auth.py              # Register / login / token refresh
│   │   ├── upload.py            # File upload + classification trigger
│   │   ├── classify.py          # Classification & folder routing
│   │   ├── search.py            # Full-text & filtered search
│   │   ├── folders.py           # Folder CRUD
│   │   ├── dashboard.py         # Stats & analytics
│   │   └── views.py             # HTML view routes
│   ├── utils/
│   │   ├── classifier.py        # TF-IDF + Logistic Regression pipeline
│   │   ├── text_extractor.py    # PDF / DOCX / plain text extraction
│   │   ├── ocr_processor.py     # Tesseract / EasyOCR wrapper
│   │   ├── folder_router.py     # Cosine similarity folder matching
│   │   ├── file_storage.py      # Encrypted file I/O
│   │   ├── rbac.py              # Role-based access decorators
│   │   ├── validators.py        # Input validation helpers
│   │   └── retraining.py        # Online re-training from feedback
│   └── static/                  # CSS, JS, assets
├── data/
│   ├── training/                # Per-category training documents
│   │   ├── Resume/
│   │   ├── Bills/
│   │   ├── Legal/
│   │   └── ...
│   └── uploads/                 # Encrypted user uploads (gitignored)
├── models/                      # Saved .pkl artefacts (gitignored)
├── scripts/
│   ├── backup.py
│   ├── restore_backup.py
│   ├── generate_self_signed_cert.py
│   └── watch_folder.py          # Auto-classify files dropped in a folder
├── tests/
│   └── test_classifier.py
├── config.py                    # Environment-aware configuration
├── train_model.py               # CLI training script
├── run.py                       # Development entry point
├── Dockerfile
├── docker-compose.yml
├── nginx.conf
└── requirements.txt
```

---

## Tech Stack

**Backend** — Python 3.9, Flask 2.3, Flask-JWT-Extended, SQLAlchemy, Flask-Limiter

**ML / NLP** — scikit-learn (TF-IDF, Logistic Regression), spaCy, numpy, pandas

**Document Processing** — pdfplumber, PyPDF2, python-docx, pytesseract, EasyOCR, Pillow, OpenCV

**Security** — bcrypt, cryptography (Fernet/AES), PyJWT

**Deployment** — Gunicorn, Nginx, Docker, Sentry

---

## Getting Started

### Prerequisites

- Python 3.9+
- Tesseract OCR — [Windows installer](https://github.com/UB-Mannheim/tesseract/wiki) · `apt install tesseract-ocr` on Linux
- Docker (optional, for containerised deployment)

### Local Setup

```bash
# 1. Clone the repository
git clone https://github.com/amisha-bitflow/ai_file_organiser.git
cd ai_file_organiser

# 2. Create and activate a virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Open .env and fill in SECRET_KEY, JWT_SECRET_KEY, ENCRYPTION_KEY at minimum

# 5. Train the classification model
python train_model.py

# 6. Start the development server
python run.py
```

The API is now available at `http://localhost:5000`.

### Docker (Recommended for Production)

```bash
cp .env.example .env   # configure secrets first
docker compose up --build -d
```

Nginx will serve on port 80 (and 443 if you provide SSL certificates in `./ssl/`).

---

## Configuration

All configuration is driven by environment variables. Copy `.env.example` to `.env` and update the values:

| Variable | Required | Description |
|---|---|---|
| `SECRET_KEY` | Yes | Flask session signing key |
| `JWT_SECRET_KEY` | Yes | JWT token signing key |
| `ENCRYPTION_KEY` | Yes | Fernet key for file encryption (32-byte base64) |
| `DATABASE_URL` | No | Defaults to `sqlite:///app.db` |
| `FLASK_ENV` | No | `development` / `production` |
| `CONFIDENCE_THRESHOLD` | No | Auto-accept threshold (default `0.80`) |
| `ENABLE_OCR` | No | `true` / `false` (default `true`) |
| `SENTRY_DSN` | No | Sentry error tracking DSN |

See [SETUP_GUIDE.md](SETUP_GUIDE.md) for the full reference.

---

## Training the Model

Place sample documents in `data/training/<CategoryName>/` and run:

```bash
python train_model.py
```

Default categories: `Resume`, `Bills`, `Legal`, `Research Paper`, `Email`, `Notes`.

Add a new category by creating a folder with representative files — no code changes required.

---

## API Overview

Full documentation is in [API_DOCUMENTATION.md](API_DOCUMENTATION.md). Key endpoints:

```
POST   /api/auth/register          Register a new user
POST   /api/auth/login             Obtain JWT access + refresh tokens
POST   /api/upload                 Upload and classify a document
GET    /api/search                 Full-text search with filters
GET    /api/dashboard/stats        File counts, storage usage, category breakdown
PATCH  /api/classify/confirm       Confirm or override the suggested folder
GET    /api/folders                List folder hierarchy
```

### Quick example — upload a file

```bash
# 1. Get a token
TOKEN=$(curl -s -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"yourpassword"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# 2. Upload a document
curl -X POST http://localhost:5000/api/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@invoice.pdf"
```

Response:

```json
{
  "predicted_label": "Bills",
  "confidence": 0.91,
  "suggested_folder": "Bills/2026",
  "suggested_tags": ["invoice", "payment"],
  "document_id": 42
}
```

---

## Classification Pipeline

```
Upload
  └─ Text extraction  (pdfplumber → python-docx → OCR fallback)
       └─ Preprocessing  (lowercase, stop-word removal, lemmatisation)
            └─ TF-IDF vectorisation
                 └─ Logistic Regression  → label + confidence
                      └─ Cosine similarity against folder names
                           └─ Threshold decision
                                ├─ confidence > 0.80  → auto-suggest
                                ├─ 0.60–0.80          → user picks from options
                                └─ < 0.60             → user creates/selects folder
                                     └─ AES encryption + storage + audit log
```

User corrections are stored in the `feedback` table and can be used to periodically retrain the model.

---

## Security

- Passwords hashed with bcrypt (12 rounds)
- Files encrypted at rest using Fernet (AES-128-CBC)
- JWT tokens with configurable expiry; refresh-token rotation supported
- Per-IP rate limiting on all endpoints
- RBAC: admins can manage users and view all logs; users are scoped to their own files
- All file uploads validated against an allowlist of MIME types and a 50 MB size cap
- Security headers (CSP, X-Frame-Options, HSTS) added on every response

See [SECURITY.md](SECURITY.md) for the full threat model.

---

## Testing

```bash
# Run the full test suite
pytest

# With coverage report
pytest --cov=app --cov-report=term-missing tests/

# A specific module
pytest tests/test_classifier.py -v
```

---

## Deployment

See [DEPLOYMENT.md](DEPLOYMENT.md) for production instructions covering:

- Linux server setup with Gunicorn + Nginx + Supervisor
- Docker Compose with health checks
- SSL certificate provisioning
- Scheduled backups (`scripts/backup.py`)

---

## Documentation Index

| Document | Contents |
|---|---|
| [SETUP_GUIDE.md](SETUP_GUIDE.md) | Full installation and environment reference |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Component design and data-flow diagrams |
| [API_DOCUMENTATION.md](API_DOCUMENTATION.md) | Complete REST API reference |
| [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md) | Schema design and relationships |
| [SECURITY.md](SECURITY.md) | Threat model, security controls, reporting |
| [DEPLOYMENT.md](DEPLOYMENT.md) | Production deployment guide |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute |

---

## Contributing

Contributions are welcome. Please read [CONTRIBUTING.md](CONTRIBUTING.md) before opening a pull request.

---

## License

MIT — see [LICENSE](LICENSE) for details.
