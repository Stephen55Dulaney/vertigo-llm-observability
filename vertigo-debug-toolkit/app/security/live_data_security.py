"""
Security module for live data integration.
Provides authentication, authorization, and security validation for real-time data features.
"""

import os
import hmac
import hashlib
import logging
import jwt
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from functools import wraps
from flask import request, current_app, g, jsonify
from flask_login import current_user
from werkzeug.exceptions import Forbidden, Unauthorized
from sqlalchemy import text
from app.models import db

logger = logging.getLogger(__name__)

class SecurityError(Exception):
    """Base security exception."""
    pass

class LiveDataSecurity:
    """
    Security manager for live data integration features.
    
    Handles:
    - API authentication and authorization
    - Webhook signature verification
    - Rate limiting
    - Access control for sensitive operations
    """
    
    def __init__(self):
        self.webhook_secrets = {
            'langwatch': os.getenv('LANGWATCH_WEBHOOK_SECRET'),
            'langfuse': os.getenv('LANGFUSE_WEBHOOK_SECRET'),
            'custom': os.getenv('CUSTOM_WEBHOOK_SECRET', 'dev-secret-key')
        }
        
        self.rate_limits = {
            'api_requests_per_minute': 100,
            'webhook_requests_per_minute': 1000,
            'sync_triggers_per_hour': 10
        }
        
        # Initialize rate limiting storage
        self._rate_limit_storage = {}
    
    def verify_webhook_signature(self, payload: bytes, signature: str, source: str) -> bool:
        """
        Verify HMAC signature for webhook requests.
        
        Args:
            payload: Raw request payload
            signature: HMAC signature from headers
            source: Webhook source identifier
            
        Returns:
            True if signature is valid
        """
        try:
            secret = self.webhook_secrets.get(source)
            if not secret:
                logger.warning(f"No webhook secret configured for source: {source}")
                return False
            
            # Handle different signature formats
            if signature.startswith('sha256='):
                signature = signature[7:]
            elif signature.startswith('sha1='):
                # Support sha1 for older systems
                signature = signature[5:]
                expected = hmac.new(
                    secret.encode('utf-8'),
                    payload,
                    hashlib.sha1
                ).hexdigest()
                return hmac.compare_digest(expected, signature)
            
            # Default to sha256
            expected = hmac.new(
                secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(expected, signature)
            
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False
    
    def check_api_rate_limit(self, identifier: str, limit_type: str) -> bool:
        """
        Check if request is within rate limits.
        
        Args:
            identifier: Unique identifier (IP, user ID, etc.)
            limit_type: Type of rate limit to check
            
        Returns:
            True if within limits
        """
        try:
            current_time = datetime.utcnow()
            limit_key = f"{limit_type}:{identifier}"
            
            # Get rate limit configuration
            limit_per_period = self.rate_limits.get(limit_type, 100)
            
            # Clean old entries
            if limit_key in self._rate_limit_storage:
                self._rate_limit_storage[limit_key] = [
                    timestamp for timestamp in self._rate_limit_storage[limit_key]
                    if current_time - timestamp < timedelta(minutes=1)
                ]
            else:
                self._rate_limit_storage[limit_key] = []
            
            # Check current count
            current_count = len(self._rate_limit_storage[limit_key])
            
            if current_count >= limit_per_period:
                logger.warning(f"Rate limit exceeded for {identifier}: {current_count}/{limit_per_period}")
                return False
            
            # Add current request
            self._rate_limit_storage[limit_key].append(current_time)
            return True
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            return True  # Allow request on error
    
    def validate_api_permissions(self, required_permissions: List[str]) -> bool:
        """
        Validate that current user has required permissions.
        
        Args:
            required_permissions: List of required permission strings
            
        Returns:
            True if user has all required permissions
        """
        try:
            if not current_user or not current_user.is_authenticated:
                return False
            
            # Admin users have all permissions
            if current_user.is_admin:
                return True
            
            # Check specific permissions
            user_permissions = self._get_user_permissions(current_user.id)
            
            return all(perm in user_permissions for perm in required_permissions)
            
        except Exception as e:
            logger.error(f"Error validating permissions: {e}")
            return False
    
    def _get_user_permissions(self, user_id: int) -> List[str]:
        """Get user permissions from database."""
        try:
            # For now, return basic permissions for authenticated users
            # In a full implementation, this would query a permissions table
            return [
                'read_performance_data',
                'read_traces',
                'read_sync_status'
            ]
            
        except Exception as e:
            logger.error(f"Error getting user permissions: {e}")
            return []
    
    def validate_sync_trigger_permission(self) -> bool:
        """Validate permission to trigger manual sync operations."""
        try:
            if not current_user or not current_user.is_authenticated:
                return False
            
            # Only admin users can trigger sync operations
            if not current_user.is_admin:
                logger.warning(f"Non-admin user {current_user.id} attempted sync trigger")
                return False
            
            # Check rate limits for sync triggers
            identifier = f"user_{current_user.id}"
            if not self.check_api_rate_limit(identifier, 'sync_triggers_per_hour'):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating sync trigger permission: {e}")
            return False
    
    def sanitize_query_parameters(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize query parameters to prevent injection attacks.
        
        Args:
            params: Raw query parameters
            
        Returns:
            Sanitized parameters
        """
        sanitized = {}
        
        try:
            # Define allowed parameters and their validation rules
            allowed_params = {
                'hours': {'type': int, 'min': 1, 'max': 168},
                'limit': {'type': int, 'min': 1, 'max': 500},
                'offset': {'type': int, 'min': 0, 'max': 10000},
                'status': {'type': str, 'allowed': ['all', 'success', 'error', 'pending']},
                'source': {'type': str, 'allowed': ['all', 'firestore', 'webhook', 'langwatch']},
                'model': {'type': str, 'max_length': 100},
                'user_id': {'type': str, 'max_length': 100}
            }
            
            for key, value in params.items():
                if key not in allowed_params:
                    logger.warning(f"Ignoring unknown parameter: {key}")
                    continue
                
                rules = allowed_params[key]
                param_type = rules['type']
                
                try:
                    # Type conversion
                    if param_type == int:
                        value = int(value)
                        if 'min' in rules and value < rules['min']:
                            value = rules['min']
                        if 'max' in rules and value > rules['max']:
                            value = rules['max']
                    
                    elif param_type == str:
                        value = str(value)
                        if 'max_length' in rules:
                            value = value[:rules['max_length']]
                        if 'allowed' in rules and value not in rules['allowed']:
                            logger.warning(f"Invalid value for {key}: {value}")
                            continue
                    
                    sanitized[key] = value
                    
                except (ValueError, TypeError) as e:
                    logger.warning(f"Invalid parameter value for {key}: {value} ({e})")
                    continue
            
            return sanitized
            
        except Exception as e:
            logger.error(f"Error sanitizing query parameters: {e}")
            return {}
    
    def log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security-related events for monitoring."""
        try:
            security_log = {
                'timestamp': datetime.utcnow().isoformat(),
                'event_type': event_type,
                'user_id': current_user.id if current_user and current_user.is_authenticated else None,
                'ip_address': request.remote_addr if request else None,
                'user_agent': request.headers.get('User-Agent') if request else None,
                'details': details
            }
            
            # In production, this should go to a security log system
            logger.warning(f"SECURITY EVENT: {json.dumps(security_log, default=str)}")
            
        except Exception as e:
            logger.error(f"Error logging security event: {e}")

# Security decorators
def require_permissions(permissions: List[str]):
    """
    Decorator to require specific permissions for API endpoints.
    
    Args:
        permissions: List of required permission strings
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            security_manager = LiveDataSecurity()
            
            if not security_manager.validate_api_permissions(permissions):
                security_manager.log_security_event('permission_denied', {
                    'required_permissions': permissions,
                    'endpoint': request.endpoint
                })
                raise Forbidden("Insufficient permissions")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def require_admin():
    """Decorator to require admin privileges."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            if not current_user or not current_user.is_authenticated or not current_user.is_admin:
                security_manager = LiveDataSecurity()
                security_manager.log_security_event('admin_required', {
                    'endpoint': request.endpoint
                })
                raise Forbidden("Admin privileges required")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def rate_limit(limit_type: str = 'api_requests_per_minute'):
    """
    Decorator to apply rate limiting to endpoints.
    
    Args:
        limit_type: Type of rate limit to apply
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            security_manager = LiveDataSecurity()
            
            # Use user ID if authenticated, otherwise IP address
            identifier = f"user_{current_user.id}" if current_user and current_user.is_authenticated else request.remote_addr
            
            if not security_manager.check_api_rate_limit(identifier, limit_type):
                security_manager.log_security_event('rate_limit_exceeded', {
                    'identifier': identifier,
                    'limit_type': limit_type,
                    'endpoint': request.endpoint
                })
                return jsonify({
                    'success': False,
                    'error': 'Rate limit exceeded',
                    'retry_after': 60
                }), 429
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

def validate_webhook_source():
    """Decorator to validate webhook requests."""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            security_manager = LiveDataSecurity()
            
            # Skip validation in development
            if current_app.config.get('ENV') == 'development':
                return func(*args, **kwargs)
            
            # Get source from URL
            source = kwargs.get('source') or request.view_args.get('source')
            if not source:
                return jsonify({'error': 'Invalid webhook source'}), 400
            
            # Get signature from headers
            signature = (
                request.headers.get('X-Signature') or 
                request.headers.get('X-Hub-Signature-256') or
                request.headers.get('X-Hub-Signature')
            )
            
            if not signature:
                security_manager.log_security_event('webhook_no_signature', {
                    'source': source,
                    'headers': dict(request.headers)
                })
                return jsonify({'error': 'Missing signature'}), 401
            
            # Verify signature
            payload = request.get_data()
            if not security_manager.verify_webhook_signature(payload, signature, source):
                security_manager.log_security_event('webhook_invalid_signature', {
                    'source': source,
                    'signature_provided': signature[:10] + '...'
                })
                return jsonify({'error': 'Invalid signature'}), 401
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Global security manager instance
live_data_security = LiveDataSecurity()