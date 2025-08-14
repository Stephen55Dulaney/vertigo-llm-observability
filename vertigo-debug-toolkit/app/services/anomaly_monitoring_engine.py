"""
Real-Time Anomaly Monitoring Engine for Vertigo Debug Toolkit
Provides continuous monitoring, real-time anomaly detection, and intelligent alerting.
"""

import os
import json
import logging
import threading
import time
import queue
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque
import statistics
import math

from app.models import db
from sqlalchemy import text, func
from app.services.live_data_service import live_data_service
from app.services.analytics_service import analytics_service, Anomaly
from app.services.alert_service import alert_service, AlertEvent, AlertSeverity

logger = logging.getLogger(__name__)

class MonitoringStatus(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    ERROR = "error"

class AnomalyType(Enum):
    STATISTICAL = "statistical"
    THRESHOLD = "threshold"
    PATTERN = "pattern"
    CORRELATION = "correlation"

@dataclass
class MetricPoint:
    """Single metric data point."""
    timestamp: datetime
    metric_name: str
    value: float
    source: str
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class AnomalyAlert:
    """Real-time anomaly alert."""
    id: str
    timestamp: datetime
    anomaly_type: AnomalyType
    metric_name: str
    severity: AlertSeverity
    actual_value: float
    expected_value: float
    deviation_score: float
    message: str
    context_data: Dict[str, Any]
    auto_response_triggered: bool = False
    response_actions: List[str] = field(default_factory=list)

@dataclass
class MonitoringConfig:
    """Configuration for monitoring engine."""
    poll_interval_seconds: int = 30
    anomaly_detection_window: int = 60  # minutes
    statistical_threshold: float = 2.5  # standard deviations
    correlation_threshold: float = 0.8
    max_alerts_per_minute: int = 10
    enable_auto_response: bool = True
    monitored_metrics: List[str] = field(default_factory=lambda: [
        'error_rate', 'avg_latency_ms', 'total_cost', 'total_traces', 'success_rate'
    ])

class AnomalyMonitoringEngine:
    """
    Real-time anomaly monitoring engine with advanced detection capabilities.
    
    Features:
    - Continuous metric monitoring with configurable intervals
    - Multi-method anomaly detection (statistical, threshold, pattern)
    - Real-time alert generation and prioritization
    - Integration with automated response system
    - Performance impact analysis and correlation
    - Alert deduplication and escalation
    """
    
    def __init__(self, config: Optional[MonitoringConfig] = None):
        """Initialize anomaly monitoring engine."""
        self.config = config or MonitoringConfig()
        self.status = MonitoringStatus.STOPPED
        self.monitoring_thread = None
        self.alert_queue = queue.Queue()
        self.metric_history = defaultdict(lambda: deque(maxlen=1000))
        self.alert_rate_limiter = deque(maxlen=100)
        
        # Detection methods
        self.detection_methods = {
            AnomalyType.STATISTICAL: self._detect_statistical_anomalies,
            AnomalyType.THRESHOLD: self._detect_threshold_anomalies,
            AnomalyType.PATTERN: self._detect_pattern_anomalies,
            AnomalyType.CORRELATION: self._detect_correlation_anomalies
        }
        
        # Performance metrics tracking
        self.detection_stats = {
            'total_checks': 0,
            'anomalies_detected': 0,
            'alerts_generated': 0,
            'false_positives': 0,
            'auto_responses_triggered': 0,
            'last_check_timestamp': None,
            'avg_detection_time_ms': 0
        }
        
        # Correlation tracking for multi-metric anomalies
        self.correlation_matrix = {}
        
        logger.info("Anomaly monitoring engine initialized")
    
    def start_monitoring(self) -> bool:
        """Start the real-time monitoring engine."""
        try:
            if self.status == MonitoringStatus.RUNNING:
                logger.warning("Monitoring engine is already running")
                return True
            
            self.status = MonitoringStatus.STARTING
            
            # Start monitoring thread
            self.monitoring_thread = threading.Thread(
                target=self._monitoring_loop,
                name="AnomalyMonitoringThread",
                daemon=True
            )
            self.monitoring_thread.start()
            
            self.status = MonitoringStatus.RUNNING
            logger.info(f"Anomaly monitoring engine started with {self.config.poll_interval_seconds}s intervals")
            return True
            
        except Exception as e:
            logger.error(f"Error starting monitoring engine: {e}")
            self.status = MonitoringStatus.ERROR
            return False
    
    def stop_monitoring(self) -> bool:
        """Stop the monitoring engine."""
        try:
            if self.status == MonitoringStatus.STOPPED:
                return True
            
            self.status = MonitoringStatus.STOPPED
            
            if self.monitoring_thread and self.monitoring_thread.is_alive():
                self.monitoring_thread.join(timeout=5)
            
            logger.info("Anomaly monitoring engine stopped")
            return True
            
        except Exception as e:
            logger.error(f"Error stopping monitoring engine: {e}")
            return False
    
    def get_status(self) -> Dict[str, Any]:
        """Get current monitoring status and statistics."""
        return {
            'status': self.status.value,
            'config': {
                'poll_interval_seconds': self.config.poll_interval_seconds,
                'monitored_metrics': self.config.monitored_metrics,
                'enable_auto_response': self.config.enable_auto_response
            },
            'statistics': self.detection_stats.copy(),
            'active_alerts': self.alert_queue.qsize(),
            'metric_history_size': {
                metric: len(history) for metric, history in self.metric_history.items()
            },
            'thread_alive': self.monitoring_thread.is_alive() if self.monitoring_thread else False
        }
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        logger.info("Starting anomaly monitoring loop")
        
        while self.status == MonitoringStatus.RUNNING:
            try:
                start_time = time.time()
                
                # Collect current metrics
                current_metrics = self._collect_metrics()
                
                # Update metric history
                for metric_name, value in current_metrics.items():
                    if value is not None and not math.isnan(value):
                        metric_point = MetricPoint(
                            timestamp=datetime.utcnow(),
                            metric_name=metric_name,
                            value=value,
                            source='live_data_service'
                        )
                        self.metric_history[metric_name].append(metric_point)
                
                # Run anomaly detection
                anomalies = self._run_anomaly_detection(current_metrics)
                
                # Process detected anomalies
                for anomaly in anomalies:
                    self._process_anomaly(anomaly)
                
                # Update statistics
                detection_time_ms = (time.time() - start_time) * 1000
                self._update_detection_stats(detection_time_ms, len(anomalies))
                
                # Sleep until next check
                time.sleep(self.config.poll_interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(min(self.config.poll_interval_seconds, 10))
    
    def _collect_metrics(self) -> Dict[str, float]:
        """Collect current performance metrics."""
        try:
            # Get unified metrics from live data service
            metrics = live_data_service.get_unified_performance_metrics(
                hours=self.config.poll_interval_seconds / 3600,  # Convert to hours
                data_source='all'
            )
            
            # Also get data source health metrics
            source_status = live_data_service.get_data_source_status()
            
            # Calculate data source health score
            if source_status.get('sources'):
                healthy_count = len([s for s in source_status['sources'].values() 
                                   if s.get('health') == 'healthy'])
                total_count = len(source_status['sources'])
                metrics['data_source_health_score'] = (healthy_count / total_count) * 100 if total_count > 0 else 0
            
            return {
                'error_rate': metrics.get('error_rate', 0),
                'avg_latency_ms': metrics.get('avg_latency_ms', 0),
                'total_cost': metrics.get('total_cost', 0),
                'total_traces': metrics.get('total_traces', 0),
                'success_rate': metrics.get('success_rate', 100),
                'data_source_health_score': metrics.get('data_source_health_score', 100)
            }
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
            return {}
    
    def _run_anomaly_detection(self, current_metrics: Dict[str, float]) -> List[AnomalyAlert]:
        """Run all anomaly detection methods on current metrics."""
        all_anomalies = []
        
        for detection_type, detection_method in self.detection_methods.items():
            try:
                anomalies = detection_method(current_metrics)
                all_anomalies.extend(anomalies)
            except Exception as e:
                logger.error(f"Error in {detection_type.value} detection: {e}")
        
        # Deduplicate and prioritize anomalies
        return self._deduplicate_anomalies(all_anomalies)
    
    def _detect_statistical_anomalies(self, current_metrics: Dict[str, float]) -> List[AnomalyAlert]:
        """Detect anomalies using statistical methods."""
        anomalies = []
        
        for metric_name in self.config.monitored_metrics:
            if metric_name not in current_metrics:
                continue
                
            current_value = current_metrics[metric_name]
            history = self.metric_history[metric_name]
            
            if len(history) < 10:  # Need sufficient history
                continue
            
            # Calculate statistical bounds
            values = [point.value for point in history if point.value is not None]
            if len(values) < 5:
                continue
                
            try:
                mean_value = statistics.mean(values)
                std_value = statistics.stdev(values) if len(values) > 1 else 0
                
                if std_value == 0:
                    continue
                
                deviation = abs(current_value - mean_value) / std_value
                
                if deviation > self.config.statistical_threshold:
                    severity = self._calculate_severity(deviation, metric_name)
                    
                    anomalies.append(AnomalyAlert(
                        id=f"stat_{metric_name}_{int(time.time())}",
                        timestamp=datetime.utcnow(),
                        anomaly_type=AnomalyType.STATISTICAL,
                        metric_name=metric_name,
                        severity=severity,
                        actual_value=current_value,
                        expected_value=mean_value,
                        deviation_score=deviation,
                        message=f"Statistical anomaly in {metric_name}: {current_value:.3f} (expected ~{mean_value:.3f}, σ={deviation:.2f})",
                        context_data={
                            'standard_deviation': std_value,
                            'sample_size': len(values),
                            'detection_method': 'statistical',
                            'threshold_used': self.config.statistical_threshold
                        }
                    ))
                    
            except statistics.StatisticsError as e:
                logger.debug(f"Statistical calculation error for {metric_name}: {e}")
        
        return anomalies
    
    def _detect_threshold_anomalies(self, current_metrics: Dict[str, float]) -> List[AnomalyAlert]:
        """Detect anomalies using predefined thresholds."""
        anomalies = []
        
        # Define critical thresholds for different metrics
        thresholds = {
            'error_rate': {'critical': 50, 'high': 25, 'medium': 10},
            'avg_latency_ms': {'critical': 10000, 'high': 5000, 'medium': 2000},
            'success_rate': {'critical': 50, 'high': 70, 'medium': 85},  # Below threshold
            'data_source_health_score': {'critical': 50, 'high': 70, 'medium': 85}  # Below threshold
        }
        
        for metric_name, current_value in current_metrics.items():
            if metric_name not in thresholds:
                continue
            
            metric_thresholds = thresholds[metric_name]
            triggered_severity = None
            threshold_value = None
            
            # Check thresholds (different logic for "below" metrics)
            if metric_name in ['success_rate', 'data_source_health_score']:
                # Lower values are worse
                if current_value <= metric_thresholds['critical']:
                    triggered_severity = AlertSeverity.CRITICAL
                    threshold_value = metric_thresholds['critical']
                elif current_value <= metric_thresholds['high']:
                    triggered_severity = AlertSeverity.HIGH
                    threshold_value = metric_thresholds['high']
                elif current_value <= metric_thresholds['medium']:
                    triggered_severity = AlertSeverity.MEDIUM
                    threshold_value = metric_thresholds['medium']
            else:
                # Higher values are worse
                if current_value >= metric_thresholds['critical']:
                    triggered_severity = AlertSeverity.CRITICAL
                    threshold_value = metric_thresholds['critical']
                elif current_value >= metric_thresholds['high']:
                    triggered_severity = AlertSeverity.HIGH
                    threshold_value = metric_thresholds['high']
                elif current_value >= metric_thresholds['medium']:
                    triggered_severity = AlertSeverity.MEDIUM
                    threshold_value = metric_thresholds['medium']
            
            if triggered_severity:
                operator = '<=' if metric_name in ['success_rate', 'data_source_health_score'] else '>='
                anomalies.append(AnomalyAlert(
                    id=f"thresh_{metric_name}_{int(time.time())}",
                    timestamp=datetime.utcnow(),
                    anomaly_type=AnomalyType.THRESHOLD,
                    metric_name=metric_name,
                    severity=triggered_severity,
                    actual_value=current_value,
                    expected_value=threshold_value,
                    deviation_score=abs(current_value - threshold_value) / threshold_value if threshold_value > 0 else 0,
                    message=f"Threshold breach in {metric_name}: {current_value:.3f} {operator} {threshold_value}",
                    context_data={
                        'threshold_type': triggered_severity.value,
                        'operator': operator,
                        'all_thresholds': metric_thresholds,
                        'detection_method': 'threshold'
                    }
                ))
        
        return anomalies
    
    def _detect_pattern_anomalies(self, current_metrics: Dict[str, float]) -> List[AnomalyAlert]:
        """Detect anomalies using pattern recognition."""
        anomalies = []
        
        # Look for rapid changes and unusual patterns
        for metric_name in self.config.monitored_metrics:
            if metric_name not in current_metrics:
                continue
            
            history = self.metric_history[metric_name]
            if len(history) < 5:
                continue
            
            recent_values = [point.value for point in list(history)[-5:]]
            current_value = current_metrics[metric_name]
            
            # Detect rapid increases
            if len(recent_values) >= 3:
                last_3_increasing = all(
                    recent_values[i] < recent_values[i+1] 
                    for i in range(len(recent_values)-2)
                )
                
                if last_3_increasing and len(recent_values) > 1:
                    change_rate = (current_value - recent_values[0]) / max(recent_values[0], 0.001)
                    
                    if change_rate > 2.0:  # 200% increase
                        anomalies.append(AnomalyAlert(
                            id=f"pattern_{metric_name}_{int(time.time())}",
                            timestamp=datetime.utcnow(),
                            anomaly_type=AnomalyType.PATTERN,
                            metric_name=metric_name,
                            severity=AlertSeverity.HIGH if change_rate > 5.0 else AlertSeverity.MEDIUM,
                            actual_value=current_value,
                            expected_value=recent_values[0],
                            deviation_score=change_rate,
                            message=f"Rapid increase pattern in {metric_name}: {change_rate:.1f}x growth over recent period",
                            context_data={
                                'pattern_type': 'rapid_increase',
                                'change_rate': change_rate,
                                'detection_window': len(recent_values),
                                'detection_method': 'pattern'
                            }
                        ))
        
        return anomalies
    
    def _detect_correlation_anomalies(self, current_metrics: Dict[str, float]) -> List[AnomalyAlert]:
        """Detect anomalies using metric correlations."""
        anomalies = []
        
        # Check for unusual correlations (e.g., high error rate with low latency)
        if 'error_rate' in current_metrics and 'avg_latency_ms' in current_metrics:
            error_rate = current_metrics['error_rate']
            latency = current_metrics['avg_latency_ms']
            
            # High error rate with surprisingly low latency might indicate timeouts
            if error_rate > 20 and latency < 1000:
                anomalies.append(AnomalyAlert(
                    id=f"corr_error_latency_{int(time.time())}",
                    timestamp=datetime.utcnow(),
                    anomaly_type=AnomalyType.CORRELATION,
                    metric_name="error_rate_latency_correlation",
                    severity=AlertSeverity.HIGH,
                    actual_value=error_rate,
                    expected_value=latency,
                    deviation_score=error_rate / max(latency / 1000, 1),
                    message=f"Unusual correlation: High error rate ({error_rate:.1f}%) with low latency ({latency:.0f}ms) suggests timeouts",
                    context_data={
                        'correlation_type': 'error_rate_latency_mismatch',
                        'error_rate': error_rate,
                        'latency_ms': latency,
                        'detection_method': 'correlation'
                    }
                ))
        
        # Check cost vs trace volume correlation
        if 'total_cost' in current_metrics and 'total_traces' in current_metrics:
            cost = current_metrics['total_cost']
            traces = current_metrics['total_traces']
            
            if traces > 0:
                cost_per_trace = cost / traces
                
                # Compare with historical cost per trace
                cost_history = [p.value for p in self.metric_history['total_cost'] if p.value > 0]
                trace_history = [p.value for p in self.metric_history['total_traces'] if p.value > 0]
                
                if len(cost_history) >= 5 and len(trace_history) >= 5:
                    historical_cpt = [c/t for c, t in zip(cost_history[-5:], trace_history[-5:]) if t > 0]
                    if historical_cpt:
                        avg_historical_cpt = statistics.mean(historical_cpt)
                        
                        if cost_per_trace > avg_historical_cpt * 3:  # 3x higher cost per trace
                            anomalies.append(AnomalyAlert(
                                id=f"corr_cost_efficiency_{int(time.time())}",
                                timestamp=datetime.utcnow(),
                                anomaly_type=AnomalyType.CORRELATION,
                                metric_name="cost_per_trace",
                                severity=AlertSeverity.MEDIUM,
                                actual_value=cost_per_trace,
                                expected_value=avg_historical_cpt,
                                deviation_score=cost_per_trace / avg_historical_cpt,
                                message=f"Cost efficiency anomaly: {cost_per_trace:.6f} per trace vs historical avg {avg_historical_cpt:.6f}",
                                context_data={
                                    'correlation_type': 'cost_efficiency_degradation',
                                    'current_cost_per_trace': cost_per_trace,
                                    'historical_avg_cost_per_trace': avg_historical_cpt,
                                    'total_cost': cost,
                                    'total_traces': traces,
                                    'detection_method': 'correlation'
                                }
                            ))
        
        return anomalies
    
    def _calculate_severity(self, deviation_score: float, metric_name: str) -> AlertSeverity:
        """Calculate alert severity based on deviation score and metric type."""
        # Adjust severity based on metric criticality
        critical_metrics = ['error_rate', 'success_rate', 'data_source_health_score']
        
        base_thresholds = {
            AlertSeverity.CRITICAL: 4.0,
            AlertSeverity.HIGH: 3.0,
            AlertSeverity.MEDIUM: 2.5,
            AlertSeverity.LOW: 2.0
        }
        
        # Lower thresholds for critical metrics
        if metric_name in critical_metrics:
            thresholds = {k: v * 0.8 for k, v in base_thresholds.items()}
        else:
            thresholds = base_thresholds
        
        if deviation_score >= thresholds[AlertSeverity.CRITICAL]:
            return AlertSeverity.CRITICAL
        elif deviation_score >= thresholds[AlertSeverity.HIGH]:
            return AlertSeverity.HIGH
        elif deviation_score >= thresholds[AlertSeverity.MEDIUM]:
            return AlertSeverity.MEDIUM
        else:
            return AlertSeverity.LOW
    
    def _deduplicate_anomalies(self, anomalies: List[AnomalyAlert]) -> List[AnomalyAlert]:
        """Remove duplicate anomalies and prioritize by severity."""
        if not anomalies:
            return []
        
        # Group by metric name
        anomaly_groups = defaultdict(list)
        for anomaly in anomalies:
            anomaly_groups[anomaly.metric_name].append(anomaly)
        
        # Keep highest severity for each metric
        deduplicated = []
        for metric_name, metric_anomalies in anomaly_groups.items():
            # Sort by severity (critical > high > medium > low)
            severity_order = {
                AlertSeverity.CRITICAL: 0,
                AlertSeverity.HIGH: 1,
                AlertSeverity.MEDIUM: 2,
                AlertSeverity.LOW: 3
            }
            
            metric_anomalies.sort(key=lambda a: (severity_order[a.severity], -a.deviation_score))
            deduplicated.append(metric_anomalies[0])  # Take the most severe
        
        return deduplicated
    
    def _process_anomaly(self, anomaly: AnomalyAlert):
        """Process a detected anomaly and trigger appropriate actions."""
        try:
            # Check rate limiting
            if not self._check_rate_limit():
                logger.warning(f"Rate limit exceeded, skipping anomaly: {anomaly.id}")
                return
            
            # Log the anomaly
            logger.info(f"Anomaly detected: {anomaly.message}")
            
            # Add to alert queue
            self.alert_queue.put(anomaly)
            
            # Create alert event for integration with existing alert system
            self._create_alert_event(anomaly)
            
            # Trigger automated response if enabled
            if self.config.enable_auto_response:
                self._trigger_automated_response(anomaly)
            
            # Update statistics
            self.detection_stats['alerts_generated'] += 1
            
        except Exception as e:
            logger.error(f"Error processing anomaly {anomaly.id}: {e}")
    
    def _check_rate_limit(self) -> bool:
        """Check if we're within the alert rate limit."""
        now = datetime.utcnow()
        
        # Remove alerts older than 1 minute
        cutoff = now - timedelta(minutes=1)
        while self.alert_rate_limiter and self.alert_rate_limiter[0] < cutoff:
            self.alert_rate_limiter.popleft()
        
        # Check if we're under the limit
        if len(self.alert_rate_limiter) >= self.config.max_alerts_per_minute:
            return False
        
        # Add current alert to rate limiter
        self.alert_rate_limiter.append(now)
        return True
    
    def _create_alert_event(self, anomaly: AnomalyAlert):
        """Create an alert event in the existing alert system."""
        try:
            # Import here to avoid circular imports
            from app.services.alert_service import AlertEvent, AlertStatus
            
            # Create a temporary alert rule for this anomaly
            alert_event = AlertEvent(
                id=None,
                rule_id=0,  # Special ID for anomaly-generated alerts
                triggered_at=anomaly.timestamp,
                status=AlertStatus.ACTIVE,
                trigger_value=anomaly.actual_value,
                threshold_value=anomaly.expected_value,
                message=anomaly.message,
                severity=anomaly.severity,
                context_data=anomaly.context_data
            )
            
            # Log the alert event
            alert_service._log_alert_event(alert_event)
            
        except Exception as e:
            logger.error(f"Error creating alert event for anomaly {anomaly.id}: {e}")
    
    def _trigger_automated_response(self, anomaly: AnomalyAlert):
        """Trigger automated response for the anomaly."""
        try:
            # Import here to avoid circular imports
            from app.services.automated_response_engine import automated_response_engine
            
            # Process the anomaly through the automated response engine
            executions = automated_response_engine.process_anomaly(anomaly)
            
            if executions:
                anomaly.auto_response_triggered = True
                anomaly.response_actions = [exec.action_id for exec in executions]
                
                logger.info(f"Triggered {len(executions)} automated responses for anomaly: {anomaly.id}")
                
                # Update statistics
                self.detection_stats['auto_responses_triggered'] += len(executions)
            else:
                logger.info(f"No automated responses available for anomaly: {anomaly.id}")
            
        except Exception as e:
            logger.error(f"Error triggering automated response for anomaly {anomaly.id}: {e}")
    
    def _update_detection_stats(self, detection_time_ms: float, anomalies_count: int):
        """Update detection statistics."""
        self.detection_stats['total_checks'] += 1
        self.detection_stats['anomalies_detected'] += anomalies_count
        self.detection_stats['last_check_timestamp'] = datetime.utcnow().isoformat()
        
        # Update average detection time (moving average)
        current_avg = self.detection_stats['avg_detection_time_ms']
        total_checks = self.detection_stats['total_checks']
        self.detection_stats['avg_detection_time_ms'] = (
            (current_avg * (total_checks - 1) + detection_time_ms) / total_checks
        )
    
    def get_recent_anomalies(self, limit: int = 50) -> List[AnomalyAlert]:
        """Get recent anomalies from the alert queue."""
        anomalies = []
        temp_queue = queue.Queue()
        
        try:
            # Extract anomalies from queue
            while not self.alert_queue.empty() and len(anomalies) < limit:
                anomaly = self.alert_queue.get_nowait()
                anomalies.append(anomaly)
                temp_queue.put(anomaly)  # Keep for re-queuing
        except queue.Empty:
            pass
        
        # Put anomalies back in queue
        while not temp_queue.empty():
            self.alert_queue.put(temp_queue.get_nowait())
        
        return sorted(anomalies, key=lambda a: a.timestamp, reverse=True)
    
    def clear_alerts(self, older_than_minutes: int = 60):
        """Clear old alerts from the queue."""
        cutoff = datetime.utcnow() - timedelta(minutes=older_than_minutes)
        new_queue = queue.Queue()
        
        try:
            while not self.alert_queue.empty():
                anomaly = self.alert_queue.get_nowait()
                if anomaly.timestamp > cutoff:
                    new_queue.put(anomaly)
        except queue.Empty:
            pass
        
        self.alert_queue = new_queue
        logger.info(f"Cleared alerts older than {older_than_minutes} minutes")

# Global monitoring engine instance
anomaly_monitoring_engine = AnomalyMonitoringEngine()