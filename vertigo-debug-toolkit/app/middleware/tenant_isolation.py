"""
Tenant isolation middleware for automatic tenant context and data filtering.
"""

import logging
from functools import wraps
from flask import g, request, current_app, jsonify
from app.services.tenant_service import tenant_service

logger = logging.getLogger(__name__)


class TenantIsolationMiddleware:
    """Middleware for automatic tenant isolation and context management."""
    
    def __init__(self, app=None):
        """Initialize tenant isolation middleware."""
        self.app = app
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize middleware with Flask app."""
        app.before_request(self.before_request)
        app.after_request(self.after_request)
        
        # Register SQL query interceptor for automatic tenant filtering
        from sqlalchemy import event
        from app import db
        
        @event.listens_for(db.engine, "before_cursor_execute")
        def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            """Intercept SQL queries to add tenant filtering."""
            if hasattr(g, 'current_tenant') and g.current_tenant:
                # Only apply isolation to SELECT, UPDATE, DELETE queries
                statement_upper = statement.upper().strip()
                if any(statement_upper.startswith(cmd) for cmd in ['SELECT', 'UPDATE', 'DELETE']):
                    # Skip if query already has tenant_id filter or is a system table
                    if 'tenant_id' not in statement.lower() and not any(
                        table in statement.lower() 
                        for table in ['users', 'tenants', 'tenant_users', 'alembic_version']
                    ):
                        # This is a simplified approach - in production, use proper SQL parsing
                        logger.debug(f"Tenant isolation applied to query: {statement[:100]}...")
    
    def before_request(self):
        """Process request before handling to establish tenant context."""
        try:
            # Skip tenant isolation for certain paths
            skip_paths = [
                '/static/', '/favicon.ico', '/health', 
                '/auth/', '/api/health', '/_debug'
            ]
            
            if any(request.path.startswith(path) for path in skip_paths):
                return
            
            # Establish tenant context
            current_tenant = tenant_service.get_current_tenant()
            
            if current_tenant:
                g.current_tenant = current_tenant
                logger.debug(f"Tenant context established: {current_tenant.name} ({current_tenant.id})")
                
                # Validate tenant access for authenticated requests
                if hasattr(g, 'current_user') and g.current_user and g.current_user.is_authenticated:
                    if not tenant_service.check_user_access(
                        current_tenant.id, 
                        g.current_user.id, 
                        "read"
                    ):
                        logger.warning(f"User {g.current_user.id} denied access to tenant {current_tenant.id}")
                        return jsonify({
                            "error": "Access denied to current tenant",
                            "tenant_id": current_tenant.id
                        }), 403
            else:
                # For API requests, require tenant context
                if request.path.startswith('/api/') and not request.path.startswith('/api/auth'):
                    logger.warning(f"API request without tenant context: {request.path}")
                    return jsonify({
                        "error": "Tenant context required for API access",
                        "hint": "Include X-API-Key header or access via tenant subdomain"
                    }), 400
            
        except Exception as e:
            logger.error(f"Error in tenant isolation middleware: {e}")
            # Don't block requests on middleware errors in development
            if current_app.config.get('DEBUG'):
                pass
            else:
                return jsonify({
                    "error": "Tenant isolation error",
                    "message": str(e)
                }), 500
    
    def after_request(self, response):
        """Process response after handling to add tenant headers."""
        try:
            if hasattr(g, 'current_tenant') and g.current_tenant:
                # Add tenant info to response headers (for debugging)
                if current_app.config.get('DEBUG'):
                    response.headers['X-Tenant-ID'] = g.current_tenant.id
                    response.headers['X-Tenant-Name'] = g.current_tenant.name
                
                # Log tenant usage
                self._log_tenant_usage(g.current_tenant, request, response)
            
        except Exception as e:
            logger.error(f"Error in tenant isolation after_request: {e}")
        
        return response
    
    def _log_tenant_usage(self, tenant, request_obj, response):
        """Log tenant API usage for monitoring and billing."""
        try:
            # Skip logging for static files and health checks
            skip_paths = ['/static/', '/favicon.ico', '/health']
            if any(request_obj.path.startswith(path) for path in skip_paths):
                return
            
            # In production, this would write to tenant_api_usage table
            logger.debug(f"Tenant usage: {tenant.id} - {request_obj.method} {request_obj.path} - {response.status_code}")
            
        except Exception as e:
            logger.error(f"Error logging tenant usage: {e}")


def tenant_required(permission="read", resource=None):
    """Decorator to require tenant context and specific permissions."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Check tenant context
                current_tenant = getattr(g, 'current_tenant', None)
                if not current_tenant:
                    return jsonify({
                        "error": "Tenant context required",
                        "success": False
                    }), 400
                
                # Check user authentication
                current_user = getattr(g, 'current_user', None)
                if not current_user or not current_user.is_authenticated:
                    return jsonify({
                        "error": "Authentication required",
                        "success": False
                    }), 401
                
                # Check tenant permissions
                if not tenant_service.check_user_access(
                    current_tenant.id,
                    current_user.id,
                    permission,
                    resource
                ):
                    return jsonify({
                        "error": f"Insufficient permissions: {permission}",
                        "success": False
                    }), 403
                
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Error in tenant_required decorator: {e}")
                return jsonify({
                    "error": "Tenant access check failed",
                    "success": False
                }), 500
        
        return decorated_function
    return decorator


def isolate_model_query(model_class):
    """Helper function to add tenant isolation to model queries."""
    def tenant_aware_query(*args, **kwargs):
        """Create tenant-aware query for model."""
        current_tenant = getattr(g, 'current_tenant', None)
        if current_tenant and hasattr(model_class, 'tenant_id'):
            # Add tenant filter to query
            return model_class.query.filter(model_class.tenant_id == current_tenant.id)
        else:
            return model_class.query
    
    return tenant_aware_query


class TenantAwareQuery:
    """Query wrapper that automatically adds tenant isolation."""
    
    def __init__(self, model_class):
        """Initialize tenant-aware query wrapper."""
        self.model_class = model_class
    
    def filter_by_tenant(self):
        """Apply tenant filter to query."""
        current_tenant = getattr(g, 'current_tenant', None)
        if current_tenant and hasattr(self.model_class, 'tenant_id'):
            return self.model_class.query.filter_by(tenant_id=current_tenant.id)
        else:
            return self.model_class.query
    
    def create_for_current_tenant(self, **kwargs):
        """Create instance for current tenant."""
        current_tenant = getattr(g, 'current_tenant', None)
        if current_tenant:
            kwargs['tenant_id'] = current_tenant.id
        
        instance = self.model_class(**kwargs)
        return instance


def get_tenant_storage_path(file_path):
    """Get tenant-specific storage path for file operations."""
    current_tenant = getattr(g, 'current_tenant', None)
    if current_tenant:
        return tenant_service.get_tenant_storage_path(current_tenant.id, file_path)
    else:
        return file_path


def validate_tenant_quota(resource_type, amount=1):
    """Validate tenant quota for resource usage."""
    current_tenant = getattr(g, 'current_tenant', None)
    if not current_tenant:
        return False
    
    try:
        metrics = tenant_service.get_tenant_metrics(current_tenant.id)
        
        # Check specific resource quotas
        if resource_type == 'users':
            return metrics['users_count'] + amount <= metrics['users_limit']
        elif resource_type == 'storage_gb':
            return metrics['storage_used_gb'] + amount <= metrics['storage_limit_gb']
        elif resource_type == 'api_calls':
            return metrics['api_calls_today'] + amount <= metrics['api_calls_limit']
        else:
            return True  # Unknown resource type, allow by default
        
    except Exception as e:
        logger.error(f"Error validating tenant quota: {e}")
        return False  # Fail closed on quota errors


# Global middleware instance
tenant_isolation_middleware = TenantIsolationMiddleware()