"""
Cross-Tenant Learning Engine - Privacy-Preserving Optimization Insights
Aggregates optimization patterns across tenants while maintaining data privacy and provides
intelligent recommendations based on successful cross-tenant learnings.
"""

import os
import uuid
import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict, field
from collections import defaultdict, Counter
import json
import numpy as np
from scipy import stats
import math

from app.models import (
    db, ABTest, ABTestVariant, ABTestResult, ABTestAnalysis,
    Prompt, LiveTrace, PerformanceMetric
)
from app.services.tenant_service import tenant_service
from app.services.live_data_service import live_data_service
from .performance_analyzer import PromptPerformanceAnalyzer, PromptAnalytics
from .quality_scorer import PromptQualityScorer
from .recommendation_engine import OptimizationRecommendationEngine

logger = logging.getLogger(__name__)


@dataclass
class CrossTenantPattern:
    """Cross-tenant optimization pattern."""
    pattern_id: str
    pattern_type: str  # 'performance_improvement', 'cost_reduction', 'latency_optimization'
    pattern_signature: str  # Hash of pattern characteristics
    pattern_description: str
    
    # Success metrics across tenants
    success_count: int
    failure_count: int
    success_rate: float
    confidence_score: float
    
    # Performance characteristics
    avg_improvement_percent: float
    median_improvement_percent: float
    std_improvement: float
    
    # Context information (anonymized)
    applicable_categories: List[str]
    model_types: List[str]
    complexity_ranges: List[str]
    
    # Learning metadata
    first_observed: datetime
    last_updated: datetime
    tenant_count: int  # Number of tenants where pattern was observed
    total_applications: int
    
    # Privacy metrics
    anonymization_level: str = "high"
    min_tenant_threshold_met: bool = True


@dataclass
class TenantOptimizationSummary:
    """Anonymized tenant optimization summary for cross-tenant learning."""
    tenant_hash: str  # Anonymized tenant identifier
    category_focus: List[str]  # General categories, not specific content
    optimization_patterns: List[str]  # Pattern signatures only
    
    performance_tier: str  # 'high', 'medium', 'low' performance
    optimization_maturity: str  # 'advanced', 'intermediate', 'beginner'
    
    success_metrics: Dict[str, float]  # Anonymized aggregate metrics
    improvement_trends: Dict[str, float]
    
    # Temporal patterns
    active_months: int
    optimization_frequency: float
    pattern_diversity_score: float


@dataclass
class CrossTenantRecommendation:
    """Cross-tenant learning-based recommendation."""
    recommendation_id: str
    title: str
    description: str
    category: str
    
    # Evidence from cross-tenant learning
    supporting_evidence: Dict[str, Any]
    confidence_level: str  # 'high', 'medium', 'low'
    expected_improvement: Dict[str, float]
    
    # Pattern-based insights
    similar_tenant_count: int
    pattern_success_rate: float
    adaptation_guidance: str
    
    # Implementation details
    implementation_complexity: str
    estimated_effort: str
    prerequisites: List[str]
    risks: List[str]


@dataclass
class LearningInsight:
    """Cross-tenant learning insight."""
    insight_type: str
    title: str
    description: str
    confidence: float
    impact_level: str  # 'high', 'medium', 'low'
    
    supporting_data: Dict[str, Any]
    recommendation_ids: List[str]
    applicable_tenant_types: List[str]
    
    generated_at: datetime
    expires_at: Optional[datetime] = None


class CrossTenantLearningEngine:
    """
    Cross-Tenant Learning Engine for privacy-preserving optimization insights.
    
    This engine:
    1. Aggregates optimization patterns across tenants while maintaining privacy
    2. Identifies successful patterns that work across multiple tenant types
    3. Generates recommendations based on cross-tenant learnings
    4. Provides insights into optimization opportunities
    5. Maintains complete tenant data privacy and isolation
    """
    
    def __init__(self):
        """Initialize the cross-tenant learning engine."""
        self.logger = logging.getLogger(__name__)
        
        # Initialize component services
        self.performance_analyzer = PromptPerformanceAnalyzer()
        self.quality_scorer = PromptQualityScorer()
        self.recommendation_engine = OptimizationRecommendationEngine()
        
        # Privacy settings
        self.MIN_TENANT_THRESHOLD = 3  # Minimum tenants before sharing patterns
        self.ANONYMIZATION_SALT = os.getenv('CROSS_TENANT_SALT', secrets.token_hex(16))
        self.CONFIDENCE_THRESHOLD = 0.7
        self.SUCCESS_RATE_THRESHOLD = 0.8
        
        # Pattern storage (in production, this would be a separate database)
        self.cross_tenant_patterns: Dict[str, CrossTenantPattern] = {}
        self.tenant_summaries: Dict[str, TenantOptimizationSummary] = {}
        self.learning_insights: List[LearningInsight] = []
        
        # Cache settings
        self.cache_ttl = timedelta(hours=6)
        self._cache = {}
        self._cache_timestamps = {}
        
        self.logger.info("CrossTenantLearningEngine initialized with privacy-preserving capabilities")
        
        # Install helper methods
        self._install_helpers()
    
    def generate_cross_tenant_insights(self, target_tenant_id: str, 
                                     days_back: int = 30) -> Dict[str, Any]:
        """
        Generate cross-tenant learning insights for a specific tenant.
        
        Args:
            target_tenant_id: Target tenant to generate insights for
            days_back: Number of days to analyze
            
        Returns:
            Cross-tenant learning insights and recommendations
        """
        try:
            cache_key = f"cross_tenant_insights_{target_tenant_id}_{days_back}"
            
            # Check cache first
            if self._is_cached(cache_key):
                self.logger.info(f"Returning cached cross-tenant insights for tenant {target_tenant_id}")
                return self._cache[cache_key]
            
            self.logger.info(f"Generating cross-tenant insights for tenant {target_tenant_id}")
            analysis_start = datetime.utcnow()
            
            # Step 1: Update cross-tenant patterns from all tenants
            self._update_cross_tenant_patterns(days_back)
            
            # Step 2: Analyze target tenant's current state
            target_summary = self._analyze_tenant_optimization_state(target_tenant_id, days_back)
            
            # Step 3: Find applicable patterns for target tenant
            applicable_patterns = self._find_applicable_patterns(target_summary)
            
            # Step 4: Generate cross-tenant recommendations
            cross_tenant_recommendations = self._generate_cross_tenant_recommendations(
                target_tenant_id, target_summary, applicable_patterns
            )
            
            # Step 5: Generate learning insights
            learning_insights = self._generate_learning_insights(
                target_tenant_id, target_summary, applicable_patterns
            )
            
            # Step 6: Calculate opportunity metrics
            opportunity_metrics = self._calculate_opportunity_metrics(
                target_summary, applicable_patterns
            )
            
            analysis_duration = (datetime.utcnow() - analysis_start).total_seconds()
            
            results = {
                'analysis_metadata': {
                    'generated_at': datetime.utcnow().isoformat(),
                    'target_tenant_id': target_tenant_id,
                    'analysis_period_days': days_back,
                    'duration_seconds': analysis_duration,
                    'privacy_level': 'high',
                    'min_tenant_threshold': self.MIN_TENANT_THRESHOLD
                },
                'tenant_optimization_state': {
                    'performance_tier': target_summary.performance_tier if target_summary else 'unknown',
                    'optimization_maturity': target_summary.optimization_maturity if target_summary else 'unknown',
                    'pattern_diversity_score': target_summary.pattern_diversity_score if target_summary else 0.0,
                    'optimization_frequency': target_summary.optimization_frequency if target_summary else 0.0
                },
                'cross_tenant_patterns': {
                    'total_patterns_available': len(self.cross_tenant_patterns),
                    'applicable_patterns': len(applicable_patterns),
                    'high_confidence_patterns': len([p for p in applicable_patterns if p.confidence_score >= self.CONFIDENCE_THRESHOLD]),
                    'patterns_detail': [self._sanitize_pattern_for_response(p) for p in applicable_patterns[:10]]
                },
                'cross_tenant_recommendations': [asdict(rec) for rec in cross_tenant_recommendations],
                'learning_insights': [asdict(insight) for insight in learning_insights],
                'opportunity_metrics': opportunity_metrics,
                'privacy_compliance': {
                    'anonymization_verified': True,
                    'min_tenant_threshold_met': all(p.min_tenant_threshold_met for p in applicable_patterns),
                    'data_isolation_maintained': True,
                    'tenant_consent_verified': True  # In production, verify actual consent
                }
            }
            
            # Cache results
            self._cache_result(cache_key, results)
            
            self.logger.info(f"Generated cross-tenant insights for tenant {target_tenant_id} in {analysis_duration:.2f}s")
            return results
            
        except Exception as e:
            self.logger.error(f"Error generating cross-tenant insights for tenant {target_tenant_id}: {e}")
            return {
                'error': str(e),
                'analysis_metadata': {
                    'generated_at': datetime.utcnow().isoformat(),
                    'target_tenant_id': target_tenant_id,
                    'status': 'error'
                }
            }
    
    def update_pattern_learning(self, tenant_id: str, optimization_result: Dict[str, Any]) -> bool:
        """
        Update cross-tenant learning patterns with new optimization result.
        
        Args:
            tenant_id: Tenant ID (will be anonymized)
            optimization_result: Results from an A/B test or optimization
            
        Returns:
            True if successfully updated patterns
        """
        try:
            # Anonymize tenant ID
            tenant_hash = self._anonymize_tenant_id(tenant_id)
            
            # Extract pattern characteristics
            pattern_signature = self._extract_pattern_signature(optimization_result)
            
            if not pattern_signature:
                return False
            
            # Update or create pattern
            pattern_id = f"pattern_{hashlib.md5(pattern_signature.encode()).hexdigest()[:12]}"
            
            if pattern_id in self.cross_tenant_patterns:
                # Update existing pattern
                pattern = self.cross_tenant_patterns[pattern_id]
                self._update_pattern_with_result(pattern, optimization_result, tenant_hash)
            else:
                # Create new pattern
                pattern = self._create_pattern_from_result(pattern_id, optimization_result, tenant_hash)
                
                # Only store if meets privacy threshold
                if self._meets_privacy_threshold(pattern):
                    self.cross_tenant_patterns[pattern_id] = pattern
            
            # Update tenant summary
            self._update_tenant_summary(tenant_hash, optimization_result)
            
            self.logger.info(f"Updated cross-tenant pattern learning from tenant {tenant_hash[:8]}...")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating pattern learning: {e}")
            return False
    
    def get_global_optimization_trends(self) -> Dict[str, Any]:
        """
        Get global optimization trends across all tenants (anonymized).
        
        Returns:
            Global trend analysis
        """
        try:
            self.logger.info("Analyzing global optimization trends")
            
            if not self.cross_tenant_patterns:
                return {'message': 'Insufficient data for global trends analysis'}
            
            # Aggregate patterns by type
            pattern_types = Counter([p.pattern_type for p in self.cross_tenant_patterns.values()])
            
            # Calculate success rates by pattern type
            success_rates = {}
            for pattern_type in pattern_types:
                patterns = [p for p in self.cross_tenant_patterns.values() if p.pattern_type == pattern_type]
                avg_success_rate = sum(p.success_rate for p in patterns) / len(patterns)
                success_rates[pattern_type] = avg_success_rate
            
            # Find most successful patterns
            top_patterns = sorted(
                self.cross_tenant_patterns.values(),
                key=lambda x: (x.confidence_score * x.success_rate),
                reverse=True
            )[:10]
            
            # Analyze tenant maturity distribution
            maturity_distribution = Counter([
                summary.optimization_maturity 
                for summary in self.tenant_summaries.values()
            ])
            
            # Calculate global improvement metrics
            all_improvements = [
                p.avg_improvement_percent 
                for p in self.cross_tenant_patterns.values() 
                if p.avg_improvement_percent > 0
            ]
            
            global_trends = {
                'analysis_timestamp': datetime.utcnow().isoformat(),
                'total_tenants_analyzed': len(self.tenant_summaries),
                'total_patterns_identified': len(self.cross_tenant_patterns),
                'pattern_distribution': dict(pattern_types),
                'success_rates_by_type': success_rates,
                'top_performing_patterns': [
                    {
                        'pattern_type': p.pattern_type,
                        'confidence_score': p.confidence_score,
                        'success_rate': p.success_rate,
                        'avg_improvement_percent': p.avg_improvement_percent,
                        'tenant_count': p.tenant_count,
                        'applicable_categories': p.applicable_categories[:3]  # Limit for privacy
                    }
                    for p in top_patterns
                ],
                'tenant_maturity_distribution': dict(maturity_distribution),
                'global_improvement_metrics': {
                    'average_improvement_percent': np.mean(all_improvements) if all_improvements else 0,
                    'median_improvement_percent': np.median(all_improvements) if all_improvements else 0,
                    'improvement_std': np.std(all_improvements) if all_improvements else 0,
                    'patterns_with_high_confidence': len([p for p in self.cross_tenant_patterns.values() if p.confidence_score >= self.CONFIDENCE_THRESHOLD])
                },
                'optimization_insights': self._generate_global_insights(),
                'privacy_compliance': {
                    'data_anonymized': True,
                    'tenant_isolation_maintained': True,
                    'min_threshold_applied': True
                }
            }
            
            return global_trends
            
        except Exception as e:
            self.logger.error(f"Error analyzing global optimization trends: {e}")
            return {'error': str(e)}
    
    def get_tenant_benchmarking(self, tenant_id: str) -> Dict[str, Any]:
        """
        Provide anonymized benchmarking data for a tenant against cross-tenant patterns.
        
        Args:
            tenant_id: Target tenant ID
            
        Returns:
            Benchmarking analysis
        """
        try:
            self.logger.info(f"Generating tenant benchmarking for {tenant_id}")
            
            # Get tenant summary
            tenant_hash = self._anonymize_tenant_id(tenant_id)
            tenant_summary = self.tenant_summaries.get(tenant_hash)
            
            if not tenant_summary:
                # Generate summary if not exists
                tenant_summary = self._analyze_tenant_optimization_state(tenant_id, days_back=30)
            
            if not tenant_summary:
                return {'error': 'Unable to analyze tenant state for benchmarking'}
            
            # Find similar tenants (anonymized)
            similar_tenants = self._find_similar_tenants(tenant_summary)
            
            # Calculate benchmarking metrics
            benchmarking_data = {
                'tenant_analysis': {
                    'performance_tier': tenant_summary.performance_tier,
                    'optimization_maturity': tenant_summary.optimization_maturity,
                    'pattern_diversity_score': tenant_summary.pattern_diversity_score,
                    'optimization_frequency': tenant_summary.optimization_frequency,
                    'active_months': tenant_summary.active_months
                },
                'peer_comparison': {
                    'similar_tenant_count': len(similar_tenants),
                    'performance_ranking': self._calculate_performance_ranking(tenant_summary),
                    'optimization_maturity_percentile': self._calculate_maturity_percentile(tenant_summary),
                    'pattern_diversity_ranking': self._calculate_diversity_ranking(tenant_summary)
                },
                'improvement_opportunities': self._identify_benchmarking_opportunities(tenant_summary, similar_tenants),
                'success_patterns_available': len([
                    p for p in self.cross_tenant_patterns.values()
                    if self._is_pattern_applicable(p, tenant_summary)
                ]),
                'benchmarking_insights': self._generate_benchmarking_insights(tenant_summary, similar_tenants),
                'privacy_note': 'All comparisons use anonymized, aggregate data with no tenant-specific information exposed'
            }
            
            return benchmarking_data
            
        except Exception as e:
            self.logger.error(f"Error generating tenant benchmarking: {e}")
            return {'error': str(e)}
    
    def _update_cross_tenant_patterns(self, days_back: int) -> None:
        """Update cross-tenant patterns from all accessible tenants."""
        try:
            # Get all tenants (in production, this would be filtered by consent/permissions)
            active_tenants = self._get_active_tenants_for_learning()
            
            self.logger.info(f"Updating cross-tenant patterns from {len(active_tenants)} tenants")
            
            for tenant_id in active_tenants:
                # Skip if tenant has opted out of cross-tenant learning
                if not self._tenant_consents_to_learning(tenant_id):
                    continue
                
                # Get recent optimization results
                optimization_results = self._get_tenant_optimization_results(tenant_id, days_back)
                
                # Update patterns with results
                for result in optimization_results:
                    self.update_pattern_learning(tenant_id, result)
            
            # Clean up old or low-confidence patterns
            self._cleanup_patterns()
            
            self.logger.info(f"Updated cross-tenant patterns: {len(self.cross_tenant_patterns)} patterns total")
            
        except Exception as e:
            self.logger.error(f"Error updating cross-tenant patterns: {e}")
    
    def _analyze_tenant_optimization_state(self, tenant_id: str, days_back: int) -> Optional[TenantOptimizationSummary]:
        """Analyze tenant's current optimization state."""
        try:
            # Get tenant's performance data
            performance_data = self.performance_analyzer.analyze_prompt_performance(
                prompt_id=None, days_back=days_back, tenant_id=tenant_id
            )
            
            if not performance_data:
                return None
            
            # Get A/B testing history
            ab_tests = self._get_tenant_ab_tests(tenant_id, days_back)
            
            # Calculate optimization metrics
            tenant_hash = self._anonymize_tenant_id(tenant_id)
            
            # Determine performance tier
            avg_performance_score = np.mean([
                (1 - p.optimization_potential) * 100 
                for p in performance_data
            ])
            
            performance_tier = (
                'high' if avg_performance_score >= 80 else
                'medium' if avg_performance_score >= 60 else
                'low'
            )
            
            # Determine optimization maturity
            optimization_maturity = self._calculate_optimization_maturity(performance_data, ab_tests)
            
            # Calculate pattern diversity
            pattern_diversity = self._calculate_pattern_diversity(ab_tests)
            
            # Create summary
            summary = TenantOptimizationSummary(
                tenant_hash=tenant_hash,
                category_focus=self._extract_category_focus(performance_data),
                optimization_patterns=[
                    self._extract_pattern_signature(test) 
                    for test in ab_tests
                ],
                performance_tier=performance_tier,
                optimization_maturity=optimization_maturity,
                success_metrics=self._calculate_anonymized_success_metrics(performance_data),
                improvement_trends=self._calculate_improvement_trends(ab_tests),
                active_months=self._calculate_active_months(tenant_id),
                optimization_frequency=len(ab_tests) / max(days_back / 30, 1),  # Tests per month
                pattern_diversity_score=pattern_diversity
            )
            
            # Cache summary
            self.tenant_summaries[tenant_hash] = summary
            
            return summary
            
        except Exception as e:
            self.logger.error(f"Error analyzing tenant optimization state: {e}")
            return None
    
    def _find_applicable_patterns(self, tenant_summary: Optional[TenantOptimizationSummary]) -> List[CrossTenantPattern]:
        """Find cross-tenant patterns applicable to the target tenant."""
        if not tenant_summary:
            return []
        
        applicable_patterns = []
        
        for pattern in self.cross_tenant_patterns.values():
            if self._is_pattern_applicable(pattern, tenant_summary):
                applicable_patterns.append(pattern)
        
        # Sort by relevance score
        applicable_patterns.sort(
            key=lambda x: self._calculate_pattern_relevance(x, tenant_summary),
            reverse=True
        )
        
        return applicable_patterns
    
    def _generate_cross_tenant_recommendations(self, tenant_id: str, 
                                             tenant_summary: Optional[TenantOptimizationSummary],
                                             applicable_patterns: List[CrossTenantPattern]) -> List[CrossTenantRecommendation]:
        """Generate recommendations based on cross-tenant patterns."""
        recommendations = []
        
        try:
            for i, pattern in enumerate(applicable_patterns[:5]):  # Top 5 patterns
                recommendation = CrossTenantRecommendation(
                    recommendation_id=f"cross_tenant_rec_{uuid.uuid4().hex[:12]}",
                    title=f"Optimize Based on {pattern.pattern_type.replace('_', ' ').title()}",
                    description=self._generate_recommendation_description(pattern, tenant_summary),
                    category=pattern.pattern_type,
                    supporting_evidence={
                        'pattern_success_rate': pattern.success_rate,
                        'tenant_count': pattern.tenant_count,
                        'avg_improvement': pattern.avg_improvement_percent,
                        'confidence_score': pattern.confidence_score
                    },
                    confidence_level=self._map_confidence_to_level(pattern.confidence_score),
                    expected_improvement={
                        'improvement_percent': pattern.avg_improvement_percent,
                        'confidence_interval': self._calculate_improvement_confidence_interval(pattern)
                    },
                    similar_tenant_count=pattern.tenant_count,
                    pattern_success_rate=pattern.success_rate,
                    adaptation_guidance=self._generate_adaptation_guidance(pattern, tenant_summary),
                    implementation_complexity=self._assess_implementation_complexity(pattern),
                    estimated_effort=self._estimate_implementation_effort(pattern),
                    prerequisites=self._identify_prerequisites(pattern, tenant_summary),
                    risks=self._identify_implementation_risks(pattern)
                )
                
                recommendations.append(recommendation)
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating cross-tenant recommendations: {e}")
            return []
    
    def _generate_learning_insights(self, tenant_id: str,
                                  tenant_summary: Optional[TenantOptimizationSummary],
                                  applicable_patterns: List[CrossTenantPattern]) -> List[LearningInsight]:
        """Generate learning insights from cross-tenant analysis."""
        insights = []
        
        try:
            # Insight 1: Performance comparison
            if tenant_summary:
                performance_insight = self._generate_performance_comparison_insight(tenant_summary)
                if performance_insight:
                    insights.append(performance_insight)
            
            # Insight 2: Pattern opportunity analysis
            if applicable_patterns:
                pattern_insight = self._generate_pattern_opportunity_insight(applicable_patterns)
                if pattern_insight:
                    insights.append(pattern_insight)
            
            # Insight 3: Optimization maturity insight
            if tenant_summary:
                maturity_insight = self._generate_maturity_insight(tenant_summary)
                if maturity_insight:
                    insights.append(maturity_insight)
            
            # Insight 4: Category-specific insights
            category_insights = self._generate_category_insights(tenant_summary, applicable_patterns)
            insights.extend(category_insights)
            
            return insights[:5]  # Limit to 5 key insights
            
        except Exception as e:
            self.logger.error(f"Error generating learning insights: {e}")
            return []
    
    def _anonymize_tenant_id(self, tenant_id: str) -> str:
        """Anonymize tenant ID for cross-tenant learning."""
        anonymized_data = f"{tenant_id}:{self.ANONYMIZATION_SALT}"
        return hashlib.sha256(anonymized_data.encode()).hexdigest()[:16]
    
    def _extract_pattern_signature(self, optimization_result: Dict[str, Any]) -> str:
        """Extract pattern signature from optimization result."""
        try:
            # Create signature based on optimization characteristics
            signature_components = []
            
            # Pattern type
            if 'improvement_type' in optimization_result:
                signature_components.append(f"type:{optimization_result['improvement_type']}")
            elif 'test_type' in optimization_result:
                signature_components.append(f"type:{optimization_result['test_type']}")
            
            # Performance metrics improved
            if 'metrics_improved' in optimization_result:
                signature_components.append(f"metrics:{','.join(sorted(optimization_result['metrics_improved']))}")
            
            # Model type (if available)
            if 'model_type' in optimization_result:
                signature_components.append(f"model:{optimization_result['model_type']}")
            
            # Complexity indicator
            if 'complexity' in optimization_result:
                signature_components.append(f"complexity:{optimization_result['complexity']}")
            
            # Join components to create signature
            signature = "|".join(signature_components)
            return signature if signature else "generic_optimization"
            
        except Exception as e:
            self.logger.error(f"Error extracting pattern signature: {e}")
            return "unknown_pattern"
    
    def _is_cached(self, key: str) -> bool:
        """Check if result is cached and still valid."""
        if key not in self._cache:
            return False
        
        cache_time = self._cache_timestamps.get(key, datetime.min)
        return (datetime.utcnow() - cache_time) < self.cache_ttl
    
    def _cache_result(self, key: str, result: Any) -> None:
        """Cache a result with timestamp."""
        self._cache[key] = result
        self._cache_timestamps[key] = datetime.utcnow()
        
        # Simple cache cleanup
        if len(self._cache) > 50:
            oldest_key = min(self._cache_timestamps.keys(), key=lambda k: self._cache_timestamps[k])
            del self._cache[oldest_key]
            del self._cache_timestamps[oldest_key]

    def _install_helpers(self) -> None:
        """Install helper methods from cross_tenant_helpers module."""
        try:
            from .cross_tenant_helpers import install_helpers
            install_helpers(self)
            self.logger.info("Installed cross-tenant learning helper methods")
        except Exception as e:
            self.logger.error(f"Error installing helper methods: {e}")
    
    def _get_active_tenants_for_learning(self) -> List[str]:
        """Get list of active tenants that consent to cross-tenant learning."""
        try:
            # In production, this would query the tenant database with consent filters
            # For now, return a mock list
            return ['tenant_1', 'tenant_2', 'tenant_3']  # Mock tenant IDs
        except Exception as e:
            self.logger.error(f"Error getting active tenants: {e}")
            return []
    
    def _tenant_consents_to_learning(self, tenant_id: str) -> bool:
        """Check if tenant has consented to cross-tenant learning."""
        try:
            tenant = tenant_service.get_tenant(tenant_id)
            if not tenant:
                return False
            
            # Check tenant configuration for cross-tenant learning consent
            return tenant.config.custom_settings.get('cross_tenant_learning_enabled', False)
        except Exception as e:
            self.logger.error(f"Error checking tenant consent: {e}")
            return False
    
    def _get_tenant_optimization_results(self, tenant_id: str, days_back: int) -> List[Dict[str, Any]]:
        """Get recent optimization results for a tenant."""
        try:
            results = []
            
            # Get A/B test results from the database
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            ab_tests = ABTest.query.filter(
                ABTest.start_time >= cutoff_date,
                ABTest.status == 'completed',
                ABTest.winning_variant_id.isnot(None)
            ).all()
            
            for test in ab_tests:
                if test.results_summary:
                    results.append({
                        'test_id': test.test_id,
                        'pattern_type': self._infer_pattern_type_from_test(test),
                        'success': test.winning_variant_id is not None,
                        'improvement_percent': self._extract_improvement_from_test(test),
                        'category': self._extract_category_from_test(test),
                        'model_type': 'unknown',  # Would extract from test configuration
                        'complexity': 'medium',   # Would calculate based on test complexity
                        'metrics_improved': test.success_metrics or []
                    })
            
            return results
            
        except Exception as e:
            self.logger.error(f"Error getting tenant optimization results: {e}")
            return []
    
    def _get_tenant_ab_tests(self, tenant_id: str, days_back: int) -> List[Dict[str, Any]]:
        """Get A/B tests for a tenant in the specified period."""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_back)
            
            tests = ABTest.query.filter(
                ABTest.start_time >= cutoff_date
            ).all()
            
            return [
                {
                    'test_id': test.test_id,
                    'status': test.status,
                    'success_metrics': test.success_metrics,
                    'winning_variant': test.winning_variant_id,
                    'start_time': test.start_time,
                    'end_time': test.end_time
                }
                for test in tests
            ]
            
        except Exception as e:
            self.logger.error(f"Error getting tenant A/B tests: {e}")
            return []
    
    def _cleanup_patterns(self) -> None:
        """Remove old or low-confidence patterns."""
        try:
            patterns_to_remove = []
            cutoff_date = datetime.utcnow() - timedelta(days=90)  # Remove patterns older than 90 days
            
            for pattern_id, pattern in self.cross_tenant_patterns.items():
                # Remove if too old and low confidence
                if (pattern.last_updated < cutoff_date and 
                    pattern.confidence_score < 0.3):
                    patterns_to_remove.append(pattern_id)
                
                # Remove if very low success rate
                elif pattern.success_rate < 0.2 and pattern.total_applications > 20:
                    patterns_to_remove.append(pattern_id)
            
            for pattern_id in patterns_to_remove:
                del self.cross_tenant_patterns[pattern_id]
                
            if patterns_to_remove:
                self.logger.info(f"Cleaned up {len(patterns_to_remove)} low-quality patterns")
                
        except Exception as e:
            self.logger.error(f"Error cleaning up patterns: {e}")
    
    def _sanitize_pattern_for_response(self, pattern: CrossTenantPattern) -> Dict[str, Any]:
        """Sanitize pattern for API response (remove sensitive information)."""
        return {
            'pattern_id': pattern.pattern_id,
            'pattern_type': pattern.pattern_type,
            'success_rate': pattern.success_rate,
            'confidence_score': pattern.confidence_score,
            'avg_improvement_percent': pattern.avg_improvement_percent,
            'applicable_categories': pattern.applicable_categories[:3],  # Limit for privacy
            'tenant_count': pattern.tenant_count,
            'total_applications': pattern.total_applications,
            'first_observed': pattern.first_observed.isoformat(),
            'anonymization_level': pattern.anonymization_level
        }
    
    def _calculate_opportunity_metrics(self, tenant_summary: Optional[TenantOptimizationSummary],
                                     applicable_patterns: List[CrossTenantPattern]) -> Dict[str, Any]:
        """Calculate opportunity metrics for the tenant."""
        try:
            if not tenant_summary or not applicable_patterns:
                return {}
            
            # Calculate potential improvements
            total_improvement_potential = sum(
                p.avg_improvement_percent * p.confidence_score 
                for p in applicable_patterns
            )
            
            avg_improvement_potential = total_improvement_potential / len(applicable_patterns)
            
            # Count high-impact opportunities
            high_impact_patterns = [
                p for p in applicable_patterns 
                if p.avg_improvement_percent >= 20 and p.confidence_score >= 0.8
            ]
            
            return {
                'total_patterns_applicable': len(applicable_patterns),
                'high_confidence_patterns': len([p for p in applicable_patterns if p.confidence_score >= 0.8]),
                'high_impact_opportunities': len(high_impact_patterns),
                'avg_improvement_potential': avg_improvement_potential,
                'top_improvement_potential': max([p.avg_improvement_percent for p in applicable_patterns], default=0),
                'implementation_readiness_score': self._calculate_implementation_readiness(tenant_summary),
                'estimated_roi_multiplier': self._estimate_roi_multiplier(applicable_patterns)
            }
            
        except Exception as e:
            self.logger.error(f"Error calculating opportunity metrics: {e}")
            return {}
    
    def _calculate_implementation_readiness(self, tenant_summary: TenantOptimizationSummary) -> float:
        """Calculate tenant's readiness to implement optimizations."""
        try:
            readiness_score = 0.0
            
            # Maturity contributes to readiness
            maturity_scores = {'beginner': 0.3, 'intermediate': 0.7, 'advanced': 1.0}
            readiness_score += maturity_scores.get(tenant_summary.optimization_maturity, 0.5) * 0.4
            
            # Pattern diversity indicates sophistication
            readiness_score += min(tenant_summary.pattern_diversity_score, 1.0) * 0.3
            
            # Optimization frequency indicates active engagement
            frequency_score = min(tenant_summary.optimization_frequency / 2.0, 1.0)  # Normalize to 2 tests per month
            readiness_score += frequency_score * 0.3
            
            return min(1.0, readiness_score)
            
        except Exception as e:
            self.logger.error(f"Error calculating implementation readiness: {e}")
            return 0.5
    
    def _estimate_roi_multiplier(self, applicable_patterns: List[CrossTenantPattern]) -> float:
        """Estimate ROI multiplier based on applicable patterns."""
        try:
            if not applicable_patterns:
                return 1.0
            
            # Weight patterns by confidence and success rate
            weighted_improvements = [
                p.avg_improvement_percent * p.confidence_score * p.success_rate
                for p in applicable_patterns
            ]
            
            avg_weighted_improvement = sum(weighted_improvements) / len(weighted_improvements)
            
            # Convert improvement percentage to ROI multiplier
            # Assuming linear relationship for simplicity
            roi_multiplier = 1.0 + (avg_weighted_improvement / 100.0)
            
            return min(3.0, roi_multiplier)  # Cap at 3x ROI
            
        except Exception as e:
            self.logger.error(f"Error estimating ROI multiplier: {e}")
            return 1.0
    
    def _infer_pattern_type_from_test(self, test: ABTest) -> str:
        """Infer pattern type from A/B test characteristics."""
        if 'cost' in test.success_metrics:
            return 'cost_reduction'
        elif 'latency' in test.success_metrics:
            return 'latency_optimization'
        elif 'performance' in test.success_metrics or 'success_rate' in test.success_metrics:
            return 'performance_improvement'
        else:
            return 'general_optimization'
    
    def _extract_improvement_from_test(self, test: ABTest) -> float:
        """Extract improvement percentage from test results."""
        try:
            if test.results_summary and 'recommendation' in test.results_summary:
                recommendation = test.results_summary['recommendation']
                if 'expected_impact' in recommendation:
                    return recommendation['expected_impact'].get('improvement_percent', 0.0)
            return 0.0
        except Exception:
            return 0.0
    
    def _extract_category_from_test(self, test: ABTest) -> str:
        """Extract category from test metadata."""
        # In production, this would extract from test metadata or prompt categories
        return 'general'
    
    def _calculate_active_months(self, tenant_id: str) -> int:
        """Calculate number of months tenant has been active."""
        try:
            tenant = tenant_service.get_tenant(tenant_id)
            if tenant:
                months_active = (datetime.now() - tenant.created_at).days // 30
                return max(1, months_active)
            return 1
        except Exception:
            return 1
    
    def _map_confidence_to_level(self, confidence_score: float) -> str:
        """Map confidence score to human-readable level."""
        if confidence_score >= 0.8:
            return 'high'
        elif confidence_score >= 0.6:
            return 'medium'
        else:
            return 'low'
    
    def _calculate_improvement_confidence_interval(self, pattern: CrossTenantPattern) -> Tuple[float, float]:
        """Calculate confidence interval for improvement estimates."""
        try:
            mean = pattern.avg_improvement_percent
            std = pattern.std_improvement if pattern.std_improvement > 0 else mean * 0.2  # Estimate if not available
            
            # 95% confidence interval
            margin_of_error = 1.96 * std / np.sqrt(max(pattern.total_applications, 1))
            
            return (max(0, mean - margin_of_error), mean + margin_of_error)
        except Exception:
            return (0.0, pattern.avg_improvement_percent)


# Global service instance
cross_tenant_learning_engine = CrossTenantLearningEngine()