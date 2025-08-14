"""
ML-Based Prompt Performance Analyzer
Analyzes prompt performance patterns using statistical methods and machine learning techniques.
"""

import os
import logging
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict
import statistics
import json
from scipy import stats

from app.services.live_data_service import live_data_service
from app.models import db
from sqlalchemy import text, func

logger = logging.getLogger(__name__)


@dataclass
class PerformancePattern:
    """Detected performance pattern."""
    pattern_type: str
    prompt_id: Optional[str]
    pattern_description: str
    frequency: int
    avg_latency: float
    avg_cost: float
    success_rate: float
    confidence_score: float
    samples: List[Dict[str, Any]]


@dataclass
class PromptAnalytics:
    """Analytics for a specific prompt."""
    prompt_id: str
    prompt_text: str
    total_executions: int
    avg_latency_ms: float
    avg_cost_usd: float
    success_rate: float
    error_rate: float
    p95_latency_ms: float
    cost_per_success: float
    quality_score: float
    optimization_potential: float
    performance_trends: Dict[str, float]


@dataclass 
class ModelPerformanceComparison:
    """Model performance comparison."""
    model_name: str
    avg_latency: float
    avg_cost: float
    success_rate: float
    cost_efficiency_score: float
    latency_efficiency_score: float
    overall_score: float


class PromptPerformanceAnalyzer:
    """
    ML-based prompt performance analyzer.
    
    Analyzes prompt execution patterns, identifies optimization opportunities,
    and provides statistical insights for performance improvement.
    """
    
    def __init__(self):
        """Initialize the performance analyzer."""
        self.min_samples_for_analysis = 10
        self.confidence_threshold = 0.7
        self.outlier_threshold = 2.0  # Standard deviations
        
        # Performance thresholds
        self.thresholds = {
            'high_latency_ms': 5000,
            'high_cost_usd': 0.50,
            'low_success_rate': 0.85,
            'high_error_rate': 0.15
        }
        
        logger.info("PromptPerformanceAnalyzer initialized")
    
    def analyze_prompt_performance(self, prompt_id: Optional[str] = None, 
                                 days_back: int = 30) -> List[PromptAnalytics]:
        """
        Analyze performance of specific prompt or all prompts.
        
        Args:
            prompt_id: Specific prompt to analyze, or None for all
            days_back: Number of days of data to analyze
            
        Returns:
            List of prompt analytics
        """
        try:
            # Get trace data for analysis
            traces = self._get_prompt_traces(prompt_id, days_back)
            
            if not traces:
                logger.warning(f"No trace data found for prompt analysis")
                return []
            
            # Group traces by prompt
            prompt_groups = defaultdict(list)
            for trace in traces:
                trace_prompt_id = trace.get('prompt_id', 'unknown')
                prompt_groups[trace_prompt_id].append(trace)
            
            analytics = []
            
            for trace_prompt_id, prompt_traces in prompt_groups.items():
                if len(prompt_traces) < self.min_samples_for_analysis:
                    continue
                
                analytics_result = self._analyze_single_prompt(trace_prompt_id, prompt_traces)
                if analytics_result:
                    analytics.append(analytics_result)
            
            # Sort by optimization potential
            analytics.sort(key=lambda x: x.optimization_potential, reverse=True)
            
            return analytics
            
        except Exception as e:
            logger.error(f"Error analyzing prompt performance: {e}")
            return []
    
    def detect_performance_patterns(self, days_back: int = 30) -> List[PerformancePattern]:
        """
        Detect common performance patterns across all prompts.
        
        Args:
            days_back: Number of days to analyze
            
        Returns:
            List of detected patterns
        """
        try:
            traces = self._get_prompt_traces(None, days_back)
            
            if len(traces) < self.min_samples_for_analysis:
                return []
            
            patterns = []
            
            # Pattern 1: High latency spikes
            high_latency_pattern = self._detect_high_latency_pattern(traces)
            if high_latency_pattern:
                patterns.append(high_latency_pattern)
            
            # Pattern 2: Cost inefficiency
            cost_pattern = self._detect_cost_inefficiency_pattern(traces)
            if cost_pattern:
                patterns.append(cost_pattern)
            
            # Pattern 3: Error clustering
            error_pattern = self._detect_error_clustering_pattern(traces)
            if error_pattern:
                patterns.append(error_pattern)
            
            # Pattern 4: Model performance variations
            model_variation_pattern = self._detect_model_variation_pattern(traces)
            if model_variation_pattern:
                patterns.append(model_variation_pattern)
            
            # Pattern 5: Time-based performance degradation
            time_degradation_pattern = self._detect_time_degradation_pattern(traces)
            if time_degradation_pattern:
                patterns.append(time_degradation_pattern)
            
            return patterns
            
        except Exception as e:
            logger.error(f"Error detecting performance patterns: {e}")
            return []
    
    def compare_model_performance(self, days_back: int = 30) -> List[ModelPerformanceComparison]:
        """
        Compare performance across different models.
        
        Args:
            days_back: Number of days to analyze
            
        Returns:
            List of model performance comparisons
        """
        try:
            traces = self._get_prompt_traces(None, days_back)
            
            if not traces:
                return []
            
            # Group by model
            model_groups = defaultdict(list)
            for trace in traces:
                model = trace.get('model', 'unknown')
                model_groups[model].append(trace)
            
            comparisons = []
            
            for model, model_traces in model_groups.items():
                if len(model_traces) < self.min_samples_for_analysis:
                    continue
                
                comparison = self._analyze_model_performance(model, model_traces)
                if comparison:
                    comparisons.append(comparison)
            
            # Sort by overall score
            comparisons.sort(key=lambda x: x.overall_score, reverse=True)
            
            return comparisons
            
        except Exception as e:
            logger.error(f"Error comparing model performance: {e}")
            return []
    
    def calculate_optimization_potential(self, prompt_analytics: List[PromptAnalytics]) -> Dict[str, Any]:
        """
        Calculate overall optimization potential across all prompts.
        
        Args:
            prompt_analytics: List of prompt analytics
            
        Returns:
            Optimization potential summary
        """
        try:
            if not prompt_analytics:
                return {}
            
            # Calculate aggregate metrics
            total_executions = sum(p.total_executions for p in prompt_analytics)
            weighted_avg_latency = sum(p.avg_latency_ms * p.total_executions for p in prompt_analytics) / total_executions
            weighted_avg_cost = sum(p.avg_cost_usd * p.total_executions for p in prompt_analytics) / total_executions
            avg_success_rate = statistics.mean([p.success_rate for p in prompt_analytics])
            
            # Identify high-impact optimization opportunities
            high_impact_prompts = [p for p in prompt_analytics if p.optimization_potential > 0.7]
            medium_impact_prompts = [p for p in prompt_analytics if 0.4 <= p.optimization_potential <= 0.7]
            
            # Calculate potential savings
            latency_savings_ms = sum(
                p.avg_latency_ms * 0.3 * p.total_executions for p in high_impact_prompts
            ) / total_executions if high_impact_prompts else 0
            
            cost_savings_usd = sum(
                p.avg_cost_usd * 0.25 * p.total_executions for p in high_impact_prompts
            ) / total_executions if high_impact_prompts else 0
            
            return {
                'total_prompts_analyzed': len(prompt_analytics),
                'total_executions': total_executions,
                'weighted_avg_latency_ms': weighted_avg_latency,
                'weighted_avg_cost_usd': weighted_avg_cost,
                'avg_success_rate': avg_success_rate,
                'high_impact_prompts': len(high_impact_prompts),
                'medium_impact_prompts': len(medium_impact_prompts),
                'potential_latency_savings_ms': latency_savings_ms,
                'potential_cost_savings_usd': cost_savings_usd,
                'overall_optimization_score': statistics.mean([p.optimization_potential for p in prompt_analytics]),
                'top_optimization_candidates': [
                    {
                        'prompt_id': p.prompt_id,
                        'optimization_potential': p.optimization_potential,
                        'executions': p.total_executions,
                        'avg_latency_ms': p.avg_latency_ms,
                        'avg_cost_usd': p.avg_cost_usd
                    } for p in prompt_analytics[:5]
                ]
            }
            
        except Exception as e:
            logger.error(f"Error calculating optimization potential: {e}")
            return {}
    
    def _get_prompt_traces(self, prompt_id: Optional[str], days_back: int) -> List[Dict]:
        """Get trace data for prompt analysis."""
        try:
            # Use live data service to get traces
            traces = live_data_service.get_recent_traces(
                limit=5000, 
                data_source='all'
            )
            
            # Filter by prompt_id if specified
            if prompt_id:
                traces = [t for t in traces if t.get('prompt_id') == prompt_id]
            
            # Filter by date
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            filtered_traces = []
            
            for trace in traces:
                timestamp_str = trace.get('timestamp', trace.get('created_at', ''))
                if timestamp_str:
                    try:
                        # Handle various timestamp formats
                        if 'T' in timestamp_str:
                            timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                        else:
                            timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
                        
                        if timestamp >= cutoff_date:
                            filtered_traces.append(trace)
                    except:
                        # Include trace if we can't parse timestamp
                        filtered_traces.append(trace)
            
            return filtered_traces
            
        except Exception as e:
            logger.error(f"Error getting prompt traces: {e}")
            return []
    
    def _analyze_single_prompt(self, prompt_id: str, traces: List[Dict]) -> Optional[PromptAnalytics]:
        """Analyze performance of a single prompt."""
        try:
            if len(traces) < self.min_samples_for_analysis:
                return None
            
            # Extract metrics
            latencies = [float(t.get('latency_ms', t.get('duration', 0))) for t in traces]
            costs = [float(t.get('cost', t.get('cost_usd', 0))) for t in traces]
            
            # Calculate success rate
            successful_traces = len([t for t in traces if t.get('status') in ['success', 'completed', 'ok']])
            success_rate = successful_traces / len(traces)
            error_rate = 1 - success_rate
            
            # Statistical calculations
            avg_latency = statistics.mean(latencies) if latencies else 0
            avg_cost = statistics.mean(costs) if costs else 0
            
            # Calculate percentiles
            p95_latency = np.percentile(latencies, 95) if latencies else 0
            
            # Cost per success
            successful_cost = sum(c for i, c in enumerate(costs) if traces[i].get('status') in ['success', 'completed', 'ok'])
            cost_per_success = successful_cost / max(successful_traces, 1)
            
            # Calculate quality score (composite metric)
            quality_score = self._calculate_quality_score(
                success_rate, avg_latency, avg_cost, len(traces)
            )
            
            # Calculate optimization potential
            optimization_potential = self._calculate_optimization_potential(
                success_rate, avg_latency, avg_cost, p95_latency
            )
            
            # Performance trends (simplified - comparing first half vs second half)
            mid_point = len(traces) // 2
            first_half_latency = statistics.mean(latencies[:mid_point]) if latencies[:mid_point] else 0
            second_half_latency = statistics.mean(latencies[mid_point:]) if latencies[mid_point:] else 0
            
            latency_trend = ((second_half_latency - first_half_latency) / max(first_half_latency, 1)) * 100 if first_half_latency > 0 else 0
            
            return PromptAnalytics(
                prompt_id=prompt_id,
                prompt_text=traces[0].get('prompt', 'N/A')[:200] + '...' if traces[0].get('prompt', '') else 'N/A',
                total_executions=len(traces),
                avg_latency_ms=avg_latency,
                avg_cost_usd=avg_cost,
                success_rate=success_rate,
                error_rate=error_rate,
                p95_latency_ms=p95_latency,
                cost_per_success=cost_per_success,
                quality_score=quality_score,
                optimization_potential=optimization_potential,
                performance_trends={
                    'latency_trend_percentage': latency_trend
                }
            )
            
        except Exception as e:
            logger.error(f"Error analyzing single prompt {prompt_id}: {e}")
            return None
    
    def _calculate_quality_score(self, success_rate: float, avg_latency: float, 
                               avg_cost: float, sample_size: int) -> float:
        """Calculate composite quality score (0-100)."""
        try:
            score = 100.0
            
            # Success rate component (40% of score)
            success_component = success_rate * 40
            
            # Latency component (30% of score)
            if avg_latency > self.thresholds['high_latency_ms']:
                latency_penalty = min(30, (avg_latency / self.thresholds['high_latency_ms']) * 15)
            else:
                latency_penalty = 0
            latency_component = max(0, 30 - latency_penalty)
            
            # Cost component (20% of score)  
            if avg_cost > self.thresholds['high_cost_usd']:
                cost_penalty = min(20, (avg_cost / self.thresholds['high_cost_usd']) * 10)
            else:
                cost_penalty = 0
            cost_component = max(0, 20 - cost_penalty)
            
            # Sample size component (10% of score)
            sample_component = min(10, (sample_size / 100) * 10)
            
            total_score = success_component + latency_component + cost_component + sample_component
            
            return max(0.0, min(100.0, total_score))
            
        except Exception as e:
            logger.error(f"Error calculating quality score: {e}")
            return 50.0
    
    def _calculate_optimization_potential(self, success_rate: float, avg_latency: float,
                                        avg_cost: float, p95_latency: float) -> float:
        """Calculate optimization potential score (0-1)."""
        try:
            potential = 0.0
            
            # High optimization potential indicators
            if success_rate < self.thresholds['low_success_rate']:
                potential += 0.4  # High potential from improving success rate
            
            if avg_latency > self.thresholds['high_latency_ms']:
                potential += 0.3  # High potential from latency optimization
            
            if avg_cost > self.thresholds['high_cost_usd']:
                potential += 0.2  # Potential from cost optimization
            
            # P95 latency indicates inconsistency
            if p95_latency > avg_latency * 2:
                potential += 0.1  # Potential from consistency improvements
            
            return min(1.0, potential)
            
        except Exception as e:
            logger.error(f"Error calculating optimization potential: {e}")
            return 0.0
    
    def _detect_high_latency_pattern(self, traces: List[Dict]) -> Optional[PerformancePattern]:
        """Detect high latency spike patterns."""
        try:
            latencies = [float(t.get('latency_ms', t.get('duration', 0))) for t in traces]
            
            if not latencies:
                return None
            
            mean_latency = statistics.mean(latencies)
            std_latency = statistics.stdev(latencies) if len(latencies) > 1 else 0
            
            if std_latency == 0:
                return None
            
            # Find outlier traces (> 2 std deviations)
            outlier_traces = []
            for i, latency in enumerate(latencies):
                if latency > mean_latency + (self.outlier_threshold * std_latency):
                    outlier_traces.append(traces[i])
            
            if len(outlier_traces) > len(traces) * 0.05:  # More than 5% outliers
                avg_cost = statistics.mean([float(t.get('cost', 0)) for t in outlier_traces])
                success_count = len([t for t in outlier_traces if t.get('status') in ['success', 'completed', 'ok']])
                success_rate = success_count / len(outlier_traces)
                
                return PerformancePattern(
                    pattern_type='high_latency_spikes',
                    prompt_id=None,
                    pattern_description=f'Detected {len(outlier_traces)} high latency spikes ({len(outlier_traces)/len(traces)*100:.1f}% of requests)',
                    frequency=len(outlier_traces),
                    avg_latency=statistics.mean([float(t.get('latency_ms', 0)) for t in outlier_traces]),
                    avg_cost=avg_cost,
                    success_rate=success_rate,
                    confidence_score=min(0.9, len(outlier_traces) / 50),
                    samples=outlier_traces[:5]  # Sample traces
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting high latency pattern: {e}")
            return None
    
    def _detect_cost_inefficiency_pattern(self, traces: List[Dict]) -> Optional[PerformancePattern]:
        """Detect cost inefficiency patterns."""
        try:
            costs = [float(t.get('cost', 0)) for t in traces if float(t.get('cost', 0)) > 0]
            
            if not costs:
                return None
            
            high_cost_threshold = np.percentile(costs, 90)  # Top 10% of costs
            high_cost_traces = [t for t in traces if float(t.get('cost', 0)) >= high_cost_threshold]
            
            if len(high_cost_traces) > 10:  # Significant number of high-cost traces
                avg_latency = statistics.mean([float(t.get('latency_ms', 0)) for t in high_cost_traces])
                avg_cost = statistics.mean([float(t.get('cost', 0)) for t in high_cost_traces])
                success_count = len([t for t in high_cost_traces if t.get('status') in ['success', 'completed', 'ok']])
                success_rate = success_count / len(high_cost_traces)
                
                return PerformancePattern(
                    pattern_type='cost_inefficiency',
                    prompt_id=None,
                    pattern_description=f'Detected {len(high_cost_traces)} high-cost operations (>${high_cost_threshold:.3f}+ per request)',
                    frequency=len(high_cost_traces),
                    avg_latency=avg_latency,
                    avg_cost=avg_cost,
                    success_rate=success_rate,
                    confidence_score=0.8,
                    samples=high_cost_traces[:5]
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting cost inefficiency pattern: {e}")
            return None
    
    def _detect_error_clustering_pattern(self, traces: List[Dict]) -> Optional[PerformancePattern]:
        """Detect error clustering patterns."""
        try:
            error_traces = [t for t in traces if t.get('status') not in ['success', 'completed', 'ok']]
            
            if len(error_traces) < 5:
                return None
            
            # Group errors by type/message
            error_groups = defaultdict(list)
            for trace in error_traces:
                error_msg = trace.get('error', trace.get('error_message', 'unknown_error'))[:50]
                error_groups[error_msg].append(trace)
            
            # Find the largest error cluster
            largest_cluster = max(error_groups.values(), key=len)
            
            if len(largest_cluster) >= len(error_traces) * 0.3:  # 30% of errors are the same type
                avg_latency = statistics.mean([float(t.get('latency_ms', 0)) for t in largest_cluster])
                avg_cost = statistics.mean([float(t.get('cost', 0)) for t in largest_cluster])
                
                return PerformancePattern(
                    pattern_type='error_clustering',
                    prompt_id=None,
                    pattern_description=f'Detected cluster of {len(largest_cluster)} similar errors',
                    frequency=len(largest_cluster),
                    avg_latency=avg_latency,
                    avg_cost=avg_cost,
                    success_rate=0.0,
                    confidence_score=0.85,
                    samples=largest_cluster[:5]
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting error clustering pattern: {e}")
            return None
    
    def _detect_model_variation_pattern(self, traces: List[Dict]) -> Optional[PerformancePattern]:
        """Detect significant performance variations across models."""
        try:
            model_groups = defaultdict(list)
            for trace in traces:
                model = trace.get('model', 'unknown')
                model_groups[model].append(trace)
            
            if len(model_groups) < 2:
                return None
            
            # Calculate performance metrics for each model
            model_performances = []
            for model, model_traces in model_groups.items():
                if len(model_traces) < self.min_samples_for_analysis:
                    continue
                
                latencies = [float(t.get('latency_ms', 0)) for t in model_traces]
                costs = [float(t.get('cost', 0)) for t in model_traces]
                success_count = len([t for t in model_traces if t.get('status') in ['success', 'completed', 'ok']])
                
                model_performances.append({
                    'model': model,
                    'avg_latency': statistics.mean(latencies) if latencies else 0,
                    'avg_cost': statistics.mean(costs) if costs else 0,
                    'success_rate': success_count / len(model_traces),
                    'trace_count': len(model_traces)
                })
            
            if len(model_performances) < 2:
                return None
            
            # Find performance variations
            latency_values = [p['avg_latency'] for p in model_performances]
            cost_values = [p['avg_cost'] for p in model_performances]
            
            latency_cv = (statistics.stdev(latency_values) / statistics.mean(latency_values)) if statistics.mean(latency_values) > 0 else 0
            cost_cv = (statistics.stdev(cost_values) / statistics.mean(cost_values)) if statistics.mean(cost_values) > 0 else 0
            
            # High coefficient of variation indicates significant differences
            if latency_cv > 0.5 or cost_cv > 0.5:
                best_model = min(model_performances, key=lambda x: x['avg_cost'] + (x['avg_latency'] / 1000))
                worst_model = max(model_performances, key=lambda x: x['avg_cost'] + (x['avg_latency'] / 1000))
                
                return PerformancePattern(
                    pattern_type='model_variation',
                    prompt_id=None,
                    pattern_description=f'Significant performance variation across models. Best: {best_model["model"]}, Worst: {worst_model["model"]}',
                    frequency=len(model_performances),
                    avg_latency=statistics.mean(latency_values),
                    avg_cost=statistics.mean(cost_values),
                    success_rate=statistics.mean([p['success_rate'] for p in model_performances]),
                    confidence_score=0.8,
                    samples=[]  # Could add sample traces from each model
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting model variation pattern: {e}")
            return None
    
    def _detect_time_degradation_pattern(self, traces: List[Dict]) -> Optional[PerformancePattern]:
        """Detect performance degradation over time."""
        try:
            # Sort traces by timestamp
            sorted_traces = sorted(traces, key=lambda t: t.get('timestamp', t.get('created_at', '')))
            
            if len(sorted_traces) < 20:  # Need sufficient data
                return None
            
            # Split into time windows
            window_size = len(sorted_traces) // 4
            windows = [
                sorted_traces[i:i+window_size] 
                for i in range(0, len(sorted_traces), window_size)
            ]
            
            # Calculate performance for each window
            window_performances = []
            for window in windows:
                if len(window) < 5:
                    continue
                
                latencies = [float(t.get('latency_ms', 0)) for t in window]
                costs = [float(t.get('cost', 0)) for t in window]
                success_count = len([t for t in window if t.get('status') in ['success', 'completed', 'ok']])
                
                window_performances.append({
                    'avg_latency': statistics.mean(latencies) if latencies else 0,
                    'avg_cost': statistics.mean(costs) if costs else 0,
                    'success_rate': success_count / len(window)
                })
            
            if len(window_performances) < 3:
                return None
            
            # Check for degradation trends
            latencies = [w['avg_latency'] for w in window_performances]
            success_rates = [w['success_rate'] for w in window_performances]
            
            # Simple trend detection using correlation with time
            time_indices = list(range(len(window_performances)))
            
            # Calculate correlation with time (positive = increasing/degrading)
            latency_correlation = stats.pearsonr(time_indices, latencies)[0] if len(latencies) > 1 else 0
            success_correlation = stats.pearsonr(time_indices, success_rates)[0] if len(success_rates) > 1 else 0
            
            # Degradation detected if latency increasing OR success rate decreasing
            if latency_correlation > 0.6 or success_correlation < -0.6:
                return PerformancePattern(
                    pattern_type='time_degradation',
                    prompt_id=None,
                    pattern_description=f'Performance degradation over time detected (latency trend: {latency_correlation:.2f}, success trend: {success_correlation:.2f})',
                    frequency=len(window_performances),
                    avg_latency=statistics.mean(latencies),
                    avg_cost=statistics.mean([w['avg_cost'] for w in window_performances]),
                    success_rate=statistics.mean(success_rates),
                    confidence_score=max(abs(latency_correlation), abs(success_correlation)),
                    samples=[]
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting time degradation pattern: {e}")
            return None
    
    def _analyze_model_performance(self, model_name: str, traces: List[Dict]) -> Optional[ModelPerformanceComparison]:
        """Analyze performance of a specific model."""
        try:
            latencies = [float(t.get('latency_ms', 0)) for t in traces]
            costs = [float(t.get('cost', 0)) for t in traces]
            success_count = len([t for t in traces if t.get('status') in ['success', 'completed', 'ok']])
            
            avg_latency = statistics.mean(latencies) if latencies else 0
            avg_cost = statistics.mean(costs) if costs else 0
            success_rate = success_count / len(traces)
            
            # Calculate efficiency scores (higher is better)
            cost_efficiency = 1 / (avg_cost + 0.01)  # Avoid division by zero
            latency_efficiency = 1 / (avg_latency / 1000 + 0.1)  # Convert to seconds
            
            # Overall score (weighted combination)
            overall_score = (
                success_rate * 0.4 +           # 40% weight on success rate
                (cost_efficiency / 10) * 0.3 +  # 30% weight on cost efficiency  
                (latency_efficiency / 10) * 0.3  # 30% weight on latency efficiency
            )
            
            return ModelPerformanceComparison(
                model_name=model_name,
                avg_latency=avg_latency,
                avg_cost=avg_cost,
                success_rate=success_rate,
                cost_efficiency_score=cost_efficiency,
                latency_efficiency_score=latency_efficiency,
                overall_score=min(1.0, overall_score)  # Cap at 1.0
            )
            
        except Exception as e:
            logger.error(f"Error analyzing model performance for {model_name}: {e}")
            return None