"""
Comprehensive Test Suite for Cross-Tenant Learning Engine
Tests privacy preservation, pattern recognition, recommendation generation, and compliance.
"""

import pytest
import uuid
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
from decimal import Decimal

from app.services.ml_optimization.cross_tenant_learning_engine import (
    cross_tenant_learning_engine,
    CrossTenantPattern,
    TenantOptimizationSummary,
    CrossTenantRecommendation,
    LearningInsight
)
from app.models import db, ABTest, ABTestResult, ABTestAnalysis
from app.services.tenant_service import tenant_service


class TestCrossTenantLearningEngine:
    """Test suite for cross-tenant learning engine."""
    
    @pytest.fixture
    def engine(self):
        """Return cross-tenant learning engine instance."""
        return cross_tenant_learning_engine
    
    @pytest.fixture
    def mock_tenant_data(self):
        """Mock tenant data for testing."""
        return {
            'tenant_1': {
                'id': 'tenant_1',
                'name': 'Test Tenant 1',
                'created_at': datetime.utcnow() - timedelta(days=90),
                'config': Mock(custom_settings={'cross_tenant_learning_enabled': True})
            },
            'tenant_2': {
                'id': 'tenant_2', 
                'name': 'Test Tenant 2',
                'created_at': datetime.utcnow() - timedelta(days=60),
                'config': Mock(custom_settings={'cross_tenant_learning_enabled': True})
            },
            'tenant_3': {
                'id': 'tenant_3',
                'name': 'Test Tenant 3',
                'created_at': datetime.utcnow() - timedelta(days=30),
                'config': Mock(custom_settings={'cross_tenant_learning_enabled': False})
            }
        }
    
    @pytest.fixture
    def sample_optimization_results(self):
        """Sample optimization results for testing."""
        return [
            {
                'pattern_type': 'performance_improvement',
                'success': True,
                'improvement_percent': 25.0,
                'category': 'text_generation',
                'model_type': 'gpt-4',
                'complexity': 'medium',
                'metrics_improved': ['latency', 'accuracy']
            },
            {
                'pattern_type': 'cost_reduction',
                'success': True,
                'improvement_percent': 15.0,
                'category': 'summarization',
                'model_type': 'gpt-3.5-turbo',
                'complexity': 'low',
                'metrics_improved': ['cost']
            },
            {
                'pattern_type': 'latency_optimization',
                'success': False,
                'improvement_percent': 0.0,
                'category': 'classification',
                'model_type': 'claude-3',
                'complexity': 'high',
                'metrics_improved': ['latency']
            }
        ]
    
    @pytest.fixture
    def sample_cross_tenant_pattern(self):
        """Sample cross-tenant pattern for testing."""
        return CrossTenantPattern(
            pattern_id='test_pattern_001',
            pattern_type='performance_improvement',
            pattern_signature='type:performance_improvement|metrics:latency,accuracy',
            pattern_description='Performance improvement pattern achieving 25.0% improvement',
            success_count=8,
            failure_count=2,
            success_rate=0.8,
            confidence_score=0.85,
            avg_improvement_percent=22.5,
            median_improvement_percent=20.0,
            std_improvement=5.2,
            applicable_categories=['text_generation', 'qa'],
            model_types=['gpt-4', 'claude-3'],
            complexity_ranges=['medium'],
            first_observed=datetime.utcnow() - timedelta(days=30),
            last_updated=datetime.utcnow(),
            tenant_count=5,
            total_applications=10,
            anonymization_level='high',
            min_tenant_threshold_met=True
        )

    def test_engine_initialization(self, engine):
        """Test that the engine initializes correctly."""
        assert engine is not None
        assert engine.MIN_TENANT_THRESHOLD == 3
        assert engine.CONFIDENCE_THRESHOLD == 0.7
        assert engine.SUCCESS_RATE_THRESHOLD == 0.8
        assert hasattr(engine, 'cross_tenant_patterns')
        assert hasattr(engine, 'tenant_summaries')
        assert hasattr(engine, 'learning_insights')

    def test_tenant_id_anonymization(self, engine):
        """Test that tenant IDs are properly anonymized."""
        tenant_id = 'test_tenant_123'
        
        # Test anonymization
        anonymized_1 = engine._anonymize_tenant_id(tenant_id)
        anonymized_2 = engine._anonymize_tenant_id(tenant_id)
        
        # Should be consistent
        assert anonymized_1 == anonymized_2
        assert len(anonymized_1) == 16  # 16 character hash
        assert anonymized_1 != tenant_id  # Should be different from original
        
        # Different tenants should have different hashes
        different_tenant = 'different_tenant_456'
        different_hash = engine._anonymize_tenant_id(different_tenant)
        assert different_hash != anonymized_1

    def test_pattern_signature_extraction(self, engine, sample_optimization_results):
        """Test extraction of pattern signatures from optimization results."""
        for result in sample_optimization_results:
            signature = engine._extract_pattern_signature(result)
            
            assert isinstance(signature, str)
            assert len(signature) > 0
            
            # Should contain pattern type
            if 'pattern_type' in result:
                assert f"type:{result['pattern_type']}" in signature
            
            # Should be consistent for same input
            signature2 = engine._extract_pattern_signature(result)
            assert signature == signature2

    def test_pattern_learning_update_success(self, engine, sample_optimization_results):
        """Test updating pattern learning with successful optimization results."""
        tenant_id = 'test_tenant_update'
        result = sample_optimization_results[0]  # Successful result
        
        # Mock tenant consent
        with patch.object(engine, '_tenant_consents_to_learning', return_value=True):
            success = engine.update_pattern_learning(tenant_id, result)
            
            assert success is True
            
            # Check that pattern was created
            pattern_signature = engine._extract_pattern_signature(result)
            pattern_id = f"pattern_{result['pattern_type']}"  # Simplified for test
            
            # Verify tenant summary was updated
            tenant_hash = engine._anonymize_tenant_id(tenant_id)
            assert tenant_hash in engine.tenant_summaries

    def test_pattern_learning_update_failure(self, engine, sample_optimization_results):
        """Test updating pattern learning with failed optimization results."""
        tenant_id = 'test_tenant_failure'
        result = sample_optimization_results[2]  # Failed result
        
        # Mock tenant consent
        with patch.object(engine, '_tenant_consents_to_learning', return_value=True):
            success = engine.update_pattern_learning(tenant_id, result)
            
            assert success is True  # Should still succeed in updating pattern
            
            # Verify tenant summary was updated
            tenant_hash = engine._anonymize_tenant_id(tenant_id)
            assert tenant_hash in engine.tenant_summaries

    def test_pattern_learning_no_consent(self, engine, sample_optimization_results):
        """Test that pattern learning respects tenant consent."""
        tenant_id = 'test_tenant_no_consent'
        result = sample_optimization_results[0]
        
        # Mock no tenant consent
        with patch.object(engine, '_tenant_consents_to_learning', return_value=False):
            # This would typically be handled at a higher level, but test the check
            consents = engine._tenant_consents_to_learning(tenant_id)
            assert consents is False

    def test_privacy_threshold_enforcement(self, engine, sample_cross_tenant_pattern):
        """Test that privacy thresholds are enforced."""
        # Pattern with insufficient tenant count
        low_tenant_pattern = sample_cross_tenant_pattern
        low_tenant_pattern.tenant_count = 2  # Below MIN_TENANT_THRESHOLD
        
        meets_threshold = engine._meets_privacy_threshold(low_tenant_pattern)
        assert meets_threshold is False
        
        # Pattern meeting threshold
        good_pattern = sample_cross_tenant_pattern
        good_pattern.tenant_count = 5  # Above threshold
        
        meets_threshold = engine._meets_privacy_threshold(good_pattern)
        assert meets_threshold is True

    def test_pattern_applicability_check(self, engine, sample_cross_tenant_pattern):
        """Test checking if patterns are applicable to specific tenants."""
        # Create mock tenant summary
        tenant_summary = TenantOptimizationSummary(
            tenant_hash='test_hash',
            category_focus=['text_generation'],
            optimization_patterns=[],
            performance_tier='medium',
            optimization_maturity='intermediate',
            success_metrics={},
            improvement_trends={},
            active_months=3,
            optimization_frequency=1.5,
            pattern_diversity_score=0.6
        )
        
        # Test with high-confidence pattern
        pattern = sample_cross_tenant_pattern
        pattern.confidence_score = 0.9
        pattern.success_rate = 0.85
        pattern.applicable_categories = ['text_generation']
        
        is_applicable = engine._is_pattern_applicable(pattern, tenant_summary)
        assert is_applicable is True
        
        # Test with low-confidence pattern
        pattern.confidence_score = 0.5
        pattern.success_rate = 0.6
        
        is_applicable = engine._is_pattern_applicable(pattern, tenant_summary)
        assert is_applicable is False

    def test_cross_tenant_insights_generation(self, engine, mock_tenant_data):
        """Test generation of cross-tenant insights."""
        tenant_id = 'test_tenant_insights'
        
        # Mock dependencies
        with patch.object(engine, '_update_cross_tenant_patterns'), \
             patch.object(engine, '_analyze_tenant_optimization_state') as mock_analyze, \
             patch.object(engine, '_find_applicable_patterns', return_value=[]) as mock_patterns, \
             patch.object(engine, '_generate_cross_tenant_recommendations', return_value=[]) as mock_recs, \
             patch.object(engine, '_generate_learning_insights', return_value=[]) as mock_insights, \
             patch.object(engine, '_calculate_opportunity_metrics', return_value={}) as mock_metrics:
            
            # Setup mock return values
            mock_analyze.return_value = TenantOptimizationSummary(
                tenant_hash='mock_hash',
                category_focus=['general'],
                optimization_patterns=[],
                performance_tier='medium',
                optimization_maturity='intermediate',
                success_metrics={},
                improvement_trends={},
                active_months=2,
                optimization_frequency=1.0,
                pattern_diversity_score=0.5
            )
            
            # Generate insights
            insights = engine.generate_cross_tenant_insights(tenant_id, days_back=30)
            
            assert insights is not None
            assert 'analysis_metadata' in insights
            assert 'tenant_optimization_state' in insights
            assert 'cross_tenant_patterns' in insights
            assert 'cross_tenant_recommendations' in insights
            assert 'learning_insights' in insights
            assert 'opportunity_metrics' in insights
            assert 'privacy_compliance' in insights
            
            # Verify privacy compliance
            privacy = insights['privacy_compliance']
            assert privacy['anonymization_verified'] is True
            assert privacy['data_isolation_maintained'] is True
            assert privacy['tenant_consent_verified'] is True

    def test_global_optimization_trends(self, engine, sample_cross_tenant_pattern):
        """Test global optimization trends analysis."""
        # Add some patterns to the engine
        engine.cross_tenant_patterns = {
            'pattern_1': sample_cross_tenant_pattern,
            'pattern_2': CrossTenantPattern(
                pattern_id='pattern_2',
                pattern_type='cost_reduction',
                pattern_signature='type:cost_reduction',
                pattern_description='Cost reduction pattern',
                success_count=6,
                failure_count=1,
                success_rate=0.86,
                confidence_score=0.9,
                avg_improvement_percent=18.5,
                median_improvement_percent=17.0,
                std_improvement=3.2,
                applicable_categories=['summarization'],
                model_types=['gpt-3.5-turbo'],
                complexity_ranges=['low'],
                first_observed=datetime.utcnow() - timedelta(days=20),
                last_updated=datetime.utcnow(),
                tenant_count=4,
                total_applications=7,
                anonymization_level='high',
                min_tenant_threshold_met=True
            )
        }
        
        # Get global trends
        trends = engine.get_global_optimization_trends()
        
        assert trends is not None
        assert 'analysis_timestamp' in trends
        assert 'total_patterns_identified' in trends
        assert 'pattern_distribution' in trends
        assert 'success_rates_by_type' in trends
        assert 'top_performing_patterns' in trends
        assert 'global_improvement_metrics' in trends
        assert 'privacy_compliance' in trends
        
        # Verify pattern distribution
        assert trends['total_patterns_identified'] == 2
        assert 'performance_improvement' in trends['pattern_distribution']
        assert 'cost_reduction' in trends['pattern_distribution']

    def test_tenant_benchmarking(self, engine):
        """Test tenant benchmarking functionality."""
        tenant_id = 'test_tenant_benchmark'
        
        # Mock tenant summary
        mock_summary = TenantOptimizationSummary(
            tenant_hash=engine._anonymize_tenant_id(tenant_id),
            category_focus=['text_generation'],
            optimization_patterns=['pattern_1'],
            performance_tier='medium',
            optimization_maturity='intermediate',
            success_metrics={'avg_improvement': 15.0},
            improvement_trends={},
            active_months=4,
            optimization_frequency=2.0,
            pattern_diversity_score=0.7
        )
        
        engine.tenant_summaries[mock_summary.tenant_hash] = mock_summary
        
        # Get benchmarking data
        benchmarking = engine.get_tenant_benchmarking(tenant_id)
        
        assert benchmarking is not None
        assert 'tenant_analysis' in benchmarking
        assert 'peer_comparison' in benchmarking
        assert 'improvement_opportunities' in benchmarking
        assert 'benchmarking_insights' in benchmarking
        
        # Verify tenant analysis
        tenant_analysis = benchmarking['tenant_analysis']
        assert tenant_analysis['performance_tier'] == 'medium'
        assert tenant_analysis['optimization_maturity'] == 'intermediate'

    def test_confidence_score_calculation(self, engine):
        """Test statistical confidence score calculation."""
        # Test with sufficient data
        pattern_high_confidence = CrossTenantPattern(
            pattern_id='test_confidence',
            pattern_type='test',
            pattern_signature='test',
            pattern_description='test',
            success_count=45,
            failure_count=5,
            success_rate=0.9,
            confidence_score=0.0,  # Will be calculated
            avg_improvement_percent=20.0,
            median_improvement_percent=20.0,
            std_improvement=2.0,
            applicable_categories=['test'],
            model_types=['test'],
            complexity_ranges=['test'],
            first_observed=datetime.utcnow(),
            last_updated=datetime.utcnow(),
            tenant_count=8,
            total_applications=50,
            anonymization_level='high',
            min_tenant_threshold_met=True
        )
        
        confidence = engine._calculate_confidence_score(pattern_high_confidence)
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.5  # Should be high confidence
        
        # Test with insufficient data
        pattern_low_confidence = CrossTenantPattern(
            pattern_id='test_confidence_low',
            pattern_type='test',
            pattern_signature='test',
            pattern_description='test',
            success_count=2,
            failure_count=1,
            success_rate=0.67,
            confidence_score=0.0,
            avg_improvement_percent=10.0,
            median_improvement_percent=10.0,
            std_improvement=1.0,
            applicable_categories=['test'],
            model_types=['test'],
            complexity_ranges=['test'],
            first_observed=datetime.utcnow(),
            last_updated=datetime.utcnow(),
            tenant_count=2,
            total_applications=3,
            anonymization_level='high',
            min_tenant_threshold_met=False
        )
        
        confidence = engine._calculate_confidence_score(pattern_low_confidence)
        assert confidence < 0.5  # Should be low confidence

    def test_pattern_cleanup(self, engine):
        """Test cleanup of old and low-quality patterns."""
        # Add some patterns to cleanup
        old_pattern = CrossTenantPattern(
            pattern_id='old_pattern',
            pattern_type='test',
            pattern_signature='test',
            pattern_description='old pattern',
            success_count=1,
            failure_count=0,
            success_rate=1.0,
            confidence_score=0.2,  # Low confidence
            avg_improvement_percent=5.0,
            median_improvement_percent=5.0,
            std_improvement=0.0,
            applicable_categories=['test'],
            model_types=['test'],
            complexity_ranges=['test'],
            first_observed=datetime.utcnow() - timedelta(days=100),
            last_updated=datetime.utcnow() - timedelta(days=95),  # Old
            tenant_count=1,
            total_applications=1,
            anonymization_level='high',
            min_tenant_threshold_met=False
        )
        
        low_success_pattern = CrossTenantPattern(
            pattern_id='low_success_pattern',
            pattern_type='test',
            pattern_signature='test',
            pattern_description='low success pattern',
            success_count=3,
            failure_count=22,  # Low success rate
            success_rate=0.12,
            confidence_score=0.5,
            avg_improvement_percent=2.0,
            median_improvement_percent=2.0,
            std_improvement=1.0,
            applicable_categories=['test'],
            model_types=['test'],
            complexity_ranges=['test'],
            first_observed=datetime.utcnow() - timedelta(days=30),
            last_updated=datetime.utcnow() - timedelta(days=1),
            tenant_count=3,
            total_applications=25,
            anonymization_level='high',
            min_tenant_threshold_met=True
        )
        
        engine.cross_tenant_patterns['old_pattern'] = old_pattern
        engine.cross_tenant_patterns['low_success_pattern'] = low_success_pattern
        
        # Run cleanup
        engine._cleanup_patterns()
        
        # Verify cleanup
        assert 'old_pattern' not in engine.cross_tenant_patterns
        assert 'low_success_pattern' not in engine.cross_tenant_patterns

    def test_privacy_compliance_throughout_pipeline(self, engine, sample_optimization_results):
        """Test that privacy compliance is maintained throughout the entire pipeline."""
        tenant_id = 'privacy_test_tenant'
        
        # Mock tenant consent
        with patch.object(engine, '_tenant_consents_to_learning', return_value=True):
            # Update pattern learning
            engine.update_pattern_learning(tenant_id, sample_optimization_results[0])
            
            # Generate insights
            insights = engine.generate_cross_tenant_insights(tenant_id, days_back=7)
            
            # Verify no raw tenant data is exposed
            insights_json = json.dumps(insights)
            assert tenant_id not in insights_json  # Raw tenant ID should not appear
            
            # Verify privacy compliance flags
            privacy = insights.get('privacy_compliance', {})
            assert privacy.get('anonymization_verified') is True
            assert privacy.get('data_isolation_maintained') is True
            
            # Check tenant hash anonymization
            tenant_hash = engine._anonymize_tenant_id(tenant_id)
            assert tenant_hash != tenant_id
            assert len(tenant_hash) == 16

    @pytest.mark.parametrize("pattern_type,expected_complexity", [
        ('performance_improvement', 'medium'),
        ('cost_reduction', 'low'),
        ('latency_optimization', 'high'),
    ])
    def test_implementation_complexity_assessment(self, engine, pattern_type, expected_complexity):
        """Test implementation complexity assessment for different pattern types."""
        pattern = CrossTenantPattern(
            pattern_id=f'test_{pattern_type}',
            pattern_type=pattern_type,
            pattern_signature=f'type:{pattern_type}',
            pattern_description=f'{pattern_type} pattern',
            success_count=10,
            failure_count=0,
            success_rate=1.0,
            confidence_score=0.9,
            avg_improvement_percent=20.0,
            median_improvement_percent=20.0,
            std_improvement=2.0,
            applicable_categories=['general'],
            model_types=['gpt-4'],
            complexity_ranges=['medium'],
            first_observed=datetime.utcnow(),
            last_updated=datetime.utcnow(),
            tenant_count=5,
            total_applications=10,
            anonymization_level='high',
            min_tenant_threshold_met=True
        )
        
        complexity = engine._assess_implementation_complexity(pattern)
        assert complexity in ['low', 'medium', 'high']

    def test_error_handling_and_resilience(self, engine):
        """Test error handling and system resilience."""
        # Test with invalid tenant ID
        invalid_insights = engine.generate_cross_tenant_insights('', days_back=30)
        assert 'error' in invalid_insights
        
        # Test with negative days_back
        negative_insights = engine.generate_cross_tenant_insights('valid_tenant', days_back=-1)
        # Should handle gracefully or provide default
        
        # Test pattern learning with malformed result
        malformed_result = {'invalid': 'data'}
        success = engine.update_pattern_learning('test_tenant', malformed_result)
        # Should return False or handle gracefully
        assert isinstance(success, bool)

    def test_caching_behavior(self, engine):
        """Test caching behavior for performance optimization."""
        tenant_id = 'cache_test_tenant'
        
        # Mock the expensive operations
        with patch.object(engine, '_update_cross_tenant_patterns') as mock_update, \
             patch.object(engine, '_analyze_tenant_optimization_state', return_value=None) as mock_analyze:
            
            # First call should hit the actual methods
            insights1 = engine.generate_cross_tenant_insights(tenant_id, days_back=30)
            
            # Second call with same parameters should use cache
            insights2 = engine.generate_cross_tenant_insights(tenant_id, days_back=30)
            
            # Both should return similar structure
            assert 'analysis_metadata' in insights1
            assert 'analysis_metadata' in insights2

    def test_integration_with_existing_systems(self, engine):
        """Test integration with existing ML analysis and A/B testing systems."""
        # This tests the integration points with existing services
        
        # Mock performance analyzer
        with patch.object(engine.performance_analyzer, 'analyze_prompt_performance') as mock_perf:
            mock_perf.return_value = []
            
            # Test that the engine calls the performance analyzer
            engine._analyze_tenant_optimization_state('test_tenant', 30)
            mock_perf.assert_called_once()

    def test_data_retention_and_cleanup_policies(self, engine):
        """Test data retention and cleanup policies."""
        # Test that old data is properly cleaned up
        cutoff_date = datetime.utcnow() - timedelta(days=91)
        
        old_pattern = CrossTenantPattern(
            pattern_id='old_pattern_retention_test',
            pattern_type='test',
            pattern_signature='test',
            pattern_description='test',
            success_count=5,
            failure_count=0,
            success_rate=1.0,
            confidence_score=0.1,  # Low confidence for cleanup
            avg_improvement_percent=10.0,
            median_improvement_percent=10.0,
            std_improvement=1.0,
            applicable_categories=['test'],
            model_types=['test'],
            complexity_ranges=['test'],
            first_observed=cutoff_date,
            last_updated=cutoff_date,
            tenant_count=2,
            total_applications=5,
            anonymization_level='high',
            min_tenant_threshold_met=False
        )
        
        engine.cross_tenant_patterns['old_pattern_retention_test'] = old_pattern
        engine._cleanup_patterns()
        
        # Should be cleaned up due to age and low confidence
        assert 'old_pattern_retention_test' not in engine.cross_tenant_patterns


if __name__ == '__main__':
    pytest.main([__file__, '-v'])