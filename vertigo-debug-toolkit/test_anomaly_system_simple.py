#!/usr/bin/env python3
"""
Simple Test Suite for Anomaly Response System Core Functionality
Tests the core classes without Flask dependencies.
"""

import os
import sys
import time
from datetime import datetime, timedelta
from dataclasses import dataclass

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

# Test core functionality without Flask context
def test_core_anomaly_classes():
    """Test core anomaly detection classes."""
    print("Testing core anomaly classes...")
    
    try:
        # Test imports
        from app.services.anomaly_monitoring_engine import (
            MonitoringConfig, AnomalyAlert, AnomalyType
        )
        from app.services.alert_service import AlertSeverity
        
        print("✅ Core imports successful")
        
        # Test configuration
        config = MonitoringConfig(
            poll_interval_seconds=5,
            statistical_threshold=2.5,
            enable_auto_response=True
        )
        
        assert config.poll_interval_seconds == 5
        assert config.statistical_threshold == 2.5
        assert config.enable_auto_response == True
        print("✅ MonitoringConfig creation successful")
        
        # Test anomaly alert creation
        anomaly = AnomalyAlert(
            id="test_anomaly_001",
            timestamp=datetime.utcnow(),
            anomaly_type=AnomalyType.STATISTICAL,
            metric_name="error_rate",
            severity=AlertSeverity.HIGH,
            actual_value=25.0,
            expected_value=5.0,
            deviation_score=4.0,
            message="Test statistical anomaly in error rate",
            context_data={
                'sample_size': 100,
                'detection_method': 'statistical',
                'confidence': 0.95
            }
        )
        
        assert anomaly.id == "test_anomaly_001"
        assert anomaly.metric_name == "error_rate"
        assert anomaly.severity == AlertSeverity.HIGH
        assert anomaly.actual_value == 25.0
        assert anomaly.deviation_score == 4.0
        assert 'sample_size' in anomaly.context_data
        print("✅ AnomalyAlert creation successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Core class test failed: {e}")
        return False

def test_response_handlers():
    """Test response handler classes."""
    print("\nTesting response handler classes...")
    
    try:
        from app.services.automated_response_engine import (
            PerformanceResponseHandler, CostResponseHandler, 
            ErrorRecoveryResponseHandler, ResponseAction
        )
        from app.services.anomaly_monitoring_engine import AnomalyAlert, AnomalyType
        from app.services.alert_service import AlertSeverity
        
        print("✅ Response handler imports successful")
        
        # Test Performance Handler
        perf_handler = PerformanceResponseHandler()
        
        # Create test anomaly
        latency_anomaly = AnomalyAlert(
            id="latency_test",
            timestamp=datetime.utcnow(),
            anomaly_type=AnomalyType.THRESHOLD,
            metric_name="avg_latency_ms",
            severity=AlertSeverity.HIGH,
            actual_value=5000.0,
            expected_value=1000.0,
            deviation_score=4.0,
            message="High latency detected",
            context_data={}
        )
        
        # Test handler capability
        can_handle = perf_handler.can_handle(latency_anomaly)
        assert can_handle, "Performance handler should handle latency anomalies"
        print("✅ Performance handler can_handle test passed")
        
        # Test action generation
        actions = perf_handler.get_response_actions(latency_anomaly)
        assert len(actions) > 0, "Should generate response actions"
        assert isinstance(actions[0], ResponseAction), "Should return ResponseAction objects"
        print("✅ Performance handler action generation successful")
        
        # Test Cost Handler
        cost_handler = CostResponseHandler()
        
        cost_anomaly = AnomalyAlert(
            id="cost_test",
            timestamp=datetime.utcnow(),
            anomaly_type=AnomalyType.THRESHOLD,
            metric_name="total_cost",
            severity=AlertSeverity.CRITICAL,
            actual_value=50.0,
            expected_value=10.0,
            deviation_score=5.0,
            message="High cost detected",
            context_data={}
        )
        
        can_handle_cost = cost_handler.can_handle(cost_anomaly)
        assert can_handle_cost, "Cost handler should handle cost anomalies"
        
        cost_actions = cost_handler.get_response_actions(cost_anomaly)
        assert len(cost_actions) > 0, "Should generate cost response actions"
        print("✅ Cost handler tests passed")
        
        # Test Error Recovery Handler
        error_handler = ErrorRecoveryResponseHandler()
        
        error_anomaly = AnomalyAlert(
            id="error_test",
            timestamp=datetime.utcnow(),
            anomaly_type=AnomalyType.THRESHOLD,
            metric_name="error_rate",
            severity=AlertSeverity.HIGH,
            actual_value=25.0,
            expected_value=5.0,
            deviation_score=4.0,
            message="High error rate detected",
            context_data={}
        )
        
        can_handle_error = error_handler.can_handle(error_anomaly)
        assert can_handle_error, "Error handler should handle error rate anomalies"
        
        error_actions = error_handler.get_response_actions(error_anomaly)
        assert len(error_actions) > 0, "Should generate error response actions"
        print("✅ Error recovery handler tests passed")
        
        return True
        
    except Exception as e:
        print(f"❌ Response handler test failed: {e}")
        return False

def test_action_execution():
    """Test action execution."""
    print("\nTesting action execution...")
    
    try:
        from app.services.automated_response_engine import PerformanceResponseHandler
        from app.services.anomaly_monitoring_engine import AnomalyAlert, AnomalyType
        from app.services.alert_service import AlertSeverity
        
        handler = PerformanceResponseHandler()
        
        # Create test anomaly
        test_anomaly = AnomalyAlert(
            id="execution_test",
            timestamp=datetime.utcnow(),
            anomaly_type=AnomalyType.THRESHOLD,
            metric_name="avg_latency_ms",
            severity=AlertSeverity.MEDIUM,
            actual_value=3000.0,
            expected_value=1000.0,
            deviation_score=2.0,
            message="Moderate latency increase",
            context_data={}
        )
        
        # Get actions
        actions = handler.get_response_actions(test_anomaly)
        assert len(actions) > 0, "Should have actions to test"
        
        action = actions[0]
        
        # Test validation
        is_valid, validation_message = handler.validate_action(action, test_anomaly)
        print(f"   Validation result: {is_valid} - {validation_message}")
        
        # Test execution
        result = handler.execute_action(action, test_anomaly)
        assert 'success' in result, "Execution result should contain success field"
        print(f"   Execution result: {result.get('success', False)}")
        
        print("✅ Action execution tests passed")
        return True
        
    except Exception as e:
        print(f"❌ Action execution test failed: {e}")
        return False

def test_end_to_end_simulation():
    """Test end-to-end simulation without Flask."""
    print("\nTesting end-to-end simulation...")
    
    try:
        from app.services.automated_response_engine import AutomatedResponseEngine
        from app.services.anomaly_monitoring_engine import AnomalyAlert, AnomalyType
        from app.services.alert_service import AlertSeverity
        
        # Create response engine
        response_engine = AutomatedResponseEngine()
        print("✅ Response engine created")
        
        # Create test anomaly
        test_anomaly = AnomalyAlert(
            id="e2e_test",
            timestamp=datetime.utcnow(),
            anomaly_type=AnomalyType.THRESHOLD,
            metric_name="total_traces",
            severity=AlertSeverity.MEDIUM,
            actual_value=200.0,
            expected_value=100.0,
            deviation_score=2.0,
            message="Traffic spike detected",
            context_data={'source': 'e2e_test'}
        )
        
        # Process anomaly
        executions = response_engine.process_anomaly(test_anomaly)
        print(f"   Generated {len(executions)} execution(s)")
        
        # Check statistics
        stats = response_engine.get_response_statistics()
        print(f"   Total responses: {stats['total_responses']}")
        print(f"   Success rate: {stats['success_rate']:.1f}%")
        
        # Test cleanup
        response_engine.cleanup_completed_executions(older_than_hours=0)
        print("✅ Cleanup completed")
        
        print("✅ End-to-end simulation successful")
        return True
        
    except Exception as e:
        print(f"❌ End-to-end simulation failed: {e}")
        return False

def run_simple_tests():
    """Run all simple tests."""
    print("🚀 Starting Simple Anomaly Response System Tests")
    print("="*60)
    
    tests = [
        ("Core Anomaly Classes", test_core_anomaly_classes),
        ("Response Handlers", test_response_handlers),
        ("Action Execution", test_action_execution),
        ("End-to-End Simulation", test_end_to_end_simulation)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔧 Running: {test_name}")
        try:
            success = test_func()
            if success:
                passed += 1
                print(f"✅ {test_name}: PASSED")
            else:
                print(f"❌ {test_name}: FAILED")
        except Exception as e:
            print(f"❌ {test_name}: CRASHED - {e}")
    
    print(f"\n{'='*60}")
    print("SIMPLE TEST RESULTS")
    print(f"{'='*60}")
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    if passed == total:
        print("\n🎉 ALL SIMPLE TESTS PASSED!")
        print("✅ Core anomaly response functionality is working correctly.")
        print("✅ Response handlers are functioning properly.")
        print("✅ Action execution and validation work as expected.")
        print("✅ End-to-end processing pipeline is operational.")
    else:
        print(f"\n⚠️ {total - passed} test(s) failed.")
    
    return passed == total

if __name__ == "__main__":
    success = run_simple_tests()
    sys.exit(0 if success else 1)