"""
Cross-Tenant Learning Engine Helper Methods
Contains implementation details for pattern analysis, privacy preservation, 
and cross-tenant recommendation generation.
"""

import logging
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict, Counter
import numpy as np
from scipy import stats

from app.models import ABTest, ABTestResult, ABTestAnalysis, Prompt
from .cross_tenant_learning_engine import (
    CrossTenantPattern, TenantOptimizationSummary, 
    CrossTenantRecommendation, LearningInsight
)

logger = logging.getLogger(__name__)


class CrossTenantHelpers:
    """Helper methods for cross-tenant learning operations."""
    
    def __init__(self, engine):
        """Initialize with reference to main engine."""
        self.engine = engine
        self.logger = logging.getLogger(__name__)
    
    def meets_privacy_threshold(self, pattern: CrossTenantPattern) -> bool:
        """Check if pattern meets privacy requirements."""
        return (
            pattern.tenant_count >= self.engine.MIN_TENANT_THRESHOLD and
            pattern.total_applications >= 10 and
            pattern.confidence_score >= 0.5
        )
    
    def update_pattern_with_result(self, pattern: CrossTenantPattern, 
                                  optimization_result: Dict[str, Any],
                                  tenant_hash: str) -> None:
        """Update existing pattern with new optimization result."""
        try:
            # Check if result was successful
            is_successful = optimization_result.get('success', False)
            improvement = optimization_result.get('improvement_percent', 0.0)
            
            if is_successful:
                pattern.success_count += 1
                
                # Update improvement metrics
                total_improvement = (pattern.avg_improvement_percent * (pattern.success_count - 1) + improvement)
                pattern.avg_improvement_percent = total_improvement / pattern.success_count
                
            else:
                pattern.failure_count += 1
            
            # Update success rate
            total_applications = pattern.success_count + pattern.failure_count
            pattern.success_rate = pattern.success_count / total_applications
            
            # Update confidence score based on statistical significance
            pattern.confidence_score = self._calculate_confidence_score(pattern)
            
            # Update metadata
            pattern.last_updated = datetime.utcnow()
            pattern.total_applications = total_applications
            
            # Update applicable contexts
            if 'category' in optimization_result:
                if optimization_result['category'] not in pattern.applicable_categories:
                    pattern.applicable_categories.append(optimization_result['category'])
            
            if 'model_type' in optimization_result:
                if optimization_result['model_type'] not in pattern.model_types:
                    pattern.model_types.append(optimization_result['model_type'])
            
            self.logger.debug(f"Updated pattern {pattern.pattern_id} with new result")
            
        except Exception as e:
            self.logger.error(f"Error updating pattern with result: {e}")
    
    def create_pattern_from_result(self, pattern_id: str, 
                                  optimization_result: Dict[str, Any],
                                  tenant_hash: str) -> CrossTenantPattern:
        """Create new cross-tenant pattern from optimization result."""
        try:
            is_successful = optimization_result.get('success', False)
            improvement = optimization_result.get('improvement_percent', 0.0)
            
            pattern = CrossTenantPattern(
                pattern_id=pattern_id,
                pattern_type=optimization_result.get('pattern_type', 'general_optimization'),
                pattern_signature=self.engine._extract_pattern_signature(optimization_result),
                pattern_description=self._generate_pattern_description(optimization_result),
                success_count=1 if is_successful else 0,
                failure_count=0 if is_successful else 1,
                success_rate=1.0 if is_successful else 0.0,
                confidence_score=0.5,  # Initial confidence
                avg_improvement_percent=improvement if is_successful else 0.0,
                median_improvement_percent=improvement if is_successful else 0.0,
                std_improvement=0.0,  # Will be calculated as more data comes in
                applicable_categories=[optimization_result.get('category', 'general')],
                model_types=[optimization_result.get('model_type', 'unknown')],
                complexity_ranges=[optimization_result.get('complexity', 'medium')],
                first_observed=datetime.utcnow(),
                last_updated=datetime.utcnow(),
                tenant_count=1,
                total_applications=1,
                anonymization_level="high",
                min_tenant_threshold_met=False  # Will be updated as more tenants contribute
            )
            
            return pattern
            
        except Exception as e:
            self.logger.error(f"Error creating pattern from result: {e}")
            raise
    
    def update_tenant_summary(self, tenant_hash: str, optimization_result: Dict[str, Any]) -> None:
        """Update tenant optimization summary with new result."""
        try:
            if tenant_hash not in self.engine.tenant_summaries:
                # Create initial summary
                summary = TenantOptimizationSummary(
                    tenant_hash=tenant_hash,
                    category_focus=[],
                    optimization_patterns=[],
                    performance_tier='unknown',
                    optimization_maturity='beginner',
                    success_metrics={},
                    improvement_trends={},
                    active_months=1,
                    optimization_frequency=0.0,
                    pattern_diversity_score=0.0
                )
                self.engine.tenant_summaries[tenant_hash] = summary
            
            summary = self.engine.tenant_summaries[tenant_hash]
            
            # Update pattern list
            pattern_sig = self.engine._extract_pattern_signature(optimization_result)
            if pattern_sig not in summary.optimization_patterns:
                summary.optimization_patterns.append(pattern_sig)
            
            # Update category focus
            category = optimization_result.get('category', 'general')
            if category not in summary.category_focus:
                summary.category_focus.append(category)
            
            # Update success metrics (anonymized)
            if optimization_result.get('success'):
                improvement = optimization_result.get('improvement_percent', 0.0)
                
                if 'avg_improvement' not in summary.success_metrics:
                    summary.success_metrics['avg_improvement'] = improvement
                else:
                    # Running average
                    current_avg = summary.success_metrics['avg_improvement']
                    summary.success_metrics['avg_improvement'] = (current_avg + improvement) / 2
            
            # Update pattern diversity score
            summary.pattern_diversity_score = len(set(summary.optimization_patterns)) / max(len(summary.optimization_patterns), 1)
            
            self.logger.debug(f"Updated tenant summary for {tenant_hash[:8]}...")
            
        except Exception as e:
            self.logger.error(f"Error updating tenant summary: {e}")
    
    def calculate_confidence_score(self, pattern: CrossTenantPattern) -> float:
        """Calculate statistical confidence score for a pattern."""
        try:
            total_applications = pattern.success_count + pattern.failure_count
            
            if total_applications < 5:
                return 0.3  # Low confidence with few samples
            
            # Use Wilson score interval for binomial confidence
            success_rate = pattern.success_rate
            z = 1.96  # 95% confidence
            n = total_applications
            
            wilson_score = (
                success_rate + z*z/(2*n) - z * np.sqrt(
                    (success_rate * (1 - success_rate) + z*z/(4*n)) / n
                )
            ) / (1 + z*z/n)
            
            # Adjust for sample size and tenant diversity
            sample_size_factor = min(1.0, total_applications / 50)  # Max factor at 50 applications
            tenant_diversity_factor = min(1.0, pattern.tenant_count / 10)  # Max factor at 10 tenants
            
            confidence = wilson_score * sample_size_factor * tenant_diversity_factor
            
            return max(0.1, min(1.0, confidence))  # Clamp between 0.1 and 1.0
            
        except Exception as e:
            self.logger.error(f"Error calculating confidence score: {e}")
            return 0.5  # Default moderate confidence
    
    def is_pattern_applicable(self, pattern: CrossTenantPattern, 
                             tenant_summary: TenantOptimizationSummary) -> bool:
        """Check if a pattern is applicable to a tenant."""
        try:
            # Check if pattern meets minimum confidence threshold
            if pattern.confidence_score < self.engine.CONFIDENCE_THRESHOLD:
                return False
            
            # Check if pattern has sufficient success rate
            if pattern.success_rate < self.engine.SUCCESS_RATE_THRESHOLD:
                return False
            
            # Check category overlap
            category_overlap = set(pattern.applicable_categories).intersection(
                set(tenant_summary.category_focus)
            )
            
            # Allow application if there's category overlap or if pattern is very general
            if category_overlap or 'general' in pattern.applicable_categories:
                return True
            
            # Check if tenant's optimization maturity matches pattern complexity
            maturity_compatibility = self._check_maturity_compatibility(
                pattern, tenant_summary.optimization_maturity
            )
            
            return maturity_compatibility
            
        except Exception as e:
            self.logger.error(f"Error checking pattern applicability: {e}")
            return False
    
    def calculate_pattern_relevance(self, pattern: CrossTenantPattern,
                                   tenant_summary: TenantOptimizationSummary) -> float:
        """Calculate relevance score for a pattern to a specific tenant."""
        try:
            relevance_score = 0.0
            
            # Base score from pattern confidence and success rate
            relevance_score += pattern.confidence_score * 0.3
            relevance_score += pattern.success_rate * 0.3
            
            # Category relevance
            category_overlap = set(pattern.applicable_categories).intersection(
                set(tenant_summary.category_focus)
            )
            category_relevance = len(category_overlap) / max(len(tenant_summary.category_focus), 1)
            relevance_score += category_relevance * 0.2
            
            # Improvement potential
            improvement_relevance = min(pattern.avg_improvement_percent / 50.0, 1.0)  # Normalize to 50% improvement
            relevance_score += improvement_relevance * 0.2
            
            return min(1.0, relevance_score)
            
        except Exception as e:
            self.logger.error(f"Error calculating pattern relevance: {e}")
            return 0.0
    
    def generate_recommendation_description(self, pattern: CrossTenantPattern,
                                          tenant_summary: Optional[TenantOptimizationSummary]) -> str:
        """Generate human-readable recommendation description."""
        try:
            improvement_pct = pattern.avg_improvement_percent
            tenant_count = pattern.tenant_count
            success_rate = pattern.success_rate * 100
            
            description_parts = []
            
            # Main recommendation
            if pattern.pattern_type == 'performance_improvement':
                description_parts.append(f"Implement performance optimization patterns that have shown {improvement_pct:.1f}% improvement")
            elif pattern.pattern_type == 'cost_reduction':
                description_parts.append(f"Apply cost reduction techniques that have achieved {improvement_pct:.1f}% cost savings")
            elif pattern.pattern_type == 'latency_optimization':
                description_parts.append(f"Use latency optimization methods that have reduced response times by {improvement_pct:.1f}%")
            else:
                description_parts.append(f"Implement {pattern.pattern_type} optimization with {improvement_pct:.1f}% improvement potential")
            
            # Evidence
            description_parts.append(f"across {tenant_count} similar organizations with {success_rate:.0f}% success rate")
            
            # Applicability note
            if tenant_summary and pattern.applicable_categories:
                categories = ", ".join(pattern.applicable_categories[:3])
                description_parts.append(f"Particularly effective for {categories} use cases")
            
            return " ".join(description_parts) + "."
            
        except Exception as e:
            self.logger.error(f"Error generating recommendation description: {e}")
            return f"Apply {pattern.pattern_type} optimization based on cross-tenant learning."
    
    def generate_adaptation_guidance(self, pattern: CrossTenantPattern,
                                   tenant_summary: Optional[TenantOptimizationSummary]) -> str:
        """Generate guidance for adapting pattern to specific tenant."""
        try:
            guidance_parts = []
            
            # Maturity-based guidance
            if tenant_summary:
                if tenant_summary.optimization_maturity == 'beginner':
                    guidance_parts.append("Start with basic implementation and gradually increase sophistication")
                elif tenant_summary.optimization_maturity == 'intermediate':
                    guidance_parts.append("Can implement full pattern with moderate customization")
                else:
                    guidance_parts.append("Advanced implementation with full customization recommended")
            
            # Category-specific guidance
            if pattern.applicable_categories:
                primary_category = pattern.applicable_categories[0]
                guidance_parts.append(f"Focus adaptation on {primary_category} requirements")
            
            # Success factors
            if pattern.success_rate > 0.9:
                guidance_parts.append("High success rate suggests minimal adaptation needed")
            else:
                guidance_parts.append("Monitor implementation closely and adjust based on initial results")
            
            return " • ".join(guidance_parts)
            
        except Exception as e:
            self.logger.error(f"Error generating adaptation guidance: {e}")
            return "Follow standard implementation practices and monitor results."
    
    def assess_implementation_complexity(self, pattern: CrossTenantPattern) -> str:
        """Assess implementation complexity of a pattern."""
        try:
            # Base complexity on pattern characteristics
            complexity_indicators = 0
            
            # More categories = more complexity
            if len(pattern.applicable_categories) > 3:
                complexity_indicators += 1
            
            # Multiple model types = more complexity
            if len(pattern.model_types) > 2:
                complexity_indicators += 1
            
            # Lower success rate might indicate higher complexity
            if pattern.success_rate < 0.8:
                complexity_indicators += 1
            
            # Pattern type complexity
            if pattern.pattern_type in ['latency_optimization', 'cost_reduction']:
                complexity_indicators += 1
            
            if complexity_indicators >= 3:
                return 'high'
            elif complexity_indicators >= 1:
                return 'medium'
            else:
                return 'low'
                
        except Exception as e:
            self.logger.error(f"Error assessing implementation complexity: {e}")
            return 'medium'
    
    def estimate_implementation_effort(self, pattern: CrossTenantPattern) -> str:
        """Estimate implementation effort for a pattern."""
        try:
            complexity = self.assess_implementation_complexity(pattern)
            
            effort_mapping = {
                'low': '1-2 days',
                'medium': '3-5 days', 
                'high': '1-2 weeks'
            }
            
            return effort_mapping.get(complexity, '3-5 days')
            
        except Exception as e:
            self.logger.error(f"Error estimating implementation effort: {e}")
            return '3-5 days'
    
    def identify_prerequisites(self, pattern: CrossTenantPattern,
                              tenant_summary: Optional[TenantOptimizationSummary]) -> List[str]:
        """Identify prerequisites for implementing a pattern."""
        try:
            prerequisites = []
            
            # Maturity-based prerequisites
            if tenant_summary and tenant_summary.optimization_maturity == 'beginner':
                prerequisites.append('Basic A/B testing framework')
                prerequisites.append('Performance monitoring system')
            
            # Pattern-specific prerequisites
            if pattern.pattern_type == 'cost_reduction':
                prerequisites.append('Cost tracking and analysis capabilities')
                prerequisites.append('Resource usage monitoring')
            
            if pattern.pattern_type == 'latency_optimization':
                prerequisites.append('Latency measurement infrastructure')
                prerequisites.append('Performance baseline establishment')
            
            if pattern.pattern_type == 'performance_improvement':
                prerequisites.append('Comprehensive performance metrics')
                prerequisites.append('Rollback capabilities')
            
            # Model-specific prerequisites
            if len(pattern.model_types) > 1:
                prerequisites.append('Multi-model testing capability')
            
            return prerequisites[:5]  # Limit to 5 key prerequisites
            
        except Exception as e:
            self.logger.error(f"Error identifying prerequisites: {e}")
            return ['Basic optimization infrastructure']
    
    def identify_implementation_risks(self, pattern: CrossTenantPattern) -> List[str]:
        """Identify risks associated with implementing a pattern."""
        try:
            risks = []
            
            # Success rate based risks
            if pattern.success_rate < 0.9:
                failure_rate = (1 - pattern.success_rate) * 100
                risks.append(f'{failure_rate:.0f}% chance of not achieving expected improvements')
            
            # Complexity-based risks
            complexity = self.assess_implementation_complexity(pattern)
            if complexity == 'high':
                risks.append('Complex implementation may require specialized expertise')
                risks.append('Higher chance of integration issues')
            
            # Pattern-specific risks
            if pattern.pattern_type == 'cost_reduction':
                risks.append('May impact performance or quality metrics')
            
            if pattern.pattern_type == 'latency_optimization':
                risks.append('Potential trade-offs with accuracy or cost')
            
            # Low confidence risks
            if pattern.confidence_score < 0.8:
                risks.append('Pattern confidence below optimal threshold')
            
            return risks[:4]  # Limit to 4 key risks
            
        except Exception as e:
            self.logger.error(f"Error identifying implementation risks: {e}")
            return ['Standard implementation risks apply']
    
    def _generate_pattern_description(self, optimization_result: Dict[str, Any]) -> str:
        """Generate description for a pattern based on optimization result."""
        try:
            pattern_type = optimization_result.get('pattern_type', 'optimization')
            improvement = optimization_result.get('improvement_percent', 0)
            
            if pattern_type == 'performance_improvement':
                return f"Performance optimization pattern achieving {improvement:.1f}% improvement"
            elif pattern_type == 'cost_reduction':
                return f"Cost reduction pattern saving {improvement:.1f}% on operational costs"
            elif pattern_type == 'latency_optimization':
                return f"Latency optimization pattern reducing response time by {improvement:.1f}%"
            else:
                return f"{pattern_type.replace('_', ' ').title()} pattern with {improvement:.1f}% improvement"
                
        except Exception as e:
            self.logger.error(f"Error generating pattern description: {e}")
            return "Optimization pattern based on cross-tenant learning"
    
    def _check_maturity_compatibility(self, pattern: CrossTenantPattern, 
                                     tenant_maturity: str) -> bool:
        """Check if tenant maturity is compatible with pattern complexity."""
        complexity = self.assess_implementation_complexity(pattern)
        
        compatibility_matrix = {
            'beginner': ['low'],
            'intermediate': ['low', 'medium'],
            'advanced': ['low', 'medium', 'high']
        }
        
        return complexity in compatibility_matrix.get(tenant_maturity, ['low'])


# Helper functions for the main engine
def install_helpers(engine):
    """Install helper methods into the main engine."""
    helpers = CrossTenantHelpers(engine)
    
    # Bind helper methods to engine
    engine._meets_privacy_threshold = helpers.meets_privacy_threshold
    engine._update_pattern_with_result = helpers.update_pattern_with_result
    engine._create_pattern_from_result = helpers.create_pattern_from_result
    engine._update_tenant_summary = helpers.update_tenant_summary
    engine._calculate_confidence_score = helpers.calculate_confidence_score
    engine._is_pattern_applicable = helpers.is_pattern_applicable
    engine._calculate_pattern_relevance = helpers.calculate_pattern_relevance
    engine._generate_recommendation_description = helpers.generate_recommendation_description
    engine._generate_adaptation_guidance = helpers.generate_adaptation_guidance
    engine._assess_implementation_complexity = helpers.assess_implementation_complexity
    engine._estimate_implementation_effort = helpers.estimate_implementation_effort
    engine._identify_prerequisites = helpers.identify_prerequisites
    engine._identify_implementation_risks = helpers.identify_implementation_risks
    
    return helpers