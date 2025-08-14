"""
API Key Authentication Service

Comprehensive API key management system with scopes, rate limiting,
and security monitoring for the Vertigo Debug Toolkit.
"""

import os
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from flask import request, g
from dataclasses import dataclass
from enum import Enum
import logging
import json

from app.models import User, db

logger = logging.getLogger(__name__)


class APIKeyStatus(Enum):
    """API key status."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    EXPIRED = "expired"
    REVOKED = "revoked"


class APIKeyScope(Enum):
    """API key scopes/permissions."""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    ANALYTICS = "analytics"
    PROMPTS = "prompts"
    PERFORMANCE = "performance"
    COSTS = "costs"
    SYNC = "sync"
    WEBHOOKS = "webhooks"
    ALERTS = "alerts"


@dataclass
class APIKeyInfo:
    """API key information."""
    key_id: str
    name: str
    user_id: int
    scopes: List[str]
    status: APIKeyStatus
    created_at: datetime
    expires_at: Optional[datetime] = None
    last_used_at: Optional[datetime] = None
    usage_count: int = 0
    rate_limit_tier: str = "free"


class APIKeyService:
    """API key authentication and management service."""
    
    def __init__(self):
        # API key storage (in production, use database)
        self.api_keys: Dict[str, APIKeyInfo] = {}
        
        # Default scopes by user role
        self.default_scopes = {
            'admin': [scope.value for scope in APIKeyScope],
            'user': [APIKeyScope.READ.value, APIKeyScope.WRITE.value, 
                    APIKeyScope.ANALYTICS.value, APIKeyScope.PROMPTS.value],
            'readonly': [APIKeyScope.READ.value, APIKeyScope.ANALYTICS.value]
        }
        
        # Rate limiting tiers
        self.rate_limit_tiers = {
            'free': {'requests_per_hour': 100, 'requests_per_minute': 10},
            'premium': {'requests_per_hour': 1000, 'requests_per_minute': 50},
            'enterprise': {'requests_per_hour': 10000, 'requests_per_minute': 200}
        }
    
    def generate_api_key(self, user: User, name: str, scopes: List[str] = None, 
                        expires_days: int = None, rate_limit_tier: str = "free") -> Tuple[str, str]:
        """Generate new API key for user."""
        # Generate key ID and secret
        key_id = f"vdb_{secrets.token_urlsafe(16)}"
        key_secret = secrets.token_urlsafe(32)
        
        # Hash the secret for storage
        key_hash = self._hash_key(key_secret)
        
        # Determine scopes
        if scopes is None:
            if user.is_admin:
                scopes = self.default_scopes['admin']
            else:
                scopes = self.default_scopes['user']
        
        # Validate scopes
        valid_scopes = [scope.value for scope in APIKeyScope]
        scopes = [s for s in scopes if s in valid_scopes]
        
        # Create expiration date
        expires_at = None
        if expires_days:
            expires_at = datetime.utcnow() + timedelta(days=expires_days)
        
        # Create API key info
        api_key_info = APIKeyInfo(
            key_id=key_id,
            name=name,
            user_id=user.id,
            scopes=scopes,
            status=APIKeyStatus.ACTIVE,
            created_at=datetime.utcnow(),
            expires_at=expires_at,
            rate_limit_tier=rate_limit_tier
        )
        
        # Store the key (hash as key, info as value)
        self.api_keys[key_hash] = api_key_info
        
        # Log key creation
        logger.info(f"API key created: {key_id} for user {user.username}")
        
        # Return the full key (key_id + secret for user)
        full_key = f"{key_id}.{key_secret}"
        return full_key, key_id
    
    def authenticate_api_key(self, api_key: str) -> Tuple[bool, Optional[APIKeyInfo], Optional[str]]:
        """Authenticate API key and return key info."""
        if not api_key:
            return False, None, "No API key provided"
        
        # Parse key format: key_id.key_secret
        try:
            if '.' not in api_key:
                return False, None, "Invalid API key format"
            
            key_id, key_secret = api_key.split('.', 1)
            
            # Verify key ID format
            if not key_id.startswith('vdb_'):
                return False, None, "Invalid API key format"
            
        except ValueError:
            return False, None, "Invalid API key format"
        
        # Hash the secret to find in storage
        key_hash = self._hash_key(key_secret)
        
        # Find key info
        api_key_info = self.api_keys.get(key_hash)
        if not api_key_info:
            logger.warning(f"API key not found: {key_id}")
            return False, None, "Invalid API key"
        
        # Verify key ID matches
        if api_key_info.key_id != key_id:
            logger.warning(f"API key ID mismatch: {key_id}")
            return False, None, "Invalid API key"
        
        # Check key status
        if api_key_info.status != APIKeyStatus.ACTIVE:
            return False, None, f"API key is {api_key_info.status.value}"
        
        # Check expiration
        if api_key_info.expires_at and datetime.utcnow() > api_key_info.expires_at:
            # Update status to expired
            api_key_info.status = APIKeyStatus.EXPIRED
            return False, None, "API key has expired"
        
        # Update usage stats
        api_key_info.last_used_at = datetime.utcnow()
        api_key_info.usage_count += 1
        
        # Get user info
        user = User.query.get(api_key_info.user_id)
        if not user or not user.is_active:
            return False, None, "Associated user account is inactive"
        
        logger.debug(f"API key authenticated: {key_id} for user {user.username}")
        
        return True, api_key_info, None
    
    def check_api_key_scope(self, api_key_info: APIKeyInfo, required_scope: str) -> bool:
        """Check if API key has required scope."""
        if not api_key_info or not api_key_info.scopes:
            return False
        
        # Admin scope grants all permissions
        if APIKeyScope.ADMIN.value in api_key_info.scopes:
            return True
        
        return required_scope in api_key_info.scopes
    
    def get_api_keys_for_user(self, user_id: int) -> List[APIKeyInfo]:
        """Get all API keys for a user."""
        return [info for info in self.api_keys.values() if info.user_id == user_id]
    
    def revoke_api_key(self, key_id: str, user_id: int = None) -> bool:
        """Revoke an API key."""
        for key_hash, info in self.api_keys.items():
            if info.key_id == key_id:
                # Check if user has permission to revoke
                if user_id and info.user_id != user_id:
                    # Allow admin to revoke any key
                    user = User.query.get(user_id)
                    if not user or not user.is_admin:
                        return False
                
                info.status = APIKeyStatus.REVOKED
                logger.info(f"API key revoked: {key_id}")
                return True
        
        return False
    
    def suspend_api_key(self, key_id: str, reason: str = None) -> bool:
        """Suspend an API key."""
        for info in self.api_keys.values():
            if info.key_id == key_id:
                info.status = APIKeyStatus.SUSPENDED
                logger.warning(f"API key suspended: {key_id}, reason: {reason}")
                return True
        
        return False
    
    def get_rate_limits(self, api_key_info: APIKeyInfo) -> Dict[str, int]:
        """Get rate limits for API key."""
        tier = api_key_info.rate_limit_tier
        return self.rate_limit_tiers.get(tier, self.rate_limit_tiers['free'])
    
    def cleanup_expired_keys(self):
        """Clean up expired API keys."""
        now = datetime.utcnow()
        expired_keys = []
        
        for key_hash, info in self.api_keys.items():
            if info.expires_at and now > info.expires_at:
                info.status = APIKeyStatus.EXPIRED
                expired_keys.append(info.key_id)
        
        if expired_keys:
            logger.info(f"Marked {len(expired_keys)} API keys as expired")
        
        return expired_keys
    
    def get_usage_stats(self, days: int = 7) -> Dict[str, Any]:
        """Get API key usage statistics."""
        stats = {
            'total_keys': len(self.api_keys),
            'active_keys': 0,
            'suspended_keys': 0,
            'expired_keys': 0,
            'revoked_keys': 0,
            'usage_by_tier': {},
            'usage_by_scope': {},
            'recent_usage': []
        }
        
        now = datetime.utcnow()
        cutoff_date = now - timedelta(days=days)
        
        for info in self.api_keys.values():
            # Count by status
            stats[f"{info.status.value}_keys"] += 1
            
            # Count by tier
            tier = info.rate_limit_tier
            stats['usage_by_tier'][tier] = stats['usage_by_tier'].get(tier, 0) + 1
            
            # Count by scope
            for scope in info.scopes:
                stats['usage_by_scope'][scope] = stats['usage_by_scope'].get(scope, 0) + 1
            
            # Recent usage
            if info.last_used_at and info.last_used_at > cutoff_date:
                stats['recent_usage'].append({
                    'key_id': info.key_id,
                    'name': info.name,
                    'last_used': info.last_used_at.isoformat(),
                    'usage_count': info.usage_count
                })
        
        return stats
    
    def _hash_key(self, key_secret: str) -> str:
        """Hash API key secret for storage."""
        # Use SHA-256 for key hashing
        return hashlib.sha256(key_secret.encode()).hexdigest()
    
    def export_key_info(self, key_id: str, user_id: int) -> Optional[Dict[str, Any]]:
        """Export API key information (excluding secret)."""
        for info in self.api_keys.values():
            if info.key_id == key_id and info.user_id == user_id:
                return {
                    'key_id': info.key_id,
                    'name': info.name,
                    'scopes': info.scopes,
                    'status': info.status.value,
                    'created_at': info.created_at.isoformat(),
                    'expires_at': info.expires_at.isoformat() if info.expires_at else None,
                    'last_used_at': info.last_used_at.isoformat() if info.last_used_at else None,
                    'usage_count': info.usage_count,
                    'rate_limit_tier': info.rate_limit_tier
                }
        
        return None


class APIKeyAuthenticator:
    """API key authentication decorator and middleware."""
    
    def __init__(self, api_key_service: APIKeyService):
        self.service = api_key_service
    
    def authenticate_request(self, required_scopes: List[str] = None) -> Tuple[bool, Optional[str]]:
        """Authenticate current request using API key."""
        # Check for API key in headers
        api_key = None
        
        # Check Authorization header (Bearer token)
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            api_key = auth_header[7:]  # Remove 'Bearer ' prefix
        
        # Check X-API-Key header
        if not api_key:
            api_key = request.headers.get('X-API-Key')
        
        # Check query parameter (least secure, for development only)
        if not api_key and current_app.debug:
            api_key = request.args.get('api_key')
        
        if not api_key:
            return False, "No API key provided"
        
        # Authenticate API key
        valid, api_key_info, error = self.service.authenticate_api_key(api_key)
        if not valid:
            return False, error
        
        # Check required scopes
        if required_scopes:
            for scope in required_scopes:
                if not self.service.check_api_key_scope(api_key_info, scope):
                    return False, f"Insufficient permissions: {scope} scope required"
        
        # Store API key info in request context
        g.api_key_info = api_key_info
        g.api_authenticated = True
        
        # Get user for context
        user = User.query.get(api_key_info.user_id)
        if user:
            g.api_user = user
        
        return True, None
    
    def require_api_key(self, scopes: List[str] = None):
        """Decorator to require API key authentication."""
        def decorator(f):
            def wrapper(*args, **kwargs):
                valid, error = self.authenticate_request(scopes)
                if not valid:
                    from flask import jsonify
                    return jsonify({'error': 'Authentication failed', 'message': error}), 401
                return f(*args, **kwargs)
            
            wrapper.__name__ = f.__name__
            return wrapper
        
        return decorator


# Global API key service instance
api_key_service = APIKeyService()

# Global API key authenticator
api_key_authenticator = APIKeyAuthenticator(api_key_service)