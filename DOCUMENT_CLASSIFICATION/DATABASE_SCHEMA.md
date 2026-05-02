# Database Schema

## Overview

The application uses **SQLite** as the database with **SQLAlchemy** ORM for data management. Below is the complete database schema design.

## Entity Relationship Diagram

```
┌─────────────┐          ┌──────────────┐          ┌─────────────┐
│    User     │──────────│   Document   │──────────│  AuditLog   │
└─────────────┘ 1:N      └──────────────┘ 1:N      └─────────────┘
       │                        │
       │                        └─────────────────┐
       │                                          │
       │                        ┌──────────────┐  │
       └────────────────────────│  Feedback    │  │
                                └──────────────┘  │
                                                  ▼
                                        ┌──────────────────┐
                                        │   File_Metadata  │
                                        └──────────────────┘
```

## Tables

### 1. USER Table
Stores user account information.

```sql
CREATE TABLE "user" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    role VARCHAR(50) DEFAULT 'user',  -- 'admin' or 'user'
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    storage_limit INTEGER DEFAULT 5368709120  -- 5GB in bytes
);
```

**Columns:**
- `id` - Primary key, auto-increment
- `email` - Unique email address
- `password_hash` - Bcrypt hashed password (never store plain text)
- `full_name` - User's full name
- `role` - User role (admin/user) for RBAC
- `is_active` - Account activation status
- `created_at` - Account creation timestamp
- `updated_at` - Last update timestamp
- `last_login` - Last login timestamp for tracking
- `storage_limit` - Maximum storage allowed (5GB default)

---

### 2. DOCUMENT Table
Stores metadata about uploaded documents.

```sql
CREATE TABLE "document" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER NOT NULL,
    file_hash VARCHAR(256) UNIQUE NOT NULL,  -- SHA256 hash for duplicate detection
    mime_type VARCHAR(100),
    
    -- Classification data
    predicted_label VARCHAR(100),  -- AI predicted category
    confidence_score FLOAT,  -- 0.0 to 1.0
    suggested_folder VARCHAR(255),  -- Best matching folder
    user_folder VARCHAR(255),  -- Where user actually placed it
    
    -- Content data
    extracted_text TEXT,  -- Full extracted text from document
    text_preview VARCHAR(500),  -- First 500 chars preview
    
    -- Tagging
    tags VARCHAR(500),  -- Comma-separated tags: "invoice,bills,2024"
    
    -- Status
    is_encrypted BOOLEAN DEFAULT TRUE,
    encryption_key_hash VARCHAR(256),  -- Hash of encryption key
    is_duplicate BOOLEAN DEFAULT FALSE,
    duplicate_of INTEGER,  -- Reference to original if duplicate
    
    -- Timestamps
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processed_at TIMESTAMP,
    accessed_at TIMESTAMP,
    deleted_at TIMESTAMP,  -- Soft delete
    
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE,
    FOREIGN KEY (duplicate_of) REFERENCES document(id)
);
```

**Columns:**
- `id` - Primary key
- `user_id` - Foreign key to User table
- `filename` - Encrypted/stored filename
- `original_filename` - Original filename for display
- `file_path` - Physical path to encrypted file
- `file_size` - Size in bytes
- `file_hash` - SHA256 hash for duplicate detection
- `mime_type` - MIME type (application/pdf, etc.)
- `predicted_label` - AI classification result
- `confidence_score` - Prediction confidence (0.87 = 87%)
- `suggested_folder` - Best matching folder name
- `user_folder` - Actual folder user selected
- `extracted_text` - Full document text for searching
- `text_preview` - First 500 chars for UI preview
- `tags` - Multiple tags separated by commas
- `is_encrypted` - Encryption status
- `encryption_key_hash` - For key verification
- `is_duplicate` - Duplicate detection flag
- `duplicate_of` - Points to original document if duplicate
- `uploaded_at` - Upload timestamp
- `processed_at` - When classification was completed
- `accessed_at` - Last access timestamp
- `deleted_at` - Soft delete timestamp

---

### 3. FEEDBACK Table
Stores user corrections for improving the ML model.

```sql
CREATE TABLE "feedback" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    predicted_label VARCHAR(100),  -- What AI predicted
    corrected_label VARCHAR(100),  -- What user said was correct
    feedback_text TEXT,  -- Optional user comment
    is_useful BOOLEAN,  -- Thumbs up/down
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (document_id) REFERENCES document(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE CASCADE
);
```

**Columns:**
- `id` - Primary key
- `document_id` - Reference to document
- `user_id` - User who provided feedback
- `predicted_label` - Original AI prediction
- `corrected_label` - Correct category
- `feedback_text` - Optional comments
- `is_useful` - User feedback on prediction quality
- `created_at` - Timestamp

---

### 4. AUDIT_LOG Table
Comprehensive audit trail for compliance and security.

```sql
CREATE TABLE "audit_log" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action VARCHAR(100) NOT NULL,  -- 'upload', 'download', 'delete', 'access'
    resource_type VARCHAR(50),  -- 'document', 'folder', 'user'
    resource_id INTEGER,  -- ID of affected resource
    resource_name VARCHAR(255),  -- Name for logging
    ip_address VARCHAR(45),  -- IPv4 or IPv6
    user_agent TEXT,  -- Browser user agent
    status VARCHAR(50),  -- 'success', 'failed'
    error_message TEXT,  -- If failed
    details JSON,  -- Additional context
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES user(id) ON DELETE SET NULL
);
```

**Columns:**
- `id` - Primary key
- `user_id` - User performing action (null for system actions)
- `action` - Type of action performed
- `resource_type` - Type of resource (document, folder, user)
- `resource_id` - ID of affected resource
- `resource_name` - Name for easy identification
- `ip_address` - Client IP for security
- `user_agent` - Browser info
- `status` - Success or failure
- `error_message` - Error details if failed
- `details` - JSON with additional context
- `created_at` - When action occurred

---

### 5. FILE_METADATA Table
Stores extracted metadata from documents.

```sql
CREATE TABLE "file_metadata" (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id INTEGER NOT NULL UNIQUE,
    num_pages INTEGER,  -- For PDFs
    author VARCHAR(255),
    subject VARCHAR(255),
    keywords VARCHAR(500),
    creation_date TIMESTAMP,
    modification_date TIMESTAMP,
    language VARCHAR(20),  -- Detected language
    word_count INTEGER,
    character_count INTEGER,
    ocr_used BOOLEAN DEFAULT FALSE,  -- If OCR was used
    
    FOREIGN KEY (document_id) REFERENCES document(id) ON DELETE CASCADE
);
```

**Columns:**
- `id` - Primary key
- `document_id` - Reference to document
- `num_pages` - Number of pages (for PDFs)
- `author` - Document author
- `subject` - Document subject
- `keywords` - Extracted keywords
- `creation_date` - Document creation date
- `modification_date` - Last modification date
- `language` - Detected document language
- `word_count` - Total words
- `character_count` - Total characters
- `ocr_used` - Whether OCR was applied

---

## Indexes for Performance

```sql
-- User lookups
CREATE INDEX idx_user_email ON user(email);
CREATE INDEX idx_user_role ON user(role);

-- Document lookups
CREATE INDEX idx_document_user_id ON document(user_id);
CREATE INDEX idx_document_file_hash ON document(file_hash);
CREATE INDEX idx_document_uploaded_at ON document(uploaded_at);
CREATE INDEX idx_document_user_folder ON document(user_folder);

-- Feedback lookups
CREATE INDEX idx_feedback_document_id ON feedback(document_id);
CREATE INDEX idx_feedback_user_id ON feedback(user_id);

-- Audit log lookups
CREATE INDEX idx_audit_log_user_id ON audit_log(user_id);
CREATE INDEX idx_audit_log_created_at ON audit_log(created_at);
CREATE INDEX idx_audit_log_action ON audit_log(action);

-- Search optimization
CREATE FULLTEXT INDEX idx_document_text ON document(extracted_text);
```

---

## Sample Queries

### 1. Get all documents for a user
```sql
SELECT * FROM document 
WHERE user_id = 1 
ORDER BY uploaded_at DESC;
```

### 2. Find duplicate documents
```sql
SELECT * FROM document 
WHERE file_hash IN (
    SELECT file_hash FROM document GROUP BY file_hash HAVING COUNT(*) > 1
);
```

### 3. User audit trail
```sql
SELECT * FROM audit_log 
WHERE user_id = 1 
ORDER BY created_at DESC 
LIMIT 100;
```

### 4. Search documents
```sql
SELECT * FROM document 
WHERE user_id = 1 
AND extracted_text LIKE '%invoice%' 
AND uploaded_at > '2024-01-01';
```

### 5. Model performance metrics
```sql
SELECT 
    predicted_label,
    AVG(confidence_score) as avg_confidence,
    COUNT(*) as count
FROM document 
GROUP BY predicted_label;
```

---

## Data Types

| Type | SQLite | Python | Example |
|------|--------|--------|---------|
| Integer | INTEGER | int | 123 |
| Float | REAL | float | 0.87 |
| String | VARCHAR | str | "Resume" |
| Text | TEXT | str | Long document text |
| Boolean | BOOLEAN | bool | True/False |
| Timestamp | TIMESTAMP | datetime | 2024-01-15 10:30:00 |
| JSON | JSON | dict | {"key": "value"} |

---

## Migrations

Database schema changes should be managed with **Alembic** migrations:

```bash
# Create new migration
alembic revision --autogenerate -m "Add new column"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

---

## Backup & Recovery

### Backup
```bash
# SQLite backup
sqlite3 app.db ".backup 'backup.db'"

# Or using Python
import shutil
shutil.copy('app.db', 'backup.db')
```

### Recovery
```bash
sqlite3 backup.db ".restore app.db"
```

---

## Encryption Considerations

- Passwords stored as bcrypt hashes (one-way)
- Files encrypted with AES-256
- Encryption keys derived from user password
- Never store keys in database - derive from authentication

---

## GDPR Compliance

- Implement right-to-deletion (cascade deletes)
- Implement data export functionality
- Keep audit logs for compliance
- Encrypt sensitive data at rest
- Use HTTPS for data in transit

---

Last Updated: April 20, 2026
