"""
Flask Application Factory - Initialize Flask app with all extensions
"""
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import logging
from logging.handlers import RotatingFileHandler
import os

try:
    import sentry_sdk
    from sentry_sdk.integrations.flask import FlaskIntegration
except Exception:  # pragma: no cover - optional dependency
    sentry_sdk = None
    FlaskIntegration = None

from config import config
from app.models import db, bcrypt


def create_app(config_name=None):
    """
    Application factory function
    
    Args:
        config_name (str): Configuration environment (development, testing, production)
    
    Returns:
        Flask: Flask application instance
    """
    
    # Determine config
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # ==================== Monitoring (Sentry) ====================
    if sentry_sdk and app.config.get('SENTRY_DSN'):
        sentry_sdk.init(
            dsn=app.config['SENTRY_DSN'],
            environment=app.config.get('SENTRY_ENVIRONMENT', config_name),
            traces_sample_rate=app.config.get('SENTRY_TRACES_SAMPLE_RATE', 0.1),
            integrations=[FlaskIntegration()],
            send_default_pii=False,
        )
    
    # ==================== Initialize Extensions ====================
    
    # Database
    db.init_app(app)
    
    # Authentication
    bcrypt.init_app(app)
    jwt = JWTManager(app)
    
    # CORS
    CORS(app, resources={
        r"/api/*": {
            "origins": app.config['CORS_ORIGINS'].split(','),
            "methods": ["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True,
            "max_age": 3600
        }
    })
    
    # Rate Limiting — read limits from config so DevelopmentConfig can override
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=app.config.get('RATELIMIT_DEFAULT', '200 per day;50 per hour').split(';')
    )
    
    # ==================== Create Tables ====================

    with app.app_context():
        db.create_all()
        # Lightweight schema migrations for new columns added after first install
        from app.utils.local_indexer import ensure_fts_table, ensure_columns
        ensure_columns(db)
        from app.models.virtual_path import seed_hierarchy_templates
        seed_hierarchy_templates()
        ensure_fts_table(db)

    # ==================== Error Handlers ====================
    
    @app.errorhandler(404)
    def not_found(error):
        return {
            'success': False,
            'error': 'Resource not found'
        }, 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return {
            'success': False,
            'error': 'Method not allowed'
        }, 405
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {
            'success': False,
            'error': 'Internal server error'
        }, 500
    
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return {
            'success': False,
            'error': f'Rate limit exceeded: {e.description}'
        }, 429

    # ==================== Security Headers ====================

    @app.after_request
    def add_security_headers(response):
        response.headers.setdefault('X-Content-Type-Options', 'nosniff')
        response.headers.setdefault('X-Frame-Options', 'DENY')
        response.headers.setdefault('Referrer-Policy', 'no-referrer')
        response.headers.setdefault('Permissions-Policy', 'geolocation=(), microphone=(), camera=()')
        if request.is_secure:
            response.headers.setdefault(
                'Strict-Transport-Security',
                'max-age=31536000; includeSubDomains'
            )
        return response
    
    # ==================== JWT Handlers ====================
    
    @jwt.user_lookup_loader
    def user_lookup_callback(_jwt_header, jwt_data):
        identity = jwt_data["sub"]
        from app.models import User
        return User.query.filter_by(id=identity).first()
    
    @jwt.additional_claims_loader
    def add_claims_to_access_token(identity):
        from app.models import User
        user = User.query.filter_by(id=identity).first()
        if user:
            return {"role": user.role}
        return {}
    
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_data):
        return False

    # Return 401 for ALL JWT auth failures so the client can handle uniformly
    @jwt.invalid_token_loader
    def invalid_token_callback(reason):
        return {'success': False, 'error': f'Invalid token: {reason}'}, 401

    @jwt.unauthorized_loader
    def missing_token_callback(reason):
        return {'success': False, 'error': f'Authorization required: {reason}'}, 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_data):
        return {'success': False, 'error': 'Token has expired. Please sign in again.'}, 401

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_data):
        return {'success': False, 'error': 'Token has been revoked. Please sign in again.'}, 401
    
    # ==================== Health Check ====================
    
    @app.route('/health', methods=['GET'])
    def health_check():
        """Health check endpoint"""
        try:
            # Check database connection
            db.session.execute('SELECT 1')
            return {
                'status': 'healthy',
                'message': 'Application is running'
            }, 200
        except:
            return {
                'status': 'unhealthy',
                'message': 'Database connection failed'
            }, 503
    
    # ==================== SPA Frontend ====================

    from flask import send_from_directory

    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def serve_frontend(path):
        """Serve the React/SPA frontend for all non-API routes."""
        static_dir = os.path.join(app.root_path, 'static')
        if path and os.path.exists(os.path.join(static_dir, path)):
            return send_from_directory(static_dir, path)
        return send_from_directory(static_dir, 'index.html')

    # ==================== API Root ====================
    
    @app.route('/api', methods=['GET'])
    def api_root():
        """API root endpoint"""
        return {
            'success': True,
            'message': 'SmartDoc AI API',
            'version': '1.0.0',
            'endpoints': {
                'auth': '/api/auth',
                'documents': '/api/documents',
                'upload': '/api/upload',
                'search': '/api/search',
                'dashboard': '/api/dashboard'
            }
        }, 200
    
    # ==================== Register Blueprints ====================
    
    from app.routes.auth import auth_bp
    from app.routes.classify import classify_bp
    from app.routes.upload import upload_bp
    from app.routes.folders import folders_bp
    from app.routes.search import search_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.views import views_bp
    from app.routes.indexer import indexer_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(classify_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(folders_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(views_bp)
    app.register_blueprint(indexer_bp)
    
    # ==================== Setup Logging ====================
    
    if not app.debug:
        # Create logs directory
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # Setup file handler
        file_handler = RotatingFileHandler(
            app.config['LOG_FILE'],
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        
        formatter = logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        )
        file_handler.setFormatter(formatter)
        file_handler.setLevel(logging.INFO)
        
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('SmartDoc AI Application Startup')
    
    # ==================== Create Directories ====================
    
    # Create upload directory if it doesn't exist
    upload_folder = app.config.get('UPLOAD_FOLDER', 'data/uploads')
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)
    
    # Create models directory if it doesn't exist
    models_folder = app.config.get('MODEL_FOLDER', 'models')
    if not os.path.exists(models_folder):
        os.makedirs(models_folder)
    
    return app
