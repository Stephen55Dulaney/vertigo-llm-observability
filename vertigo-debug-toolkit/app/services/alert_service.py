"""
Real-time Alerting Service for Vertigo Debug Toolkit
Handles alert rule evaluation, notification dispatch, and alert management.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum

from flask import current_app
from app.models import db
from sqlalchemy import text, func
from app.services.live_data_service import live_data_service

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertStatus(Enum):
    ACTIVE = "active"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"
    SUPPRESSED = "suppressed"

@dataclass
class AlertRule:
    """Alert rule configuration."""
    id: Optional[int]
    name: str
    alert_type: str
    threshold_value: float
    comparison_operator: str
    time_window_minutes: int
    severity: AlertSeverity
    is_active: bool
    notification_channels: List[str]
    condition_metadata: Dict[str, Any]
    data_source_id: Optional[int] = None
    cooldown_minutes: int = 60

@dataclass
class AlertEvent:
    """Alert event instance."""
    id: Optional[int]
    rule_id: int
    triggered_at: datetime
    status: AlertStatus
    trigger_value: float
    threshold_value: float
    message: str
    severity: AlertSeverity
    context_data: Dict[str, Any]
    resolved_at: Optional[datetime] = None

class AlertService:
    """
    Service for managing alerts and notifications.
    
    Features:
    - Real-time alert rule evaluation
    - Multi-channel notification dispatch
    - Alert lifecycle management
    - Escalation and cooldown handling
    """
    
    def __init__(self):
        """Initialize alert service."""
        self.notification_channels = {
            'email': self._send_email_notification,
            'slack': self._send_slack_notification,
            'webhook': self._send_webhook_notification,
            'dashboard': self._send_dashboard_notification
        }
        
        # Alert type evaluators
        self.alert_evaluators = {
            'error_rate': self._evaluate_error_rate,
            'latency_spike': self._evaluate_latency_spike,
            'cost_threshold': self._evaluate_cost_threshold,
            'trace_volume': self._evaluate_trace_volume,
            'success_rate_drop': self._evaluate_success_rate_drop,
            'data_source_health': self._evaluate_data_source_health
        }
    
    def create_alert_rule(self, rule_config: Dict[str, Any]) -> AlertRule:
        """Create a new alert rule."""
        try:
            # Validate rule configuration
            self._validate_alert_rule_config(rule_config)
            
            # Insert into database
            current_time = datetime.utcnow()
            rule_data = {
                'name': rule_config['name'],
                'alert_type': rule_config['alert_type'],
                'threshold_value': float(rule_config['threshold_value']),
                'comparison_operator': rule_config.get('comparison_operator', '>'),
                'time_window_minutes': int(rule_config.get('time_window_minutes', 5)),
                'severity': rule_config.get('severity', 'medium'),
                'is_active': rule_config.get('is_active', True),
                'notification_channels': json.dumps(rule_config.get('notification_channels', ['dashboard'])),
                'condition_metadata': json.dumps(rule_config.get('condition_metadata', {})),
                'data_source_id': rule_config.get('data_source_id'),
                'cooldown_minutes': int(rule_config.get('cooldown_minutes', 60)),
                'created_at': current_time,
                'updated_at': current_time
            }
            
            result = db.session.execute(
                text("""
                INSERT INTO alert_rules 
                (name, alert_type, threshold_value, comparison_operator, time_window_minutes, 
                 severity, is_active, notification_channels, condition_metadata, 
                 data_source_id, cooldown_minutes, created_at, updated_at)
                VALUES (:name, :alert_type, :threshold_value, :comparison_operator, 
                        :time_window_minutes, :severity, :is_active, :notification_channels, 
                        :condition_metadata, :data_source_id, :cooldown_minutes, 
                        :created_at, :updated_at)
                """),
                rule_data
            )
            db.session.commit()
            
            # Get the created rule ID
            rule_id = result.lastrowid
            
            logger.info(f"Created alert rule '{rule_config['name']}' with ID {rule_id}")
            
            return AlertRule(
                id=rule_id,
                name=rule_data['name'],
                alert_type=rule_data['alert_type'],
                threshold_value=rule_data['threshold_value'],
                comparison_operator=rule_data['comparison_operator'],
                time_window_minutes=rule_data['time_window_minutes'],
                severity=AlertSeverity(rule_data['severity']),
                is_active=rule_data['is_active'],
                notification_channels=json.loads(rule_data['notification_channels']),
                condition_metadata=json.loads(rule_data['condition_metadata']),
                data_source_id=rule_data['data_source_id'],
                cooldown_minutes=rule_data['cooldown_minutes']
            )
            
        except Exception as e:
            logger.error(f"Error creating alert rule: {e}")
            db.session.rollback()
            raise
    
    def get_alert_rules(self, active_only: bool = True) -> List[AlertRule]:
        """Get all alert rules."""
        try:
            where_clause = "WHERE is_active = 1" if active_only else ""
            
            result = db.session.execute(
                text(f"""
                SELECT id, name, alert_type, threshold_value, comparison_operator, 
                       time_window_minutes, severity, is_active, notification_channels, 
                       condition_metadata, data_source_id, cooldown_minutes
                FROM alert_rules 
                {where_clause}
                ORDER BY severity DESC, name
                """)
            ).fetchall()
            
            rules = []
            for row in result:
                rules.append(AlertRule(
                    id=row[0],
                    name=row[1],
                    alert_type=row[2],
                    threshold_value=row[3],
                    comparison_operator=row[4],
                    time_window_minutes=row[5],
                    severity=AlertSeverity(row[6]),
                    is_active=bool(row[7]),
                    notification_channels=json.loads(row[8]) if row[8] else [],
                    condition_metadata=json.loads(row[9]) if row[9] else {},
                    data_source_id=row[10],
                    cooldown_minutes=row[11]
                ))
            
            return rules
            
        except Exception as e:
            logger.error(f"Error getting alert rules: {e}")
            return []
    
    def evaluate_alert_rules(self) -> List[AlertEvent]:
        """Evaluate all active alert rules against current data."""
        try:
            active_rules = self.get_alert_rules(active_only=True)
            triggered_alerts = []
            
            for rule in active_rules:
                try:
                    # Check if rule is in cooldown
                    if self._is_rule_in_cooldown(rule.id):
                        continue
                    
                    # Evaluate rule condition
                    alert_event = self._evaluate_alert_rule(rule)
                    if alert_event:
                        triggered_alerts.append(alert_event)
                        
                        # Send notifications
                        self._dispatch_notifications(alert_event, rule)
                        
                        # Log alert event
                        self._log_alert_event(alert_event)
                        
                except Exception as e:
                    logger.error(f"Error evaluating rule '{rule.name}': {e}")
            
            return triggered_alerts
            
        except Exception as e:
            logger.error(f"Error evaluating alert rules: {e}")
            return []
    
    def _evaluate_alert_rule(self, rule: AlertRule) -> Optional[AlertEvent]:
        """Evaluate a specific alert rule."""
        evaluator = self.alert_evaluators.get(rule.alert_type)
        if not evaluator:
            logger.warning(f"No evaluator for alert type: {rule.alert_type}")
            return None
        
        return evaluator(rule)
    
    def _evaluate_error_rate(self, rule: AlertRule) -> Optional[AlertEvent]:
        """Evaluate error rate alert rule."""
        try:
            # Get metrics for the specified time window
            data_source = 'all' if not rule.data_source_id else self._get_data_source_name(rule.data_source_id)
            metrics = live_data_service.get_unified_performance_metrics(
                hours=rule.time_window_minutes / 60, 
                data_source=data_source
            )
            
            current_error_rate = metrics.get('error_rate', 0)
            
            # Check if threshold is exceeded
            if self._compare_values(current_error_rate, rule.threshold_value, rule.comparison_operator):
                return AlertEvent(
                    id=None,
                    rule_id=rule.id,
                    triggered_at=datetime.utcnow(),
                    status=AlertStatus.ACTIVE,
                    trigger_value=current_error_rate,
                    threshold_value=rule.threshold_value,
                    message=f"Error rate {current_error_rate}% exceeds threshold {rule.threshold_value}%",
                    severity=rule.severity,
                    context_data={
                        'total_traces': metrics.get('total_traces', 0),
                        'error_count': metrics.get('error_count', 0),
                        'time_window_minutes': rule.time_window_minutes,
                        'data_source': data_source
                    }
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error evaluating error rate rule: {e}")
            return None
    
    def _evaluate_latency_spike(self, rule: AlertRule) -> Optional[AlertEvent]:
        """Evaluate latency spike alert rule."""
        try:
            data_source = 'all' if not rule.data_source_id else self._get_data_source_name(rule.data_source_id)
            metrics = live_data_service.get_unified_performance_metrics(
                hours=rule.time_window_minutes / 60,
                data_source=data_source
            )
            
            current_latency = metrics.get('avg_latency_ms', 0)
            
            if self._compare_values(current_latency, rule.threshold_value, rule.comparison_operator):
                return AlertEvent(
                    id=None,
                    rule_id=rule.id,
                    triggered_at=datetime.utcnow(),
                    status=AlertStatus.ACTIVE,
                    trigger_value=current_latency,
                    threshold_value=rule.threshold_value,
                    message=f"Average latency {current_latency}ms exceeds threshold {rule.threshold_value}ms",
                    severity=rule.severity,
                    context_data={
                        'total_traces': metrics.get('total_traces', 0),
                        'time_window_minutes': rule.time_window_minutes,
                        'data_source': data_source
                    }
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error evaluating latency spike rule: {e}")
            return None
    
    def _evaluate_cost_threshold(self, rule: AlertRule) -> Optional[AlertEvent]:
        """Evaluate cost threshold alert rule."""
        try:
            data_source = 'all' if not rule.data_source_id else self._get_data_source_name(rule.data_source_id)
            metrics = live_data_service.get_unified_performance_metrics(
                hours=rule.time_window_minutes / 60,
                data_source=data_source
            )
            
            current_cost = metrics.get('total_cost', 0)
            
            if self._compare_values(current_cost, rule.threshold_value, rule.comparison_operator):
                return AlertEvent(
                    id=None,
                    rule_id=rule.id,
                    triggered_at=datetime.utcnow(),
                    status=AlertStatus.ACTIVE,
                    trigger_value=current_cost,
                    threshold_value=rule.threshold_value,
                    message=f"Total cost ${current_cost:.4f} exceeds threshold ${rule.threshold_value:.4f}",
                    severity=rule.severity,
                    context_data={
                        'total_traces': metrics.get('total_traces', 0),
                        'time_window_minutes': rule.time_window_minutes,
                        'data_source': data_source
                    }
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error evaluating cost threshold rule: {e}")
            return None
    
    def _evaluate_trace_volume(self, rule: AlertRule) -> Optional[AlertEvent]:
        """Evaluate trace volume alert rule."""
        try:
            data_source = 'all' if not rule.data_source_id else self._get_data_source_name(rule.data_source_id)
            metrics = live_data_service.get_unified_performance_metrics(
                hours=rule.time_window_minutes / 60,
                data_source=data_source
            )
            
            current_traces = metrics.get('total_traces', 0)
            
            if self._compare_values(current_traces, rule.threshold_value, rule.comparison_operator):
                return AlertEvent(
                    id=None,
                    rule_id=rule.id,
                    triggered_at=datetime.utcnow(),
                    status=AlertStatus.ACTIVE,
                    trigger_value=current_traces,
                    threshold_value=rule.threshold_value,
                    message=f"Trace volume {current_traces} {rule.comparison_operator} threshold {rule.threshold_value}",
                    severity=rule.severity,
                    context_data={
                        'time_window_minutes': rule.time_window_minutes,
                        'data_source': data_source
                    }
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error evaluating trace volume rule: {e}")
            return None
    
    def _evaluate_success_rate_drop(self, rule: AlertRule) -> Optional[AlertEvent]:
        """Evaluate success rate drop alert rule."""
        try:
            data_source = 'all' if not rule.data_source_id else self._get_data_source_name(rule.data_source_id)
            metrics = live_data_service.get_unified_performance_metrics(
                hours=rule.time_window_minutes / 60,
                data_source=data_source
            )
            
            current_success_rate = metrics.get('success_rate', 0)
            
            if self._compare_values(current_success_rate, rule.threshold_value, rule.comparison_operator):
                return AlertEvent(
                    id=None,
                    rule_id=rule.id,
                    triggered_at=datetime.utcnow(),
                    status=AlertStatus.ACTIVE,
                    trigger_value=current_success_rate,
                    threshold_value=rule.threshold_value,
                    message=f"Success rate {current_success_rate}% dropped below threshold {rule.threshold_value}%",
                    severity=rule.severity,
                    context_data={
                        'total_traces': metrics.get('total_traces', 0),
                        'success_count': metrics.get('success_count', 0),
                        'time_window_minutes': rule.time_window_minutes,
                        'data_source': data_source
                    }
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error evaluating success rate drop rule: {e}")
            return None
    
    def _evaluate_data_source_health(self, rule: AlertRule) -> Optional[AlertEvent]:
        """Evaluate data source health alert rule."""
        try:
            status = live_data_service.get_data_source_status()
            
            unhealthy_sources = []
            for source_name, source_info in status['sources'].items():
                if source_info['health'] != 'healthy':
                    unhealthy_sources.append(f"{source_name}: {source_info['health']}")
            
            if unhealthy_sources:
                return AlertEvent(
                    id=None,
                    rule_id=rule.id,
                    triggered_at=datetime.utcnow(),
                    status=AlertStatus.ACTIVE,
                    trigger_value=len(unhealthy_sources),
                    threshold_value=rule.threshold_value,
                    message=f"Unhealthy data sources detected: {', '.join(unhealthy_sources)}",
                    severity=rule.severity,
                    context_data={
                        'unhealthy_sources': unhealthy_sources,
                        'total_sources': len(status['sources']),
                        'all_healthy': status['all_healthy']
                    }
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error evaluating data source health rule: {e}")
            return None
    
    def _compare_values(self, current: float, threshold: float, operator: str) -> bool:
        """Compare values using the specified operator."""
        operators = {
            '>': lambda a, b: a > b,
            '>=': lambda a, b: a >= b,
            '<': lambda a, b: a < b,
            '<=': lambda a, b: a <= b,
            '=': lambda a, b: abs(a - b) < 0.001,  # Float equality
            '!=': lambda a, b: abs(a - b) >= 0.001
        }
        
        return operators.get(operator, lambda a, b: False)(current, threshold)
    
    def _is_rule_in_cooldown(self, rule_id: int) -> bool:
        """Check if alert rule is in cooldown period."""
        try:
            result = db.session.execute(
                text("""
                SELECT last_triggered, cooldown_minutes
                FROM alert_rules
                WHERE id = :rule_id
                """),
                {"rule_id": rule_id}
            ).fetchone()
            
            if result and result[0]:
                last_triggered = datetime.fromisoformat(result[0]) if isinstance(result[0], str) else result[0]
                cooldown_minutes = result[1] or 60
                
                cooldown_until = last_triggered + timedelta(minutes=cooldown_minutes)
                return datetime.utcnow() < cooldown_until
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking rule cooldown: {e}")
            return False
    
    def _get_data_source_name(self, data_source_id: int) -> str:
        """Get data source name by ID."""
        try:
            result = db.session.execute(
                text("SELECT name FROM data_sources WHERE id = :id"),
                {"id": data_source_id}
            ).fetchone()
            
            return result[0] if result else 'all'
            
        except Exception as e:
            logger.error(f"Error getting data source name: {e}")
            return 'all'
    
    def _dispatch_notifications(self, alert_event: AlertEvent, rule: AlertRule):
        """Dispatch notifications for alert event."""
        for channel in rule.notification_channels:
            try:
                notification_func = self.notification_channels.get(channel)
                if notification_func:
                    notification_func(alert_event, rule)
                else:
                    logger.warning(f"Unknown notification channel: {channel}")
            except Exception as e:
                logger.error(f"Error sending {channel} notification: {e}")
    
    def _send_email_notification(self, alert_event: AlertEvent, rule: AlertRule):
        """Send email notification."""
        try:
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            # Get email configuration from environment
            alert_email = os.getenv('ALERT_EMAIL', 'sdulaney@mergeworld.com')
            smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            smtp_user = os.getenv('SMTP_USER', 'vertigo.agent.2025@gmail.com')
            smtp_password = os.getenv('SMTP_PASSWORD', '')
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = alert_email
            msg['Subject'] = f"🚨 Vertigo Alert: {rule.name} - {alert_event.severity.value.upper()}"
            
            # Create HTML email body
            html_body = f"""
            <html>
            <body>
                <h2>🚨 Vertigo System Alert</h2>
                <table border="1" cellpadding="5" cellspacing="0">
                    <tr><td><strong>Alert Rule:</strong></td><td>{rule.name}</td></tr>
                    <tr><td><strong>Severity:</strong></td><td>{alert_event.severity.value.upper()}</td></tr>
                    <tr><td><strong>Status:</strong></td><td>{alert_event.status.value}</td></tr>
                    <tr><td><strong>Time:</strong></td><td>{alert_event.timestamp.strftime('%Y-%m-%d %H:%M:%S')} UTC</td></tr>
                    <tr><td><strong>Message:</strong></td><td>{alert_event.message}</td></tr>
                    <tr><td><strong>Metric Value:</strong></td><td>{alert_event.metric_value}</td></tr>
                    <tr><td><strong>Threshold:</strong></td><td>{rule.threshold_value} ({rule.comparison_operator})</td></tr>
                </table>
                
                <h3>📊 Additional Details</h3>
                <p><strong>Data Source:</strong> {rule.data_source_id or 'System'}</p>
                <p><strong>Time Window:</strong> {rule.time_window_minutes} minutes</p>
                
                <hr>
                <p><em>This alert was generated by Vertigo Debug Toolkit monitoring system.</em></p>
                <p><strong>Action Required:</strong> Please check the Vertigo dashboard and investigate the issue.</p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(html_body, 'html'))
            
            # Send email if SMTP is configured
            if smtp_password:
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(smtp_user, smtp_password)
                    server.send_message(msg)
                logger.info(f"✅ Email alert sent to {alert_email} for: {alert_event.message}")
            else:
                logger.warning(f"⚠️ SMTP not configured. Would send email to {alert_email}: {alert_event.message}")
                
        except Exception as e:
            logger.error(f"❌ Failed to send email notification: {e}")
    
    def _send_slack_notification(self, alert_event: AlertEvent, rule: AlertRule):
        """Send Slack notification."""
        # Placeholder for Slack notification
        logger.info(f"Slack notification for alert: {alert_event.message}")
    
    def _send_webhook_notification(self, alert_event: AlertEvent, rule: AlertRule):
        """Send webhook notification."""
        # Placeholder for webhook notification
        logger.info(f"Webhook notification for alert: {alert_event.message}")
    
    def _send_dashboard_notification(self, alert_event: AlertEvent, rule: AlertRule):
        """Send dashboard notification."""
        # Placeholder for dashboard/WebSocket notification
        logger.info(f"Dashboard notification for alert: {alert_event.message}")
    
    def _log_alert_event(self, alert_event: AlertEvent):
        """Log alert event to database."""
        try:
            db.session.execute(
                text("""
                INSERT INTO alert_events 
                (rule_id, triggered_at, status, trigger_value, threshold_value, 
                 message, severity, context_data, created_at)
                VALUES (:rule_id, :triggered_at, :status, :trigger_value, :threshold_value,
                        :message, :severity, :context_data, :created_at)
                """),
                {
                    'rule_id': alert_event.rule_id,
                    'triggered_at': alert_event.triggered_at,
                    'status': alert_event.status.value,
                    'trigger_value': alert_event.trigger_value,
                    'threshold_value': alert_event.threshold_value,
                    'message': alert_event.message,
                    'severity': alert_event.severity.value,
                    'context_data': json.dumps(alert_event.context_data),
                    'created_at': datetime.utcnow()
                }
            )
            
            # Update rule last triggered time
            db.session.execute(
                text("UPDATE alert_rules SET last_triggered = :now WHERE id = :rule_id"),
                {"now": alert_event.triggered_at, "rule_id": alert_event.rule_id}
            )
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error logging alert event: {e}")
            db.session.rollback()
    
    def _validate_alert_rule_config(self, config: Dict[str, Any]):
        """Validate alert rule configuration."""
        required_fields = ['name', 'alert_type', 'threshold_value']
        for field in required_fields:
            if field not in config:
                raise ValueError(f"Missing required field: {field}")
        
        if config['alert_type'] not in self.alert_evaluators:
            raise ValueError(f"Unsupported alert type: {config['alert_type']}")
        
        if config.get('comparison_operator', '>') not in ['>', '>=', '<', '<=', '=', '!=']:
            raise ValueError(f"Invalid comparison operator: {config.get('comparison_operator')}")

# Global service instance
alert_service = AlertService()