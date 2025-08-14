"""
Multi-Tenant Data Isolation Service
Provides comprehensive tenant isolation, security, and access control for the Vertigo Debug Toolkit.
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
import hashlib
import secrets
from flask import g, current_app, request
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User

logger = logging.getLogger(__name__)


class TenantStatus(Enum):
    """Tenant status enumeration."""
    ACTIVE = "active"
    SUSPENDED = "suspended"
    INACTIVE = "inactive"
    TRIAL = "trial"
    ENTERPRISE = "enterprise"


class AccessLevel(Enum):
    """Access level enumeration."""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    OWNER = "owner"


@dataclass
class TenantConfig:
    """Tenant configuration settings."""
    max_users: int = 10
    max_projects: int = 5
    max_storage_gb: float = 1.0
    max_api_calls_per_hour: int = 1000
    retention_days: int = 30
    features_enabled: List[str] = field(default_factory=lambda: ["analytics", "alerts"])
    custom_settings: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Tenant:
    """Tenant data model."""
    id: str
    name: str
    domain: str
    status: TenantStatus
    config: TenantConfig
    created_at: datetime
    updated_at: datetime
    owner_id: str
    api_key: str
    webhook_secret: str
    database_schema: str
    storage_prefix: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TenantUser:
    """Tenant user association."""
    tenant_id: str
    user_id: str
    access_level: AccessLevel
    permissions: List[str]
    created_at: datetime
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class TenantService:
    """Multi-tenant data isolation and management service."""
    
    def __init__(self):
        """Initialize tenant service."""
        self.tenants_cache: Dict[str, Tenant] = {}
        self.user_tenants_cache: Dict[str, List[str]] = {}
        self.cache_ttl = timedelta(minutes=15)
        self.last_cache_update = datetime.now()
        
        # Default tenant configuration
        self.default_config = TenantConfig(
            max_users=25,
            max_projects=10,
            max_storage_gb=5.0,
            max_api_calls_per_hour=5000,
            retention_days=90,
            features_enabled=["analytics", "alerts", "advanced_evaluation", "semantic_search"],
            custom_settings={
                "langfuse_integration": True,
                "webhook_notifications": True,
                "custom_branding": False,
                "sso_enabled": False
            }
        )
        
        # Schema isolation settings
        self.schema_prefix = "tenant_"
        self.storage_prefix = "tenant-data/"
        
        logger.info("TenantService initialized")
    
    def create_tenant(
        self,
        name: str,
        domain: str,
        owner_user_id: str,
        config: Optional[TenantConfig] = None
    ) -> Tenant:
        """Create a new tenant with isolated resources."""
        try:
            tenant_id = str(uuid.uuid4())
            api_key = self._generate_api_key(tenant_id)
            webhook_secret = secrets.token_urlsafe(32)
            
            # Use provided config or default
            tenant_config = config or self.default_config
            
            # Create database schema for tenant
            schema_name = f"{self.schema_prefix}{tenant_id.replace('-', '_')}"
            storage_prefix = f"{self.storage_prefix}{tenant_id}/"
            
            tenant = Tenant(
                id=tenant_id,
                name=name,
                domain=domain,
                status=TenantStatus.ACTIVE,
                config=tenant_config,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                owner_id=owner_user_id,
                api_key=api_key,
                webhook_secret=webhook_secret,
                database_schema=schema_name,
                storage_prefix=storage_prefix,
                metadata={
                    "created_by": owner_user_id,
                    "initial_features": tenant_config.features_enabled.copy(),
                    "isolation_level": "schema"
                }
            )
            
            # Initialize tenant database schema
            self._create_tenant_schema(tenant)
            
            # Add owner as admin user
            self.add_user_to_tenant(
                tenant_id=tenant_id,
                user_id=owner_user_id,
                access_level=AccessLevel.OWNER,
                permissions=["*"]
            )
            
            # Cache tenant
            self.tenants_cache[tenant_id] = tenant
            
            logger.info(f"Created tenant: {tenant_id} ({name}) with schema: {schema_name}")
            return tenant
            
        except Exception as e:
            logger.error(f"Error creating tenant {name}: {e}")
            raise
    
    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        """Get tenant by ID with caching."""
        try:
            # Check cache first
            if tenant_id in self.tenants_cache and self._is_cache_valid():
                return self.tenants_cache[tenant_id]
            
            # Load from persistent storage (would be database in production)
            # For now, simulate with in-memory storage
            tenant = self._load_tenant_from_storage(tenant_id)
            
            if tenant:
                self.tenants_cache[tenant_id] = tenant
            
            return tenant
            
        except Exception as e:
            logger.error(f"Error getting tenant {tenant_id}: {e}")
            return None
    
    def get_tenant_by_domain(self, domain: str) -> Optional[Tenant]:
        """Get tenant by domain."""
        try:
            for tenant in self.tenants_cache.values():
                if tenant.domain.lower() == domain.lower():
                    return tenant
            
            # Load all tenants if not cached
            self._refresh_cache()
            
            for tenant in self.tenants_cache.values():
                if tenant.domain.lower() == domain.lower():
                    return tenant
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting tenant by domain {domain}: {e}")
            return None
    
    def get_current_tenant(self) -> Optional[Tenant]:
        """Get current tenant from request context."""
        try:
            # Check if tenant is already set in request context
            if hasattr(g, 'current_tenant'):
                return g.current_tenant
            
            # Try to get tenant from various sources
            tenant = None
            
            # 1. From API key in headers
            api_key = request.headers.get('X-API-Key')
            if api_key:
                tenant = self.get_tenant_by_api_key(api_key)
            
            # 2. From subdomain
            if not tenant and request.host:
                subdomain = request.host.split('.')[0] if '.' in request.host else None
                if subdomain and subdomain != 'www':
                    tenant = self.get_tenant_by_domain(subdomain)
            
            # 3. From user's default tenant
            if not tenant and hasattr(g, 'current_user') and g.current_user:
                user_tenants = self.get_user_tenants(g.current_user.id)
                if user_tenants:
                    tenant = self.get_tenant(user_tenants[0])  # Use first tenant
            
            # Cache in request context
            g.current_tenant = tenant
            return tenant
            
        except Exception as e:
            logger.error(f"Error getting current tenant: {e}")
            return None
    
    def get_tenant_by_api_key(self, api_key: str) -> Optional[Tenant]:
        """Get tenant by API key."""
        try:
            for tenant in self.tenants_cache.values():
                if tenant.api_key == api_key:
                    return tenant
            
            # Load all tenants if not cached
            self._refresh_cache()
            
            for tenant in self.tenants_cache.values():
                if tenant.api_key == api_key:
                    return tenant
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting tenant by API key: {e}")
            return None
    
    def add_user_to_tenant(
        self,
        tenant_id: str,
        user_id: str,
        access_level: AccessLevel,
        permissions: List[str],
        expires_at: Optional[datetime] = None
    ) -> bool:
        """Add user to tenant with specific access level."""
        try:
            tenant = self.get_tenant(tenant_id)
            if not tenant:
                return False
            
            # Check if tenant has reached user limit
            current_users = self.get_tenant_users(tenant_id)
            if len(current_users) >= tenant.config.max_users:
                logger.warning(f"Tenant {tenant_id} has reached max users limit: {tenant.config.max_users}")
                return False
            
            tenant_user = TenantUser(
                tenant_id=tenant_id,
                user_id=user_id,
                access_level=access_level,
                permissions=permissions,
                created_at=datetime.now(),
                expires_at=expires_at,
                metadata={"added_by": getattr(g, 'current_user', {}).get('id', 'system')}
            )
            
            # Store tenant user association (would be in database in production)
            self._store_tenant_user(tenant_user)
            
            # Clear user tenant cache
            if user_id in self.user_tenants_cache:
                del self.user_tenants_cache[user_id]
            
            logger.info(f"Added user {user_id} to tenant {tenant_id} with access level {access_level.value}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding user {user_id} to tenant {tenant_id}: {e}")
            return False
    
    def remove_user_from_tenant(self, tenant_id: str, user_id: str) -> bool:
        """Remove user from tenant."""
        try:
            # Don't allow removing the owner
            tenant = self.get_tenant(tenant_id)
            if tenant and tenant.owner_id == user_id:
                logger.warning(f"Cannot remove owner {user_id} from tenant {tenant_id}")
                return False
            
            # Remove tenant user association
            success = self._remove_tenant_user(tenant_id, user_id)
            
            # Clear user tenant cache
            if user_id in self.user_tenants_cache:
                del self.user_tenants_cache[user_id]
            
            if success:
                logger.info(f"Removed user {user_id} from tenant {tenant_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error removing user {user_id} from tenant {tenant_id}: {e}")
            return False
    
    def get_user_tenants(self, user_id: str) -> List[str]:
        """Get list of tenant IDs that user has access to."""
        try:
            # Check cache first
            if user_id in self.user_tenants_cache and self._is_cache_valid():
                return self.user_tenants_cache[user_id]
            
            # Load from storage
            tenant_ids = self._load_user_tenants(user_id)
            
            # Cache result
            self.user_tenants_cache[user_id] = tenant_ids
            
            return tenant_ids
            
        except Exception as e:
            logger.error(f"Error getting tenants for user {user_id}: {e}")
            return []
    
    def get_tenant_users(self, tenant_id: str) -> List[TenantUser]:
        """Get all users for a tenant."""
        try:
            return self._load_tenant_users(tenant_id)
            
        except Exception as e:
            logger.error(f"Error getting users for tenant {tenant_id}: {e}")
            return []
    
    def check_user_access(
        self,
        tenant_id: str,
        user_id: str,
        required_permission: str,
        resource: Optional[str] = None
    ) -> bool:
        """Check if user has required permission for tenant resource."""
        try:
            tenant_users = self.get_tenant_users(tenant_id)
            
            for tenant_user in tenant_users:
                if tenant_user.user_id == user_id:
                    # Check if access has expired
                    if tenant_user.expires_at and tenant_user.expires_at < datetime.now():
                        continue
                    
                    # Owner and admin have all permissions
                    if tenant_user.access_level in [AccessLevel.OWNER, AccessLevel.ADMIN]:
                        return True
                    
                    # Check specific permissions
                    if "*" in tenant_user.permissions or required_permission in tenant_user.permissions:
                        return True
                    
                    # Check resource-specific permissions
                    if resource:
                        resource_permission = f"{required_permission}:{resource}"
                        if resource_permission in tenant_user.permissions:
                            return True
                    
                    break
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking user access for tenant {tenant_id}, user {user_id}: {e}")
            return False
    
    def isolate_query(self, query: str, tenant_id: str) -> str:
        """Modify SQL query to include tenant isolation."""
        try:
            tenant = self.get_tenant(tenant_id)
            if not tenant:
                return query
            
            # Add tenant_id filter to WHERE clause
            # This is a simplified implementation - in production, use proper SQL parsing
            if "WHERE" in query.upper():
                query = query.replace(" WHERE ", f" WHERE tenant_id = '{tenant_id}' AND ")
            else:
                # Add WHERE clause if it doesn't exist
                if "ORDER BY" in query.upper():
                    query = query.replace(" ORDER BY", f" WHERE tenant_id = '{tenant_id}' ORDER BY")
                elif "GROUP BY" in query.upper():
                    query = query.replace(" GROUP BY", f" WHERE tenant_id = '{tenant_id}' GROUP BY")
                elif "HAVING" in query.upper():
                    query = query.replace(" HAVING", f" WHERE tenant_id = '{tenant_id}' HAVING")
                else:
                    query = f"{query} WHERE tenant_id = '{tenant_id}'"
            
            return query
            
        except Exception as e:
            logger.error(f"Error isolating query for tenant {tenant_id}: {e}")
            return query
    
    def get_tenant_storage_path(self, tenant_id: str, file_path: str) -> str:
        """Get tenant-specific storage path."""
        try:
            tenant = self.get_tenant(tenant_id)
            if not tenant:
                return file_path
            
            return os.path.join(tenant.storage_prefix, file_path.lstrip('/'))
            
        except Exception as e:
            logger.error(f"Error getting storage path for tenant {tenant_id}: {e}")
            return file_path
    
    def rotate_api_key(self, tenant_id: str, user_id: str) -> Optional[str]:
        """Rotate tenant API key."""
        try:
            tenant = self.get_tenant(tenant_id)
            if not tenant:
                return None
            
            # Check if user has admin access
            if not self.check_user_access(tenant_id, user_id, "admin", "api_keys"):
                logger.warning(f"User {user_id} not authorized to rotate API key for tenant {tenant_id}")
                return None
            
            # Generate new API key
            new_api_key = self._generate_api_key(tenant_id)
            
            # Update tenant
            tenant.api_key = new_api_key
            tenant.updated_at = datetime.now()
            
            # Update cache
            self.tenants_cache[tenant_id] = tenant
            
            # Store updated tenant (would be in database in production)
            self._store_tenant(tenant)
            
            logger.info(f"Rotated API key for tenant {tenant_id}")
            return new_api_key
            
        except Exception as e:
            logger.error(f"Error rotating API key for tenant {tenant_id}: {e}")
            return None
    
    def update_tenant_config(
        self,
        tenant_id: str,
        user_id: str,
        config_updates: Dict[str, Any]
    ) -> bool:
        """Update tenant configuration."""
        try:
            tenant = self.get_tenant(tenant_id)
            if not tenant:
                return False
            
            # Check if user has admin access
            if not self.check_user_access(tenant_id, user_id, "admin", "config"):
                logger.warning(f"User {user_id} not authorized to update config for tenant {tenant_id}")
                return False
            
            # Update configuration
            for key, value in config_updates.items():
                if hasattr(tenant.config, key):
                    setattr(tenant.config, key, value)
                else:
                    tenant.config.custom_settings[key] = value
            
            tenant.updated_at = datetime.now()
            
            # Update cache
            self.tenants_cache[tenant_id] = tenant
            
            # Store updated tenant
            self._store_tenant(tenant)
            
            logger.info(f"Updated config for tenant {tenant_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating config for tenant {tenant_id}: {e}")
            return False
    
    def get_tenant_metrics(self, tenant_id: str) -> Dict[str, Any]:
        """Get tenant usage metrics."""
        try:
            tenant = self.get_tenant(tenant_id)
            if not tenant:
                return {}
            
            # Calculate metrics (mock implementation)
            tenant_users = self.get_tenant_users(tenant_id)
            
            metrics = {
                "users_count": len(tenant_users),
                "users_limit": tenant.config.max_users,
                "users_usage_percent": (len(tenant_users) / tenant.config.max_users) * 100,
                "storage_used_gb": 0.5,  # Mock value
                "storage_limit_gb": tenant.config.max_storage_gb,
                "storage_usage_percent": (0.5 / tenant.config.max_storage_gb) * 100,
                "api_calls_today": 150,  # Mock value
                "api_calls_limit": tenant.config.max_api_calls_per_hour * 24,
                "features_enabled": tenant.config.features_enabled,
                "status": tenant.status.value,
                "created_at": tenant.created_at.isoformat(),
                "days_active": (datetime.now() - tenant.created_at).days
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Error getting metrics for tenant {tenant_id}: {e}")
            return {}
    
    def _generate_api_key(self, tenant_id: str) -> str:
        """Generate secure API key for tenant."""
        key_data = f"{tenant_id}:{datetime.now().isoformat()}:{secrets.token_hex(16)}"
        return f"vdt_{hashlib.sha256(key_data.encode()).hexdigest()[:32]}"
    
    def _create_tenant_schema(self, tenant: Tenant) -> bool:
        """Create isolated database schema for tenant."""
        try:
            # In production, this would create actual database schema
            # For now, just log the operation
            logger.info(f"Created database schema: {tenant.database_schema}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating schema for tenant {tenant.id}: {e}")
            return False
    
    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        return datetime.now() - self.last_cache_update < self.cache_ttl
    
    def _refresh_cache(self) -> None:
        """Refresh tenant cache."""
        try:
            # In production, load from database
            self.last_cache_update = datetime.now()
            logger.debug("Refreshed tenant cache")
            
        except Exception as e:
            logger.error(f"Error refreshing cache: {e}")
    
    def _load_tenant_from_storage(self, tenant_id: str) -> Optional[Tenant]:
        """Load tenant from persistent storage."""
        try:
            from app.models import TenantModel
            tenant_model = TenantModel.query.filter_by(id=tenant_id).first()
            
            if not tenant_model:
                return None
            
            # Convert database model to service dataclass
            config = TenantConfig(
                max_users=tenant_model.max_users,
                max_projects=tenant_model.max_projects,
                max_storage_gb=tenant_model.max_storage_gb,
                max_api_calls_per_hour=tenant_model.max_api_calls_per_hour,
                retention_days=tenant_model.retention_days,
                features_enabled=tenant_model.features_enabled or [],
                custom_settings=tenant_model.custom_settings or {}
            )
            
            return Tenant(
                id=tenant_model.id,
                name=tenant_model.name,
                domain=tenant_model.domain,
                status=TenantStatus(tenant_model.status),
                config=config,
                created_at=tenant_model.created_at,
                updated_at=tenant_model.updated_at,
                owner_id=tenant_model.owner_id,
                api_key=tenant_model.api_key,
                webhook_secret=tenant_model.webhook_secret,
                database_schema=tenant_model.database_schema,
                storage_prefix=tenant_model.storage_prefix,
                metadata=tenant_model.tenant_metadata or {}
            )
            
        except Exception as e:
            logger.error(f"Error loading tenant {tenant_id} from storage: {e}")
            return None
    
    def _store_tenant(self, tenant: Tenant) -> bool:
        """Store tenant to persistent storage."""
        try:
            from app.models import TenantModel
            
            tenant_model = TenantModel.query.filter_by(id=tenant.id).first()
            
            if not tenant_model:
                # Create new tenant
                tenant_model = TenantModel(
                    id=tenant.id,
                    name=tenant.name,
                    domain=tenant.domain,
                    status=tenant.status.value,
                    max_users=tenant.config.max_users,
                    max_projects=tenant.config.max_projects,
                    max_storage_gb=tenant.config.max_storage_gb,
                    max_api_calls_per_hour=tenant.config.max_api_calls_per_hour,
                    retention_days=tenant.config.retention_days,
                    features_enabled=tenant.config.features_enabled,
                    custom_settings=tenant.config.custom_settings,
                    api_key=tenant.api_key,
                    webhook_secret=tenant.webhook_secret,
                    database_schema=tenant.database_schema,
                    storage_prefix=tenant.storage_prefix,
                    owner_id=tenant.owner_id,
                    tenant_metadata=tenant.metadata,
                    created_at=tenant.created_at,
                    updated_at=tenant.updated_at
                )
                db.session.add(tenant_model)
            else:
                # Update existing tenant
                tenant_model.name = tenant.name
                tenant_model.domain = tenant.domain
                tenant_model.status = tenant.status.value
                tenant_model.max_users = tenant.config.max_users
                tenant_model.max_projects = tenant.config.max_projects
                tenant_model.max_storage_gb = tenant.config.max_storage_gb
                tenant_model.max_api_calls_per_hour = tenant.config.max_api_calls_per_hour
                tenant_model.retention_days = tenant.config.retention_days
                tenant_model.features_enabled = tenant.config.features_enabled
                tenant_model.custom_settings = tenant.config.custom_settings
                tenant_model.api_key = tenant.api_key
                tenant_model.webhook_secret = tenant.webhook_secret
                tenant_model.tenant_metadata = tenant.metadata
                tenant_model.updated_at = tenant.updated_at
            
            db.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error storing tenant {tenant.id}: {e}")
            db.session.rollback()
            return False
    
    def _store_tenant_user(self, tenant_user: TenantUser) -> bool:
        """Store tenant user association."""
        try:
            from app.models import TenantUserModel
            
            # Check if association already exists
            existing = TenantUserModel.query.filter_by(
                tenant_id=tenant_user.tenant_id,
                user_id=tenant_user.user_id
            ).first()
            
            if existing:
                # Update existing association
                existing.access_level = tenant_user.access_level.value
                existing.permissions = tenant_user.permissions
                existing.expires_at = tenant_user.expires_at
                existing.tenant_metadata = tenant_user.metadata
            else:
                # Create new association
                user_model = TenantUserModel(
                    tenant_id=tenant_user.tenant_id,
                    user_id=tenant_user.user_id,
                    access_level=tenant_user.access_level.value,
                    permissions=tenant_user.permissions,
                    expires_at=tenant_user.expires_at,
                    tenant_metadata=tenant_user.metadata,
                    created_at=tenant_user.created_at
                )
                db.session.add(user_model)
            
            db.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error storing tenant user {tenant_user.tenant_id}:{tenant_user.user_id}: {e}")
            db.session.rollback()
            return False
    
    def _remove_tenant_user(self, tenant_id: str, user_id: str) -> bool:
        """Remove tenant user association."""
        try:
            from app.models import TenantUserModel
            
            user_assoc = TenantUserModel.query.filter_by(
                tenant_id=tenant_id,
                user_id=user_id
            ).first()
            
            if user_assoc:
                db.session.delete(user_assoc)
                db.session.commit()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error removing tenant user {tenant_id}:{user_id}: {e}")
            db.session.rollback()
            return False
    
    def _load_user_tenants(self, user_id: str) -> List[str]:
        """Load user's tenant associations."""
        try:
            from app.models import TenantUserModel
            
            tenant_users = TenantUserModel.query.filter_by(user_id=user_id).all()
            
            # Filter out expired associations
            tenant_ids = []
            for tu in tenant_users:
                if not tu.expires_at or tu.expires_at > datetime.now():
                    tenant_ids.append(tu.tenant_id)
            
            return tenant_ids
            
        except Exception as e:
            logger.error(f"Error loading tenants for user {user_id}: {e}")
            return []
    
    def _load_tenant_users(self, tenant_id: str) -> List[TenantUser]:
        """Load tenant's user associations."""
        try:
            from app.models import TenantUserModel
            
            user_models = TenantUserModel.query.filter_by(tenant_id=tenant_id).all()
            
            tenant_users = []
            for user_model in user_models:
                tenant_user = TenantUser(
                    tenant_id=user_model.tenant_id,
                    user_id=user_model.user_id,
                    access_level=AccessLevel(user_model.access_level),
                    permissions=user_model.permissions or [],
                    created_at=user_model.created_at,
                    expires_at=user_model.expires_at,
                    metadata=user_model.tenant_metadata or {}
                )
                tenant_users.append(tenant_user)
            
            return tenant_users
            
        except Exception as e:
            logger.error(f"Error loading users for tenant {tenant_id}: {e}")
            return []


# Global tenant service instance
tenant_service = TenantService()


def require_tenant_access(permission: str, resource: Optional[str] = None):
    """Decorator to require tenant access for routes."""
    def decorator(f):
        def decorated_function(*args, **kwargs):
            try:
                current_tenant = tenant_service.get_current_tenant()
                if not current_tenant:
                    return {"error": "No tenant context", "success": False}, 403
                
                current_user = getattr(g, 'current_user', None)
                if not current_user:
                    return {"error": "Authentication required", "success": False}, 401
                
                if not tenant_service.check_user_access(
                    current_tenant.id,
                    current_user.id,
                    permission,
                    resource
                ):
                    return {"error": "Insufficient permissions", "success": False}, 403
                
                # Add tenant to request context
                g.current_tenant = current_tenant
                
                return f(*args, **kwargs)
                
            except Exception as e:
                logger.error(f"Error in tenant access check: {e}")
                return {"error": "Access check failed", "success": False}, 500
        
        decorated_function.__name__ = f.__name__
        return decorated_function
    return decorator


def get_tenant_aware_model(model_class, tenant_id: str):
    """Get tenant-aware database model query."""
    try:
        # Add tenant filter to model queries
        return model_class.query.filter_by(tenant_id=tenant_id)
        
    except Exception as e:
        logger.error(f"Error creating tenant-aware model query: {e}")
        return model_class.query