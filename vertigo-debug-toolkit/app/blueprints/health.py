"""
Health Check Blueprint for Service Monitoring
Provides endpoints for monitoring service health and dependencies.
"""

import logging
from datetime import datetime
from flask import Blueprint, jsonify, request
from app.services.sync_scheduler import sync_scheduler
from app.services.firestore_sync import firestore_sync_service
from app.services.langwatch_client import langwatch_client
from app.models import db
from sqlalchemy import text

logger = logging.getLogger(__name__)

health_bp = Blueprint('health', __name__, url_prefix='/health')

@health_bp.route('/')
def basic_health():
    """Basic health check - always returns 200 OK if service is running."""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'vertigo-debug-toolkit'
    })

@health_bp.route('/detailed')
def detailed_health():
    """Detailed health check including all dependencies."""
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'service': 'vertigo-debug-toolkit',
        'checks': {}
    }
    
    overall_healthy = True
    
    # Database health check
    try:
        db.session.execute(text('SELECT 1')).fetchone()
        health_status['checks']['database'] = {
            'status': 'healthy',
            'message': 'Database connection successful'
        }
    except Exception as e:
        overall_healthy = False
        health_status['checks']['database'] = {
            'status': 'unhealthy',
            'message': f'Database connection failed: {str(e)}'
        }
    
    # Firestore sync service health check
    try:
        firestore_available = firestore_sync_service.is_available()
        stats = firestore_sync_service.get_sync_statistics()
        
        health_status['checks']['firestore_sync'] = {
            'status': 'healthy' if firestore_available else 'degraded',
            'available': firestore_available,
            'total_records': stats.get('total_records', 0),
            'latest_record': stats.get('latest_record'),
            'message': 'Firestore sync service operational' if firestore_available else 'Firestore sync not available'
        }
        
        if not firestore_available:
            logger.debug("Firestore sync service not available but service continues")
            
    except Exception as e:
        logger.warning(f"Error checking Firestore sync health: {e}")
        health_status['checks']['firestore_sync'] = {
            'status': 'degraded',
            'available': False,
            'message': f'Firestore sync check failed: {str(e)}'
        }
    
    # Sync scheduler health check
    try:
        scheduler_status = sync_scheduler.get_scheduler_status()
        
        health_status['checks']['sync_scheduler'] = {
            'status': 'healthy' if scheduler_status.get('is_running') else 'degraded',
            'running': scheduler_status.get('is_running', False),
            'jobs': len(scheduler_status.get('jobs', [])),
            'stats': {
                'sync_count': scheduler_status.get('stats', {}).get('sync_count', 0),
                'success_count': scheduler_status.get('stats', {}).get('success_count', 0),
                'error_count': scheduler_status.get('stats', {}).get('error_count', 0)
            },
            'message': 'Sync scheduler operational' if scheduler_status.get('is_running') else 'Sync scheduler not running'
        }
        
        if not scheduler_status.get('is_running'):
            logger.debug("Sync scheduler not running but service continues")
            
    except Exception as e:
        logger.warning(f"Error checking scheduler health: {e}")
        health_status['checks']['sync_scheduler'] = {
            'status': 'degraded',
            'running': False,
            'message': f'Scheduler check failed: {str(e)}'
        }
    
    # LangWatch client health check
    try:
        langwatch_status = langwatch_client.get_service_status()
        
        health_status['checks']['langwatch'] = {
            'status': 'healthy' if langwatch_status.get('enabled') else 'disabled',
            'enabled': langwatch_status.get('enabled', False),
            'api_configured': langwatch_status.get('api_configured', False),
            'circuit_breaker': langwatch_status.get('circuit_breaker', {}),
            'message': 'LangWatch client operational' if langwatch_status.get('enabled') else 'LangWatch client disabled'
        }
        
    except Exception as e:
        logger.warning(f"Error checking LangWatch health: {e}")
        health_status['checks']['langwatch'] = {
            'status': 'degraded',
            'enabled': False,
            'message': f'LangWatch check failed: {str(e)}'
        }
    
    # Set overall status
    if not overall_healthy:
        health_status['status'] = 'unhealthy'
    elif any(check.get('status') == 'degraded' for check in health_status['checks'].values()):
        health_status['status'] = 'degraded'
    
    # Return appropriate HTTP status code
    if health_status['status'] == 'healthy':
        return jsonify(health_status), 200
    elif health_status['status'] == 'degraded':
        return jsonify(health_status), 200  # Still operational
    else:
        return jsonify(health_status), 503  # Service unavailable

@health_bp.route('/liveness')
def liveness():
    """Kubernetes liveness probe - checks if service should be restarted."""
    try:
        # Very basic check - if we can respond, we're alive
        return jsonify({
            'status': 'alive',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        return jsonify({
            'status': 'dead',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503

@health_bp.route('/readiness')
def readiness():
    """Kubernetes readiness probe - checks if service can handle requests."""
    try:
        # Check critical dependencies
        db.session.execute(text('SELECT 1')).fetchone()
        
        return jsonify({
            'status': 'ready',
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return jsonify({
            'status': 'not_ready',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 503

@health_bp.route('/metrics')
def basic_metrics():
    """Basic metrics endpoint for monitoring."""
    try:
        metrics = {
            'timestamp': datetime.utcnow().isoformat(),
            'uptime_seconds': None,  # Could be calculated if we track start time
            'database': {},
            'sync_scheduler': {},
            'firestore_sync': {},
            'langwatch': {}
        }
        
        # Database metrics
        try:
            result = db.session.execute(text("SELECT COUNT(*) FROM live_traces")).fetchone()
            metrics['database']['live_traces_count'] = result[0] if result else 0
        except Exception as e:
            metrics['database']['error'] = str(e)
        
        # Scheduler metrics
        try:
            scheduler_status = sync_scheduler.get_scheduler_status()
            metrics['sync_scheduler'] = scheduler_status.get('stats', {})
        except Exception as e:
            metrics['sync_scheduler']['error'] = str(e)
        
        # Firestore sync metrics  
        try:
            sync_stats = firestore_sync_service.get_sync_statistics()
            metrics['firestore_sync'] = {
                'total_records': sync_stats.get('total_records', 0),
                'is_available': sync_stats.get('is_available', False)
            }
        except Exception as e:
            metrics['firestore_sync']['error'] = str(e)
        
        # LangWatch metrics
        try:
            langwatch_status = langwatch_client.get_service_status()
            metrics['langwatch'] = {
                'enabled': langwatch_status.get('enabled', False),
                'circuit_breaker_state': langwatch_status.get('circuit_breaker', {}).get('state', 'unknown')
            }
        except Exception as e:
            metrics['langwatch']['error'] = str(e)
        
        return jsonify(metrics), 200
        
    except Exception as e:
        logger.error(f"Metrics collection failed: {e}")
        return jsonify({
            'error': 'Failed to collect metrics',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@health_bp.route('/debug')
def debug_info():
    """Debug information for troubleshooting (only in debug mode)."""
    from flask import current_app
    
    if not current_app.debug:
        return jsonify({'error': 'Debug info only available in debug mode'}), 403
    
    try:
        debug_data = {
            'timestamp': datetime.utcnow().isoformat(),
            'flask_debug': current_app.debug,
            'config': {
                'database_url': current_app.config.get('SQLALCHEMY_DATABASE_URI', '').replace('sqlite:///', 'sqlite:///[PATH]'),
                'langfuse_configured': bool(current_app.config.get('LANGFUSE_PUBLIC_KEY')),
                'enable_firestore_sync': current_app.config.get('ENABLE_FIRESTORE_SYNC', False),
            },
            'services': {}
        }
        
        # Add detailed service information
        try:
            debug_data['services']['sync_scheduler'] = sync_scheduler.get_scheduler_status()
        except Exception as e:
            debug_data['services']['sync_scheduler'] = {'error': str(e)}
        
        try:
            debug_data['services']['firestore_sync'] = firestore_sync_service.get_sync_statistics()
        except Exception as e:
            debug_data['services']['firestore_sync'] = {'error': str(e)}
        
        try:
            debug_data['services']['langwatch'] = langwatch_client.get_service_status()
        except Exception as e:
            debug_data['services']['langwatch'] = {'error': str(e)}
        
        return jsonify(debug_data), 200
        
    except Exception as e:
        logger.error(f"Debug info collection failed: {e}")
        return jsonify({
            'error': 'Failed to collect debug info',
            'details': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500