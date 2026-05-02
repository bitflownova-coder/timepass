"""
Authentication Routes - User registration, login, logout
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from app.models import User, db, AuditLog
from app.utils.validators import validate_email, validate_password
import os

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
def register():
    """
    Register a new user account
    
    Request JSON:
    {
        "email": "user@example.com",
        "password": "secure_password_123",
        "full_name": "John Doe" (optional)
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return {
                'success': False,
                'error': 'Request body is required'
            }, 400
        
        # Validate input
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        full_name = data.get('full_name', '').strip() if data.get('full_name') else None
        
        # Email validation
        if not email:
            return {
                'success': False,
                'error': 'Email is required'
            }, 400
        
        if not validate_email(email):
            return {
                'success': False,
                'error': 'Invalid email format'
            }, 400
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            return {
                'success': False,
                'error': 'Email already registered'
            }, 409
        
        # Password validation
        if not password:
            return {
                'success': False,
                'error': 'Password is required'
            }, 400
        
        is_valid, message = validate_password(password)
        if not is_valid:
            return {
                'success': False,
                'error': message
            }, 400
        
        # Create new user
        user = User(
            email=email,
            full_name=full_name,
            role='user'
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Generate JWT token for immediate login after registration
        access_token = create_access_token(identity=user.id)
        
        # Log audit
        log_audit_action(
            user_id=user.id,
            action='register',
            resource_type='user',
            resource_name=user.email,
            status='success'
        )
        
        return {
            'success': True,
            'message': 'User registered successfully',
            'token': access_token,
            'user': user.to_dict()
        }, 201
    
    except Exception as e:
        db.session.rollback()
        return {
            'success': False,
            'error': 'An error occurred during registration'
        }, 500


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    Authenticate user and get JWT token
    
    Request JSON:
    {
        "email": "user@example.com",
        "password": "secure_password_123"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return {
                'success': False,
                'error': 'Request body is required'
            }, 400
        
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return {
                'success': False,
                'error': 'Email and password are required'
            }, 400
        
        # Find user
        user = User.query.filter_by(email=email).first()
        
        if not user or not user.check_password(password):
            log_audit_action(
                user_id=None,
                action='login',
                resource_type='user',
                resource_name=email,
                status='failed',
                error='Invalid email or password'
            )
            
            return {
                'success': False,
                'error': 'Invalid email or password'
            }, 401
        
        if not user.is_active:
            return {
                'success': False,
                'error': 'Account is disabled'
            }, 403
        
        # Update last login
        user.update_last_login()
        
        # Generate JWT token
        access_token = create_access_token(identity=user.id)
        
        # Log audit
        log_audit_action(
            user_id=user.id,
            action='login',
            resource_type='user',
            resource_name=user.email,
            status='success'
        )
        
        return {
            'success': True,
            'message': 'Login successful',
            'token': access_token,
            'user': user.to_dict()
        }, 200
    
    except Exception as e:
        return {
            'success': False,
            'error': 'An error occurred during login'
        }, 500


@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Logout user (invalidate token)
    """
    try:
        current_user_id = get_jwt_identity()
        
        # Log audit
        log_audit_action(
            user_id=current_user_id,
            action='logout',
            resource_type='user',
            resource_name='',
            status='success'
        )
        
        return {
            'success': True,
            'message': 'Logout successful'
        }, 200
    
    except Exception as e:
        return {
            'success': False,
            'error': 'An error occurred during logout'
        }, 500


@auth_bp.route('/verify', methods=['GET'])
@jwt_required()
def verify_token():
    """Lightweight endpoint to check if the current JWT is still valid."""
    return {'success': True}, 200


@auth_bp.route('/auto-login', methods=['POST', 'GET'])
def auto_login():
    """
    Single-user local mode: get-or-create the default local user and
    return a JWT. Used to bypass the login screen for desktop/local use.
    """
    try:
        DEFAULT_EMAIL = 'local@smartdoc.local'
        user = User.query.filter_by(email=DEFAULT_EMAIL).first()
        if user is None:
            user = User(email=DEFAULT_EMAIL, full_name='Local User')
            user.set_password(os.urandom(16).hex())  # unguessable; never used
            db.session.add(user)
            db.session.commit()
        if not user.is_active:
            user.is_active = True
            db.session.commit()
        user.update_last_login()
        access_token = create_access_token(identity=user.id)
        return {
            'success': True,
            'token':   access_token,
            'user':    user.to_dict(),
        }, 200
    except Exception as e:
        db.session.rollback()
        return {'success': False, 'error': f'Auto-login failed: {e}'}, 500


@auth_bp.route('/profile', methods=['GET'])
@jwt_required()
def get_profile():
    """
    Get current user profile
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return {
                'success': False,
                'error': 'User not found'
            }, 404
        
        return {
            'success': True,
            'user': user.to_dict()
        }, 200
    
    except Exception as e:
        return {
            'success': False,
            'error': 'An error occurred'
        }, 500


@auth_bp.route('/profile', methods=['PATCH'])
@jwt_required()
def update_profile():
    """
    Update user profile
    
    Request JSON:
    {
        "full_name": "Jane Doe" (optional)
    }
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return {
                'success': False,
                'error': 'User not found'
            }, 404
        
        data = request.get_json()
        
        if data.get('full_name'):
            user.full_name = data.get('full_name').strip()
        
        db.session.commit()
        
        # Log audit
        log_audit_action(
            user_id=current_user_id,
            action='update_profile',
            resource_type='user',
            resource_name=user.email,
            status='success'
        )
        
        return {
            'success': True,
            'message': 'Profile updated successfully',
            'user': user.to_dict()
        }, 200
    
    except Exception as e:
        db.session.rollback()
        return {
            'success': False,
            'error': 'An error occurred'
        }, 500


@auth_bp.route('/change-password', methods=['POST'])
@jwt_required()
def change_password():
    """
    Change user password
    
    Request JSON:
    {
        "current_password": "old_password",
        "new_password": "new_password"
    }
    """
    try:
        current_user_id = get_jwt_identity()
        user = User.query.get(current_user_id)
        
        if not user:
            return {
                'success': False,
                'error': 'User not found'
            }, 404
        
        data = request.get_json()
        
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        
        # Verify current password
        if not user.check_password(current_password):
            return {
                'success': False,
                'error': 'Current password is incorrect'
            }, 401
        
        # Validate new password
        is_valid, message = validate_password(new_password)
        if not is_valid:
            return {
                'success': False,
                'error': message
            }, 400
        
        # Update password
        user.set_password(new_password)
        db.session.commit()
        
        # Log audit
        log_audit_action(
            user_id=current_user_id,
            action='change_password',
            resource_type='user',
            resource_name=user.email,
            status='success'
        )
        
        return {
            'success': True,
            'message': 'Password changed successfully'
        }, 200
    
    except Exception as e:
        db.session.rollback()
        return {
            'success': False,
            'error': 'An error occurred'
        }, 500


def log_audit_action(user_id, action, resource_type, resource_name, status='success', error=None):
    """Helper function to log audit actions"""
    try:
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_name=resource_name,
            ip_address=request.remote_addr if request else None,
            user_agent=request.headers.get('User-Agent') if request else None,
            status=status,
            error_message=error
        )
        db.session.add(audit_log)
        db.session.commit()
    except:
        pass
