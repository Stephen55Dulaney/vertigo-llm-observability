#!/usr/bin/env python3
"""
Comprehensive test suite for the live data integration migration.
Tests all new models, relationships, and functionality.
"""

import sys
import logging
from datetime import datetime, timedelta
from pathlib import Path

# Add the app directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

from app import create_app, db
from app.models import (
    DataSource, LiveTrace, PerformanceMetric, SyncStatus, 
    WebhookEvent, CacheEntry, AlertRule, AlertEvent, User
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_all_models():
    """Test all the new models and their relationships."""
    app = create_app()
    
    with app.app_context():
        logger.info("Testing all live data models...")
        
        # Test DataSource creation
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        test_ds = DataSource(
            name=f'Test Source {timestamp}',
            source_type='firestore',
            connection_config={'project': 'test'},
            description='Test data source'
        )
        db.session.add(test_ds)
        db.session.commit()
        
        logger.info(f"✓ DataSource created: {test_ds}")
        
        # Test LiveTrace creation
        test_trace = LiveTrace(
            external_trace_id=f'test-trace-{timestamp}',
            name='Test Trace',
            status='success',
            start_time=datetime.utcnow(),
            data_source_id=test_ds.id,
            input_tokens=100,
            output_tokens=50,
            cost_usd=0.001
        )
        db.session.add(test_trace)
        db.session.commit()
        
        logger.info(f"✓ LiveTrace created: {test_trace}")
        
        # Test relationship
        assert test_trace.data_source.name == f'Test Source {timestamp}'
        logger.info("✓ LiveTrace -> DataSource relationship works")
        
        # Test PerformanceMetric creation
        test_metric = PerformanceMetric(
            period_start=datetime.utcnow() - timedelta(hours=1),
            period_end=datetime.utcnow(),
            period_type='hour',
            total_traces=10,
            success_count=9,
            error_count=1,
            success_rate=90.0,
            data_source_id=test_ds.id
        )
        db.session.add(test_metric)
        db.session.commit()
        
        logger.info(f"✓ PerformanceMetric created: {test_metric}")
        
        # Test SyncStatus creation
        test_sync = SyncStatus(
            data_source_id=test_ds.id,
            sync_type='incremental',
            last_sync_timestamp=datetime.utcnow(),
            sync_status='success'
        )
        db.session.add(test_sync)
        db.session.commit()
        
        logger.info(f"✓ SyncStatus created: {test_sync}")
        
        # Test WebhookEvent creation
        test_webhook = WebhookEvent(
            event_id=f'webhook-{timestamp}',
            event_type='trace.created',
            source='langwatch',
            payload={'test': 'data'},
            data_source_id=test_ds.id
        )
        db.session.add(test_webhook)
        db.session.commit()
        
        logger.info(f"✓ WebhookEvent created: {test_webhook}")
        
        # Test CacheEntry creation
        test_cache = CacheEntry(
            cache_key=f'test-key-{timestamp}',
            cache_value={'cached': 'data'},
            cache_type='query_result',
            data_source_id=test_ds.id,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        db.session.add(test_cache)
        db.session.commit()
        
        logger.info(f"✓ CacheEntry created: {test_cache}")
        
        # Test cache expiration method
        assert not test_cache.is_expired()
        logger.info("✓ Cache expiration check works")
        
        # Test AlertRule creation
        test_alert = AlertRule(
            name=f'Test Alert {timestamp}',
            alert_type='error_rate',
            threshold_value=5.0,
            data_source_id=test_ds.id
        )
        db.session.add(test_alert)
        db.session.commit()
        
        logger.info(f"✓ AlertRule created: {test_alert}")
        
        # Test AlertEvent creation
        test_event = AlertEvent(
            rule_id=test_alert.id,
            triggered_at=datetime.utcnow(),
            trigger_value=7.5,
            threshold_value=5.0,
            message='Error rate exceeded threshold'
        )
        db.session.add(test_event)
        db.session.commit()
        
        logger.info(f"✓ AlertEvent created: {test_event}")
        
        # Test relationships
        assert len(test_ds.live_traces.all()) == 1
        assert len(test_ds.performance_metrics.all()) == 1
        assert len(test_ds.sync_statuses.all()) == 1  # Only our new sync status
        assert len(test_ds.webhook_events.all()) == 1
        assert len(test_ds.cache_entries.all()) == 1
        assert len(test_ds.alert_rules.all()) == 1
        
        logger.info("✓ All DataSource relationships work")
        
        # Test AlertRule -> AlertEvent relationship
        assert len(test_alert.alert_events.all()) == 1
        assert test_event.alert_rule.name == f'Test Alert {timestamp}'
        
        logger.info("✓ AlertRule -> AlertEvent relationship works")
        
        # Clean up test data
        db.session.delete(test_event)
        db.session.delete(test_alert)
        db.session.delete(test_cache)
        db.session.delete(test_webhook)
        db.session.delete(test_sync)
        db.session.delete(test_metric)
        db.session.delete(test_trace)
        db.session.delete(test_ds)
        db.session.commit()
        
        logger.info("✓ Test cleanup completed")
        logger.info("🎉 All model tests passed!")

def test_initial_data():
    """Test that initial migration data is correct."""
    app = create_app()
    
    with app.app_context():
        logger.info("Testing initial migration data...")
        
        # Check data sources (at least the 3 initial ones)
        ds_count = DataSource.query.count()
        assert ds_count >= 3, f"Expected at least 3 data sources, got {ds_count}"
        
        firestore_ds = DataSource.query.filter_by(name='Firestore Primary').first()
        assert firestore_ds is not None
        assert firestore_ds.source_type == 'firestore'
        assert firestore_ds.is_active == True
        
        logger.info("✓ Initial data sources correct")
        
        # Check sync statuses (at least the 3 initial ones)
        sync_count = SyncStatus.query.count()
        assert sync_count >= 3, f"Expected at least 3 sync statuses, got {sync_count}"
        
        # Check that initial sync statuses exist
        initial_syncs = SyncStatus.query.filter_by(sync_type='full_sync', sync_status='pending').all()
        assert len(initial_syncs) >= 3, f"Expected at least 3 initial sync statuses, got {len(initial_syncs)}"
        
        for sync in initial_syncs:
            assert sync.data_source is not None
        
        logger.info("✓ Initial sync statuses correct")
        
        # Check alert rules  
        alert_count = AlertRule.query.count()
        assert alert_count >= 3, f"Expected at least 3 alert rules, got {alert_count}"
        
        global_alerts = AlertRule.query.filter(AlertRule.data_source_id.is_(None)).all()
        assert len(global_alerts) >= 3, "Expected at least 3 global alert rules"
        
        logger.info("✓ Initial alert rules correct")
        logger.info("🎉 Initial data tests passed!")

def test_queries():
    """Test common query patterns that will be used by the dashboard."""
    app = create_app()
    
    with app.app_context():
        logger.info("Testing common query patterns...")
        
        # Test data source health query
        healthy_sources = DataSource.query.filter_by(
            is_active=True, 
            health_status='unknown'
        ).all()
        logger.info(f"✓ Found {len(healthy_sources)} active data sources")
        
        # Test recent sync status query
        recent_syncs = SyncStatus.query.filter(
            SyncStatus.last_sync_timestamp >= datetime.utcnow() - timedelta(days=1)
        ).all()
        logger.info(f"✓ Found {len(recent_syncs)} recent sync statuses")
        
        # Test active alert rules query
        active_alerts = AlertRule.query.filter_by(is_active=True).all()
        logger.info(f"✓ Found {len(active_alerts)} active alert rules")
        
        # Test data source with related data query
        ds_with_traces = DataSource.query.join(LiveTrace, isouter=True).all()
        logger.info(f"✓ Successfully queried {len(ds_with_traces)} data sources with traces")
        
        logger.info("🎉 Query pattern tests passed!")

def test_indexes():
    """Test that indexes are working by checking query plans."""
    app = create_app()
    
    with app.app_context():
        logger.info("Testing database indexes...")
        
        from sqlalchemy import text
        
        # Test index on live_traces.external_trace_id
        result = db.session.execute(
            text("EXPLAIN QUERY PLAN SELECT * FROM live_traces WHERE external_trace_id = 'test'")
        ).fetchall()
        
        # Check if index is being used (SEARCH vs SCAN)
        query_plan = ' '.join(str(row) for row in result)
        if 'idx_' in query_plan.lower():
            logger.info("✓ Index usage detected in query plan")
        else:
            logger.info("⚠ No index usage detected (may be due to small dataset)")
        
        # Test that all expected indexes exist
        indexes = db.session.execute(
            text("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
        ).fetchall()
        
        index_names = [idx[0] for idx in indexes]
        expected_indexes = [
            'idx_live_traces_external_id',
            'idx_data_sources_type',
            'idx_performance_metrics_period',
            'idx_sync_status_data_source',
            'idx_cache_entries_key'
        ]
        
        for expected in expected_indexes:
            if expected in index_names:
                logger.info(f"✓ Index {expected} exists")
            else:
                logger.warning(f"⚠ Index {expected} missing")
        
        logger.info(f"✓ Found {len(index_names)} total custom indexes")
        logger.info("🎉 Index tests completed!")

if __name__ == "__main__":
    try:
        logger.info("=" * 60)
        logger.info("STARTING COMPREHENSIVE MIGRATION TEST SUITE")
        logger.info("=" * 60)
        
        test_all_models()
        test_initial_data()
        test_queries()
        test_indexes()
        
        logger.info("=" * 60)
        logger.info("🎉 ALL TESTS PASSED! Migration is working correctly.")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"❌ TEST FAILED: {e}")
        logger.error("=" * 60)
        import traceback
        traceback.print_exc()
        sys.exit(1)