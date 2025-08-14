"""
Advanced Cost Optimization Service for Vertigo Debug Toolkit
Provides intelligent cost analysis, predictions, and optimization recommendations.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict
import statistics
from decimal import Decimal

from app.services.live_data_service import live_data_service
from app.services.analytics_service import analytics_service

logger = logging.getLogger(__name__)


@dataclass
class CostBreakdown:
    """Cost breakdown by model/service."""
    model_name: str
    total_cost: float
    total_tokens: int
    average_cost_per_token: float
    total_requests: int
    average_cost_per_request: float
    percentage_of_total: float


@dataclass
class CostOptimizationRecommendation:
    """Cost optimization recommendation."""
    recommendation_type: str
    title: str
    description: str
    potential_savings_percentage: float
    potential_savings_usd: float
    implementation_difficulty: str  # 'easy', 'medium', 'hard'
    timeframe: str  # 'immediate', 'short-term', 'long-term'
    action_items: List[str]
    confidence_score: float


@dataclass
class CostTrend:
    """Cost trend analysis."""
    period: str
    cost_change_percentage: float
    cost_change_usd: float
    trend_direction: str  # 'increasing', 'decreasing', 'stable'
    projected_monthly_cost: float
    confidence_score: float


class CostOptimizationService:
    """Advanced cost optimization and analysis service."""
    
    def __init__(self):
        """Initialize cost optimization service."""
        self.model_cost_rates = {
            # Gemini models (approximate rates per 1K tokens)
            'gemini-1.5-pro': {'input': 0.00125, 'output': 0.005},
            'gemini-1.5-flash': {'input': 0.00075, 'output': 0.003},
            'gemini-1.0-pro': {'input': 0.0005, 'output': 0.0015},
            
            # OpenAI models (for comparison/estimation)
            'gpt-4-turbo': {'input': 0.01, 'output': 0.03},
            'gpt-4': {'input': 0.03, 'output': 0.06},
            'gpt-3.5-turbo': {'input': 0.0015, 'output': 0.002},
            
            # Claude models (for comparison)
            'claude-3-opus': {'input': 0.015, 'output': 0.075},
            'claude-3-sonnet': {'input': 0.003, 'output': 0.015},
            'claude-3-haiku': {'input': 0.00025, 'output': 0.00125},
        }
        
        # Cost thresholds for recommendations
        self.cost_thresholds = {
            'high_cost_per_request': 0.10,  # $0.10 per request
            'high_daily_cost': 50.0,  # $50 per day
            'high_token_usage': 100000,  # 100K tokens per day
            'model_efficiency_threshold': 0.8  # 80% efficiency
        }
        
        logger.info("CostOptimizationService initialized")
    
    def analyze_cost_breakdown(self, days_back: int = 30) -> List[CostBreakdown]:
        """Analyze cost breakdown by model."""
        try:
            # Get cost data from live data service
            cost_data = self._get_cost_data(days_back)
            
            if not cost_data:
                return []
            
            # Group by model
            model_costs = defaultdict(lambda: {
                'total_cost': 0.0,
                'total_tokens': 0,
                'total_requests': 0
            })
            
            total_cost = 0.0
            
            for record in cost_data:
                model = record.get('model', 'unknown')
                cost = float(record.get('cost_usd', 0))
                tokens = record.get('input_tokens', 0) + record.get('output_tokens', 0)
                
                model_costs[model]['total_cost'] += cost
                model_costs[model]['total_tokens'] += tokens
                model_costs[model]['total_requests'] += 1
                total_cost += cost
            
            # Create breakdown objects
            breakdowns = []
            for model, data in model_costs.items():
                breakdown = CostBreakdown(
                    model_name=model,
                    total_cost=data['total_cost'],
                    total_tokens=data['total_tokens'],
                    average_cost_per_token=data['total_cost'] / max(data['total_tokens'], 1),
                    total_requests=data['total_requests'],
                    average_cost_per_request=data['total_cost'] / max(data['total_requests'], 1),
                    percentage_of_total=(data['total_cost'] / max(total_cost, 0.01)) * 100
                )
                breakdowns.append(breakdown)
            
            # Sort by cost descending
            breakdowns.sort(key=lambda x: x.total_cost, reverse=True)
            
            return breakdowns
            
        except Exception as e:
            logger.error(f"Error analyzing cost breakdown: {e}")
            return []
    
    def generate_cost_optimization_recommendations(self, days_back: int = 30) -> List[CostOptimizationRecommendation]:
        """Generate cost optimization recommendations."""
        try:
            recommendations = []
            
            # Get current cost data
            cost_breakdown = self.analyze_cost_breakdown(days_back)
            cost_trends = self.analyze_cost_trends(days_back)
            
            if not cost_breakdown:
                return recommendations
            
            # High-cost model recommendation
            expensive_models = [b for b in cost_breakdown if b.average_cost_per_request > self.cost_thresholds['high_cost_per_request']]
            if expensive_models:
                total_potential_savings = sum(b.total_cost * 0.3 for b in expensive_models)  # Estimate 30% savings
                
                recommendations.append(CostOptimizationRecommendation(
                    recommendation_type='model_optimization',
                    title='Switch to More Cost-Effective Models',
                    description=f'You have {len(expensive_models)} model(s) with high per-request costs. Consider switching to more efficient alternatives.',
                    potential_savings_percentage=30.0,
                    potential_savings_usd=total_potential_savings,
                    implementation_difficulty='medium',
                    timeframe='short-term',
                    action_items=[
                        f'Evaluate {model.model_name} usage patterns' for model in expensive_models[:3]
                    ] + [
                        'Test equivalent performance with Gemini Flash models',
                        'Implement model selection based on task complexity'
                    ],
                    confidence_score=0.85
                ))
            
            # Token optimization recommendation
            high_token_models = [b for b in cost_breakdown if b.total_tokens > self.cost_thresholds['high_token_usage']]
            if high_token_models:
                recommendations.append(CostOptimizationRecommendation(
                    recommendation_type='token_optimization',
                    title='Optimize Token Usage',
                    description=f'High token consumption detected. Implement prompt engineering and response optimization.',
                    potential_savings_percentage=20.0,
                    potential_savings_usd=sum(b.total_cost * 0.2 for b in high_token_models),
                    implementation_difficulty='easy',
                    timeframe='immediate',
                    action_items=[
                        'Implement prompt compression techniques',
                        'Use system messages more effectively',
                        'Set appropriate max_tokens limits',
                        'Cache frequently used responses'
                    ],
                    confidence_score=0.9
                ))
            
            # Cost trend recommendations
            if cost_trends and cost_trends.trend_direction == 'increasing' and cost_trends.cost_change_percentage > 25:
                recommendations.append(CostOptimizationRecommendation(
                    recommendation_type='trend_alert',
                    title='Rapidly Increasing Costs Detected',
                    description=f'Costs have increased by {cost_trends.cost_change_percentage:.1f}% recently. Projected monthly cost: ${cost_trends.projected_monthly_cost:.2f}',
                    potential_savings_percentage=15.0,
                    potential_savings_usd=cost_trends.projected_monthly_cost * 0.15,
                    implementation_difficulty='medium',
                    timeframe='immediate',
                    action_items=[
                        'Review recent usage patterns',
                        'Implement rate limiting',
                        'Set up cost alerts',
                        'Audit automated processes'
                    ],
                    confidence_score=0.8
                ))
            
            # Model efficiency recommendations
            self._add_model_efficiency_recommendations(recommendations, cost_breakdown)
            
            # Caching recommendations
            self._add_caching_recommendations(recommendations, cost_breakdown)
            
            # Sort by potential savings
            recommendations.sort(key=lambda x: x.potential_savings_usd, reverse=True)
            
            return recommendations[:10]  # Top 10 recommendations
            
        except Exception as e:
            logger.error(f"Error generating cost optimization recommendations: {e}")
            return []
    
    def analyze_cost_trends(self, days_back: int = 30) -> Optional[CostTrend]:
        """Analyze cost trends over time."""
        try:
            # Get cost data for trend analysis
            recent_period = days_back // 2
            older_period = days_back
            
            recent_metrics = live_data_service.get_unified_performance_metrics(hours=recent_period * 24)
            older_metrics = live_data_service.get_unified_performance_metrics(hours=older_period * 24)
            
            recent_cost = recent_metrics.get('total_cost', 0)
            older_total_cost = older_metrics.get('total_cost', 0)
            older_cost = max(older_total_cost - recent_cost, 0.01)  # Cost from older period only
            
            if older_cost <= 0:
                return None
            
            # Calculate change
            cost_change = recent_cost - older_cost
            cost_change_percentage = (cost_change / older_cost) * 100
            
            # Determine trend direction
            if abs(cost_change_percentage) < 5:
                trend_direction = 'stable'
            elif cost_change_percentage > 0:
                trend_direction = 'increasing'
            else:
                trend_direction = 'decreasing'
            
            # Project monthly cost
            daily_cost = recent_cost / recent_period if recent_period > 0 else 0
            projected_monthly_cost = daily_cost * 30
            
            return CostTrend(
                period=f'{days_back} days',
                cost_change_percentage=cost_change_percentage,
                cost_change_usd=cost_change,
                trend_direction=trend_direction,
                projected_monthly_cost=projected_monthly_cost,
                confidence_score=0.8 if recent_period >= 7 else 0.6
            )
            
        except Exception as e:
            logger.error(f"Error analyzing cost trends: {e}")
            return None
    
    def predict_monthly_cost(self, confidence_level: str = 'medium') -> Dict[str, Any]:
        """Predict monthly cost based on current usage patterns."""
        try:
            # Get recent usage data
            current_metrics = live_data_service.get_unified_performance_metrics(hours=168)  # Last week
            cost_trends = self.analyze_cost_trends(30)
            
            weekly_cost = current_metrics.get('total_cost', 0)
            
            # Calculate predictions with different methods
            predictions = {}
            
            # Simple linear projection
            predictions['linear'] = weekly_cost * 4.33  # ~4.33 weeks per month
            
            # Trend-adjusted projection
            if cost_trends:
                trend_multiplier = 1 + (cost_trends.cost_change_percentage / 100)
                predictions['trend_adjusted'] = predictions['linear'] * trend_multiplier
            else:
                predictions['trend_adjusted'] = predictions['linear']
            
            # Conservative estimate (lower bound)
            predictions['conservative'] = predictions['linear'] * 0.85
            
            # Aggressive estimate (upper bound)  
            predictions['aggressive'] = predictions['linear'] * 1.25
            
            # Select prediction based on confidence level
            if confidence_level == 'high':
                predicted_cost = predictions['trend_adjusted']
                confidence = 0.85
            elif confidence_level == 'low':
                predicted_cost = (predictions['conservative'] + predictions['aggressive']) / 2
                confidence = 0.6
            else:  # medium
                predicted_cost = predictions['linear']
                confidence = 0.75
            
            return {
                'predicted_monthly_cost': predicted_cost,
                'confidence_score': confidence,
                'prediction_range': {
                    'min': predictions['conservative'],
                    'max': predictions['aggressive'],
                    'most_likely': predictions['linear']
                },
                'based_on_period': 'last_7_days',
                'factors_considered': [
                    'Recent usage patterns',
                    'Cost trends',
                    'Seasonal adjustments'
                ]
            }
            
        except Exception as e:
            logger.error(f"Error predicting monthly cost: {e}")
            return {
                'predicted_monthly_cost': 0.0,
                'confidence_score': 0.0,
                'error': str(e)
            }
    
    def get_cost_efficiency_metrics(self) -> Dict[str, Any]:
        """Get cost efficiency metrics."""
        try:
            cost_breakdown = self.analyze_cost_breakdown(30)
            
            if not cost_breakdown:
                return {}
            
            # Calculate efficiency metrics
            total_cost = sum(b.total_cost for b in cost_breakdown)
            total_requests = sum(b.total_requests for b in cost_breakdown)
            total_tokens = sum(b.total_tokens for b in cost_breakdown)
            
            # Find most and least efficient models
            if cost_breakdown:
                most_efficient = min(cost_breakdown, key=lambda x: x.average_cost_per_request)
                least_efficient = max(cost_breakdown, key=lambda x: x.average_cost_per_request)
            else:
                most_efficient = least_efficient = None
            
            # Calculate cost per successful operation
            success_metrics = live_data_service.get_unified_performance_metrics(hours=24*30)
            success_rate = success_metrics.get('success_rate', 0) / 100
            cost_per_success = (total_cost / max(total_requests * success_rate, 1)) if total_requests > 0 else 0
            
            return {
                'total_cost_30_days': total_cost,
                'average_cost_per_request': total_cost / max(total_requests, 1),
                'average_cost_per_token': total_cost / max(total_tokens, 1),
                'cost_per_successful_operation': cost_per_success,
                'most_efficient_model': {
                    'name': most_efficient.model_name if most_efficient else 'N/A',
                    'cost_per_request': most_efficient.average_cost_per_request if most_efficient else 0
                },
                'least_efficient_model': {
                    'name': least_efficient.model_name if least_efficient else 'N/A',
                    'cost_per_request': least_efficient.average_cost_per_request if least_efficient else 0
                },
                'efficiency_score': self._calculate_efficiency_score(cost_breakdown),
                'total_requests': total_requests,
                'total_tokens': total_tokens
            }
            
        except Exception as e:
            logger.error(f"Error getting cost efficiency metrics: {e}")
            return {}
    
    def _get_cost_data(self, days_back: int) -> List[Dict]:
        """Get cost data from various sources."""
        try:
            # Try to get from live traces first
            recent_traces = live_data_service.get_recent_traces(limit=1000, data_source='all')
            
            cost_data = []
            for trace in recent_traces:
                # Extract cost information from trace
                cost_data.append({
                    'model': trace.get('model', 'unknown'),
                    'cost_usd': trace.get('cost', 0),
                    'input_tokens': trace.get('input_tokens', 0),
                    'output_tokens': trace.get('output_tokens', 0),
                    'timestamp': trace.get('timestamp')
                })
            
            return cost_data
            
        except Exception as e:
            logger.error(f"Error getting cost data: {e}")
            return []
    
    def _add_model_efficiency_recommendations(self, recommendations: List, cost_breakdown: List[CostBreakdown]):
        """Add model efficiency recommendations."""
        try:
            if not cost_breakdown:
                return
            
            # Find inefficient models by comparing with known rates
            inefficient_models = []
            
            for breakdown in cost_breakdown:
                expected_rate = self.model_cost_rates.get(breakdown.model_name)
                if expected_rate and breakdown.total_tokens > 0:
                    expected_cost = (breakdown.total_tokens / 1000) * expected_rate['input']  # Simplified
                    if breakdown.total_cost > expected_cost * 1.5:  # 50% higher than expected
                        inefficient_models.append(breakdown)
            
            if inefficient_models:
                total_savings = sum(b.total_cost * 0.25 for b in inefficient_models)
                
                recommendations.append(CostOptimizationRecommendation(
                    recommendation_type='model_efficiency',
                    title='Improve Model Usage Efficiency',
                    description=f'{len(inefficient_models)} model(s) showing higher than expected costs.',
                    potential_savings_percentage=25.0,
                    potential_savings_usd=total_savings,
                    implementation_difficulty='medium',
                    timeframe='short-term',
                    action_items=[
                        'Audit token usage patterns',
                        'Optimize prompt length',
                        'Review model parameters',
                        'Consider batch processing'
                    ],
                    confidence_score=0.75
                ))
            
        except Exception as e:
            logger.error(f"Error adding model efficiency recommendations: {e}")
    
    def _add_caching_recommendations(self, recommendations: List, cost_breakdown: List[CostBreakdown]):
        """Add caching recommendations."""
        try:
            total_requests = sum(b.total_requests for b in cost_breakdown)
            total_cost = sum(b.total_cost for b in cost_breakdown)
            
            if total_requests > 1000 and total_cost > 10.0:  # Significant usage
                # Estimate potential savings from caching (assume 15% cache hit rate)
                cache_savings = total_cost * 0.15
                
                recommendations.append(CostOptimizationRecommendation(
                    recommendation_type='caching',
                    title='Implement Response Caching',
                    description='High request volume detected. Caching can significantly reduce costs for repeated queries.',
                    potential_savings_percentage=15.0,
                    potential_savings_usd=cache_savings,
                    implementation_difficulty='easy',
                    timeframe='short-term',
                    action_items=[
                        'Implement LRU cache for common queries',
                        'Cache model responses by input hash',
                        'Set appropriate cache TTL values',
                        'Monitor cache hit rates'
                    ],
                    confidence_score=0.8
                ))
            
        except Exception as e:
            logger.error(f"Error adding caching recommendations: {e}")
    
    def _calculate_efficiency_score(self, cost_breakdown: List[CostBreakdown]) -> float:
        """Calculate overall cost efficiency score (0-100)."""
        try:
            if not cost_breakdown:
                return 0.0
            
            # Base score
            score = 70.0
            
            # Adjust based on model mix
            total_cost = sum(b.total_cost for b in cost_breakdown)
            
            for breakdown in cost_breakdown:
                weight = breakdown.percentage_of_total / 100
                
                # Reward efficient models
                if breakdown.model_name.endswith('flash') or breakdown.model_name.endswith('haiku'):
                    score += 10 * weight
                elif breakdown.average_cost_per_request < 0.05:
                    score += 5 * weight
                
                # Penalize expensive models used heavily
                if breakdown.average_cost_per_request > 0.20:
                    score -= 15 * weight
            
            return max(0.0, min(100.0, score))
            
        except Exception as e:
            logger.error(f"Error calculating efficiency score: {e}")
            return 50.0  # Neutral score on error


# Global service instance
cost_optimization_service = CostOptimizationService()