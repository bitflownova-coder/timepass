"""
IndexedFile Model — tracks every local file scanned from the PC.
Files are NEVER moved or copied — only their metadata + text is stored here.
"""
from datetime import datetime
from app.models.user import db


class IndexedFile(db.Model):
    """Represents a file on disk that has been indexed."""
    __tablename__ = 'indexed_file'

    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)

    # Location on disk — original path, never changed
    file_path     = db.Column(db.String(1024), nullable=False)
    filename      = db.Column(db.String(255),  nullable=False, index=True)
    extension     = db.Column(db.String(20),   nullable=True,  index=True)
    folder_path   = db.Column(db.String(1024), nullable=True,  index=True)

    # File identity
    file_size     = db.Column(db.Integer,      nullable=True)
    file_hash     = db.Column(db.String(64),   nullable=True,  index=True)
    modified_at   = db.Column(db.DateTime,     nullable=True)   # mtime from OS
    indexed_at    = db.Column(db.DateTime,     default=datetime.utcnow)
    last_seen_at  = db.Column(db.DateTime,     default=datetime.utcnow)

    # Extracted content
    extracted_text = db.Column(db.Text, nullable=True)
    text_preview   = db.Column(db.String(500), nullable=True)
    page_count     = db.Column(db.Integer,     nullable=True)

    # Classification (auto-tagged)
    predicted_label   = db.Column(db.String(100), nullable=True, index=True)
    confidence_score  = db.Column(db.Float,        nullable=True)

    # Business-document attributes (mirrors Document model — for VirtualPath)
    client_name     = db.Column(db.String(255), nullable=True, index=True)
    doc_type        = db.Column(db.String(100), nullable=True, index=True)
    doc_year        = db.Column(db.String(10),  nullable=True, index=True)
    attributes_json = db.Column(db.Text, nullable=True)   # raw extractor output

    # Code-project attributes
    is_code      = db.Column(db.Boolean,      default=False, index=True)
    project_name = db.Column(db.String(255),  nullable=True, index=True)
    project_root = db.Column(db.String(1024), nullable=True)
    language     = db.Column(db.String(50),   nullable=True, index=True)

    # Background embedding flag
    is_embedded  = db.Column(db.Boolean,      default=False, index=True)

    # Status flags
    index_status  = db.Column(db.String(20),  default='indexed')  # indexed | error | skipped
    error_message = db.Column(db.String(500), nullable=True)
    is_deleted    = db.Column(db.Boolean,     default=False, index=True)  # file gone from disk

    # Unique: one record per (user, path)
    __table_args__ = (
        db.UniqueConstraint('user_id', 'file_path', name='uq_indexed_user_path'),
    )

    def to_dict(self):
        return {
            'id':               self.id,
            'file_path':        self.file_path,
            'filename':         self.filename,
            'extension':        self.extension,
            'folder_path':      self.folder_path,
            'file_size':        self.file_size,
            'modified_at':      self.modified_at.isoformat() if self.modified_at else None,
            'indexed_at':       self.indexed_at.isoformat()  if self.indexed_at  else None,
            'text_preview':     self.text_preview,
            'page_count':       self.page_count,
            'predicted_label':  self.predicted_label,
            'confidence_score': self.confidence_score,
            'client_name':      self.client_name,
            'doc_type':         self.doc_type,
            'doc_year':         self.doc_year,
            'is_code':          bool(self.is_code),
            'project_name':     self.project_name,
            'language':         self.language,
            'is_embedded':      bool(self.is_embedded),
            'index_status':     self.index_status,
        }


class FileOpen(db.Model):
    """Tracks every time a user opens / views a file — "Read Later" history."""
    __tablename__ = 'file_open'

    id             = db.Column(db.Integer, primary_key=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    indexed_file_id = db.Column(db.Integer, db.ForeignKey('indexed_file.id'), nullable=False, index=True)
    opened_at      = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    duration_secs  = db.Column(db.Integer,  nullable=True)   # optional: how long viewed

    file = db.relationship('IndexedFile', backref='opens', lazy='joined')


class WatchedFolder(db.Model):
    """Folders the user has asked the app to watch / index."""
    __tablename__ = 'watched_folder'

    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    folder_path = db.Column(db.String(1024), nullable=False)
    recursive   = db.Column(db.Boolean, default=True)
    added_at    = db.Column(db.DateTime, default=datetime.utcnow)
    last_scan_at = db.Column(db.DateTime, nullable=True)
    file_count  = db.Column(db.Integer,  default=0)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'folder_path', name='uq_watched_user_folder'),
    )
