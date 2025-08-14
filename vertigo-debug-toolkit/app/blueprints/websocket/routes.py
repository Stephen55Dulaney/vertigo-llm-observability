"""
WebSocket management routes and real-time event handlers.
"""

from flask import render_template, jsonify, request
from flask_login import login_required, current_user
from app.blueprints.websocket import websocket_bp
from app.services.websocket_service import get_websocket_service, MessageType
from app.services.performance_optimizer import performance_optimizer
from app.services.cache_service import default_cache_service
from app.services.analytics_service import analytics_service
import logging

logger = logging.getLogger(__name__)


@websocket_bp.route('/')
@login_required
def websocket_dashboard():
    """WebSocket management dashboard."""
    try:
        ws_service = get_websocket_service()
        if not ws_service:
            return render_template('error.html', error="WebSocket service not initialized"), 500
        
        stats = ws_service.get_connection_stats()
        return render_template('websocket/index.html', websocket_stats=stats)
        
    except Exception as e:
        logger.error(f"Error loading WebSocket dashboard: {e}")
        return render_template('error.html', error="Failed to load WebSocket dashboard"), 500


@websocket_bp.route('/api/stats')
@login_required
def get_websocket_stats():
    """Get WebSocket connection statistics."""
    try:
        ws_service = get_websocket_service()
        if not ws_service:
            return jsonify({
                "success": False,
                "error": "WebSocket service not available"
            }), 503
        
        stats = ws_service.get_connection_stats()
        
        return jsonify({
            "success": True,
            "stats": stats
        })
        
    except Exception as e:
        logger.error(f"Error getting WebSocket stats: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@websocket_bp.route('/api/rooms/<room_name>')
@login_required
def get_room_info(room_name):
    """Get information about a specific room."""
    try:
        ws_service = get_websocket_service()
        if not ws_service:
            return jsonify({
                "success": False,
                "error": "WebSocket service not available"
            }), 503
        
        room_info = ws_service.get_room_info(room_name)
        
        return jsonify({
            "success": True,
            "room": room_name,
            "info": room_info
        })
        
    except Exception as e:
        logger.error(f"Error getting room info: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@websocket_bp.route('/api/broadcast', methods=['POST'])
@login_required
def broadcast_message():
    """Broadcast message to WebSocket clients."""
    try:
        ws_service = get_websocket_service()
        if not ws_service:
            return jsonify({
                "success": False,
                "error": "WebSocket service not available"
            }), 503
        
        data = request.get_json()
        
        if not data or 'type' not in data or 'data' not in data:
            return jsonify({
                "success": False,
                "error": "Invalid message format"
            }), 400
        
        # Validate message type
        try:
            message_type = MessageType(data['type'])
        except ValueError:
            return jsonify({
                "success": False,
                "error": f"Invalid message type: {data['type']}"
            }), 400
        
        # Create and broadcast message
        from app.services.websocket_service import WebSocketMessage
        message = WebSocketMessage(
            type=message_type,
            data=data['data'],
            room=data.get('room'),
            target_user=data.get('target_user'),
            target_tenant=data.get('target_tenant'),
            priority=data.get('priority', 'normal')
        )
        
        recipients = ws_service.broadcast_message(message)
        
        return jsonify({
            "success": True,
            "message": f"Message broadcast to {recipients} recipients",
            "recipients": recipients
        })
        
    except Exception as e:
        logger.error(f"Error broadcasting message: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@websocket_bp.route('/api/trigger-refresh', methods=['POST'])
@login_required
def trigger_dashboard_refresh():
    """Trigger dashboard refresh for all clients."""
    try:
        ws_service = get_websocket_service()
        if not ws_service:
            return jsonify({
                "success": False,
                "error": "WebSocket service not available"
            }), 503
        
        data = request.get_json() or {}
        components = data.get('components', ['all'])
        
        ws_service.trigger_dashboard_refresh(components)
        
        return jsonify({
            "success": True,
            "message": f"Dashboard refresh triggered for components: {components}"
        })
        
    except Exception as e:
        logger.error(f"Error triggering refresh: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@websocket_bp.route('/api/send-performance-update', methods=['POST'])
@login_required
def send_performance_update():
    """Send performance metrics update to WebSocket clients."""
    try:
        ws_service = get_websocket_service()
        if not ws_service:
            return jsonify({
                "success": False,
                "error": "WebSocket service not available"
            }), 503
        
        # Get latest performance metrics
        profile = performance_optimizer.collect_metrics()
        metrics = {
            'cpu_usage': profile.cpu_usage_percent,
            'memory_usage': profile.memory_usage_percent,
            'cache_hit_ratio': profile.cache_hit_ratio,
            'timestamp': profile.timestamp.isoformat()
        }
        
        ws_service.send_performance_update(metrics)
        
        return jsonify({
            "success": True,
            "message": "Performance update sent",
            "metrics": metrics
        })
        
    except Exception as e:
        logger.error(f"Error sending performance update: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@websocket_bp.route('/api/send-cache-update', methods=['POST'])
@login_required
def send_cache_update():
    """Send cache statistics update to WebSocket clients."""
    try:
        ws_service = get_websocket_service()
        if not ws_service:
            return jsonify({
                "success": False,
                "error": "WebSocket service not available"
            }), 503
        
        # Get latest cache statistics
        cache_stats = default_cache_service.get_stats()
        
        ws_service.send_cache_stats_update(cache_stats)
        
        return jsonify({
            "success": True,
            "message": "Cache update sent",
            "stats": cache_stats
        })
        
    except Exception as e:
        logger.error(f"Error sending cache update: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@websocket_bp.route('/api/send-analytics-update', methods=['POST'])
@login_required
def send_analytics_update():
    """Send analytics update to WebSocket clients."""
    try:
        ws_service = get_websocket_service()
        if not ws_service:
            return jsonify({
                "success": False,
                "error": "WebSocket service not available"
            }), 503
        
        # Get latest analytics summary
        analytics_summary = analytics_service.get_analytics_summary()
        
        ws_service.send_analytics_update(analytics_summary)
        
        return jsonify({
            "success": True,
            "message": "Analytics update sent",
            "analytics": analytics_summary
        })
        
    except Exception as e:
        logger.error(f"Error sending analytics update: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@websocket_bp.route('/api/send-alert', methods=['POST'])
@login_required
def send_alert_notification():
    """Send alert notification to WebSocket clients."""
    try:
        ws_service = get_websocket_service()
        if not ws_service:
            return jsonify({
                "success": False,
                "error": "WebSocket service not available"
            }), 503
        
        data = request.get_json()
        
        if not data or 'alert' not in data:
            return jsonify({
                "success": False,
                "error": "Alert data is required"
            }), 400
        
        alert = data['alert']
        priority = data.get('priority', 'normal')
        
        ws_service.send_alert_notification(alert, priority)
        
        return jsonify({
            "success": True,
            "message": "Alert notification sent",
            "alert": alert
        })
        
    except Exception as e:
        logger.error(f"Error sending alert: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@websocket_bp.route('/api/test-connection', methods=['POST'])
@login_required
def test_websocket_connection():
    """Test WebSocket connectivity."""
    try:
        ws_service = get_websocket_service()
        if not ws_service:
            return jsonify({
                "success": False,
                "error": "WebSocket service not available"
            }), 503
        
        # Send test message to all connections
        from app.services.websocket_service import WebSocketMessage
        test_message = WebSocketMessage(
            type=MessageType.SYSTEM_STATUS,
            data={
                'test': True,
                'message': 'WebSocket connection test',
                'timestamp': datetime.now().isoformat(),
                'sent_by': current_user.username if current_user else 'system'
            }
        )
        
        recipients = ws_service.broadcast_message(test_message)
        
        return jsonify({
            "success": True,
            "message": f"Test message sent to {recipients} connections",
            "recipients": recipients,
            "websocket_stats": ws_service.get_connection_stats()
        })
        
    except Exception as e:
        logger.error(f"Error testing WebSocket connection: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500