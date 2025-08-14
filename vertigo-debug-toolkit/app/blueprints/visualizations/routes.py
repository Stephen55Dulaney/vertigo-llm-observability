"""
Visualization routes for advanced dashboard components.
"""

from flask import render_template, jsonify, request
from flask_login import login_required
from datetime import datetime
from app.blueprints.visualizations import visualizations_bp
from app.services.visualization_service import visualization_service
from app.services.websocket_service import get_websocket_service, MessageType
import logging

logger = logging.getLogger(__name__)


@visualizations_bp.route('/')
@login_required
def visualization_dashboard():
    """Advanced visualization dashboard."""
    try:
        layout_config = visualization_service.get_dashboard_layout_config()
        return render_template('visualizations/dashboard.html', layout=layout_config)
    except Exception as e:
        logger.error(f"Error loading visualization dashboard: {e}")
        return render_template('error.html', error="Failed to load visualization dashboard"), 500


@visualizations_bp.route('/api/chart/<chart_type>')
@login_required
def get_chart_data(chart_type):
    """Get chart data for specific visualization type."""
    try:
        chart_data = None
        
        if chart_type == 'performance_timeline':
            hours = request.args.get('hours', 24, type=int)
            chart_data = visualization_service.get_performance_timeline_chart(hours)
            
        elif chart_type == 'prompt_heatmap':
            chart_data = visualization_service.get_prompt_performance_heatmap()
            
        elif chart_type == 'cost_breakdown':
            period = request.args.get('period', '7d')
            chart_data = visualization_service.get_cost_breakdown_donut(period)
            
        elif chart_type == 'realtime_gauges':
            gauge_data = visualization_service.get_real_time_metrics_gauge()
            return jsonify({
                "success": True,
                "data": {
                    gauge_name: {
                        "labels": gauge.labels,
                        "datasets": gauge.datasets,
                        "config": gauge.config.__dict__,
                        "metadata": gauge.metadata
                    } for gauge_name, gauge in gauge_data.items()
                }
            })
            
        elif chart_type == 'user_activity':
            chart_data = visualization_service.get_user_activity_bubble_chart()
            
        elif chart_type == 'api_performance':
            chart_data = visualization_service.get_api_endpoint_performance_bar()
            
        elif chart_type == 'error_distribution':
            chart_data = visualization_service.get_error_distribution_radar()
            
        else:
            return jsonify({
                "success": False,
                "error": f"Unknown chart type: {chart_type}"
            }), 400
        
        if chart_data is None:
            return jsonify({
                "success": False,
                "error": "Failed to generate chart data"
            }), 500
        
        # Send real-time update via WebSocket if available
        ws_service = get_websocket_service()
        if ws_service:
            try:
                ws_service.send_visualization_update(chart_type, {
                    "labels": chart_data.labels,
                    "datasets": chart_data.datasets,
                    "config": chart_data.config.__dict__,
                    "metadata": chart_data.metadata
                })
            except Exception as ws_error:
                logger.warning(f"Failed to send WebSocket update: {ws_error}")
        
        return jsonify({
            "success": True,
            "data": {
                "labels": chart_data.labels,
                "datasets": chart_data.datasets,
                "config": chart_data.config.__dict__,
                "metadata": chart_data.metadata
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting chart data for {chart_type}: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@visualizations_bp.route('/api/layout')
@login_required  
def get_dashboard_layout():
    """Get dashboard layout configuration."""
    try:
        layout = visualization_service.get_dashboard_layout_config()
        return jsonify({
            "success": True,
            "layout": layout
        })
    except Exception as e:
        logger.error(f"Error getting dashboard layout: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@visualizations_bp.route('/api/refresh-all', methods=['POST'])
@login_required
def refresh_all_visualizations():
    """Refresh all visualization components."""
    try:
        refreshed_charts = []
        chart_types = [
            'performance_timeline',
            'prompt_heatmap', 
            'cost_breakdown',
            'realtime_gauges',
            'user_activity',
            'api_performance',
            'error_distribution'
        ]
        
        for chart_type in chart_types:
            try:
                # This will trigger data refresh and WebSocket updates
                response = get_chart_data(chart_type)
                if response.status_code == 200:
                    refreshed_charts.append(chart_type)
            except Exception as chart_error:
                logger.warning(f"Failed to refresh {chart_type}: {chart_error}")
        
        return jsonify({
            "success": True,
            "message": f"Refreshed {len(refreshed_charts)} visualizations",
            "refreshed_charts": refreshed_charts
        })
        
    except Exception as e:
        logger.error(f"Error refreshing all visualizations: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@visualizations_bp.route('/interactive')
@login_required
def interactive_playground():
    """Interactive visualization playground."""
    try:
        return render_template('visualizations/interactive.html')
    except Exception as e:
        logger.error(f"Error loading interactive playground: {e}")
        return render_template('error.html', error="Failed to load interactive playground"), 500


@visualizations_bp.route('/api/custom-chart', methods=['POST'])
@login_required
def create_custom_chart():
    """Create custom visualization from user-defined parameters."""
    try:
        data = request.get_json()
        
        if not data or 'chart_config' not in data:
            return jsonify({
                "success": False,
                "error": "Chart configuration is required"
            }), 400
        
        chart_config = data['chart_config']
        chart_type = chart_config.get('type', 'line')
        title = chart_config.get('title', 'Custom Chart')
        
        # For now, return sample data based on chart type
        # In real implementation, this would process user data
        if chart_type == 'line':
            chart_data = visualization_service.get_performance_timeline_chart()
        elif chart_type == 'bar':
            chart_data = visualization_service.get_api_endpoint_performance_bar()
        elif chart_type == 'pie':
            chart_data = visualization_service.get_cost_breakdown_donut()
        else:
            chart_data = visualization_service.get_performance_timeline_chart()
        
        # Update title if provided
        chart_data.config.title = title
        
        return jsonify({
            "success": True,
            "data": {
                "labels": chart_data.labels,
                "datasets": chart_data.datasets,
                "config": chart_data.config.__dict__,
                "metadata": chart_data.metadata
            }
        })
        
    except Exception as e:
        logger.error(f"Error creating custom chart: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500