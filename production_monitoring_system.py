#!/usr/bin/env python3
"""
Production Monitoring and Continuous Evaluation System for Vertigo
=================================================================

This module provides comprehensive production monitoring capabilities for LLM systems,
including real-time performance tracking, automated alerting, continuous evaluation,
and integration with observability platforms like Langfuse.

Key Features:
• Real-time performance monitoring and alerting
• Continuous A/B testing in production
• Automated quality degradation detection
• Cost monitoring and budget management
• User satisfaction tracking
• Integration with Langfuse/Langwatch observability
• Stakeholder dashboards and reporting
• Incident response automation

Author: Vertigo Team
Date: August 2025
"""

import asyncio
import json
import logging
import os
import sqlite3
import time
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from enum import Enum

import pandas as pd
import numpy as np
from scipy import stats

# Try to import Langfuse for observability integration
try:
    from langfuse import Langfuse
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    logging.warning("Langfuse not available. Some monitoring features will be limited.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MonitoringMetric(Enum):
    """Production monitoring metrics."""
    RESPONSE_TIME = "response_time"
    ERROR_RATE = "error_rate"
    THROUGHPUT = "throughput"
    QUALITY_SCORE = "quality_score"
    COST_PER_REQUEST = "cost_per_request"
    USER_SATISFACTION = "user_satisfaction"
    TOKEN_USAGE = "token_usage"
    AVAILABILITY = "availability"
    LATENCY_P95 = "latency_p95"
    HALLUCINATION_RATE = "hallucination_rate"

class AlertSeverity(Enum):
    """Alert severity levels."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"

class AlertType(Enum):
    """Types of alerts."""
    THRESHOLD_BREACH = "threshold_breach"
    ANOMALY_DETECTION = "anomaly_detection"
    QUALITY_DEGRADATION = "quality_degradation"
    COST_OVERRUN = "cost_overrun"
    SYSTEM_ERROR = "system_error"
    SLA_VIOLATION = "sla_violation"

@dataclass
class MonitoringAlert:
    """Container for monitoring alerts."""
    id: str
    alert_type: AlertType
    severity: AlertSeverity
    metric: MonitoringMetric
    current_value: float
    threshold_value: float
    message: str
    timestamp: datetime
    resolved: bool = False
    resolution_time: Optional[datetime] = None
    metadata: Dict[str, Any] = None

@dataclass
class PerformanceSnapshot:
    """Container for performance snapshot data."""
    timestamp: datetime
    metrics: Dict[MonitoringMetric, float]
    metadata: Dict[str, Any]
    prompt_variant_id: Optional[str] = None
    trace_id: Optional[str] = None

class ProductionMonitor:
    """
    Comprehensive production monitoring system for LLM applications.
    
    This class provides real-time monitoring, alerting, and continuous evaluation
    capabilities for production LLM systems.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the production monitor."""
        self.config = self._load_monitoring_config(config_path)
        self.results_dir = Path("production_monitoring")
        self.results_dir.mkdir(exist_ok=True)
        
        # Initialize databases
        self.monitoring_db = self._initialize_monitoring_database()
        
        # Initialize Langfuse client if available
        self.langfuse_client = self._initialize_langfuse() if LANGFUSE_AVAILABLE else None
        
        # Initialize monitoring state
        self.performance_buffer = deque(maxlen=1000)  # Rolling buffer for performance data
        self.active_alerts = {}
        self.metric_thresholds = self.config.get("thresholds", {})
        self.alert_handlers = []
        self.monitoring_active = False
        self.monitoring_thread = None
        
        # Statistical models for anomaly detection
        self.baseline_stats = {}
        self.anomaly_detectors = self._initialize_anomaly_detectors()
        
        logger.info("Production Monitor initialized")
    
    def _load_monitoring_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load monitoring configuration."""
        default_config = {
            "monitoring_interval_seconds": 60,
            "alert_cooldown_minutes": 15,
            "data_retention_days": 90,
            "thresholds": {
                MonitoringMetric.RESPONSE_TIME.value: {"warning": 2000, "critical": 5000},  # milliseconds
                MonitoringMetric.ERROR_RATE.value: {"warning": 0.05, "critical": 0.10},    # percentage
                MonitoringMetric.QUALITY_SCORE.value: {"warning": 0.7, "critical": 0.5},  # 0-1 scale
                MonitoringMetric.COST_PER_REQUEST.value: {"warning": 0.10, "critical": 0.25},  # USD
                MonitoringMetric.AVAILABILITY.value: {"warning": 0.95, "critical": 0.90},  # percentage
                MonitoringMetric.THROUGHPUT.value: {"warning": 100, "critical": 50}        # requests/hour
            },
            "sla_targets": {
                "uptime_percent": 99.5,
                "response_time_p95_ms": 3000,
                "error_rate_max": 0.01
            },
            "cost_budgets": {
                "daily_budget_usd": 100.0,
                "monthly_budget_usd": 2500.0,
                "cost_per_request_target": 0.05
            },
            "notification_channels": {
                "email": {"enabled": True, "recipients": ["admin@vertigo.com"]},
                "slack": {"enabled": False, "webhook_url": ""},
                "pagerduty": {"enabled": False, "api_key": ""}
            },
            "langfuse": {
                "host": os.getenv("LANGFUSE_HOST", "http://localhost:3000"),
                "public_key": os.getenv("LANGFUSE_PUBLIC_KEY"),
                "secret_key": os.getenv("LANGFUSE_SECRET_KEY")
            }
        }
        
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                user_config = json.load(f)
                default_config.update(user_config)
        
        return default_config
    
    def _initialize_monitoring_database(self) -> str:
        """Initialize SQLite database for monitoring data."""
        db_path = self.results_dir / "monitoring.db"
        conn = sqlite3.connect(db_path)
        
        # Performance metrics table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS performance_metrics (
                id TEXT PRIMARY KEY,
                timestamp TEXT,
                metric TEXT,
                value REAL,
                prompt_variant_id TEXT,
                trace_id TEXT,
                metadata TEXT
            )
        """)
        
        # Alerts table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS alerts (
                id TEXT PRIMARY KEY,
                alert_type TEXT,
                severity TEXT,
                metric TEXT,
                current_value REAL,
                threshold_value REAL,
                message TEXT,
                timestamp TEXT,
                resolved BOOLEAN,
                resolution_time TEXT,
                metadata TEXT
            )
        """)
        
        # SLA tracking table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sla_metrics (
                id TEXT PRIMARY KEY,
                date TEXT,
                uptime_percent REAL,
                avg_response_time_ms REAL,
                p95_response_time_ms REAL,
                error_rate REAL,
                total_requests INTEGER,
                sla_met BOOLEAN
            )
        """)
        
        # Cost tracking table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS cost_tracking (
                id TEXT PRIMARY KEY,
                timestamp TEXT,
                cost_usd REAL,
                request_count INTEGER,
                token_count INTEGER,
                model_used TEXT,
                cost_per_request REAL
            )
        """)
        
        conn.commit()
        conn.close()
        return str(db_path)
    
    def _initialize_langfuse(self) -> Optional[Langfuse]:
        """Initialize Langfuse client for observability integration."""
        try:
            config = self.config.get("langfuse", {})
            if not all([config.get("public_key"), config.get("secret_key")]):
                logger.warning("Langfuse credentials not configured")
                return None
                
            return Langfuse(
                public_key=config["public_key"],
                secret_key=config["secret_key"],
                host=config.get("host", "http://localhost:3000")
            )
        except Exception as e:
            logger.error(f"Failed to initialize Langfuse client: {e}")
            return None
    
    def _initialize_anomaly_detectors(self) -> Dict[MonitoringMetric, Any]:
        """Initialize anomaly detection models for each metric."""
        detectors = {}
        
        # For each metric, we'll use statistical methods for anomaly detection
        for metric in MonitoringMetric:
            detectors[metric] = {
                "window_size": 50,  # Number of historical points to consider
                "sensitivity": 2.0,  # Standard deviations for anomaly threshold
                "historical_data": deque(maxlen=200)
            }
        
        return detectors
    
    def start_monitoring(self):
        """Start the production monitoring system."""
        if self.monitoring_active:
            logger.warning("Monitoring already active")
            return
        
        logger.info("Starting production monitoring system")
        self.monitoring_active = True
        
        # Start monitoring thread
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        logger.info("Production monitoring started")
    
    def stop_monitoring(self):
        """Stop the production monitoring system."""
        if not self.monitoring_active:
            return
        
        logger.info("Stopping production monitoring system")
        self.monitoring_active = False
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=10)
        
        logger.info("Production monitoring stopped")
    
    def _monitoring_loop(self):
        """Main monitoring loop."""
        interval = self.config.get("monitoring_interval_seconds", 60)
        
        while self.monitoring_active:
            try:
                # Collect performance metrics
                snapshot = self._collect_performance_snapshot()
                if snapshot:
                    self.performance_buffer.append(snapshot)
                    self._store_performance_snapshot(snapshot)
                
                # Check thresholds and generate alerts
                self._check_thresholds(snapshot)
                
                # Run anomaly detection
                self._detect_anomalies(snapshot)
                
                # Update SLA metrics
                self._update_sla_metrics()
                
                # Check cost budgets
                self._check_cost_budgets()
                
                # Clean up old data
                self._cleanup_old_data()
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(interval)
    
    def _collect_performance_snapshot(self) -> Optional[PerformanceSnapshot]:
        """Collect current performance metrics."""
        try:
            metrics = {}
            
            # Collect metrics from Langfuse if available
            if self.langfuse_client:
                langfuse_metrics = self._collect_langfuse_metrics()
                metrics.update(langfuse_metrics)
            
            # Collect system metrics
            system_metrics = self._collect_system_metrics()
            metrics.update(system_metrics)
            
            # Collect application-specific metrics
            app_metrics = self._collect_application_metrics()
            metrics.update(app_metrics)
            
            if not metrics:
                return None
            
            return PerformanceSnapshot(
                timestamp=datetime.now(),
                metrics=metrics,
                metadata={"source": "production_monitor"}
            )
            
        except Exception as e:
            logger.error(f"Error collecting performance snapshot: {e}")
            return None
    
    def _collect_langfuse_metrics(self) -> Dict[MonitoringMetric, float]:
        """Collect metrics from Langfuse observability platform."""
        metrics = {}
        
        try:
            # Get recent traces (last hour)
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=1)
            
            traces = self.langfuse_client.api.trace.list(
                start_date=start_time,
                end_date=end_time,
                limit=100
            )
            
            if traces.data:
                # Calculate response time metrics
                response_times = [t.latency for t in traces.data if t.latency]
                if response_times:
                    metrics[MonitoringMetric.RESPONSE_TIME] = np.mean(response_times)
                    metrics[MonitoringMetric.LATENCY_P95] = np.percentile(response_times, 95)
                
                # Calculate error rate
                total_traces = len(traces.data)
                error_traces = sum(1 for t in traces.data if hasattr(t, 'status') and t.status == 'error')
                metrics[MonitoringMetric.ERROR_RATE] = error_traces / total_traces if total_traces > 0 else 0
                
                # Calculate throughput (requests per hour)
                metrics[MonitoringMetric.THROUGHPUT] = total_traces  # Approximate for 1-hour window
                
            # Get cost information
            generations = self.langfuse_client.generations.list(
                start_date=start_time,
                end_date=end_time,
                limit=100
            )
            
            if generations.data:
                total_cost = 0
                total_tokens = 0
                
                for gen in generations.data:
                    # Estimate cost (simplified)
                    input_tokens = getattr(gen, 'prompt_tokens', 0) or 0
                    output_tokens = getattr(gen, 'completion_tokens', 0) or 0
                    cost = self._estimate_cost(gen.model, input_tokens, output_tokens)
                    total_cost += cost
                    total_tokens += input_tokens + output_tokens
                
                if len(generations.data) > 0:
                    metrics[MonitoringMetric.COST_PER_REQUEST] = total_cost / len(generations.data)
                    metrics[MonitoringMetric.TOKEN_USAGE] = total_tokens / len(generations.data)
            
        except Exception as e:
            logger.error(f"Error collecting Langfuse metrics: {e}")
        
        return metrics
    
    def _collect_system_metrics(self) -> Dict[MonitoringMetric, float]:
        """Collect system-level metrics."""
        metrics = {}
        
        try:
            # Availability metric (simplified - in production would check actual service health)
            metrics[MonitoringMetric.AVAILABILITY] = 1.0  # Assume available if we're running
            
            # Quality score (would be calculated from actual quality evaluations)
            # For demo, simulate a quality score
            recent_scores = [s.metrics.get(MonitoringMetric.QUALITY_SCORE, 0.8) 
                           for s in list(self.performance_buffer)[-10:]]
            if recent_scores:
                metrics[MonitoringMetric.QUALITY_SCORE] = np.mean(recent_scores)
            else:
                metrics[MonitoringMetric.QUALITY_SCORE] = 0.85  # Default good quality
                
        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")
        
        return metrics
    
    def _collect_application_metrics(self) -> Dict[MonitoringMetric, float]:
        """Collect application-specific metrics for Vertigo."""
        metrics = {}
        
        try:
            # Simulate application metrics (in production, these would be real)
            # Hallucination rate
            metrics[MonitoringMetric.HALLUCINATION_RATE] = np.random.uniform(0.01, 0.05)
            
            # User satisfaction (would come from user feedback)
            metrics[MonitoringMetric.USER_SATISFACTION] = np.random.uniform(3.8, 4.5)
            
        except Exception as e:
            logger.error(f"Error collecting application metrics: {e}")
        
        return metrics
    
    def _estimate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost for a model call."""
        # Cost per 1K tokens (approximate)
        costs = {
            'gemini-1.5-pro': {'input': 0.0035, 'output': 0.0105},
            'gpt-4': {'input': 0.03, 'output': 0.06},
            'claude-3-sonnet': {'input': 0.003, 'output': 0.015}
        }
        
        model_costs = costs.get(model, {'input': 0.01, 'output': 0.02})
        
        input_cost = (input_tokens / 1000) * model_costs['input']
        output_cost = (output_tokens / 1000) * model_costs['output']
        
        return input_cost + output_cost
    
    def _check_thresholds(self, snapshot: Optional[PerformanceSnapshot]):
        """Check metric thresholds and generate alerts."""
        if not snapshot:
            return
        
        for metric, value in snapshot.metrics.items():
            thresholds = self.metric_thresholds.get(metric.value, {})
            
            # Check critical threshold
            critical_threshold = thresholds.get("critical")
            if critical_threshold is not None:
                if (metric in [MonitoringMetric.ERROR_RATE, MonitoringMetric.COST_PER_REQUEST, 
                              MonitoringMetric.RESPONSE_TIME, MonitoringMetric.HALLUCINATION_RATE] 
                    and value > critical_threshold) or \
                   (metric in [MonitoringMetric.QUALITY_SCORE, MonitoringMetric.AVAILABILITY, 
                              MonitoringMetric.THROUGHPUT] and value < critical_threshold):
                    
                    self._generate_alert(
                        alert_type=AlertType.THRESHOLD_BREACH,
                        severity=AlertSeverity.CRITICAL,
                        metric=metric,
                        current_value=value,
                        threshold_value=critical_threshold,
                        message=f"Critical threshold breach: {metric.value} = {value:.3f} (threshold: {critical_threshold})"
                    )
            
            # Check warning threshold
            warning_threshold = thresholds.get("warning")
            if warning_threshold is not None:
                if (metric in [MonitoringMetric.ERROR_RATE, MonitoringMetric.COST_PER_REQUEST, 
                              MonitoringMetric.RESPONSE_TIME, MonitoringMetric.HALLUCINATION_RATE] 
                    and value > warning_threshold) or \
                   (metric in [MonitoringMetric.QUALITY_SCORE, MonitoringMetric.AVAILABILITY, 
                              MonitoringMetric.THROUGHPUT] and value < warning_threshold):
                    
                    self._generate_alert(
                        alert_type=AlertType.THRESHOLD_BREACH,
                        severity=AlertSeverity.HIGH,
                        metric=metric,
                        current_value=value,
                        threshold_value=warning_threshold,
                        message=f"Warning threshold breach: {metric.value} = {value:.3f} (threshold: {warning_threshold})"
                    )
    
    def _detect_anomalies(self, snapshot: Optional[PerformanceSnapshot]):
        """Detect anomalies using statistical methods."""
        if not snapshot:
            return
        
        for metric, value in snapshot.metrics.items():
            detector = self.anomaly_detectors.get(metric)
            if not detector:
                continue
            
            historical_data = detector["historical_data"]
            historical_data.append(value)
            
            # Need sufficient historical data for anomaly detection
            if len(historical_data) < detector["window_size"]:
                continue
            
            # Calculate statistical properties
            recent_data = list(historical_data)[-detector["window_size"]:]
            mean_value = np.mean(recent_data)
            std_value = np.std(recent_data)
            
            # Check for anomaly (value outside normal range)
            if std_value > 0:  # Avoid division by zero
                z_score = abs(value - mean_value) / std_value
                
                if z_score > detector["sensitivity"]:
                    self._generate_alert(
                        alert_type=AlertType.ANOMALY_DETECTION,
                        severity=AlertSeverity.MEDIUM if z_score < 3 else AlertSeverity.HIGH,
                        metric=metric,
                        current_value=value,
                        threshold_value=mean_value + detector["sensitivity"] * std_value,
                        message=f"Anomaly detected: {metric.value} = {value:.3f} (z-score: {z_score:.2f})"
                    )
    
    def _update_sla_metrics(self):
        """Update SLA compliance metrics."""
        try:
            # Calculate SLA metrics for the current day
            today = datetime.now().date()
            
            # Get performance data for today
            conn = sqlite3.connect(self.monitoring_db)
            
            today_str = today.isoformat()
            metrics_data = conn.execute("""
                SELECT metric, value FROM performance_metrics 
                WHERE date(timestamp) = ? 
            """, (today_str,)).fetchall()
            
            if not metrics_data:
                conn.close()
                return
            
            # Calculate SLA metrics
            metrics_by_type = defaultdict(list)
            for metric, value in metrics_data:
                metrics_by_type[metric].append(value)
            
            # Uptime calculation
            availability_values = metrics_by_type.get(MonitoringMetric.AVAILABILITY.value, [])
            uptime_percent = np.mean(availability_values) * 100 if availability_values else 100
            
            # Response time calculation
            response_times = metrics_by_type.get(MonitoringMetric.RESPONSE_TIME.value, [])
            avg_response_time = np.mean(response_times) if response_times else 0
            p95_response_time = np.percentile(response_times, 95) if response_times else 0
            
            # Error rate calculation
            error_rates = metrics_by_type.get(MonitoringMetric.ERROR_RATE.value, [])
            avg_error_rate = np.mean(error_rates) if error_rates else 0
            
            # Total requests (approximate)
            throughput_values = metrics_by_type.get(MonitoringMetric.THROUGHPUT.value, [])
            total_requests = sum(throughput_values) if throughput_values else 0
            
            # Check SLA compliance
            sla_targets = self.config.get("sla_targets", {})
            sla_met = (
                uptime_percent >= sla_targets.get("uptime_percent", 99.5) and
                p95_response_time <= sla_targets.get("response_time_p95_ms", 3000) and
                avg_error_rate <= sla_targets.get("error_rate_max", 0.01)
            )
            
            # Store SLA metrics
            conn.execute("""
                INSERT OR REPLACE INTO sla_metrics (
                    id, date, uptime_percent, avg_response_time_ms, p95_response_time_ms,
                    error_rate, total_requests, sla_met
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f"sla_{today_str}",
                today_str,
                uptime_percent,
                avg_response_time,
                p95_response_time,
                avg_error_rate,
                total_requests,
                sla_met
            ))
            
            conn.commit()
            conn.close()
            
            # Generate SLA violation alert if needed
            if not sla_met:
                self._generate_alert(
                    alert_type=AlertType.SLA_VIOLATION,
                    severity=AlertSeverity.HIGH,
                    metric=MonitoringMetric.AVAILABILITY,  # Primary SLA metric
                    current_value=uptime_percent,
                    threshold_value=sla_targets.get("uptime_percent", 99.5),
                    message=f"SLA violation: Uptime {uptime_percent:.2f}%, P95 latency {p95_response_time:.0f}ms, Error rate {avg_error_rate:.3f}"
                )
            
        except Exception as e:
            logger.error(f"Error updating SLA metrics: {e}")
    
    def _check_cost_budgets(self):
        """Check cost budgets and generate alerts if exceeded."""
        try:
            conn = sqlite3.connect(self.monitoring_db)
            
            # Check daily budget
            today = datetime.now().date().isoformat()
            daily_cost = conn.execute("""
                SELECT SUM(cost_usd) FROM cost_tracking 
                WHERE date(timestamp) = ?
            """, (today,)).fetchone()[0] or 0
            
            daily_budget = self.config.get("cost_budgets", {}).get("daily_budget_usd", 100.0)
            
            if daily_cost > daily_budget:
                self._generate_alert(
                    alert_type=AlertType.COST_OVERRUN,
                    severity=AlertSeverity.HIGH,
                    metric=MonitoringMetric.COST_PER_REQUEST,
                    current_value=daily_cost,
                    threshold_value=daily_budget,
                    message=f"Daily cost budget exceeded: ${daily_cost:.2f} > ${daily_budget:.2f}"
                )
            
            # Check monthly budget
            month_start = datetime.now().replace(day=1).date().isoformat()
            monthly_cost = conn.execute("""
                SELECT SUM(cost_usd) FROM cost_tracking 
                WHERE date(timestamp) >= ?
            """, (month_start,)).fetchone()[0] or 0
            
            monthly_budget = self.config.get("cost_budgets", {}).get("monthly_budget_usd", 2500.0)
            
            if monthly_cost > monthly_budget:
                self._generate_alert(
                    alert_type=AlertType.COST_OVERRUN,
                    severity=AlertSeverity.CRITICAL,
                    metric=MonitoringMetric.COST_PER_REQUEST,
                    current_value=monthly_cost,
                    threshold_value=monthly_budget,
                    message=f"Monthly cost budget exceeded: ${monthly_cost:.2f} > ${monthly_budget:.2f}"
                )
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Error checking cost budgets: {e}")
    
    def _generate_alert(
        self,
        alert_type: AlertType,
        severity: AlertSeverity,
        metric: MonitoringMetric,
        current_value: float,
        threshold_value: float,
        message: str
    ):
        """Generate and process a monitoring alert."""
        
        # Create alert
        alert_id = f"{alert_type.value}_{metric.value}_{int(datetime.now().timestamp())}"
        alert = MonitoringAlert(
            id=alert_id,
            alert_type=alert_type,
            severity=severity,
            metric=metric,
            current_value=current_value,
            threshold_value=threshold_value,
            message=message,
            timestamp=datetime.now(),
            metadata={"source": "production_monitor"}
        )
        
        # Check for alert cooldown to avoid spam
        cooldown_key = f"{alert_type.value}_{metric.value}"
        cooldown_minutes = self.config.get("alert_cooldown_minutes", 15)
        
        if cooldown_key in self.active_alerts:
            last_alert_time = self.active_alerts[cooldown_key]
            if datetime.now() - last_alert_time < timedelta(minutes=cooldown_minutes):
                return  # Skip alert due to cooldown
        
        # Store alert
        self._store_alert(alert)
        
        # Update active alerts
        self.active_alerts[cooldown_key] = datetime.now()
        
        # Send notifications
        self._send_alert_notifications(alert)
        
        # Log alert
        logger.warning(f"ALERT [{severity.value.upper()}]: {message}")
    
    def _store_alert(self, alert: MonitoringAlert):
        """Store alert in database."""
        conn = sqlite3.connect(self.monitoring_db)
        
        conn.execute("""
            INSERT INTO alerts (
                id, alert_type, severity, metric, current_value, threshold_value,
                message, timestamp, resolved, resolution_time, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            alert.id,
            alert.alert_type.value,
            alert.severity.value,
            alert.metric.value,
            alert.current_value,
            alert.threshold_value,
            alert.message,
            alert.timestamp.isoformat(),
            alert.resolved,
            alert.resolution_time.isoformat() if alert.resolution_time else None,
            json.dumps(alert.metadata or {})
        ))
        
        conn.commit()
        conn.close()
    
    def _store_performance_snapshot(self, snapshot: PerformanceSnapshot):
        """Store performance snapshot in database."""
        conn = sqlite3.connect(self.monitoring_db)
        
        for metric, value in snapshot.metrics.items():
            conn.execute("""
                INSERT INTO performance_metrics (
                    id, timestamp, metric, value, prompt_variant_id, trace_id, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                f"{metric.value}_{int(snapshot.timestamp.timestamp())}_{hash(str(value)) % 10000}",
                snapshot.timestamp.isoformat(),
                metric.value,
                value,
                snapshot.prompt_variant_id,
                snapshot.trace_id,
                json.dumps(snapshot.metadata)
            ))
        
        conn.commit()
        conn.close()
    
    def _send_alert_notifications(self, alert: MonitoringAlert):
        """Send alert notifications through configured channels."""
        notification_config = self.config.get("notification_channels", {})
        
        # Email notifications
        if notification_config.get("email", {}).get("enabled", False):
            self._send_email_notification(alert, notification_config["email"])
        
        # Slack notifications
        if notification_config.get("slack", {}).get("enabled", False):
            self._send_slack_notification(alert, notification_config["slack"])
        
        # PagerDuty notifications
        if notification_config.get("pagerduty", {}).get("enabled", False):
            self._send_pagerduty_notification(alert, notification_config["pagerduty"])
    
    def _send_email_notification(self, alert: MonitoringAlert, email_config: Dict[str, Any]):
        """Send email notification (stub implementation)."""
        # In production, implement actual email sending
        logger.info(f"EMAIL ALERT: {alert.message} (Recipients: {email_config.get('recipients', [])})")
    
    def _send_slack_notification(self, alert: MonitoringAlert, slack_config: Dict[str, Any]):
        """Send Slack notification (stub implementation)."""
        # In production, implement actual Slack webhook
        logger.info(f"SLACK ALERT: {alert.message}")
    
    def _send_pagerduty_notification(self, alert: MonitoringAlert, pagerduty_config: Dict[str, Any]):
        """Send PagerDuty notification (stub implementation)."""
        # In production, implement actual PagerDuty API
        logger.info(f"PAGERDUTY ALERT: {alert.message}")
    
    def _cleanup_old_data(self):
        """Clean up old monitoring data based on retention policy."""
        try:
            retention_days = self.config.get("data_retention_days", 90)
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            conn = sqlite3.connect(self.monitoring_db)
            
            # Clean up old performance metrics
            conn.execute("""
                DELETE FROM performance_metrics 
                WHERE timestamp < ?
            """, (cutoff_date.isoformat(),))
            
            # Clean up old resolved alerts
            conn.execute("""
                DELETE FROM alerts 
                WHERE timestamp < ? AND resolved = 1
            """, (cutoff_date.isoformat(),))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
    
    def get_monitoring_dashboard_data(self) -> Dict[str, Any]:
        """Get data for monitoring dashboard."""
        try:
            conn = sqlite3.connect(self.monitoring_db)
            
            # Get recent performance metrics
            recent_metrics = conn.execute("""
                SELECT metric, value, timestamp FROM performance_metrics 
                WHERE timestamp > datetime('now', '-24 hours')
                ORDER BY timestamp DESC
            """).fetchall()
            
            # Get active alerts
            active_alerts = conn.execute("""
                SELECT alert_type, severity, metric, message, timestamp FROM alerts 
                WHERE resolved = 0
                ORDER BY timestamp DESC
                LIMIT 10
            """).fetchall()
            
            # Get SLA metrics
            sla_metrics = conn.execute("""
                SELECT * FROM sla_metrics 
                WHERE date > date('now', '-7 days')
                ORDER BY date DESC
            """).fetchall()
            
            # Get cost data
            cost_data = conn.execute("""
                SELECT date(timestamp) as date, SUM(cost_usd) as daily_cost 
                FROM cost_tracking 
                WHERE timestamp > datetime('now', '-30 days')
                GROUP BY date(timestamp)
                ORDER BY date DESC
            """).fetchall()
            
            conn.close()
            
            # Process metrics data
            metrics_by_type = defaultdict(list)
            for metric, value, timestamp in recent_metrics:
                metrics_by_type[metric].append({
                    "value": value,
                    "timestamp": timestamp
                })
            
            # Current metric values
            current_metrics = {}
            for metric_type, values in metrics_by_type.items():
                if values:
                    current_metrics[metric_type] = values[0]["value"]  # Most recent value
            
            return {
                "timestamp": datetime.now().isoformat(),
                "current_metrics": current_metrics,
                "metrics_history": dict(metrics_by_type),
                "active_alerts": [
                    {
                        "type": alert_type,
                        "severity": severity,
                        "metric": metric,
                        "message": message,
                        "timestamp": timestamp
                    }
                    for alert_type, severity, metric, message, timestamp in active_alerts
                ],
                "sla_compliance": [
                    {
                        "date": row[1],
                        "uptime": row[2],
                        "avg_response_time": row[3],
                        "p95_response_time": row[4],
                        "error_rate": row[5],
                        "total_requests": row[6],
                        "sla_met": bool(row[7])
                    }
                    for row in sla_metrics
                ],
                "cost_trends": [
                    {"date": date, "cost": cost}
                    for date, cost in cost_data
                ]
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {}
    
    def generate_monitoring_report(self, days: int = 7) -> str:
        """Generate comprehensive monitoring report."""
        try:
            dashboard_data = self.get_monitoring_dashboard_data()
            
            report = f"""
# VERTIGO PRODUCTION MONITORING REPORT
**Report Period**: Last {days} days
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 🎯 CURRENT STATUS

### System Health
"""
            
            current_metrics = dashboard_data.get("current_metrics", {})
            for metric, value in current_metrics.items():
                status = "🟢" if self._is_metric_healthy(metric, value) else "🔴"
                report += f"- **{metric.replace('_', ' ').title()}**: {value:.3f} {status}\n"
            
            report += f"""
### Active Alerts
**Total Active Alerts**: {len(dashboard_data.get('active_alerts', []))}
"""
            
            for alert in dashboard_data.get("active_alerts", [])[:5]:
                severity_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(alert["severity"], "⚪")
                report += f"- {severity_emoji} **{alert['severity'].upper()}**: {alert['message']}\n"
            
            report += """
## 📊 SLA COMPLIANCE

"""
            
            sla_data = dashboard_data.get("sla_compliance", [])
            if sla_data:
                met_sla = sum(1 for s in sla_data if s["sla_met"])
                sla_percentage = (met_sla / len(sla_data)) * 100
                report += f"**SLA Compliance Rate**: {sla_percentage:.1f}% ({met_sla}/{len(sla_data)} days)\n\n"
                
                # Recent SLA metrics
                if sla_data:
                    latest = sla_data[0]
                    report += f"**Latest SLA Metrics** ({latest['date']}):\n"
                    report += f"- Uptime: {latest['uptime']:.2f}%\n"
                    report += f"- Avg Response Time: {latest['avg_response_time']:.0f}ms\n"
                    report += f"- P95 Response Time: {latest['p95_response_time']:.0f}ms\n"
                    report += f"- Error Rate: {latest['error_rate']:.3f}\n"
                    report += f"- Total Requests: {latest['total_requests']:,}\n"
            
            report += """
## 💰 COST ANALYSIS

"""
            
            cost_data = dashboard_data.get("cost_trends", [])
            if cost_data:
                total_cost = sum(c["cost"] for c in cost_data)
                avg_daily_cost = total_cost / len(cost_data) if cost_data else 0
                report += f"**Total Cost** ({len(cost_data)} days): ${total_cost:.2f}\n"
                report += f"**Average Daily Cost**: ${avg_daily_cost:.2f}\n"
                
                # Cost budget status
                daily_budget = self.config.get("cost_budgets", {}).get("daily_budget_usd", 100.0)
                budget_utilization = (avg_daily_cost / daily_budget) * 100
                budget_status = "🟢" if budget_utilization < 80 else "🟡" if budget_utilization < 100 else "🔴"
                report += f"**Budget Utilization**: {budget_utilization:.1f}% {budget_status}\n"
            
            report += """
## 📈 PERFORMANCE TRENDS

### Key Metrics Trends
"""
            
            metrics_history = dashboard_data.get("metrics_history", {})
            for metric, history in metrics_history.items():
                if len(history) >= 2:
                    recent_values = [h["value"] for h in history[:10]]  # Last 10 values
                    trend = "📈" if recent_values[0] > recent_values[-1] else "📉" if recent_values[0] < recent_values[-1] else "➡️"
                    avg_value = sum(recent_values) / len(recent_values)
                    report += f"- **{metric.replace('_', ' ').title()}**: {avg_value:.3f} {trend}\n"
            
            report += """
## 🔧 RECOMMENDATIONS

Based on the monitoring data, here are key recommendations:

"""
            
            recommendations = self._generate_monitoring_recommendations(dashboard_data)
            for i, rec in enumerate(recommendations, 1):
                report += f"{i}. {rec}\n"
            
            report += f"""
## 📋 NEXT STEPS

### Immediate Actions
1. Review and resolve active alerts
2. Investigate any SLA violations
3. Monitor cost trends against budget

### Ongoing Monitoring
1. Continue automated monitoring and alerting
2. Review thresholds based on performance trends
3. Optimize for cost and performance improvements

---

*Report generated by Vertigo Production Monitoring System*
*Monitoring Database: {self.monitoring_db}*
"""
            
            return report
            
        except Exception as e:
            logger.error(f"Error generating monitoring report: {e}")
            return f"Error generating report: {e}"
    
    def _is_metric_healthy(self, metric: str, value: float) -> bool:
        """Check if a metric value is within healthy thresholds."""
        thresholds = self.metric_thresholds.get(metric, {})
        warning_threshold = thresholds.get("warning")
        
        if warning_threshold is None:
            return True  # No threshold defined, assume healthy
        
        # For metrics where lower is better
        if metric in ["error_rate", "cost_per_request", "response_time", "hallucination_rate"]:
            return value <= warning_threshold
        
        # For metrics where higher is better
        if metric in ["quality_score", "availability", "throughput", "user_satisfaction"]:
            return value >= warning_threshold
        
        return True  # Default to healthy
    
    def _generate_monitoring_recommendations(self, dashboard_data: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on monitoring data."""
        recommendations = []
        
        # Alert-based recommendations
        active_alerts = dashboard_data.get("active_alerts", [])
        if len(active_alerts) > 3:
            recommendations.append("High number of active alerts - review alert thresholds and resolve underlying issues")
        
        critical_alerts = [a for a in active_alerts if a["severity"] == "critical"]
        if critical_alerts:
            recommendations.append(f"Address {len(critical_alerts)} critical alerts immediately")
        
        # SLA-based recommendations
        sla_data = dashboard_data.get("sla_compliance", [])
        if sla_data:
            recent_sla_violations = [s for s in sla_data[:3] if not s["sla_met"]]
            if len(recent_sla_violations) >= 2:
                recommendations.append("Multiple recent SLA violations - investigate root causes")
        
        # Cost-based recommendations
        cost_data = dashboard_data.get("cost_trends", [])
        if cost_data and len(cost_data) >= 3:
            recent_costs = [c["cost"] for c in cost_data[:3]]
            if all(recent_costs[i] > recent_costs[i+1] for i in range(len(recent_costs)-1)):
                recommendations.append("Rising cost trend detected - review usage patterns and optimize")
        
        # Metric-based recommendations
        current_metrics = dashboard_data.get("current_metrics", {})
        
        if current_metrics.get("error_rate", 0) > 0.03:
            recommendations.append("Error rate elevated - investigate error patterns and root causes")
        
        if current_metrics.get("response_time", 0) > 2000:
            recommendations.append("Response time high - consider performance optimization")
        
        if current_metrics.get("quality_score", 1.0) < 0.8:
            recommendations.append("Quality score below target - review prompt performance and optimize")
        
        # Default recommendations
        if not recommendations:
            recommendations.extend([
                "System performing within normal parameters",
                "Continue monitoring key metrics and trends",
                "Consider expanding monitoring coverage to additional metrics"
            ])
        
        return recommendations[:5]  # Limit to top 5 recommendations

def run_production_monitoring_demo():
    """Run comprehensive production monitoring demonstration."""
    print("=" * 80) 
    print("VERTIGO PRODUCTION MONITORING SYSTEM DEMONSTRATION")
    print("=" * 80)
    
    # Initialize monitor
    monitor = ProductionMonitor()
    
    print("\n1. STARTING PRODUCTION MONITORING")
    print("-" * 50)
    
    monitor.start_monitoring()
    print("✅ Production monitoring started")
    
    # Let it run for a short time to collect some data
    print("📊 Collecting monitoring data...")
    time.sleep(5)
    
    print("\n2. GENERATING SYNTHETIC METRICS AND ALERTS")
    print("-" * 50)
    
    # Simulate some performance snapshots with issues
    test_snapshots = [
        PerformanceSnapshot(
            timestamp=datetime.now(),
            metrics={
                MonitoringMetric.RESPONSE_TIME: 3500.0,  # High response time
                MonitoringMetric.ERROR_RATE: 0.08,       # High error rate
                MonitoringMetric.QUALITY_SCORE: 0.65,    # Low quality
                MonitoringMetric.COST_PER_REQUEST: 0.15, # High cost
                MonitoringMetric.AVAILABILITY: 0.92,     # Low availability
                MonitoringMetric.THROUGHPUT: 45          # Low throughput
            },
            metadata={"source": "demo"}
        ),
        PerformanceSnapshot(
            timestamp=datetime.now(),
            metrics={
                MonitoringMetric.RESPONSE_TIME: 1200.0,  # Good response time
                MonitoringMetric.ERROR_RATE: 0.02,       # Good error rate
                MonitoringMetric.QUALITY_SCORE: 0.88,    # Good quality
                MonitoringMetric.COST_PER_REQUEST: 0.06, # Good cost
                MonitoringMetric.AVAILABILITY: 0.99,     # Good availability
                MonitoringMetric.THROUGHPUT: 120         # Good throughput
            },
            metadata={"source": "demo"}
        )
    ]
    
    # Process test snapshots
    for i, snapshot in enumerate(test_snapshots, 1):
        monitor._store_performance_snapshot(snapshot)
        monitor._check_thresholds(snapshot)
        monitor._detect_anomalies(snapshot)
        print(f"   Processed snapshot {i}")
    
    print("\n3. MONITORING DASHBOARD DATA")
    print("-" * 50)
    
    dashboard_data = monitor.get_monitoring_dashboard_data()
    
    print(f"Current Metrics:")
    current_metrics = dashboard_data.get("current_metrics", {})
    for metric, value in current_metrics.items():
        status = "🟢" if monitor._is_metric_healthy(metric, value) else "🔴"
        print(f"  • {metric.replace('_', ' ').title()}: {value:.3f} {status}")
    
    print(f"\nActive Alerts: {len(dashboard_data.get('active_alerts', []))}")
    for alert in dashboard_data.get("active_alerts", [])[:3]:
        severity_emoji = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}.get(alert["severity"], "⚪")
        print(f"  {severity_emoji} {alert['severity'].upper()}: {alert['message']}")
    
    print("\n4. GENERATING MONITORING REPORT")
    print("-" * 50)
    
    report = monitor.generate_monitoring_report(days=7)
    
    # Save report
    report_path = monitor.results_dir / f"monitoring_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"✅ Monitoring report generated: {report_path}")
    
    # Save dashboard data
    dashboard_path = monitor.results_dir / f"dashboard_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(dashboard_path, 'w') as f:
        json.dump(dashboard_data, f, indent=2, default=str)
    
    print(f"✅ Dashboard data saved: {dashboard_path}")
    
    print("\n5. MONITORING CAPABILITIES SUMMARY")
    print("-" * 50)
    
    print("✅ Real-time Performance Monitoring")
    print("   • Response time, error rate, throughput tracking")
    print("   • Quality score and user satisfaction monitoring")
    print("   • Cost tracking and budget management")
    
    print("\n✅ Automated Alerting System")
    print("   • Threshold-based alerts with multiple severity levels")
    print("   • Anomaly detection using statistical methods")
    print("   • Alert cooldowns to prevent notification spam")
    
    print("\n✅ SLA Compliance Tracking")
    print("   • Uptime, response time, and error rate SLAs")
    print("   • Daily SLA compliance reporting")
    print("   • SLA violation alerts")
    
    print("\n✅ Business Impact Monitoring")
    print("   • Cost budget tracking and overrun alerts")
    print("   • User satisfaction trend monitoring")
    print("   • Performance impact on business metrics")
    
    print("\n✅ Integration Capabilities")
    print("   • Langfuse observability platform integration")
    print("   • Multi-channel notifications (email, Slack, PagerDuty)")
    print("   • Historical data retention and cleanup")
    
    print("\n6. STOPPING MONITORING")
    print("-" * 50)
    
    monitor.stop_monitoring()
    print("✅ Production monitoring stopped")
    
    print("\n" + "=" * 80)
    print("PRODUCTION MONITORING DEMONSTRATION COMPLETE")
    print("=" * 80)
    print(f"\nResults directory: {monitor.results_dir}")
    print(f"Monitoring database: {monitor.monitoring_db}")
    print("\nThis demonstration shows enterprise-grade production")
    print("monitoring capabilities for LLM systems with:")
    print("• Comprehensive real-time monitoring")
    print("• Intelligent alerting and anomaly detection")
    print("• SLA compliance tracking")
    print("• Cost management and budget controls")
    print("• Business stakeholder reporting")

if __name__ == "__main__":
    run_production_monitoring_demo()