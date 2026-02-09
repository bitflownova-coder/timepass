"""
Database Models and ORM Setup using SQLAlchemy
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, sessionmaker, relationship, Session
from sqlalchemy.pool import StaticPool
from pathlib import Path

Base = declarative_base()


# ============== TIME TRACKER MODELS ==============

class Project(Base):
    """Project for time tracking"""
    __tablename__ = 'projects'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    color = Column(String(7), default="#6366f1")
    hourly_rate = Column(Float, default=0.0)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    client = relationship("Client", back_populates="projects")
    time_entries = relationship("TimeEntry", back_populates="project", cascade="all, delete-orphan")
    

class TimeEntry(Base):
    """Time tracking entry"""
    __tablename__ = 'time_entries'
    
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=True)
    description = Column(Text)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, default=0)
    is_manual = Column(Boolean, default=False)
    tags = Column(JSON, default=list)  # List of tag strings
    billable = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    project = relationship("Project", back_populates="time_entries")


# ============== QUICK NOTES MODELS ==============

class NoteFolder(Base):
    """Folder for organizing notes"""
    __tablename__ = 'note_folders'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    color = Column(String(7), default="#6366f1")
    icon = Column(String(50), default="folder")
    parent_id = Column(Integer, ForeignKey('note_folders.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    notes = relationship("QuickNote", back_populates="folder", cascade="all, delete-orphan")
    children = relationship("NoteFolder", backref="parent", remote_side=[id])


class QuickNote(Base):
    """Quick note entry"""
    __tablename__ = 'quick_notes'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    content = Column(Text, default="")
    folder_id = Column(Integer, ForeignKey('note_folders.id'), nullable=True)
    is_pinned = Column(Boolean, default=False)
    color = Column(String(7), nullable=True)
    tags = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    folder = relationship("NoteFolder", back_populates="notes")


# ============== CODE SNIPPETS MODELS ==============

class SnippetCategory(Base):
    """Category for organizing snippets"""
    __tablename__ = 'snippet_categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    color = Column(String(7), default="#10b981")
    icon = Column(String(50), default="code")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    snippets = relationship("CodeSnippet", back_populates="category", cascade="all, delete-orphan")


class CodeSnippet(Base):
    """Code snippet entry"""
    __tablename__ = 'code_snippets'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    code = Column(Text, nullable=False)
    language = Column(String(50), default="plaintext")
    category_id = Column(Integer, ForeignKey('snippet_categories.id'), nullable=True)
    tags = Column(JSON, default=list)
    variables = Column(JSON, default=list)  # Placeholders like ${className}
    usage_count = Column(Integer, default=0)
    is_favorite = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    category = relationship("SnippetCategory", back_populates="snippets")


# ============== API TESTER MODELS ==============

class ApiCollection(Base):
    """Collection of API requests"""
    __tablename__ = 'api_collections'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    base_url = Column(String(500))
    auth_type = Column(String(50))  # bearer, basic, api_key, none
    auth_data = Column(JSON)
    variables = Column(JSON, default=dict)  # Environment variables
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    requests = relationship("ApiRequest", back_populates="collection", cascade="all, delete-orphan")


class ApiRequest(Base):
    """Saved API request"""
    __tablename__ = 'api_requests'
    
    id = Column(Integer, primary_key=True)
    collection_id = Column(Integer, ForeignKey('api_collections.id'), nullable=True)
    name = Column(String(200), nullable=False)
    method = Column(String(10), default="GET")
    url = Column(String(2000), nullable=False)
    headers = Column(JSON, default=dict)
    params = Column(JSON, default=dict)
    body_type = Column(String(20))  # json, form, raw, none
    body = Column(Text)
    auth_override = Column(JSON)  # Override collection auth
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    collection = relationship("ApiCollection", back_populates="requests")
    history = relationship("ApiHistory", back_populates="request", cascade="all, delete-orphan")


class ApiHistory(Base):
    """API request history"""
    __tablename__ = 'api_history'
    
    id = Column(Integer, primary_key=True)
    request_id = Column(Integer, ForeignKey('api_requests.id'), nullable=True)
    method = Column(String(10))
    url = Column(String(2000))
    status_code = Column(Integer)
    response_time_ms = Column(Integer)
    response_size_bytes = Column(Integer)
    response_headers = Column(JSON)
    response_body = Column(Text)
    error_message = Column(Text)
    executed_at = Column(DateTime, default=datetime.utcnow)
    
    request = relationship("ApiRequest", back_populates="history")


# ============== FINANCE MODELS ==============

class Client(Base):
    """Client for finance tracking"""
    __tablename__ = 'clients'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    email = Column(String(200))
    phone = Column(String(50))
    company = Column(String(200))
    address = Column(Text)
    gst_number = Column(String(50))
    pan_number = Column(String(20))
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    projects = relationship("Project", back_populates="client")
    invoices = relationship("Invoice", back_populates="client", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="client", cascade="all, delete-orphan")


class Invoice(Base):
    """Invoice for billing"""
    __tablename__ = 'invoices'
    
    id = Column(Integer, primary_key=True)
    invoice_number = Column(String(50), unique=True, nullable=False)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    issue_date = Column(DateTime, nullable=False)
    due_date = Column(DateTime)
    subtotal = Column(Float, default=0.0)
    tax_rate = Column(Float, default=18.0)  # GST %
    tax_amount = Column(Float, default=0.0)
    total = Column(Float, default=0.0)
    status = Column(String(20), default="draft")  # draft, sent, paid, overdue, cancelled
    notes = Column(Text)
    items = Column(JSON, default=list)  # List of line items
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    client = relationship("Client", back_populates="invoices")


class Payment(Base):
    """Payment record"""
    __tablename__ = 'payments'
    
    id = Column(Integer, primary_key=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=True)
    invoice_id = Column(Integer, ForeignKey('invoices.id'), nullable=True)
    amount = Column(Float, nullable=False)
    payment_date = Column(DateTime, nullable=False)
    payment_method = Column(String(50))  # bank_transfer, cash, upi, cheque
    reference_number = Column(String(100))
    notes = Column(Text)
    category = Column(String(100), default="Income")
    is_income = Column(Boolean, default=True)  # True = income, False = expense
    created_at = Column(DateTime, default=datetime.utcnow)
    
    client = relationship("Client", back_populates="payments")


# ============== CRAWLER MODELS ==============

class CrawlJob(Base):
    """Website crawl job"""
    __tablename__ = 'crawl_jobs'
    
    id = Column(Integer, primary_key=True)
    crawl_id = Column(String(50), unique=True, nullable=False)
    start_url = Column(String(2000), nullable=False)
    domain = Column(String(500))
    status = Column(String(20), default="pending")  # pending, running, paused, completed, failed
    config = Column(JSON, default=dict)
    pages_crawled = Column(Integer, default=0)
    pages_failed = Column(Integer, default=0)
    total_size_bytes = Column(Integer, default=0)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    error_message = Column(Text)
    output_path = Column(String(1000))
    created_at = Column(DateTime, default=datetime.utcnow)


class CrawledPage(Base):
    """Crawled page record"""
    __tablename__ = 'crawled_pages'
    
    id = Column(Integer, primary_key=True)
    crawl_job_id = Column(Integer, ForeignKey('crawl_jobs.id'), nullable=False)
    url = Column(String(2000), nullable=False)
    title = Column(String(500))
    depth = Column(Integer, default=0)
    status_code = Column(Integer)
    content_type = Column(String(100))
    content_length = Column(Integer)
    content_path = Column(String(1000))  # Path to saved content file
    crawled_at = Column(DateTime, default=datetime.utcnow)
    error_message = Column(Text)


# ============== UTILITY MODELS ==============

class PasswordHistory(Base):
    """Generated password history"""
    __tablename__ = 'password_history'
    
    id = Column(Integer, primary_key=True)
    password = Column(String(500), nullable=False)
    length = Column(Integer)
    type = Column(String(20))  # random, passphrase, pronounceable
    strength = Column(String(20))  # weak, medium, strong, very_strong
    label = Column(String(100))
    created_at = Column(DateTime, default=datetime.utcnow)


class SavedColor(Base):
    """Saved color palette"""
    __tablename__ = 'saved_colors'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100))
    hex_value = Column(String(9))  # #RRGGBB or #RRGGBBAA
    category = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow)


class EnvironmentProfile(Base):
    """Environment variable profile"""
    __tablename__ = 'environment_profiles'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    project_path = Column(String(1000))
    variables = Column(JSON, default=dict)  # Key-value pairs
    is_active = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============== DATABASE MANAGER ==============

class Database:
    """Database connection manager"""
    
    _instance = None
    
    def __new__(cls, db_path: Optional[str] = None):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize(db_path)
        return cls._instance
    
    def _initialize(self, db_path: Optional[str]):
        """Initialize database connection"""
        from .config import config
        
        if db_path is None:
            db_path = str(config.database_path)
        
        self.engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
            echo=False
        )
        
        # Create all tables
        Base.metadata.create_all(self.engine)
        
        self.SessionLocal = sessionmaker(bind=self.engine, autocommit=False, autoflush=False)
    
    def get_session(self) -> Session:
        """Get a new database session"""
        return self.SessionLocal()
    
    def close(self):
        """Close database connection"""
        self.engine.dispose()


# Convenience functions
def get_db() -> Database:
    """Get the database singleton"""
    return Database()


def get_session() -> Session:
    """Get a new database session"""
    return get_db().get_session()
