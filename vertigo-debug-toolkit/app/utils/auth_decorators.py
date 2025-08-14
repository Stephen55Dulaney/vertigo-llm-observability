"""
Custom authentication decorators for API endpoints.
"""

from functools import wraps
from flask import jsonify, request, current_app
from flask_login import current_user


def api_login_required(f):
    """
    Custom login_required decorator for API endpoints.
    Returns JSON error instead of redirecting to login page.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            # For API requests, return JSON error instead of redirect
            if request.path.startswith('/api/') or request.path.startswith('/dashboard/api/'):
                return jsonify({
                    'status': 'error',
                    'message': 'Authentication required',
                    'code': 'AUTH_REQUIRED'
                }), 401
            
            # For non-API requests, use the default behavior
            from flask_login import login_required
            return login_required(f)(*args, **kwargs)
        
        return f(*args, **kwargs)
    
    return decorated_function


def api_auth_error_handler(f):
    """
    Decorator to handle authentication errors gracefully for API endpoints.
    Can be used in addition to login_required for better error handling.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            # Check if this looks like an authentication error
            if 'login' in str(e).lower() or 'authentication' in str(e).lower():
                return jsonify({
                    'status': 'error',
                    'message': 'Authentication failed',
                    'code': 'AUTH_ERROR'
                }), 401
            
            # Re-raise other exceptions
            raise e
    
    return decorated_function