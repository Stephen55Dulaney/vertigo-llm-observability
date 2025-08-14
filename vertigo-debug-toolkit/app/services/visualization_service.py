"""
Advanced Visualization Service

Provides enhanced data visualization capabilities for the Vertigo Debug Toolkit
with real-time chart updates, interactive components, and advanced analytics displays.
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from app.services.langwatch_client import LangWatchClient
from app.services.performance_optimizer import performance_optimizer
from app.services.analytics_service import analytics_service
from app.services.cache_service import default_cache_service

logger = logging.getLogger(__name__)


@dataclass
class ChartConfig:
    """Chart configuration settings."""
    chart_type: str
    title: str
    x_axis_label: str = ""
    y_axis_label: str = ""
    colors: List[str] = None
    height: int = 300
    animation: bool = True
    responsive: bool = True
    legend_position: str = "top"
    show_data_labels: bool = False
    
    def __post_init__(self):
        if self.colors is None:
            self.colors = [
                "#4F46E5", "#10B981", "#F59E0B", "#EF4444",
                "#8B5CF6", "#06B6D4", "#84CC16", "#F97316"
            ]


@dataclass
class ChartData:
    """Structured chart data container."""
    labels: List[str]
    datasets: List[Dict[str, Any]]
    config: ChartConfig
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {
                "generated_at": datetime.now().isoformat(),
                "data_points": len(self.labels),
                "dataset_count": len(self.datasets)
            }


class VisualizationService:
    """Advanced visualization service for dashboard components."""
    
    def __init__(self):
        self.langwatch_client = LangWatchClient()
        self.chart_cache = {}
        self.cache_ttl = 300  # 5 minutes
        logger.info("VisualizationService initialized")
    
    def get_performance_timeline_chart(self, hours: int = 24) -> ChartData:
        """Generate performance metrics timeline chart."""
        try:
            # Generate time series data for performance metrics
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours)
            
            # Create hourly intervals
            intervals = []
            current_time = start_time
            while current_time <= end_time:
                intervals.append(current_time.strftime("%H:%M"))
                current_time += timedelta(hours=1)
            
            # Get performance metrics over time
            profile = performance_optimizer.collect_metrics()
            
            # Simulate historical data (in real implementation, fetch from database)
            cpu_data = [profile.cpu_usage_percent + (i % 5 - 2) for i in range(len(intervals))]
            memory_data = [profile.memory_usage_percent + (i % 3 - 1) for i in range(len(intervals))]
            cache_data = [profile.cache_hit_ratio * 100 + (i % 4 - 2) for i in range(len(intervals))]
            
            config = ChartConfig(
                chart_type="line",
                title="Performance Metrics Timeline",
                x_axis_label="Time",
                y_axis_label="Percentage (%)",
                height=400
            )
            
            datasets = [
                {
                    "label": "CPU Usage",
                    "data": cpu_data,
                    "borderColor": config.colors[0],
                    "backgroundColor": config.colors[0] + "20",
                    "tension": 0.4,
                    "fill": False
                },
                {
                    "label": "Memory Usage",
                    "data": memory_data,
                    "borderColor": config.colors[1],
                    "backgroundColor": config.colors[1] + "20",
                    "tension": 0.4,
                    "fill": False
                },
                {
                    "label": "Cache Hit Ratio",
                    "data": cache_data,
                    "borderColor": config.colors[2],
                    "backgroundColor": config.colors[2] + "20",
                    "tension": 0.4,
                    "fill": False
                }
            ]
            
            return ChartData(
                labels=intervals,
                datasets=datasets,
                config=config,
                metadata={"time_range_hours": hours}
            )
            
        except Exception as e:
            logger.error(f"Error generating performance timeline chart: {e}")
            return self._get_error_chart("Performance Timeline", str(e))
    
    def get_prompt_performance_heatmap(self) -> ChartData:
        """Generate heatmap of prompt performance across different metrics."""
        try:
            # Get prompt analytics data
            analytics = analytics_service.get_analytics_summary()
            
            # Create sample heatmap data for different prompts and metrics
            prompts = ["Email Processing", "Meeting Summary", "Status Generation", "Command Detection", "Error Handling"]
            metrics = ["Response Time", "Success Rate", "Token Usage", "Cost Efficiency", "User Rating"]
            
            # Generate heatmap data matrix
            data = []
            for i, prompt in enumerate(prompts):
                for j, metric in enumerate(metrics):
                    # Simulate performance score (0-100)
                    score = 85 + (i * j % 15) - 7
                    data.append([j, i, score])
            
            config = ChartConfig(
                chart_type="heatmap",
                title="Prompt Performance Heatmap",
                x_axis_label="Metrics",
                y_axis_label="Prompts",
                height=350
            )
            
            return ChartData(
                labels=metrics,
                datasets=[{
                    "label": "Performance Score",
                    "data": data,
                    "backgroundColor": self._get_heatmap_colors()
                }],
                config=config,
                metadata={
                    "prompts": prompts,
                    "metrics": metrics,
                    "score_range": [0, 100]
                }
            )
            
        except Exception as e:
            logger.error(f"Error generating prompt performance heatmap: {e}")
            return self._get_error_chart("Prompt Performance Heatmap", str(e))
    
    def get_cost_breakdown_donut(self, period: str = "7d") -> ChartData:
        """Generate donut chart for cost breakdown by service."""
        try:
            # Get cost data from analytics
            analytics = analytics_service.get_analytics_summary()
            
            # Sample cost breakdown data
            cost_data = {
                "Gemini API": 45.67,
                "Firestore": 12.34,
                "Cloud Functions": 8.90,
                "Gmail API": 3.45,
                "Langfuse Hosting": 15.20,
                "Other Services": 6.78
            }
            
            labels = list(cost_data.keys())
            data = list(cost_data.values())
            
            config = ChartConfig(
                chart_type="doughnut",
                title=f"Cost Breakdown - Last {period}",
                height=350,
                legend_position="right",
                show_data_labels=True
            )
            
            datasets = [{
                "label": "Cost ($)",
                "data": data,
                "backgroundColor": config.colors[:len(labels)],
                "borderWidth": 2,
                "borderColor": "#FFFFFF"
            }]
            
            return ChartData(
                labels=labels,
                datasets=datasets,
                config=config,
                metadata={
                    "total_cost": sum(data),
                    "period": period,
                    "currency": "USD"
                }
            )
            
        except Exception as e:
            logger.error(f"Error generating cost breakdown chart: {e}")
            return self._get_error_chart("Cost Breakdown", str(e))
    
    def get_real_time_metrics_gauge(self) -> Dict[str, ChartData]:
        """Generate gauge charts for real-time metrics."""
        try:
            gauges = {}
            
            # CPU Usage Gauge
            profile = performance_optimizer.collect_metrics()
            gauges["cpu"] = self._create_gauge_chart(
                "CPU Usage",
                profile.cpu_usage_percent,
                100,
                "#EF4444"
            )
            
            # Memory Usage Gauge
            gauges["memory"] = self._create_gauge_chart(
                "Memory Usage",
                profile.memory_usage_percent,
                100,
                "#F59E0B"
            )
            
            # Cache Hit Ratio Gauge
            gauges["cache"] = self._create_gauge_chart(
                "Cache Hit Ratio",
                profile.cache_hit_ratio * 100,
                100,
                "#10B981"
            )
            
            # Response Time Gauge
            avg_response_time = 245  # Sample value in ms
            gauges["response_time"] = self._create_gauge_chart(
                "Avg Response Time",
                avg_response_time,
                1000,
                "#8B5CF6",
                unit="ms"
            )
            
            return gauges
            
        except Exception as e:
            logger.error(f"Error generating gauge charts: {e}")
            return {"error": self._get_error_chart("Real-time Metrics", str(e))}
    
    def get_user_activity_bubble_chart(self) -> ChartData:
        """Generate bubble chart showing user activity patterns."""
        try:
            # Sample user activity data
            users = ["Admin", "Developer 1", "Developer 2", "Analyst 1", "Analyst 2"]
            
            # Generate bubble data: [x, y, r] where x=sessions, y=avg_duration, r=total_actions
            data = []
            for i, user in enumerate(users):
                sessions = 20 + (i * 15) + (i % 3 * 5)
                avg_duration = 25 + (i * 8) + (i % 4 * 3)
                total_actions = 150 + (i * 50) + (i % 5 * 20)
                
                data.append({
                    "x": sessions,
                    "y": avg_duration,
                    "r": total_actions / 10,  # Scale bubble size
                    "label": user
                })
            
            config = ChartConfig(
                chart_type="bubble",
                title="User Activity Patterns",
                x_axis_label="Sessions Count",
                y_axis_label="Avg Session Duration (min)",
                height=400
            )
            
            datasets = [{
                "label": "User Activity",
                "data": data,
                "backgroundColor": [color + "60" for color in config.colors[:len(users)]],
                "borderColor": config.colors[:len(users)],
                "borderWidth": 2
            }]
            
            return ChartData(
                labels=users,
                datasets=datasets,
                config=config,
                metadata={"total_users": len(users)}
            )
            
        except Exception as e:
            logger.error(f"Error generating user activity bubble chart: {e}")
            return self._get_error_chart("User Activity", str(e))
    
    def get_api_endpoint_performance_bar(self) -> ChartData:
        """Generate horizontal bar chart for API endpoint performance."""
        try:
            endpoints = [
                "/api/prompts/analyze",
                "/api/costs/summary",
                "/api/performance/metrics",
                "/ws/api/broadcast",
                "/api/sync/firestore",
                "/api/analytics/summary"
            ]
            
            # Sample response times in milliseconds
            response_times = [320, 180, 95, 45, 890, 150]
            
            config = ChartConfig(
                chart_type="horizontalBar",
                title="API Endpoint Response Times",
                x_axis_label="Response Time (ms)",
                y_axis_label="Endpoints",
                height=300
            )
            
            # Color code based on performance (green=fast, yellow=medium, red=slow)
            colors = []
            for time in response_times:
                if time < 100:
                    colors.append("#10B981")  # Green
                elif time < 300:
                    colors.append("#F59E0B")  # Yellow
                else:
                    colors.append("#EF4444")  # Red
            
            datasets = [{
                "label": "Response Time (ms)",
                "data": response_times,
                "backgroundColor": colors,
                "borderWidth": 1,
                "borderColor": "#E5E7EB"
            }]
            
            return ChartData(
                labels=endpoints,
                datasets=datasets,
                config=config,
                metadata={"total_endpoints": len(endpoints)}
            )
            
        except Exception as e:
            logger.error(f"Error generating API performance bar chart: {e}")
            return self._get_error_chart("API Performance", str(e))
    
    def get_error_distribution_radar(self) -> ChartData:
        """Generate radar chart showing error distribution across different categories."""
        try:
            categories = [
                "Authentication",
                "API Rate Limits",
                "Database Errors",
                "Network Timeouts",
                "Validation Errors",
                "Permission Denied"
            ]
            
            # Sample error counts for different time periods
            current_week = [5, 12, 3, 8, 15, 2]
            previous_week = [8, 18, 7, 12, 20, 5]
            
            config = ChartConfig(
                chart_type="radar",
                title="Error Distribution Comparison",
                height=400
            )
            
            datasets = [
                {
                    "label": "Current Week",
                    "data": current_week,
                    "borderColor": config.colors[0],
                    "backgroundColor": config.colors[0] + "30",
                    "pointBackgroundColor": config.colors[0],
                    "pointBorderColor": "#FFFFFF",
                    "pointHoverBackgroundColor": "#FFFFFF",
                    "pointHoverBorderColor": config.colors[0]
                },
                {
                    "label": "Previous Week",
                    "data": previous_week,
                    "borderColor": config.colors[1],
                    "backgroundColor": config.colors[1] + "30",
                    "pointBackgroundColor": config.colors[1],
                    "pointBorderColor": "#FFFFFF",
                    "pointHoverBackgroundColor": "#FFFFFF",
                    "pointHoverBorderColor": config.colors[1]
                }
            ]
            
            return ChartData(
                labels=categories,
                datasets=datasets,
                config=config,
                metadata={
                    "total_current": sum(current_week),
                    "total_previous": sum(previous_week)
                }
            )
            
        except Exception as e:
            logger.error(f"Error generating error distribution radar: {e}")
            return self._get_error_chart("Error Distribution", str(e))
    
    def _create_gauge_chart(self, title: str, value: float, max_value: float, 
                           color: str, unit: str = "%") -> ChartData:
        """Create a gauge chart configuration."""
        config = ChartConfig(
            chart_type="gauge",
            title=f"{title}: {value:.1f}{unit}",
            height=200
        )
        
        datasets = [{
            "data": [value, max_value - value],
            "backgroundColor": [color, "#E5E7EB"],
            "borderWidth": 0,
            "cutout": "80%"
        }]
        
        return ChartData(
            labels=[title, ""],
            datasets=datasets,
            config=config,
            metadata={
                "current_value": value,
                "max_value": max_value,
                "unit": unit,
                "percentage": (value / max_value) * 100
            }
        )
    
    def _get_heatmap_colors(self) -> List[str]:
        """Generate color gradient for heatmap."""
        return [
            "#FEF3C7", "#FDE68A", "#FCD34D", "#FBBF24", "#F59E0B",
            "#D97706", "#B45309", "#92400E", "#78350F", "#451A03"
        ]
    
    def _get_error_chart(self, chart_name: str, error_message: str) -> ChartData:
        """Generate error chart when visualization fails."""
        config = ChartConfig(
            chart_type="bar",
            title=f"Error: {chart_name}",
            height=200
        )
        
        return ChartData(
            labels=["Error"],
            datasets=[{
                "label": "Error",
                "data": [1],
                "backgroundColor": "#EF4444"
            }],
            config=config,
            metadata={"error": error_message}
        )
    
    def get_dashboard_layout_config(self) -> Dict[str, Any]:
        """Get responsive dashboard layout configuration."""
        return {
            "grid": {
                "columns": 12,
                "row_height": 60,
                "margin": [10, 10],
                "container_padding": [20, 20]
            },
            "components": [
                {
                    "name": "performance_timeline",
                    "title": "Performance Timeline",
                    "type": "line_chart",
                    "layout": {"x": 0, "y": 0, "w": 8, "h": 6},
                    "refresh_interval": 30
                },
                {
                    "name": "cpu_gauge",
                    "title": "CPU Usage",
                    "type": "gauge",
                    "layout": {"x": 8, "y": 0, "w": 2, "h": 3},
                    "refresh_interval": 5
                },
                {
                    "name": "memory_gauge",
                    "title": "Memory Usage",
                    "type": "gauge",
                    "layout": {"x": 10, "y": 0, "w": 2, "h": 3},
                    "refresh_interval": 5
                },
                {
                    "name": "cost_breakdown",
                    "title": "Cost Breakdown",
                    "type": "donut_chart",
                    "layout": {"x": 8, "y": 3, "w": 4, "h": 5},
                    "refresh_interval": 300
                },
                {
                    "name": "api_performance",
                    "title": "API Performance",
                    "type": "bar_chart",
                    "layout": {"x": 0, "y": 6, "w": 6, "h": 4},
                    "refresh_interval": 60
                },
                {
                    "name": "error_radar",
                    "title": "Error Distribution",
                    "type": "radar_chart",
                    "layout": {"x": 6, "y": 6, "w": 6, "h": 4},
                    "refresh_interval": 120
                },
                {
                    "name": "user_activity",
                    "title": "User Activity",
                    "type": "bubble_chart",
                    "layout": {"x": 0, "y": 10, "w": 8, "h": 5},
                    "refresh_interval": 180
                },
                {
                    "name": "prompt_heatmap",
                    "title": "Prompt Performance",
                    "type": "heatmap",
                    "layout": {"x": 8, "y": 8, "w": 4, "h": 7},
                    "refresh_interval": 240
                }
            ],
            "responsive_breakpoints": {
                "lg": 1200,
                "md": 996,
                "sm": 768,
                "xs": 480
            }
        }


# Global visualization service instance
visualization_service = VisualizationService()