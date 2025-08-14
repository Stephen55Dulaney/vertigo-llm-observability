"""
Enhanced Authentication Service

Comprehensive authentication service with JWT token management, 
session security, and advanced security features.
"""

import os
import jwt
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from flask import current_app, request, session, g
from flask_login import login_user, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from cryptography.fernet import Fernet
import logging
import json
import re

from app.models import User, db

logger = logging.getLogger(__name__)


class JWTTokenManager:
    """JWT token management with access and refresh tokens."""
    
    def __init__(self, app=None):
        self.secret_key = os.getenv('JWT_SECRET_KEY') or 'fallback-dev-secret-key'
        if app:
            self.secret_key = app.config.get('SECRET_KEY', self.secret_key)
        self.algorithm = 'HS256'
        
        # Token expiration times
        self.access_token_expiry = timedelta(minutes=15)  # Short-lived access tokens
        self.refresh_token_expiry = timedelta(days=7)     # Longer-lived refresh tokens
        self.remember_token_expiry = timedelta(days=30)   # Remember me tokens
        
        # Token issuer
        self.issuer = 'vertigo-debug-toolkit'
        
        # Encryption key for sensitive data
        fernet_key = os.getenv('FERNET_KEY')
        if not fernet_key:
            # Generate a key for development (not secure for production)
            fernet_key = Fernet.generate_key()
            logger.warning("Using generated Fernet key. Set FERNET_KEY environment variable for production.")
        
        try:
            self.cipher_suite = Fernet(fernet_key if isinstance(fernet_key, bytes) else fernet_key.encode())
        except Exception as e:
            logger.error(f"Failed to initialize encryption: {e}")
            # Fallback to no encryption (not recommended)
            self.cipher_suite = None
    
    def generate_access_token(self, user: User, scopes: List[str] = None) -> str:
        """Generate access token for user."""
        now = datetime.utcnow()
        payload = {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'is_admin': user.is_admin,
            'scopes': scopes or ['read', 'write'],
            'token_type': 'access',
            'iat': now,
            'exp': now + self.access_token_expiry,
            'iss': self.issuer,
            'jti': secrets.token_urlsafe(16)  # JWT ID for revocation
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def generate_refresh_token(self, user: User) -> str:
        """Generate refresh token for user."""
        now = datetime.utcnow()
        payload = {
            'user_id': user.id,
            'username': user.username,
            'token_type': 'refresh',
            'iat': now,
            'exp': now + self.refresh_token_expiry,
            'iss': self.issuer,
            'jti': secrets.token_urlsafe(16)
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def generate_remember_token(self, user: User) -> str:
        """Generate remember me token."""
        now = datetime.utcnow()
        payload = {
            'user_id': user.id,
            'username': user.username,
            'token_type': 'remember',
            'iat': now,
            'exp': now + self.remember_token_expiry,
            'iss': self.issuer,
            'jti': secrets.token_urlsafe(16)
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str, token_type: str = None) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            
            # Verify token type if specified
            if token_type and payload.get('token_type') != token_type:
                logger.warning(f"Token type mismatch: expected {token_type}, got {payload.get('token_type')}")
                return None
            
            # Verify issuer
            if payload.get('iss') != self.issuer:
                logger.warning(f"Invalid token issuer: {payload.get('iss')}")
                return None
            
            # Check if token is revoked (implement token blacklist if needed)
            if self._is_token_revoked(payload.get('jti')):
                logger.warning(f"Token is revoked: {payload.get('jti')}")
                return None
            
            return payload
        
        except jwt.ExpiredSignatureError:
            logger.debug("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            return None
        except Exception as e:
            logger.error(f"Error verifying token: {e}")
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[Tuple[str, str]]:
        """Generate new access token using refresh token."""
        payload = self.verify_token(refresh_token, 'refresh')
        if not payload:
            return None
        
        # Get user and verify they still exist and are active
        user = User.query.get(payload['user_id'])
        if not user or not user.is_active:
            return None
        
        # Generate new access token and refresh token
        new_access_token = self.generate_access_token(user)
        new_refresh_token = self.generate_refresh_token(user)
        
        # Optionally revoke old refresh token
        self._revoke_token(payload.get('jti'))
        
        return new_access_token, new_refresh_token
    
    def _is_token_revoked(self, jti: str) -> bool:
        """Check if token is revoked (implement with Redis or database)."""
        # TODO: Implement token blacklist
        # For now, return False (no revocation)
        return False
    
    def _revoke_token(self, jti: str):
        """Revoke token by adding to blacklist."""
        # TODO: Implement token revocation
        # Add jti to Redis blacklist or database
        pass
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data."""
        if not self.cipher_suite:
            return data  # No encryption available
        
        try:
            return self.cipher_suite.encrypt(data.encode()).decode()
        except Exception as e:
            logger.error(f"Error encrypting data: {e}")
            return data
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data."""
        if not self.cipher_suite:
            return encrypted_data  # No decryption available
        
        try:
            return self.cipher_suite.decrypt(encrypted_data.encode()).decode()
        except Exception as e:
            logger.error(f"Error decrypting data: {e}")
            return encrypted_data


class SessionSecurityManager:
    """Enhanced session security management."""
    
    def __init__(self):
        self.max_session_lifetime = timedelta(hours=8)
        self.session_refresh_interval = timedelta(minutes=30)
        self.max_concurrent_sessions = 5
    
    def create_secure_session(self, user: User, remember_me: bool = False) -> Dict[str, Any]:
        """Create secure session for user."""
        now = datetime.utcnow()
        
        # Generate session ID and security tokens
        session_id = secrets.token_urlsafe(32)
        csrf_token = secrets.token_urlsafe(32)
        
        # Session data
        session_data = {
            'user_id': user.id,
            'session_id': session_id,
            'csrf_token': csrf_token,
            'created_at': now.isoformat(),
            'last_activity': now.isoformat(),
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', '')[:200],
            'remember_me': remember_me,
            'expires_at': (now + self.max_session_lifetime).isoformat()
        }
        
        # Store session data
        session.update(session_data)
        session.permanent = remember_me
        
        # Update user last login
        user.last_login = now
        db.session.commit()
        
        logger.info(f"Secure session created for user {user.username}")
        
        return session_data
    
    def validate_session(self) -> Tuple[bool, Optional[str]]:
        """Validate current session security."""
        if not session or 'user_id' not in session:
            return False, "No valid session"
        
        now = datetime.utcnow()
        
        # Check session expiration
        expires_at = session.get('expires_at')
        if expires_at:
            try:
                expires_datetime = datetime.fromisoformat(expires_at)
                if now > expires_datetime:
                    return False, "Session expired"
            except ValueError:
                return False, "Invalid session expiration"
        
        # Check IP address consistency (optional, can cause issues with proxies)
        session_ip = session.get('ip_address')
        current_ip = request.remote_addr
        if session_ip and session_ip != current_ip:
            logger.warning(f"IP address mismatch for user {session.get('user_id')}: {session_ip} vs {current_ip}")
            # Don't fail the session, just log it
        
        # Check user agent consistency
        session_ua = session.get('user_agent', '')
        current_ua = request.headers.get('User-Agent', '')[:200]
        if session_ua and session_ua != current_ua:
            logger.warning(f"User agent mismatch for user {session.get('user_id')}")
            # Don't fail the session, just log it
        
        # Update last activity
        last_activity = session.get('last_activity')
        if last_activity:
            try:
                last_datetime = datetime.fromisoformat(last_activity)
                if now - last_datetime > self.session_refresh_interval:
                    session['last_activity'] = now.isoformat()
            except ValueError:
                pass
        
        return True, None
    
    def invalidate_session(self, session_id: str = None):
        """Invalidate session."""
        if session_id:
            # TODO: Invalidate specific session (implement with Redis or database)
            pass
        else:
            # Clear current session
            session.clear()
        
        logger.info("Session invalidated")
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get current session information."""
        if not session or 'user_id' not in session:
            return {}
        
        return {
            'session_id': session.get('session_id'),
            'user_id': session.get('user_id'),
            'created_at': session.get('created_at'),
            'last_activity': session.get('last_activity'),
            'expires_at': session.get('expires_at'),
            'remember_me': session.get('remember_me', False),
            'ip_address': session.get('ip_address')
        }


class PasswordSecurityManager:
    """Enhanced password security management."""
    
    def __init__(self):
        self.min_length = 12
        self.require_uppercase = True
        self.require_lowercase = True
        self.require_digits = True
        self.require_special = True
        self.max_age_days = 90
        self.password_history_count = 5
        
        # Common weak patterns
        self.weak_patterns = [
            r'password',
            r'123456',
            r'admin',
            r'qwerty',
            r'letmein',
            r'welcome',
            r'monkey',
            r'dragon',
            r'master',
            r'login'
        ]
        
        # Compile patterns for performance
        self.weak_regex = [re.compile(pattern, re.IGNORECASE) for pattern in self.weak_patterns]
    
    def validate_password_strength(self, password: str) -> Tuple[bool, List[str]]:
        """Validate password strength."""
        errors = []
        
        # Length check
        if len(password) < self.min_length:
            errors.append(f"Password must be at least {self.min_length} characters long")
        
        # Character type checks
        if self.require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        if self.require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        if self.require_digits and not re.search(r'\d', password):
            errors.append("Password must contain at least one digit")
        
        if self.require_special and not re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password):
            errors.append("Password must contain at least one special character")
        
        # Check for weak patterns
        for pattern in self.weak_regex:
            if pattern.search(password):
                errors.append(f"Password contains weak pattern: {pattern.pattern}")
        
        # Check for common sequences
        if self._contains_sequences(password):
            errors.append("Password contains sequential characters")
        
        # Check for repeated characters
        if self._contains_repetition(password):
            errors.append("Password contains too many repeated characters")
        
        return len(errors) == 0, errors
    
    def _contains_sequences(self, password: str) -> bool:
        """Check for sequential characters (123, abc, etc.)."""
        sequences = [
            'abcdefghijklmnopqrstuvwxyz',
            '0123456789',
            'qwertyuiop',
            'asdfghjkl',
            'zxcvbnm'
        ]
        
        password_lower = password.lower()
        
        for sequence in sequences:
            # Check forward sequences
            for i in range(len(sequence) - 2):
                if sequence[i:i+3] in password_lower:
                    return True
            
            # Check reverse sequences
            reverse_sequence = sequence[::-1]
            for i in range(len(reverse_sequence) - 2):
                if reverse_sequence[i:i+3] in password_lower:
                    return True
        
        return False
    
    def _contains_repetition(self, password: str) -> bool:
        """Check for excessive character repetition."""
        # Check for 3 or more consecutive identical characters
        for i in range(len(password) - 2):
            if password[i] == password[i+1] == password[i+2]:
                return True
        
        return False
    
    def generate_password_hash(self, password: str) -> str:
        """Generate secure password hash."""
        # Use higher cost factor for better security
        return generate_password_hash(password, method='pbkdf2:sha256:100000')
    
    def check_password_hash(self, password_hash: str, password: str) -> bool:
        """Check password against hash."""
        return check_password_hash(password_hash, password)
    
    def is_password_expired(self, user: User) -> bool:
        """Check if user's password has expired."""
        if not user.created_at:
            return False
        
        password_age = datetime.utcnow() - user.created_at
        return password_age.days > self.max_age_days
    
    def generate_secure_password(self, length: int = 16) -> str:
        """Generate cryptographically secure password."""
        import string
        
        # Character sets
        uppercase = string.ascii_uppercase
        lowercase = string.ascii_lowercase
        digits = string.digits
        special = "!@#$%^&*()_+-="
        
        # Ensure at least one character from each required set
        password_chars = []
        
        if self.require_uppercase:
            password_chars.append(secrets.choice(uppercase))
        
        if self.require_lowercase:
            password_chars.append(secrets.choice(lowercase))
        
        if self.require_digits:
            password_chars.append(secrets.choice(digits))
        
        if self.require_special:
            password_chars.append(secrets.choice(special))
        
        # Fill remaining length with random characters
        all_chars = uppercase + lowercase + digits + special
        for _ in range(length - len(password_chars)):
            password_chars.append(secrets.choice(all_chars))
        
        # Shuffle the characters
        secrets.SystemRandom().shuffle(password_chars)
        
        return ''.join(password_chars)


class AuthenticationService:
    """Main authentication service."""
    
    def __init__(self, app=None):
        self.jwt_manager = JWTTokenManager(app)
        self.session_manager = SessionSecurityManager()
        self.password_manager = PasswordSecurityManager()
        
        # Failed login tracking
        self.failed_logins = {}  # In production, use Redis
        self.max_failed_attempts = 5
        self.lockout_duration = timedelta(minutes=15)
    
    def authenticate_user(self, username: str, password: str, remember_me: bool = False) -> Tuple[bool, Optional[User], Optional[str]]:
        """Authenticate user with enhanced security."""
        # Check for account lockout
        if self.is_account_locked(username):
            return False, None, "Account temporarily locked due to too many failed attempts"
        
        # Find user
        user = User.query.filter_by(username=username).first()
        if not user:
            # Record failed attempt (even for non-existent users to prevent enumeration)
            self.record_failed_login(username)
            return False, None, "Invalid credentials"
        
        # Check if user is active
        if not user.is_active:
            return False, None, "Account is deactivated"
        
        # Verify password
        if not user.check_password(password):
            self.record_failed_login(username)
            return False, None, "Invalid credentials"
        
        # Check if password needs update
        if self.password_manager.is_password_expired(user):
            return False, user, "Password has expired and must be changed"
        
        # Clear failed login attempts
        self.clear_failed_logins(username)
        
        # Create secure session
        session_data = self.session_manager.create_secure_session(user, remember_me)
        
        # Log successful login
        logger.info(f"Successful login for user {username} from {request.remote_addr}")
        
        return True, user, None
    
    def is_account_locked(self, username: str) -> bool:
        """Check if account is locked due to failed attempts."""
        if username not in self.failed_logins:
            return False
        
        attempts = self.failed_logins[username]
        if attempts['count'] >= self.max_failed_attempts:
            # Check if lockout has expired
            if datetime.utcnow() - attempts['last_attempt'] > self.lockout_duration:
                del self.failed_logins[username]
                return False
            return True
        
        return False
    
    def record_failed_login(self, username: str):
        """Record failed login attempt."""
        now = datetime.utcnow()
        
        if username in self.failed_logins:
            # Check if we should reset the counter (after lockout period)
            if now - self.failed_logins[username]['last_attempt'] > self.lockout_duration:
                self.failed_logins[username] = {'count': 1, 'last_attempt': now}
            else:
                self.failed_logins[username]['count'] += 1
                self.failed_logins[username]['last_attempt'] = now
        else:
            self.failed_logins[username] = {'count': 1, 'last_attempt': now}
        
        logger.warning(f"Failed login attempt for {username} from {request.remote_addr}")
    
    def clear_failed_logins(self, username: str):
        """Clear failed login attempts for user."""
        self.failed_logins.pop(username, None)
    
    def change_password(self, user: User, old_password: str, new_password: str) -> Tuple[bool, List[str]]:
        """Change user password with validation."""
        # Verify old password
        if not user.check_password(old_password):
            return False, ["Current password is incorrect"]
        
        # Validate new password
        valid, errors = self.password_manager.validate_password_strength(new_password)
        if not valid:
            return False, errors
        
        # Check if new password is different from old
        if user.check_password(new_password):
            return False, ["New password must be different from current password"]
        
        # Set new password
        try:
            user.set_password(new_password)
            db.session.commit()
            logger.info(f"Password changed for user {user.username}")
            return True, []
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error changing password for user {user.username}: {e}")
            return False, ["Error updating password"]
    
    def generate_tokens(self, user: User) -> Dict[str, str]:
        """Generate JWT tokens for user."""
        return {
            'access_token': self.jwt_manager.generate_access_token(user),
            'refresh_token': self.jwt_manager.generate_refresh_token(user)
        }
    
    def get_security_info(self) -> Dict[str, Any]:
        """Get authentication security information."""
        return {
            'failed_login_attempts': len(self.failed_logins),
            'locked_accounts': sum(1 for attempts in self.failed_logins.values() 
                                 if attempts['count'] >= self.max_failed_attempts),
            'session_info': self.session_manager.get_session_info(),
            'password_requirements': {
                'min_length': self.password_manager.min_length,
                'require_uppercase': self.password_manager.require_uppercase,
                'require_lowercase': self.password_manager.require_lowercase,
                'require_digits': self.password_manager.require_digits,
                'require_special': self.password_manager.require_special,
                'max_age_days': self.password_manager.max_age_days
            }
        }


# Global authentication service instance - initialized in app factory
auth_service = None

def init_auth_service(app=None):
    """Initialize the auth service (called from app factory)"""
    global auth_service
    if auth_service is None:
        auth_service = AuthenticationService(app)
    return auth_service