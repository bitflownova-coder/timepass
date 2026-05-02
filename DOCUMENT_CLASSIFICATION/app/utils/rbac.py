"""
RBAC - Role-Based Access Control decorators and helpers

Roles (stored in User.role column and JWT claims):
  admin   - full access, can retrain, view all users
  user    - standard access (upload, classify, manage own docs)
  viewer  - read-only access (download and view only)
"""
from functools import wraps
from flask import jsonify
from flask_jwt_extended import get_jwt, verify_jwt_in_request


# Ordered hierarchy: higher index = more permissions
ROLE_HIERARCHY = ['viewer', 'user', 'admin']


def _role_rank(role: str) -> int:
    try:
        return ROLE_HIERARCHY.index(role)
    except ValueError:
        return -1


def require_role(*roles):
    """
    Decorator that requires the JWT holder to have one of the specified roles.

    Usage:
        @require_role('admin')
        @require_role('admin', 'user')

    Must be applied AFTER @jwt_required().
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims = get_jwt()
            user_role = claims.get('role', 'viewer')
            if user_role not in roles:
                return {
                    'success': False,
                    'error': f'Access denied. Required role(s): {", ".join(roles)}. '
                             f'Your role: {user_role}',
                }, 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def require_min_role(min_role: str):
    """
    Decorator that requires the user's role to be at least min_role in
    the hierarchy (viewer < user < admin).

    Usage:
        @require_min_role('user')   # allows user and admin, blocks viewer
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            claims   = get_jwt()
            user_role = claims.get('role', 'viewer')
            if _role_rank(user_role) < _role_rank(min_role):
                return {
                    'success': False,
                    'error': f'Access denied. Minimum required role: {min_role}.',
                }, 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator


def get_current_role() -> str:
    """Return the role from the current JWT claims (call inside request context)."""
    try:
        claims = get_jwt()
        return claims.get('role', 'viewer')
    except Exception:
        return 'viewer'


def is_admin() -> bool:
    return get_current_role() == 'admin'


def can_write() -> bool:
    return _role_rank(get_current_role()) >= _role_rank('user')
