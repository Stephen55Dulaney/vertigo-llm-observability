"""
A/B Testing Orchestrator - Automated Prompt Optimization Testing
Manages the complete lifecycle of A/B tests for prompt optimization including traffic splitting,
statistical analysis, and automated decision making.
"""

import os
import uuid
import logging
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import json
import random
import math
from scipy import stats
import numpy as np

from app.models import (
    db, ABTest, ABTestVariant, ABTestResult, ABTestAnalysis,
    Prompt, LiveTrace, PerformanceMetric
)
from app.services.live_data_service import live_data_service
from .ml_service import ml_optimization_service

logger = logging.getLogger(__name__)


@dataclass
class TrafficSplit:
    """Traffic split configuration for A/B tests."""
    variant_id: str
    percentage: float
    is_control: bool = False


@dataclass
class ABTestConfiguration:
    """A/B test configuration."""
    name: str
    description: str
    hypothesis: str
    success_metrics: List[str]
    traffic_splits: List[TrafficSplit]
    min_sample_size: int = 100
    confidence_level: float = 0.95
    statistical_power: float = 0.80
    max_duration_hours: int = 168
    auto_conclude: bool = True
    auto_implement: bool = False


@dataclass
class StatisticalResult:
    """Statistical analysis result."""
    p_value: float
    effect_size: float
    confidence_interval: Tuple[float, float]
    is_significant: bool
    statistical_power: float
    sample_size_adequate: bool


@dataclass
class ABTestRecommendation:
    """A/B test recommendation."""
    action: str  # continue, stop_winner, stop_no_effect, extend, early_stop
    confidence: float
    reasoning: str
    winning_variant_id: Optional[str] = None
    expected_impact: Optional[Dict[str, float]] = None


class ABTestingOrchestrator:
    """
    A/B Testing Orchestrator for automated prompt optimization.
    
    Manages the complete A/B testing lifecycle:
    - Test creation and configuration
    - Traffic splitting and variant selection
    - Performance tracking and data collection
    - Statistical analysis and significance testing
    - Automated test conclusion and winner selection
    """
    
    def __init__(self):
        """Initialize the A/B testing orchestrator."""
        self.logger = logging.getLogger(__name__)
        self.ml_service = ml_optimization_service
        
        # Statistical constants
        self.MIN_EFFECT_SIZE = 0.1  # Minimum effect size to consider meaningful
        self.EARLY_STOPPING_THRESHOLD = 0.001  # p-value threshold for early stopping
        self.POWER_ANALYSIS_ALPHA = 0.05
        
        self.logger.info("ABTestingOrchestrator initialized")
    
    def create_ab_test(self, config: ABTestConfiguration, creator_id: int) -> str:
        """
        Create a new A/B test with the specified configuration.
        
        Args:
            config: A/B test configuration
            creator_id: User ID creating the test
            
        Returns:
            Test ID of the created test
        """
        try:
            test_id = f"ab_test_{uuid.uuid4().hex[:12]}"
            
            # Validate configuration
            self._validate_test_configuration(config)
            
            # Create traffic split mapping
            traffic_split = {
                split.variant_id: float(split.percentage) 
                for split in config.traffic_splits
            }
            
            # Create the test
            ab_test = ABTest(
                test_id=test_id,
                name=config.name,
                description=config.description,
                hypothesis=config.hypothesis,
                success_metrics=config.success_metrics,
                traffic_split=traffic_split,
                min_sample_size=config.min_sample_size,
                confidence_level=config.confidence_level,
                statistical_power=config.statistical_power,
                max_duration_hours=config.max_duration_hours,
                auto_conclude=config.auto_conclude,
                auto_implement=config.auto_implement,
                creator_id=creator_id,
                status='draft'
            )
            
            db.session.add(ab_test)
            db.session.flush()  # Get the ID
            
            # Create variants
            for split in config.traffic_splits:
                variant_id = f"{test_id}_variant_{split.variant_id}"
                variant = ABTestVariant(
                    variant_id=variant_id,
                    ab_test_id=ab_test.id,
                    name=f"Variant {split.variant_id}",
                    is_control=split.is_control,
                    traffic_percentage=split.percentage
                )
                db.session.add(variant)
            
            db.session.commit()
            
            self.logger.info(f"Created A/B test {test_id} with {len(config.traffic_splits)} variants")
            return test_id
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error creating A/B test: {e}")
            raise
    
    def configure_variants(self, test_id: str, variant_configs: Dict[str, Dict[str, Any]]) -> bool:
        """
        Configure the content and parameters for test variants.
        
        Args:
            test_id: Test identifier
            variant_configs: Dictionary mapping variant_id to configuration
            
        Returns:
            True if successful
        """
        try:
            test = ABTest.query.filter_by(test_id=test_id).first()
            if not test:
                raise ValueError(f"Test {test_id} not found")
            
            if test.status != 'draft':
                raise ValueError(f"Can only configure variants for draft tests")
            
            # Update each variant
            for variant_id, config in variant_configs.items():
                full_variant_id = f"{test_id}_variant_{variant_id}"
                variant = ABTestVariant.query.filter_by(variant_id=full_variant_id).first()
                
                if not variant:
                    self.logger.warning(f"Variant {full_variant_id} not found")
                    continue
                
                # Update variant configuration
                if 'name' in config:
                    variant.name = config['name']
                if 'description' in config:
                    variant.description = config['description']
                if 'prompt_content' in config:
                    variant.prompt_content = config['prompt_content']
                if 'model_config' in config:
                    variant.model_config = config['model_config']
                if 'parameters' in config:
                    variant.parameters = config['parameters']
                if 'generation_method' in config:
                    variant.generation_method = config['generation_method']
                if 'generation_context' in config:
                    variant.generation_context = config['generation_context']
            
            db.session.commit()
            self.logger.info(f"Configured {len(variant_configs)} variants for test {test_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error configuring variants: {e}")
            raise
    
    def start_test(self, test_id: str) -> bool:
        """
        Start an A/B test.
        
        Args:
            test_id: Test identifier
            
        Returns:
            True if started successfully
        """
        try:
            test = ABTest.query.filter_by(test_id=test_id).first()
            if not test:
                raise ValueError(f"Test {test_id} not found")
            
            if test.status != 'draft':
                raise ValueError(f"Can only start draft tests")
            
            # Validate all variants are configured
            variants = ABTestVariant.query.filter_by(ab_test_id=test.id).all()
            if not variants:
                raise ValueError("No variants configured for test")
            
            for variant in variants:
                if not variant.prompt_content and not variant.model_config:
                    raise ValueError(f"Variant {variant.variant_id} not configured")
            
            # Calculate required sample size
            required_sample_size = self._calculate_required_sample_size(
                test.statistical_power,
                test.confidence_level,
                self.MIN_EFFECT_SIZE
            )
            
            # Start the test
            test.status = 'running'
            test.start_time = datetime.utcnow()
            
            # Create initial analysis record
            analysis = ABTestAnalysis(
                ab_test_id=test.id,
                required_sample_size=required_sample_size,
                confidence_level=test.confidence_level,
                recommendation='continue',
                recommendation_confidence=1.0,
                analysis_method='frequentist'
            )
            
            db.session.add(analysis)
            db.session.commit()
            
            self.logger.info(f"Started A/B test {test_id}")
            return True
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error starting test: {e}")
            raise
    
    def select_variant(self, test_id: str, user_session: Optional[str] = None, 
                      context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Select a variant for the given test and user session.
        
        Args:
            test_id: Test identifier
            user_session: User session ID for consistent assignment
            context: Additional context for selection
            
        Returns:
            Variant ID to use, or None if test not active
        """
        try:
            test = ABTest.query.filter_by(test_id=test_id).first()
            if not test or test.status != 'running':
                return None
            
            # Check if test has expired
            if test.max_duration_hours and test.start_time:
                elapsed_hours = (datetime.utcnow() - test.start_time).total_seconds() / 3600
                if elapsed_hours > test.max_duration_hours:
                    self._auto_conclude_test(test_id, reason="Max duration reached")
                    return None
            
            variants = ABTestVariant.query.filter_by(ab_test_id=test.id).all()
            if not variants:
                return None
            
            # Use consistent assignment based on user session
            if user_session:
                # Hash user session with test ID for consistent assignment
                hash_input = f"{test_id}_{user_session}"
                hash_value = int(hashlib.md5(hash_input.encode()).hexdigest()[:8], 16)
                selection_point = (hash_value % 100) / 100.0
            else:
                # Random assignment
                selection_point = random.random()
            
            # Select variant based on traffic split
            cumulative_percentage = 0.0
            for variant in variants:
                cumulative_percentage += float(variant.traffic_percentage) / 100.0
                if selection_point <= cumulative_percentage:
                    return variant.variant_id
            
            # Fallback to first variant
            return variants[0].variant_id
            
        except Exception as e:
            self.logger.error(f"Error selecting variant: {e}")
            return None
    
    def record_result(self, test_id: str, variant_id: str, request_id: str,
                     latency_ms: float, cost_usd: float, success: bool,
                     user_session: Optional[str] = None,
                     context: Optional[Dict[str, Any]] = None,
                     external_trace_id: Optional[str] = None) -> bool:
        """
        Record a test result for analysis.
        
        Args:
            test_id: Test identifier
            variant_id: Variant that was used
            request_id: Unique request identifier
            latency_ms: Request latency in milliseconds
            cost_usd: Request cost in USD
            success: Whether the request was successful
            user_session: User session ID
            context: Additional context
            external_trace_id: Link to external trace
            
        Returns:
            True if recorded successfully
        """
        try:
            test = ABTest.query.filter_by(test_id=test_id).first()
            if not test or test.status != 'running':
                return False
            
            # Record the result
            result = ABTestResult(
                ab_test_id=test.id,
                variant_id=variant_id,
                request_id=request_id,
                user_session=user_session,
                latency_ms=latency_ms,
                cost_usd=cost_usd,
                success=success,
                request_context=context,
                external_trace_id=external_trace_id
            )
            
            db.session.add(result)
            
            # Update variant metrics
            variant = ABTestVariant.query.filter_by(variant_id=variant_id).first()
            if variant:
                variant.requests_served += 1
                if success:
                    variant.success_count += 1
                else:
                    variant.error_count += 1
                
                variant.total_latency_ms += float(latency_ms)
                variant.total_cost_usd += float(cost_usd)
                
                # Update computed metrics
                if variant.requests_served > 0:
                    variant.avg_latency_ms = float(variant.total_latency_ms) / variant.requests_served
                    variant.avg_cost_usd = float(variant.total_cost_usd) / variant.requests_served
                    variant.success_rate = float(variant.success_count) / variant.requests_served
            
            db.session.commit()
            
            # Check if we should run analysis
            total_results = ABTestResult.query.filter_by(ab_test_id=test.id).count()
            if total_results % 50 == 0:  # Analyze every 50 results
                self._analyze_test_async(test_id)
            
            return True
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error recording result: {e}")
            return False
    
    def analyze_test(self, test_id: str) -> Dict[str, Any]:
        """
        Perform statistical analysis on a running A/B test.
        
        Args:
            test_id: Test identifier
            
        Returns:
            Analysis results
        """
        try:
            test = ABTest.query.filter_by(test_id=test_id).first()
            if not test:
                raise ValueError(f"Test {test_id} not found")
            
            variants = ABTestVariant.query.filter_by(ab_test_id=test.id).all()
            if len(variants) < 2:
                raise ValueError("Need at least 2 variants for analysis")
            
            results = ABTestResult.query.filter_by(ab_test_id=test.id).all()
            if len(results) < 10:
                return {
                    'status': 'insufficient_data',
                    'message': 'Need at least 10 results for analysis',
                    'current_sample_size': len(results)
                }
            
            # Analyze each metric
            analysis_results = {}
            
            for metric in test.success_metrics:
                metric_results = self._analyze_metric(variants, results, metric)
                analysis_results[metric] = metric_results
            
            # Determine overall recommendation
            recommendation = self._generate_test_recommendation(test, analysis_results)
            
            # Store analysis results
            analysis = ABTestAnalysis(
                ab_test_id=test.id,
                current_sample_size=len(results),
                sample_size_adequate=len(results) >= test.min_sample_size,
                statistical_significance=min(r.get('p_value', 1.0) for r in analysis_results.values()),
                variant_comparisons=analysis_results,
                recommendation=recommendation.action,
                recommendation_confidence=recommendation.confidence,
                recommended_actions=[recommendation.reasoning]
            )
            
            db.session.add(analysis)
            db.session.commit()
            
            # Auto-conclude if configured
            if test.auto_conclude and recommendation.action in ['stop_winner', 'stop_no_effect']:
                self._conclude_test(test_id, recommendation)
            
            return {
                'status': 'analyzed',
                'sample_size': len(results),
                'analysis_results': analysis_results,
                'recommendation': asdict(recommendation),
                'test_status': test.status
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing test: {e}")
            return {'status': 'error', 'error': str(e)}
    
    def get_test_status(self, test_id: str) -> Dict[str, Any]:
        """
        Get comprehensive status of an A/B test.
        
        Args:
            test_id: Test identifier
            
        Returns:
            Test status information
        """
        try:
            test = ABTest.query.filter_by(test_id=test_id).first()
            if not test:
                return {'error': 'Test not found'}
            
            variants = ABTestVariant.query.filter_by(ab_test_id=test.id).all()
            results_count = ABTestResult.query.filter_by(ab_test_id=test.id).count()
            
            latest_analysis = ABTestAnalysis.query.filter_by(
                ab_test_id=test.id
            ).order_by(ABTestAnalysis.analysis_date.desc()).first()
            
            # Calculate progress
            progress = 0.0
            if test.min_sample_size > 0:
                progress = min(1.0, results_count / test.min_sample_size)
            
            # Calculate elapsed time
            elapsed_hours = 0
            if test.start_time:
                elapsed_hours = (datetime.utcnow() - test.start_time).total_seconds() / 3600
            
            return {
                'test_id': test_id,
                'name': test.name,
                'status': test.status,
                'start_time': test.start_time.isoformat() if test.start_time else None,
                'elapsed_hours': elapsed_hours,
                'max_duration_hours': test.max_duration_hours,
                'progress': progress,
                'results_count': results_count,
                'min_sample_size': test.min_sample_size,
                'variants': [
                    {
                        'variant_id': v.variant_id,
                        'name': v.name,
                        'is_control': v.is_control,
                        'requests_served': v.requests_served,
                        'success_rate': float(v.success_rate) if v.success_rate else 0.0,
                        'avg_latency_ms': float(v.avg_latency_ms) if v.avg_latency_ms else 0.0,
                        'avg_cost_usd': float(v.avg_cost_usd) if v.avg_cost_usd else 0.0
                    }
                    for v in variants
                ],
                'latest_analysis': {
                    'analysis_date': latest_analysis.analysis_date.isoformat() if latest_analysis else None,
                    'recommendation': latest_analysis.recommendation if latest_analysis else None,
                    'statistical_significance': float(latest_analysis.statistical_significance) if latest_analysis and latest_analysis.statistical_significance else None,
                    'recommendation_confidence': float(latest_analysis.recommendation_confidence) if latest_analysis else None
                } if latest_analysis else None,
                'winning_variant_id': test.winning_variant_id
            }
            
        except Exception as e:
            self.logger.error(f"Error getting test status: {e}")
            return {'error': str(e)}
    
    def list_active_tests(self) -> List[Dict[str, Any]]:
        """
        List all active A/B tests.
        
        Returns:
            List of active test summaries
        """
        try:
            tests = ABTest.query.filter(ABTest.status.in_(['running', 'paused'])).all()
            
            return [
                {
                    'test_id': test.test_id,
                    'name': test.name,
                    'status': test.status,
                    'start_time': test.start_time.isoformat() if test.start_time else None,
                    'variants_count': ABTestVariant.query.filter_by(ab_test_id=test.id).count(),
                    'results_count': ABTestResult.query.filter_by(ab_test_id=test.id).count()
                }
                for test in tests
            ]
            
        except Exception as e:
            self.logger.error(f"Error listing active tests: {e}")
            return []
    
    def stop_test(self, test_id: str, reason: str = "Manual stop") -> bool:
        """
        Stop a running A/B test.
        
        Args:
            test_id: Test identifier
            reason: Reason for stopping
            
        Returns:
            True if stopped successfully
        """
        try:
            test = ABTest.query.filter_by(test_id=test_id).first()
            if not test:
                raise ValueError(f"Test {test_id} not found")
            
            if test.status not in ['running', 'paused']:
                raise ValueError(f"Can only stop running or paused tests")
            
            test.status = 'cancelled'
            test.end_time = datetime.utcnow()
            if test.start_time:
                test.actual_duration_hours = (test.end_time - test.start_time).total_seconds() / 3600
            
            db.session.commit()
            
            self.logger.info(f"Stopped A/B test {test_id}: {reason}")
            return True
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error stopping test: {e}")
            raise
    
    def _validate_test_configuration(self, config: ABTestConfiguration) -> None:
        """Validate A/B test configuration."""
        if not config.name or not config.description:
            raise ValueError("Name and description are required")
        
        if not config.traffic_splits or len(config.traffic_splits) < 2:
            raise ValueError("Need at least 2 variants")
        
        total_percentage = sum(split.percentage for split in config.traffic_splits)
        if abs(total_percentage - 100.0) > 0.01:
            raise ValueError(f"Traffic splits must total 100%, got {total_percentage}")
        
        control_count = sum(1 for split in config.traffic_splits if split.is_control)
        if control_count != 1:
            raise ValueError("Exactly one variant must be marked as control")
        
        if not config.success_metrics:
            raise ValueError("Must specify at least one success metric")
    
    def _calculate_required_sample_size(self, power: float, alpha: float, effect_size: float) -> int:
        """Calculate required sample size for statistical power."""
        try:
            # Simplified sample size calculation
            # For more accuracy, would use power analysis libraries like statsmodels
            base_size = 100  # Base sample size
            
            # Adjust based on power and effect size
            power_adjustment = 1.0 / max(0.1, float(power))  # Higher power needs more samples
            effect_adjustment = 1.0 / max(0.05, float(effect_size))  # Smaller effects need more samples
            
            n = int(base_size * power_adjustment * effect_adjustment)
            return max(50, min(1000, n))  # Between 50 and 1000 per group
            
        except Exception as e:
            self.logger.error(f"Error calculating sample size: {e}")
            return 100  # Default fallback
    
    def _analyze_metric(self, variants: List[ABTestVariant], results: List[ABTestResult], 
                       metric: str) -> Dict[str, Any]:
        """Analyze a specific metric across variants."""
        try:
            # Group results by variant
            variant_data = {}
            for variant in variants:
                variant_results = [r for r in results if r.variant_id == variant.variant_id]
                
                if metric == 'success_rate':
                    values = [1.0 if r.success else 0.0 for r in variant_results]
                elif metric == 'latency':
                    values = [float(r.latency_ms) for r in variant_results if r.latency_ms is not None]
                elif metric == 'cost':
                    values = [float(r.cost_usd) for r in variant_results if r.cost_usd is not None]
                else:
                    continue
                
                if values:
                    variant_data[variant.variant_id] = {
                        'values': values,
                        'mean': np.mean(values),
                        'std': np.std(values),
                        'count': len(values),
                        'is_control': variant.is_control
                    }
            
            if len(variant_data) < 2:
                return {'error': 'Insufficient data for analysis'}
            
            # Find control and treatment groups
            control_data = None
            treatment_data = []
            
            for variant_id, data in variant_data.items():
                if data['is_control']:
                    control_data = data
                else:
                    treatment_data.append((variant_id, data))
            
            if not control_data or not treatment_data:
                return {'error': 'Missing control or treatment data'}
            
            # Perform t-test for each treatment vs control
            comparisons = {}
            for treatment_id, treatment in treatment_data:
                try:
                    # Two-sample t-test
                    statistic, p_value = stats.ttest_ind(
                        treatment['values'], 
                        control_data['values']
                    )
                    
                    # Calculate effect size (Cohen's d)
                    pooled_std = np.sqrt(
                        ((len(treatment['values']) - 1) * treatment['std']**2 + 
                         (len(control_data['values']) - 1) * control_data['std']**2) /
                        (len(treatment['values']) + len(control_data['values']) - 2)
                    )
                    
                    effect_size = (treatment['mean'] - control_data['mean']) / pooled_std if pooled_std > 0 else 0.0
                    
                    # Calculate confidence interval (simplified)
                    se_diff = pooled_std * np.sqrt(1/len(treatment['values']) + 1/len(control_data['values']))
                    t_critical = stats.t.ppf(0.975, len(treatment['values']) + len(control_data['values']) - 2)
                    
                    mean_diff = treatment['mean'] - control_data['mean']
                    ci_lower = mean_diff - t_critical * se_diff
                    ci_upper = mean_diff + t_critical * se_diff
                    
                    comparisons[treatment_id] = {
                        'p_value': p_value,
                        'effect_size': effect_size,
                        'mean_difference': mean_diff,
                        'confidence_interval': [ci_lower, ci_upper],
                        'is_significant': p_value < 0.05,
                        'improvement_percent': (mean_diff / control_data['mean']) * 100 if control_data['mean'] != 0 else 0
                    }
                    
                except Exception as e:
                    self.logger.error(f"Error in statistical test: {e}")
                    comparisons[treatment_id] = {'error': str(e)}
            
            return {
                'metric': metric,
                'control_data': {
                    'mean': control_data['mean'],
                    'std': control_data['std'],
                    'count': control_data['count']
                },
                'comparisons': comparisons,
                'overall_significant': any(c.get('is_significant', False) for c in comparisons.values())
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing metric {metric}: {e}")
            return {'error': str(e)}
    
    def _generate_test_recommendation(self, test: ABTest, analysis_results: Dict[str, Any]) -> ABTestRecommendation:
        """Generate recommendation based on analysis results."""
        try:
            # Check if we have sufficient sample size
            results_count = ABTestResult.query.filter_by(ab_test_id=test.id).count()
            if results_count < test.min_sample_size:
                return ABTestRecommendation(
                    action='continue',
                    confidence=0.8,
                    reasoning=f"Need more data: {results_count}/{test.min_sample_size} samples"
                )
            
            # Check for significant results
            significant_results = []
            for metric, results in analysis_results.items():
                if results.get('overall_significant'):
                    significant_results.append(metric)
            
            if not significant_results:
                return ABTestRecommendation(
                    action='stop_no_effect',
                    confidence=0.7,
                    reasoning="No statistically significant effects detected"
                )
            
            # Find best performing variant
            best_variant = None
            best_score = float('-inf')
            
            for metric, results in analysis_results.items():
                comparisons = results.get('comparisons', {})
                for variant_id, comparison in comparisons.items():
                    if comparison.get('is_significant'):
                        improvement = comparison.get('improvement_percent', 0)
                        if improvement > best_score:
                            best_score = improvement
                            best_variant = variant_id
            
            if best_variant and best_score > 5:  # At least 5% improvement
                return ABTestRecommendation(
                    action='stop_winner',
                    confidence=0.9,
                    reasoning=f"Clear winner found: {best_score:.1f}% improvement",
                    winning_variant_id=best_variant,
                    expected_impact={'improvement_percent': best_score}
                )
            
            # Check if test should continue
            if test.max_duration_hours:
                elapsed_hours = (datetime.utcnow() - test.start_time).total_seconds() / 3600
                if elapsed_hours > test.max_duration_hours * 0.9:  # 90% of max duration
                    return ABTestRecommendation(
                        action='stop_no_effect',
                        confidence=0.6,
                        reasoning="Approaching maximum test duration"
                    )
            
            return ABTestRecommendation(
                action='continue',
                confidence=0.8,
                reasoning="Test showing promise, continue collecting data"
            )
            
        except Exception as e:
            self.logger.error(f"Error generating recommendation: {e}")
            return ABTestRecommendation(
                action='continue',
                confidence=0.5,
                reasoning=f"Analysis error: {str(e)}"
            )
    
    def _conclude_test(self, test_id: str, recommendation: ABTestRecommendation) -> None:
        """Conclude an A/B test based on recommendation."""
        try:
            test = ABTest.query.filter_by(test_id=test_id).first()
            if not test:
                return
            
            test.status = 'completed'
            test.end_time = datetime.utcnow()
            if test.start_time:
                test.actual_duration_hours = (test.end_time - test.start_time).total_seconds() / 3600
            
            if recommendation.winning_variant_id:
                test.winning_variant_id = recommendation.winning_variant_id
                
                # Auto-implement winner if configured
                if test.auto_implement:
                    self._implement_winning_variant(test_id, recommendation.winning_variant_id)
            
            # Store final results
            test.results_summary = {
                'recommendation': asdict(recommendation),
                'conclusion_time': datetime.utcnow().isoformat(),
                'final_sample_size': ABTestResult.query.filter_by(ab_test_id=test.id).count()
            }
            
            db.session.commit()
            self.logger.info(f"Concluded A/B test {test_id}: {recommendation.action}")
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error concluding test: {e}")
    
    def _auto_conclude_test(self, test_id: str, reason: str) -> None:
        """Auto-conclude test due to external conditions."""
        try:
            test = ABTest.query.filter_by(test_id=test_id).first()
            if not test:
                return
            
            test.status = 'completed'
            test.end_time = datetime.utcnow()
            if test.start_time:
                test.actual_duration_hours = (test.end_time - test.start_time).total_seconds() / 3600
            
            test.results_summary = {
                'auto_concluded': True,
                'reason': reason,
                'conclusion_time': datetime.utcnow().isoformat()
            }
            
            db.session.commit()
            self.logger.info(f"Auto-concluded A/B test {test_id}: {reason}")
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Error auto-concluding test: {e}")
    
    def _implement_winning_variant(self, test_id: str, winning_variant_id: str) -> None:
        """Implement the winning variant as the new default."""
        # This would integrate with the prompt management system
        # to update the active prompt with the winning variant
        self.logger.info(f"Auto-implementing winning variant {winning_variant_id} for test {test_id}")
        # TODO: Implement integration with prompt management
    
    def _analyze_test_async(self, test_id: str) -> None:
        """Analyze test asynchronously (placeholder for background task)."""
        # In a production system, this would queue a background job
        # For now, we'll just trigger the analysis directly
        try:
            self.analyze_test(test_id)
        except Exception as e:
            self.logger.error(f"Error in async analysis: {e}")


# Global service instance
ab_testing_orchestrator = ABTestingOrchestrator()