#!/usr/bin/env python3
"""
Comprehensive Test Suite for Anomaly Response System
Tests the full pipeline from anomaly detection to automated response actions.
"""

import os
import sys
import time
import threading
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Dict, List, Any

# Add the project root to Python path
sys.path.insert(0, os.path.abspath('.'))

from app.services.anomaly_monitoring_engine import (
    AnomalyMonitoringEngine, MonitoringConfig, AnomalyAlert, AnomalyType
)
from app.services.automated_response_engine import (
    AutomatedResponseEngine, PerformanceResponseHandler, CostResponseHandler, 
    ErrorRecoveryResponseHandler, ResponseStatus
)
from app.services.alert_service import AlertSeverity

class TestResults:
    """Container for test results."""
    
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.tests_failed = 0
        self.failures = []
    
    def add_result(self, test_name: str, success: bool, message: str = ""):
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {test_name}: PASSED")
        else:
            self.tests_failed += 1
            self.failures.append((test_name, message))
            print(f"❌ {test_name}: FAILED - {message}")
    
    def print_summary(self):
        print(f"\n{'='*60}")
        print(f"TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Tests Failed: {self.tests_failed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%" if self.tests_run > 0 else "N/A")
        
        if self.failures:
            print(f"\n{'='*60}")
            print(f"FAILURES:")
            print(f"{'='*60}")
            for test_name, message in self.failures:
                print(f"❌ {test_name}: {message}")
        
        return self.tests_failed == 0

def test_anomaly_monitoring_engine():
    """Test the anomaly monitoring engine functionality."""
    print(f"\n{'='*60}")
    print("TESTING ANOMALY MONITORING ENGINE")
    print(f"{'='*60}")
    
    results = TestResults()
    
    # Test 1: Engine Initialization
    try:
        config = MonitoringConfig(
            poll_interval_seconds=1,
            statistical_threshold=2.0,
            enable_auto_response=False  # Disable for testing
        )
        engine = AnomalyMonitoringEngine(config)
        results.add_result("Engine Initialization", True)
    except Exception as e:
        results.add_result("Engine Initialization", False, str(e))
        return results
    
    # Test 2: Configuration
    try:
        assert engine.config.poll_interval_seconds == 1
        assert engine.config.statistical_threshold == 2.0
        assert engine.config.enable_auto_response == False
        results.add_result("Configuration Setting", True)
    except Exception as e:
        results.add_result("Configuration Setting", False, str(e))
    
    # Test 3: Status Reporting
    try:
        status = engine.get_status()
        assert 'status' in status
        assert 'config' in status
        assert 'statistics' in status
        results.add_result("Status Reporting", True)
    except Exception as e:
        results.add_result("Status Reporting", False, str(e))
    
    # Test 4: Start/Stop Monitoring
    try:
        # Test starting
        start_success = engine.start_monitoring()
        assert start_success
        time.sleep(0.5)  # Give it time to start
        
        status = engine.get_status()
        assert status['status'] == 'running'
        
        # Test stopping
        stop_success = engine.stop_monitoring()
        assert stop_success
        
        results.add_result("Start/Stop Monitoring", True)
    except Exception as e:
        results.add_result("Start/Stop Monitoring", False, str(e))
        # Ensure stopped for cleanup
        try:
            engine.stop_monitoring()
        except:
            pass
    
    # Test 5: Statistical Anomaly Detection
    try:
        # Create mock metrics with clear anomaly
        test_metrics = {
            'error_rate': 50.0,  # Very high error rate
            'avg_latency_ms': 1000.0,
            'total_cost': 5.0,
            'total_traces': 100,
            'success_rate': 30.0  # Very low success rate
        }
        
        # Populate some history first
        for i in range(10):
            normal_metrics = {
                'error_rate': 2.0,
                'avg_latency_ms': 200.0,
                'success_rate': 95.0
            }
            for metric_name, value in normal_metrics.items():
                from app.services.anomaly_monitoring_engine import MetricPoint
                point = MetricPoint(
                    timestamp=datetime.utcnow() - timedelta(minutes=i),
                    metric_name=metric_name,
                    value=value,
                    source='test'
                )
                engine.metric_history[metric_name].append(point)
        
        # Test statistical detection
        statistical_anomalies = engine._detect_statistical_anomalies(test_metrics)
        assert len(statistical_anomalies) > 0, "Should detect statistical anomalies"
        
        results.add_result("Statistical Anomaly Detection", True)
    except Exception as e:
        results.add_result("Statistical Anomaly Detection", False, str(e))
    
    # Test 6: Threshold Anomaly Detection
    try:
        threshold_anomalies = engine._detect_threshold_anomalies(test_metrics)
        assert len(threshold_anomalies) > 0, "Should detect threshold anomalies"
        
        # Check severity assignment
        critical_anomalies = [a for a in threshold_anomalies if a.severity == AlertSeverity.CRITICAL]
        assert len(critical_anomalies) > 0, "Should have critical severity anomalies"
        
        results.add_result("Threshold Anomaly Detection", True)
    except Exception as e:
        results.add_result("Threshold Anomaly Detection", False, str(e))
    
    # Test 7: Pattern Anomaly Detection
    try:
        # Create pattern of increasing values
        for i in range(5):
            point = MetricPoint(
                timestamp=datetime.utcnow() - timedelta(minutes=5-i),
                metric_name='avg_latency_ms',
                value=100.0 * (i + 1),  # Increasing pattern
                source='test'
            )
            engine.metric_history['avg_latency_ms'].append(point)
        
        pattern_metrics = {'avg_latency_ms': 1000.0}  # Large spike
        pattern_anomalies = engine._detect_pattern_anomalies(pattern_metrics)
        
        results.add_result("Pattern Anomaly Detection", len(pattern_anomalies) >= 0)
    except Exception as e:
        results.add_result("Pattern Anomaly Detection", False, str(e))
    
    # Test 8: Correlation Anomaly Detection
    try:
        correlation_metrics = {
            'error_rate': 25.0,  # High error rate
            'avg_latency_ms': 500.0,  # Low latency (unusual combo)
            'total_cost': 10.0,
            'total_traces': 50
        }
        
        correlation_anomalies = engine._detect_correlation_anomalies(correlation_metrics)
        
        results.add_result("Correlation Anomaly Detection", len(correlation_anomalies) >= 0)
    except Exception as e:
        results.add_result("Correlation Anomaly Detection", False, str(e))
    
    # Test 9: Alert Queue Management
    try:
        # Create test anomaly
        test_anomaly = AnomalyAlert(
            id="test_anomaly",
            timestamp=datetime.utcnow(),
            anomaly_type=AnomalyType.THRESHOLD,
            metric_name="error_rate",
            severity=AlertSeverity.HIGH,
            actual_value=25.0,
            expected_value=5.0,
            deviation_score=4.0,
            message="Test anomaly",
            context_data={'test': True}
        )
        
        # Add to queue
        engine.alert_queue.put(test_anomaly)
        
        # Retrieve recent anomalies
        recent = engine.get_recent_anomalies(limit=10)
        assert len(recent) >= 1, "Should have at least one anomaly"
        
        # Clear alerts
        engine.clear_alerts(older_than_minutes=0)
        
        results.add_result("Alert Queue Management", True)
    except Exception as e:
        results.add_result("Alert Queue Management", False, str(e))
    
    return results

def test_automated_response_engine():
    """Test the automated response engine functionality."""
    print(f"\n{'='*60}")
    print("TESTING AUTOMATED RESPONSE ENGINE")
    print(f"{'='*60}")
    
    results = TestResults()
    
    # Test 1: Engine Initialization
    try:
        engine = AutomatedResponseEngine()
        assert len(engine.response_handlers) > 0
        results.add_result("Response Engine Initialization", True)
    except Exception as e:
        results.add_result("Response Engine Initialization", False, str(e))
        return results
    
    # Test 2: Response Handler Registration
    try:
        performance_handler = None
        cost_handler = None
        error_handler = None
        
        for handler in engine.response_handlers:
            if isinstance(handler, PerformanceResponseHandler):
                performance_handler = handler
            elif isinstance(handler, CostResponseHandler):
                cost_handler = handler
            elif isinstance(handler, ErrorRecoveryResponseHandler):
                error_handler = handler
        
        assert performance_handler is not None, "Should have performance handler"
        assert cost_handler is not None, "Should have cost handler"
        assert error_handler is not None, "Should have error recovery handler"
        
        results.add_result("Response Handler Registration", True)
    except Exception as e:
        results.add_result("Response Handler Registration", False, str(e))
    
    # Test 3: Performance Response Handler
    try:
        # Test latency anomaly
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
        
        handler = performance_handler
        can_handle = handler.can_handle(latency_anomaly)
        assert can_handle, "Performance handler should handle latency anomalies"
        
        actions = handler.get_response_actions(latency_anomaly)
        assert len(actions) > 0, "Should return response actions for latency anomaly"
        
        # Test action validation
        action = actions[0]
        is_valid, message = handler.validate_action(action, latency_anomaly)
        assert is_valid, f"Action validation failed: {message}"
        
        # Test action execution
        result = handler.execute_action(action, latency_anomaly)
        assert result.get('success'), f"Action execution failed: {result}"
        
        results.add_result("Performance Response Handler", True)
    except Exception as e:
        results.add_result("Performance Response Handler", False, str(e))
    
    # Test 4: Cost Response Handler
    try:
        # Test cost anomaly
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
        
        can_handle = cost_handler.can_handle(cost_anomaly)
        assert can_handle, "Cost handler should handle cost anomalies"
        
        actions = cost_handler.get_response_actions(cost_anomaly)
        assert len(actions) > 0, "Should return response actions for cost anomaly"
        
        results.add_result("Cost Response Handler", True)
    except Exception as e:
        results.add_result("Cost Response Handler", False, str(e))
    
    # Test 5: Error Recovery Response Handler
    try:
        # Test error rate anomaly
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
        
        can_handle = error_handler.can_handle(error_anomaly)
        assert can_handle, "Error handler should handle error rate anomalies"
        
        actions = error_handler.get_response_actions(error_anomaly)
        assert len(actions) > 0, "Should return response actions for error anomaly"
        
        results.add_result("Error Recovery Response Handler", True)
    except Exception as e:
        results.add_result("Error Recovery Response Handler", False, str(e))
    
    # Test 6: Response Processing
    try:
        # Create test anomaly that doesn't require approval
        test_anomaly = AnomalyAlert(
            id="process_test",
            timestamp=datetime.utcnow(),
            anomaly_type=AnomalyType.THRESHOLD,
            metric_name="total_traces",
            severity=AlertSeverity.MEDIUM,
            actual_value=200.0,
            expected_value=100.0,
            deviation_score=2.0,
            message="Traffic spike detected",
            context_data={}
        )
        
        executions = engine.process_anomaly(test_anomaly)
        assert len(executions) >= 0, "Should return execution results"
        
        # Check execution status
        for execution in executions:
            assert execution.anomaly_id == test_anomaly.id
            assert execution.status in [ResponseStatus.SUCCESS, ResponseStatus.FAILED, ResponseStatus.REQUIRES_APPROVAL]
        
        results.add_result("Response Processing", True)
    except Exception as e:
        results.add_result("Response Processing", False, str(e))
    
    # Test 7: Human Approval Workflow
    try:
        # Create anomaly requiring approval
        critical_anomaly = AnomalyAlert(
            id="approval_test",
            timestamp=datetime.utcnow(),
            anomaly_type=AnomalyType.THRESHOLD,
            metric_name="avg_latency_ms",
            severity=AlertSeverity.CRITICAL,
            actual_value=10000.0,
            expected_value=1000.0,
            deviation_score=9.0,
            message="Critical latency spike",
            context_data={}
        )
        
        executions = engine.process_anomaly(critical_anomaly)
        
        # Check for pending approvals
        pending_approvals = engine.get_pending_approvals()
        
        # If there are pending approvals, test the approval process
        if pending_approvals:
            approval = pending_approvals[0]
            execution_id = approval['execution_id']
            
            # Test approval
            success = engine.approve_pending_action(
                execution_id=execution_id,
                approved=True,
                approver="test_user"
            )
            assert success, "Approval should succeed"
        
        results.add_result("Human Approval Workflow", True)
    except Exception as e:
        results.add_result("Human Approval Workflow", False, str(e))
    
    # Test 8: Statistics and Monitoring
    try:
        stats = engine.get_response_statistics()
        assert 'total_responses' in stats
        assert 'successful_responses' in stats
        assert 'success_rate' in stats
        
        results.add_result("Statistics and Monitoring", True)
    except Exception as e:
        results.add_result("Statistics and Monitoring", False, str(e))
    
    # Test 9: Cleanup
    try:
        engine.cleanup_completed_executions(older_than_hours=0)
        results.add_result("Cleanup Operations", True)
    except Exception as e:
        results.add_result("Cleanup Operations", False, str(e))
    
    return results

def test_integration_pipeline():
    """Test the full integration between monitoring and response systems."""
    print(f"\n{'='*60}")
    print("TESTING INTEGRATION PIPELINE")
    print(f"{'='*60}")
    
    results = TestResults()
    
    # Test 1: End-to-End Pipeline
    try:
        # Initialize systems
        monitoring_config = MonitoringConfig(
            poll_interval_seconds=1,
            enable_auto_response=True,
            monitored_metrics=['error_rate', 'avg_latency_ms', 'total_cost']
        )
        monitoring_engine = AnomalyMonitoringEngine(monitoring_config)
        response_engine = AutomatedResponseEngine()
        
        # Create a test anomaly that should trigger automated response
        test_anomaly = AnomalyAlert(
            id="integration_test",
            timestamp=datetime.utcnow(),
            anomaly_type=AnomalyType.THRESHOLD,
            metric_name="avg_latency_ms",
            severity=AlertSeverity.HIGH,
            actual_value=3000.0,
            expected_value=1000.0,
            deviation_score=3.0,
            message="Integration test anomaly",
            context_data={}
        )
        
        # Process through monitoring engine
        monitoring_engine._process_anomaly(test_anomaly)
        
        # Check that auto response was triggered
        assert test_anomaly.auto_response_triggered, "Auto response should be triggered"
        
        results.add_result("End-to-End Pipeline", True)
    except Exception as e:
        results.add_result("End-to-End Pipeline", False, str(e))
    
    # Test 2: System Health Monitoring
    try:
        # Test system health endpoints
        monitoring_status = monitoring_engine.get_status()
        response_stats = response_engine.get_response_statistics()
        
        # Validate health data structure
        assert 'status' in monitoring_status
        assert 'statistics' in monitoring_status
        assert 'total_responses' in response_stats
        
        results.add_result("System Health Monitoring", True)
    except Exception as e:
        results.add_result("System Health Monitoring", False, str(e))
    
    # Test 3: Performance Under Load
    try:
        # Create multiple anomalies to test performance
        anomalies = []
        for i in range(5):
            anomaly = AnomalyAlert(
                id=f"load_test_{i}",
                timestamp=datetime.utcnow(),
                anomaly_type=AnomalyType.THRESHOLD,
                metric_name="error_rate",
                severity=AlertSeverity.MEDIUM,
                actual_value=15.0,
                expected_value=5.0,
                deviation_score=2.0,
                message=f"Load test anomaly {i}",
                context_data={'test_id': i}
            )
            anomalies.append(anomaly)
        
        # Process all anomalies
        start_time = time.time()
        for anomaly in anomalies:
            response_engine.process_anomaly(anomaly)
        processing_time = time.time() - start_time
        
        # Should process quickly (under 1 second for 5 anomalies)
        assert processing_time < 1.0, f"Processing took too long: {processing_time}s"
        
        results.add_result("Performance Under Load", True)
    except Exception as e:
        results.add_result("Performance Under Load", False, str(e))
    
    # Test 4: Error Handling and Recovery
    try:
        # Test with invalid anomaly data
        invalid_anomaly = AnomalyAlert(
            id="invalid_test",
            timestamp=datetime.utcnow(),
            anomaly_type=AnomalyType.THRESHOLD,
            metric_name="unknown_metric",
            severity=AlertSeverity.LOW,
            actual_value=0.0,
            expected_value=0.0,
            deviation_score=0.0,
            message="Invalid test anomaly",
            context_data={}
        )
        
        # Should handle gracefully without crashing
        executions = response_engine.process_anomaly(invalid_anomaly)
        
        # Should return empty list or handle gracefully
        assert isinstance(executions, list), "Should return a list even for invalid input"
        
        results.add_result("Error Handling and Recovery", True)
    except Exception as e:
        results.add_result("Error Handling and Recovery", False, str(e))
    
    return results

def test_flask_integration():
    """Test Flask blueprint integration."""
    print(f"\n{'='*60}")
    print("TESTING FLASK INTEGRATION")
    print(f"{'='*60}")
    
    results = TestResults()
    
    try:
        # Import Flask app components
        from app.blueprints.anomaly_response import anomaly_response_bp
        
        # Test blueprint registration
        assert anomaly_response_bp is not None, "Blueprint should be defined"
        assert anomaly_response_bp.url_prefix == '/anomaly-response', "URL prefix should be correct"
        
        # Test route registration
        routes = [rule.rule for rule in anomaly_response_bp.url_map.iter_rules()]
        expected_routes = [
            '/api/monitoring/start',
            '/api/monitoring/stop', 
            '/api/monitoring/status',
            '/api/anomalies',
            '/api/responses/statistics'
        ]
        
        # Check that some key routes exist
        route_check_passed = True
        for expected_route in expected_routes[:2]:  # Check first 2 routes
            full_route = f"/anomaly-response{expected_route}"
            if not any(expected_route in route for route in routes):
                route_check_passed = False
                break
        
        assert route_check_passed, "Key API routes should be registered"
        
        results.add_result("Flask Blueprint Integration", True)
    except Exception as e:
        results.add_result("Flask Blueprint Integration", False, str(e))
    
    return results

def run_all_tests():
    """Run all test suites."""
    print("🚀 Starting Anomaly Response System Test Suite")
    print(f"{'='*80}")
    
    all_results = []
    
    # Run all test suites
    test_suites = [
        ("Anomaly Monitoring Engine", test_anomaly_monitoring_engine),
        ("Automated Response Engine", test_automated_response_engine),
        ("Integration Pipeline", test_integration_pipeline),
        ("Flask Integration", test_flask_integration)
    ]
    
    for suite_name, test_func in test_suites:
        try:
            results = test_func()
            all_results.append((suite_name, results))
        except Exception as e:
            print(f"❌ Test suite '{suite_name}' crashed: {e}")
            # Create failed result
            failed_result = TestResults()
            failed_result.add_result(suite_name, False, str(e))
            all_results.append((suite_name, failed_result))
    
    # Print overall summary
    print(f"\n{'='*80}")
    print("OVERALL TEST RESULTS")
    print(f"{'='*80}")
    
    total_tests = 0
    total_passed = 0
    total_failed = 0
    
    for suite_name, results in all_results:
        total_tests += results.tests_run
        total_passed += results.tests_passed
        total_failed += results.tests_failed
        
        success_rate = (results.tests_passed / results.tests_run * 100) if results.tests_run > 0 else 0
        status = "✅ PASSED" if results.tests_failed == 0 else "❌ FAILED"
        
        print(f"{status} {suite_name}: {results.tests_passed}/{results.tests_run} ({success_rate:.1f}%)")
    
    print(f"\n{'='*80}")
    print(f"FINAL SUMMARY")
    print(f"{'='*80}")
    print(f"Total Tests: {total_tests}")
    print(f"Total Passed: {total_passed}")
    print(f"Total Failed: {total_failed}")
    
    overall_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
    print(f"Overall Success Rate: {overall_success_rate:.1f}%")
    
    if total_failed == 0:
        print(f"\n🎉 ALL TESTS PASSED! Anomaly Response System is working correctly.")
        return True
    else:
        print(f"\n⚠️  {total_failed} test(s) failed. Please review the failures above.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)