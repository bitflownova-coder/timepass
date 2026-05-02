# Deployment Guide

Complete guide for deploying SmartDoc AI to production.

## Table of Contents

1. [Pre-Deployment Checklist](#pre-deployment-checklist)
2. [Linux Server Deployment](#linux-server-deployment)
3. [Docker Deployment](#docker-deployment)
4. [AWS Deployment](#aws-deployment)
5. [Monitoring & Maintenance](#monitoring--maintenance)
6. [Rollback Procedures](#rollback-procedures)

---

## Pre-Deployment Checklist

- [ ] All tests passing (`pytest`)
- [ ] Code reviewed and approved
- [ ] Security audit completed
- [ ] Environment variables configured
- [ ] Database migrations tested
- [ ] Backups configured and tested
- [ ] SSL certificates generated
- [ ] Monitoring set up
- [ ] Logging configured
- [ ] Team notified of deployment

---

## Linux Server Deployment

### Step 1: Server Setup

**1.1 Launch Ubuntu Server**

```bash
# System update
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y \
    python3.9 python3.9-venv python3.9-dev \
    postgresql postgresql-contrib \
    nginx supervisor redis-server \
    certbot python3-certbot-nginx \
    git curl wget

# Install Tesseract OCR
sudo apt install -y tesseract-ocr
```

**1.2 Create Application User**

```bash
# Create non-root user
sudo useradd -m -s /bin/bash smartdoc
sudo usermod -aG sudo smartdoc

# Switch to user
sudo su - smartdoc
```

### Step 2: Application Setup

**2.1 Clone Repository**

```bash
git clone https://github.com/yourusername/document-classification.git
cd document-classification
```

**2.2 Create Virtual Environment**

```bash
python3.9 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

**2.3 Configure Environment**

```bash
cp .env.example .env
nano .env
```

Set production values:
```env
FLASK_ENV=production
SECRET_KEY=<generated-secure-key>
JWT_SECRET_KEY=<generated-jwt-key>
DEBUG=False
DATABASE_URL=postgresql://smartdoc:password@localhost/smartdoc_db
```

### Step 3: Database Setup

**3.1 Create PostgreSQL Database**

```bash
sudo -u postgres psql
```

```sql
CREATE USER smartdoc WITH PASSWORD 'strong_password_here';
CREATE DATABASE smartdoc_db OWNER smartdoc;
GRANT ALL PRIVILEGES ON DATABASE smartdoc_db TO smartdoc;
\q
```

**3.2 Initialize Database**

```bash
# Switch back to smartdoc user
cd ~/document-classification

source venv/bin/activate

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

### Step 4: Gunicorn Configuration

**4.1 Create Gunicorn Config**

```bash
nano ~/document-classification/gunicorn.conf.py
```

```python
import multiprocessing

workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
bind = "127.0.0.1:8000"
backlog = 2048
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'
access_log = "/home/smartdoc/document-classification/logs/access.log"
error_logfile = "/home/smartdoc/document-classification/logs/error.log"
loglevel = "info"
```

**4.2 Create Gunicorn Startup Script**

```bash
nano ~/document-classification/start_gunicorn.sh
```

```bash
#!/bin/bash

NAME="smartdoc"
DIR="/home/smartdoc/document-classification"
VENV="$DIR/venv"
BIND="127.0.0.1:8000"
WORKERS=9
TIMEOUT=30

cd $DIR
source $VENV/bin/activate

exec $VENV/bin/gunicorn \
    --name $NAME \
    --workers $WORKERS \
    --worker-class sync \
    --bind $BIND \
    --timeout $TIMEOUT \
    --access-logfile - \
    --error-logfile - \
    --log-level info \
    "app:create_app()"
```

```bash
chmod +x ~/document-classification/start_gunicorn.sh
```

### Step 5: Supervisor Configuration

**5.1 Create Supervisor Config**

```bash
sudo nano /etc/supervisor/conf.d/smartdoc.conf
```

```ini
[program:smartdoc]
directory=/home/smartdoc/document-classification
command=/home/smartdoc/document-classification/start_gunicorn.sh
user=smartdoc
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/smartdoc/document-classification/logs/supervisor.log
stderr_logfile=/home/smartdoc/document-classification/logs/supervisor_error.log
environment=PATH="/home/smartdoc/document-classification/venv/bin",FLASK_ENV="production"

[group:smartdoc]
programs=smartdoc
```

**5.2 Start Service**

```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start smartdoc
sudo supervisorctl status smartdoc
```

### Step 6: Nginx Configuration

**6.1 Create Nginx Config**

```bash
sudo nano /etc/nginx/sites-available/smartdoc
```

```nginx
upstream smartdoc {
    server 127.0.0.1:8000;
    keepalive 32;
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    listen [::]:80;
    server_name yourdomain.com www.yourdomain.com;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL certificates
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # File upload size
    client_max_body_size 50M;
    
    # Logging
    access_log /var/log/nginx/smartdoc_access.log;
    error_log /var/log/nginx/smartdoc_error.log;
    
    # Static files
    location /static {
        alias /home/smartdoc/document-classification/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    # API and application
    location / {
        proxy_pass http://smartdoc;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_request_buffering off;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

**6.2 Enable Site**

```bash
sudo ln -s /etc/nginx/sites-available/smartdoc /etc/nginx/sites-enabled/smartdoc
sudo nginx -t
sudo systemctl restart nginx
```

### Step 7: SSL Certificate

**7.1 Get Let's Encrypt Certificate**

```bash
sudo certbot certonly --nginx -d yourdomain.com -d www.yourdomain.com

# Auto-renewal
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

### Step 8: Backups

**8.1 Create Backup Script**

```bash
sudo nano /home/smartdoc/backup.sh
```

```bash
#!/bin/bash

BACKUP_DIR="/home/smartdoc/backups"
DB_NAME="smartdoc_db"
DB_USER="smartdoc"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
PGPASSWORD='password' pg_dump -h localhost -U $DB_USER $DB_NAME | \
    gzip > $BACKUP_DIR/db_$TIMESTAMP.sql.gz

# Backup application files
tar -czf $BACKUP_DIR/app_$TIMESTAMP.tar.gz \
    /home/smartdoc/document-classification/data/uploads \
    /home/smartdoc/document-classification/instance

# Keep only last 30 days
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "Backup completed: $TIMESTAMP"
```

```bash
chmod +x /home/smartdoc/backup.sh
```

**8.2 Schedule with Crontab**

```bash
sudo crontab -e
```

```
# Daily backup at 2 AM
0 2 * * * /home/smartdoc/backup.sh
```

---

## Docker Deployment

### Step 1: Create Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create logs directory
RUN mkdir -p logs instance

# Run Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:create_app()"]
```

### Step 2: Docker Compose

```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: smartdoc
      POSTGRES_PASSWORD: ${DB_PASSWORD}
      POSTGRES_DB: smartdoc_db
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: always
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U smartdoc"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    restart: always
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      FLASK_ENV: production
      SECRET_KEY: ${SECRET_KEY}
      DATABASE_URL: postgresql://smartdoc:${DB_PASSWORD}@db:5432/smartdoc_db
      REDIS_URL: redis://redis:6379
    volumes:
      - ./data/uploads:/app/data/uploads
      - ./logs:/app/logs
      - ./instance:/app/instance
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - app
    restart: always

volumes:
  postgres_data:
```

### Step 3: Build and Deploy

```bash
# Build image
docker-compose build

# Start services
docker-compose up -d

# View logs
docker-compose logs -f app

# Stop services
docker-compose down
```

---

## AWS Deployment

### Step 1: EC2 Instance Setup

```bash
# Launch Ubuntu 20.04 t3.medium instance
# Security group: Allow 22 (SSH), 80 (HTTP), 443 (HTTPS)

# SSH into instance
ssh -i your-key.pem ec2-user@your-instance-ip
```

### Step 2: RDS Database

1. Create PostgreSQL RDS instance
2. Security group: Allow port 5432 from EC2
3. Set up database:

```bash
psql -h your-rds-endpoint.rds.amazonaws.com -U smartdoc -d smartdoc_db
```

### Step 3: S3 for File Storage

```bash
# Create S3 bucket
aws s3 mb s3://smartdoc-uploads --region us-east-1

# Set encryption and versioning
aws s3api put-bucket-encryption \
    --bucket smartdoc-uploads \
    --server-side-encryption-configuration '{"Rules": [{"ApplyServerSideEncryptionByDefault": {"SSEAlgorithm": "AES256"}}]}'
```

### Step 4: Deploy Application

```bash
# Follow Linux deployment steps above, but use RDS endpoint
# Update .env with RDS_ENDPOINT
```

### Step 5: CloudFront CDN

```bash
# Create CloudFront distribution
# Origin: ALB pointing to EC2 instance
# Cache behavior: /static -> cache 30 days
#                  / -> cache 0 (no cache)
```

---

## Monitoring & Maintenance

### Step 1: Logging Setup

**1.1 Centralized Logging**

```python
# config.py
import logging
from logging.handlers import RotatingFileHandler
import os

if not os.path.exists('logs'):
    os.mkdir('logs')

file_handler = RotatingFileHandler('logs/smartdoc.log', 
                                  maxBytes=10240000, 
                                  backupCount=10)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
```

**1.2 Log Rotation**

```bash
# /etc/logrotate.d/smartdoc
/home/smartdoc/document-classification/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 smartdoc smartdoc
    sharedscripts
    postrotate
        supervisorctl restart smartdoc > /dev/null
    endscript
}
```

### Step 2: Monitoring

**2.1 Health Check Endpoint**

```python
@app.route('/health')
def health_check():
    try:
        db.session.execute('SELECT 1')
        return {'status': 'healthy'}, 200
    except:
        return {'status': 'unhealthy'}, 500
```

**2.2 Metrics Collection**

```bash
# Install Prometheus client
pip install prometheus-client

# Monitor in code
from prometheus_client import Counter, Histogram

request_count = Counter('requests_total', 'Total requests')
request_duration = Histogram('request_duration_seconds', 'Request duration')

@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    request_count.inc()
    duration = time.time() - request.start_time
    request_duration.observe(duration)
    return response
```

### Step 3: Automated Alerts

```bash
# Monitor service status
sudo systemctl status smartdoc

# Set up email alerts
sudo nano /etc/supervisor/conf.d/smartdoc.conf
# Add: eventlisteners = watchdog
```

---

## Rollback Procedures

### Quick Rollback

```bash
# Stop current version
sudo supervisorctl stop smartdoc

# Restore from backup
cd /home/smartdoc/document-classification
git checkout previous-tag

# Restart service
sudo supervisorctl start smartdoc
```

### Database Rollback

```bash
# Restore database backup
PGPASSWORD='password' psql -h localhost -U smartdoc smartdoc_db < backup.sql

# Or migrate down
alembic downgrade -1
```

---

## Post-Deployment

- [ ] Verify application running
- [ ] Test file upload
- [ ] Test document classification
- [ ] Verify backups working
- [ ] Check logs for errors
- [ ] Monitor resource usage
- [ ] Update documentation
- [ ] Notify team of deployment

---

Last Updated: April 20, 2026
