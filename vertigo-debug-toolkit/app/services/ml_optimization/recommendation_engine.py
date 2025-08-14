"""
ML-Based Optimization Recommendation Engine
Generates intelligent, actionable recommendations for prompt optimization based on analysis results.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from collections import defaultdict, Counter
import statistics
import json

from .performance_analyzer import PromptAnalytics, PerformancePattern, ModelPerformanceComparison
from .quality_scorer import PromptQualityAssessment, QualityMetric

logger = logging.getLogger(__name__)


@dataclass
class OptimizationRecommendation:
    """Individual optimization recommendation."""
    recommendation_id: str
    category: str  # performance, quality, cost, reliability
    priority: str  # critical, high, medium, low
    title: str
    description: str
    rationale: str
    expected_impact: Dict[str, float]  # metrics -> expected improvement
    implementation_effort: str  # low, medium, high
    timeframe: str  # immediate, short-term, long-term
    specific_actions: List[str]
    prerequisites: List[str]
    success_metrics: List[str]
    confidence_score: float  # 0-1
    applicable_prompts: List[str]
    tags: List[str]


@dataclass
class OptimizationPlan:
    """Complete optimization plan with prioritized recommendations."""
    plan_id: str
    created_at: datetime
    summary: str
    total_recommendations: int
    priority_breakdown: Dict[str, int]
    expected_improvements: Dict[str, float]
    estimated_timeline: str
    recommendations: List[OptimizationRecommendation]
    quick_wins: List[OptimizationRecommendation]
    long_term_goals: List[OptimizationRecommendation]


class OptimizationRecommendationEngine:
    """
    Intelligent recommendation engine for prompt optimization.
    
    Analyzes performance data, quality assessments, and patterns to generate
    actionable optimization recommendations with prioritization.
    """
    
    def __init__(self):
        """Initialize the recommendation engine."""
        
        # Impact weights for different improvements
        self.impact_weights = {
            'latency_improvement': 0.25,
            'cost_reduction': 0.30,
            'success_rate_improvement': 0.35,
            'quality_improvement': 0.10
        }
        
        # Recommendation templates
        self.recommendation_templates = self._initialize_templates()
        
        # Thresholds for generating recommendations
        self.thresholds = {
            'high_latency_ms': 3000,
            'high_cost_usd': 0.20,
            'low_success_rate': 0.85,
            'low_quality_score': 60,
            'high_error_rate': 0.15,
            'min_samples_for_recommendation': 10
        }
        
        logger.info("OptimizationRecommendationEngine initialized")
    
    def generate_optimization_plan(self, 
                                 performance_analytics: List[PromptAnalytics],
                                 quality_assessments: List[PromptQualityAssessment],
                                 performance_patterns: List[PerformancePattern],
                                 model_comparisons: List[ModelPerformanceComparison]) -> OptimizationPlan:
        """
        Generate a comprehensive optimization plan.
        
        Args:
            performance_analytics: Performance analysis results
            quality_assessments: Quality assessment results
            performance_patterns: Detected performance patterns
            model_comparisons: Model performance comparisons
            
        Returns:
            Complete optimization plan
        """
        try:
            recommendations = []
            
            # Generate performance-based recommendations
            perf_recommendations = self._generate_performance_recommendations(
                performance_analytics, performance_patterns
            )
            recommendations.extend(perf_recommendations)
            
            # Generate quality-based recommendations
            quality_recommendations = self._generate_quality_recommendations(quality_assessments)
            recommendations.extend(quality_recommendations)
            
            # Generate model optimization recommendations
            model_recommendations = self._generate_model_recommendations(model_comparisons)
            recommendations.extend(model_recommendations)
            
            # Generate pattern-based recommendations
            pattern_recommendations = self._generate_pattern_recommendations(performance_patterns)
            recommendations.extend(pattern_recommendations)
            
            # Generate cross-cutting recommendations
            cross_recommendations = self._generate_cross_cutting_recommendations(
                performance_analytics, quality_assessments
            )
            recommendations.extend(cross_recommendations)
            
            # Remove duplicates and merge similar recommendations
            recommendations = self._deduplicate_recommendations(recommendations)
            
            # Prioritize recommendations
            recommendations = self._prioritize_recommendations(recommendations)
            
            # Calculate expected improvements
            expected_improvements = self._calculate_expected_improvements(recommendations)
            
            # Separate into quick wins and long-term goals
            quick_wins = [r for r in recommendations if r.implementation_effort == 'low' and r.timeframe in ['immediate', 'short-term']]
            long_term_goals = [r for r in recommendations if r.implementation_effort == 'high' or r.timeframe == 'long-term']
            
            # Create priority breakdown
            priority_breakdown = Counter(r.priority for r in recommendations)
            
            # Generate summary
            summary = self._generate_plan_summary(recommendations, expected_improvements)
            
            # Estimate timeline
            timeline = self._estimate_timeline(recommendations)
            
            plan_id = f"opt_plan_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            
            return OptimizationPlan(
                plan_id=plan_id,
                created_at=datetime.utcnow(),
                summary=summary,
                total_recommendations=len(recommendations),
                priority_breakdown=dict(priority_breakdown),
                expected_improvements=expected_improvements,
                estimated_timeline=timeline,
                recommendations=recommendations,
                quick_wins=quick_wins[:5],  # Top 5 quick wins
                long_term_goals=long_term_goals[:3]  # Top 3 long-term goals
            )
            
        except Exception as e:
            logger.error(f"Error generating optimization plan: {e}")
            return self._create_empty_plan()
    
    def get_targeted_recommendations(self, prompt_id: str,
                                   performance_data: Optional[PromptAnalytics] = None,
                                   quality_data: Optional[PromptQualityAssessment] = None) -> List[OptimizationRecommendation]:
        """
        Get targeted recommendations for a specific prompt.
        
        Args:
            prompt_id: Target prompt identifier
            performance_data: Performance analytics for the prompt
            quality_data: Quality assessment for the prompt
            
        Returns:
            List of targeted recommendations
        """
        try:
            recommendations = []
            
            # Performance-specific recommendations
            if performance_data:
                if performance_data.avg_latency_ms > self.thresholds['high_latency_ms']:
                    recommendations.append(self._create_latency_recommendation(prompt_id, performance_data))
                
                if performance_data.avg_cost_usd > self.thresholds['high_cost_usd']:
                    recommendations.append(self._create_cost_recommendation(prompt_id, performance_data))
                
                if performance_data.success_rate < self.thresholds['low_success_rate']:
                    recommendations.append(self._create_reliability_recommendation(prompt_id, performance_data))
            
            # Quality-specific recommendations
            if quality_data:
                if quality_data.overall_score < self.thresholds['low_quality_score']:
                    recommendations.extend(self._create_quality_recommendations(prompt_id, quality_data))
            
            # Filter and prioritize
            recommendations = [r for r in recommendations if r is not None]
            recommendations = self._prioritize_recommendations(recommendations)
            
            return recommendations[:5]  # Top 5 recommendations
            
        except Exception as e:
            logger.error(f"Error generating targeted recommendations for {prompt_id}: {e}")
            return []
    
    def _generate_performance_recommendations(self, analytics: List[PromptAnalytics],
                                            patterns: List[PerformancePattern]) -> List[OptimizationRecommendation]:
        """Generate recommendations based on performance analytics."""
        recommendations = []
        
        try:
            # High latency recommendations
            high_latency_prompts = [a for a in analytics if a.avg_latency_ms > self.thresholds['high_latency_ms']]
            if high_latency_prompts:
                rec = self._create_batch_latency_recommendation(high_latency_prompts)
                if rec:
                    recommendations.append(rec)
            
            # High cost recommendations  
            high_cost_prompts = [a for a in analytics if a.avg_cost_usd > self.thresholds['high_cost_usd']]
            if high_cost_prompts:
                rec = self._create_batch_cost_recommendation(high_cost_prompts)
                if rec:
                    recommendations.append(rec)
            
            # Low success rate recommendations
            low_success_prompts = [a for a in analytics if a.success_rate < self.thresholds['low_success_rate']]
            if low_success_prompts:
                rec = self._create_batch_reliability_recommendation(low_success_prompts)
                if rec:
                    recommendations.append(rec)
            
            # Inconsistent performance recommendations
            inconsistent_prompts = [a for a in analytics if a.p95_latency_ms > a.avg_latency_ms * 2.5]
            if inconsistent_prompts:
                rec = self._create_consistency_recommendation(inconsistent_prompts)
                if rec:
                    recommendations.append(rec)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating performance recommendations: {e}")
            return []
    
    def _generate_quality_recommendations(self, assessments: List[PromptQualityAssessment]) -> List[OptimizationRecommendation]:
        """Generate recommendations based on quality assessments."""
        recommendations = []
        
        try:
            # Low quality prompts
            low_quality_prompts = [a for a in assessments if a.overall_score < self.thresholds['low_quality_score']]
            
            if low_quality_prompts:
                # Group by common weaknesses
                weakness_groups = defaultdict(list)
                for assessment in low_quality_prompts:
                    for weakness in assessment.weaknesses:
                        weakness_groups[weakness].append(assessment.prompt_id)
                
                # Create recommendations for common issues
                for weakness, affected_prompts in weakness_groups.items():
                    if len(affected_prompts) >= 3:  # At least 3 prompts affected
                        rec = self._create_quality_improvement_recommendation(weakness, affected_prompts)
                        if rec:
                            recommendations.append(rec)
            
            # High improvement potential
            high_potential_prompts = [a for a in assessments if a.estimated_improvement_potential > 0.6]
            if high_potential_prompts:
                rec = self._create_improvement_potential_recommendation(high_potential_prompts)
                if rec:
                    recommendations.append(rec)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating quality recommendations: {e}")
            return []
    
    def _generate_model_recommendations(self, comparisons: List[ModelPerformanceComparison]) -> List[OptimizationRecommendation]:
        """Generate recommendations based on model performance comparisons."""
        recommendations = []
        
        try:
            if len(comparisons) < 2:
                return recommendations
            
            # Find best and worst performing models
            best_model = max(comparisons, key=lambda x: x.overall_score)
            worst_model = min(comparisons, key=lambda x: x.overall_score)
            
            # If there's significant performance difference, recommend switching
            if best_model.overall_score > worst_model.overall_score * 1.3:
                recommendations.append(OptimizationRecommendation(
                    recommendation_id=f"model_switch_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    category='performance',
                    priority='medium',
                    title=f'Switch from {worst_model.model_name} to {best_model.model_name}',
                    description=f'Model performance analysis shows {best_model.model_name} significantly outperforms {worst_model.model_name}',
                    rationale=f'Best model score: {best_model.overall_score:.2f}, Current worst model score: {worst_model.overall_score:.2f}',
                    expected_impact={
                        'latency_improvement': (worst_model.avg_latency - best_model.avg_latency) / worst_model.avg_latency,
                        'cost_reduction': (worst_model.avg_cost - best_model.avg_cost) / worst_model.avg_cost,
                        'success_rate_improvement': best_model.success_rate - worst_model.success_rate
                    },
                    implementation_effort='medium',
                    timeframe='short-term',
                    specific_actions=[
                        f'Test {best_model.model_name} with current prompts',
                        'Compare output quality between models',
                        f'Gradually migrate from {worst_model.model_name}',
                        'Monitor performance after migration'
                    ],
                    prerequisites=['Model testing environment', 'Quality validation process'],
                    success_metrics=['Improved response time', 'Reduced cost per request', 'Maintained output quality'],
                    confidence_score=0.8,
                    applicable_prompts=['all'],
                    tags=['model_optimization', 'performance', 'cost_efficiency']
                ))
            
            # Cost efficiency recommendations
            most_cost_efficient = min(comparisons, key=lambda x: x.avg_cost)
            if most_cost_efficient.avg_cost < statistics.mean([c.avg_cost for c in comparisons]) * 0.7:
                recommendations.append(OptimizationRecommendation(
                    recommendation_id=f"cost_efficient_model_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                    category='cost',
                    priority='medium',
                    title=f'Consider {most_cost_efficient.model_name} for Cost Optimization',
                    description=f'{most_cost_efficient.model_name} offers significant cost savings while maintaining performance',
                    rationale=f'Cost per request: ${most_cost_efficient.avg_cost:.3f} vs average ${statistics.mean([c.avg_cost for c in comparisons]):.3f}',
                    expected_impact={'cost_reduction': 0.3},
                    implementation_effort='low',
                    timeframe='immediate',
                    specific_actions=[f'Test {most_cost_efficient.model_name} for cost-sensitive operations'],
                    prerequisites=[],
                    success_metrics=['Reduced total cost'],
                    confidence_score=0.7,
                    applicable_prompts=['cost_sensitive'],
                    tags=['cost_optimization', 'model_selection']
                ))
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating model recommendations: {e}")
            return []
    
    def _generate_pattern_recommendations(self, patterns: List[PerformancePattern]) -> List[OptimizationRecommendation]:
        """Generate recommendations based on detected patterns."""
        recommendations = []
        
        try:
            for pattern in patterns:
                if pattern.pattern_type == 'high_latency_spikes':
                    recommendations.append(OptimizationRecommendation(
                        recommendation_id=f"latency_spikes_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                        category='performance',
                        priority='high',
                        title='Address Latency Spike Pattern',
                        description=pattern.pattern_description,
                        rationale=f'Detected {pattern.frequency} latency spikes affecting user experience',
                        expected_impact={'latency_improvement': 0.3},
                        implementation_effort='medium',
                        timeframe='short-term',
                        specific_actions=[
                            'Implement request timeout handling',
                            'Add circuit breaker patterns',
                            'Analyze spike triggers',
                            'Optimize prompt complexity'
                        ],
                        prerequisites=['Monitoring setup', 'Error handling framework'],
                        success_metrics=['Reduced p95 latency', 'Fewer timeouts'],
                        confidence_score=pattern.confidence_score,
                        applicable_prompts=['all'],
                        tags=['latency_optimization', 'reliability']
                    ))
                
                elif pattern.pattern_type == 'cost_inefficiency':
                    recommendations.append(OptimizationRecommendation(
                        recommendation_id=f"cost_inefficiency_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                        category='cost',
                        priority='high',
                        title='Optimize High-Cost Operations',
                        description=pattern.pattern_description,
                        rationale=f'Identified {pattern.frequency} high-cost operations draining budget',
                        expected_impact={'cost_reduction': 0.25},
                        implementation_effort='medium',
                        timeframe='immediate',
                        specific_actions=[
                            'Review high-cost prompt patterns',
                            'Implement cost monitoring',
                            'Optimize token usage',
                            'Consider alternative models'
                        ],
                        prerequisites=['Cost tracking system'],
                        success_metrics=['Reduced average cost per request', 'Lower daily spending'],
                        confidence_score=pattern.confidence_score,
                        applicable_prompts=['high_cost'],
                        tags=['cost_optimization', 'efficiency']
                    ))
                
                elif pattern.pattern_type == 'error_clustering':
                    recommendations.append(OptimizationRecommendation(
                        recommendation_id=f"error_clustering_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                        category='reliability',
                        priority='critical',
                        title='Fix Clustered Error Pattern',
                        description=pattern.pattern_description,
                        rationale=f'Pattern of {pattern.frequency} similar errors indicates systematic issue',
                        expected_impact={'success_rate_improvement': 0.15},
                        implementation_effort='high',
                        timeframe='immediate',
                        specific_actions=[
                            'Analyze error root cause',
                            'Improve prompt error handling',
                            'Add input validation',
                            'Implement retry logic'
                        ],
                        prerequisites=['Error logging system', 'Development resources'],
                        success_metrics=['Reduced error rate', 'Improved success rate'],
                        confidence_score=pattern.confidence_score,
                        applicable_prompts=['error_prone'],
                        tags=['error_handling', 'reliability', 'quality']
                    ))
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating pattern recommendations: {e}")
            return []
    
    def _generate_cross_cutting_recommendations(self, analytics: List[PromptAnalytics],
                                              assessments: List[PromptQualityAssessment]) -> List[OptimizationRecommendation]:
        """Generate cross-cutting recommendations that apply to multiple areas."""
        recommendations = []
        
        try:
            # Token optimization across all prompts
            if analytics:
                avg_cost = statistics.mean([a.avg_cost_usd for a in analytics])
                if avg_cost > self.thresholds['high_cost_usd'] * 0.7:  # Above 70% of high cost threshold
                    recommendations.append(OptimizationRecommendation(
                        recommendation_id=f"token_optimization_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                        category='efficiency',
                        priority='medium',
                        title='Implement Token Optimization Strategy',
                        description='Average prompt costs are elevated, indicating opportunity for token optimization',
                        rationale=f'Average cost per request: ${avg_cost:.3f}',
                        expected_impact={'cost_reduction': 0.20},
                        implementation_effort='low',
                        timeframe='short-term',
                        specific_actions=[
                            'Audit prompt lengths and complexity',
                            'Implement prompt compression techniques',
                            'Use more efficient instruction formats',
                            'Cache common response patterns'
                        ],
                        prerequisites=[],
                        success_metrics=['Reduced token usage', 'Lower cost per request'],
                        confidence_score=0.8,
                        applicable_prompts=['all'],
                        tags=['token_optimization', 'cost_efficiency', 'prompt_engineering']
                    ))
            
            # Quality standardization
            if assessments:
                quality_variance = statistics.stdev([a.overall_score for a in assessments]) if len(assessments) > 1 else 0
                if quality_variance > 20:  # High variance in quality scores
                    recommendations.append(OptimizationRecommendation(
                        recommendation_id=f"quality_standardization_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
                        category='quality',
                        priority='medium',
                        title='Standardize Prompt Quality Practices',
                        description='High variance in prompt quality suggests need for standardization',
                        rationale=f'Quality score variance: {quality_variance:.1f}',
                        expected_impact={'quality_improvement': 0.25},
                        implementation_effort='medium',
                        timeframe='long-term',
                        specific_actions=[
                            'Develop prompt quality guidelines',
                            'Create prompt templates',
                            'Implement peer review process',
                            'Establish quality metrics tracking'
                        ],
                        prerequisites=['Quality framework', 'Team training'],
                        success_metrics=['Reduced quality variance', 'Higher average quality scores'],
                        confidence_score=0.7,
                        applicable_prompts=['all'],
                        tags=['quality_assurance', 'standardization', 'process_improvement']
                    ))
            
            return recommendations
            
        except Exception as e:
            logger.error(f"Error generating cross-cutting recommendations: {e}")
            return []
    
    def _create_latency_recommendation(self, prompt_id: str, performance_data: PromptAnalytics) -> OptimizationRecommendation:
        """Create a latency-specific recommendation."""
        return OptimizationRecommendation(
            recommendation_id=f"latency_{prompt_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            category='performance',
            priority='high' if performance_data.avg_latency_ms > 5000 else 'medium',
            title=f'Optimize Latency for Prompt {prompt_id}',
            description=f'Current average latency of {performance_data.avg_latency_ms:.0f}ms is above recommended threshold',
            rationale=f'Target latency: <{self.thresholds["high_latency_ms"]}ms, Current: {performance_data.avg_latency_ms:.0f}ms',
            expected_impact={'latency_improvement': 0.3},
            implementation_effort='medium',
            timeframe='short-term',
            specific_actions=[
                'Reduce prompt complexity',
                'Optimize model parameters',
                'Implement response caching',
                'Consider faster model alternatives'
            ],
            prerequisites=['Performance monitoring'],
            success_metrics=[f'Latency below {self.thresholds["high_latency_ms"]}ms'],
            confidence_score=0.8,
            applicable_prompts=[prompt_id],
            tags=['latency_optimization', 'performance']
        )
    
    def _deduplicate_recommendations(self, recommendations: List[OptimizationRecommendation]) -> List[OptimizationRecommendation]:
        """Remove duplicate and merge similar recommendations."""
        try:
            # Simple deduplication based on title similarity
            unique_recommendations = []
            seen_titles = set()
            
            for rec in recommendations:
                if rec.title not in seen_titles:
                    unique_recommendations.append(rec)
                    seen_titles.add(rec.title)
            
            return unique_recommendations
            
        except Exception as e:
            logger.error(f"Error deduplicating recommendations: {e}")
            return recommendations
    
    def _prioritize_recommendations(self, recommendations: List[OptimizationRecommendation]) -> List[OptimizationRecommendation]:
        """Prioritize recommendations based on impact and effort."""
        try:
            def priority_score(rec):
                priority_values = {'critical': 4, 'high': 3, 'medium': 2, 'low': 1}
                effort_penalty = {'low': 0, 'medium': -0.2, 'high': -0.5}
                
                base_score = priority_values.get(rec.priority, 1)
                effort_adjustment = effort_penalty.get(rec.implementation_effort, 0)
                confidence_bonus = rec.confidence_score * 0.5
                
                # Calculate expected impact score
                impact_score = sum(rec.expected_impact.values()) * 0.3
                
                return base_score + effort_adjustment + confidence_bonus + impact_score
            
            return sorted(recommendations, key=priority_score, reverse=True)
            
        except Exception as e:
            logger.error(f"Error prioritizing recommendations: {e}")
            return recommendations
    
    def _calculate_expected_improvements(self, recommendations: List[OptimizationRecommendation]) -> Dict[str, float]:
        """Calculate expected improvements from implementing recommendations."""
        try:
            improvements = defaultdict(float)
            
            for rec in recommendations:
                for metric, improvement in rec.expected_impact.items():
                    improvements[metric] += improvement * rec.confidence_score
            
            # Normalize improvements (diminishing returns)
            for metric in improvements:
                improvements[metric] = min(0.8, improvements[metric])  # Cap at 80% improvement
            
            return dict(improvements)
            
        except Exception as e:
            logger.error(f"Error calculating expected improvements: {e}")
            return {}
    
    def _generate_plan_summary(self, recommendations: List[OptimizationRecommendation],
                             expected_improvements: Dict[str, float]) -> str:
        """Generate a summary of the optimization plan."""
        try:
            summary_parts = []
            
            if recommendations:
                summary_parts.append(f"Generated {len(recommendations)} optimization recommendations")
                
                # Priority distribution
                priorities = Counter(r.priority for r in recommendations)
                if priorities['critical'] > 0:
                    summary_parts.append(f"{priorities['critical']} critical issues require immediate attention")
                
                # Expected improvements
                if expected_improvements:
                    improvement_strs = []
                    for metric, improvement in expected_improvements.items():
                        if improvement > 0.1:  # Only mention significant improvements
                            improvement_strs.append(f"{improvement:.0%} {metric.replace('_', ' ')}")
                    
                    if improvement_strs:
                        summary_parts.append("Expected improvements: " + ", ".join(improvement_strs))
            
            return ". ".join(summary_parts) if summary_parts else "No significant optimization opportunities identified"
            
        except Exception as e:
            logger.error(f"Error generating plan summary: {e}")
            return "Optimization plan generated with recommendations"
    
    def _estimate_timeline(self, recommendations: List[OptimizationRecommendation]) -> str:
        """Estimate implementation timeline for the plan."""
        try:
            immediate = len([r for r in recommendations if r.timeframe == 'immediate'])
            short_term = len([r for r in recommendations if r.timeframe == 'short-term'])  
            long_term = len([r for r in recommendations if r.timeframe == 'long-term'])
            
            if immediate > 0 and short_term > 0 and long_term > 0:
                return "3-6 months (phased implementation)"
            elif immediate > 0 and short_term > 0:
                return "1-3 months"
            elif immediate > 0:
                return "2-4 weeks"
            elif short_term > 0:
                return "1-2 months"
            elif long_term > 0:
                return "3-6 months"
            else:
                return "Timeline varies"
                
        except Exception as e:
            logger.error(f"Error estimating timeline: {e}")
            return "Timeline to be determined"
    
    def _create_empty_plan(self) -> OptimizationPlan:
        """Create an empty optimization plan for error cases."""
        return OptimizationPlan(
            plan_id="empty_plan",
            created_at=datetime.utcnow(),
            summary="Unable to generate optimization plan",
            total_recommendations=0,
            priority_breakdown={},
            expected_improvements={},
            estimated_timeline="N/A",
            recommendations=[],
            quick_wins=[],
            long_term_goals=[]
        )
    
    def _initialize_templates(self) -> Dict[str, Any]:
        """Initialize recommendation templates."""
        return {
            'latency_optimization': {
                'category': 'performance',
                'specific_actions': [
                    'Reduce prompt complexity',
                    'Optimize model parameters',
                    'Implement response caching',
                    'Consider faster model alternatives'
                ]
            },
            'cost_optimization': {
                'category': 'cost',
                'specific_actions': [
                    'Optimize token usage',
                    'Use more efficient models',
                    'Implement smart caching',
                    'Reduce unnecessary prompt elements'
                ]
            },
            'quality_improvement': {
                'category': 'quality',
                'specific_actions': [
                    'Improve prompt clarity',
                    'Add specific examples',
                    'Enhance structure and formatting',
                    'Include error handling instructions'
                ]
            }
        }
    
    # Helper methods for creating specific recommendation types
    def _create_batch_latency_recommendation(self, prompts: List[PromptAnalytics]) -> Optional[OptimizationRecommendation]:
        """Create recommendation for multiple high-latency prompts."""
        if not prompts:
            return None
            
        avg_latency = statistics.mean([p.avg_latency_ms for p in prompts])
        prompt_ids = [p.prompt_id for p in prompts]
        
        return OptimizationRecommendation(
            recommendation_id=f"batch_latency_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            category='performance',
            priority='high',
            title=f'Optimize Latency for {len(prompts)} High-Latency Prompts',
            description=f'Multiple prompts showing high latency (avg: {avg_latency:.0f}ms)',
            rationale=f'{len(prompts)} prompts exceed {self.thresholds["high_latency_ms"]}ms threshold',
            expected_impact={'latency_improvement': 0.35},
            implementation_effort='medium',
            timeframe='short-term',
            specific_actions=[
                'Analyze common patterns in slow prompts',
                'Implement batch optimization techniques',
                'Consider model parameter tuning',
                'Add performance monitoring'
            ],
            prerequisites=['Performance analysis tools'],
            success_metrics=['Reduced average latency across affected prompts'],
            confidence_score=0.8,
            applicable_prompts=prompt_ids,
            tags=['batch_optimization', 'latency', 'performance']
        )
    
    def _create_batch_cost_recommendation(self, prompts: List[PromptAnalytics]) -> Optional[OptimizationRecommendation]:
        """Create recommendation for multiple high-cost prompts."""
        if not prompts:
            return None
            
        avg_cost = statistics.mean([p.avg_cost_usd for p in prompts])
        total_executions = sum([p.total_executions for p in prompts])
        prompt_ids = [p.prompt_id for p in prompts]
        
        return OptimizationRecommendation(
            recommendation_id=f"batch_cost_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            category='cost',
            priority='high',
            title=f'Reduce Costs for {len(prompts)} Expensive Prompts',
            description=f'High-cost prompts consuming significant budget (avg: ${avg_cost:.3f}/request)',
            rationale=f'{len(prompts)} prompts with {total_executions} total executions above cost threshold',
            expected_impact={'cost_reduction': 0.30},
            implementation_effort='medium',
            timeframe='immediate',
            specific_actions=[
                'Analyze token usage patterns',
                'Implement prompt compression',
                'Test alternative models',
                'Add cost monitoring and alerts'
            ],
            prerequisites=['Cost tracking system'],
            success_metrics=['Reduced cost per request', 'Lower total daily spending'],
            confidence_score=0.85,
            applicable_prompts=prompt_ids,
            tags=['cost_optimization', 'batch_optimization', 'efficiency']
        )
    
    def _create_batch_reliability_recommendation(self, prompts: List[PromptAnalytics]) -> Optional[OptimizationRecommendation]:
        """Create recommendation for multiple low-reliability prompts."""
        if not prompts:
            return None
            
        avg_success_rate = statistics.mean([p.success_rate for p in prompts])
        prompt_ids = [p.prompt_id for p in prompts]
        
        return OptimizationRecommendation(
            recommendation_id=f"batch_reliability_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            category='reliability',
            priority='critical',
            title=f'Improve Reliability for {len(prompts)} Low-Success Prompts',
            description=f'Multiple prompts with poor success rates (avg: {avg_success_rate:.1%})',
            rationale=f'{len(prompts)} prompts below {self.thresholds["low_success_rate"]:.0%} success rate',
            expected_impact={'success_rate_improvement': 0.20},
            implementation_effort='high',
            timeframe='short-term',
            specific_actions=[
                'Analyze failure patterns and root causes',
                'Improve error handling in prompts',
                'Add input validation and constraints',
                'Implement retry mechanisms'
            ],
            prerequisites=['Error analysis tools', 'Development resources'],
            success_metrics=['Improved success rates', 'Reduced error frequency'],
            confidence_score=0.9,
            applicable_prompts=prompt_ids,
            tags=['reliability', 'error_handling', 'quality']
        )
    
    def _create_consistency_recommendation(self, prompts: List[PromptAnalytics]) -> Optional[OptimizationRecommendation]:
        """Create recommendation for inconsistent performance prompts."""
        if not prompts:
            return None
            
        prompt_ids = [p.prompt_id for p in prompts]
        
        return OptimizationRecommendation(
            recommendation_id=f"consistency_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            category='performance',
            priority='medium',
            title=f'Improve Consistency for {len(prompts)} Variable-Performance Prompts',
            description='Prompts showing high variability in response times',
            rationale=f'{len(prompts)} prompts with high P95/average latency ratios',
            expected_impact={'latency_improvement': 0.15},
            implementation_effort='medium',
            timeframe='short-term',
            specific_actions=[
                'Identify sources of variability',
                'Standardize prompt complexity',
                'Implement consistent model parameters',
                'Add performance variance monitoring'
            ],
            prerequisites=['Performance monitoring'],
            success_metrics=['Reduced latency variance', 'More predictable response times'],
            confidence_score=0.7,
            applicable_prompts=prompt_ids,
            tags=['consistency', 'performance', 'standardization']
        )
    
    def _create_quality_improvement_recommendation(self, weakness: str, affected_prompts: List[str]) -> Optional[OptimizationRecommendation]:
        """Create recommendation for common quality issues."""
        return OptimizationRecommendation(
            recommendation_id=f"quality_{weakness.replace(' ', '_')}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            category='quality',
            priority='medium',
            title=f'Address Common Quality Issue: {weakness}',
            description=f'Multiple prompts affected by {weakness}',
            rationale=f'{len(affected_prompts)} prompts show this quality issue',
            expected_impact={'quality_improvement': 0.20},
            implementation_effort='low',
            timeframe='short-term',
            specific_actions=[
                f'Review and improve {weakness.lower()}',
                'Apply quality guidelines consistently',
                'Test improvements with sample prompts',
                'Monitor quality metrics after changes'
            ],
            prerequisites=['Quality guidelines'],
            success_metrics=['Improved quality scores', 'Reduced common weaknesses'],
            confidence_score=0.7,
            applicable_prompts=affected_prompts,
            tags=['quality', 'standardization', weakness.replace(' ', '_').lower()]
        )
    
    def _create_improvement_potential_recommendation(self, prompts: List[PromptQualityAssessment]) -> Optional[OptimizationRecommendation]:
        """Create recommendation for high improvement potential prompts."""
        if not prompts:
            return None
            
        prompt_ids = [p.prompt_id for p in prompts]
        avg_potential = statistics.mean([p.estimated_improvement_potential for p in prompts])
        
        return OptimizationRecommendation(
            recommendation_id=f"improvement_potential_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}",
            category='quality',
            priority='high',
            title=f'High-Impact Quality Improvements for {len(prompts)} Prompts',
            description=f'Prompts with high improvement potential (avg: {avg_potential:.1%})',
            rationale=f'{len(prompts)} prompts identified as having significant improvement opportunities',
            expected_impact={'quality_improvement': 0.40},
            implementation_effort='medium',
            timeframe='short-term',
            specific_actions=[
                'Prioritize high-potential prompts for improvement',
                'Apply comprehensive quality enhancements',
                'Measure before/after quality scores',
                'Document successful improvement patterns'
            ],
            prerequisites=['Quality assessment tools'],
            success_metrics=['Increased quality scores', 'Realized improvement potential'],
            confidence_score=0.8,
            applicable_prompts=prompt_ids,
            tags=['high_impact', 'quality_improvement', 'optimization']
        )