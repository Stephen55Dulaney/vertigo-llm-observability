"""
Anomaly Response Blueprint for Vertigo Debug Toolkit
Provides API endpoints for anomaly monitoring and automated response management.
"""

import json
import logging
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template
from app.services.anomaly_monitoring_engine import anomaly_monitoring_engine, MonitoringConfig
from app.services.automated_response_engine import automated_response_engine

logger = logging.getLogger(__name__)

anomaly_response_bp = Blueprint('anomaly_response', __name__, url_prefix='/anomaly-response')

@anomaly_response_bp.route('/')
def dashboard():
    """Anomaly response dashboard."""
    try:
        # Get monitoring status
        monitoring_status = anomaly_monitoring_engine.get_status()
        
        # Get recent anomalies
        recent_anomalies = anomaly_monitoring_engine.get_recent_anomalies(limit=20)
        
        # Get response statistics
        response_stats = automated_response_engine.get_response_statistics()
        
        # Get pending approvals
        pending_approvals = automated_response_engine.get_pending_approvals()
        
        return render_template(
            'anomaly_response/dashboard.html',
            monitoring_status=monitoring_status,
            recent_anomalies=recent_anomalies,
            response_stats=response_stats,
            pending_approvals=pending_approvals
        )
        
    except Exception as e:
        logger.error(f"Error loading anomaly response dashboard: {e}")
        return render_template('error.html', error=str(e)), 500

@anomaly_response_bp.route('/api/monitoring/start', methods=['POST'])
def start_monitoring():
    """Start anomaly monitoring."""
    try:
        success = anomaly_monitoring_engine.start_monitoring()
        return jsonify({
            'success': success,
            'message': 'Monitoring started successfully' if success else 'Failed to start monitoring',
            'status': anomaly_monitoring_engine.get_status()
        })
        
    except Exception as e:
        logger.error(f"Error starting monitoring: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@anomaly_response_bp.route('/api/monitoring/stop', methods=['POST'])
def stop_monitoring():
    """Stop anomaly monitoring."""
    try:
        success = anomaly_monitoring_engine.stop_monitoring()
        return jsonify({
            'success': success,
            'message': 'Monitoring stopped successfully' if success else 'Failed to stop monitoring',
            'status': anomaly_monitoring_engine.get_status()
        })
        
    except Exception as e:
        logger.error(f"Error stopping monitoring: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@anomaly_response_bp.route('/api/monitoring/status')
def get_monitoring_status():
    """Get monitoring status."""
    try:
        status = anomaly_monitoring_engine.get_status()
        return jsonify(status)
        
    except Exception as e:
        logger.error(f"Error getting monitoring status: {e}")
        return jsonify({'error': str(e)}), 500

@anomaly_response_bp.route('/api/monitoring/config', methods=['GET', 'POST'])
def monitoring_config():
    """Get or update monitoring configuration."""
    try:
        if request.method == 'GET':
            return jsonify({
                'config': {
                    'poll_interval_seconds': anomaly_monitoring_engine.config.poll_interval_seconds,
                    'anomaly_detection_window': anomaly_monitoring_engine.config.anomaly_detection_window,
                    'statistical_threshold': anomaly_monitoring_engine.config.statistical_threshold,
                    'correlation_threshold': anomaly_monitoring_engine.config.correlation_threshold,
                    'max_alerts_per_minute': anomaly_monitoring_engine.config.max_alerts_per_minute,
                    'enable_auto_response': anomaly_monitoring_engine.config.enable_auto_response,
                    'monitored_metrics': anomaly_monitoring_engine.config.monitored_metrics
                }
            })
        
        elif request.method == 'POST':
            data = request.get_json()
            
            # Update configuration
            if 'poll_interval_seconds' in data:
                anomaly_monitoring_engine.config.poll_interval_seconds = int(data['poll_interval_seconds'])
            if 'statistical_threshold' in data:
                anomaly_monitoring_engine.config.statistical_threshold = float(data['statistical_threshold'])
            if 'enable_auto_response' in data:
                anomaly_monitoring_engine.config.enable_auto_response = bool(data['enable_auto_response'])
            if 'monitored_metrics' in data:
                anomaly_monitoring_engine.config.monitored_metrics = data['monitored_metrics']
            
            return jsonify({
                'success': True,
                'message': 'Configuration updated successfully',
                'config': anomaly_monitoring_engine.config.__dict__
            })
    
    except Exception as e:
        logger.error(f"Error handling monitoring config: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@anomaly_response_bp.route('/api/anomalies')
def get_anomalies():
    """Get recent anomalies."""
    try:
        limit = request.args.get('limit', 50, type=int)
        anomalies = anomaly_monitoring_engine.get_recent_anomalies(limit=limit)
        
        # Convert to serializable format
        anomalies_data = []
        for anomaly in anomalies:
            anomalies_data.append({
                'id': anomaly.id,
                'timestamp': anomaly.timestamp.isoformat(),
                'anomaly_type': anomaly.anomaly_type.value,
                'metric_name': anomaly.metric_name,
                'severity': anomaly.severity.value,
                'actual_value': anomaly.actual_value,
                'expected_value': anomaly.expected_value,
                'deviation_score': anomaly.deviation_score,
                'message': anomaly.message,
                'context_data': anomaly.context_data,
                'auto_response_triggered': anomaly.auto_response_triggered,
                'response_actions': anomaly.response_actions
            })
        
        return jsonify({
            'anomalies': anomalies_data,
            'count': len(anomalies_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting anomalies: {e}")
        return jsonify({'error': str(e)}), 500

@anomaly_response_bp.route('/api/anomalies/clear', methods=['POST'])
def clear_anomalies():
    """Clear old anomalies."""
    try:
        older_than_minutes = request.args.get('older_than_minutes', 60, type=int)
        anomaly_monitoring_engine.clear_alerts(older_than_minutes=older_than_minutes)
        
        return jsonify({
            'success': True,
            'message': f'Cleared anomalies older than {older_than_minutes} minutes'
        })
        
    except Exception as e:
        logger.error(f"Error clearing anomalies: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@anomaly_response_bp.route('/api/responses/statistics')
def get_response_statistics():
    """Get automated response statistics."""
    try:
        stats = automated_response_engine.get_response_statistics()
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting response statistics: {e}")
        return jsonify({'error': str(e)}), 500

@anomaly_response_bp.route('/api/responses/pending-approvals')
def get_pending_approvals():
    """Get pending approval requests."""
    try:
        approvals = automated_response_engine.get_pending_approvals()
        return jsonify({
            'pending_approvals': approvals,
            'count': len(approvals)
        })
        
    except Exception as e:
        logger.error(f"Error getting pending approvals: {e}")
        return jsonify({'error': str(e)}), 500

@anomaly_response_bp.route('/api/responses/approve/<execution_id>', methods=['POST'])
def approve_response(execution_id):
    """Approve or reject a pending response action."""
    try:
        data = request.get_json()
        approved = data.get('approved', False)
        approver = data.get('approver', 'anonymous')
        
        success = automated_response_engine.approve_pending_action(
            execution_id=execution_id,
            approved=approved,
            approver=approver
        )
        
        action = 'approved' if approved else 'rejected'
        return jsonify({
            'success': success,
            'message': f'Response action {action} successfully' if success else f'Failed to {action} response action',
            'execution_id': execution_id,
            'approved': approved,
            'approver': approver
        })
        
    except Exception as e:
        logger.error(f"Error approving response {execution_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@anomaly_response_bp.route('/api/responses/rollback/<execution_id>', methods=['POST'])
def rollback_response(execution_id):
    """Rollback a previously executed response action."""
    try:
        success = automated_response_engine.rollback_execution(execution_id)
        
        return jsonify({
            'success': success,
            'message': 'Response rolled back successfully' if success else 'Failed to rollback response',
            'execution_id': execution_id
        })
        
    except Exception as e:
        logger.error(f"Error rolling back response {execution_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@anomaly_response_bp.route('/api/responses/execution/<execution_id>')
def get_execution_status(execution_id):
    """Get the status of a specific response execution."""
    try:
        execution = automated_response_engine.get_execution_status(execution_id)
        
        if not execution:
            return jsonify({'error': 'Execution not found'}), 404
        
        # Convert to serializable format
        execution_data = {
            'id': execution.id,
            'action_id': execution.action_id,
            'anomaly_id': execution.anomaly_id,
            'started_at': execution.started_at.isoformat(),
            'completed_at': execution.completed_at.isoformat() if execution.completed_at else None,
            'status': execution.status.value,
            'result_data': execution.result_data,
            'error_message': execution.error_message,
            'rollback_executed': execution.rollback_executed,
            'human_approved': execution.human_approved,
            'impact_assessment': execution.impact_assessment
        }
        
        return jsonify(execution_data)
        
    except Exception as e:
        logger.error(f"Error getting execution status {execution_id}: {e}")
        return jsonify({'error': str(e)}), 500

@anomaly_response_bp.route('/api/responses/cleanup', methods=['POST'])
def cleanup_responses():
    """Clean up old completed response executions."""
    try:
        older_than_hours = request.args.get('older_than_hours', 24, type=int)
        automated_response_engine.cleanup_completed_executions(older_than_hours=older_than_hours)
        
        return jsonify({
            'success': True,
            'message': f'Cleaned up executions older than {older_than_hours} hours'
        })
        
    except Exception as e:
        logger.error(f"Error cleaning up responses: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@anomaly_response_bp.route('/api/health')
def health_check():
    """Health check endpoint for anomaly response system."""
    try:
        monitoring_status = anomaly_monitoring_engine.get_status()
        response_stats = automated_response_engine.get_response_statistics()
        
        health_data = {
            'status': 'healthy',
            'monitoring_engine': {
                'status': monitoring_status['status'],
                'thread_alive': monitoring_status['thread_alive'],
                'last_check': monitoring_status['statistics']['last_check_timestamp']
            },
            'response_engine': {
                'active_executions': response_stats['active_executions'],
                'success_rate': response_stats['success_rate'],
                'pending_approvals': response_stats['pending_approvals']
            },
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return jsonify(health_data)
        
    except Exception as e:
        logger.error(f"Error in health check: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500