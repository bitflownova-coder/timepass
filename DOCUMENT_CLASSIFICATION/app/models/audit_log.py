"""
Additional Models - AuditLog and Feedback models
"""
from datetime import datetime
from app.models.user import db


class AuditLog(db.Model):
    """Audit log model for tracking all user actions"""
    __tablename__ = 'audit_log'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # User who performed action
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)
    
    # Resource information
    action = db.Column(db.String(100), nullable=False)  # 'upload', 'download', 'delete', 'access'
    resource_type = db.Column(db.String(50), nullable=True)  # 'document', 'folder', 'user'
    resource_id = db.Column(db.Integer, nullable=True, index=True)
    resource_name = db.Column(db.String(255), nullable=True)
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=True)
    
    # Request information
    ip_address = db.Column(db.String(45), nullable=True)  # IPv4 or IPv6
    user_agent = db.Column(db.String(255), nullable=True)
    
    # Status
    status = db.Column(db.String(50), default='success')  # 'success', 'failed'
    error_message = db.Column(db.String(255), nullable=True)
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def to_dict(self):
        """Convert audit log to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'action': self.action,
            'resource_type': self.resource_type,
            'resource_name': self.resource_name,
            'status': self.status,
            'ip_address': self.ip_address,
            'created_at': self.created_at.isoformat(),
        }
    
    def __repr__(self):
        return f'<AuditLog {self.action} by user_id={self.user_id}>'


class Feedback(db.Model):
    """User feedback model for storing corrections to improve model"""
    __tablename__ = 'feedback'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # Document and user
    document_id = db.Column(db.Integer, db.ForeignKey('document.id'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Predictions and corrections
    predicted_label = db.Column(db.String(100), nullable=False)  # What AI predicted
    corrected_label = db.Column(db.String(100), nullable=True)  # What user corrected to
    
    # Feedback
    feedback_text = db.Column(db.Text, nullable=True)  # User comments
    is_useful = db.Column(db.Boolean, nullable=True)  # Thumbs up/down
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def to_dict(self):
        """Convert feedback to dictionary"""
        return {
            'id': self.id,
            'document_id': self.document_id,
            'predicted_label': self.predicted_label,
            'corrected_label': self.corrected_label,
            'feedback_text': self.feedback_text,
            'is_useful': self.is_useful,
            'created_at': self.created_at.isoformat(),
        }
    
    def __repr__(self):
        return f'<Feedback document_id={self.document_id}>'
