# Security Configuration Guide

## Overview

The Vertigo Debug Toolkit now includes comprehensive security enhancements including API rate limiting, advanced authentication, security monitoring, and threat detection. This guide covers configuration and usage of all security features.

## Security Components

### 1. API Rate Limiting Service

**Location**: `app/services/rate_limiter.py`

Features:
- Redis-backed rate limiting with memory fallback
- Multiple rate limiting strategies (per-user, per-IP, per-endpoint)
- User tier-based limits (free, premium, admin)
- Rate limit headers and proper HTTP responses
- Admin bypass mechanisms

#### Configuration

```python
# Environment Variables
REDIS_URL=redis://localhost:6379/0  # Redis connection for rate limiting

# Rate Limit Tiers (configured in code)
FREE_TIER = {
    'requests_per_hour': 100,
    'requests_per_minute': 10
}

PREMIUM_TIER = {
    'requests_per_hour': 500,
    'requests_per_minute': 50
}

ADMIN_TIER = {
    'requests_per_hour': 2000,
    'requests_per_minute': 100
}
```

#### Usage

```python
from app.services.rate_limiter import rate_limiter

# Check rate limits
result = rate_limiter.check_rate_limit('/api/endpoint')
if not result.allowed:
    return jsonify({'error': 'Rate limit exceeded'}), 429

# Get rate limit status
status = rate_limiter.get_rate_limit_status(user, endpoint)

# Reset limits (admin only)
rate_limiter.reset_user_limits(user_id)
```

### 2. Security Middleware

**Location**: `app/middleware/security_middleware.py`

Features:
- Request validation and sanitization
- CORS configuration with origin validation
- Content Security Policy (CSP) headers
- Request size limiting
- File upload security
- Malicious input detection

#### Configuration

```python
# CORS Configuration
CORS_ALLOWED_ORIGINS=http://localhost:8080,http://localhost:5000

# Content Security Policy
DEFAULT_CSP = {
    'default-src': "'self'",
    'script-src': "'self' 'unsafe-inline' 'unsafe-eval'",
    'style-src': "'self' 'unsafe-inline'",
    'img-src': "'self' data: https:",
    'connect-src': "'self' wss: ws:",
}

# Request Limits
MAX_JSON_SIZE = 1024 * 1024  # 1MB
MAX_FORM_FIELDS = 50
MAX_FIELD_LENGTH = 10000
```

### 3. Enhanced Authentication

**Location**: `app/services/auth_service.py`

Features:
- JWT token management with refresh tokens
- Session security improvements
- Password strength validation
- Account lockout protection
- Multi-factor authentication preparation

#### Configuration

```python
# JWT Configuration
JWT_SECRET_KEY=your-jwt-secret-key
FERNET_KEY=your-fernet-encryption-key

# Password Requirements
MIN_PASSWORD_LENGTH = 12
REQUIRE_UPPERCASE = True
REQUIRE_LOWERCASE = True
REQUIRE_DIGITS = True
REQUIRE_SPECIAL_CHARS = True
PASSWORD_MAX_AGE_DAYS = 90

# Account Lockout
MAX_FAILED_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15
```

#### Usage

```python
from app.services.auth_service import auth_service

# Authenticate user
success, user, error = auth_service.authenticate_user(username, password, remember_me)

# Generate JWT tokens
tokens = auth_service.generate_tokens(user)
access_token = tokens['access_token']
refresh_token = tokens['refresh_token']

# Change password
success, errors = auth_service.change_password(user, old_password, new_password)
```

### 4. API Key Authentication

**Location**: `app/services/api_key_service.py`

Features:
- Secure API key generation and management
- Scope-based permissions
- Rate limiting integration
- Usage tracking and analytics
- Key expiration and revocation

#### Configuration

```python
# API Key Scopes
AVAILABLE_SCOPES = [
    'read', 'write', 'admin', 'analytics', 
    'prompts', 'performance', 'costs', 'sync'
]

# Default Scopes by Role
ADMIN_SCOPES = ['read', 'write', 'admin', 'analytics', 'prompts', 'performance', 'costs', 'sync']
USER_SCOPES = ['read', 'write', 'analytics', 'prompts']
READONLY_SCOPES = ['read', 'analytics']
```

#### Usage

```python
from app.services.api_key_service import api_key_service, api_key_authenticator

# Generate API key
api_key, key_id = api_key_service.generate_api_key(
    user=current_user,
    name="My API Key",
    scopes=['read', 'write'],
    expires_days=30,
    rate_limit_tier='premium'
)

# Authenticate API request
@api_key_authenticator.require_api_key(['read'])
def api_endpoint():
    return jsonify({'data': 'success'})

# Check API key permissions
has_permission = api_key_service.check_api_key_scope(api_key_info, 'write')
```

### 5. Security Monitoring

**Location**: `app/services/security_monitor.py`

Features:
- Failed authentication tracking
- Suspicious activity detection
- Real-time security event logging
- IP reputation analysis
- Automated threat response

#### Configuration

```python
# Detection Thresholds
FAILED_LOGIN_ATTEMPTS = 5
FAILED_LOGIN_WINDOW = 300  # 5 minutes
BRUTE_FORCE_THRESHOLD = 10
SUSPICIOUS_IP_THRESHOLD = 20
RATE_LIMIT_VIOLATIONS = 3

# Data Retention
SECURITY_DATA_RETENTION_DAYS = 30
CRITICAL_EVENT_RETENTION_DAYS = 90
```

#### Usage

```python
from app.services.security_monitor import security_monitor

# Record security events
security_monitor.record_login_attempt(username, success=False, failure_reason="invalid_password")

security_monitor.record_security_event(
    event_type="malicious_input",
    description="XSS attempt detected",
    severity="high",
    event_data={'pattern': '<script>', 'field': 'comment'}
)

# Analyze IP reputation
analysis = security_monitor.analyze_ip_reputation("192.168.1.100")

# Get security dashboard data
dashboard_data = security_monitor.get_security_dashboard_data()
```

## Security Headers

The application automatically applies security headers:

```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
Content-Security-Policy: default-src 'self'; script-src 'self' 'unsafe-inline'
Referrer-Policy: strict-origin-when-cross-origin
```

## Database Security

### Security Models

New database tables for security tracking:

- `api_keys` - API key storage and metadata
- `api_key_usage` - API key usage logging
- `security_events` - Security event tracking
- `login_attempts` - Login attempt monitoring
- `session_security` - Session security tracking
- `rate_limit_violations` - Rate limit violation logs
- `security_configuration` - Security settings

### Migration

Run database migration to create security tables:

```bash
cd vertigo-debug-toolkit
python -c "from app import create_app, db; app = create_app(); app.app_context().push(); db.create_all()"
```

## Security Dashboard

Access the security dashboard at: `http://localhost:8080/security/dashboard`

Features:
- Real-time security metrics
- Failed login tracking
- Rate limit violation monitoring
- Suspicious IP analysis
- Security event timeline
- Threat level distribution

## API Endpoints

### Security Management

```
GET    /security/dashboard                    - Security dashboard
GET    /security/api/events                   - List security events
GET    /security/api/ip-analysis/<ip>         - Analyze IP address
GET    /security/api/api-keys                 - List API keys
POST   /security/api/api-keys                 - Create API key
DELETE /security/api/api-keys/<key_id>        - Revoke API key
GET    /security/api/rate-limits/status       - Rate limit status
POST   /security/api/rate-limits/reset        - Reset rate limits (admin)
POST   /security/api/change-password          - Change password
GET    /security/api/security-info            - Security information
GET    /security/api/metrics                  - Security metrics (admin)
POST   /security/api/cleanup                  - Clean old data (admin)
```

### API Authentication

Use API keys in requests:

```bash
# Using Authorization header
curl -H "Authorization: Bearer vdb_abc123.def456ghi789" http://localhost:8080/api/endpoint

# Using X-API-Key header
curl -H "X-API-Key: vdb_abc123.def456ghi789" http://localhost:8080/api/endpoint
```

## Production Security Checklist

### Environment Variables

Ensure these are set in production:

```bash
# Core Security
FLASK_SECRET_KEY=your-strong-secret-key
JWT_SECRET_KEY=your-jwt-secret-key  
FERNET_KEY=your-fernet-encryption-key

# Redis (for rate limiting)
REDIS_URL=redis://your-redis-server:6379/0

# CORS
CORS_ALLOWED_ORIGINS=https://your-domain.com

# Database
DATABASE_URL=postgresql://user:password@host:port/database
```

### SSL/TLS Configuration

- Use HTTPS in production
- Enable HSTS headers
- Configure proper SSL certificates
- Use secure cookie settings

### Rate Limiting

- Configure Redis for production use
- Set appropriate rate limits for your use case
- Monitor rate limit violations
- Implement IP blocking for repeat offenders

### Monitoring

- Set up log aggregation (ELK stack, Splunk, etc.)
- Configure alerting for critical security events
- Monitor failed authentication attempts
- Track suspicious IP activity

### Database Security

- Use encrypted database connections
- Implement regular backups
- Set up database access logging
- Use strong database passwords

### Access Control

- Regularly audit user accounts
- Implement role-based access control
- Remove inactive user accounts
- Monitor privileged account usage

## Troubleshooting

### Rate Limiting Issues

If rate limiting isn't working:

1. Check Redis connection:
   ```python
   from app.services.rate_limiter import rate_limiter
   rate_limiter.redis_client.ping()
   ```

2. Check logs for rate limiting errors
3. Verify rate limit configuration
4. Test with different user tiers

### Authentication Problems

For authentication issues:

1. Check password requirements in logs
2. Verify JWT secret key configuration
3. Check account lockout status
4. Review security event logs

### Security Monitoring

If security monitoring isn't capturing events:

1. Check database connectivity
2. Verify security event logging is enabled
3. Check background processor status
4. Review error logs for exceptions

## Security Best Practices

1. **Regular Updates**: Keep all dependencies updated
2. **Monitoring**: Implement comprehensive logging and monitoring
3. **Access Control**: Use principle of least privilege
4. **Incident Response**: Have a security incident response plan
5. **Regular Audits**: Conduct security audits and penetration testing
6. **Backup**: Maintain secure, regular backups
7. **Training**: Train users on security best practices

## Support

For security-related issues:

1. Check logs in `/security/api/events`
2. Review security dashboard metrics
3. Analyze suspicious IP activity
4. Contact system administrators for critical issues

---

**Note**: This security implementation provides enterprise-grade security features. Regular monitoring and maintenance are essential for optimal security posture.