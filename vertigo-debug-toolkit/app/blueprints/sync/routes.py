"""
Sync Management API Routes

Provides REST API endpoints for:
- Sync status monitoring
- Manual sync triggers
- Sync history and statistics
- Scheduler control (admin only)
"""

import logging
from datetime import datetime, timedelta
from flask import jsonify, request, current_app
from flask_login import login_required, current_user

from . import sync_bp
from app.services.sync_scheduler import sync_scheduler
from app.services.firestore_sync import firestore_sync_service
from app.models import db
from sqlalchemy import text

logger = logging.getLogger(__name__)

def admin_required(f):
    """Decorator to require admin access."""
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'error': 'Admin access required'}), 403
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@sync_bp.route('/status', methods=['GET'])
@login_required
def get_sync_status():
    """
    Get current sync status and health information.
    
    Returns:
        JSON with sync status, scheduler info, and health metrics
    """
    try:
        # Get scheduler status
        scheduler_status = sync_scheduler.get_scheduler_status()
        
        # Get Firestore sync statistics
        sync_stats = firestore_sync_service.get_sync_statistics()
        
        # Get next sync time
        next_sync = sync_scheduler.get_next_sync_time()
        
        # Recent sync performance
        recent_syncs = get_recent_sync_history(limit=10)
        
        return jsonify({
            'success': True,
            'data': {
                'scheduler': scheduler_status,
                'firestore': sync_stats,
                'next_sync': next_sync.isoformat() if next_sync else None,
                'recent_syncs': recent_syncs,
                'health': {
                    'overall_status': 'healthy' if scheduler_status.get('is_running') and sync_stats.get('is_available') else 'degraded',
                    'firestore_available': sync_stats.get('is_available', False),
                    'scheduler_running': scheduler_status.get('is_running', False),
                    'last_check': datetime.utcnow().isoformat()
                }
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@sync_bp.route('/trigger', methods=['POST'])
@login_required
@admin_required
def trigger_manual_sync():
    """
    Trigger a manual sync operation.
    
    Admin only endpoint for forcing immediate sync.
    """
    try:
        # Get optional parameters
        data = request.get_json() or {}
        hours_back = data.get('hours_back', 24)
        force_full = data.get('force_full', False)
        
        logger.info(f"Manual sync triggered by {current_user.username}")
        
        if force_full:
            # Force full sync
            result = firestore_sync_service.force_full_sync(hours_back=hours_back)
        else:
            # Regular incremental sync
            result = sync_scheduler.trigger_manual_sync()
        
        if result.get('success') or (hasattr(result, 'success') and result.success):
            return jsonify({
                'success': True,
                'message': 'Manual sync completed successfully',
                'data': {
                    'records_processed': result.get('records_processed', 0),
                    'errors': result.get('errors', []),
                    'sync_type': 'full' if force_full else 'incremental',
                    'triggered_by': current_user.username,
                    'timestamp': datetime.utcnow().isoformat()
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Manual sync failed',
                'error': result.get('error', 'Unknown error'),
                'errors': result.get('errors', [])
            }), 500
            
    except Exception as e:
        logger.error(f"Error triggering manual sync: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@sync_bp.route('/history', methods=['GET'])
@login_required
def get_sync_history():
    """
    Get recent sync operations history.
    
    Query parameters:
        - limit: Number of records to return (default: 50, max: 200)
        - offset: Offset for pagination (default: 0)
        - status: Filter by sync status ('success', 'error', 'pending')
        - since: ISO timestamp to get syncs since (optional)
    """
    try:
        # Parse query parameters
        limit = min(int(request.args.get('limit', 50)), 200)
        offset = int(request.args.get('offset', 0))
        status_filter = request.args.get('status')
        since = request.args.get('since')
        
        # Get sync history
        history = get_recent_sync_history(
            limit=limit,
            offset=offset,
            status_filter=status_filter,
            since=since
        )
        
        # Get total count for pagination
        total_count = get_sync_history_count(status_filter=status_filter, since=since)
        
        return jsonify({
            'success': True,
            'data': {
                'syncs': history,
                'pagination': {
                    'total': total_count,
                    'limit': limit,
                    'offset': offset,
                    'has_more': (offset + limit) < total_count
                }
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting sync history: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@sync_bp.route('/config', methods=['GET'])
@login_required
def get_sync_config():
    """
    Get current sync configuration.
    """
    try:
        config = {
            'firestore': {
                'sync_enabled': current_app.config.get('ENABLE_FIRESTORE_SYNC', True),
                'sync_interval_minutes': current_app.config.get('FIRESTORE_SYNC_INTERVAL_MINUTES', 5),
                'batch_size': current_app.config.get('FIRESTORE_SYNC_BATCH_SIZE', 100),
                'max_workers': current_app.config.get('SYNC_MAX_WORKERS', 2),
                'project_id': current_app.config.get('GOOGLE_CLOUD_PROJECT')
            },
            'scheduler': {
                'is_running': sync_scheduler.is_running,
                'sync_interval_minutes': sync_scheduler.sync_interval_minutes,
                'max_workers': sync_scheduler.max_workers
            },
            'health_check': {
                'interval_minutes': 10,
                'timeout_seconds': 30
            }
        }
        
        return jsonify({
            'success': True,
            'data': config,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting sync config: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@sync_bp.route('/pause', methods=['POST'])
@login_required
@admin_required
def pause_sync():
    """
    Pause sync operations (admin only).
    """
    try:
        success = sync_scheduler.pause_sync()
        
        if success:
            logger.info(f"Sync paused by {current_user.username}")
            return jsonify({
                'success': True,
                'message': 'Sync operations paused',
                'paused_by': current_user.username,
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to pause sync operations'
            }), 500
            
    except Exception as e:
        logger.error(f"Error pausing sync: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@sync_bp.route('/resume', methods=['POST'])
@login_required
@admin_required
def resume_sync():
    """
    Resume sync operations (admin only).
    """
    try:
        success = sync_scheduler.resume_sync()
        
        if success:
            logger.info(f"Sync resumed by {current_user.username}")
            return jsonify({
                'success': True,
                'message': 'Sync operations resumed',
                'resumed_by': current_user.username,
                'timestamp': datetime.utcnow().isoformat()
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Failed to resume sync operations'
            }), 500
            
    except Exception as e:
        logger.error(f"Error resuming sync: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@sync_bp.route('/metrics', methods=['GET'])
@login_required
def get_sync_metrics():
    """
    Get detailed sync performance metrics.
    
    Query parameters:
        - period: Time period ('hour', 'day', 'week') - default: 'day'
        - limit: Number of data points to return - default: 24
    """
    try:
        period = request.args.get('period', 'day')
        limit = min(int(request.args.get('limit', 24)), 100)
        
        # Get sync metrics from database
        metrics = get_sync_performance_metrics(period=period, limit=limit)
        
        # Get current sync statistics
        current_stats = firestore_sync_service.get_sync_statistics()
        
        return jsonify({
            'success': True,
            'data': {
                'metrics': metrics,
                'current_stats': current_stats,
                'period': period,
                'limit': limit
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting sync metrics: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# Helper functions

def get_recent_sync_history(limit=50, offset=0, status_filter=None, since=None):
    """Get recent sync history from database."""
    try:
        sql = """
        SELECT sync_type, sync_status, last_sync_timestamp, last_successful_sync,
               records_processed, error_message, updated_at
        FROM sync_status
        WHERE 1=1
        """
        params = {}
        
        if status_filter:
            sql += " AND sync_status = :status"
            params['status'] = status_filter
            
        if since:
            sql += " AND updated_at >= :since"
            params['since'] = since
        
        sql += " ORDER BY updated_at DESC LIMIT :limit OFFSET :offset"
        params['limit'] = limit
        params['offset'] = offset
        
        result = db.session.execute(text(sql), params).fetchall()
        
        return [
            {
                'sync_type': row[0],
                'status': row[1],
                'last_sync': row[2],
                'last_success': row[3],
                'records_processed': row[4],
                'error_message': row[5],
                'updated_at': row[6]
            }
            for row in result
        ]
        
    except Exception as e:
        logger.error(f"Error getting sync history: {e}")
        return []

def get_sync_history_count(status_filter=None, since=None):
    """Get total count of sync history records."""
    try:
        sql = "SELECT COUNT(*) FROM sync_status WHERE 1=1"
        params = {}
        
        if status_filter:
            sql += " AND sync_status = :status"
            params['status'] = status_filter
            
        if since:
            sql += " AND updated_at >= :since"
            params['since'] = since
        
        result = db.session.execute(text(sql), params).fetchone()
        return result[0] if result else 0
        
    except Exception as e:
        logger.error(f"Error getting sync history count: {e}")
        return 0

def get_sync_performance_metrics(period='day', limit=24):
    """Get sync performance metrics over time."""
    try:
        # This would query the performance_metrics table
        # For now, return placeholder data
        return {
            'sync_success_rate': [],
            'records_per_sync': [],
            'sync_duration': [],
            'error_rate': []
        }
        
    except Exception as e:
        logger.error(f"Error getting sync performance metrics: {e}")
        return {}

# Error handlers

@sync_bp.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404

@sync_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500