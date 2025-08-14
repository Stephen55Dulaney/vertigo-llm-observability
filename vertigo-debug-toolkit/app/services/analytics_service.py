"""
Advanced Analytics Service for Vertigo Debug Toolkit
Provides intelligent insights, trend analysis, and predictive monitoring.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict
import statistics
import math

from app.models import db
from sqlalchemy import text, func
from app.services.live_data_service import live_data_service

logger = logging.getLogger(__name__)

@dataclass
class TrendAnalysis:
    """Trend analysis result."""
    metric_name: str
    current_value: float
    previous_value: float
    change_percentage: float
    trend_direction: str  # 'up', 'down', 'stable'
    confidence_score: float
    prediction_next_hour: Optional[float] = None
    prediction_confidence: Optional[float] = None

@dataclass
class Anomaly:
    """Anomaly detection result."""
    metric_name: str
    timestamp: datetime
    actual_value: float
    expected_value: float
    deviation_score: float
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str

@dataclass
class PerformanceInsight:
    """Performance insight."""
    insight_type: str
    title: str
    description: str
    impact_level: str  # 'low', 'medium', 'high', 'critical'
    recommendation: str
    metrics: Dict[str, Any]
    confidence: float

class AnalyticsService:
    """
    Advanced analytics service for performance monitoring.
    
    Features:
    - Trend analysis with statistical significance
    - Anomaly detection using statistical methods
    - Performance insights and recommendations
    - Predictive analytics for capacity planning
    - Pattern recognition in trace data
    """
    
    def __init__(self):
        """Initialize analytics service."""
        self.trend_window_hours = 24
        self.anomaly_threshold = 2.0  # Standard deviations
        self.prediction_window_hours = 1
        
        # Insight generators
        self.insight_generators = [
            self._generate_error_rate_insights,
            self._generate_latency_insights,
            self._generate_cost_insights,
            self._generate_throughput_insights,
            self._generate_data_source_insights
        ]
    
    def analyze_performance_trends(self, hours_back: int = 24) -> List[TrendAnalysis]:
        """Analyze performance trends over time."""
        try:
            trends = []
            
            # Get current and historical metrics
            current_metrics = live_data_service.get_unified_performance_metrics(
                hours=1, data_source='all'
            )
            historical_metrics = live_data_service.get_unified_performance_metrics(
                hours=hours_back, data_source='all'
            )
            
            # Analyze key metrics
            metrics_to_analyze = [
                ('error_rate', 'Error Rate', '%'),
                ('avg_latency_ms', 'Average Latency', 'ms'),
                ('total_cost', 'Total Cost', '$'),
                ('total_traces', 'Trace Volume', 'traces'),
                ('success_rate', 'Success Rate', '%')
            ]
            
            for metric_key, metric_name, unit in metrics_to_analyze:
                current_value = current_metrics.get(metric_key, 0)
                historical_value = historical_metrics.get(metric_key, 0)
                
                if historical_value > 0:
                    change_pct = ((current_value - historical_value) / historical_value) * 100
                else:
                    change_pct = 100 if current_value > 0 else 0
                
                # Determine trend direction
                if abs(change_pct) < 5:
                    trend_direction = 'stable'
                elif change_pct > 0:
                    trend_direction = 'up'
                else:
                    trend_direction = 'down'
                
                # Calculate confidence based on data availability
                confidence = min(0.9, max(0.3, current_metrics.get('total_traces', 0) / 100))
                
                # Simple prediction (linear trend)
                prediction = None
                prediction_confidence = None
                if historical_value > 0 and abs(change_pct) > 1:
                    hourly_change = change_pct / hours_back
                    prediction = current_value * (1 + (hourly_change / 100))
                    prediction_confidence = confidence * 0.7
                
                trends.append(TrendAnalysis(
                    metric_name=metric_name,
                    current_value=current_value,
                    previous_value=historical_value,
                    change_percentage=change_pct,
                    trend_direction=trend_direction,
                    confidence_score=confidence,
                    prediction_next_hour=prediction,
                    prediction_confidence=prediction_confidence
                ))
            
            return trends
            
        except Exception as e:
            logger.error(f"Error analyzing performance trends: {e}")
            return []
    
    def detect_anomalies(self, hours_back: int = 168) -> List[Anomaly]:
        """Detect anomalies in performance metrics using statistical methods."""
        try:
            anomalies = []
            
            # Get time series data for anomaly detection
            time_series = live_data_service.get_latency_time_series(hours=hours_back, data_source='all')
            
            if len(time_series) < 10:  # Need sufficient data
                return anomalies
            
            # Analyze latency anomalies
            latencies = [point.get('latency_avg', 0) for point in time_series if point.get('latency_avg', 0) > 0]
            
            if len(latencies) >= 5:
                mean_latency = statistics.mean(latencies)
                std_latency = statistics.stdev(latencies) if len(latencies) > 1 else 0
                
                # Check recent data points for anomalies
                recent_points = time_series[-5:]  # Last 5 data points
                for point in recent_points:
                    latency = point.get('latency_avg', 0)
                    if latency > 0 and std_latency > 0:
                        deviation = abs(latency - mean_latency) / std_latency
                        
                        if deviation > self.anomaly_threshold:
                            severity = self._calculate_anomaly_severity(deviation)
                            anomalies.append(Anomaly(
                                metric_name='latency',
                                timestamp=datetime.fromisoformat(point['time'].replace('Z', '+00:00')),
                                actual_value=latency,
                                expected_value=mean_latency,
                                deviation_score=deviation,
                                severity=severity,
                                description=f"Latency spike detected: {latency:.1f}ms vs expected {mean_latency:.1f}ms"
                            ))
            
            # Analyze error rate anomalies
            current_metrics = live_data_service.get_unified_performance_metrics(hours=1)
            historical_metrics = live_data_service.get_unified_performance_metrics(hours=hours_back)
            
            current_error_rate = current_metrics.get('error_rate', 0)
            historical_error_rate = historical_metrics.get('error_rate', 0)
            
            if historical_error_rate > 0:
                error_rate_change = abs(current_error_rate - historical_error_rate) / historical_error_rate
                
                if error_rate_change > 0.5:  # 50% change threshold
                    anomalies.append(Anomaly(
                        metric_name='error_rate',
                        timestamp=datetime.utcnow(),
                        actual_value=current_error_rate,
                        expected_value=historical_error_rate,
                        deviation_score=error_rate_change,
                        severity=self._calculate_anomaly_severity(error_rate_change * 2),
                        description=f"Error rate anomaly: {current_error_rate:.1f}% vs expected {historical_error_rate:.1f}%"
                    ))
            
            return sorted(anomalies, key=lambda x: x.deviation_score, reverse=True)
            
        except Exception as e:
            logger.error(f"Error detecting anomalies: {e}")
            return []
    
    def generate_performance_insights(self) -> List[PerformanceInsight]:
        """Generate actionable performance insights."""
        try:
            insights = []
            
            for generator in self.insight_generators:
                try:
                    insight = generator()
                    if insight:
                        insights.append(insight)
                except Exception as e:
                    logger.error(f"Error generating insight: {e}")
            
            # Sort by impact level and confidence
            impact_scores = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
            insights.sort(key=lambda x: (impact_scores.get(x.impact_level, 0), x.confidence), reverse=True)
            
            return insights[:10]  # Return top 10 insights
            
        except Exception as e:
            logger.error(f"Error generating performance insights: {e}")
            return []
    
    def _generate_error_rate_insights(self) -> Optional[PerformanceInsight]:
        """Generate insights about error rates."""
        try:
            current_metrics = live_data_service.get_unified_performance_metrics(hours=1)
            historical_metrics = live_data_service.get_unified_performance_metrics(hours=24)
            
            current_error_rate = current_metrics.get('error_rate', 0)
            historical_error_rate = historical_metrics.get('error_rate', 0)
            
            if current_error_rate > 10:  # High error rate
                return PerformanceInsight(
                    insight_type='error_analysis',
                    title='High Error Rate Detected',
                    description=f'Current error rate of {current_error_rate:.1f}% is significantly elevated.',
                    impact_level='high' if current_error_rate > 20 else 'medium',
                    recommendation='Review recent traces for common error patterns. Check data source health and API dependencies.',
                    metrics={
                        'current_error_rate': current_error_rate,
                        'historical_error_rate': historical_error_rate,
                        'error_count': current_metrics.get('error_count', 0)
                    },
                    confidence=0.9
                )
            elif historical_error_rate > 0 and current_error_rate < historical_error_rate * 0.5:
                return PerformanceInsight(
                    insight_type='improvement',
                    title='Error Rate Improvement',
                    description=f'Error rate improved from {historical_error_rate:.1f}% to {current_error_rate:.1f}%.',
                    impact_level='low',
                    recommendation='Monitor this improvement trend. Consider documenting what changes led to this improvement.',
                    metrics={
                        'current_error_rate': current_error_rate,
                        'historical_error_rate': historical_error_rate,
                        'improvement_percentage': ((historical_error_rate - current_error_rate) / historical_error_rate) * 100
                    },
                    confidence=0.8
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating error rate insights: {e}")
            return None
    
    def _generate_latency_insights(self) -> Optional[PerformanceInsight]:
        """Generate insights about latency patterns."""
        try:
            time_series = live_data_service.get_latency_time_series(hours=24)
            if len(time_series) < 5:
                return None
            
            latencies = [point.get('latency_avg', 0) for point in time_series if point.get('latency_avg', 0) > 0]
            
            if latencies:
                avg_latency = statistics.mean(latencies)
                max_latency = max(latencies)
                min_latency = min(latencies)
                
                if max_latency > avg_latency * 3:  # Significant spike
                    return PerformanceInsight(
                        insight_type='latency_analysis',
                        title='Latency Spike Pattern Detected',
                        description=f'Maximum latency ({max_latency:.1f}ms) is {max_latency/avg_latency:.1f}x the average ({avg_latency:.1f}ms).',
                        impact_level='medium' if max_latency > 5000 else 'low',
                        recommendation='Investigate causes of latency spikes. Consider implementing request timeouts and circuit breakers.',
                        metrics={
                            'avg_latency_ms': avg_latency,
                            'max_latency_ms': max_latency,
                            'spike_ratio': max_latency / avg_latency,
                            'variance': statistics.variance(latencies) if len(latencies) > 1 else 0
                        },
                        confidence=0.85
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating latency insights: {e}")
            return None
    
    def _generate_cost_insights(self) -> Optional[PerformanceInsight]:
        """Generate insights about cost patterns."""
        try:
            current_metrics = live_data_service.get_unified_performance_metrics(hours=1)
            daily_metrics = live_data_service.get_unified_performance_metrics(hours=24)
            
            hourly_cost = current_metrics.get('total_cost', 0)
            daily_cost = daily_metrics.get('total_cost', 0)
            
            if hourly_cost > 0:
                projected_daily_cost = hourly_cost * 24
                
                if projected_daily_cost > daily_cost * 2:  # Cost spike
                    return PerformanceInsight(
                        insight_type='cost_analysis',
                        title='Cost Spike Detected',
                        description=f'Current hourly cost trend suggests daily cost could reach ${projected_daily_cost:.2f}, up from ${daily_cost:.2f}.',
                        impact_level='high' if projected_daily_cost > 50 else 'medium',
                        recommendation='Review recent high-cost operations. Consider optimizing model selection or implementing cost controls.',
                        metrics={
                            'hourly_cost': hourly_cost,
                            'daily_cost': daily_cost,
                            'projected_daily_cost': projected_daily_cost,
                            'cost_per_trace': hourly_cost / max(current_metrics.get('total_traces', 1), 1)
                        },
                        confidence=0.75
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating cost insights: {e}")
            return None
    
    def _generate_throughput_insights(self) -> Optional[PerformanceInsight]:
        """Generate insights about throughput patterns."""
        try:
            current_metrics = live_data_service.get_unified_performance_metrics(hours=1)
            historical_metrics = live_data_service.get_unified_performance_metrics(hours=24)
            
            current_traces = current_metrics.get('total_traces', 0)
            historical_traces = historical_metrics.get('total_traces', 0)
            
            if historical_traces > 0:
                hourly_rate = current_traces
                daily_average_hourly = historical_traces / 24
                
                if hourly_rate > daily_average_hourly * 2:  # Traffic spike
                    return PerformanceInsight(
                        insight_type='throughput_analysis',
                        title='Traffic Spike Detected',
                        description=f'Current hourly rate ({hourly_rate} traces) is {hourly_rate/daily_average_hourly:.1f}x the daily average ({daily_average_hourly:.1f}/hour).',
                        impact_level='medium',
                        recommendation='Monitor system resources and response times during high traffic. Consider auto-scaling if available.',
                        metrics={
                            'current_hourly_traces': hourly_rate,
                            'daily_average_hourly': daily_average_hourly,
                            'traffic_multiplier': hourly_rate / daily_average_hourly,
                            'total_daily_traces': historical_traces
                        },
                        confidence=0.8
                    )
                elif hourly_rate < daily_average_hourly * 0.3:  # Traffic drop
                    return PerformanceInsight(
                        insight_type='throughput_analysis',
                        title='Traffic Drop Detected',
                        description=f'Current traffic ({hourly_rate} traces/hour) is significantly below average ({daily_average_hourly:.1f}/hour).',
                        impact_level='low',
                        recommendation='Verify if this is expected (maintenance, scheduled downtime) or investigate potential issues.',
                        metrics={
                            'current_hourly_traces': hourly_rate,
                            'daily_average_hourly': daily_average_hourly,
                            'traffic_ratio': hourly_rate / daily_average_hourly if daily_average_hourly > 0 else 0
                        },
                        confidence=0.7
                    )
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating throughput insights: {e}")
            return None
    
    def _generate_data_source_insights(self) -> Optional[PerformanceInsight]:
        """Generate insights about data source health."""
        try:
            source_status = live_data_service.get_data_source_status()
            
            unhealthy_sources = []
            degraded_sources = []
            
            for source_name, source_info in source_status.get('sources', {}).items():
                health = source_info.get('health', 'unknown')
                if health == 'unhealthy':
                    unhealthy_sources.append(source_name)
                elif health == 'degraded':
                    degraded_sources.append(source_name)
            
            if unhealthy_sources:
                return PerformanceInsight(
                    insight_type='infrastructure',
                    title='Data Source Issues Detected',
                    description=f'Unhealthy data sources: {", ".join(unhealthy_sources)}. This may impact data completeness.',
                    impact_level='critical' if len(unhealthy_sources) > 1 else 'high',
                    recommendation='Check data source connections and authentication. Review logs for specific error messages.',
                    metrics={
                        'unhealthy_sources': unhealthy_sources,
                        'degraded_sources': degraded_sources,
                        'total_sources': len(source_status.get('sources', {})),
                        'healthy_percentage': ((len(source_status.get('sources', {})) - len(unhealthy_sources) - len(degraded_sources)) / max(len(source_status.get('sources', {})), 1)) * 100
                    },
                    confidence=0.95
                )
            elif degraded_sources:
                return PerformanceInsight(
                    insight_type='infrastructure',
                    title='Data Source Performance Issues',
                    description=f'Degraded data sources: {", ".join(degraded_sources)}. Performance may be impacted.',
                    impact_level='medium',
                    recommendation='Monitor these sources closely. Consider implementing failover or retry mechanisms.',
                    metrics={
                        'degraded_sources': degraded_sources,
                        'total_sources': len(source_status.get('sources', {}))
                    },
                    confidence=0.8
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating data source insights: {e}")
            return None
    
    def _calculate_anomaly_severity(self, deviation_score: float) -> str:
        """Calculate anomaly severity based on deviation score."""
        if deviation_score > 4:
            return 'critical'
        elif deviation_score > 3:
            return 'high'
        elif deviation_score > 2:
            return 'medium'
        else:
            return 'low'
    
    def predict_capacity_needs(self, hours_ahead: int = 24) -> Dict[str, Any]:
        """Predict capacity needs based on current trends."""
        try:
            trends = self.analyze_performance_trends(hours_back=168)  # Use weekly data
            current_metrics = live_data_service.get_unified_performance_metrics(hours=1)
            
            predictions = {}
            
            for trend in trends:
                if trend.prediction_next_hour and trend.prediction_confidence:
                    # Extrapolate to requested time horizon
                    hourly_change_rate = (trend.prediction_next_hour - trend.current_value) / trend.current_value if trend.current_value > 0 else 0
                    predicted_value = trend.current_value * (1 + (hourly_change_rate * hours_ahead))
                    
                    predictions[trend.metric_name.lower().replace(' ', '_')] = {
                        'current_value': trend.current_value,
                        'predicted_value': predicted_value,
                        'change_percentage': ((predicted_value - trend.current_value) / trend.current_value) * 100 if trend.current_value > 0 else 0,
                        'confidence': trend.prediction_confidence * (1 - (hours_ahead / 168))  # Confidence decreases with time
                    }
            
            # Capacity recommendations
            recommendations = []
            
            if 'trace_volume' in predictions:
                volume_prediction = predictions['trace_volume']
                if volume_prediction['change_percentage'] > 50 and volume_prediction['confidence'] > 0.5:
                    recommendations.append("Consider scaling infrastructure to handle increased trace volume")
            
            if 'total_cost' in predictions:
                cost_prediction = predictions['total_cost']
                if cost_prediction['change_percentage'] > 100 and cost_prediction['confidence'] > 0.5:
                    recommendations.append("Budget for increased LLM costs due to growing usage")
            
            return {
                'predictions': predictions,
                'recommendations': recommendations,
                'prediction_horizon_hours': hours_ahead,
                'confidence_note': 'Confidence decreases with longer prediction horizons'
            }
            
        except Exception as e:
            logger.error(f"Error predicting capacity needs: {e}")
            return {
                'predictions': {},
                'recommendations': ['Unable to generate capacity predictions'],
                'error': str(e)
            }
    
    def get_analytics_summary(self) -> Dict[str, Any]:
        """Get comprehensive analytics summary."""
        try:
            trends = self.analyze_performance_trends()
            anomalies = self.detect_anomalies()
            insights = self.generate_performance_insights()
            capacity = self.predict_capacity_needs()
            
            # Calculate overall system health score
            health_factors = []
            
            # Factor in error rates
            current_metrics = live_data_service.get_unified_performance_metrics(hours=1)
            error_rate = current_metrics.get('error_rate', 0)
            error_health = max(0, 100 - (error_rate * 5))  # 5% error = 75 health
            health_factors.append(error_health)
            
            # Factor in anomalies
            critical_anomalies = len([a for a in anomalies if a.severity in ['critical', 'high']])
            anomaly_health = max(0, 100 - (critical_anomalies * 20))
            health_factors.append(anomaly_health)
            
            # Factor in data source health
            source_status = live_data_service.get_data_source_status()
            source_health = (len([s for s in source_status.get('sources', {}).values() if s.get('health') == 'healthy']) / max(len(source_status.get('sources', {})), 1)) * 100
            health_factors.append(source_health)
            
            overall_health = statistics.mean(health_factors) if health_factors else 50
            
            return {
                'overall_health_score': round(overall_health, 1),
                'trends_analyzed': len(trends),
                'anomalies_detected': len(anomalies),
                'critical_anomalies': len([a for a in anomalies if a.severity in ['critical', 'high']]),
                'insights_generated': len(insights),
                'high_impact_insights': len([i for i in insights if i.impact_level in ['high', 'critical']]),
                'capacity_predictions_available': len(capacity.get('predictions', {})),
                'recommendations_count': len(capacity.get('recommendations', [])),
                'data_quality_score': round(source_health, 1),
                'analysis_timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting analytics summary: {e}")
            return {
                'overall_health_score': 0,
                'error': str(e),
                'analysis_timestamp': datetime.utcnow().isoformat()
            }

# Global service instance
analytics_service = AnalyticsService()