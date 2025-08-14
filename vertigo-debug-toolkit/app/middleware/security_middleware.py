"""
Security Middleware

Comprehensive security middleware for request validation, sanitization,
CORS configuration, and request security monitoring.
"""

import os
import json
import re
from typing import Tuple, Dict, List, Any, Optional, Union
import bleach
from datetime import datetime, timedelta
from flask import request, jsonify, g, current_app
from werkzeug.datastructures import FileStorage
from urllib.parse import urlparse
import logging

logger = logging.getLogger(__name__)


class SecurityConfig:
    """Security configuration constants."""
    
    # Content Security Policy
    DEFAULT_CSP = {
        'default-src': "'self'",
        'script-src': "'self' 'unsafe-inline' 'unsafe-eval' cdn.jsdelivr.net cdnjs.cloudflare.com",
        'style-src': "'self' 'unsafe-inline' fonts.googleapis.com cdn.jsdelivr.net",
        'font-src': "'self' fonts.gstatic.com cdn.jsdelivr.net",
        'img-src': "'self' data: https:",
        'connect-src': "'self' wss: ws:",
        'frame-ancestors': "'none'",
        'base-uri': "'self'",
        'form-action': "'self'"
    }
    
    # CORS Configuration
    DEFAULT_CORS_ORIGINS = [
        'http://localhost:8080',
        'http://localhost:5000',
        'http://127.0.0.1:8080',
        'http://127.0.0.1:5000'
    ]
    
    # File Upload Configuration
    ALLOWED_EXTENSIONS = {'.txt', '.json', '.csv', '.log', '.md'}
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    # Request Validation
    MAX_JSON_SIZE = 1024 * 1024  # 1MB
    MAX_FORM_FIELDS = 50
    MAX_FIELD_LENGTH = 10000
    
    # Dangerous patterns to block
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'vbscript:',
        r'data:text/html',
        r'eval\s*\(',
        r'setTimeout\s*\(',
        r'setInterval\s*\(',
        r'Function\s*\(',
        r'\.innerHTML\s*=',
        r'document\.write',
        r'window\.location',
    ]


class RequestValidator:
    """Request validation and sanitization."""
    
    def __init__(self):
        self.config = SecurityConfig()
        
        # Compile dangerous patterns for performance
        self.dangerous_regex = [re.compile(pattern, re.IGNORECASE | re.DOTALL) 
                               for pattern in self.config.DANGEROUS_PATTERNS]
    
    def validate_request_size(self, request) -> bool:
        """Validate request size limits."""
        try:
            # Check Content-Length header
            content_length = request.content_length
            if content_length and content_length > self.config.MAX_JSON_SIZE:
                logger.warning(f"Request too large: {content_length} bytes from {request.remote_addr}")
                return False
            
            return True
        except Exception as e:
            logger.error(f"Error validating request size: {e}")
            return False
    
    def validate_content_type(self, request) -> bool:
        """Validate request content type."""
        allowed_types = [
            'application/json',
            'application/x-www-form-urlencoded',
            'multipart/form-data',
            'text/plain'
        ]
        
        content_type = request.content_type
        if content_type:
            # Extract base content type without parameters
            base_type = content_type.split(';')[0].strip()
            if base_type not in allowed_types:
                logger.warning(f"Suspicious content type: {content_type} from {request.remote_addr}")
                return False
        
        return True
    
    def sanitize_string(self, value: str) -> str:
        """Sanitize string input."""
        if not isinstance(value, str):
            return str(value)
        
        # Check for dangerous patterns
        for pattern in self.dangerous_regex:
            if pattern.search(value):
                logger.warning(f"Dangerous pattern detected in input: {pattern.pattern}")
                # Remove the dangerous content
                value = pattern.sub('', value)
        
        # Use bleach for HTML sanitization
        value = bleach.clean(value, tags=[], attributes={}, strip=True)
        
        # Limit string length
        if len(value) > self.config.MAX_FIELD_LENGTH:
            logger.warning(f"String too long, truncating: {len(value)} chars")
            value = value[:self.config.MAX_FIELD_LENGTH]
        
        return value
    
    def validate_json_data(self, data: Any) -> Tuple[bool, Any]:
        """Validate and sanitize JSON data recursively."""
        try:
            if isinstance(data, dict):
                if len(data) > self.config.MAX_FORM_FIELDS:
                    logger.warning(f"Too many form fields: {len(data)}")
                    return False, None
                
                sanitized = {}
                for key, value in data.items():
                    # Sanitize key
                    clean_key = self.sanitize_string(str(key))
                    
                    # Recursively validate value
                    valid, clean_value = self.validate_json_data(value)
                    if not valid:
                        return False, None
                    
                    sanitized[clean_key] = clean_value
                
                return True, sanitized
            
            elif isinstance(data, list):
                if len(data) > self.config.MAX_FORM_FIELDS:
                    logger.warning(f"Too many list items: {len(data)}")
                    return False, None
                
                sanitized = []
                for item in data:
                    valid, clean_item = self.validate_json_data(item)
                    if not valid:
                        return False, None
                    sanitized.append(clean_item)
                
                return True, sanitized
            
            elif isinstance(data, str):
                return True, self.sanitize_string(data)
            
            elif isinstance(data, (int, float, bool)) or data is None:
                return True, data
            
            else:
                # Unknown type, convert to string and sanitize
                return True, self.sanitize_string(str(data))
        
        except Exception as e:
            logger.error(f"Error validating JSON data: {e}")
            return False, None
    
    def validate_file_upload(self, file: FileStorage) -> Tuple[bool, str]:
        """Validate file upload."""
        if not file or not file.filename:
            return False, "No file provided"
        
        # Check file extension
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in self.config.ALLOWED_EXTENSIONS:
            return False, f"File type not allowed: {ext}"
        
        # Check file size (if available)
        if hasattr(file, 'content_length') and file.content_length:
            if file.content_length > self.config.MAX_FILE_SIZE:
                return False, f"File too large: {file.content_length} bytes"
        
        # Basic filename sanitization
        safe_filename = re.sub(r'[^\w\-_\.]', '', file.filename)
        if not safe_filename:
            return False, "Invalid filename"
        
        return True, safe_filename


class CORSManager:
    """CORS (Cross-Origin Resource Sharing) management."""
    
    def __init__(self):
        self.config = SecurityConfig()
        self.allowed_origins = set(self.config.DEFAULT_CORS_ORIGINS)
        
        # Load additional origins from environment
        env_origins = os.getenv('CORS_ALLOWED_ORIGINS', '')
        if env_origins:
            additional_origins = [origin.strip() for origin in env_origins.split(',')]
            self.allowed_origins.update(additional_origins)
    
    def is_origin_allowed(self, origin: str) -> bool:
        """Check if origin is allowed."""
        if not origin:
            return False
        
        # Parse origin to validate format
        try:
            parsed = urlparse(origin)
            if not parsed.scheme or not parsed.netloc:
                return False
        except Exception:
            return False
        
        # Check against allowed origins
        if origin in self.allowed_origins:
            return True
        
        # Check for wildcard matches (be careful with this in production)
        for allowed in self.allowed_origins:
            if allowed.endswith('*'):
                if origin.startswith(allowed[:-1]):
                    return True
        
        return False
    
    def get_cors_headers(self, origin: str = None) -> Dict[str, str]:
        """Get CORS headers for response."""
        headers = {}
        
        # Check origin
        request_origin = origin or request.headers.get('Origin')
        if request_origin and self.is_origin_allowed(request_origin):
            headers['Access-Control-Allow-Origin'] = request_origin
        else:
            # Default to first allowed origin for same-origin requests
            if self.allowed_origins:
                headers['Access-Control-Allow-Origin'] = list(self.allowed_origins)[0]
        
        # Standard CORS headers
        headers.update({
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With, X-API-Key',
            'Access-Control-Max-Age': '86400',  # 24 hours
            'Access-Control-Allow-Credentials': 'true'
        })
        
        return headers


class SecurityHeadersManager:
    """Security headers management."""
    
    def __init__(self):
        self.config = SecurityConfig()
    
    def get_security_headers(self, is_api: bool = False) -> Dict[str, str]:
        """Get security headers for response."""
        headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'X-Permitted-Cross-Domain-Policies': 'none'
        }
        
        # HSTS for production
        if not current_app.debug:
            headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        # CSP header (more restrictive for API endpoints)
        if is_api:
            headers['Content-Security-Policy'] = "default-src 'none'; frame-ancestors 'none';"
        else:
            csp_parts = []
            for directive, value in self.config.DEFAULT_CSP.items():
                csp_parts.append(f"{directive} {value}")
            headers['Content-Security-Policy'] = '; '.join(csp_parts)
        
        return headers


class SecurityMiddleware:
    """Main security middleware class."""
    
    def __init__(self, app=None):
        self.app = app
        self.validator = RequestValidator()
        self.cors_manager = CORSManager()
        self.headers_manager = SecurityHeadersManager()
        
        # Security event tracking
        self.blocked_requests = []
        self.suspicious_activities = []
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize middleware with Flask app."""
        self.app = app
        
        # Register before_request handler
        app.before_request(self.before_request)
        
        # Register after_request handler
        app.after_request(self.after_request)
        
        # Register OPTIONS handler for CORS preflight
        app.before_request(self.handle_preflight)
    
    def handle_preflight(self):
        """Handle CORS preflight requests."""
        if request.method == 'OPTIONS':
            headers = self.cors_manager.get_cors_headers()
            headers.update(self.headers_manager.get_security_headers(is_api=True))
            return '', 200, headers
    
    def before_request(self):
        """Security checks before processing request."""
        # Skip security checks for static files and health checks
        if (request.path.startswith('/static/') or 
            request.path.startswith('/favicon.ico') or
            request.path == '/health'):
            return
        
        # Log request for monitoring
        g.request_start_time = datetime.utcnow()
        g.request_id = f"{datetime.utcnow().timestamp()}_{request.remote_addr}"
        
        # Validate request size
        if not self.validator.validate_request_size(request):
            self._log_security_event('request_too_large', {
                'content_length': request.content_length,
                'ip': request.remote_addr,
                'path': request.path
            })
            return jsonify({'error': 'Request too large'}), 413
        
        # Validate content type
        if not self.validator.validate_content_type(request):
            self._log_security_event('invalid_content_type', {
                'content_type': request.content_type,
                'ip': request.remote_addr,
                'path': request.path
            })
            return jsonify({'error': 'Invalid content type'}), 415
        
        # Validate and sanitize JSON data
        if request.is_json and request.get_json(silent=True):
            try:
                data = request.get_json()
                valid, sanitized_data = self.validator.validate_json_data(data)
                if not valid:
                    self._log_security_event('invalid_json_data', {
                        'ip': request.remote_addr,
                        'path': request.path,
                        'data_keys': list(data.keys()) if isinstance(data, dict) else None
                    })
                    return jsonify({'error': 'Invalid request data'}), 400
                
                # Store sanitized data for use in views
                g.sanitized_json = sanitized_data
            except Exception as e:
                logger.error(f"Error processing JSON data: {e}")
                return jsonify({'error': 'Invalid JSON format'}), 400
        
        # Validate file uploads
        if request.files:
            for field_name, file in request.files.items():
                if file:  # Skip empty files
                    valid, message = self.validator.validate_file_upload(file)
                    if not valid:
                        self._log_security_event('invalid_file_upload', {
                            'filename': file.filename,
                            'field': field_name,
                            'message': message,
                            'ip': request.remote_addr,
                            'path': request.path
                        })
                        return jsonify({'error': f'File upload error: {message}'}), 400
        
        # Check for suspicious User-Agent
        user_agent = request.headers.get('User-Agent', '')
        if self._is_suspicious_user_agent(user_agent):
            self._log_security_event('suspicious_user_agent', {
                'user_agent': user_agent,
                'ip': request.remote_addr,
                'path': request.path
            })
    
    def after_request(self, response):
        """Security headers and logging after request processing."""
        # Skip for static files
        if request.path.startswith('/static/') or request.path.startswith('/favicon.ico'):
            return response
        
        # Add CORS headers
        cors_headers = self.cors_manager.get_cors_headers()
        for header, value in cors_headers.items():
            response.headers[header] = value
        
        # Add security headers
        is_api = request.path.startswith('/api/') or request.is_json
        security_headers = self.headers_manager.get_security_headers(is_api=is_api)
        for header, value in security_headers.items():
            response.headers[header] = value
        
        # Add rate limit headers if available
        if hasattr(g, 'rate_limit_result'):
            rate_limit = g.rate_limit_result
            response.headers['X-RateLimit-Limit'] = str(rate_limit.limit)
            response.headers['X-RateLimit-Remaining'] = str(rate_limit.remaining)
            response.headers['X-RateLimit-Reset'] = str(rate_limit.reset_time)
            
            if rate_limit.warning:
                response.headers['X-RateLimit-Warning'] = 'Approaching limit'
            
            if not rate_limit.allowed:
                response.headers['Retry-After'] = str(rate_limit.retry_after)
        
        # Log response time for monitoring
        if hasattr(g, 'request_start_time'):
            duration = (datetime.utcnow() - g.request_start_time).total_seconds() * 1000
            response.headers['X-Response-Time'] = f"{duration:.2f}ms"
        
        return response
    
    def _is_suspicious_user_agent(self, user_agent: str) -> bool:
        """Check for suspicious user agents."""
        suspicious_patterns = [
            r'sqlmap',
            r'nikto',
            r'nmap',
            r'masscan',
            r'whatweb',
            r'dirbuster',
            r'gobuster',
            r'<script',
            r'python-requests/(?!2\.[2-9])',  # Very old requests library
        ]
        
        if not user_agent:
            return True  # Empty user agent is suspicious
        
        for pattern in suspicious_patterns:
            if re.search(pattern, user_agent, re.IGNORECASE):
                return True
        
        return False
    
    def _log_security_event(self, event_type: str, details: Dict[str, Any]):
        """Log security events for monitoring."""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'type': event_type,
            'details': details,
            'request_id': getattr(g, 'request_id', None)
        }
        
        logger.warning(f"Security event: {event_type} - {json.dumps(event)}")
        
        # Store in memory for recent events (in production, send to monitoring system)
        self.suspicious_activities.append(event)
        
        # Keep only recent events (last 1000)
        if len(self.suspicious_activities) > 1000:
            self.suspicious_activities = self.suspicious_activities[-1000:]
    
    def get_security_metrics(self) -> Dict[str, Any]:
        """Get security metrics for monitoring."""
        return {
            'blocked_requests_count': len(self.blocked_requests),
            'suspicious_activities_count': len(self.suspicious_activities),
            'recent_events': self.suspicious_activities[-10:],  # Last 10 events
            'event_types': self._get_event_type_counts()
        }
    
    def _get_event_type_counts(self) -> Dict[str, int]:
        """Count events by type."""
        counts = {}
        for event in self.suspicious_activities:
            event_type = event.get('type', 'unknown')
            counts[event_type] = counts.get(event_type, 0) + 1
        return counts


# Global security middleware instance
security_middleware = SecurityMiddleware()