"""
Live Data API Routes for real-time integration.
Provides endpoints for live metrics, webhook processing, and sync management.
"""

import json
import logging
from datetime import datetime, timedelta
from flask import jsonify, request, current_app
from flask_login import login_required, current_user
from sqlalchemy import text, func
from sqlalchemy.exc import SQLAlchemyError

from app.blueprints.live_data import live_data_bp
from app.models import db
from app.services.firestore_sync import firestore_sync_service
from app.services.webhook_handler import webhook_handler
from app.services.langwatch_client import langwatch_client

logger = logging.getLogger(__name__)

# ============================================================================
# LIVE METRICS API ENDPOINTS
# ============================================================================

@live_data_bp.route('/api/live-metrics')
@login_required
def get_live_metrics():
    """
    Get real-time performance metrics from live data sources.
    
    Query Parameters:
    - hours: Time range in hours (default: 24, max: 168)
    - source: Data source filter ('all', 'firestore', 'webhook', 'langwatch')
    
    Returns:
    - Combined metrics from all configured sources
    - Source attribution for each metric
    - Data freshness indicators
    """
    try:
        hours = min(request.args.get('hours', 24, type=int), 168)
        source_filter = request.args.get('source', 'all')
        
        # Calculate time range
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # Initialize response structure
        response_data = {
            'time_range': {
                'hours': hours,
                'start_time': start_time.isoformat(),
                'end_time': end_time.isoformat()
            },
            'sources': {},
            'combined_metrics': {},
            'data_freshness': {}
        }
        
        # Get Firestore data if available and requested
        if source_filter in ['all', 'firestore'] and firestore_sync_service.is_available():
            firestore_metrics = _get_firestore_metrics(start_time, end_time)
            response_data['sources']['firestore'] = firestore_metrics
            response_data['data_freshness']['firestore'] = _get_data_freshness('firestore')
        
        # Get LangWatch data if available and requested
        if source_filter in ['all', 'langwatch'] and langwatch_client.is_enabled():
            langwatch_metrics = langwatch_client.get_performance_metrics(hours=hours)
            response_data['sources']['langwatch'] = langwatch_metrics
            response_data['data_freshness']['langwatch'] = datetime.utcnow().isoformat()
        
        # Get webhook data if requested
        if source_filter in ['all', 'webhook']:
            webhook_metrics = _get_webhook_metrics(start_time, end_time)
            response_data['sources']['webhook'] = webhook_metrics
            response_data['data_freshness']['webhook'] = _get_data_freshness('webhook')
        
        # Combine metrics from all sources
        response_data['combined_metrics'] = _combine_metrics(response_data['sources'])
        
        return jsonify({
            'success': True,
            'data': response_data,
            'metadata': {
                'generated_at': datetime.utcnow().isoformat(),
                'sources_available': list(response_data['sources'].keys()),
                'query_duration_ms': 0  # Would be calculated in production
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting live metrics: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'data': {}
        }), 500

@live_data_bp.route('/api/live-traces')
@login_required  
def get_live_traces():
    """
    Get live trace data with real-time updates.
    
    Query Parameters:
    - limit: Number of traces to return (default: 50, max: 500)
    - offset: Pagination offset
    - status: Status filter ('all', 'success', 'error', 'pending')
    - source: Data source filter
    - model: Model filter
    - user_id: User filter
    """
    try:
        limit = min(request.args.get('limit', 50, type=int), 500)
        offset = max(request.args.get('offset', 0, type=int), 0)
        status_filter = request.args.get('status', 'all')
        source_filter = request.args.get('source', 'all')
        model_filter = request.args.get('model')
        user_filter = request.args.get('user_id')
        
        # Build query conditions
        where_conditions = ['1=1']
        query_params = {}
        
        if status_filter != 'all':
            where_conditions.append('status = :status')
            query_params['status'] = status_filter
        
        if source_filter != 'all':
            where_conditions.append('data_source LIKE :source')
            query_params['source'] = f'%{source_filter}%'
        
        if model_filter:
            where_conditions.append('model = :model')
            query_params['model'] = model_filter
        
        if user_filter:
            where_conditions.append('user_id = :user_id')
            query_params['user_id'] = user_filter
        
        # Execute query
        query = f"""
        SELECT 
            external_trace_id,
            name,
            status,
            model,
            start_time,
            end_time,
            duration_ms,
            input_tokens,
            output_tokens,
            cost_usd,
            user_id,
            session_id,
            data_source,
            created_at,
            updated_at
        FROM live_traces 
        WHERE {' AND '.join(where_conditions)}
        ORDER BY start_time DESC 
        LIMIT :limit OFFSET :offset
        """
        
        query_params.update({'limit': limit, 'offset': offset})
        
        results = db.session.execute(text(query), query_params).fetchall()
        
        # Format results
        traces = []
        for row in results:
            traces.append({
                'id': row[0],
                'name': row[1],
                'status': row[2],
                'model': row[3],
                'start_time': row[4].isoformat() if row[4] else None,
                'end_time': row[5].isoformat() if row[5] else None,
                'duration_ms': row[6],
                'input_tokens': row[7] or 0,
                'output_tokens': row[8] or 0,
                'cost_usd': float(row[9]) if row[9] else 0.0,
                'user_id': row[10],
                'session_id': row[11],
                'data_source': row[12],
                'created_at': row[13].isoformat() if row[13] else None,
                'updated_at': row[14].isoformat() if row[14] else None
            })
        
        # Get total count for pagination
        count_query = f"""
        SELECT COUNT(*) FROM live_traces 
        WHERE {' AND '.join(where_conditions)}
        """
        
        total_count = db.session.execute(
            text(count_query), 
            {k: v for k, v in query_params.items() if k not in ['limit', 'offset']}
        ).scalar()
        
        return jsonify({
            'success': True,
            'traces': traces,
            'pagination': {
                'limit': limit,
                'offset': offset,
                'total': total_count,
                'has_more': (offset + limit) < total_count
            },
            'filters_applied': {
                'status': status_filter,
                'source': source_filter,
                'model': model_filter,
                'user_id': user_filter
            },
            'metadata': {
                'generated_at': datetime.utcnow().isoformat(),
                'query_time_ms': 0  # Would be calculated in production
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting live traces: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'traces': []
        }), 500

@live_data_bp.route('/api/sync-status')
@login_required
def get_sync_status():
    """Get synchronization status for all data sources."""
    try:
        # Get Firestore sync status
        firestore_stats = firestore_sync_service.get_sync_statistics()
        
        # Get webhook status
        webhook_stats = webhook_handler.get_webhook_statistics()
        
        # Get LangWatch connection status
        langwatch_status = {
            'enabled': langwatch_client.is_enabled(),
            'last_request': datetime.utcnow().isoformat()
        }
        
        return jsonify({
            'success': True,
            'sync_status': {
                'firestore': firestore_stats,
                'webhook': webhook_stats,
                'langwatch': langwatch_status
            },
            'overall_health': _calculate_overall_health(firestore_stats, webhook_stats, langwatch_status),
            'last_updated': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting sync status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# WEBHOOK ENDPOINTS
# ============================================================================

@live_data_bp.route('/webhooks/<source>', methods=['POST'])
def receive_webhook(source):
    """
    Secure webhook endpoint for receiving real-time data updates.
    
    Supports: langwatch, langfuse, custom
    Security: HMAC signature verification
    """
    try:
        # Get request data
        payload = request.get_json(force=True)
        signature = request.headers.get('X-Signature') or request.headers.get('X-Hub-Signature-256')
        
        # Process webhook
        result = webhook_handler.process_webhook(
            source=source,
            payload=payload,
            signature=signature
        )
        
        if result.get('status') == 'success':
            return jsonify(result), 200
        elif result.get('status') == 'duplicate':
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Error processing webhook from {source}: {e}")
        return jsonify({
            'status': 'error',
            'error': str(e)
        }), 500

# ============================================================================
# SYNC MANAGEMENT ENDPOINTS
# ============================================================================

@live_data_bp.route('/api/sync/trigger', methods=['POST'])
@login_required
def trigger_sync():
    """
    Manually trigger data synchronization.
    
    Requires admin privileges.
    """
    if not current_user.is_admin:
        return jsonify({
            'success': False,
            'error': 'Admin privileges required'
        }), 403
    
    try:
        sync_type = request.json.get('sync_type', 'firestore')
        hours_back = min(request.json.get('hours_back', 24), 168)
        force_full = request.json.get('force_full', False)
        
        if sync_type == 'firestore':
            if force_full:
                result = firestore_sync_service.force_full_sync(hours_back=hours_back)
            else:
                result = firestore_sync_service.sync_traces_from_firestore(hours_back=hours_back)
            
            return jsonify({
                'success': result.success,
                'sync_type': sync_type,
                'records_processed': result.records_processed,
                'errors': result.errors,
                'metadata': result.metadata
            })
        else:
            return jsonify({
                'success': False,
                'error': f'Unsupported sync type: {sync_type}'
            }), 400
            
    except Exception as e:
        logger.error(f"Error triggering sync: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def _get_firestore_metrics(start_time: datetime, end_time: datetime) -> dict:
    """Get metrics from Firestore-synced data."""
    try:
        query = """
        SELECT 
            COUNT(*) as total_traces,
            SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
            SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as error_count,
            AVG(duration_ms) as avg_latency,
            SUM(cost_usd) as total_cost,
            SUM(input_tokens) as total_input_tokens,
            SUM(output_tokens) as total_output_tokens
        FROM live_traces 
        WHERE data_source = 'firestore' 
        AND start_time BETWEEN :start_time AND :end_time
        """
        
        result = db.session.execute(text(query), {
            'start_time': start_time,
            'end_time': end_time
        }).fetchone()
        
        if result and result[0] > 0:
            total = result[0]
            success = result[1] or 0
            error = result[2] or 0
            
            return {
                'total_traces': total,
                'success_count': success,
                'error_count': error,
                'success_rate': round((success / total * 100), 2) if total > 0 else 0,
                'error_rate': round((error / total * 100), 2) if total > 0 else 0,
                'average_latency_ms': round(result[3] or 0, 2),
                'total_cost': round(result[4] or 0, 6),
                'total_input_tokens': result[5] or 0,
                'total_output_tokens': result[6] or 0
            }
        else:
            return {
                'total_traces': 0,
                'success_count': 0,
                'error_count': 0,
                'success_rate': 0,
                'error_rate': 0,
                'average_latency_ms': 0,
                'total_cost': 0,
                'total_input_tokens': 0,
                'total_output_tokens': 0
            }
            
    except Exception as e:
        logger.error(f"Error getting Firestore metrics: {e}")
        return {}

def _get_webhook_metrics(start_time: datetime, end_time: datetime) -> dict:
    """Get metrics from webhook data."""
    try:
        # Get webhook processing stats
        webhook_query = """
        SELECT 
            COUNT(*) as total_events,
            SUM(CASE WHEN processed THEN 1 ELSE 0 END) as processed_events,
            COUNT(DISTINCT source) as active_sources
        FROM webhook_events
        WHERE received_at BETWEEN :start_time AND :end_time
        """
        
        webhook_result = db.session.execute(text(webhook_query), {
            'start_time': start_time,
            'end_time': end_time
        }).fetchone()
        
        # Get trace metrics from webhook sources
        trace_query = """
        SELECT 
            COUNT(*) as total_traces,
            SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) as success_count,
            AVG(duration_ms) as avg_latency,
            SUM(cost_usd) as total_cost
        FROM live_traces 
        WHERE data_source LIKE 'webhook%'
        AND start_time BETWEEN :start_time AND :end_time
        """
        
        trace_result = db.session.execute(text(trace_query), {
            'start_time': start_time,
            'end_time': end_time
        }).fetchone()
        
        return {
            'webhook_events': {
                'total_events': webhook_result[0] if webhook_result else 0,
                'processed_events': webhook_result[1] if webhook_result else 0,
                'active_sources': webhook_result[2] if webhook_result else 0
            },
            'trace_metrics': {
                'total_traces': trace_result[0] if trace_result else 0,
                'success_count': trace_result[1] if trace_result else 0,
                'average_latency_ms': round(trace_result[2] or 0, 2),
                'total_cost': round(trace_result[3] or 0, 6)
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting webhook metrics: {e}")
        return {}

def _combine_metrics(sources_data: dict) -> dict:
    """Combine metrics from multiple sources."""
    combined = {
        'total_traces': 0,
        'success_count': 0,
        'error_count': 0,
        'success_rate': 0,
        'error_rate': 0,
        'average_latency_ms': 0,
        'total_cost': 0,
        'sources_contributing': []
    }
    
    total_traces = 0
    total_success = 0
    total_errors = 0
    weighted_latency = 0
    total_cost = 0
    
    for source_name, source_data in sources_data.items():
        if isinstance(source_data, dict) and 'total_traces' in source_data:
            traces = source_data.get('total_traces', 0)
            success = source_data.get('success_count', 0)
            errors = source_data.get('error_count', 0)
            latency = source_data.get('average_latency_ms', 0)
            cost = source_data.get('total_cost', 0)
            
            total_traces += traces
            total_success += success
            total_errors += errors
            weighted_latency += latency * traces if traces > 0 else 0
            total_cost += cost
            
            if traces > 0:
                combined['sources_contributing'].append(source_name)
    
    # Calculate combined metrics
    if total_traces > 0:
        combined['total_traces'] = total_traces
        combined['success_count'] = total_success
        combined['error_count'] = total_errors
        combined['success_rate'] = round((total_success / total_traces * 100), 2)
        combined['error_rate'] = round((total_errors / total_traces * 100), 2)
        combined['average_latency_ms'] = round(weighted_latency / total_traces, 2)
        combined['total_cost'] = round(total_cost, 6)
    
    return combined

def _get_data_freshness(source: str) -> str:
    """Get data freshness indicator for a source."""
    try:
        if source == 'firestore':
            result = db.session.execute(
                text("SELECT MAX(updated_at) FROM live_traces WHERE data_source = 'firestore'")
            ).scalar()
        elif source == 'webhook':
            result = db.session.execute(
                text("SELECT MAX(processed_at) FROM webhook_events WHERE processed = 1")
            ).scalar()
        else:
            return datetime.utcnow().isoformat()
        
        return result.isoformat() if result else 'No data'
        
    except Exception:
        return 'Unknown'

def _calculate_overall_health(firestore_stats: dict, webhook_stats: dict, langwatch_status: dict) -> dict:
    """Calculate overall system health score."""
    health_score = 0
    max_score = 100
    issues = []
    
    # Firestore health (40 points)
    if firestore_stats.get('is_available'):
        health_score += 20
        sync_statuses = firestore_stats.get('sync_statuses', [])
        if sync_statuses and any(s['status'] == 'success' for s in sync_statuses):
            health_score += 20
        else:
            issues.append("Firestore sync issues detected")
    else:
        issues.append("Firestore not available")
    
    # Webhook health (30 points)
    webhook_events = webhook_stats.get('event_statistics', [])
    if webhook_events:
        success_rates = [e.get('success_rate', 0) for e in webhook_events]
        avg_success_rate = sum(success_rates) / len(success_rates) if success_rates else 0
        health_score += int(avg_success_rate * 0.3)
        if avg_success_rate < 95:
            issues.append(f"Webhook success rate low: {avg_success_rate:.1f}%")
    else:
        health_score += 15  # No webhooks but no issues
    
    # LangWatch health (30 points)
    if langwatch_status.get('enabled'):
        health_score += 30
    else:
        issues.append("LangWatch integration not enabled")
    
    # Determine overall status
    if health_score >= 90:
        status = 'excellent'
    elif health_score >= 70:
        status = 'good'
    elif health_score >= 50:
        status = 'fair'
    else:
        status = 'poor'
    
    return {
        'score': health_score,
        'max_score': max_score,
        'percentage': round((health_score / max_score) * 100, 1),
        'status': status,
        'issues': issues,
        'last_calculated': datetime.utcnow().isoformat()
    }