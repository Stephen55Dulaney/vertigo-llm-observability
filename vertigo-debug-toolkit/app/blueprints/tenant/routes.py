"""
Tenant management routes for multi-tenant administration and isolation.
"""

from flask import render_template, request, jsonify, current_app, g
from flask_login import login_required, current_user
from app.blueprints.tenant import tenant_bp
from app.services.tenant_service import (
    tenant_service, require_tenant_access, 
    TenantConfig, AccessLevel, TenantStatus
)
import logging

logger = logging.getLogger(__name__)


@tenant_bp.route('/')
@login_required
def index():
    """Tenant management dashboard."""
    try:
        # Get user's tenants
        user_tenants = tenant_service.get_user_tenants(current_user.id)
        tenants = []
        
        for tenant_id in user_tenants:
            tenant = tenant_service.get_tenant(tenant_id)
            if tenant:
                metrics = tenant_service.get_tenant_metrics(tenant_id)
                tenants.append({
                    'tenant': tenant,
                    'metrics': metrics
                })
        
        return render_template('tenant/index.html', tenants=tenants)
        
    except Exception as e:
        logger.error(f"Error loading tenant dashboard: {e}")
        return render_template('error.html', error="Failed to load tenant dashboard"), 500


@tenant_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create_tenant():
    """Create new tenant."""
    if request.method == 'GET':
        return render_template('tenant/create.html')
    
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['name', 'domain']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400
        
        # Create tenant configuration
        config_data = data.get('config', {})
        config = TenantConfig(
            max_users=config_data.get('max_users', 25),
            max_projects=config_data.get('max_projects', 10),
            max_storage_gb=config_data.get('max_storage_gb', 5.0),
            max_api_calls_per_hour=config_data.get('max_api_calls_per_hour', 5000),
            retention_days=config_data.get('retention_days', 90),
            features_enabled=config_data.get('features_enabled', [
                "analytics", "alerts", "advanced_evaluation", "semantic_search"
            ]),
            custom_settings=config_data.get('custom_settings', {})
        )
        
        # Create tenant
        tenant = tenant_service.create_tenant(
            name=data['name'],
            domain=data['domain'],
            owner_user_id=current_user.id,
            config=config
        )
        
        return jsonify({
            "success": True,
            "tenant_id": tenant.id,
            "api_key": tenant.api_key,
            "message": f"Tenant '{tenant.name}' created successfully"
        })
        
    except Exception as e:
        logger.error(f"Error creating tenant: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@tenant_bp.route('/<tenant_id>')
@login_required
@require_tenant_access("read")
def tenant_details(tenant_id):
    """Get tenant details."""
    try:
        tenant = tenant_service.get_tenant(tenant_id)
        if not tenant:
            return jsonify({"success": False, "error": "Tenant not found"}), 404
        
        # Get tenant metrics and users
        metrics = tenant_service.get_tenant_metrics(tenant_id)
        users = tenant_service.get_tenant_users(tenant_id)
        
        # Check if current user can manage tenant
        can_manage = tenant_service.check_user_access(
            tenant_id, current_user.id, "admin"
        )
        
        tenant_data = {
            "id": tenant.id,
            "name": tenant.name,
            "domain": tenant.domain,
            "status": tenant.status.value,
            "config": {
                "max_users": tenant.config.max_users,
                "max_projects": tenant.config.max_projects,
                "max_storage_gb": tenant.config.max_storage_gb,
                "max_api_calls_per_hour": tenant.config.max_api_calls_per_hour,
                "retention_days": tenant.config.retention_days,
                "features_enabled": tenant.config.features_enabled,
                "custom_settings": tenant.config.custom_settings
            },
            "api_key": tenant.api_key if can_manage else "***hidden***",
            "webhook_secret": tenant.webhook_secret if can_manage else "***hidden***",
            "created_at": tenant.created_at.isoformat(),
            "updated_at": tenant.updated_at.isoformat(),
            "metrics": metrics,
            "users": [{
                "user_id": user.user_id,
                "access_level": user.access_level.value,
                "permissions": user.permissions,
                "created_at": user.created_at.isoformat(),
                "expires_at": user.expires_at.isoformat() if user.expires_at else None
            } for user in users],
            "can_manage": can_manage
        }
        
        return jsonify({
            "success": True,
            "tenant": tenant_data
        })
        
    except Exception as e:
        logger.error(f"Error getting tenant details: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@tenant_bp.route('/<tenant_id>/config', methods=['PUT'])
@login_required
@require_tenant_access("admin", "config")
def update_tenant_config(tenant_id):
    """Update tenant configuration."""
    try:
        data = request.get_json()
        
        # Update tenant configuration
        success = tenant_service.update_tenant_config(
            tenant_id=tenant_id,
            user_id=current_user.id,
            config_updates=data
        )
        
        if success:
            return jsonify({
                "success": True,
                "message": "Tenant configuration updated successfully"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to update tenant configuration"
            }), 400
        
    except Exception as e:
        logger.error(f"Error updating tenant config: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@tenant_bp.route('/<tenant_id>/api-key', methods=['POST'])
@login_required
@require_tenant_access("admin", "api_keys")
def rotate_api_key(tenant_id):
    """Rotate tenant API key."""
    try:
        new_api_key = tenant_service.rotate_api_key(tenant_id, current_user.id)
        
        if new_api_key:
            return jsonify({
                "success": True,
                "api_key": new_api_key,
                "message": "API key rotated successfully"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to rotate API key"
            }), 400
        
    except Exception as e:
        logger.error(f"Error rotating API key: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@tenant_bp.route('/<tenant_id>/users', methods=['GET'])
@login_required
@require_tenant_access("read", "users")
def get_tenant_users(tenant_id):
    """Get tenant users."""
    try:
        users = tenant_service.get_tenant_users(tenant_id)
        
        users_data = [{
            "user_id": user.user_id,
            "access_level": user.access_level.value,
            "permissions": user.permissions,
            "created_at": user.created_at.isoformat(),
            "expires_at": user.expires_at.isoformat() if user.expires_at else None,
            "metadata": user.metadata
        } for user in users]
        
        return jsonify({
            "success": True,
            "users": users_data,
            "total": len(users_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting tenant users: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@tenant_bp.route('/<tenant_id>/users', methods=['POST'])
@login_required
@require_tenant_access("admin", "users")
def add_tenant_user(tenant_id):
    """Add user to tenant."""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['user_id', 'access_level']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400
        
        # Parse access level
        try:
            access_level = AccessLevel(data['access_level'])
        except ValueError:
            return jsonify({
                "success": False,
                "error": f"Invalid access level: {data['access_level']}"
            }), 400
        
        # Parse expiration date
        expires_at = None
        if data.get('expires_at'):
            from datetime import datetime
            expires_at = datetime.fromisoformat(data['expires_at'].replace('Z', '+00:00'))
        
        # Add user to tenant
        success = tenant_service.add_user_to_tenant(
            tenant_id=tenant_id,
            user_id=data['user_id'],
            access_level=access_level,
            permissions=data.get('permissions', []),
            expires_at=expires_at
        )
        
        if success:
            return jsonify({
                "success": True,
                "message": f"User added to tenant successfully"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to add user to tenant"
            }), 400
        
    except Exception as e:
        logger.error(f"Error adding user to tenant: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@tenant_bp.route('/<tenant_id>/users/<user_id>', methods=['DELETE'])
@login_required
@require_tenant_access("admin", "users")
def remove_tenant_user(tenant_id, user_id):
    """Remove user from tenant."""
    try:
        success = tenant_service.remove_user_from_tenant(tenant_id, user_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": "User removed from tenant successfully"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Failed to remove user from tenant"
            }), 400
        
    except Exception as e:
        logger.error(f"Error removing user from tenant: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@tenant_bp.route('/<tenant_id>/metrics')
@login_required
@require_tenant_access("read", "metrics")
def get_tenant_metrics(tenant_id):
    """Get tenant usage metrics."""
    try:
        metrics = tenant_service.get_tenant_metrics(tenant_id)
        
        return jsonify({
            "success": True,
            "metrics": metrics
        })
        
    except Exception as e:
        logger.error(f"Error getting tenant metrics: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@tenant_bp.route('/current')
@login_required
def get_current_tenant():
    """Get current tenant context."""
    try:
        current_tenant = tenant_service.get_current_tenant()
        
        if current_tenant:
            # Check user access level
            user_access = tenant_service.check_user_access(
                current_tenant.id, current_user.id, "read"
            )
            
            if user_access:
                tenant_data = {
                    "id": current_tenant.id,
                    "name": current_tenant.name,
                    "domain": current_tenant.domain,
                    "status": current_tenant.status.value,
                    "features_enabled": current_tenant.config.features_enabled
                }
                
                return jsonify({
                    "success": True,
                    "tenant": tenant_data
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Access denied to current tenant"
                }), 403
        else:
            return jsonify({
                "success": True,
                "tenant": None,
                "message": "No current tenant context"
            })
        
    except Exception as e:
        logger.error(f"Error getting current tenant: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@tenant_bp.route('/switch', methods=['POST'])
@login_required
def switch_tenant():
    """Switch to different tenant context."""
    try:
        data = request.get_json()
        tenant_id = data.get('tenant_id')
        
        if not tenant_id:
            return jsonify({
                "success": False,
                "error": "Missing tenant_id"
            }), 400
        
        # Check if user has access to tenant
        user_tenants = tenant_service.get_user_tenants(current_user.id)
        if tenant_id not in user_tenants:
            return jsonify({
                "success": False,
                "error": "Access denied to specified tenant"
            }), 403
        
        # Set tenant in session/context
        tenant = tenant_service.get_tenant(tenant_id)
        if tenant:
            g.current_tenant = tenant
            return jsonify({
                "success": True,
                "tenant": {
                    "id": tenant.id,
                    "name": tenant.name,
                    "domain": tenant.domain
                },
                "message": f"Switched to tenant: {tenant.name}"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Tenant not found"
            }), 404
        
    except Exception as e:
        logger.error(f"Error switching tenant: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@tenant_bp.route('/list')
@login_required
def list_user_tenants():
    """List user's accessible tenants."""
    try:
        user_tenants = tenant_service.get_user_tenants(current_user.id)
        tenants_data = []
        
        for tenant_id in user_tenants:
            tenant = tenant_service.get_tenant(tenant_id)
            if tenant:
                # Get user access level for this tenant
                tenant_users = tenant_service.get_tenant_users(tenant_id)
                user_access_level = "read"
                
                for tu in tenant_users:
                    if tu.user_id == current_user.id:
                        user_access_level = tu.access_level.value
                        break
                
                tenants_data.append({
                    "id": tenant.id,
                    "name": tenant.name,
                    "domain": tenant.domain,
                    "status": tenant.status.value,
                    "user_access_level": user_access_level,
                    "created_at": tenant.created_at.isoformat()
                })
        
        return jsonify({
            "success": True,
            "tenants": tenants_data,
            "total": len(tenants_data)
        })
        
    except Exception as e:
        logger.error(f"Error listing user tenants: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500