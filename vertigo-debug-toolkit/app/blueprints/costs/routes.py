"""
Advanced cost optimization routes for the Vertigo Debug Toolkit.
"""

from flask import render_template, jsonify, request
from flask_login import login_required
from app.blueprints.costs import costs_bp
from app.services.cost_optimization_service import cost_optimization_service
import logging

logger = logging.getLogger(__name__)


@costs_bp.route('/')
@login_required
def index():
    """Cost optimization dashboard."""
    return render_template('costs/index.html')


@costs_bp.route('/api/cost-breakdown')
@login_required
def get_cost_breakdown():
    """Get cost breakdown by model."""
    try:
        days_back = request.args.get('days', 30, type=int)
        days_back = max(1, min(days_back, 90))  # Limit between 1 and 90 days
        
        breakdown = cost_optimization_service.analyze_cost_breakdown(days_back)
        
        breakdown_data = []
        for item in breakdown:
            breakdown_data.append({
                'model_name': item.model_name,
                'total_cost': round(item.total_cost, 4),
                'total_tokens': item.total_tokens,
                'average_cost_per_token': round(item.average_cost_per_token, 6),
                'total_requests': item.total_requests,
                'average_cost_per_request': round(item.average_cost_per_request, 4),
                'percentage_of_total': round(item.percentage_of_total, 1)
            })
        
        return jsonify({
            'success': True,
            'breakdown': breakdown_data,
            'period_days': days_back
        })
        
    except Exception as e:
        logger.error(f"Error getting cost breakdown: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'breakdown': []
        }), 500


@costs_bp.route('/api/optimization-recommendations')
@login_required
def get_optimization_recommendations():
    """Get cost optimization recommendations."""
    try:
        days_back = request.args.get('days', 30, type=int)
        days_back = max(1, min(days_back, 90))
        
        recommendations = cost_optimization_service.generate_cost_optimization_recommendations(days_back)
        
        recommendations_data = []
        for rec in recommendations:
            recommendations_data.append({
                'type': rec.recommendation_type,
                'title': rec.title,
                'description': rec.description,
                'potential_savings_percentage': round(rec.potential_savings_percentage, 1),
                'potential_savings_usd': round(rec.potential_savings_usd, 2),
                'implementation_difficulty': rec.implementation_difficulty,
                'timeframe': rec.timeframe,
                'action_items': rec.action_items,
                'confidence_score': round(rec.confidence_score, 2)
            })
        
        return jsonify({
            'success': True,
            'recommendations': recommendations_data,
            'total_recommendations': len(recommendations_data)
        })
        
    except Exception as e:
        logger.error(f"Error getting optimization recommendations: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'recommendations': []
        }), 500


@costs_bp.route('/api/cost-trends')
@login_required
def get_cost_trends():
    """Get cost trend analysis."""
    try:
        days_back = request.args.get('days', 30, type=int)
        days_back = max(7, min(days_back, 90))
        
        trends = cost_optimization_service.analyze_cost_trends(days_back)
        
        if trends:
            trends_data = {
                'period': trends.period,
                'cost_change_percentage': round(trends.cost_change_percentage, 2),
                'cost_change_usd': round(trends.cost_change_usd, 4),
                'trend_direction': trends.trend_direction,
                'projected_monthly_cost': round(trends.projected_monthly_cost, 2),
                'confidence_score': round(trends.confidence_score, 2)
            }
        else:
            trends_data = None
        
        return jsonify({
            'success': True,
            'trends': trends_data
        })
        
    except Exception as e:
        logger.error(f"Error getting cost trends: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'trends': None
        }), 500


@costs_bp.route('/api/monthly-prediction')
@login_required
def get_monthly_prediction():
    """Get monthly cost prediction."""
    try:
        confidence_level = request.args.get('confidence', 'medium')
        if confidence_level not in ['low', 'medium', 'high']:
            confidence_level = 'medium'
        
        prediction = cost_optimization_service.predict_monthly_cost(confidence_level)
        
        return jsonify({
            'success': True,
            'prediction': {
                'predicted_monthly_cost': round(prediction.get('predicted_monthly_cost', 0), 2),
                'confidence_score': round(prediction.get('confidence_score', 0), 2),
                'prediction_range': {
                    'min': round(prediction.get('prediction_range', {}).get('min', 0), 2),
                    'max': round(prediction.get('prediction_range', {}).get('max', 0), 2),
                    'most_likely': round(prediction.get('prediction_range', {}).get('most_likely', 0), 2)
                },
                'based_on_period': prediction.get('based_on_period', 'unknown'),
                'factors_considered': prediction.get('factors_considered', [])
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting monthly prediction: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'prediction': {}
        }), 500


@costs_bp.route('/api/efficiency-metrics')
@login_required
def get_efficiency_metrics():
    """Get cost efficiency metrics."""
    try:
        metrics = cost_optimization_service.get_cost_efficiency_metrics()
        
        # Round numerical values for display
        if metrics:
            for key, value in metrics.items():
                if isinstance(value, float):
                    metrics[key] = round(value, 4)
                elif isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, float):
                            metrics[key][sub_key] = round(sub_value, 4)
        
        return jsonify({
            'success': True,
            'metrics': metrics
        })
        
    except Exception as e:
        logger.error(f"Error getting efficiency metrics: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'metrics': {}
        }), 500


@costs_bp.route('/api/cost-summary')
@login_required
def get_cost_summary():
    """Get comprehensive cost summary."""
    try:
        # Get all cost data
        breakdown = cost_optimization_service.analyze_cost_breakdown(30)
        efficiency = cost_optimization_service.get_cost_efficiency_metrics()
        trends = cost_optimization_service.analyze_cost_trends(30)
        prediction = cost_optimization_service.predict_monthly_cost('medium')
        
        # Calculate summary metrics
        total_cost_30_days = sum(b.total_cost for b in breakdown) if breakdown else 0
        total_requests = sum(b.total_requests for b in breakdown) if breakdown else 0
        
        summary = {
            'total_cost_30_days': round(total_cost_30_days, 2),
            'average_daily_cost': round(total_cost_30_days / 30, 2),
            'total_requests_30_days': total_requests,
            'average_cost_per_request': round(total_cost_30_days / max(total_requests, 1), 4),
            'predicted_monthly_cost': round(prediction.get('predicted_monthly_cost', 0), 2),
            'efficiency_score': round(efficiency.get('efficiency_score', 0), 1),
            'trend_direction': trends.trend_direction if trends else 'stable',
            'cost_change_percentage': round(trends.cost_change_percentage, 1) if trends else 0,
            'top_cost_model': breakdown[0].model_name if breakdown else 'N/A',
            'model_count': len(breakdown)
        }
        
        return jsonify({
            'success': True,
            'summary': summary
        })
        
    except Exception as e:
        logger.error(f"Error getting cost summary: {e}")
        return jsonify({
            'success': False,
            'error': str(e),
            'summary': {}
        }), 500 