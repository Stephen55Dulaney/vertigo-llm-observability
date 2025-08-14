"""
ML Optimization Service - Main Coordinator
Coordinates ML-based prompt performance analysis, quality scoring, and optimization recommendations.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import asdict
import json

from .performance_analyzer import PromptPerformanceAnalyzer, PromptAnalytics, PerformancePattern
from .quality_scorer import PromptQualityScorer, PromptQualityAssessment
from .recommendation_engine import OptimizationRecommendationEngine, OptimizationPlan, OptimizationRecommendation

from app.services.live_data_service import live_data_service
from app.models import db
from sqlalchemy import text

logger = logging.getLogger(__name__)


class MLOptimizationService:
    """
    Main ML optimization service that coordinates all ML-based optimization components.
    
    Provides a unified interface for:
    - Performance analysis
    - Quality assessment  
    - Optimization recommendations
    - ML insights generation
    """
    
    def __init__(self):
        """Initialize the ML optimization service."""
        self.performance_analyzer = PromptPerformanceAnalyzer()
        self.quality_scorer = PromptQualityScorer()
        self.recommendation_engine = OptimizationRecommendationEngine()
        
        # Cache settings
        self.cache_ttl_seconds = 300  # 5 minutes
        self._cache = {}
        self._cache_timestamps = {}
        
        logger.info("MLOptimizationService initialized with all components")
    
    def generate_comprehensive_analysis(self, days_back: int = 30, 
                                      include_quality: bool = True,
                                      include_recommendations: bool = True) -> Dict[str, Any]:
        """
        Generate comprehensive ML-based analysis of prompt performance.
        
        Args:
            days_back: Number of days to analyze
            include_quality: Whether to include quality assessments
            include_recommendations: Whether to generate recommendations
            
        Returns:
            Complete analysis results
        """
        try:
            cache_key = f"comprehensive_analysis_{days_back}_{include_quality}_{include_recommendations}"
            
            # Check cache
            if self._is_cached(cache_key):
                logger.info("Returning cached comprehensive analysis")
                return self._cache[cache_key]
            
            logger.info(f"Starting comprehensive ML analysis for {days_back} days")
            analysis_start = datetime.utcnow()
            
            # 1. Performance Analysis
            logger.info("Analyzing prompt performance patterns...")
            performance_analytics = self.performance_analyzer.analyze_prompt_performance(
                prompt_id=None, days_back=days_back
            )
            
            performance_patterns = self.performance_analyzer.detect_performance_patterns(days_back)
            model_comparisons = self.performance_analyzer.compare_model_performance(days_back)
            optimization_potential = self.performance_analyzer.calculate_optimization_potential(performance_analytics)
            
            # 2. Quality Analysis (if requested)
            quality_assessments = []
            quality_insights = {}
            
            if include_quality:
                logger.info("Performing quality assessments...")
                
                # Get prompts with performance data for quality analysis
                prompts_for_quality = []
                for analytics in performance_analytics:
                    if analytics.total_executions >= 5:  # Only assess prompts with sufficient data
                        prompts_for_quality.append({
                            'id': analytics.prompt_id,
                            'text': analytics.prompt_text,
                            'performance_data': {
                                'avg_latency_ms': analytics.avg_latency_ms,
                                'avg_cost_usd': analytics.avg_cost_usd,
                                'success_rate': analytics.success_rate,
                                'p95_latency_ms': analytics.p95_latency_ms,
                                'total_executions': analytics.total_executions
                            }
                        })
                
                quality_assessments = self.quality_scorer.batch_assess_prompts(prompts_for_quality)
                quality_insights = self.quality_scorer.get_quality_insights(quality_assessments)
            
            # 3. Optimization Recommendations (if requested)
            optimization_plan = None
            
            if include_recommendations:
                logger.info("Generating optimization recommendations...")
                optimization_plan = self.recommendation_engine.generate_optimization_plan(
                    performance_analytics=performance_analytics,
                    quality_assessments=quality_assessments,
                    performance_patterns=performance_patterns,
                    model_comparisons=model_comparisons
                )
            
            # 4. Generate ML insights summary
            ml_insights = self._generate_ml_insights(
                performance_analytics, quality_assessments, performance_patterns, model_comparisons
            )
            
            analysis_duration = (datetime.utcnow() - analysis_start).total_seconds()
            logger.info(f"Comprehensive analysis completed in {analysis_duration:.2f} seconds")
            
            # Compile results
            results = {
                'analysis_metadata': {
                    'generated_at': datetime.utcnow().isoformat(),
                    'analysis_period_days': days_back,
                    'duration_seconds': analysis_duration,
                    'included_quality': include_quality,
                    'included_recommendations': include_recommendations
                },
                'performance_analysis': {
                    'prompt_analytics': [asdict(p) for p in performance_analytics],
                    'patterns_detected': [asdict(p) for p in performance_patterns],
                    'model_comparisons': [asdict(m) for m in model_comparisons],
                    'optimization_potential': optimization_potential
                },
                'quality_analysis': {
                    'assessments': [asdict(q) for q in quality_assessments],
                    'insights': quality_insights
                } if include_quality else None,
                'optimization_plan': asdict(optimization_plan) if optimization_plan else None,
                'ml_insights': ml_insights,
                'summary': self._generate_analysis_summary(
                    performance_analytics, quality_assessments, performance_patterns, optimization_plan
                )
            }
            
            # Cache results
            self._cache_result(cache_key, results)
            
            return results
            
        except Exception as e:
            logger.error(f"Error in comprehensive analysis: {e}")
            return {
                'error': str(e),
                'analysis_metadata': {
                    'generated_at': datetime.utcnow().isoformat(),
                    'status': 'error'
                }
            }
    
    def analyze_specific_prompt(self, prompt_id: str, prompt_text: str = None,
                               days_back: int = 30) -> Dict[str, Any]:
        """
        Analyze a specific prompt in detail.
        
        Args:
            prompt_id: Prompt identifier
            prompt_text: Optional prompt text for quality analysis
            days_back: Number of days to analyze
            
        Returns:
            Detailed prompt analysis
        """
        try:
            logger.info(f"Analyzing specific prompt: {prompt_id}")
            
            # Performance analysis
            performance_analytics = self.performance_analyzer.analyze_prompt_performance(
                prompt_id=prompt_id, days_back=days_back
            )
            
            performance_data = performance_analytics[0] if performance_analytics else None
            
            # Quality assessment (if prompt text available)
            quality_assessment = None
            if prompt_text:
                perf_data = {
                    'avg_latency_ms': performance_data.avg_latency_ms,
                    'avg_cost_usd': performance_data.avg_cost_usd,
                    'success_rate': performance_data.success_rate,
                    'p95_latency_ms': performance_data.p95_latency_ms
                } if performance_data else None
                
                quality_assessment = self.quality_scorer.assess_prompt_quality(
                    prompt_text=prompt_text,
                    prompt_id=prompt_id,
                    performance_data=perf_data
                )
            
            # Targeted recommendations
            recommendations = self.recommendation_engine.get_targeted_recommendations(
                prompt_id=prompt_id,
                performance_data=performance_data,
                quality_data=quality_assessment
            )
            
            return {
                'prompt_id': prompt_id,
                'analysis_timestamp': datetime.utcnow().isoformat(),
                'performance_analysis': asdict(performance_data) if performance_data else None,
                'quality_assessment': asdict(quality_assessment) if quality_assessment else None,
                'recommendations': [asdict(r) for r in recommendations],
                'optimization_score': self._calculate_prompt_optimization_score(
                    performance_data, quality_assessment
                )
            }
            
        except Exception as e:
            logger.error(f"Error analyzing prompt {prompt_id}: {e}")
            return {'error': str(e), 'prompt_id': prompt_id}
    
    def get_ml_insights_dashboard(self) -> Dict[str, Any]:
        """
        Get ML insights optimized for dashboard display.
        
        Returns:
            Dashboard-ready ML insights
        """
        try:
            cache_key = "ml_insights_dashboard"
            
            if self._is_cached(cache_key):
                return self._cache[cache_key]
            
            logger.info("Generating ML insights dashboard")
            
            # Get recent data for dashboard
            performance_analytics = self.performance_analyzer.analyze_prompt_performance(days_back=7)
            patterns = self.performance_analyzer.detect_performance_patterns(days_back=7)
            
            # Dashboard metrics
            dashboard_data = {
                'overview': {
                    'total_prompts_analyzed': len(performance_analytics),
                    'patterns_detected': len(patterns),
                    'analysis_timestamp': datetime.utcnow().isoformat()
                },
                'top_insights': [
                    {
                        'type': 'performance',
                        'title': 'High-Impact Optimization Opportunities',
                        'value': len([p for p in performance_analytics if p.optimization_potential > 0.6]),
                        'trend': 'up',
                        'description': 'Prompts with significant optimization potential'
                    },
                    {
                        'type': 'patterns',
                        'title': 'Performance Patterns Detected',
                        'value': len(patterns),
                        'trend': 'stable',
                        'description': 'Automated pattern detection in prompt performance'
                    }
                ],
                'performance_distribution': self._get_performance_distribution(performance_analytics),
                'optimization_opportunities': self._get_optimization_opportunities(performance_analytics),
                'recent_patterns': [
                    {
                        'type': p.pattern_type,
                        'description': p.pattern_description[:100] + '...',
                        'confidence': p.confidence_score,
                        'frequency': p.frequency
                    }
                    for p in patterns[:5]  # Top 5 patterns
                ],
                'recommendations_preview': self._get_recommendations_preview(performance_analytics)
            }
            
            self._cache_result(cache_key, dashboard_data)
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error generating ML insights dashboard: {e}")
            return {'error': str(e)}
    
    def get_model_optimization_insights(self) -> Dict[str, Any]:
        """
        Get model-specific optimization insights.
        
        Returns:
            Model optimization recommendations
        """
        try:
            model_comparisons = self.performance_analyzer.compare_model_performance(days_back=14)
            
            if not model_comparisons:
                return {'message': 'Insufficient data for model optimization insights'}
            
            # Find best performing model
            best_model = max(model_comparisons, key=lambda x: x.overall_score)
            
            # Calculate potential savings from model optimization
            model_insights = {
                'best_performing_model': {
                    'name': best_model.model_name,
                    'overall_score': best_model.overall_score,
                    'avg_latency': best_model.avg_latency,
                    'avg_cost': best_model.avg_cost,
                    'success_rate': best_model.success_rate
                },
                'model_comparisons': [asdict(m) for m in model_comparisons],
                'optimization_recommendations': []
            }
            
            # Generate model-specific recommendations
            for comparison in model_comparisons:
                if comparison.overall_score < best_model.overall_score * 0.8:
                    model_insights['optimization_recommendations'].append({
                        'current_model': comparison.model_name,
                        'recommended_model': best_model.model_name,
                        'expected_improvement': {
                            'latency_reduction_pct': ((comparison.avg_latency - best_model.avg_latency) / comparison.avg_latency) * 100,
                            'cost_reduction_pct': ((comparison.avg_cost - best_model.avg_cost) / comparison.avg_cost) * 100,
                            'success_rate_improvement': best_model.success_rate - comparison.success_rate
                        }
                    })
            
            return model_insights
            
        except Exception as e:
            logger.error(f"Error generating model optimization insights: {e}")
            return {'error': str(e)}
    
    def generate_quality_report(self, prompts: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Generate a comprehensive quality report for given prompts.
        
        Args:
            prompts: List of prompt dictionaries with 'id' and 'text' keys
            
        Returns:
            Quality report
        """
        try:
            logger.info(f"Generating quality report for {len(prompts)} prompts")
            
            # Assess quality for all prompts
            assessments = self.quality_scorer.batch_assess_prompts(prompts)
            insights = self.quality_scorer.get_quality_insights(assessments)
            
            # Generate improvement recommendations for low-quality prompts
            low_quality_prompts = [a for a in assessments if a.overall_score < 60]
            improvement_recommendations = []
            
            for assessment in low_quality_prompts[:10]:  # Top 10 for improvement
                recommendations = self.recommendation_engine.get_targeted_recommendations(
                    prompt_id=assessment.prompt_id,
                    quality_data=assessment
                )
                improvement_recommendations.extend(recommendations)
            
            return {
                'report_metadata': {
                    'generated_at': datetime.utcnow().isoformat(),
                    'prompts_analyzed': len(prompts),
                    'assessments_completed': len(assessments)
                },
                'quality_assessments': [asdict(a) for a in assessments],
                'insights': insights,
                'improvement_recommendations': [asdict(r) for r in improvement_recommendations],
                'summary': {
                    'average_quality_score': insights.get('summary', {}).get('average_quality_score', 0),
                    'prompts_needing_improvement': len(low_quality_prompts),
                    'high_potential_improvements': len([a for a in assessments if a.estimated_improvement_potential > 0.6]),
                    'recommendations_generated': len(improvement_recommendations)
                }
            }
            
        except Exception as e:
            logger.error(f"Error generating quality report: {e}")
            return {'error': str(e)}
    
    def _generate_ml_insights(self, performance_analytics: List[PromptAnalytics],
                             quality_assessments: List[PromptQualityAssessment],
                             patterns: List[PerformancePattern],
                             model_comparisons: List) -> Dict[str, Any]:
        """Generate high-level ML insights."""
        try:
            insights = {
                'key_findings': [],
                'optimization_opportunities': [],
                'performance_trends': {},
                'quality_trends': {},
                'actionable_insights': []
            }
            
            # Performance insights
            if performance_analytics:
                avg_latency = sum(p.avg_latency_ms for p in performance_analytics) / len(performance_analytics)
                avg_cost = sum(p.avg_cost_usd for p in performance_analytics) / len(performance_analytics)
                avg_success = sum(p.success_rate for p in performance_analytics) / len(performance_analytics)
                
                insights['performance_trends'] = {
                    'average_latency_ms': avg_latency,
                    'average_cost_usd': avg_cost,
                    'average_success_rate': avg_success,
                    'high_optimization_potential': len([p for p in performance_analytics if p.optimization_potential > 0.6])
                }
                
                # Key findings
                if avg_latency > 3000:
                    insights['key_findings'].append("Average prompt latency is high - optimization needed")
                
                if avg_cost > 0.20:
                    insights['key_findings'].append("Average prompt costs are elevated - cost optimization recommended")
                
                if avg_success < 0.90:
                    insights['key_findings'].append("Success rate below target - reliability improvements needed")
            
            # Quality insights
            if quality_assessments:
                avg_quality = sum(q.overall_score for q in quality_assessments) / len(quality_assessments)
                
                insights['quality_trends'] = {
                    'average_quality_score': avg_quality,
                    'high_quality_prompts': len([q for q in quality_assessments if q.overall_score >= 80]),
                    'improvement_candidates': len([q for q in quality_assessments if q.estimated_improvement_potential > 0.5])
                }
                
                if avg_quality < 70:
                    insights['key_findings'].append("Overall prompt quality below target - systematic improvements needed")
            
            # Pattern insights
            if patterns:
                pattern_types = [p.pattern_type for p in patterns]
                most_common_pattern = max(set(pattern_types), key=pattern_types.count) if pattern_types else None
                
                if most_common_pattern:
                    insights['key_findings'].append(f"Most common performance issue: {most_common_pattern}")
            
            # Generate actionable insights
            if performance_analytics and quality_assessments:
                # Cross-reference performance and quality
                perf_quality_correlation = self._analyze_performance_quality_correlation(
                    performance_analytics, quality_assessments
                )
                
                if perf_quality_correlation['correlation'] > 0.3:
                    insights['actionable_insights'].append(
                        "Strong correlation between prompt quality and performance - quality improvements will boost performance"
                    )
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating ML insights: {e}")
            return {'error': str(e)}
    
    def _calculate_prompt_optimization_score(self, performance_data: Optional[PromptAnalytics],
                                           quality_data: Optional[PromptQualityAssessment]) -> float:
        """Calculate composite optimization score for a prompt."""
        try:
            if not performance_data and not quality_data:
                return 0.0
            
            scores = []
            
            if performance_data:
                # Performance contribution (0-100)
                perf_score = (1 - performance_data.optimization_potential) * 100
                scores.append(perf_score)
            
            if quality_data:
                # Quality contribution (0-100)
                quality_score = quality_data.overall_score
                scores.append(quality_score)
            
            return sum(scores) / len(scores) if scores else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating optimization score: {e}")
            return 0.0
    
    def _get_performance_distribution(self, analytics: List[PromptAnalytics]) -> Dict[str, int]:
        """Get distribution of performance scores."""
        try:
            if not analytics:
                return {}
            
            distribution = {'excellent': 0, 'good': 0, 'fair': 0, 'poor': 0}
            
            for analytic in analytics:
                # Calculate performance score based on multiple factors
                perf_score = (1 - analytic.optimization_potential) * 100
                
                if perf_score >= 85:
                    distribution['excellent'] += 1
                elif perf_score >= 70:
                    distribution['good'] += 1
                elif perf_score >= 50:
                    distribution['fair'] += 1
                else:
                    distribution['poor'] += 1
            
            return distribution
            
        except Exception as e:
            logger.error(f"Error getting performance distribution: {e}")
            return {}
    
    def _get_optimization_opportunities(self, analytics: List[PromptAnalytics]) -> List[Dict[str, Any]]:
        """Get top optimization opportunities."""
        try:
            # Sort by optimization potential
            sorted_analytics = sorted(analytics, key=lambda x: x.optimization_potential, reverse=True)
            
            opportunities = []
            for analytic in sorted_analytics[:5]:  # Top 5 opportunities
                opportunities.append({
                    'prompt_id': analytic.prompt_id,
                    'optimization_potential': analytic.optimization_potential,
                    'current_latency_ms': analytic.avg_latency_ms,
                    'current_cost_usd': analytic.avg_cost_usd,
                    'success_rate': analytic.success_rate,
                    'total_executions': analytic.total_executions
                })
            
            return opportunities
            
        except Exception as e:
            logger.error(f"Error getting optimization opportunities: {e}")
            return []
    
    def _get_recommendations_preview(self, analytics: List[PromptAnalytics]) -> List[Dict[str, str]]:
        """Get preview of key recommendations."""
        try:
            previews = []
            
            # High latency prompts
            high_latency = [a for a in analytics if a.avg_latency_ms > 3000]
            if high_latency:
                previews.append({
                    'type': 'latency',
                    'title': 'Latency Optimization',
                    'description': f'{len(high_latency)} prompts with high latency detected',
                    'impact': 'high'
                })
            
            # High cost prompts
            high_cost = [a for a in analytics if a.avg_cost_usd > 0.20]
            if high_cost:
                previews.append({
                    'type': 'cost',
                    'title': 'Cost Reduction',
                    'description': f'{len(high_cost)} expensive prompts identified',
                    'impact': 'high'
                })
            
            # Low success rate prompts
            low_success = [a for a in analytics if a.success_rate < 0.85]
            if low_success:
                previews.append({
                    'type': 'reliability',
                    'title': 'Reliability Improvement',
                    'description': f'{len(low_success)} prompts with low success rates',
                    'impact': 'critical'
                })
            
            return previews[:3]  # Top 3 previews
            
        except Exception as e:
            logger.error(f"Error generating recommendations preview: {e}")
            return []
    
    def _analyze_performance_quality_correlation(self, performance_analytics: List[PromptAnalytics],
                                               quality_assessments: List[PromptQualityAssessment]) -> Dict[str, Any]:
        """Analyze correlation between performance and quality scores."""
        try:
            # Match performance and quality data by prompt_id
            matched_data = []
            
            for perf in performance_analytics:
                for qual in quality_assessments:
                    if perf.prompt_id == qual.prompt_id:
                        perf_score = (1 - perf.optimization_potential) * 100
                        matched_data.append({
                            'performance_score': perf_score,
                            'quality_score': qual.overall_score
                        })
                        break
            
            if len(matched_data) < 3:
                return {'correlation': 0, 'message': 'Insufficient matched data'}
            
            # Simple correlation calculation
            perf_scores = [d['performance_score'] for d in matched_data]
            qual_scores = [d['quality_score'] for d in matched_data]
            
            # Calculate Pearson correlation coefficient
            n = len(matched_data)
            sum_perf = sum(perf_scores)
            sum_qual = sum(qual_scores)
            sum_perf_qual = sum(p * q for p, q in zip(perf_scores, qual_scores))
            sum_perf_sq = sum(p * p for p in perf_scores)
            sum_qual_sq = sum(q * q for q in qual_scores)
            
            numerator = n * sum_perf_qual - sum_perf * sum_qual
            denominator = ((n * sum_perf_sq - sum_perf * sum_perf) * (n * sum_qual_sq - sum_qual * sum_qual)) ** 0.5
            
            correlation = numerator / denominator if denominator != 0 else 0
            
            return {
                'correlation': correlation,
                'sample_size': n,
                'interpretation': 'strong' if abs(correlation) > 0.7 else 'moderate' if abs(correlation) > 0.3 else 'weak'
            }
            
        except Exception as e:
            logger.error(f"Error analyzing performance-quality correlation: {e}")
            return {'correlation': 0, 'error': str(e)}
    
    def _generate_analysis_summary(self, performance_analytics: List[PromptAnalytics],
                                 quality_assessments: List[PromptQualityAssessment],
                                 patterns: List[PerformancePattern],
                                 optimization_plan: Optional[OptimizationPlan]) -> Dict[str, Any]:
        """Generate high-level analysis summary."""
        try:
            summary = {
                'prompts_analyzed': len(performance_analytics),
                'patterns_detected': len(patterns),
                'quality_assessments': len(quality_assessments),
                'key_metrics': {},
                'top_recommendations': [],
                'overall_health_score': 75.0  # Default
            }
            
            # Key metrics
            if performance_analytics:
                summary['key_metrics'] = {
                    'avg_latency_ms': sum(p.avg_latency_ms for p in performance_analytics) / len(performance_analytics),
                    'avg_cost_usd': sum(p.avg_cost_usd for p in performance_analytics) / len(performance_analytics),
                    'avg_success_rate': sum(p.success_rate for p in performance_analytics) / len(performance_analytics),
                    'high_optimization_potential': len([p for p in performance_analytics if p.optimization_potential > 0.6])
                }
            
            # Top recommendations
            if optimization_plan and optimization_plan.recommendations:
                summary['top_recommendations'] = [
                    {
                        'title': rec.title,
                        'priority': rec.priority,
                        'category': rec.category
                    }
                    for rec in optimization_plan.recommendations[:3]
                ]
            
            # Calculate overall health score
            if performance_analytics and quality_assessments:
                avg_perf_score = sum((1 - p.optimization_potential) * 100 for p in performance_analytics) / len(performance_analytics)
                avg_quality_score = sum(q.overall_score for q in quality_assessments) / len(quality_assessments)
                summary['overall_health_score'] = (avg_perf_score + avg_quality_score) / 2
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating analysis summary: {e}")
            return {'error': str(e)}
    
    def _is_cached(self, key: str) -> bool:
        """Check if result is cached and still valid."""
        if key not in self._cache:
            return False
        
        cache_time = self._cache_timestamps.get(key, datetime.min)
        return (datetime.utcnow() - cache_time).total_seconds() < self.cache_ttl_seconds
    
    def _cache_result(self, key: str, result: Any) -> None:
        """Cache a result with timestamp."""
        self._cache[key] = result
        self._cache_timestamps[key] = datetime.utcnow()
        
        # Simple cache cleanup - remove old entries
        if len(self._cache) > 100:  # Max cache size
            oldest_key = min(self._cache_timestamps.keys(), key=lambda k: self._cache_timestamps[k])
            del self._cache[oldest_key]
            del self._cache_timestamps[oldest_key]


# Global service instance
ml_optimization_service = MLOptimizationService()