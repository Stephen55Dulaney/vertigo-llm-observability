"""
LangWatch Webhook Service for Real-time Data Integration
Handles secure webhook endpoints for receiving trace data from LangWatch.
"""

import os
import json
import hmac
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from flask import request, current_app
from app.models import db
from app.models import Trace
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

@dataclass
class WebhookEvent:
    """Represents a webhook event from LangWatch."""
    event_type: str
    trace_id: str
    timestamp: datetime
    data: Dict[str, Any]
    source: str = "langwatch"

class WebhookService:
    """
    Service for handling LangWatch webhooks securely.
    
    Features:
    - HMAC signature verification
    - Real-time trace data processing
    - Event deduplication
    - Error handling and retry logic
    """
    
    def __init__(self):
        """Initialize webhook service."""
        self.webhook_secret = os.getenv('LANGWATCH_WEBHOOK_SECRET')
        self.supported_events = {
            'trace.created',
            'trace.updated', 
            'trace.completed',
            'span.created',
            'span.updated'
        }
        
        # Event processing configuration
        self.max_event_age_minutes = 10
        self.deduplication_window_minutes = 5
        
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook HMAC signature for security."""
        if not self.webhook_secret:
            logger.warning("LANGWATCH_WEBHOOK_SECRET not configured")
            return False
            
        try:
            # Extract signature from header (format: sha256=signature)
            if signature.startswith('sha256='):
                signature = signature[7:]
            
            # Compute expected signature
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            # Secure comparison to prevent timing attacks
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False
    
    def is_event_duplicate(self, trace_id: str, event_type: str, timestamp: datetime) -> bool:
        """Check if event is a duplicate within deduplication window."""
        try:
            cutoff_time = timestamp - timedelta(minutes=self.deduplication_window_minutes)
            
            result = db.session.execute(
                text("""
                SELECT COUNT(*) FROM webhook_events 
                WHERE trace_id = :trace_id 
                AND event_type = :event_type 
                AND received_at >= :cutoff_time
                """),
                {
                    "trace_id": trace_id,
                    "event_type": event_type,
                    "cutoff_time": cutoff_time
                }
            ).fetchone()
            
            return result[0] > 0
            
        except Exception as e:
            logger.error(f"Error checking event duplication: {e}")
            return False
    
    def log_webhook_event(self, event: WebhookEvent, status: str, error_message: str = None):
        """Log webhook event for monitoring and debugging."""
        try:
            db.session.execute(
                text("""
                INSERT INTO webhook_events 
                (trace_id, event_type, event_data, source, received_at, processed_at, status, error_message)
                VALUES (:trace_id, :event_type, :event_data, :source, :received_at, :processed_at, :status, :error_message)
                """),
                {
                    "trace_id": event.trace_id,
                    "event_type": event.event_type,
                    "event_data": json.dumps(event.data),
                    "source": event.source,
                    "received_at": event.timestamp,
                    "processed_at": datetime.utcnow(),
                    "status": status,
                    "error_message": error_message
                }
            )
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error logging webhook event: {e}")
            db.session.rollback()
    
    def process_trace_event(self, event: WebhookEvent) -> bool:
        """Process a trace-related webhook event."""
        try:
            trace_data = event.data.get('trace', {})
            
            # Extract trace information
            trace_info = {
                'external_trace_id': event.trace_id,
                'name': trace_data.get('name', 'LangWatch Trace'),
                'status': self._map_langwatch_status(trace_data.get('status', 'unknown')),
                'model': trace_data.get('model'),
                'start_time': self._parse_timestamp(trace_data.get('startTime')),
                'end_time': self._parse_timestamp(trace_data.get('endTime')),
                'duration_ms': trace_data.get('duration'),
                'input_text': self._extract_text_content(trace_data.get('input')),
                'output_text': self._extract_text_content(trace_data.get('output')),
                'input_tokens': trace_data.get('inputTokens', 0),
                'output_tokens': trace_data.get('outputTokens', 0),
                'cost_usd': float(trace_data.get('cost', 0)),
                'user_id': trace_data.get('userId'),
                'session_id': trace_data.get('sessionId'),
                'tags': json.dumps(trace_data.get('tags', [])),
                'trace_metadata': json.dumps(trace_data.get('metadata', {})),
                'source_updated_at': datetime.utcnow()
            }
            
            # Get LangWatch data source ID
            ds_result = db.session.execute(
                text("SELECT id FROM data_sources WHERE name = 'langwatch' LIMIT 1")
            ).fetchone()
            
            if not ds_result:
                # Create LangWatch data source
                db.session.execute(
                    text("""
                    INSERT INTO data_sources 
                    (name, source_type, connection_config, is_active, sync_enabled, sync_interval_minutes, created_at, updated_at)
                    VALUES ('langwatch', 'webhook', '{}', 1, 1, 1, :now, :now)
                    """),
                    {"now": datetime.utcnow()}
                )
                db.session.commit()
                ds_result = db.session.execute(
                    text("SELECT id FROM data_sources WHERE name = 'langwatch' LIMIT 1")
                ).fetchone()
            
            trace_info['data_source_id'] = ds_result[0]
            
            # Check if trace already exists
            existing = db.session.execute(
                text("SELECT id FROM live_traces WHERE external_trace_id = :id"),
                {"id": event.trace_id}
            ).fetchone()
            
            if existing:
                # Update existing trace
                update_fields = []
                update_values = {"id": existing[0]}
                
                for key, value in trace_info.items():
                    if key != 'external_trace_id' and value is not None:
                        update_fields.append(f"{key} = :{key}")
                        update_values[key] = value
                
                if update_fields:
                    update_values['updated_at'] = datetime.utcnow()
                    update_fields.append("updated_at = :updated_at")
                    
                    sql = f"UPDATE live_traces SET {', '.join(update_fields)} WHERE id = :id"
                    db.session.execute(text(sql), update_values)
            else:
                # Insert new trace
                trace_info['created_at'] = datetime.utcnow()
                trace_info['updated_at'] = datetime.utcnow()
                
                columns = list(trace_info.keys())
                placeholders = [f":{col}" for col in columns]
                
                sql = f"""
                INSERT INTO live_traces ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                """
                db.session.execute(text(sql), trace_info)
            
            db.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"Error processing trace event: {e}")
            db.session.rollback()
            return False
    
    def _map_langwatch_status(self, langwatch_status: str) -> str:
        """Map LangWatch status to internal status."""
        status_mapping = {
            'pending': 'pending',
            'running': 'running', 
            'completed': 'success',
            'failed': 'error',
            'error': 'error'
        }
        return status_mapping.get(langwatch_status.lower(), 'unknown')
    
    def _parse_timestamp(self, timestamp_str: str) -> Optional[datetime]:
        """Parse timestamp from LangWatch format."""
        if not timestamp_str:
            return None
            
        try:
            # Handle ISO format with timezone
            if timestamp_str.endswith('Z'):
                timestamp_str = timestamp_str[:-1] + '+00:00'
            return datetime.fromisoformat(timestamp_str)
        except Exception as e:
            logger.warning(f"Error parsing timestamp {timestamp_str}: {e}")
            return None
    
    def _extract_text_content(self, content) -> str:
        """Extract text content from LangWatch message format."""
        if not content:
            return ""
        
        if isinstance(content, str):
            return content
        elif isinstance(content, dict):
            return content.get('text', content.get('content', str(content)))
        elif isinstance(content, list):
            return ' '.join(str(item) for item in content)
        else:
            return str(content)
    
    def process_webhook_payload(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process incoming webhook payload."""
        try:
            # Extract event information
            event_type = payload.get('type', 'unknown')
            event_id = payload.get('id', '')
            timestamp = datetime.utcnow()
            
            # Parse timestamp from payload if available
            if 'timestamp' in payload:
                timestamp = self._parse_timestamp(payload['timestamp']) or timestamp
            
            # Validate event age (ensure both timestamps are timezone-aware or naive)
            current_time = datetime.utcnow()
            if timestamp.tzinfo is not None:
                # If timestamp is timezone-aware, make current_time timezone-aware too
                import pytz
                current_time = current_time.replace(tzinfo=pytz.UTC)
            
            if (current_time - timestamp).total_seconds() > (self.max_event_age_minutes * 60):
                return {
                    'success': False,
                    'error': 'Event too old',
                    'event_type': event_type
                }
            
            # Check if event type is supported
            if event_type not in self.supported_events:
                logger.info(f"Unsupported event type: {event_type}")
                return {
                    'success': True,
                    'message': f'Event type {event_type} not processed',
                    'event_type': event_type
                }
            
            # Extract trace ID
            trace_id = payload.get('data', {}).get('trace', {}).get('id') or event_id
            if not trace_id:
                return {
                    'success': False,
                    'error': 'No trace ID found in payload',
                    'event_type': event_type
                }
            
            # Check for duplicates
            if self.is_event_duplicate(trace_id, event_type, timestamp):
                return {
                    'success': True,
                    'message': 'Event already processed (duplicate)',
                    'event_type': event_type,
                    'trace_id': trace_id
                }
            
            # Create webhook event
            event = WebhookEvent(
                event_type=event_type,
                trace_id=trace_id,
                timestamp=timestamp,
                data=payload.get('data', {}),
                source="langwatch"
            )
            
            # Process the event
            if event_type.startswith('trace.'):
                success = self.process_trace_event(event)
            else:
                # Handle other event types (spans, etc.)
                success = True
                logger.info(f"Event type {event_type} acknowledged but not processed")
            
            # Log the event
            status = 'success' if success else 'error'
            error_message = None if success else 'Processing failed'
            self.log_webhook_event(event, status, error_message)
            
            return {
                'success': success,
                'event_type': event_type,
                'trace_id': trace_id,
                'processed': success
            }
            
        except Exception as e:
            logger.error(f"Error processing webhook payload: {e}")
            return {
                'success': False,
                'error': str(e),
                'event_type': payload.get('type', 'unknown')
            }
    
    def get_webhook_statistics(self) -> Dict[str, Any]:
        """Get webhook processing statistics."""
        try:
            # Get event counts by type and status
            event_stats = db.session.execute(
                text("""
                SELECT event_type, status, COUNT(*) as count
                FROM webhook_events 
                WHERE received_at >= :since
                GROUP BY event_type, status
                ORDER BY event_type, status
                """),
                {"since": datetime.utcnow() - timedelta(hours=24)}
            ).fetchall()
            
            # Get recent events
            recent_events = db.session.execute(
                text("""
                SELECT trace_id, event_type, status, received_at, error_message
                FROM webhook_events 
                WHERE received_at >= :since
                ORDER BY received_at DESC 
                LIMIT 50
                """),
                {"since": datetime.utcnow() - timedelta(hours=1)}
            ).fetchall()
            
            return {
                'event_statistics': [
                    {
                        'event_type': row[0],
                        'status': row[1],
                        'count': row[2]
                    }
                    for row in event_stats
                ],
                'recent_events': [
                    {
                        'trace_id': row[0],
                        'event_type': row[1],
                        'status': row[2],
                        'received_at': row[3].isoformat() if row[3] else None,
                        'error_message': row[4]
                    }
                    for row in recent_events
                ],
                'webhook_secret_configured': bool(self.webhook_secret),
                'supported_events': list(self.supported_events)
            }
            
        except Exception as e:
            logger.error(f"Error getting webhook statistics: {e}")
            return {
                'error': str(e),
                'webhook_secret_configured': bool(self.webhook_secret)
            }

# Global service instance
webhook_service = WebhookService()