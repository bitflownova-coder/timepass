"""
Pytest configuration - shared fixtures for all tests
"""
import pytest
import io
from app import create_app
from app.models import db as _db
from app.models.user import User


@pytest.fixture(scope='session')
def app():
    """Create application instance configured for testing."""
    application = create_app('testing')
    application.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'JWT_SECRET_KEY': 'test-jwt-secret',
        'ENCRYPTION_KEY': 'test-enc-key-32-bytes-padded-000',
        'UPLOAD_FOLDER': '/tmp/smartdoc_test_uploads',
        'WTF_CSRF_ENABLED': False,
    })
    return application


@pytest.fixture(scope='session')
def db(app):
    """Create all tables once per test session."""
    with app.app_context():
        _db.create_all()
        yield _db
        _db.drop_all()


@pytest.fixture(autouse=True)
def db_session(db, app):
    """Wrap each test in a transaction that is rolled back after the test."""
    with app.app_context():
        connection = db.engine.connect()
        transaction = connection.begin()
        db.session.bind = connection
        yield db.session
        db.session.remove()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client(app):
    """Flask test client."""
    return app.test_client()


@pytest.fixture
def user_payload():
    return {
        'email': 'test@example.com',
        'password': 'Test@1234!',
        'full_name': 'Test User',
    }


@pytest.fixture
def admin_payload():
    return {
        'email': 'admin@example.com',
        'password': 'Admin@1234!',
        'full_name': 'Admin User',
    }


@pytest.fixture
def registered_user(client, user_payload, app):
    """Register a user and return the JSON response."""
    res = client.post('/api/auth/register',
                      json=user_payload,
                      content_type='application/json')
    return res.get_json()


@pytest.fixture
def auth_headers(client, user_payload, registered_user):
    """Return Authorization headers for a logged-in user."""
    res = client.post('/api/auth/login',
                      json={'email': user_payload['email'],
                            'password': user_payload['password']},
                      content_type='application/json')
    data = res.get_json()
    token = data.get('token', '')
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def sample_txt_file():
    """In-memory .txt file for upload tests."""
    content = (
        b"Invoice #2024-001\n"
        b"Amount Due: $500.00\n"
        b"Payment Terms: Net 30\n"
        b"Please remit payment to the account specified.\n"
    )
    return io.BytesIO(content), 'invoice.txt'
