"""
Performance routes for the Vertigo Debug Toolkit.
"""

from flask import render_template, jsonify, request
from flask_login import login_required
from app.blueprints.performance import performance_bp
from app.services.langwatch_client import langwatch_client
from app.services.live_data_service import live_data_service
from app.services.performance_optimizer import performance_optimizer
from app.services.cache_service import default_cache_service
import logging

logger = logging.getLogger(__name__)

@performance_bp.route('/')
@login_required
def index():
    """Performance monitoring page."""
    return render_template('performance/index.html')

@performance_bp.route('/api/metrics')
@login_required
def get_metrics():
    """Get unified performance metrics from all available sources."""
    try:
        hours = request.args.get('hours', 24, type=int)
        hours = max(1, min(hours, 168))  # Limit between 1 hour and 1 week
        data_source = request.args.get('source', 'all')  # 'all', 'database', 'langwatch', 'firestore'
        
        metrics = live_data_service.get_unified_performance_metrics(hours=hours, data_source=data_source)
        
        return jsonify({
            "success": True,
            "metrics": metrics,
            "data_source": data_source
        })
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "metrics": {}
        }), 500

@performance_bp.route('/api/latency-series')
@login_required
def get_latency_series():
    """Get latency time series data for charts."""
    try:
        hours = request.args.get('hours', 24, type=int)
        hours = max(1, min(hours, 168))
        data_source = request.args.get('source', 'all')
        
        latency_data = live_data_service.get_latency_time_series(hours=hours, data_source=data_source)
        
        return jsonify({
            "success": True,
            "data": latency_data,
            "data_source": data_source
        })
        
    except Exception as e:
        logger.error(f"Error getting latency series: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "data": []
        }), 500

@performance_bp.route('/api/error-rates')
@login_required
def get_error_rates():
    """Get error rate metrics."""
    try:
        hours = request.args.get('hours', 24, type=int)
        hours = max(1, min(hours, 168))
        
        error_data = langwatch_client.get_error_rate_metrics(hours=hours)
        
        return jsonify({
            "success": True,
            "data": error_data,
            "source": "langwatch"
        })
        
    except Exception as e:
        logger.error(f"Error getting error rates: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "data": {}
        }), 500

@performance_bp.route('/api/recent-traces')
@login_required
def get_recent_traces():
    """Get recent traces for display."""
    try:
        limit = request.args.get('limit', 10, type=int)
        limit = max(1, min(limit, 50))  # Limit between 1 and 50
        data_source = request.args.get('source', 'all')
        
        traces = live_data_service.get_recent_traces(limit=limit, data_source=data_source)
        
        return jsonify({
            "success": True,
            "traces": traces,
            "data_source": data_source
        })
        
    except Exception as e:
        logger.error(f"Error getting recent traces: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "traces": []
        }), 500

@performance_bp.route('/api/data-sources')
@login_required
def get_data_sources():
    """Get status of all data sources."""
    try:
        status = live_data_service.get_data_source_status()
        
        return jsonify({
            "success": True,
            "status": status
        })
        
    except Exception as e:
        logger.error(f"Error getting data source status: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "status": {}
        }), 500

@performance_bp.route('/api/performance-summary')
@login_required
def get_performance_summary():
    """Get comprehensive performance summary."""
    try:
        summary = performance_optimizer.get_performance_summary()
        return jsonify({
            "success": True,
            "summary": summary
        })
        
    except Exception as e:
        logger.error(f"Error getting performance summary: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@performance_bp.route('/api/optimize', methods=['POST'])
@login_required
def optimize_performance():
    """Run performance optimization."""
    try:
        results = performance_optimizer.auto_optimize()
        return jsonify({
            "success": True,
            "results": results
        })
        
    except Exception as e:
        logger.error(f"Error running optimization: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@performance_bp.route('/api/recommendations')
@login_required
def get_recommendations():
    """Get performance recommendations."""
    try:
        recommendations = performance_optimizer.generate_recommendations()
        
        return jsonify({
            "success": True,
            "recommendations": [{
                'strategy': r.strategy.value,
                'title': r.title,
                'description': r.description,
                'impact': r.impact,
                'effort': r.effort,
                'priority': r.priority,
                'auto_applicable': r.auto_applicable,
                'estimated_improvement': r.estimated_improvement
            } for r in recommendations]
        })
        
    except Exception as e:
        logger.error(f"Error getting recommendations: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# Import cache routes
from app.blueprints.performance import cache_routes