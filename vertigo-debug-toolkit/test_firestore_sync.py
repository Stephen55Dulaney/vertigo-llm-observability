#!/usr/bin/env python3
"""
Test script for Firestore sync functionality.

Tests:
1. Firestore client initialization
2. Database connection and schema
3. Sync service functionality
4. Background scheduler (if enabled)
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up environment
os.environ.setdefault('FLASK_SECRET_KEY', 'test-secret-key')
os.environ.setdefault('DATABASE_URL', 'sqlite:///test_vertigo.db')
os.environ.setdefault('GOOGLE_CLOUD_PROJECT', 'vertigo-466116')

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_firestore_client():
    """Test Firestore client initialization."""
    print("=" * 60)
    print("TESTING FIRESTORE CLIENT INITIALIZATION")
    print("=" * 60)
    
    try:
        from app.services.firestore_sync import firestore_sync_service
        
        print(f"✓ Firestore sync service imported successfully")
        print(f"  Project ID: {firestore_sync_service.project_id}")
        print(f"  Client available: {firestore_sync_service.is_available()}")
        
        if firestore_sync_service.is_available():
            print(f"  Collection configs: {list(firestore_sync_service.collection_configs.keys())}")
            
            # Test getting sync statistics
            stats = firestore_sync_service.get_sync_statistics()
            print(f"  Sync stats: {stats}")
            
        return firestore_sync_service.is_available()
        
    except Exception as e:
        print(f"✗ Error testing Firestore client: {e}")
        return False

def test_database_schema():
    """Test database schema and migrations."""
    print("\n" + "=" * 60)
    print("TESTING DATABASE SCHEMA")
    print("=" * 60)
    
    try:
        from app import create_app, db
        from app.models import LiveTrace, SyncStatus, PerformanceMetric
        
        app = create_app()
        with app.app_context():
            # Check if tables exist
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            required_tables = ['live_traces', 'sync_status', 'performance_metrics']
            
            print(f"  Available tables: {tables}")
            
            for table in required_tables:
                if table in tables:
                    print(f"✓ Table '{table}' exists")
                else:
                    print(f"✗ Table '{table}' missing")
                    return False
            
            # Test basic queries
            sync_count = db.session.query(SyncStatus).count()
            trace_count = db.session.query(LiveTrace).count()
            
            print(f"  Sync status records: {sync_count}")
            print(f"  Live traces records: {trace_count}")
            
        return True
        
    except Exception as e:
        print(f"✗ Error testing database schema: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_sync_service():
    """Test sync service functionality."""
    print("\n" + "=" * 60)
    print("TESTING SYNC SERVICE")
    print("=" * 60)
    
    try:
        from app import create_app
        from app.services.firestore_sync import firestore_sync_service
        
        app = create_app()
        with app.app_context():
            
            if not firestore_sync_service.is_available():
                print("⚠ Firestore client not available, skipping sync test")
                return True
            
            # Test getting last sync timestamp
            last_sync = firestore_sync_service.get_last_sync_timestamp('firestore')
            print(f"  Last sync timestamp: {last_sync}")
            
            # Test sync statistics
            stats = firestore_sync_service.get_sync_statistics()
            print(f"  Current sync statistics:")
            for key, value in stats.items():
                if key != 'sync_statuses':
                    print(f"    {key}: {value}")
            
            # Test incremental sync (dry run - just test the method)
            print("  Testing incremental sync...")
            result = firestore_sync_service.sync_traces_from_firestore(hours_back=1)
            
            if result.success:
                print(f"✓ Sync completed successfully")
                print(f"  Records processed: {result.records_processed}")
                if result.errors:
                    print(f"  Warnings: {result.errors}")
            else:
                print(f"✗ Sync failed: {result.errors}")
                return False
            
        return True
        
    except Exception as e:
        print(f"✗ Error testing sync service: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_background_scheduler():
    """Test background scheduler."""
    print("\n" + "=" * 60)
    print("TESTING BACKGROUND SCHEDULER")
    print("=" * 60)
    
    try:
        from app import create_app
        from app.services.sync_scheduler import sync_scheduler
        
        app = create_app()
        with app.app_context():
            
            # Test scheduler status
            status = sync_scheduler.get_scheduler_status()
            print(f"  Scheduler running: {status.get('is_running')}")
            print(f"  Sync interval: {status.get('sync_interval_minutes')} minutes")
            print(f"  Max workers: {status.get('max_workers')}")
            print(f"  Firestore available: {status.get('firestore_available')}")
            
            # Show scheduled jobs
            jobs = status.get('jobs', [])
            print(f"  Scheduled jobs ({len(jobs)}):")
            for job in jobs:
                print(f"    - {job['name']} (next: {job['next_run_time']})")
            
            # Show statistics
            stats = status.get('stats', {})
            print(f"  Statistics:")
            for key, value in stats.items():
                if key not in ['scheduler_started_at'] or value:
                    print(f"    {key}: {value}")
            
        return True
        
    except Exception as e:
        print(f"✗ Error testing background scheduler: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoints():
    """Test API endpoints."""
    print("\n" + "=" * 60)
    print("TESTING API ENDPOINTS")
    print("=" * 60)
    
    try:
        from app import create_app
        
        app = create_app()
        client = app.test_client()
        
        # Test sync status endpoint (should require auth)
        response = client.get('/api/sync/status')
        print(f"  GET /api/sync/status: {response.status_code}")
        
        # Test sync config endpoint (should require auth)
        response = client.get('/api/sync/config')
        print(f"  GET /api/sync/config: {response.status_code}")
        
        # Test that endpoints are registered
        endpoints = []
        for rule in app.url_map.iter_rules():
            if 'sync' in rule.rule:
                endpoints.append(f"{rule.methods} {rule.rule}")
        
        print(f"  Registered sync endpoints:")
        for endpoint in sorted(endpoints):
            print(f"    {endpoint}")
        
        return True
        
    except Exception as e:
        print(f"✗ Error testing API endpoints: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("🔥 FIRESTORE SYNC SERVICE TEST SUITE")
    print(f"Time: {datetime.now()}")
    print(f"Project: {os.environ.get('GOOGLE_CLOUD_PROJECT', 'Not set')}")
    
    tests = [
        ("Firestore Client", test_firestore_client),
        ("Database Schema", test_database_schema),
        ("Sync Service", test_sync_service),
        ("Background Scheduler", test_background_scheduler),
        ("API Endpoints", test_api_endpoints),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"\n✗ CRITICAL ERROR in {test_name}: {e}")
            results[test_name] = False
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(results.values())
    total = len(results)
    
    for test_name, passed_test in results.items():
        status = "✓ PASS" if passed_test else "✗ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nRESULT: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Firestore sync service is ready.")
        return 0
    else:
        print("⚠ SOME TESTS FAILED. Check the output above for details.")
        return 1

if __name__ == '__main__':
    sys.exit(main())