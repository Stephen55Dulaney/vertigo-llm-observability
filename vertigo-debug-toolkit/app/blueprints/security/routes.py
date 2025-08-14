"""
Security Management Routes

API endpoints for security monitoring, API key management, and security configuration.
"""

from flask import request, jsonify, render_template, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime, timedelta
import logging

from app.blueprints.security import security_bp
from app.services.security_monitor import security_monitor
from app.services.api_key_service import api_key_service
from app.services.auth_service import auth_service
from app.services.rate_limiter import rate_limiter
from app.models.security_models import SecurityEvent, LoginAttempt, APIKey
from app.models import User, db

logger = logging.getLogger(__name__)


@security_bp.route('/dashboard')
@login_required
def dashboard():
    """Security dashboard."""
    if not current_user.is_admin:
        flash('Access denied. Admin privileges required.', 'error')
        return redirect(url_for('dashboard.index'))
    
    try:
        dashboard_data = security_monitor.get_security_dashboard_data()
        return render_template('security/dashboard.html', data=dashboard_data)
    except Exception as e:
        logger.error(f"Error loading security dashboard: {e}")
        flash('Error loading security dashboard.', 'error')
        return redirect(url_for('dashboard.index'))


@security_bp.route('/api/events')
@login_required
def api_security_events():
    """Get security events (API endpoint)."""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 25, type=int)
        severity = request.args.get('severity')
        event_type = request.args.get('event_type')
        hours = request.args.get('hours', 24, type=int)
        
        # Build query
        query = SecurityEvent.query
        
        # Filter by time
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        query = query.filter(SecurityEvent.timestamp >= cutoff)
        
        # Filter by severity
        if severity:
            query = query.filter(SecurityEvent.severity == severity)
        
        # Filter by event type
        if event_type:
            query = query.filter(SecurityEvent.event_type == event_type)
        
        # Order and paginate
        query = query.order_by(SecurityEvent.timestamp.desc())
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        events = [event.to_dict() for event in pagination.items]
        
        return jsonify({
            'events': events,
            'pagination': {
                'page': page,
                'pages': pagination.pages,
                'per_page': per_page,
                'total': pagination.total,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        })
    
    except Exception as e:
        logger.error(f"Error getting security events: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@security_bp.route('/api/ip-analysis/<ip_address>')
@login_required
def api_ip_analysis(ip_address):
    """Analyze IP address reputation."""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        analysis = security_monitor.analyze_ip_reputation(ip_address)
        return jsonify(analysis)
    except Exception as e:
        logger.error(f"Error analyzing IP {ip_address}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@security_bp.route('/api/api-keys', methods=['GET', 'POST'])
@login_required
def api_manage_api_keys():
    """Manage API keys."""
    if request.method == 'GET':
        # Get user's API keys
        api_keys = api_key_service.get_api_keys_for_user(current_user.id)
        return jsonify({
            'api_keys': [
                {
                    'key_id': key.key_id,
                    'name': key.name,
                    'scopes': key.scopes,
                    'status': key.status.value,
                    'created_at': key.created_at.isoformat(),
                    'expires_at': key.expires_at.isoformat() if key.expires_at else None,
                    'last_used_at': key.last_used_at.isoformat() if key.last_used_at else None,
                    'usage_count': key.usage_count,
                    'rate_limit_tier': key.rate_limit_tier
                }
                for key in api_keys
            ]
        })
    
    elif request.method == 'POST':
        # Create new API key
        try:
            data = request.get_json()
            name = data.get('name', '').strip()
            scopes = data.get('scopes', [])
            expires_days = data.get('expires_days')
            rate_limit_tier = data.get('rate_limit_tier', 'free')
            
            if not name:
                return jsonify({'error': 'Name is required'}), 400
            
            # Generate API key
            api_key, key_id = api_key_service.generate_api_key(
                current_user, name, scopes, expires_days, rate_limit_tier
            )
            
            return jsonify({
                'message': 'API key created successfully',
                'api_key': api_key,  # Only returned once!
                'key_id': key_id
            })
        
        except Exception as e:
            logger.error(f"Error creating API key: {e}")
            return jsonify({'error': 'Failed to create API key'}), 500


@security_bp.route('/api/api-keys/<key_id>', methods=['DELETE'])
@login_required
def api_revoke_api_key(key_id):
    """Revoke API key."""
    try:
        success = api_key_service.revoke_api_key(key_id, current_user.id)
        if success:
            return jsonify({'message': 'API key revoked successfully'})
        else:
            return jsonify({'error': 'API key not found or access denied'}), 404
    
    except Exception as e:
        logger.error(f"Error revoking API key {key_id}: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@security_bp.route('/api/rate-limits/status')
@login_required
def api_rate_limit_status():
    """Get rate limit status for current user."""
    try:
        status = rate_limiter.get_rate_limit_status(current_user)
        return jsonify(status)
    except Exception as e:
        logger.error(f"Error getting rate limit status: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@security_bp.route('/api/rate-limits/reset', methods=['POST'])
@login_required
def api_reset_rate_limits():
    """Reset rate limits (admin only)."""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'User ID is required'}), 400
        
        rate_limiter.reset_user_limits(user_id)
        return jsonify({'message': 'Rate limits reset successfully'})
    
    except Exception as e:
        logger.error(f"Error resetting rate limits: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@security_bp.route('/api/security-info')
@login_required
def api_security_info():
    """Get security information."""
    try:
        info = auth_service.get_security_info()
        
        # Add current user session info
        session_info = auth_service.session_manager.get_session_info()
        info['current_session'] = session_info
        
        # Add rate limit info
        rate_limit_info = rate_limiter.get_rate_limit_status(current_user)
        info['rate_limits'] = rate_limit_info
        
        return jsonify(info)
    
    except Exception as e:
        logger.error(f"Error getting security info: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@security_bp.route('/api/change-password', methods=['POST'])
@login_required
def api_change_password():
    """Change user password."""
    try:
        data = request.get_json()
        old_password = data.get('old_password', '')
        new_password = data.get('new_password', '')
        
        if not old_password or not new_password:
            return jsonify({'error': 'Both old and new passwords are required'}), 400
        
        success, errors = auth_service.change_password(
            current_user, old_password, new_password
        )
        
        if success:
            return jsonify({'message': 'Password changed successfully'})
        else:
            return jsonify({'error': 'Password change failed', 'details': errors}), 400
    
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@security_bp.route('/api/admin/users', methods=['GET'])
@login_required
def api_admin_users():
    """Get users list (admin only)."""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        users = User.query.all()
        return jsonify({
            'users': [
                {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'is_admin': user.is_admin,
                    'is_active': user.is_active,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    'last_login': user.last_login.isoformat() if user.last_login else None
                }
                for user in users
            ]
        })
    
    except Exception as e:
        logger.error(f"Error getting users list: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@security_bp.route('/api/admin/users/<int:user_id>/toggle-status', methods=['POST'])
@login_required
def api_admin_toggle_user_status(user_id):
    """Toggle user active status (admin only)."""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        user = User.query.get_or_404(user_id)
        
        # Prevent deactivating self
        if user.id == current_user.id:
            return jsonify({'error': 'Cannot deactivate your own account'}), 400
        
        user.is_active = not user.is_active
        db.session.commit()
        
        action = 'activated' if user.is_active else 'deactivated'
        return jsonify({'message': f'User {action} successfully'})
    
    except Exception as e:
        logger.error(f"Error toggling user status: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@security_bp.route('/api/metrics')
@login_required
def api_security_metrics():
    """Get security metrics (admin only)."""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        # Get metrics from various sources
        security_dashboard = security_monitor.get_security_dashboard_data()
        api_key_stats = api_key_service.get_usage_stats()
        rate_limiter_metrics = rate_limiter.get_metrics()
        
        return jsonify({
            'security_events': security_dashboard,
            'api_keys': api_key_stats,
            'rate_limiting': rate_limiter_metrics,
            'timestamp': datetime.utcnow().isoformat()
        })
    
    except Exception as e:
        logger.error(f"Error getting security metrics: {e}")
        return jsonify({'error': 'Internal server error'}), 500


@security_bp.route('/api/cleanup', methods=['POST'])
@login_required
def api_cleanup_old_data():
    """Clean up old security data (admin only)."""
    if not current_user.is_admin:
        return jsonify({'error': 'Access denied'}), 403
    
    try:
        data = request.get_json()
        days_to_keep = data.get('days_to_keep', 30)
        
        if days_to_keep < 7:
            return jsonify({'error': 'Must keep at least 7 days of data'}), 400
        
        security_monitor.cleanup_old_data(days_to_keep)
        return jsonify({'message': f'Cleaned up data older than {days_to_keep} days'})
    
    except Exception as e:
        logger.error(f"Error cleaning up old data: {e}")
        return jsonify({'error': 'Internal server error'}), 500


# Error handlers for the security blueprint
@security_bp.errorhandler(404)
def security_not_found(error):
    """Handle 404 errors in security blueprint."""
    return jsonify({'error': 'Endpoint not found'}), 404


@security_bp.errorhandler(500)
def security_internal_error(error):
    """Handle 500 errors in security blueprint."""
    return jsonify({'error': 'Internal server error'}), 500