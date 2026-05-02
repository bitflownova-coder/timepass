"""
Routes Package - API route blueprints
"""
from app.routes.auth import auth_bp
from app.routes.classify import classify_bp
from app.routes.upload import upload_bp
from app.routes.folders import folders_bp
from app.routes.views import views_bp

__all__ = ['auth_bp', 'classify_bp', 'upload_bp', 'folders_bp', 'views_bp']
