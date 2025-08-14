#!/usr/bin/env python3
"""
Predictive Scaling Service for Vertigo Debug Toolkit.

Implements load forecasting and automated scaling recommendations based on:
- Historical usage patterns
- Time-based prediction models
- Resource utilization trends
- Cost optimization constraints
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import numpy as np
from sqlalchemy import func, desc

from app.models import Trace, Cost, db
from app.services.cache_service import default_cache_service as cache_service

logger = logging.getLogger(__name__)

@dataclass
class LoadForecast:
    """Predicted load metrics for a time period."""
    timestamp: str
    predicted_traces: int
    predicted_cost: float
    confidence_interval: Tuple[float, float]  # (lower, upper)
    forecast_period_hours: int
    model_accuracy: float

@dataclass 
class ScalingRecommendation:
    """Scaling recommendation with justification."""
    action: str  # scale_up, scale_down, maintain
    target_capacity: int  # percentage of current capacity
    confidence: float
    justification: str
    expected_cost_impact: float
    implementation_priority: str  # high, medium, low
    estimated_response_time_ms: float

@dataclass
class ResourceMetrics:
    """Current resource utilization metrics."""
    cpu_usage_percent: float
    memory_usage_percent: float
    request_rate_per_minute: float
    avg_response_time_ms: float
    error_rate_percent: float
    cost_per_hour: float

class PredictiveScalingService:
    """Predictive scaling service with load forecasting."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cache_ttl = 300  # 5 minutes
        self.forecast_models = {
            'linear_trend': self._linear_trend_forecast,
            'moving_average': self._moving_average_forecast,
            'seasonal_decomposition': self._seasonal_forecast,
        }
        
        # Scaling thresholds
        self.scaling_config = {
            'scale_up_cpu_threshold': 75.0,
            'scale_up_memory_threshold': 80.0,
            'scale_down_cpu_threshold': 30.0,
            'scale_down_memory_threshold': 35.0,
            'min_capacity_percent': 25,
            'max_capacity_percent': 300,
            'cost_optimization_weight': 0.3,
            'performance_weight': 0.7
        }
        
        self.logger.info("PredictiveScalingService initialized")
    
    def generate_load_forecast(self, hours_ahead: int = 24) -> List[LoadForecast]:
        """Generate load forecast for the next N hours."""
        cache_key = f"load_forecast_{hours_ahead}h"
        
        try:
            # Check cache first
            cached = cache_service.get(cache_key)
            if cached:
                return [LoadForecast(**f) for f in cached]
            
            # Get historical data
            historical_data = self._get_historical_load_data(days_back=14)
            
            if len(historical_data) < 24:  # Need at least 24 hours of data
                return self._generate_baseline_forecast(hours_ahead)
            
            forecasts = []
            base_time = datetime.utcnow()
            
            # Generate forecast for each hour
            for hour_offset in range(1, hours_ahead + 1):
                forecast_time = base_time + timedelta(hours=hour_offset)
                
                # Use ensemble of models
                predictions = []
                for model_name, model_func in self.forecast_models.items():
                    try:
                        pred = model_func(historical_data, hour_offset)
                        predictions.append(pred)
                    except Exception as e:
                        self.logger.warning(f"Model {model_name} failed: {e}")
                
                if predictions:
                    # Average predictions with confidence intervals
                    avg_traces = int(np.mean([p['traces'] for p in predictions]))
                    avg_cost = np.mean([p['cost'] for p in predictions])
                    
                    # Calculate confidence interval
                    traces_std = np.std([p['traces'] for p in predictions])
                    confidence_interval = (
                        max(0, avg_traces - 1.96 * traces_std),
                        avg_traces + 1.96 * traces_std
                    )
                    
                    # Model accuracy based on historical validation
                    accuracy = self._calculate_model_accuracy(historical_data)
                    
                    forecast = LoadForecast(
                        timestamp=forecast_time.isoformat(),
                        predicted_traces=avg_traces,
                        predicted_cost=round(avg_cost, 4),
                        confidence_interval=confidence_interval,
                        forecast_period_hours=hour_offset,
                        model_accuracy=round(accuracy, 2)
                    )
                    forecasts.append(forecast)
                else:
                    # Fallback to simple trend
                    recent_avg = np.mean([d['traces'] for d in historical_data[-6:]])
                    forecasts.append(LoadForecast(
                        timestamp=forecast_time.isoformat(),
                        predicted_traces=int(recent_avg),
                        predicted_cost=recent_avg * 0.02,  # Estimated cost per trace
                        confidence_interval=(recent_avg * 0.8, recent_avg * 1.2),
                        forecast_period_hours=hour_offset,
                        model_accuracy=0.6
                    ))
            
            # Cache results
            cache_service.set(cache_key, [asdict(f) for f in forecasts], ttl=self.cache_ttl)
            return forecasts
            
        except Exception as e:
            self.logger.error(f"Error generating load forecast: {e}")
            return self._generate_baseline_forecast(hours_ahead)
    
    def get_scaling_recommendations(self, forecast_hours: int = 6) -> List[ScalingRecommendation]:
        """Generate scaling recommendations based on load forecast."""
        try:
            # Get load forecast
            forecasts = self.generate_load_forecast(forecast_hours)
            
            # Get current metrics
            current_metrics = self._get_current_resource_metrics()
            
            # Analyze scaling needs
            recommendations = []
            
            # Short-term recommendations (next 1-2 hours)
            short_term_forecast = forecasts[:2]
            short_term_rec = self._analyze_short_term_scaling(
                short_term_forecast, current_metrics
            )
            if short_term_rec:
                recommendations.append(short_term_rec)
            
            # Medium-term recommendations (next 3-6 hours)
            medium_term_forecast = forecasts[2:6]
            medium_term_rec = self._analyze_medium_term_scaling(
                medium_term_forecast, current_metrics
            )
            if medium_term_rec:
                recommendations.append(medium_term_rec)
            
            # Cost optimization recommendations
            cost_rec = self._analyze_cost_optimization(forecasts, current_metrics)
            if cost_rec:
                recommendations.append(cost_rec)
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating scaling recommendations: {e}")
            return [ScalingRecommendation(
                action="maintain",
                target_capacity=100,
                confidence=0.5,
                justification="Error in analysis - maintaining current capacity",
                expected_cost_impact=0.0,
                implementation_priority="low",
                estimated_response_time_ms=current_metrics.avg_response_time_ms if current_metrics else 1500
            )]
    
    def _get_historical_load_data(self, days_back: int = 14) -> List[Dict[str, Any]]:
        """Get historical load data for forecasting."""
        try:
            cutoff_time = datetime.utcnow() - timedelta(days=days_back)
            
            # Query traces grouped by hour
            hourly_data = db.session.query(
                func.date_trunc('hour', Trace.start_time).label('hour'),
                func.count(Trace.id).label('trace_count'),
                func.avg(Trace.duration_ms).label('avg_duration'),
                func.count(
                    case([(Trace.status == 'error', 1)])
                ).label('error_count')
            ).filter(
                Trace.start_time >= cutoff_time
            ).group_by(
                func.date_trunc('hour', Trace.start_time)
            ).order_by(
                func.date_trunc('hour', Trace.start_time)
            ).all()
            
            # Query costs grouped by hour
            hourly_costs = db.session.query(
                func.date_trunc('hour', Cost.timestamp).label('hour'),
                func.sum(Cost.cost_usd).label('total_cost')
            ).filter(
                Cost.timestamp >= cutoff_time
            ).group_by(
                func.date_trunc('hour', Cost.timestamp)
            ).order_by(
                func.date_trunc('hour', Cost.timestamp)
            ).all()
            
            # Combine data
            cost_dict = {c.hour: float(c.total_cost) for c in hourly_costs}
            
            historical_data = []
            for row in hourly_data:
                hour = row.hour
                historical_data.append({
                    'timestamp': hour.isoformat(),
                    'traces': row.trace_count,
                    'avg_duration_ms': float(row.avg_duration) if row.avg_duration else 0,
                    'error_count': row.error_count,
                    'cost': cost_dict.get(hour, 0.0),
                    'hour_of_day': hour.hour,
                    'day_of_week': hour.weekday()
                })
            
            return historical_data
            
        except Exception as e:
            self.logger.error(f"Error getting historical data: {e}")
            return []
    
    def _linear_trend_forecast(self, historical_data: List[Dict], hours_ahead: int) -> Dict[str, float]:
        """Simple linear trend forecasting."""
        if len(historical_data) < 2:
            return {'traces': 0, 'cost': 0}
        
        # Extract recent trend (last 48 hours)
        recent_data = historical_data[-48:] if len(historical_data) >= 48 else historical_data
        
        traces = [d['traces'] for d in recent_data]
        costs = [d['cost'] for d in recent_data]
        
        # Simple linear regression
        x = np.arange(len(traces))
        trace_slope = np.polyfit(x, traces, 1)[0] if len(traces) > 1 else 0
        cost_slope = np.polyfit(x, costs, 1)[0] if len(costs) > 1 else 0
        
        # Project forward
        last_traces = traces[-1] if traces else 0
        last_cost = costs[-1] if costs else 0
        
        predicted_traces = max(0, last_traces + (trace_slope * hours_ahead))
        predicted_cost = max(0, last_cost + (cost_slope * hours_ahead))
        
        return {'traces': predicted_traces, 'cost': predicted_cost}
    
    def _moving_average_forecast(self, historical_data: List[Dict], hours_ahead: int) -> Dict[str, float]:
        """Moving average forecasting with seasonal adjustment."""
        if len(historical_data) < 24:
            return {'traces': 0, 'cost': 0}
        
        # Get same hour of day from previous days
        target_hour = (datetime.utcnow() + timedelta(hours=hours_ahead)).hour
        same_hour_data = [d for d in historical_data if d['hour_of_day'] == target_hour]
        
        if same_hour_data:
            # Weighted average of same hours, more weight to recent
            weights = np.exp(np.linspace(-1, 0, len(same_hour_data)))
            weights /= weights.sum()
            
            predicted_traces = sum(d['traces'] * w for d, w in zip(same_hour_data, weights))
            predicted_cost = sum(d['cost'] * w for d, w in zip(same_hour_data, weights))
        else:
            # Fallback to overall average
            predicted_traces = np.mean([d['traces'] for d in historical_data[-24:]])
            predicted_cost = np.mean([d['cost'] for d in historical_data[-24:]])
        
        return {'traces': predicted_traces, 'cost': predicted_cost}
    
    def _seasonal_forecast(self, historical_data: List[Dict], hours_ahead: int) -> Dict[str, float]:
        """Seasonal decomposition forecasting."""
        if len(historical_data) < 168:  # Need at least 1 week of data
            return self._moving_average_forecast(historical_data, hours_ahead)
        
        # Simple seasonal adjustment based on day of week and hour
        target_time = datetime.utcnow() + timedelta(hours=hours_ahead)
        target_dow = target_time.weekday()
        target_hour = target_time.hour
        
        # Find similar time periods
        similar_periods = [
            d for d in historical_data 
            if d['day_of_week'] == target_dow and abs(d['hour_of_day'] - target_hour) <= 1
        ]
        
        if similar_periods:
            # Recent seasonal pattern
            recent_similar = similar_periods[-4:] if len(similar_periods) >= 4 else similar_periods
            predicted_traces = np.mean([d['traces'] for d in recent_similar])
            predicted_cost = np.mean([d['cost'] for d in recent_similar])
        else:
            # Fallback
            predicted_traces = np.mean([d['traces'] for d in historical_data[-24:]])
            predicted_cost = np.mean([d['cost'] for d in historical_data[-24:]])
        
        return {'traces': predicted_traces, 'cost': predicted_cost}
    
    def _calculate_model_accuracy(self, historical_data: List[Dict]) -> float:
        """Calculate model accuracy based on recent predictions."""
        if len(historical_data) < 48:
            return 0.7  # Default accuracy
        
        # Test model on last 24 hours using previous 24 hours as input
        test_data = historical_data[-24:]
        train_data = historical_data[-48:-24]
        
        errors = []
        for i, actual in enumerate(test_data):
            try:
                prediction = self._linear_trend_forecast(train_data, i + 1)
                error = abs(prediction['traces'] - actual['traces']) / max(actual['traces'], 1)
                errors.append(error)
            except:
                continue
        
        if errors:
            mean_error = np.mean(errors)
            accuracy = max(0.1, 1.0 - mean_error)  # Convert error to accuracy
        else:
            accuracy = 0.7
        
        return min(1.0, accuracy)
    
    def _generate_baseline_forecast(self, hours_ahead: int) -> List[LoadForecast]:
        """Generate baseline forecast when insufficient historical data."""
        baseline_traces = 5  # Conservative estimate
        baseline_cost = 0.1
        
        forecasts = []
        base_time = datetime.utcnow()
        
        for hour_offset in range(1, hours_ahead + 1):
            forecast_time = base_time + timedelta(hours=hour_offset)
            
            forecasts.append(LoadForecast(
                timestamp=forecast_time.isoformat(),
                predicted_traces=baseline_traces,
                predicted_cost=baseline_cost,
                confidence_interval=(baseline_traces * 0.5, baseline_traces * 2.0),
                forecast_period_hours=hour_offset,
                model_accuracy=0.5
            ))
        
        return forecasts
    
    def _get_current_resource_metrics(self) -> ResourceMetrics:
        """Get current resource utilization metrics."""
        try:
            # Get recent data (last hour)
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            
            recent_traces = db.session.query(Trace).filter(
                Trace.start_time >= one_hour_ago
            ).all()
            
            recent_costs = db.session.query(func.sum(Cost.cost_usd)).filter(
                Cost.timestamp >= one_hour_ago
            ).scalar() or 0
            
            # Calculate metrics
            trace_count = len(recent_traces)
            avg_response_time = np.mean([t.duration_ms for t in recent_traces if t.duration_ms]) if recent_traces else 1500
            error_count = sum(1 for t in recent_traces if t.status == 'error')
            error_rate = (error_count / trace_count * 100) if trace_count > 0 else 0
            
            # Mock system metrics (in production, use actual system monitoring)
            cpu_usage = min(95, max(10, 30 + (trace_count * 2)))  # Simulate CPU based on load
            memory_usage = min(90, max(20, 25 + (trace_count * 1.5)))  # Simulate memory
            
            return ResourceMetrics(
                cpu_usage_percent=cpu_usage,
                memory_usage_percent=memory_usage,
                request_rate_per_minute=trace_count,
                avg_response_time_ms=avg_response_time,
                error_rate_percent=error_rate,
                cost_per_hour=float(recent_costs)
            )
            
        except Exception as e:
            self.logger.error(f"Error getting current metrics: {e}")
            return ResourceMetrics(
                cpu_usage_percent=50.0,
                memory_usage_percent=45.0,
                request_rate_per_minute=10.0,
                avg_response_time_ms=1500,
                error_rate_percent=2.0,
                cost_per_hour=0.1
            )
    
    def _analyze_short_term_scaling(self, forecasts: List[LoadForecast], 
                                  current_metrics: ResourceMetrics) -> Optional[ScalingRecommendation]:
        """Analyze short-term scaling needs (1-2 hours)."""
        if not forecasts:
            return None
        
        # Predict resource usage based on load forecast
        avg_predicted_load = np.mean([f.predicted_traces for f in forecasts])
        current_load = current_metrics.request_rate_per_minute
        
        load_increase_ratio = avg_predicted_load / max(current_load, 1)
        
        # Predict resource impact
        predicted_cpu = current_metrics.cpu_usage_percent * load_increase_ratio
        predicted_memory = current_metrics.memory_usage_percent * load_increase_ratio
        
        # Determine scaling action
        if (predicted_cpu > self.scaling_config['scale_up_cpu_threshold'] or 
            predicted_memory > self.scaling_config['scale_up_memory_threshold']):
            
            # Scale up needed
            scale_factor = max(predicted_cpu / 70, predicted_memory / 70)  # Target 70% utilization
            target_capacity = min(int(100 * scale_factor), self.scaling_config['max_capacity_percent'])
            
            return ScalingRecommendation(
                action="scale_up",
                target_capacity=target_capacity,
                confidence=0.8,
                justification=f"Predicted load increase of {load_increase_ratio:.1f}x will exceed resource thresholds",
                expected_cost_impact=sum(f.predicted_cost for f in forecasts) * 1.2,
                implementation_priority="high",
                estimated_response_time_ms=current_metrics.avg_response_time_ms * 0.8
            )
        
        elif (predicted_cpu < self.scaling_config['scale_down_cpu_threshold'] and 
              predicted_memory < self.scaling_config['scale_down_memory_threshold'] and
              current_metrics.cpu_usage_percent < 60):
            
            # Scale down possible
            target_capacity = max(int(100 * max(predicted_cpu / 50, predicted_memory / 50)), 
                                self.scaling_config['min_capacity_percent'])
            
            return ScalingRecommendation(
                action="scale_down",
                target_capacity=target_capacity,
                confidence=0.7,
                justification=f"Predicted low load allows for resource optimization",
                expected_cost_impact=-sum(f.predicted_cost for f in forecasts) * 0.3,
                implementation_priority="medium",
                estimated_response_time_ms=current_metrics.avg_response_time_ms * 1.1
            )
        
        return None
    
    def _analyze_medium_term_scaling(self, forecasts: List[LoadForecast], 
                                   current_metrics: ResourceMetrics) -> Optional[ScalingRecommendation]:
        """Analyze medium-term scaling needs (3-6 hours)."""
        if not forecasts:
            return None
        
        # Look for sustained trends
        load_trend = [f.predicted_traces for f in forecasts]
        
        if len(load_trend) >= 3:
            # Check if load is consistently increasing
            increasing = all(load_trend[i] >= load_trend[i-1] * 0.9 for i in range(1, len(load_trend)))
            decreasing = all(load_trend[i] <= load_trend[i-1] * 1.1 for i in range(1, len(load_trend)))
            
            if increasing and load_trend[-1] > load_trend[0] * 1.3:
                # Sustained growth trend
                growth_rate = load_trend[-1] / load_trend[0]
                target_capacity = min(int(100 * growth_rate * 1.2), self.scaling_config['max_capacity_percent'])
                
                return ScalingRecommendation(
                    action="scale_up",
                    target_capacity=target_capacity,
                    confidence=0.7,
                    justification=f"Sustained growth trend detected (4+3% increase over {len(forecasts)} hours)",
                    expected_cost_impact=sum(f.predicted_cost for f in forecasts),
                    implementation_priority="medium",
                    estimated_response_time_ms=current_metrics.avg_response_time_ms * 0.9
                )
            
            elif decreasing and load_trend[-1] < load_trend[0] * 0.7:
                # Sustained decline trend
                decline_rate = load_trend[-1] / load_trend[0]
                target_capacity = max(int(100 * decline_rate * 1.2), self.scaling_config['min_capacity_percent'])
                
                return ScalingRecommendation(
                    action="scale_down",
                    target_capacity=target_capacity,
                    confidence=0.6,
                    justification=f"Sustained decline trend allows gradual scaling down",
                    expected_cost_impact=-sum(f.predicted_cost for f in forecasts) * 0.2,
                    implementation_priority="low",
                    estimated_response_time_ms=current_metrics.avg_response_time_ms * 1.05
                )
        
        return None
    
    def _analyze_cost_optimization(self, forecasts: List[LoadForecast], 
                                 current_metrics: ResourceMetrics) -> Optional[ScalingRecommendation]:
        """Analyze cost optimization opportunities."""
        if not forecasts:
            return None
        
        total_predicted_cost = sum(f.predicted_cost for f in forecasts)
        current_hourly_cost = current_metrics.cost_per_hour
        
        # If predicted costs are high but current utilization is low, recommend optimization
        if (total_predicted_cost > current_hourly_cost * 1.5 and 
            current_metrics.cpu_usage_percent < 50 and
            current_metrics.avg_response_time_ms < 2000):
            
            return ScalingRecommendation(
                action="maintain",
                target_capacity=85,
                confidence=0.6,
                justification="Cost optimization: maintain slightly reduced capacity to optimize spend",
                expected_cost_impact=-total_predicted_cost * 0.15,
                implementation_priority="low",
                estimated_response_time_ms=current_metrics.avg_response_time_ms * 1.02
            )
        
        return None

# Global instance
predictive_scaling_service = PredictiveScalingService()