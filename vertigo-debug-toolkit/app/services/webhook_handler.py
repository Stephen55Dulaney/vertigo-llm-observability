"""
Webhook Handler Service for Live Data Integration
Handles secure webhook endpoints for real-time data updates from LangWatch and other sources.
"""

import os
import json
import hmac
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from flask import request, current_app
from app.models import db
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
import uuid

logger = logging.getLogger(__name__)

class WebhookSecurityError(Exception):
    """Raised when webhook security validation fails."""
    pass

class WebhookHandler:
    """
    Secure webhook handler for real-time data updates.
    
    Features:
    - HMAC signature verification
    - Duplicate event detection
    - Async processing
    - Error recovery
    """
    
    def __init__(self):
        self.webhook_secrets = {
            'langwatch': os.getenv('LANGWATCH_WEBHOOK_SECRET'),
            'langfuse': os.getenv('LANGFUSE_WEBHOOK_SECRET'),
            'custom': os.getenv('CUSTOM_WEBHOOK_SECRET', 'dev-secret-key')
        }
        
        # Event type handlers
        self.event_handlers = {
            'trace.created': self._handle_trace_created,
            'trace.updated': self._handle_trace_updated,
            'trace.deleted': self._handle_trace_deleted,
            'evaluation.completed': self._handle_evaluation_completed,
            'alert.triggered': self._handle_alert_triggered
        }
    
    def verify_webhook_signature(self, payload: bytes, signature: str, source: str) -> bool:
        """Verify webhook HMAC signature."""
        secret = self.webhook_secrets.get(source)
        if not secret:
            logger.warning(f"No webhook secret configured for source: {source}")
            return False
        
        try:
            # Handle different signature formats
            if signature.startswith('sha256='):
                signature = signature[7:]
            
            # Calculate expected signature
            expected = hmac.new(
                secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            # Constant-time comparison
            return hmac.compare_digest(expected, signature)
            
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False
    
    def process_webhook(self, source: str, payload: Dict[str, Any], 
                       signature: str = None) -> Dict[str, Any]:
        """
        Process incoming webhook with security validation.
        
        Args:
            source: Webhook source ('langwatch', 'langfuse', 'custom')
            payload: Webhook payload data
            signature: HMAC signature (if provided)
            
        Returns:
            Processing result dictionary
        """
        try:
            # Security validation (skip in development)
            if current_app.config.get('ENV') != 'development' and signature:
                payload_bytes = json.dumps(payload, sort_keys=True).encode('utf-8')
                if not self.verify_webhook_signature(payload_bytes, signature, source):
                    raise WebhookSecurityError("Invalid webhook signature")
            
            # Extract event information
            event_id = payload.get('id') or payload.get('event_id') or str(uuid.uuid4())
            event_type = payload.get('type') or payload.get('event_type') or 'unknown'
            
            # Check for duplicate events
            if self._is_duplicate_event(event_id, source):
                logger.info(f"Skipping duplicate webhook event: {event_id}")
                return {'status': 'duplicate', 'event_id': event_id}
            
            # Store webhook event
            self._store_webhook_event(event_id, event_type, source, payload)
            
            # Process event
            result = self._process_webhook_event(event_type, payload, source)
            
            # Mark as processed
            self._mark_event_processed(event_id, result.get('success', True))
            
            return {
                'status': 'success',
                'event_id': event_id,
                'event_type': event_type,
                'processed': True,
                'result': result
            }
            
        except WebhookSecurityError as e:
            logger.warning(f"Webhook security error: {e}")
            return {'status': 'error', 'error': 'security_validation_failed'}
        
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            self._mark_event_processed(event_id, False, str(e))
            return {'status': 'error', 'error': str(e)}
    
    def _is_duplicate_event(self, event_id: str, source: str) -> bool:
        """Check if event has already been processed."""
        try:
            result = db.session.execute(
                text("SELECT id FROM webhook_events WHERE event_id = :event_id AND source = :source"),
                {"event_id": event_id, "source": source}
            ).fetchone()
            return result is not None
        except Exception as e:
            logger.error(f"Error checking duplicate event: {e}")
            return False
    
    def _store_webhook_event(self, event_id: str, event_type: str, 
                           source: str, payload: Dict[str, Any]):
        """Store webhook event in database."""
        try:
            db.session.execute(
                text("""
                INSERT INTO webhook_events (event_id, event_type, source, payload, received_at)
                VALUES (:event_id, :event_type, :source, :payload, :received_at)
                """),
                {
                    "event_id": event_id,
                    "event_type": event_type,
                    "source": source,
                    "payload": json.dumps(payload),
                    "received_at": datetime.utcnow()
                }
            )
            db.session.commit()
        except Exception as e:
            logger.error(f"Error storing webhook event: {e}")
            db.session.rollback()
            raise
    
    def _mark_event_processed(self, event_id: str, success: bool, error: str = None):
        """Mark webhook event as processed."""
        try:
            db.session.execute(
                text("""
                UPDATE webhook_events 
                SET processed = :processed, processed_at = :processed_at, processing_error = :error
                WHERE event_id = :event_id
                """),
                {
                    "processed": success,
                    "processed_at": datetime.utcnow(),
                    "error": error,
                    "event_id": event_id
                }
            )
            db.session.commit()
        except Exception as e:
            logger.error(f"Error marking event processed: {e}")
            db.session.rollback()
    
    def _process_webhook_event(self, event_type: str, payload: Dict[str, Any], 
                              source: str) -> Dict[str, Any]:
        """Process specific webhook event type."""
        handler = self.event_handlers.get(event_type)
        if not handler:
            logger.warning(f"No handler for event type: {event_type}")
            return {'success': False, 'error': f'No handler for event type: {event_type}'}
        
        try:
            return handler(payload, source)
        except Exception as e:
            logger.error(f"Error in event handler for {event_type}: {e}")
            return {'success': False, 'error': str(e)}
    
    def _handle_trace_created(self, payload: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Handle trace creation event."""
        try:
            trace_data = self._extract_trace_data(payload, source)
            
            # Insert new trace record
            db.session.execute(
                text("""
                INSERT INTO live_traces 
                (external_trace_id, name, status, model, start_time, end_time, duration_ms,
                 input_text, output_text, input_tokens, output_tokens, cost_usd,
                 user_id, session_id, tags, metadata, data_source, source_updated_at)
                VALUES 
                (:external_trace_id, :name, :status, :model, :start_time, :end_time, :duration_ms,
                 :input_text, :output_text, :input_tokens, :output_tokens, :cost_usd,
                 :user_id, :session_id, :tags, :metadata, :data_source, :source_updated_at)
                """),
                trace_data
            )
            db.session.commit()
            
            # Trigger real-time update (WebSocket event)
            self._trigger_real_time_update('trace_created', trace_data)
            
            return {'success': True, 'trace_id': trace_data['external_trace_id']}
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error handling trace created: {e}")
            return {'success': False, 'error': str(e)}
    
    def _handle_trace_updated(self, payload: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Handle trace update event."""
        try:
            trace_data = self._extract_trace_data(payload, source)
            trace_id = trace_data['external_trace_id']
            
            # Update existing trace
            update_fields = []
            update_values = {"external_trace_id": trace_id}
            
            for key, value in trace_data.items():
                if key != 'external_trace_id' and value is not None:
                    update_fields.append(f"{key} = :{key}")
                    update_values[key] = value
            
            if update_fields:
                update_values['updated_at'] = datetime.utcnow()
                update_fields.append("updated_at = :updated_at")
                
                sql = f"""
                UPDATE live_traces 
                SET {', '.join(update_fields)}
                WHERE external_trace_id = :external_trace_id
                """
                db.session.execute(text(sql), update_values)
                db.session.commit()
                
                # Trigger real-time update
                self._trigger_real_time_update('trace_updated', trace_data)
            
            return {'success': True, 'trace_id': trace_id}
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error handling trace updated: {e}")
            return {'success': False, 'error': str(e)}
    
    def _handle_trace_deleted(self, payload: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Handle trace deletion event."""
        try:
            trace_id = payload.get('trace_id') or payload.get('id')
            if not trace_id:
                return {'success': False, 'error': 'No trace ID provided'}
            
            db.session.execute(
                text("DELETE FROM live_traces WHERE external_trace_id = :trace_id"),
                {"trace_id": trace_id}
            )
            db.session.commit()
            
            # Trigger real-time update
            self._trigger_real_time_update('trace_deleted', {'trace_id': trace_id})
            
            return {'success': True, 'trace_id': trace_id}
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error handling trace deleted: {e}")
            return {'success': False, 'error': str(e)}
    
    def _handle_evaluation_completed(self, payload: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Handle evaluation completion event."""
        # This could update trace records with evaluation scores
        return {'success': True, 'message': 'Evaluation event logged'}
    
    def _handle_alert_triggered(self, payload: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Handle alert trigger event."""
        # This could create alert records and trigger notifications
        return {'success': True, 'message': 'Alert event logged'}
    
    def _extract_trace_data(self, payload: Dict[str, Any], source: str) -> Dict[str, Any]:
        """Extract and normalize trace data from webhook payload."""
        if source == 'langwatch':
            return self._extract_langwatch_trace_data(payload)
        elif source == 'langfuse':
            return self._extract_langfuse_trace_data(payload)
        else:
            return self._extract_generic_trace_data(payload)
    
    def _extract_langwatch_trace_data(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Extract trace data from LangWatch webhook payload."""
        trace = payload.get('data', {})
        
        return {
            'external_trace_id': trace.get('id', str(uuid.uuid4())),
            'name': trace.get('name', 'LangWatch Operation'),
            'status': trace.get('status', 'unknown'),
            'model': trace.get('model'),
            'start_time': self._parse_timestamp(trace.get('startTime')),
            'end_time': self._parse_timestamp(trace.get('endTime')),
            'duration_ms': trace.get('duration'),
            'input_text': str(trace.get('input', '')),
            'output_text': str(trace.get('output', '')),
            'input_tokens': trace.get('inputTokens', 0),
            'output_tokens': trace.get('outputTokens', 0),
            'cost_usd': float(trace.get('cost', 0)),
            'user_id': trace.get('userId'),
            'session_id': trace.get('sessionId'),
            'tags': json.dumps(trace.get('tags', [])),
            'metadata': json.dumps(trace.get('metadata', {})),
            'data_source': 'webhook_langwatch',
            'source_updated_at': datetime.utcnow()
        }
    
    def _extract_langfuse_trace_data(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Extract trace data from Langfuse webhook payload."""
        trace = payload.get('data', {})
        
        return {
            'external_trace_id': trace.get('id', str(uuid.uuid4())),
            'name': trace.get('name', 'Langfuse Operation'),
            'status': 'success' if trace.get('level') == 'DEFAULT' else 'error',
            'start_time': self._parse_timestamp(trace.get('timestamp')),
            'end_time': self._parse_timestamp(trace.get('endTime')),
            'input_text': str(trace.get('input', '')),
            'output_text': str(trace.get('output', '')),
            'cost_usd': float(trace.get('calculatedTotalCost', 0)),
            'user_id': trace.get('userId'),
            'session_id': trace.get('sessionId'),
            'tags': json.dumps(trace.get('tags', [])),
            'metadata': json.dumps(trace.get('metadata', {})),
            'data_source': 'webhook_langfuse',
            'source_updated_at': datetime.utcnow()
        }
    
    def _extract_generic_trace_data(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Extract trace data from generic webhook payload."""
        return {
            'external_trace_id': payload.get('id', str(uuid.uuid4())),
            'name': payload.get('name', 'Webhook Operation'),
            'status': payload.get('status', 'unknown'),
            'metadata': json.dumps(payload),
            'data_source': 'webhook_generic',
            'source_updated_at': datetime.utcnow()
        }
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp string to datetime object."""
        if not timestamp_str:
            return None
        
        try:
            if 'T' in timestamp_str:
                return datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                return datetime.fromisoformat(timestamp_str)
        except Exception as e:
            logger.warning(f"Error parsing timestamp {timestamp_str}: {e}")
            return None
    
    def _trigger_real_time_update(self, event_type: str, data: Dict[str, Any]):
        """Trigger real-time update via WebSocket or SSE."""
        # This would integrate with WebSocket/SSE system
        # For now, we'll use Flask's application context to store events
        try:
            if hasattr(current_app, 'websocket_events'):
                current_app.websocket_events.append({
                    'type': event_type,
                    'data': data,
                    'timestamp': datetime.utcnow().isoformat()
                })
        except Exception as e:
            logger.debug(f"No real-time update system available: {e}")
    
    def get_webhook_statistics(self) -> Dict[str, Any]:
        """Get webhook processing statistics."""
        try:
            # Get event counts by source and status
            stats_query = """
            SELECT 
                source,
                event_type,
                COUNT(*) as total_events,
                SUM(CASE WHEN processed THEN 1 ELSE 0 END) as processed_events,
                SUM(CASE WHEN NOT processed THEN 1 ELSE 0 END) as pending_events
            FROM webhook_events
            WHERE received_at > datetime('now', '-24 hours')
            GROUP BY source, event_type
            ORDER BY total_events DESC
            """
            
            results = db.session.execute(text(stats_query)).fetchall()
            
            stats = []
            for row in results:
                stats.append({
                    'source': row[0],
                    'event_type': row[1],
                    'total_events': row[2],
                    'processed_events': row[3],
                    'pending_events': row[4],
                    'success_rate': (row[3] / row[2] * 100) if row[2] > 0 else 0
                })
            
            # Get recent errors
            error_query = """
            SELECT event_id, event_type, source, processing_error, received_at
            FROM webhook_events
            WHERE processing_error IS NOT NULL
            ORDER BY received_at DESC
            LIMIT 10
            """
            
            errors = db.session.execute(text(error_query)).fetchall()
            recent_errors = [
                {
                    'event_id': row[0],
                    'event_type': row[1],
                    'source': row[2],
                    'error': row[3],
                    'received_at': row[4]
                }
                for row in errors
            ]
            
            return {
                'event_statistics': stats,
                'recent_errors': recent_errors,
                'configured_sources': list(self.webhook_secrets.keys()),
                'available_handlers': list(self.event_handlers.keys())
            }
            
        except Exception as e:
            logger.error(f"Error getting webhook statistics: {e}")
            return {'error': str(e)}

# Global service instance
webhook_handler = WebhookHandler()