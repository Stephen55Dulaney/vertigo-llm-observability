#!/usr/bin/env python3
"""
Cross-Tenant Learning Engine Integration Validation
Validates integration with existing ML analysis and A/B testing systems.
"""

import os
import sys
import pytest
import logging
from datetime import datetime, timedelta
from unittest.mock import Mock, patch

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.services.ml_optimization.cross_tenant_learning_engine import cross_tenant_learning_engine
from app.services.ml_optimization.ab_testing_orchestrator import ab_testing_orchestrator  
from app.services.ml_optimization.ml_service import ml_optimization_service
from app.services.tenant_service import tenant_service
from app.models import db, ABTest, ABTestVariant, ABTestResult


class TestCrossTenantIntegration:
    """Integration validation for cross-tenant learning with existing systems."""
    
    def setup_method(self):
        """Set up test environment."""
        self.logger = logging.getLogger(__name__)
        self.test_tenant_id = 'integration_test_tenant'
        
    def test_ml_service_integration(self):
        """Test integration with ML optimization service."""
        try:
            # Test that cross-tenant engine can access ML service components
            assert hasattr(cross_tenant_learning_engine, 'performance_analyzer')
            assert hasattr(cross_tenant_learning_engine, 'quality_scorer')
            assert hasattr(cross_tenant_learning_engine, 'recommendation_engine')
            
            # Test that ML service is available
            assert ml_optimization_service is not None
            
            # Test integration method calls
            with patch.object(cross_tenant_learning_engine.performance_analyzer, 'analyze_prompt_performance') as mock_perf:
                mock_perf.return_value = []
                
                # This should call the performance analyzer
                result = cross_tenant_learning_engine._analyze_tenant_optimization_state(
                    self.test_tenant_id, days_back=7
                )
                
                # Verify the integration call was made
                mock_perf.assert_called()
            
            print("✅ ML Service Integration: PASSED")
            return True
            
        except Exception as e:
            print(f"❌ ML Service Integration: FAILED - {e}")
            return False
    
    def test_ab_testing_integration(self):
        """Test integration with A/B testing orchestrator."""
        try:
            # Test that cross-tenant engine can access A/B testing results
            with patch('app.models.ABTest') as mock_ab_test:
                # Setup mock A/B test data
                mock_test = Mock()
                mock_test.test_id = 'test_123'
                mock_test.status = 'completed'
                mock_test.winning_variant_id = 'variant_a'
                mock_test.success_metrics = ['latency', 'cost']
                mock_test.results_summary = {
                    'recommendation': {
                        'expected_impact': {
                            'improvement_percent': 15.0
                        }
                    }
                }
                
                mock_ab_test.query.filter.return_value.all.return_value = [mock_test]
                
                # Test getting optimization results  
                results = cross_tenant_learning_engine._get_tenant_optimization_results(
                    self.test_tenant_id, days_back=30
                )
                
                # Should return results in expected format
                assert isinstance(results, list)
            
            print("✅ A/B Testing Integration: PASSED")
            return True
            
        except Exception as e:
            print(f"❌ A/B Testing Integration: FAILED - {e}")
            return False
    
    def test_tenant_service_integration(self):
        """Test integration with tenant service."""
        try:
            # Test tenant anonymization
            tenant_id = 'test_tenant_123'
            anonymized = cross_tenant_learning_engine._anonymize_tenant_id(tenant_id)
            
            # Should produce consistent anonymized ID
            assert anonymized != tenant_id
            assert len(anonymized) == 16
            
            # Test tenant consent checking
            with patch.object(tenant_service, 'get_tenant') as mock_get_tenant:
                mock_tenant = Mock()
                mock_tenant.config.custom_settings = {'cross_tenant_learning_enabled': True}
                mock_get_tenant.return_value = mock_tenant
                
                consents = cross_tenant_learning_engine._tenant_consents_to_learning(tenant_id)
                assert consents is True
            
            print("✅ Tenant Service Integration: PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Tenant Service Integration: FAILED - {e}")
            return False
    
    def test_database_models_integration(self):
        """Test integration with database models."""
        try:
            # Test that new models can be imported and used
            from app.models import (
                CrossTenantPattern, TenantOptimizationSummary, 
                CrossTenantRecommendation, LearningInsight, CrossTenantAuditLog
            )
            
            # Test model creation (without database commit)
            pattern = CrossTenantPattern(
                pattern_id='test_pattern',
                pattern_type='performance_improvement',
                pattern_signature='test_signature',
                pattern_description='Test pattern',
                success_count=5,
                failure_count=1,
                success_rate=0.83,
                confidence_score=0.8,
                avg_improvement_percent=15.0,
                median_improvement_percent=14.0,
                std_improvement=2.0,
                applicable_categories=['test'],
                model_types=['test'],
                complexity_ranges=['medium'],
                first_observed=datetime.utcnow(),
                last_updated=datetime.utcnow(),
                tenant_count=3,
                total_applications=6,
                anonymization_level='high',
                min_tenant_threshold_met=True
            )
            
            # Should create without error
            assert pattern.pattern_id == 'test_pattern'
            assert pattern.pattern_type == 'performance_improvement'
            
            print("✅ Database Models Integration: PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Database Models Integration: FAILED - {e}")
            return False
    
    def test_api_endpoints_integration(self):
        """Test integration with API endpoints."""
        try:
            # Test that API endpoints can be imported
            from app.api.cross_tenant_learning import cross_tenant_learning_bp
            from app.blueprints.cross_tenant_learning import cross_tenant_learning_blueprint
            
            # Test blueprint structure
            assert cross_tenant_learning_bp is not None
            assert cross_tenant_learning_blueprint is not None
            
            # Test blueprint URL patterns
            assert cross_tenant_learning_bp.url_prefix == '/api/v1/cross-tenant-learning'
            assert cross_tenant_learning_blueprint.url_prefix == '/cross-tenant-learning'
            
            print("✅ API Endpoints Integration: PASSED") 
            return True
            
        except Exception as e:
            print(f"❌ API Endpoints Integration: FAILED - {e}")
            return False
    
    def test_helper_methods_integration(self):
        """Test integration of helper methods."""
        try:
            # Test that helper methods are installed
            assert hasattr(cross_tenant_learning_engine, '_meets_privacy_threshold')
            assert hasattr(cross_tenant_learning_engine, '_calculate_confidence_score')
            assert hasattr(cross_tenant_learning_engine, '_is_pattern_applicable')
            
            # Test helper method functionality
            from app.services.ml_optimization.cross_tenant_learning_engine import CrossTenantPattern
            
            test_pattern = CrossTenantPattern(
                pattern_id='helper_test',
                pattern_type='test',
                pattern_signature='test',
                pattern_description='test',
                success_count=10,
                failure_count=2,
                success_rate=0.83,
                confidence_score=0.8,
                avg_improvement_percent=20.0,
                median_improvement_percent=19.0,
                std_improvement=3.0,
                applicable_categories=['test'],
                model_types=['test'],
                complexity_ranges=['medium'],
                first_observed=datetime.utcnow(),
                last_updated=datetime.utcnow(),
                tenant_count=5,
                total_applications=12,
                anonymization_level='high',
                min_tenant_threshold_met=True
            )
            
            # Test privacy threshold check
            meets_threshold = cross_tenant_learning_engine._meets_privacy_threshold(test_pattern)
            assert isinstance(meets_threshold, bool)
            
            print("✅ Helper Methods Integration: PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Helper Methods Integration: FAILED - {e}")
            return False
    
    def test_end_to_end_workflow(self):
        """Test complete end-to-end workflow integration."""
        try:
            # Mock all external dependencies
            with patch.object(cross_tenant_learning_engine, '_get_active_tenants_for_learning') as mock_tenants, \
                 patch.object(cross_tenant_learning_engine, '_tenant_consents_to_learning') as mock_consent, \
                 patch.object(cross_tenant_learning_engine, '_get_tenant_optimization_results') as mock_results, \
                 patch.object(cross_tenant_learning_engine, '_analyze_tenant_optimization_state') as mock_state:
                
                # Setup mocks
                mock_tenants.return_value = [self.test_tenant_id]
                mock_consent.return_value = True
                mock_results.return_value = [{
                    'pattern_type': 'performance_improvement',
                    'success': True,
                    'improvement_percent': 20.0,
                    'category': 'test',
                    'model_type': 'test',
                    'complexity': 'medium',
                    'metrics_improved': ['latency']
                }]
                
                from app.services.ml_optimization.cross_tenant_learning_engine import TenantOptimizationSummary
                mock_state.return_value = TenantOptimizationSummary(
                    tenant_hash='test_hash',
                    category_focus=['test'],
                    optimization_patterns=[],
                    performance_tier='medium',
                    optimization_maturity='intermediate',
                    success_metrics={},
                    improvement_trends={},
                    active_months=2,
                    optimization_frequency=1.0,
                    pattern_diversity_score=0.5
                )
                
                # Test complete workflow
                insights = cross_tenant_learning_engine.generate_cross_tenant_insights(
                    self.test_tenant_id, days_back=7
                )
                
                # Verify workflow completed successfully
                assert insights is not None
                assert 'analysis_metadata' in insights
                assert 'privacy_compliance' in insights
                assert insights['privacy_compliance']['anonymization_verified'] is True
                
            print("✅ End-to-End Workflow: PASSED")
            return True
            
        except Exception as e:
            print(f"❌ End-to-End Workflow: FAILED - {e}")
            return False
    
    def test_performance_and_scalability(self):
        """Test performance characteristics and scalability."""
        try:
            # Test caching behavior
            cache_key = 'test_cache_key'
            test_data = {'test': 'data'}
            
            # Test cache methods
            cross_tenant_learning_engine._cache_result(cache_key, test_data)
            assert cross_tenant_learning_engine._is_cached(cache_key)
            
            # Test pattern cleanup performance
            start_time = datetime.utcnow()
            cross_tenant_learning_engine._cleanup_patterns()
            end_time = datetime.utcnow()
            
            cleanup_duration = (end_time - start_time).total_seconds()
            assert cleanup_duration < 1.0  # Should complete quickly
            
            print("✅ Performance and Scalability: PASSED")
            return True
            
        except Exception as e:
            print(f"❌ Performance and Scalability: FAILED - {e}")
            return False


def run_integration_validation():
    """Run the complete integration validation suite."""
    print("🔍 Cross-Tenant Learning Engine Integration Validation")
    print("=" * 60)
    
    validator = TestCrossTenantIntegration()
    validator.setup_method()
    
    # Run all integration tests
    tests = [
        validator.test_ml_service_integration,
        validator.test_ab_testing_integration,
        validator.test_tenant_service_integration,
        validator.test_database_models_integration,
        validator.test_api_endpoints_integration,
        validator.test_helper_methods_integration,
        validator.test_end_to_end_workflow,
        validator.test_performance_and_scalability
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__}: FAILED - {e}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 60)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"🎉 Integration Validation: ALL {total} TESTS PASSED!")
        print("\n✅ Cross-Tenant Learning Engine is successfully integrated with:")
        print("   - ML Optimization Service")
        print("   - A/B Testing Orchestrator") 
        print("   - Tenant Service")
        print("   - Database Models")
        print("   - API Endpoints")
        print("   - Helper Methods")
        print("   - End-to-End Workflow")
        print("   - Performance Requirements")
        return True
    else:
        print(f"⚠️  Integration Validation: {passed}/{total} TESTS PASSED")
        print(f"   {total - passed} integration issues need resolution")
        return False


if __name__ == '__main__':
    success = run_integration_validation()
    sys.exit(0 if success else 1)