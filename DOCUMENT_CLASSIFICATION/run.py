"""
Application Entry Point - Start the Flask application
"""
import os
from dotenv import load_dotenv
from app import create_app, db
from app.models import User, Document, AuditLog, Feedback, FileMetadata

# Load environment variables
load_dotenv()

# Create Flask application
app = create_app(os.getenv('FLASK_ENV', 'development'))


@app.shell_context_processor
def make_shell_context():
    """Make models available in Flask shell"""
    return {
        'db': db,
        'User': User,
        'Document': Document,
        'AuditLog': AuditLog,
        'Feedback': Feedback,
        'FileMetadata': FileMetadata
    }


if __name__ == '__main__':
    # Ensure required directories exist
    os.makedirs('data/uploads', exist_ok=True)
    os.makedirs('models', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
    os.makedirs('instance', exist_ok=True)
    
    # Run development server
    ssl_cert = os.getenv('SSL_CERT_PATH')
    ssl_key = os.getenv('SSL_KEY_PATH')
    ssl_context = (ssl_cert, ssl_key) if ssl_cert and ssl_key else None

    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('FLASK_ENV') == 'development',
        ssl_context=ssl_context,
    )
