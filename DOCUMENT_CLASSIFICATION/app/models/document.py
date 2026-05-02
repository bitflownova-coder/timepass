"""
Document Model - Database model for uploaded documents and metadata
"""
from datetime import datetime
from app.models.user import db


class Document(db.Model):
    """Document metadata model"""
    __tablename__ = 'document'

    __table_args__ = (
        db.UniqueConstraint('user_id', 'file_hash', name='uq_document_user_hash'),
    )
    
    id = db.Column(db.Integer, primary_key=True)
    
    # User ownership
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    
    # File information
    filename = db.Column(db.String(255), nullable=False)  # Encrypted/stored filename
    original_filename = db.Column(db.String(255), nullable=False)  # Display name
    file_path = db.Column(db.String(500), nullable=False)  # Physical path
    file_size = db.Column(db.Integer, nullable=False)  # Size in bytes
    file_hash = db.Column(db.String(256), nullable=False, index=True)  # SHA256 hash
    mime_type = db.Column(db.String(100), nullable=True)
    
    # Classification data
    predicted_label = db.Column(db.String(100), nullable=True)  # AI prediction (backward compat)
    confidence_score = db.Column(db.Float, nullable=True)  # 0.0 to 1.0
    suggested_folder = db.Column(db.String(255), nullable=True)  # Best matching folder
    user_folder = db.Column(db.String(255), nullable=True)  # Where user placed it (backward compat)

    # Knowledge model attributes (Phase 1 — VFS overhaul)
    doc_type = db.Column(db.String(100), nullable=True, index=True)   # Normalised document type (e.g. 'Invoices')
    client_name = db.Column(db.String(255), nullable=True, index=True) # Detected person/org name
    doc_year = db.Column(db.Integer, nullable=True, index=True)        # Year extracted from content or upload date
    entity_keywords = db.Column(db.String(500), nullable=True)         # spaCy persons/orgs (persisted)
    
    # Content data
    extracted_text = db.Column(db.Text, nullable=True)  # Full extracted text
    text_preview = db.Column(db.String(500), nullable=True)  # First 500 chars
    
    # Tagging
    tags = db.Column(db.String(500), nullable=True)  # Comma-separated tags
    
    # Security & Status
    is_encrypted = db.Column(db.Boolean, default=True)
    is_duplicate = db.Column(db.Boolean, default=False)
    duplicate_of = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=True)
    
    # Timestamps
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    processed_at = db.Column(db.DateTime, nullable=True)
    accessed_at = db.Column(db.DateTime, nullable=True)
    deleted_at = db.Column(db.DateTime, nullable=True)  # Soft delete
    
    # Relationships
    audit_logs = db.relationship('AuditLog', backref='document', lazy='dynamic', cascade='all, delete-orphan')
    feedback = db.relationship('Feedback', backref='document', lazy='dynamic', cascade='all, delete-orphan')
    file_metadata = db.relationship('FileMetadata', backref='document', uselist=False, cascade='all, delete-orphan')
    
    def is_active(self):
        """Check if document is not deleted"""
        return self.deleted_at is None
    
    def get_tags_list(self):
        """Parse tags string to list"""
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',')]
        return []
    
    def set_tags(self, tags_list):
        """Set tags from list"""
        if isinstance(tags_list, list):
            self.tags = ','.join(tags_list)
        else:
            self.tags = tags_list
    
    def to_dict(self, include_content=False):
        """Convert document to dictionary"""
        data = {
            'id': self.id,
            'filename': self.filename,
            'original_filename': self.original_filename,
            'file_size': self.file_size,
            'mime_type': self.mime_type,
            'user_folder': self.user_folder,
            'predicted_label': self.predicted_label,
            'confidence_score': self.confidence_score,
            'tags': self.get_tags_list(),
            'is_encrypted': self.is_encrypted,
            'is_duplicate': self.is_duplicate,
            'uploaded_at': self.uploaded_at.isoformat(),
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'accessed_at': self.accessed_at.isoformat() if self.accessed_at else None,
            # Knowledge model attributes
            'doc_type': self.doc_type,
            'client_name': self.client_name,
            'doc_year': self.doc_year,
            'entity_keywords': self.entity_keywords,
        }
        
        if include_content:
            data['text_preview'] = self.text_preview
            data['extracted_text'] = self.extracted_text
        
        return data
    
    def __repr__(self):
        return f'<Document {self.original_filename}>'


class FileMetadata(db.Model):
    """File metadata model for storing extracted document info"""
    __tablename__ = 'file_metadata'
    
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False, unique=True)
    
    # Document properties
    num_pages = db.Column(db.Integer, nullable=True)  # For PDFs
    author = db.Column(db.String(255), nullable=True)
    subject = db.Column(db.String(255), nullable=True)
    keywords = db.Column(db.String(500), nullable=True)
    
    # Dates from document
    creation_date = db.Column(db.DateTime, nullable=True)
    modification_date = db.Column(db.DateTime, nullable=True)
    
    # Text analysis
    language = db.Column(db.String(20), default='en', nullable=True)  # Detected language
    word_count = db.Column(db.Integer, nullable=True)
    character_count = db.Column(db.Integer, nullable=True)
    
    # OCR flag
    ocr_used = db.Column(db.Boolean, default=False)
    
    def to_dict(self):
        """Convert metadata to dictionary"""
        return {
            'num_pages': self.num_pages,
            'author': self.author,
            'subject': self.subject,
            'keywords': self.keywords,
            'language': self.language,
            'word_count': self.word_count,
            'character_count': self.character_count,
            'ocr_used': self.ocr_used,
        }
    
    def __repr__(self):
        return f'<FileMetadata document_id={self.document_id}>'
