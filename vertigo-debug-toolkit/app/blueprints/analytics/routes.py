"""
Analytics routes for advanced performance insights and predictions.
"""

from flask import render_template, jsonify, request
from flask_login import login_required
from app.blueprints.analytics import analytics_bp
from app.services.analytics_service import analytics_service
import logging

logger = logging.getLogger(__name__)

@analytics_bp.route('/')
@login_required
def index():
    """Analytics dashboard page."""
    return render_template('analytics/index.html')

@analytics_bp.route('/api/trends')
@login_required
def get_trends():
    """Get performance trend analysis."""
    try:
        hours_back = request.args.get('hours', 24, type=int)
        hours_back = max(1, min(hours_back, 168))  # Limit between 1 hour and 1 week
        
        trends = analytics_service.analyze_performance_trends(hours_back=hours_back)
        
        # Convert to JSON-serializable format
        trends_data = []
        for trend in trends:
            trends_data.append({
                'metric_name': trend.metric_name,
                'current_value': trend.current_value,
                'previous_value': trend.previous_value,
                'change_percentage': round(trend.change_percentage, 2),
                'trend_direction': trend.trend_direction,
                'confidence_score': round(trend.confidence_score, 2),
                'prediction_next_hour': round(trend.prediction_next_hour, 2) if trend.prediction_next_hour else None,
                'prediction_confidence': round(trend.prediction_confidence, 2) if trend.prediction_confidence else None
            })
        
        return jsonify({
            "success": True,
            "trends": trends_data,
            "analysis_period_hours": hours_back
        })
        
    except Exception as e:
        logger.error(f"Error getting trend analysis: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "trends": []
        }), 500

@analytics_bp.route('/api/anomalies')
@login_required
def get_anomalies():
    """Get anomaly detection results."""
    try:
        hours_back = request.args.get('hours', 168, type=int)
        hours_back = max(24, min(hours_back, 720))  # Limit between 1 day and 1 month
        
        anomalies = analytics_service.detect_anomalies(hours_back=hours_back)
        
        # Convert to JSON-serializable format
        anomalies_data = []
        for anomaly in anomalies:
            anomalies_data.append({
                'metric_name': anomaly.metric_name,
                'timestamp': anomaly.timestamp.isoformat(),
                'actual_value': round(anomaly.actual_value, 2),
                'expected_value': round(anomaly.expected_value, 2),
                'deviation_score': round(anomaly.deviation_score, 2),
                'severity': anomaly.severity,
                'description': anomaly.description
            })
        
        return jsonify({
            "success": True,
            "anomalies": anomalies_data,
            "total_anomalies": len(anomalies_data),
            "critical_count": len([a for a in anomalies if a.severity == 'critical']),
            "high_count": len([a for a in anomalies if a.severity == 'high'])
        })
        
    except Exception as e:
        logger.error(f"Error getting anomaly detection: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "anomalies": []
        }), 500

@analytics_bp.route('/api/insights')
@login_required
def get_insights():
    """Get performance insights and recommendations."""
    try:
        insights = analytics_service.generate_performance_insights()
        
        # Convert to JSON-serializable format
        insights_data = []
        for insight in insights:
            insights_data.append({
                'insight_type': insight.insight_type,
                'title': insight.title,
                'description': insight.description,
                'impact_level': insight.impact_level,
                'recommendation': insight.recommendation,
                'metrics': insight.metrics,
                'confidence': round(insight.confidence, 2)
            })
        
        return jsonify({
            "success": True,
            "insights": insights_data,
            "total_insights": len(insights_data),
            "high_impact_count": len([i for i in insights if i.impact_level in ['high', 'critical']])
        })
        
    except Exception as e:
        logger.error(f"Error getting performance insights: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "insights": []
        }), 500

@analytics_bp.route('/api/predictions')
@login_required
def get_predictions():
    """Get capacity and performance predictions."""
    try:
        hours_ahead = request.args.get('hours', 24, type=int)
        hours_ahead = max(1, min(hours_ahead, 168))  # Limit between 1 hour and 1 week
        
        predictions = analytics_service.predict_capacity_needs(hours_ahead=hours_ahead)
        
        return jsonify({
            "success": True,
            "predictions": predictions,
            "prediction_horizon_hours": hours_ahead
        })
        
    except Exception as e:
        logger.error(f"Error getting capacity predictions: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "predictions": {}
        }), 500

@analytics_bp.route('/api/summary')
@login_required
def get_summary():
    """Get comprehensive analytics summary."""
    try:
        summary = analytics_service.get_analytics_summary()
        
        return jsonify({
            "success": True,
            "summary": summary
        })
        
    except Exception as e:
        logger.error(f"Error getting analytics summary: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "summary": {}
        }), 500

@analytics_bp.route('/api/health-score')
@login_required
def get_health_score():
    """Get current system health score."""
    try:
        summary = analytics_service.get_analytics_summary()
        
        return jsonify({
            "success": True,
            "health_score": summary.get('overall_health_score', 0),
            "data_quality_score": summary.get('data_quality_score', 0),
            "critical_issues": summary.get('critical_anomalies', 0),
            "timestamp": summary.get('analysis_timestamp')
        })
        
    except Exception as e:
        logger.error(f"Error getting health score: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "health_score": 0
        }), 500

@analytics_bp.route('/api/trend-chart-data')
@login_required
def get_trend_chart_data():
    """Get formatted data for trend charts."""
    try:
        metric = request.args.get('metric', 'error_rate')
        hours = request.args.get('hours', 24, type=int)
        
        trends = analytics_service.analyze_performance_trends(hours_back=hours)
        
        # Find the requested metric
        trend_data = None
        for trend in trends:
            if trend.metric_name.lower().replace(' ', '_') == metric.lower():
                trend_data = trend
                break
        
        if not trend_data:
            return jsonify({
                "success": False,
                "error": f"Metric '{metric}' not found",
                "chart_data": {}
            }), 404
        
        # Generate chart data
        chart_data = {
            'labels': ['Previous Period', 'Current Period'],
            'datasets': [{
                'label': trend_data.metric_name,
                'data': [trend_data.previous_value, trend_data.current_value],
                'borderColor': '#007bff' if trend_data.trend_direction == 'up' else '#28a745' if trend_data.trend_direction == 'down' else '#6c757d',
                'backgroundColor': f"{'#007bff' if trend_data.trend_direction == 'up' else '#28a745' if trend_data.trend_direction == 'down' else '#6c757d'}20",
                'fill': True
            }],
            'trend_info': {
                'direction': trend_data.trend_direction,
                'change_percentage': round(trend_data.change_percentage, 2),
                'confidence': round(trend_data.confidence_score, 2),
                'prediction': round(trend_data.prediction_next_hour, 2) if trend_data.prediction_next_hour else None
            }
        }
        
        return jsonify({
            "success": True,
            "chart_data": chart_data,
            "metric": metric
        })
        
    except Exception as e:
        logger.error(f"Error getting trend chart data: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "chart_data": {}
        }), 500