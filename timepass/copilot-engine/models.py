"""
Database models for Copilot Engine
"""
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey, JSON, Boolean, Index
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


def _utcnow():
    return datetime.now(timezone.utc)


class Workspace(Base):
    """Tracked workspace/project"""
    __tablename__ = "workspaces"
    __table_args__ = (
        Index('idx_workspace_path', 'path'),
        Index('idx_workspace_last_active', 'last_active'),
    )
    
    id = Column(Integer, primary_key=True)
    path = Column(String(500), unique=True, nullable=False)
    name = Column(String(100))
    language = Column(String(50))  # Primary language
    framework = Column(String(50))  # Detected framework
    last_active = Column(DateTime, default=_utcnow)
    created_at = Column(DateTime, default=_utcnow)
    config = Column(JSON, default=dict)  # Workspace-specific config
    
    # Relationships
    errors = relationship("ErrorLog", back_populates="workspace", cascade="all, delete-orphan")
    fixes = relationship("FixPattern", back_populates="workspace", cascade="all, delete-orphan")
    files = relationship("FileIndex", back_populates="workspace", cascade="all, delete-orphan")


class ErrorLog(Base):
    """Logged errors for pattern learning"""
    __tablename__ = "error_logs"
    __table_args__ = (
        Index('idx_error_workspace', 'workspace_id'),
        Index('idx_error_type', 'error_type'),
        Index('idx_error_timestamp', 'timestamp'),
        Index('idx_error_type_workspace', 'error_type', 'workspace_id'),
    )
    
    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))
    error_type = Column(String(100))  # e.g., "TypeError", "ImportError"
    message = Column(Text)
    stack_trace = Column(Text)
    file_path = Column(String(500))
    line_number = Column(Integer)
    context = Column(Text)  # Code around the error
    resolved = Column(Boolean, default=False)
    resolution = Column(Text)  # How it was fixed
    timestamp = Column(DateTime, default=_utcnow)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="errors")


class FixPattern(Base):
    """Stored fix patterns for similar errors"""
    __tablename__ = "fix_patterns"
    __table_args__ = (
        Index('idx_fix_error_type', 'error_type'),
        Index('idx_fix_signature', 'error_signature'),
        Index('idx_fix_success', 'success_count'),
    )
    
    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))
    error_signature = Column(String(500))  # Normalized error pattern
    error_type = Column(String(100))
    description = Column(Text)
    fix_description = Column(Text)
    files_changed = Column(JSON)  # List of files involved
    code_before = Column(Text)
    code_after = Column(Text)
    success_count = Column(Integer, default=1)
    last_used = Column(DateTime, default=_utcnow)
    created_at = Column(DateTime, default=_utcnow)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="fixes")


class FileIndex(Base):
    """Indexed files for quick lookup"""
    __tablename__ = "file_index"
    __table_args__ = (
        Index('idx_file_workspace', 'workspace_id'),
        Index('idx_file_path', 'path'),
        Index('idx_file_language', 'language'),
    )
    
    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))
    path = Column(String(500))
    relative_path = Column(String(300))
    language = Column(String(50))
    size = Column(Integer)
    last_modified = Column(DateTime)
    imports = Column(JSON)  # Extracted imports
    exports = Column(JSON)  # Exported symbols
    functions = Column(JSON)  # Function signatures
    classes = Column(JSON)  # Class definitions
    hash = Column(String(64))  # Content hash for change detection
    indexed_at = Column(DateTime, default=_utcnow)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="files")


class APIEndpoint(Base):
    """Detected API endpoints"""
    __tablename__ = "api_endpoints"
    __table_args__ = (
        Index('idx_api_workspace', 'workspace_id'),
        Index('idx_api_method_path', 'method', 'path'),
    )
    
    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))
    method = Column(String(10))  # GET, POST, etc.
    path = Column(String(300))
    file_path = Column(String(500))
    line_number = Column(Integer)
    handler_name = Column(String(100))
    parameters = Column(JSON)
    request_body = Column(JSON)
    response_schema = Column(JSON)
    detected_at = Column(DateTime, default=_utcnow)


class ContextSession(Base):
    """Active context sessions"""
    __tablename__ = "context_sessions"
    
    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))
    current_file = Column(String(500))
    recent_files = Column(JSON)  # Last N files edited
    active_errors = Column(JSON)
    terminal_output = Column(Text)
    git_branch = Column(String(100))
    git_status = Column(JSON)
    started_at = Column(DateTime, default=_utcnow)
    last_update = Column(DateTime, default=_utcnow)


# ════════════════════════════════════════════════════════════════
# Autonomous Runtime Tables
# ════════════════════════════════════════════════════════════════

class EntityIndex(Base):
    """Semantic entity extracted from source code (model, DTO, route, service, etc.)."""
    __tablename__ = "entity_index"
    __table_args__ = (
        Index('idx_entity_workspace', 'workspace_id'),
        Index('idx_entity_file', 'file_path'),
        Index('idx_entity_type', 'entity_type'),
        Index('idx_entity_name', 'entity_name'),
        Index('idx_entity_file_type', 'file_path', 'entity_type'),
    )

    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))
    file_path = Column(String(500), nullable=False)
    file_hash = Column(String(64))
    entity_type = Column(String(50), nullable=False)  # model, dto, route, service, function, class, middleware, enum, type_alias
    entity_name = Column(String(200), nullable=False)
    line_start = Column(Integer)
    line_end = Column(Integer)
    signature = Column(Text)        # function signature, class declaration, etc.
    extra_info = Column(JSON, default=dict)  # extra parsed info (fields, params, return type)
    last_parsed = Column(DateTime, default=_utcnow)


class DependencyEdge(Base):
    """Edge in the dependency graph (file→file or entity→entity)."""
    __tablename__ = "dependency_edges"
    __table_args__ = (
        Index('idx_dep_workspace', 'workspace_id'),
        Index('idx_dep_source', 'source_file'),
        Index('idx_dep_target', 'target_file'),
        Index('idx_dep_type', 'edge_type'),
    )

    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))
    source_file = Column(String(500), nullable=False)
    source_entity = Column(String(200))
    target_file = Column(String(500), nullable=False)
    target_entity = Column(String(200))
    edge_type = Column(String(50), nullable=False)  # import, reference, extends, implements, uses, calls
    extra_info = Column(JSON, default=dict)


class ASTSnapshot(Base):
    """Serialized AST summary for drift detection."""
    __tablename__ = "ast_snapshots"
    __table_args__ = (
        Index('idx_ast_workspace', 'workspace_id'),
        Index('idx_ast_file', 'file_path'),
    )

    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))
    file_path = Column(String(500), nullable=False)
    file_hash = Column(String(64), nullable=False)
    snapshot = Column(JSON, nullable=False)  # Structured AST summary
    timestamp = Column(DateTime, default=_utcnow)


class RiskHistory(Base):
    """Point-in-time risk snapshot for trend tracking."""
    __tablename__ = "risk_history"
    __table_args__ = (
        Index('idx_risk_workspace', 'workspace_id'),
        Index('idx_risk_timestamp', 'timestamp'),
    )

    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))
    timestamp = Column(DateTime, default=_utcnow)
    schema_risk = Column(Float, default=0.0)
    contract_risk = Column(Float, default=0.0)
    migration_risk = Column(Float, default=0.0)
    dependency_risk = Column(Float, default=0.0)
    security_risk = Column(Float, default=0.0)
    naming_risk = Column(Float, default=0.0)
    drift_risk = Column(Float, default=0.0)
    overall_score = Column(Float, default=0.0)
    issue_count = Column(Integer, default=0)
    details = Column(JSON, default=dict)


class DriftEvent(Base):
    """Detected structural drift (changed/removed/renamed field, type, etc.)."""
    __tablename__ = "drift_events"
    __table_args__ = (
        Index('idx_drift_workspace', 'workspace_id'),
        Index('idx_drift_file', 'file_path'),
        Index('idx_drift_severity', 'severity'),
        Index('idx_drift_resolved', 'resolved'),
    )

    id = Column(Integer, primary_key=True)
    workspace_id = Column(Integer, ForeignKey("workspaces.id"))
    file_path = Column(String(500), nullable=False)
    entity_name = Column(String(200))
    drift_type = Column(String(50), nullable=False)  # field_removed, field_added, field_renamed, type_changed, nullability_changed, return_type_changed, route_method_changed, signature_changed
    old_value = Column(Text)
    new_value = Column(Text)
    severity = Column(String(20), default="MEDIUM")  # CRITICAL, HIGH, MEDIUM, LOW
    timestamp = Column(DateTime, default=_utcnow)
    resolved = Column(Boolean, default=False)
    resolution = Column(Text)
