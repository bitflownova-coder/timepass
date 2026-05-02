# Security Implementation Guide

Comprehensive security features for SmartDoc AI protecting user data, documents, and system integrity.

## Table of Contents

1. [Authentication & Authorization](#authentication--authorization)
2. [Data Encryption](#data-encryption)
3. [API Security](#api-security)
4. [Input Validation](#input-validation)
5. [Access Control](#access-control)
6. [Audit Logging](#audit-logging)
7. [Infrastructure Security](#infrastructure-security)
8. [Best Practices](#best-practices)
9. [Compliance](#compliance)

---

## Authentication & Authorization

### 1. User Authentication

#### Password Security

```python
# Password Hashing with bcrypt
from flask_bcrypt import Bcrypt

bcrypt = Bcrypt()

# Hash password on registration
password_hash = bcrypt.generate_password_hash('user_password')

# Verify password on login
is_correct = bcrypt.check_password_hash(password_hash, provided_password)
```

**Requirements:**
- Minimum 8 characters
- Mix of uppercase, lowercase, numbers, symbols
- Never stored in plain text
- Hashed with bcrypt (salt + iterations)

#### JWT Tokens

```python
import jwt
from datetime import datetime, timedelta

# Generate token
def create_token(user_id, expires_in=86400):
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + timedelta(seconds=expires_in),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, SECRET_KEY, algorithm='HS256')

# Verify token
@jwt.required
def protected_route():
    current_user = get_jwt_identity()
    return f"Hello {current_user}"
```

**Token Specifications:**
- Algorithm: HS256
- Secret: 32+ characters (highly random)
- Expiration: 24 hours default
- Refresh: Optional refresh token for longer sessions
- Revocation: Tokens stored in blacklist on logout

### 2. Authorization (RBAC)

```python
# Roles and Permissions
ROLES = {
    'admin': ['read', 'create', 'update', 'delete', 'manage_users'],
    'user': ['read', 'create', 'update', 'delete'],  # Own files only
    'viewer': ['read']  # Read-only access
}

# Decorator for role checking
from functools import wraps

def role_required(required_role):
    def decorator(fn):
        @wraps(fn)
        def decorated_function(*args, **kwargs):
            current_user = get_current_user()
            if current_user.role != required_role:
                return {'error': 'Insufficient permissions'}, 403
            return fn(*args, **kwargs)
        return decorated_function
    return decorator

# Usage
@app.route('/api/admin/users')
@role_required('admin')
def list_all_users():
    # Only admins can access
    pass

@app.route('/api/documents/<doc_id>')
@jwt_required
def get_document(doc_id):
    current_user = get_current_user()
    document = Document.query.get(doc_id)
    
    # Ensure user owns document
    if document.user_id != current_user.id:
        return {'error': 'Unauthorized'}, 403
    
    return document.to_dict()
```

---

## Data Encryption

### 1. File Encryption (AES-256)

```python
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
import os
import base64

class FileEncryption:
    def __init__(self, password, salt=None):
        if salt is None:
            salt = os.urandom(16)
        
        # Derive key from password
        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        self.cipher = Fernet(key)
        self.salt = salt
    
    def encrypt_file(self, input_path, output_path):
        with open(input_path, 'rb') as f:
            data = f.read()
        
        encrypted_data = self.cipher.encrypt(data)
        
        with open(output_path, 'wb') as f:
            f.write(self.salt + encrypted_data)
    
    def decrypt_file(self, encrypted_path, output_path):
        with open(encrypted_path, 'rb') as f:
            salt = f.read(16)
            encrypted_data = f.read()
        
        decrypted_data = self.cipher.decrypt(encrypted_data)
        
        with open(output_path, 'wb') as f:
            f.write(decrypted_data)
```

**Usage:**
```python
# Encryption
encryptor = FileEncryption(user_password)
encryptor.encrypt_file('original.pdf', 'encrypted.bin')

# Decryption
decryptor = FileEncryption(user_password, salt=stored_salt)
decryptor.decrypt_file('encrypted.bin', 'decrypted.pdf')
```

### 2. Database Encryption

```python
from sqlalchemy import Column, String
from sqlalchemy.types import TypeDecorator
from cryptography.fernet import Fernet

class EncryptedString(TypeDecorator):
    impl = String
    
    def __init__(self, key):
        super().__init__()
        self.cipher = Fernet(key)
    
    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        return self.cipher.encrypt(value.encode()).decode()
    
    def process_result_value(self, value, dialect):
        if value is None:
            return value
        return self.cipher.decrypt(value.encode()).decode()

# Usage in model
class Document(db.Model):
    id = Column(Integer, primary_key=True)
    encrypted_filename = Column(EncryptedString(ENCRYPTION_KEY))
```

### 3. Password Hashing

```python
import bcrypt

# Register
password = "user_password123"
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt(rounds=12))
# Store hashed in database

# Login
provided_password = "user_password123"
if bcrypt.checkpw(provided_password.encode('utf-8'), hashed):
    # Password correct
    pass
```

---

## API Security

### 1. Rate Limiting

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route('/api/upload', methods=['POST'])
@limiter.limit("5 per hour")  # 5 uploads per hour
def upload_file():
    pass

@app.route('/api/auth/login', methods=['POST'])
@limiter.limit("10 per hour")  # 10 login attempts per hour
def login():
    pass
```

### 2. CORS (Cross-Origin Resource Sharing)

```python
from flask_cors import CORS

# Restrict to specific origins
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://yourdomain.com", "https://app.yourdomain.com"],
        "methods": ["GET", "POST", "PATCH", "DELETE"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True,
        "max_age": 3600
    }
})
```

### 3. HTTPS/SSL

```python
# Force HTTPS
@app.before_request
def enforce_https():
    if not request.is_secure:
        url = request.url.replace('http://', 'https://', 1)
        return redirect(url, code=301)

# Security headers
@app.after_request
def set_security_headers(response):
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response
```

### 4. API Key Management

```python
# For server-to-server communication
@app.route('/api/protected')
def protected_route():
    api_key = request.headers.get('X-API-Key')
    
    if not api_key or not verify_api_key(api_key):
        return {'error': 'Invalid API key'}, 401
    
    return {'data': 'sensitive'}

def verify_api_key(api_key):
    # Check against stored keys
    key = APIKey.query.filter_by(key=api_key).first()
    return key is not None and key.is_active
```

---

## Input Validation

### 1. File Upload Validation

```python
import magic  # python-magic

def validate_file_upload(file):
    # Check file size
    max_size = 50 * 1024 * 1024  # 50 MB
    if len(file.read()) > max_size:
        return False, "File exceeds 50MB limit"
    
    file.seek(0)
    
    # Check file type by magic bytes
    mime = magic.Magic(mime=True)
    file_type = mime.from_buffer(file.read())
    
    allowed_types = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'image/jpeg']
    
    if file_type not in allowed_types:
        return False, "File type not allowed"
    
    file.seek(0)
    return True, "Valid"

# Usage
@app.route('/api/upload', methods=['POST'])
@jwt_required
def upload_file():
    file = request.files.get('file')
    is_valid, message = validate_file_upload(file)
    
    if not is_valid:
        return {'error': message}, 400
    
    # Process file
    pass
```

### 2. Input Sanitization

```python
from bleach import clean
import html

def sanitize_input(user_input, allowed_tags=None):
    if allowed_tags is None:
        allowed_tags = []
    
    # Remove HTML tags
    sanitized = clean(user_input, tags=allowed_tags, strip=True)
    
    # Escape special characters
    sanitized = html.escape(sanitized)
    
    return sanitized

# Usage
@app.route('/api/search')
@jwt_required
def search():
    query = request.args.get('q')
    clean_query = sanitize_input(query)
    
    # Use clean_query in database query
    pass
```

### 3. SQL Injection Prevention

```python
# WRONG - Vulnerable to SQL injection
query = f"SELECT * FROM documents WHERE title = '{user_input}'"

# CORRECT - Using parameterized queries
from sqlalchemy import text

query = text("SELECT * FROM documents WHERE title = :title")
results = db.session.execute(query, {"title": user_input})

# Or using ORM (safer)
results = Document.query.filter_by(title=user_input).all()
```

---

## Access Control

### 1. Resource-Level Access Control

```python
def check_document_access(user_id, document_id):
    """Verify user can access document"""
    document = Document.query.get(document_id)
    
    if not document:
        return False
    
    # Check ownership
    if document.user_id != user_id:
        # Check if shared with user
        if not is_document_shared(document_id, user_id):
            return False
    
    return True

@app.route('/api/documents/<doc_id>')
@jwt_required
def get_document(doc_id):
    current_user = get_jwt_identity()
    
    if not check_document_access(current_user, doc_id):
        return {'error': 'Unauthorized'}, 403
    
    document = Document.query.get(doc_id)
    return document.to_dict()
```

### 2. Folder-Level Access Control

```python
def can_access_folder(user_id, folder_name):
    """Verify user can access folder"""
    folder = Folder.query.filter_by(
        user_id=user_id,
        name=folder_name
    ).first()
    
    return folder is not None

# Prevent path traversal
def validate_folder_path(user_id, path):
    """Prevent ../ attacks"""
    if '..' in path or path.startswith('/'):
        return False
    
    # Verify user owns folder
    return can_access_folder(user_id, path)
```

---

## Audit Logging

### 1. Comprehensive Audit Trail

```python
from datetime import datetime

class AuditLog(db.Model):
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('user.id'))
    action = Column(String(100))  # 'upload', 'download', 'delete'
    resource_type = Column(String(50))  # 'document', 'folder'
    resource_id = Column(Integer)
    resource_name = Column(String(255))
    ip_address = Column(String(45))
    user_agent = Column(String(255))
    status = Column(String(50))  # 'success', 'failed'
    error_message = Column(String(255))
    timestamp = Column(DateTime, default=datetime.utcnow)

def log_action(user_id, action, resource_type, resource_id, 
               resource_name, status='success', error=None):
    """Log user action"""
    log_entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        resource_name=resource_name,
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent'),
        status=status,
        error_message=error
    )
    db.session.add(log_entry)
    db.session.commit()

# Usage
@app.route('/api/documents/<doc_id>/download')
@jwt_required
def download_document(doc_id):
    try:
        current_user = get_jwt_identity()
        document = Document.query.get(doc_id)
        
        log_action(
            user_id=current_user,
            action='download',
            resource_type='document',
            resource_id=doc_id,
            resource_name=document.filename,
            status='success'
        )
        
        return send_file(document.file_path)
    
    except Exception as e:
        log_action(
            user_id=current_user,
            action='download',
            resource_type='document',
            resource_id=doc_id,
            resource_name='unknown',
            status='failed',
            error=str(e)
        )
        return {'error': 'Download failed'}, 500
```

### 2. Audit Log Queries

```python
# Get user activity
def get_user_audit_logs(user_id, limit=100):
    return AuditLog.query.filter_by(user_id=user_id)\
        .order_by(AuditLog.timestamp.desc())\
        .limit(limit).all()

# Get suspicious activity
def detect_suspicious_activity():
    """Find suspicious patterns"""
    # Multiple failed logins
    failed_logins = AuditLog.query.filter_by(
        action='login',
        status='failed'
    ).filter(
        AuditLog.timestamp >= datetime.utcnow() - timedelta(hours=1)
    ).group_by(AuditLog.user_id)\
        .having(func.count() > 5).all()
    
    return failed_logins
```

---

## Infrastructure Security

### 1. Environment Variables

```bash
# .env (NEVER commit)
SECRET_KEY=your-very-secure-random-key-here
JWT_SECRET_KEY=your-jwt-secret-key
DATABASE_URL=sqlite:///app.db
ENCRYPTION_KEY=your-encryption-key
TESSERACT_PATH=/usr/bin/tesseract
FLASK_ENV=production
DEBUG=False
```

### 2. Secrets Management

```python
# Using python-dotenv
from dotenv import load_dotenv
import os

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY')
JWT_SECRET = os.getenv('JWT_SECRET_KEY')

# Don't hardcode secrets!
# Use environment variables or secret management services
```

### 3. Dependency Management

```bash
# Keep dependencies updated
pip check  # Find incompatible packages
pip list --outdated  # Check for updates

# Use specific versions in requirements.txt
Flask==2.3.2
SQLAlchemy==2.0.19
cryptography==41.0.3

# Regular security audits
pip-audit  # Check for known vulnerabilities
```

### 4. Backup Security

```bash
# Encrypt backups
openssl enc -aes-256-cbc -in app.db -out app.db.enc -k password

# Decrypt backup
openssl enc -d -aes-256-cbc -in app.db.enc -out app.db -k password

# Store backups securely
# - Separate server/location
# - Encrypted storage
# - Access restricted
# - Regular restore testing
```

---

## Best Practices

### 1. Principle of Least Privilege

```python
# Give users minimum necessary permissions
class User(db.Model):
    role = Column(String(20), default='viewer')  # Most restrictive by default

# Only admin users can delete all documents
@admin_required
def admin_delete_document(doc_id):
    pass

# Regular users can only access their own
@jwt_required
def user_delete_own_document(doc_id):
    current_user = get_current_user()
    document = Document.query.get(doc_id)
    
    if document.user_id != current_user.id:
        return {'error': 'Unauthorized'}, 403
    
    db.session.delete(document)
    db.session.commit()
```

### 2. Defense in Depth

```
Network Layer
    ↓ Firewall rules
    ↓ DDoS protection
    
Transport Layer
    ↓ HTTPS/TLS
    ↓ Certificate pinning
    
Application Layer
    ↓ Authentication
    ↓ Authorization
    ↓ Input validation
    ↓ Rate limiting
    
Data Layer
    ↓ Encryption at rest
    ↓ Encryption in transit
    ↓ Access control
    ↓ Audit logging
```

### 3. Secure Configuration

```python
# Development
DEBUG = False
TESTING = False

# Security headers
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Strict'

# Password requirements
PASSWORD_MIN_LENGTH = 8
PASSWORD_REQUIRE_UPPERCASE = True
PASSWORD_REQUIRE_DIGITS = True
PASSWORD_REQUIRE_SPECIAL = True

# Session timeout
PERMANENT_SESSION_LIFETIME = 3600  # 1 hour

# Token expiration
JWT_ACCESS_TOKEN_EXPIRES = 86400  # 1 day
JWT_REFRESH_TOKEN_EXPIRES = 2592000  # 30 days
```

---

## Compliance

### 1. GDPR Compliance

```python
# Right to access
@app.route('/api/user/data')
@jwt_required
def export_user_data():
    """User can export all their data"""
    current_user = get_current_user()
    
    data = {
        'user': current_user.to_dict(),
        'documents': [d.to_dict() for d in current_user.documents],
        'access_logs': [l.to_dict() for l in current_user.audit_logs]
    }
    
    return jsonify(data)

# Right to deletion
@app.route('/api/user/delete', methods=['DELETE'])
@jwt_required
def delete_user_account():
    """User can delete their account"""
    current_user = get_current_user()
    
    # Delete all user data
    Document.query.filter_by(user_id=current_user.id).delete()
    AuditLog.query.filter_by(user_id=current_user.id).delete()
    db.session.delete(current_user)
    db.session.commit()
    
    return {'message': 'Account deleted'}, 200
```

### 2. Data Retention Policy

```python
# Automatically delete old audit logs (after 1 year)
AUDIT_LOG_RETENTION_DAYS = 365

# Soft delete documents (not immediately removed)
class Document(db.Model):
    deleted_at = Column(DateTime, nullable=True)

# Only show active documents
@app.route('/api/documents')
@jwt_required
def list_documents():
    current_user = get_current_user()
    
    documents = Document.query.filter_by(
        user_id=current_user.id,
        deleted_at=None
    ).all()
    
    return jsonify([d.to_dict() for d in documents])
```

### 3. Privacy by Design

- Encrypt personal data
- Minimize data collection
- Regular security audits
- Privacy policy documentation
- User consent management

---

## Incident Response

### 1. Breach Detection

```python
# Monitor suspicious activity
@app.after_request
def monitor_activity(response):
    # Log all requests
    if response.status_code >= 400:
        logger.warning(f"Error: {request.path} - {response.status_code}")
    
    return response

# Alert on suspicious patterns
def check_suspicious_patterns():
    # Multiple failed logins
    # Unusual access patterns
    # Large data downloads
    # Admin actions
    pass
```

### 2. Breach Mitigation

```python
# Immediately revoke compromised tokens
def revoke_user_tokens(user_id):
    """Invalidate all tokens for user"""
    user = User.query.get(user_id)
    user.token_version += 1  # Invalidates old tokens
    db.session.commit()

# Force password reset
def force_password_reset(user_id):
    """Require user to reset password"""
    user = User.query.get(user_id)
    user.password_reset_required = True
    db.session.commit()
```

---

## Security Checklist

- [ ] All passwords hashed with bcrypt
- [ ] JWT tokens implemented with expiration
- [ ] RBAC configured for all roles
- [ ] File encryption (AES-256) enabled
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention (parameterized queries)
- [ ] CORS properly configured
- [ ] Rate limiting enabled
- [ ] HTTPS/SSL enforced
- [ ] Security headers added
- [ ] Audit logging comprehensive
- [ ] Backups encrypted and tested
- [ ] Dependencies up-to-date
- [ ] No hardcoded secrets
- [ ] Environment variables secured
- [ ] Error messages don't leak info
- [ ] Sensitive logs protected
- [ ] Regular security audits scheduled
- [ ] Incident response plan documented
- [ ] Privacy policy and terms updated

---

Last Updated: April 20, 2026
