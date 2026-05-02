# Setup & Installation Guide

Complete step-by-step guide to set up SmartDoc AI development and production environments.

## Table of Contents

1. [System Requirements](#system-requirements)
2. [Development Setup](#development-setup)
3. [Production Setup](#production-setup)
4. [Docker Setup](#docker-setup)
5. [Configuration](#configuration)
6. [Database Setup](#database-setup)
7. [ML Model Training](#ml-model-training)
8. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements

- **OS**: Windows, Linux, or macOS
- **Python**: 3.9 or higher
- **RAM**: 4 GB (8 GB recommended)
- **Storage**: 10 GB
- **Browser**: Chrome, Firefox, Safari (latest)

### Optional (For OCR)

- **Tesseract**: For OCR functionality
- **CUDA**: For GPU acceleration (optional)

---

## Development Setup

### Step 1: Clone Repository

```bash
git clone https://github.com/yourusername/document-classification.git
cd document-classification
```

### Step 2: Create Virtual Environment

**On Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**On Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

Verify activation (you should see `(venv)` in your terminal):
```
(venv) $
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Verify installation:
```bash
python -c "import flask, sklearn; print('All dependencies installed!')"
```

### Step 4: Environment Configuration

Copy example environment file:
```bash
cp .env.example .env
```

Edit `.env` with your settings:
```bash
# On Windows
notepad .env

# On Linux/macOS
nano .env
```

See [Configuration](#configuration) section for details.

### Step 5: Database Setup

Initialize SQLite database:

```bash
python
```

```python
from app import create_app, db

app = create_app()

with app.app_context():
    db.create_all()
    print("Database initialized!")
    
exit()
```

### Step 6: Download OCR Data (Optional)

**For Tesseract on Windows:**
1. Download from: https://github.com/UB-Mannheim/tesseract/wiki
2. Run installer
3. Update `TESSERACT_PATH` in `.env`

**For Linux:**
```bash
sudo apt-get install tesseract-ocr
```

**For macOS:**
```bash
brew install tesseract
```

### Step 7: Train ML Models

```bash
python
```

```python
from app.utils.classifier import train_classifier

# Train models
train_classifier('data/training/')
print("Models trained successfully!")

exit()
```

### Step 8: Run Development Server

```bash
python run.py
```

Output should show:
```
 * Running on http://127.0.0.1:5000
 * Debug mode: on
```

Open browser: http://localhost:5000

---

## Production Setup

### Step 1: Server Setup

**On Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install python3.9 python3.9-venv python3.9-dev
sudo apt install nginx supervisor
```

**On CentOS/RHEL:**
```bash
sudo yum install python39 python39-devel
sudo yum install nginx supervisor
```

### Step 2: Create Application User

```bash
sudo useradd -m -s /bin/bash smartdoc
sudo su - smartdoc
```

### Step 3: Clone and Setup

```bash
git clone https://github.com/yourusername/document-classification.git
cd document-classification

python3.9 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Production Environment

```bash
cp .env.example .env
```

Edit `.env` for production:
```
FLASK_ENV=production
SECRET_KEY=your-very-secure-random-key-here
DEBUG=False
DATABASE_URL=sqlite:////home/smartdoc/document-classification/instance/app.db
JWT_SECRET_KEY=your-jwt-secret-key
```

Generate secure key:
```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

### Step 5: Configure Gunicorn

Create `gunicorn.conf.py`:
```python
workers = 4
worker_class = "sync"
bind = "127.0.0.1:8000"
timeout = 30
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s'
```

### Step 6: Configure Nginx

Edit `/etc/nginx/sites-available/smartdoc`:
```nginx
upstream smartdoc {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com;
    client_max_body_size 50M;

    location / {
        proxy_pass http://smartdoc;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias /home/smartdoc/document-classification/app/static;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/smartdoc /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 7: Configure Supervisor

Edit `/etc/supervisor/conf.d/smartdoc.conf`:
```ini
[program:smartdoc]
directory=/home/smartdoc/document-classification
command=/home/smartdoc/document-classification/venv/bin/gunicorn -c gunicorn.conf.py "app:create_app()"
user=smartdoc
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/smartdoc/document-classification/logs/gunicorn.log
```

Start service:
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start smartdoc
```

### Step 8: SSL Certificate (HTTPS)

Using Let's Encrypt:
```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot certonly --nginx -d yourdomain.com
```

Update Nginx config:
```nginx
listen 443 ssl http2;
ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
```

Redirect HTTP to HTTPS:
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}
```

### Step 9: Setup Backups

Create backup script `backup.sh`:
```bash
#!/bin/bash
BACKUP_DIR="/home/smartdoc/backups"
DB_PATH="/home/smartdoc/document-classification/instance/app.db"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
sqlite3 $DB_PATH ".backup '$BACKUP_DIR/app_$TIMESTAMP.db'"

# Keep only last 30 days
find $BACKUP_DIR -name "app_*.db" -mtime +30 -delete
```

Schedule with crontab:
```bash
0 2 * * * /home/smartdoc/backup.sh
```

---

## Docker Setup

### Step 1: Build Docker Image

```bash
docker build -t smartdoc-ai:latest .
```

### Step 2: Run Container

```bash
docker run -d \
  -p 5000:5000 \
  -e FLASK_ENV=production \
  -e SECRET_KEY=your-secret-key \
  -v smartdoc-data:/app/data \
  -v smartdoc-logs:/app/logs \
  --name smartdoc-container \
  smartdoc-ai:latest
```

### Step 3: Docker Compose

Create `docker-compose.yml`:
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      FLASK_ENV: production
      SECRET_KEY: your-secret-key
    volumes:
      - smartdoc-data:/app/data
      - smartdoc-logs:/app/logs
    restart: always
  
  nginx:
    image: nginx:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/nginx/ssl
    depends_on:
      - app
    restart: always

volumes:
  smartdoc-data:
  smartdoc-logs:
```

Start services:
```bash
docker-compose up -d
```

---

## Configuration

### .env File

```env
# Flask Configuration
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DEBUG=True

# Database
DATABASE_URL=sqlite:///instance/app.db
SQLALCHEMY_TRACK_MODIFICATIONS=False

# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key
JWT_ACCESS_TOKEN_EXPIRES=86400

# File Upload
MAX_CONTENT_LENGTH=52428800  # 50MB
UPLOAD_FOLDER=data/uploads

# Security
CORS_ORIGINS=http://localhost:3000,http://localhost:5000

# OCR (Optional)
TESSERACT_PATH=C:\Program Files\Tesseract-OCR\tesseract.exe

# Email (Optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-password

# AWS S3 (Optional, for production file storage)
AWS_ACCESS_KEY_ID=your-key
AWS_SECRET_ACCESS_KEY=your-secret
AWS_S3_BUCKET=smartdoc-uploads

# Encryption
ENCRYPTION_KEY=your-encryption-key

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
```

### Configuration Priority

1. `.env` file (local)
2. Environment variables
3. Default values in `config.py`

---

## Database Setup

### Initialize Database

```bash
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

### Run Migrations

```bash
# Auto-generate migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Database Commands

```bash
# Backup
sqlite3 instance/app.db ".backup backup.db"

# Restore
sqlite3 backup.db ".restore instance/app.db"

# Check integrity
sqlite3 instance/app.db "PRAGMA integrity_check;"
```

---

## ML Model Training

### Training Dataset Structure

```
data/training/
├── Resume/
│   ├── resume_1.txt
│   ├── resume_2.pdf
│   └── ...
├── Bills/
│   ├── bill_1.txt
│   └── ...
├── Legal/
│   └── ...
└── ...
```

### Training Script

```bash
python
```

```python
from app.utils.classifier import train_classifier

# Train with data
train_classifier('data/training/')

# Check accuracy
from app.utils.classifier import evaluate_classifier
accuracy = evaluate_classifier('data/test/')
print(f"Model Accuracy: {accuracy:.2%}")
```

### Pre-trained Models

Pre-trained models included:
- `models/tfidf_vectorizer.pkl`
- `models/logistic_model.pkl`

Load them automatically on app startup.

---

## Troubleshooting

### Issue: ModuleNotFoundError

**Solution:**
```bash
# Ensure virtual environment is activated
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: Database Error

**Solution:**
```bash
# Delete old database and reinitialize
rm instance/app.db
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

### Issue: OCR Not Working

**Solution:**
```bash
# Check Tesseract installation
tesseract --version

# Update path in .env
TESSERACT_PATH=/usr/bin/tesseract  # Linux
TESSERACT_PATH=/usr/local/bin/tesseract  # macOS
```

### Issue: Port Already in Use

**Solution:**
```bash
# Find process using port 5000
lsof -i :5000  # Linux/macOS
netstat -ano | findstr :5000  # Windows

# Kill process or use different port
python run.py --port 5001
```

### Issue: CORS Error

**Solution:**
Update `CORS_ORIGINS` in `.env`:
```
CORS_ORIGINS=http://localhost:3000,http://localhost:5000,https://yourdomain.com
```

### Issue: Large File Upload Fails

**Solution:**
Increase `MAX_CONTENT_LENGTH` in `.env`:
```
MAX_CONTENT_LENGTH=104857600  # 100MB
```

Also update Nginx:
```nginx
client_max_body_size 100M;
```

---

## Verification Checklist

- [ ] Python 3.9+ installed
- [ ] Virtual environment created and activated
- [ ] Dependencies installed (`pip list`)
- [ ] .env file created and configured
- [ ] Database initialized
- [ ] ML models trained
- [ ] OCR installed (if needed)
- [ ] Development server starts without errors
- [ ] Can access http://localhost:5000
- [ ] Can create user account
- [ ] Can upload document
- [ ] Classification works

---

## Next Steps

1. Read [API Documentation](API_DOCUMENTATION.md)
2. Review [Architecture](ARCHITECTURE.md)
3. Check [Security](SECURITY.md) guidelines
4. Start Phase 2 development

---

Last Updated: April 20, 2026
