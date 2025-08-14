"""
Security Monitoring Service

Comprehensive security monitoring system for failed authentication tracking,
suspicious activity detection, and security event management.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from flask import request, g, current_app
from collections import defaultdict, deque
import logging
import threading
import time

from app.models import db

# Import security models with fallback for development
try:
    from app.models.security_models import (
        SecurityEvent, LoginAttempt, SessionSecurity, 
        RateLimitViolation, APIKeyUsage
    )
    SECURITY_MODELS_AVAILABLE = True
except ImportError:
    # Create mock classes for development
    class SecurityEvent:
        pass
    class LoginAttempt:
        pass
    class SessionSecurity:
        pass
    class RateLimitViolation:
        pass
    class APIKeyUsage:
        pass
    SECURITY_MODELS_AVAILABLE = False

logger = logging.getLogger(__name__)


class ThreatLevel:
    """Security threat levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SecurityEventType:
    """Security event types."""
    # Authentication Events
    LOGIN_FAILED = "login_failed"
    LOGIN_SUCCESS = "login_success"
    LOGIN_BRUTE_FORCE = "login_brute_force"
    ACCOUNT_LOCKED = "account_locked"
    PASSWORD_CHANGED = "password_changed"
    
    # API Key Events
    API_KEY_INVALID = "api_key_invalid"
    API_KEY_EXPIRED = "api_key_expired"
    API_KEY_ABUSE = "api_key_abuse"
    
    # Session Events
    SESSION_HIJACK_ATTEMPT = "session_hijack_attempt"
    CONCURRENT_SESSIONS = "concurrent_sessions"
    SESSION_EXPIRED = "session_expired"
    
    # Rate Limiting Events
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    RATE_LIMIT_ABUSE = "rate_limit_abuse"
    
    # Input Validation Events
    MALICIOUS_INPUT = "malicious_input"
    FILE_UPLOAD_REJECTED = "file_upload_rejected"
    SQL_INJECTION_ATTEMPT = "sql_injection_attempt"
    XSS_ATTEMPT = "xss_attempt"
    
    # Network Events
    SUSPICIOUS_IP = "suspicious_ip"
    GEO_ANOMALY = "geo_anomaly"
    TOR_ACCESS = "tor_access"
    
    # Application Events
    UNAUTHORIZED_ACCESS = "unauthorized_access"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DATA_EXFILTRATION = "data_exfiltration"


class SecurityMonitor:
    """Main security monitoring service."""
    
    def __init__(self):
        self.monitoring_enabled = True
        
        # In-memory tracking for real-time analysis
        self.failed_logins = defaultdict(list)
        self.ip_activity = defaultdict(list)
        self.user_sessions = defaultdict(list)
        self.suspicious_ips = set()
        
        # Detection thresholds
        self.thresholds = {
            'failed_login_attempts': 5,
            'failed_login_window': 300,  # 5 minutes
            'brute_force_threshold': 10,
            'brute_force_window': 600,   # 10 minutes
            'max_concurrent_sessions': 5,
            'suspicious_ip_threshold': 20,
            'rate_limit_violations': 3,
        }
        
        # Event queue for batch processing
        self.event_queue = deque(maxlen=10000)
        self.queue_lock = threading.Lock()
        
        # Background processor
        self.processor_thread = None
        self.stop_processing = threading.Event()
        
        self.start_background_processor()
    
    def start_background_processor(self):
        """Start background event processor."""
        if not self.processor_thread or not self.processor_thread.is_alive():
            self.processor_thread = threading.Thread(target=self._process_events_background)
            self.processor_thread.daemon = True
            self.processor_thread.start()
            logger.info("Security monitor background processor started")
    
    def stop_background_processor(self):
        """Stop background event processor."""
        self.stop_processing.set()
        if self.processor_thread:
            self.processor_thread.join(timeout=5)
    
    def record_login_attempt(self, username: str, success: bool, failure_reason: str = None):
        """Record login attempt and detect anomalies."""
        if not self.monitoring_enabled:
            return
        
        ip_address = request.remote_addr
        user_agent = request.headers.get('User-Agent', '')
        timestamp = datetime.utcnow()
        
        # Store in database (if security models are available)
        if SECURITY_MODELS_AVAILABLE:
            try:
                login_attempt = LoginAttempt(
                    timestamp=timestamp,
                    username=username,
                    success=success,
                    failure_reason=failure_reason,
                    ip_address=ip_address,
                    user_agent=user_agent
                )
                db.session.add(login_attempt)
                db.session.commit()
            except Exception as e:
                logger.error(f"Error recording login attempt: {e}")
                db.session.rollback()
        else:
            logger.debug(f"Login attempt recorded in memory: {username} - {'success' if success else 'failed'}")
        
        # Real-time analysis
        if not success:
            self._analyze_failed_login(username, ip_address, timestamp)
        
        # Queue event for further analysis
        self._queue_event({
            'type': SecurityEventType.LOGIN_SUCCESS if success else SecurityEventType.LOGIN_FAILED,
            'username': username,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'timestamp': timestamp,
            'failure_reason': failure_reason
        })
    
    def record_security_event(self, event_type: str, description: str, 
                            severity: str = ThreatLevel.MEDIUM,
                            event_data: Dict[str, Any] = None,
                            user_id: int = None,
                            api_key_id: int = None):
        """Record security event."""
        if not self.monitoring_enabled:
            return
        
        try:
            if SECURITY_MODELS_AVAILABLE:
                security_event = SecurityEvent(
                    event_type=event_type,
                    severity=severity,
                    category=self._get_event_category(event_type),
                    timestamp=datetime.utcnow(),
                    description=description,
                    event_data=event_data or {},
                    ip_address=getattr(request, 'remote_addr', None),
                    user_agent=request.headers.get('User-Agent', '') if hasattr(request, 'headers') else None,
                    endpoint=getattr(request, 'endpoint', None),
                    method=getattr(request, 'method', None),
                    user_id=user_id,
                    api_key_id=api_key_id,
                    is_automated=True
                )
                db.session.add(security_event)
                db.session.commit()
            else:
                logger.debug(f"Security event logged in memory: {event_type}")
                security_event = None
            
            # Log critical events immediately
            if severity == ThreatLevel.CRITICAL:
                logger.critical(f"CRITICAL SECURITY EVENT: {event_type} - {description}")
                if security_event:
                    self._handle_critical_event(security_event)
            
        except Exception as e:
            logger.error(f"Error recording security event: {e}")
            if SECURITY_MODELS_AVAILABLE:
                db.session.rollback()
    
    def record_rate_limit_violation(self, identifier: str, identifier_type: str,
                                  limit_type: str, limit_value: int, current_count: int,
                                  user_id: int = None, api_key_id: int = None):
        """Record rate limit violation."""
        if not self.monitoring_enabled:
            return
        
        try:
            if SECURITY_MODELS_AVAILABLE:
                violation = RateLimitViolation(
                    identifier=identifier,
                    identifier_type=identifier_type,
                    limit_type=limit_type,
                    limit_value=limit_value,
                    current_count=current_count,
                    endpoint=getattr(request, 'endpoint', None),
                    method=getattr(request, 'method', None),
                    ip_address=getattr(request, 'remote_addr', None),
                    user_agent=request.headers.get('User-Agent', '') if hasattr(request, 'headers') else None,
                    user_id=user_id,
                    api_key_id=api_key_id,
                    blocked=True,
                    retry_after_seconds=60
                )
                db.session.add(violation)
                db.session.commit()
            else:
                logger.debug(f"Rate limit violation logged in memory: {identifier}")
            
            # Analyze for abuse patterns
            self._analyze_rate_limit_violations(identifier, identifier_type)
            
        except Exception as e:
            logger.error(f"Error recording rate limit violation: {e}")
            db.session.rollback()
    
    def record_api_key_usage(self, api_key_id: int, endpoint: str, method: str,
                           status_code: int, response_time_ms: int,
                           rate_limit_hit: bool = False, rate_limit_remaining: int = None):
        """Record API key usage."""
        if not self.monitoring_enabled:
            return
        
        try:
            usage = APIKeyUsage(
                api_key_id=api_key_id,
                timestamp=datetime.utcnow(),
                ip_address=getattr(request, 'remote_addr', None),
                user_agent=request.headers.get('User-Agent', '') if hasattr(request, 'headers') else None,
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                response_time_ms=response_time_ms,
                rate_limit_hit=rate_limit_hit,
                rate_limit_remaining=rate_limit_remaining
            )
            
            db.session.add(usage)
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error recording API key usage: {e}")
            db.session.rollback()
    
    def analyze_ip_reputation(self, ip_address: str) -> Dict[str, Any]:
        """Analyze IP address reputation and behavior."""
        now = datetime.utcnow()
        analysis = {
            'ip_address': ip_address,
            'threat_level': ThreatLevel.LOW,
            'is_suspicious': False,
            'is_blocked': False,
            'reasons': [],
            'recent_activity': {}
        }
        
        try:
            # Check recent failed logins
            recent_failures = LoginAttempt.query.filter_by(
                ip_address=ip_address,
                success=False
            ).filter(
                LoginAttempt.timestamp >= now - timedelta(hours=1)
            ).count()
            
            if recent_failures >= 10:
                analysis['threat_level'] = ThreatLevel.HIGH
                analysis['is_suspicious'] = True
                analysis['reasons'].append(f"High failed login count: {recent_failures}")
            
            # Check rate limit violations
            recent_violations = RateLimitViolation.query.filter_by(
                ip_address=ip_address
            ).filter(
                RateLimitViolation.timestamp >= now - timedelta(hours=1)
            ).count()
            
            if recent_violations >= 5:
                analysis['threat_level'] = ThreatLevel.HIGH
                analysis['is_suspicious'] = True
                analysis['reasons'].append(f"Multiple rate limit violations: {recent_violations}")
            
            # Check security events
            security_events = SecurityEvent.query.filter_by(
                ip_address=ip_address
            ).filter(
                SecurityEvent.timestamp >= now - timedelta(hours=24)
            ).count()
            
            if security_events >= 3:
                analysis['threat_level'] = ThreatLevel.MEDIUM
                analysis['is_suspicious'] = True
                analysis['reasons'].append(f"Multiple security events: {security_events}")
            
            # Get activity summary
            analysis['recent_activity'] = {
                'failed_logins': recent_failures,
                'rate_violations': recent_violations,
                'security_events': security_events
            }
            
        except Exception as e:
            logger.error(f"Error analyzing IP reputation for {ip_address}: {e}")
            analysis['error'] = str(e)
        
        return analysis
    
    def get_security_dashboard_data(self) -> Dict[str, Any]:
        """Get security dashboard data."""
        now = datetime.utcnow()
        
        try:
            # Recent security events
            recent_events = SecurityEvent.query.filter(
                SecurityEvent.timestamp >= now - timedelta(hours=24)
            ).order_by(SecurityEvent.timestamp.desc()).limit(10).all()
            
            # Failed login statistics
            failed_logins_24h = LoginAttempt.query.filter(
                LoginAttempt.success == False,
                LoginAttempt.timestamp >= now - timedelta(hours=24)
            ).count()
            
            # Rate limit violations
            rate_violations_24h = RateLimitViolation.query.filter(
                RateLimitViolation.timestamp >= now - timedelta(hours=24)
            ).count()
            
            # Top suspicious IPs
            suspicious_ips = db.session.query(
                SecurityEvent.ip_address,
                db.func.count().label('event_count')
            ).filter(
                SecurityEvent.timestamp >= now - timedelta(hours=24),
                SecurityEvent.severity.in_([ThreatLevel.HIGH, ThreatLevel.CRITICAL])
            ).group_by(SecurityEvent.ip_address).order_by(
                db.func.count().desc()
            ).limit(5).all()
            
            # Active sessions
            active_sessions = SessionSecurity.query.filter_by(
                is_active=True
            ).count()
            
            return {
                'overview': {
                    'failed_logins_24h': failed_logins_24h,
                    'rate_violations_24h': rate_violations_24h,
                    'active_sessions': active_sessions,
                    'suspicious_ips_count': len(suspicious_ips)
                },
                'recent_events': [
                    {
                        'id': event.id,
                        'type': event.event_type,
                        'severity': event.severity,
                        'timestamp': event.timestamp.isoformat(),
                        'description': event.description,
                        'ip_address': event.ip_address
                    }
                    for event in recent_events
                ],
                'suspicious_ips': [
                    {
                        'ip_address': ip,
                        'event_count': count
                    }
                    for ip, count in suspicious_ips
                ],
                'threat_levels': {
                    'critical': SecurityEvent.query.filter(
                        SecurityEvent.severity == ThreatLevel.CRITICAL,
                        SecurityEvent.timestamp >= now - timedelta(hours=24)
                    ).count(),
                    'high': SecurityEvent.query.filter(
                        SecurityEvent.severity == ThreatLevel.HIGH,
                        SecurityEvent.timestamp >= now - timedelta(hours=24)
                    ).count(),
                    'medium': SecurityEvent.query.filter(
                        SecurityEvent.severity == ThreatLevel.MEDIUM,
                        SecurityEvent.timestamp >= now - timedelta(hours=24)
                    ).count(),
                    'low': SecurityEvent.query.filter(
                        SecurityEvent.severity == ThreatLevel.LOW,
                        SecurityEvent.timestamp >= now - timedelta(hours=24)
                    ).count()
                }
            }
        
        except Exception as e:
            logger.error(f"Error getting security dashboard data: {e}")
            return {'error': str(e)}
    
    def _analyze_failed_login(self, username: str, ip_address: str, timestamp: datetime):
        """Analyze failed login for anomaly detection."""
        # Track failed logins by IP
        self.ip_activity[ip_address].append(timestamp)
        
        # Clean old entries
        cutoff = timestamp - timedelta(seconds=self.thresholds['failed_login_window'])
        self.ip_activity[ip_address] = [
            ts for ts in self.ip_activity[ip_address] if ts > cutoff
        ]
        
        # Check for brute force
        if len(self.ip_activity[ip_address]) >= self.thresholds['brute_force_threshold']:
            self.record_security_event(
                SecurityEventType.LOGIN_BRUTE_FORCE,
                f"Brute force attack detected from {ip_address}",
                severity=ThreatLevel.HIGH,
                event_data={
                    'ip_address': ip_address,
                    'attempt_count': len(self.ip_activity[ip_address]),
                    'username': username
                }
            )
            
            # Mark IP as suspicious
            self.suspicious_ips.add(ip_address)
    
    def _analyze_rate_limit_violations(self, identifier: str, identifier_type: str):
        """Analyze rate limit violations for abuse patterns."""
        now = datetime.utcnow()
        
        # Check recent violations for this identifier
        recent_violations = RateLimitViolation.query.filter_by(
            identifier=identifier,
            identifier_type=identifier_type
        ).filter(
            RateLimitViolation.timestamp >= now - timedelta(minutes=10)
        ).count()
        
        if recent_violations >= self.thresholds['rate_limit_violations']:
            self.record_security_event(
                SecurityEventType.RATE_LIMIT_ABUSE,
                f"Rate limit abuse detected for {identifier_type}: {identifier}",
                severity=ThreatLevel.HIGH,
                event_data={
                    'identifier': identifier,
                    'identifier_type': identifier_type,
                    'violation_count': recent_violations
                }
            )
    
    def _queue_event(self, event_data: Dict[str, Any]):
        """Queue event for background processing."""
        with self.queue_lock:
            self.event_queue.append(event_data)
    
    def _process_events_background(self):
        """Background event processing."""
        while not self.stop_processing.is_set():
            try:
                events_to_process = []
                
                # Get events from queue
                with self.queue_lock:
                    while self.event_queue and len(events_to_process) < 100:
                        events_to_process.append(self.event_queue.popleft())
                
                # Process events
                if events_to_process:
                    self._analyze_event_patterns(events_to_process)
                
                # Sleep before next iteration
                time.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in background event processor: {e}")
                time.sleep(10)
    
    def _analyze_event_patterns(self, events: List[Dict[str, Any]]):
        """Analyze patterns in security events."""
        # Group events by IP
        ip_events = defaultdict(list)
        for event in events:
            if event.get('ip_address'):
                ip_events[event['ip_address']].append(event)
        
        # Analyze each IP's events
        for ip_address, ip_event_list in ip_events.items():
            if len(ip_event_list) >= 5:  # Many events from same IP
                event_types = [event.get('type') for event in ip_event_list]
                if SecurityEventType.LOGIN_FAILED in event_types:
                    self.record_security_event(
                        SecurityEventType.SUSPICIOUS_IP,
                        f"Suspicious activity pattern from IP {ip_address}",
                        severity=ThreatLevel.MEDIUM,
                        event_data={
                            'ip_address': ip_address,
                            'event_count': len(ip_event_list),
                            'event_types': list(set(event_types))
                        }
                    )
    
    def _get_event_category(self, event_type: str) -> str:
        """Get category for event type."""
        categories = {
            SecurityEventType.LOGIN_FAILED: 'authentication',
            SecurityEventType.LOGIN_SUCCESS: 'authentication',
            SecurityEventType.LOGIN_BRUTE_FORCE: 'authentication',
            SecurityEventType.ACCOUNT_LOCKED: 'authentication',
            SecurityEventType.PASSWORD_CHANGED: 'authentication',
            SecurityEventType.API_KEY_INVALID: 'authorization',
            SecurityEventType.API_KEY_EXPIRED: 'authorization',
            SecurityEventType.API_KEY_ABUSE: 'authorization',
            SecurityEventType.SESSION_HIJACK_ATTEMPT: 'session_management',
            SecurityEventType.CONCURRENT_SESSIONS: 'session_management',
            SecurityEventType.SESSION_EXPIRED: 'session_management',
            SecurityEventType.RATE_LIMIT_EXCEEDED: 'rate_limiting',
            SecurityEventType.RATE_LIMIT_ABUSE: 'rate_limiting',
            SecurityEventType.MALICIOUS_INPUT: 'input_validation',
            SecurityEventType.FILE_UPLOAD_REJECTED: 'input_validation',
            SecurityEventType.SQL_INJECTION_ATTEMPT: 'input_validation',
            SecurityEventType.XSS_ATTEMPT: 'input_validation',
            SecurityEventType.SUSPICIOUS_IP: 'network_security',
            SecurityEventType.GEO_ANOMALY: 'network_security',
            SecurityEventType.TOR_ACCESS: 'network_security',
            SecurityEventType.UNAUTHORIZED_ACCESS: 'access_control',
            SecurityEventType.PRIVILEGE_ESCALATION: 'access_control',
            SecurityEventType.DATA_EXFILTRATION: 'data_protection'
        }
        
        return categories.get(event_type, 'general')
    
    def _handle_critical_event(self, event: SecurityEvent):
        """Handle critical security events immediately."""
        # In production, this would trigger immediate alerts
        # For now, just log and could integrate with alerting systems
        
        logger.critical(f"CRITICAL SECURITY EVENT: {event.event_type}")
        logger.critical(f"Description: {event.description}")
        logger.critical(f"IP: {event.ip_address}")
        logger.critical(f"Timestamp: {event.timestamp}")
        
        # Could integrate with:
        # - Email alerts
        # - Slack notifications
        # - PagerDuty
        # - SIEM systems
    
    def cleanup_old_data(self, days_to_keep: int = 30):
        """Clean up old security monitoring data."""
        cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
        
        try:
            # Clean up old login attempts
            LoginAttempt.query.filter(LoginAttempt.timestamp < cutoff_date).delete()
            
            # Clean up old security events (keep critical events longer)
            SecurityEvent.query.filter(
                SecurityEvent.timestamp < cutoff_date,
                SecurityEvent.severity != ThreatLevel.CRITICAL
            ).delete()
            
            # Clean up old rate limit violations
            RateLimitViolation.query.filter(
                RateLimitViolation.timestamp < cutoff_date
            ).delete()
            
            # Clean up old API key usage
            APIKeyUsage.query.filter(
                APIKeyUsage.timestamp < cutoff_date
            ).delete()
            
            db.session.commit()
            logger.info(f"Cleaned up security data older than {days_to_keep} days")
            
        except Exception as e:
            logger.error(f"Error cleaning up old security data: {e}")
            db.session.rollback()


# Global security monitor instance
security_monitor = SecurityMonitor()