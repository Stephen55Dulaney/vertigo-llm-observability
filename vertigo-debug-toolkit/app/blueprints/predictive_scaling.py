"""
Predictive Scaling Blueprint for Vertigo Debug Toolkit.

Provides API endpoints for load forecasting and automated scaling recommendations.
"""

import logging
from flask import Blueprint, request, jsonify, render_template
from flask_login import login_required
from datetime import datetime, timedelta

from app.services.predictive_scaling import predictive_scaling_service

logger = logging.getLogger(__name__)

predictive_scaling_bp = Blueprint('predictive_scaling', __name__)

@predictive_scaling_bp.route('/api/load-forecast')
@login_required
def get_load_forecast():
    """Get load forecast for the specified time period."""
    try:
        hours_ahead = request.args.get('hours', 24, type=int)
        hours_ahead = max(1, min(hours_ahead, 168))  # Limit between 1 hour and 1 week
        
        forecasts = predictive_scaling_service.generate_load_forecast(hours_ahead)
        
        return jsonify({
            'status': 'success',
            'forecasts': [
                {
                    'timestamp': f.timestamp,
                    'predicted_traces': f.predicted_traces,
                    'predicted_cost': f.predicted_cost,
                    'confidence_interval': f.confidence_interval,
                    'forecast_period_hours': f.forecast_period_hours,
                    'model_accuracy': f.model_accuracy
                } for f in forecasts
            ],
            'forecast_period_hours': hours_ahead,
            'generated_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting load forecast: {e}")
        return jsonify({'error': str(e)}), 500

@predictive_scaling_bp.route('/api/scaling-recommendations')
@login_required
def get_scaling_recommendations():
    """Get scaling recommendations based on load forecast."""
    try:
        forecast_hours = request.args.get('forecast_hours', 6, type=int)
        forecast_hours = max(1, min(forecast_hours, 24))  # Limit between 1-24 hours
        
        recommendations = predictive_scaling_service.get_scaling_recommendations(forecast_hours)
        
        return jsonify({
            'status': 'success',
            'recommendations': [
                {
                    'action': r.action,
                    'target_capacity': r.target_capacity,
                    'confidence': r.confidence,
                    'justification': r.justification,
                    'expected_cost_impact': r.expected_cost_impact,
                    'implementation_priority': r.implementation_priority,
                    'estimated_response_time_ms': r.estimated_response_time_ms
                } for r in recommendations
            ],
            'forecast_period_hours': forecast_hours,
            'generated_at': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting scaling recommendations: {e}")
        return jsonify({'error': str(e)}), 500

@predictive_scaling_bp.route('/api/current-metrics')
@login_required
def get_current_metrics():
    """Get current resource utilization metrics."""
    try:
        metrics = predictive_scaling_service._get_current_resource_metrics()
        
        return jsonify({
            'status': 'success',
            'metrics': {
                'cpu_usage_percent': metrics.cpu_usage_percent,
                'memory_usage_percent': metrics.memory_usage_percent,
                'request_rate_per_minute': metrics.request_rate_per_minute,
                'avg_response_time_ms': metrics.avg_response_time_ms,
                'error_rate_percent': metrics.error_rate_percent,
                'cost_per_hour': metrics.cost_per_hour
            },
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error getting current metrics: {e}")
        return jsonify({'error': str(e)}), 500

@predictive_scaling_bp.route('/dashboard')
@login_required
def predictive_scaling_dashboard():
    """Predictive scaling dashboard page."""
    return render_template('predictive_scaling/dashboard.html')

@predictive_scaling_bp.route('/api/forecast-chart-data')
@login_required  
def get_forecast_chart_data():
    """Get forecast data formatted for charts."""
    try:
        hours_ahead = request.args.get('hours', 24, type=int)
        forecasts = predictive_scaling_service.generate_load_forecast(hours_ahead)
        
        # Format for chart visualization
        chart_data = {
            'labels': [f.timestamp for f in forecasts],
            'predicted_traces': [f.predicted_traces for f in forecasts],
            'predicted_costs': [f.predicted_cost for f in forecasts],
            'confidence_upper': [f.confidence_interval[1] for f in forecasts],
            'confidence_lower': [f.confidence_interval[0] for f in forecasts],
            'model_accuracy': [f.model_accuracy for f in forecasts]
        }
        
        return jsonify({
            'status': 'success',
            'chart_data': chart_data,
            'forecast_summary': {
                'total_predicted_traces': sum(f.predicted_traces for f in forecasts),
                'total_predicted_cost': round(sum(f.predicted_cost for f in forecasts), 4),
                'avg_model_accuracy': round(sum(f.model_accuracy for f in forecasts) / len(forecasts), 2) if forecasts else 0,
                'peak_hour': max(forecasts, key=lambda f: f.predicted_traces).timestamp if forecasts else None
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting forecast chart data: {e}")
        return jsonify({'error': str(e)}), 500