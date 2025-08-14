#!/usr/bin/env python3
"""
Database migration script for live data integration.
Apply the complete live data schema changes to the existing database.
Version: Enhanced with data_sources and cache_entries tables
"""

import os
import sys
import logging
from datetime import datetime
from pathlib import Path
import json

# Add the app directory to Python path
current_dir = Path(__file__).parent
app_dir = current_dir.parent
sys.path.insert(0, str(app_dir))

from app import create_app, db
from app.models import User
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError, IntegrityError

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def check_database_state():
    """Check current database state before migration."""
    logger.info("Checking current database state...")
    
    inspector = inspect(db.engine)
    existing_tables = inspector.get_table_names()
    
    logger.info(f"Found {len(existing_tables)} existing tables:")
    for table in sorted(existing_tables):
        logger.info(f"  - {table}")
    
    # Check for critical existing data
    critical_tables = ['users', 'prompts', 'traces', 'costs']
    for table in critical_tables:
        if table in existing_tables:
            try:
                count = db.session.execute(text(f"SELECT COUNT(*) FROM {table}")).scalar()
                logger.info(f"  → {table}: {count} records")
            except Exception as e:
                logger.warning(f"  → {table}: Could not count records - {e}")
    
    return existing_tables

def backup_existing_data():
    """Create a backup of critical existing data."""
    logger.info("Creating backup of existing data...")
    
    backup_data = {}
    critical_tables = ['users', 'prompts', 'traces', 'costs']
    
    for table in critical_tables:
        try:
            result = db.session.execute(text(f"SELECT * FROM {table}")).fetchall()
            backup_data[table] = [dict(row._mapping) for row in result]
            logger.info(f"Backed up {len(backup_data[table])} records from {table}")
        except Exception as e:
            logger.warning(f"Could not backup {table}: {e}")
    
    # Save backup to file
    backup_file = current_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(backup_file, 'w') as f:
        json.dump(backup_data, f, indent=2, default=str)
    
    logger.info(f"Backup saved to: {backup_file}")
    return backup_file

def _split_sql_statements(sql_content):
    """Split SQL content into individual statements, handling triggers properly."""
    statements = []
    current_statement = []
    in_trigger = False
    trigger_depth = 0
    
    lines = sql_content.split('\n')
    
    for line in lines:
        line = line.strip()
        
        # Skip comments and empty lines
        if not line or line.startswith('--'):
            continue
            
        # Check for trigger start
        if line.upper().startswith('CREATE TRIGGER'):
            in_trigger = True
            trigger_depth = 0
            
        current_statement.append(line)
        
        # Handle trigger statements
        if in_trigger:
            if 'BEGIN' in line.upper():
                trigger_depth += 1
            elif 'END' in line.upper():
                trigger_depth -= 1
                if trigger_depth <= 0:
                    in_trigger = False
                    # Add the complete trigger statement
                    statements.append(' '.join(current_statement))
                    current_statement = []
                    continue
        
        # Handle regular statements (not in trigger)
        if not in_trigger and line.endswith(';'):
            statements.append(' '.join(current_statement))
            current_statement = []
    
    # Add any remaining statement
    if current_statement:
        statements.append(' '.join(current_statement))
    
    return [stmt.strip() for stmt in statements if stmt.strip()]

def apply_migration(skip_backup=False):
    """Apply the live data integration migration."""
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("=" * 60)
            logger.info("STARTING LIVE DATA INTEGRATION MIGRATION")
            logger.info("=" * 60)
            
            # Check current state
            existing_tables = check_database_state()
            
            # Create backup unless skipped
            backup_file = None
            if not skip_backup and any(table in existing_tables for table in ['users', 'prompts', 'traces', 'costs']):
                backup_file = backup_existing_data()
            
            # Read migration SQL
            migration_file = current_dir / "001_live_data_schema.sql"
            
            if not migration_file.exists():
                raise FileNotFoundError(f"Migration file not found: {migration_file}")
            
            with open(migration_file, 'r') as f:
                migration_sql = f.read()
            
            # Split into individual statements (handle trigger statements properly)
            statements = _split_sql_statements(migration_sql)
            
            logger.info(f"Executing {len(statements)} SQL statements...")
            
            # Execute statements in batches
            success_count = 0
            skip_count = 0
            error_count = 0
            
            for i, statement in enumerate(statements, 1):
                try:
                    # Log statement type for important operations
                    statement_upper = statement.upper()
                    if any(statement_upper.startswith(cmd) for cmd in ['CREATE TABLE', 'CREATE INDEX', 'CREATE TRIGGER']):
                        # Extract table/index name for logging
                        parts = statement.split()
                        if len(parts) >= 5:
                            object_name = parts[4] if parts[3] == 'EXISTS' else parts[3]
                            logger.info(f"[{i:3d}/{len(statements)}] Creating {parts[1].lower()}: {object_name}")
                    elif statement_upper.startswith('INSERT'):
                        logger.info(f"[{i:3d}/{len(statements)}] Inserting initial data...")
                    
                    db.session.execute(text(statement))
                    success_count += 1
                    
                except IntegrityError as e:
                    if "UNIQUE constraint failed" in str(e) or "already exists" in str(e).lower():
                        skip_count += 1
                        logger.debug(f"Statement {i} skipped (already exists)")
                    else:
                        error_count += 1
                        logger.error(f"Integrity error in statement {i}: {e}")
                        logger.error(f"Statement: {statement[:100]}...")
                        raise
                        
                except Exception as e:
                    if "already exists" in str(e).lower():
                        skip_count += 1
                        logger.debug(f"Statement {i} skipped (already exists)")
                    else:
                        error_count += 1
                        logger.error(f"Error in statement {i}: {e}")
                        logger.error(f"Statement: {statement[:100]}...")
                        raise
            
            # Commit all changes
            db.session.commit()
            
            logger.info(f"Migration execution completed:")
            logger.info(f"  - Success: {success_count} statements")
            logger.info(f"  - Skipped: {skip_count} statements") 
            logger.info(f"  - Errors: {error_count} statements")
            
            # Verify migration
            verify_migration()
            
            logger.info("=" * 60)
            logger.info("MIGRATION COMPLETED SUCCESSFULLY!")
            logger.info("=" * 60)
            
            if backup_file:
                logger.info(f"Backup file created: {backup_file}")
            
            return True
            
        except Exception as e:
            logger.error("=" * 60)
            logger.error("MIGRATION FAILED!")
            logger.error("=" * 60)
            logger.error(f"Error: {e}")
            db.session.rollback()
            
            if backup_file:
                logger.error(f"Restore from backup if needed: {backup_file}")
            
            raise

def verify_migration():
    """Verify that the migration was applied correctly."""
    logger.info("Verifying migration...")
    
    try:
        # Expected new tables
        expected_tables = [
            'live_traces',
            'performance_metrics',
            'sync_status', 
            'webhook_events',
            'data_sources',
            'cache_entries',
            'alert_rules',
            'alert_events'
        ]
        
        verification_results = {
            'tables': {},
            'indexes': 0,
            'triggers': 0,
            'initial_data': {}
        }
        
        # Check tables
        for table_name in expected_tables:
            result = db.session.execute(
                text("SELECT name FROM sqlite_master WHERE type='table' AND name=:table_name"),
                {"table_name": table_name}
            ).fetchone()
            
            if result:
                # Count records
                count = db.session.execute(text(f"SELECT COUNT(*) FROM {table_name}")).scalar()
                verification_results['tables'][table_name] = count
                logger.info(f"✓ Table {table_name}: {count} records")
                
                # Check specific tables with initial data
                if table_name in ['data_sources', 'sync_status', 'alert_rules'] and count > 0:
                    verification_results['initial_data'][table_name] = count
                    
            else:
                verification_results['tables'][table_name] = None
                logger.error(f"✗ Table {table_name} missing!")
        
        # Check indexes
        index_count = db.session.execute(
            text("SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
        ).scalar()
        verification_results['indexes'] = index_count
        logger.info(f"✓ {index_count} custom indexes created")
        
        # Check triggers
        trigger_count = db.session.execute(
            text("SELECT COUNT(*) FROM sqlite_master WHERE type='trigger'")
        ).scalar()
        verification_results['triggers'] = trigger_count
        logger.info(f"✓ {trigger_count} triggers created")
        
        # Verify data source relationships
        if verification_results['tables'].get('data_sources', 0) > 0:
            sync_with_sources = db.session.execute(
                text("""
                    SELECT COUNT(*) FROM sync_status s 
                    JOIN data_sources ds ON s.data_source_id = ds.id
                """)
            ).scalar()
            logger.info(f"✓ {sync_with_sources} sync status records linked to data sources")
        
        # Verify foreign key constraints work
        try:
            # Test data source foreign key
            db.session.execute(
                text("INSERT INTO live_traces (external_trace_id, name, status, start_time, data_source_id) VALUES ('test-fk', 'test', 'success', datetime('now'), 999)")
            )
            db.session.rollback()
            logger.warning("⚠ Foreign key constraint not enforced (SQLite limitation)")
        except Exception:
            logger.info("✓ Foreign key constraints active")
        
        logger.info("Migration verification completed successfully!")
        return verification_results
        
    except Exception as e:
        logger.error(f"Migration verification failed: {e}")
        raise

def rollback_migration():
    """Rollback the migration (for development/testing)."""
    app = create_app()
    
    with app.app_context():
        try:
            logger.warning("=" * 60)
            logger.warning("ROLLING BACK LIVE DATA INTEGRATION MIGRATION")
            logger.warning("=" * 60)
            
            # Tables to drop (in reverse dependency order)
            tables_to_drop = [
                'alert_events',
                'alert_rules', 
                'cache_entries',
                'webhook_events',
                'sync_status',
                'performance_metrics',
                'live_traces',
                'data_sources'
            ]
            
            dropped_count = 0
            for table in tables_to_drop:
                try:
                    db.session.execute(text(f"DROP TABLE IF EXISTS {table}"))
                    logger.info(f"Dropped table: {table}")
                    dropped_count += 1
                except Exception as e:
                    logger.warning(f"Could not drop table {table}: {e}")
            
            # Drop custom indexes (they should be dropped with tables, but just in case)
            try:
                indexes = db.session.execute(
                    text("SELECT name FROM sqlite_master WHERE type='index' AND name LIKE 'idx_%'")
                ).fetchall()
                
                for idx in indexes:
                    try:
                        db.session.execute(text(f"DROP INDEX IF EXISTS {idx[0]}"))
                    except Exception as e:
                        logger.warning(f"Could not drop index {idx[0]}: {e}")
            except Exception as e:
                logger.warning(f"Could not clean up indexes: {e}")
            
            db.session.commit()
            
            logger.info("=" * 60)
            logger.info(f"ROLLBACK COMPLETED! Dropped {dropped_count} tables.")
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error("=" * 60)
            logger.error("ROLLBACK FAILED!")
            logger.error("=" * 60)
            logger.error(f"Error: {e}")
            db.session.rollback()
            sys.exit(1)

def test_migration():
    """Test migration with a sample trace."""
    app = create_app()
    
    with app.app_context():
        try:
            logger.info("Testing migration with sample data...")
            
            # Get a data source
            data_source = db.session.execute(
                text("SELECT id FROM data_sources WHERE name = 'Firestore Primary' LIMIT 1")
            ).scalar()
            
            if not data_source:
                logger.warning("No data source found, skipping integration test")
                return
            
            # Insert test trace
            test_trace_id = f"test-trace-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            db.session.execute(
                text("""
                    INSERT INTO live_traces 
                    (external_trace_id, name, status, start_time, data_source_id, input_tokens, output_tokens, cost_usd)
                    VALUES (:trace_id, :name, :status, :start_time, :data_source_id, :input_tokens, :output_tokens, :cost)
                """),
                {
                    "trace_id": test_trace_id,
                    "name": "Migration Test Trace",
                    "status": "success", 
                    "start_time": datetime.now(),
                    "data_source_id": data_source,
                    "input_tokens": 100,
                    "output_tokens": 50,
                    "cost": 0.001
                }
            )
            
            # Test cache entry
            db.session.execute(
                text("""
                    INSERT INTO cache_entries 
                    (cache_key, cache_value, cache_type, data_source_id, ttl_seconds)
                    VALUES (:key, :value, :type, :data_source_id, :ttl)
                """),
                {
                    "key": "test-cache-key",
                    "value": '{"test": "data"}',
                    "type": "test",
                    "data_source_id": data_source,
                    "ttl": 3600
                }
            )
            
            db.session.commit()
            
            # Verify test data
            trace_count = db.session.execute(
                text("SELECT COUNT(*) FROM live_traces WHERE external_trace_id = :trace_id"),
                {"trace_id": test_trace_id}
            ).scalar()
            
            cache_count = db.session.execute(
                text("SELECT COUNT(*) FROM cache_entries WHERE cache_key = :key"),
                {"key": "test-cache-key"}
            ).scalar()
            
            logger.info(f"✓ Test trace inserted: {trace_count} record")
            logger.info(f"✓ Test cache entry inserted: {cache_count} record")
            
            # Clean up test data
            db.session.execute(
                text("DELETE FROM live_traces WHERE external_trace_id = :trace_id"),
                {"trace_id": test_trace_id}
            )
            db.session.execute(
                text("DELETE FROM cache_entries WHERE cache_key = :key"),
                {"key": "test-cache-key"}
            )
            db.session.commit()
            
            logger.info("✓ Migration test completed successfully!")
            
        except Exception as e:
            logger.error(f"Migration test failed: {e}")
            db.session.rollback()
            raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Apply live data integration migration')
    parser.add_argument('--rollback', action='store_true', help='Rollback the migration')
    parser.add_argument('--verify-only', action='store_true', help='Only verify migration')
    parser.add_argument('--test', action='store_true', help='Test migration with sample data')
    parser.add_argument('--skip-backup', action='store_true', help='Skip backup creation')
    
    args = parser.parse_args()
    
    try:
        if args.rollback:
            rollback_migration()
        elif args.verify_only:
            app = create_app()
            with app.app_context():
                verify_migration()
        elif args.test:
            test_migration()
        else:
            apply_migration(skip_backup=args.skip_backup)
            
        logger.info("Operation completed successfully!")
        
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        sys.exit(1)