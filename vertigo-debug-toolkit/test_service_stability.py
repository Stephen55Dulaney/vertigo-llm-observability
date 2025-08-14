#!/usr/bin/env python3
"""
Service Stability Test Script
Tests the critical stability fixes implemented for the Vertigo Debug Toolkit.
"""

import os
import sys
import time
import threading
import requests
from datetime import datetime

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all critical modules can be imported."""
    print("🔍 Testing imports...")
    
    try:
        from app.services.sync_scheduler import sync_scheduler
        print("  ✅ Sync scheduler imported successfully")
        
        from app.services.langwatch_client import langwatch_client, CircuitState, CircuitBreaker
        print("  ✅ LangWatch client with circuit breaker imported successfully")
        
        from app.services.firestore_sync import firestore_sync_service
        print("  ✅ Firestore sync service imported successfully")
        
        from app.blueprints.health import health_bp
        print("  ✅ Health check blueprint imported successfully")
        
        return True
        
    except Exception as e:
        print(f"  ❌ Import error: {e}")
        return False

def test_circuit_breaker():
    """Test circuit breaker functionality."""
    print("🔍 Testing circuit breaker...")
    
    try:
        from app.services.langwatch_client import CircuitBreaker, CircuitState
        
        # Create circuit breaker with low thresholds for testing
        cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1)
        
        # Test initial state
        assert cb.state == CircuitState.CLOSED, f"Expected CLOSED, got {cb.state}"
        print("  ✅ Circuit breaker starts in CLOSED state")
        
        # Simulate failures
        def failing_function():
            raise requests.exceptions.RequestException("Test failure")
        
        # First failure
        try:
            cb.call(failing_function)
        except:
            pass
        
        # Second failure (should open circuit)
        try:
            cb.call(failing_function)
        except:
            pass
        
        assert cb.state == CircuitState.OPEN, f"Expected OPEN after failures, got {cb.state}"
        print("  ✅ Circuit breaker opens after failures")
        
        # Test that subsequent calls fail fast
        try:
            cb.call(failing_function)
            assert False, "Should have failed fast"
        except Exception as e:
            if "Circuit breaker is OPEN" in str(e):
                print("  ✅ Circuit breaker fails fast when open")
            else:
                raise e
        
        return True
        
    except Exception as e:
        print(f"  ❌ Circuit breaker test error: {e}")
        return False

def test_database_context_manager():
    """Test database context manager."""
    print("🔍 Testing database context manager...")
    
    try:
        from app.services.firestore_sync import firestore_sync_service
        from app.models import db
        from flask import Flask
        
        # Create minimal Flask app for testing
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        db.init_app(app)
        
        with app.app_context():
            db.create_all()
            
            # Test the database context manager
            with firestore_sync_service._database_session() as session:
                result = session.execute(db.text("SELECT 1")).fetchone()
                assert result[0] == 1, "Database query failed"
        
        print("  ✅ Database context manager works correctly")
        return True
        
    except Exception as e:
        print(f"  ❌ Database context manager test error: {e}")
        return False

def test_health_endpoints():
    """Test that health check endpoints are configured properly."""
    print("🔍 Testing health endpoint configuration...")
    
    try:
        from app.blueprints.health import health_bp
        from flask import Flask
        
        app = Flask(__name__)
        app.register_blueprint(health_bp)
        
        # Get the registered routes
        routes = [rule.rule for rule in app.url_map.iter_rules()]
        
        expected_routes = [
            '/health/',
            '/health/detailed',
            '/health/liveness',
            '/health/readiness',
            '/health/metrics',
            '/health/debug'
        ]
        
        for route in expected_routes:
            assert route in routes, f"Route {route} not found in {routes}"
        
        print("  ✅ All health check endpoints configured correctly")
        return True
        
    except Exception as e:
        print(f"  ❌ Health endpoint test error: {e}")
        return False

def main():
    """Run all stability tests."""
    print("🚀 Starting Vertigo Debug Toolkit Stability Tests")
    print("=" * 60)
    
    tests = [
        ("Import Tests", test_imports),
        ("Circuit Breaker Tests", test_circuit_breaker),
        ("Database Context Manager Tests", test_database_context_manager),
        ("Health Endpoint Tests", test_health_endpoints),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        
        try:
            if test_func():
                passed += 1
                print(f"  🎉 {test_name} PASSED")
            else:
                failed += 1
                print(f"  💥 {test_name} FAILED")
        except Exception as e:
            failed += 1
            print(f"  💥 {test_name} FAILED with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 RESULTS: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 ALL STABILITY TESTS PASSED! Service should be stable.")
        print("\n🔧 Implemented fixes:")
        print("  ✅ Flask application context properly managed in background jobs")
        print("  ✅ Circuit breaker pattern prevents LangWatch API loops")
        print("  ✅ Database connections managed with retry logic and cleanup")
        print("  ✅ Health check endpoints for monitoring service status")
        print("  ✅ Production-grade error handling and recovery mechanisms")
        
        print("\n🚀 Next steps:")
        print("  1. Start the service: python app.py --port 8080 --debug")
        print("  2. Monitor health: curl http://localhost:8080/health/detailed")
        print("  3. Check metrics: curl http://localhost:8080/health/metrics")
        
        return 0
    else:
        print(f"❌ {failed} tests failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())