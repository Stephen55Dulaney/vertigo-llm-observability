"""
Webhook Routes for LangWatch Integration
Secure endpoints for receiving real-time trace data.
"""

import json
import logging
from flask import request, jsonify, current_app
from flask_login import login_required
from app.blueprints.webhooks import webhooks_bp
from app.services.webhook_service import webhook_service
from app import csrf

logger = logging.getLogger(__name__)

@webhooks_bp.route('/langwatch', methods=['POST'])
@csrf.exempt
def langwatch_webhook():
    """
    Primary webhook endpoint for LangWatch trace events.
    
    Security:
    - HMAC signature verification
    - Event deduplication
    - Rate limiting (if configured)
    
    Supported Events:
    - trace.created
    - trace.updated
    - trace.completed
    - span.created
    - span.updated
    """
    try:
        # Get raw payload for signature verification
        payload = request.get_data()
        signature = request.headers.get('X-LangWatch-Signature', '')
        
        # Verify webhook signature
        if not webhook_service.verify_webhook_signature(payload, signature):
            logger.warning(f"Invalid webhook signature from IP: {request.remote_addr}")
            return jsonify({
                'success': False,
                'error': 'Invalid signature'
            }), 401
        
        # Parse JSON payload
        try:
            data = json.loads(payload.decode('utf-8'))
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON payload: {e}")
            return jsonify({
                'success': False,
                'error': 'Invalid JSON payload'
            }), 400
        
        # Process webhook payload
        result = webhook_service.process_webhook_payload(data)
        
        # Log successful processing
        if result.get('success'):
            logger.info(f"Successfully processed {result.get('event_type')} for trace {result.get('trace_id')}")
        else:
            logger.error(f"Failed to process webhook: {result.get('error')}")
        
        # Return appropriate HTTP status
        status_code = 200 if result.get('success') else 400
        return jsonify(result), status_code
        
    except Exception as e:
        logger.error(f"Error in LangWatch webhook: {e}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@webhooks_bp.route('/langwatch/test', methods=['POST'])
@csrf.exempt
def langwatch_webhook_test():
    """
    Test endpoint for webhook development and debugging.
    Only enabled in development mode.
    """
    if not current_app.debug:
        return jsonify({'error': 'Test endpoint only available in debug mode'}), 404
    
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No JSON payload provided'
            }), 400
        
        # Process test payload without signature verification
        result = webhook_service.process_webhook_payload(data)
        
        return jsonify({
            'test_mode': True,
            'signature_verified': False,
            **result
        })
        
    except Exception as e:
        logger.error(f"Error in webhook test endpoint: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@webhooks_bp.route('/status', methods=['GET'])
@login_required
def webhook_status():
    """
    Get webhook service status and statistics.
    Requires authentication for security.
    """
    try:
        stats = webhook_service.get_webhook_statistics()
        
        return jsonify({
            'success': True,
            'webhook_service': {
                'status': 'operational',
                'secret_configured': stats.get('webhook_secret_configured', False),
                'supported_events': stats.get('supported_events', [])
            },
            'statistics': stats.get('event_statistics', []),
            'recent_events': stats.get('recent_events', [])
        })
        
    except Exception as e:
        logger.error(f"Error getting webhook status: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@webhooks_bp.route('/config', methods=['GET'])
@login_required
def webhook_config():
    """
    Get webhook configuration information.
    For admin use in setting up LangWatch integration.
    """
    try:
        webhook_url = request.url_root.rstrip('/') + '/api/webhooks/langwatch'
        
        return jsonify({
            'success': True,
            'webhook_configuration': {
                'webhook_url': webhook_url,
                'supported_events': list(webhook_service.supported_events),
                'signature_header': 'X-LangWatch-Signature',
                'content_type': 'application/json',
                'secret_configured': bool(webhook_service.webhook_secret),
                'max_event_age_minutes': webhook_service.max_event_age_minutes,
                'deduplication_window_minutes': webhook_service.deduplication_window_minutes
            },
            'setup_instructions': {
                'step1': 'Configure LANGWATCH_WEBHOOK_SECRET environment variable',
                'step2': f'Set webhook URL in LangWatch to: {webhook_url}',
                'step3': 'Enable desired event types in LangWatch dashboard',
                'step4': 'Test webhook with /api/webhooks/langwatch/test endpoint'
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting webhook config: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@webhooks_bp.route('/events/recent', methods=['GET'])
@login_required  
def recent_webhook_events():
    """
    Get recent webhook events for monitoring.
    Supports filtering and pagination.
    """
    try:
        # Get query parameters
        limit = min(int(request.args.get('limit', 50)), 100)
        event_type = request.args.get('event_type')
        status = request.args.get('status')
        
        # Get events with optional filtering
        # This would be implemented in webhook_service.get_recent_events()
        events = webhook_service.get_webhook_statistics()
        recent_events = events.get('recent_events', [])
        
        # Apply client-side filtering for now
        if event_type:
            recent_events = [e for e in recent_events if e.get('event_type') == event_type]
        if status:
            recent_events = [e for e in recent_events if e.get('status') == status]
        
        # Apply limit
        recent_events = recent_events[:limit]
        
        return jsonify({
            'success': True,
            'events': recent_events,
            'total_returned': len(recent_events),
            'filters_applied': {
                'event_type': event_type,
                'status': status,
                'limit': limit
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting recent webhook events: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@webhooks_bp.errorhandler(404)
def webhook_not_found(error):
    """Handle 404 errors for webhook endpoints."""
    return jsonify({
        'success': False,
        'error': 'Webhook endpoint not found',
        'available_endpoints': [
            '/api/webhooks/langwatch',
            '/api/webhooks/status',
            '/api/webhooks/config'
        ]
    }), 404

@webhooks_bp.errorhandler(405)
def method_not_allowed(error):
    """Handle method not allowed errors."""
    return jsonify({
        'success': False,
        'error': 'Method not allowed',
        'allowed_methods': ['POST', 'GET']
    }), 405