"""
Firestore Sync Service for Live Data Integration
Handles bidirectional sync between Firestore and local SQLite database.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import time

from google.cloud import firestore
from google.api_core import exceptions as firestore_exceptions
from flask import current_app
from app.models import db
from app.models import Trace, Cost, User
from sqlalchemy.exc import IntegrityError, SQLAlchemyError, DisconnectionError
from sqlalchemy import text
from contextlib import contextmanager

logger = logging.getLogger(__name__)

@dataclass
class SyncResult:
    """Result of sync operation."""
    success: bool
    records_processed: int = 0
    errors: List[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.metadata is None:
            self.metadata = {}

class FirestoreSyncService:
    """
    Service for syncing data between Firestore and local database.
    
    Handles:
    - Incremental sync from Firestore to local DB
    - Conflict resolution
    - Error handling and recovery
    - Performance optimization with batching
    """
    
    def __init__(self, project_id: str = None):
        """Initialize Firestore sync service."""
        self.project_id = project_id or os.getenv('GOOGLE_CLOUD_PROJECT')
        self.client = None
        self.batch_size = 100
        self.max_workers = 4
        
        # Database connection management
        self.max_retries = 3
        self.retry_delay = 1.0
        
        # Collection mappings
        self.collection_configs = {
            'traces': {
                'collection_name': 'vertigo_traces',
                'local_table': 'live_traces',
                'timestamp_field': 'created_at',
                'id_field': 'trace_id'
            },
            'meetings': {
                'collection_name': 'meetings',
                'local_table': 'live_traces',
                'timestamp_field': 'timestamp',
                'id_field': 'meeting_id'
            }
        }
        
        try:
            self._init_firestore_client()
        except Exception as e:
            logger.warning(f"Firestore client initialization failed: {e}")
            self.client = None
    
    def _init_firestore_client(self):
        """Initialize Firestore client with proper authentication."""
        try:
            self.client = firestore.Client(project=self.project_id)
            # Test connection
            self.client.collection('health_check').limit(1).get()
            logger.info("Firestore client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Firestore client: {e}")
            raise
    
    def is_available(self) -> bool:
        """Check if Firestore sync is available."""
        return self.client is not None
    
    @contextmanager
    def _database_session(self):
        """Context manager for safe database operations with retry logic."""
        session = None
        retries = 0
        
        while retries < self.max_retries:
            try:
                # Use the global db session with proper error handling
                session = db.session
                yield session
                # If we get here, the operation was successful
                break
                
            except (DisconnectionError, SQLAlchemyError) as e:
                retries += 1
                logger.warning(f"Database connection error (attempt {retries}/{self.max_retries}): {e}")
                
                if session:
                    try:
                        session.rollback()
                    except Exception:
                        pass
                
                if retries < self.max_retries:
                    time.sleep(self.retry_delay * retries)  # Exponential backoff
                    # Try to reconnect
                    try:
                        session.connection().invalidate()
                    except Exception:
                        pass
                else:
                    logger.error(f"Database operation failed after {self.max_retries} attempts")
                    raise
            
            except Exception as e:
                if session:
                    try:
                        session.rollback()
                    except Exception:
                        pass
                raise e
    
    def get_last_sync_timestamp(self, sync_type: str) -> datetime:
        """Get the last successful sync timestamp with proper connection management."""
        try:
            with self._database_session() as session:
                # Get Firestore data source ID
                ds_result = session.execute(
                    text("SELECT id FROM data_sources WHERE name = 'firestore' LIMIT 1")
                ).fetchone()
                
                if not ds_result:
                    logger.warning("Firestore data source not found, creating it...")
                    session.execute(
                        text("""
                        INSERT INTO data_sources 
                        (name, source_type, connection_config, is_active, sync_enabled, sync_interval_minutes, created_at, updated_at)
                        VALUES ('firestore', 'firestore', '{}', 1, 1, 5, :now, :now)
                        """),
                        {"now": datetime.utcnow()}
                    )
                    session.commit()
                    ds_result = session.execute(
                        text("SELECT id FROM data_sources WHERE name = 'firestore' LIMIT 1")
                    ).fetchone()
                
                data_source_id = ds_result[0]
                
                result = session.execute(
                    text("SELECT last_successful_sync FROM sync_status WHERE data_source_id = :ds_id AND sync_type = :type"),
                    {"ds_id": data_source_id, "type": sync_type}
                ).fetchone()
                
                if result and result[0]:
                    return datetime.fromisoformat(result[0].replace('Z', '+00:00'))
                
                # Default to 24 hours ago for first sync
                return datetime.utcnow() - timedelta(hours=24)
                
        except Exception as e:
            logger.error(f"Error getting last sync timestamp: {e}")
            return datetime.utcnow() - timedelta(hours=24)
    
    def update_sync_status(self, sync_type: str, status: str, 
                          records_processed: int = 0, error_message: str = None):
        """Update sync status in database with proper connection management."""
        try:
            with self._database_session() as session:
                current_time = datetime.utcnow()
                
                # Get or create Firestore data source ID
                ds_result = session.execute(
                    text("SELECT id FROM data_sources WHERE name = 'firestore' LIMIT 1")
                ).fetchone()
                
                if not ds_result:
                    session.execute(
                        text("""
                        INSERT INTO data_sources 
                        (name, source_type, connection_config, is_active, sync_enabled, sync_interval_minutes, created_at, updated_at)
                        VALUES ('firestore', 'firestore', '{}', 1, 1, 5, :now, :now)
                        """),
                        {"now": datetime.utcnow()}
                    )
                    session.commit()
                    ds_result = session.execute(
                        text("SELECT id FROM data_sources WHERE name = 'firestore' LIMIT 1")
                    ).fetchone()
                
                data_source_id = ds_result[0]
                
                # Check if sync status record exists
                existing = session.execute(
                    text("SELECT id FROM sync_status WHERE data_source_id = :ds_id AND sync_type = :type"),
                    {"ds_id": data_source_id, "type": sync_type}
                ).fetchone()
                
                if existing:
                    # Update existing record
                    session.execute(
                        text("""
                        UPDATE sync_status 
                        SET last_sync_timestamp = :current_time,
                            last_successful_sync = CASE WHEN :status = 'success' THEN :current_time ELSE last_successful_sync END,
                            sync_status = :status,
                            records_processed = :records,
                            error_message = :error,
                            updated_at = :current_time
                        WHERE data_source_id = :ds_id AND sync_type = :type
                        """),
                        {
                            "current_time": current_time,
                            "status": status,
                            "records": records_processed,
                            "error": error_message,
                            "ds_id": data_source_id,
                            "type": sync_type
                        }
                    )
                else:
                    # Insert new record
                    session.execute(
                        text("""
                        INSERT INTO sync_status 
                        (data_source_id, sync_type, last_sync_timestamp, last_successful_sync, 
                         sync_status, records_processed, error_message, created_at, updated_at)
                        VALUES (:ds_id, :type, :current_time, 
                                CASE WHEN :status = 'success' THEN :current_time ELSE NULL END,
                                :status, :records, :error, :current_time, :current_time)
                        """),
                        {
                            "ds_id": data_source_id,
                            "type": sync_type,
                            "current_time": current_time,
                            "status": status,
                            "records": records_processed,
                            "error": error_message
                        }
                    )
                
                session.commit()
                
        except Exception as e:
            logger.error(f"Error updating sync status: {e}")
            # Session rollback is handled by the context manager
    
    def sync_traces_from_firestore(self, hours_back: int = 24) -> SyncResult:
        """Sync traces from Firestore to local database."""
        if not self.is_available():
            return SyncResult(False, errors=["Firestore client not available"])
        
        try:
            self.update_sync_status('firestore', 'running')
            
            # Get last sync timestamp
            last_sync = self.get_last_sync_timestamp('firestore')
            logger.info(f"Starting Firestore sync from {last_sync}")
            
            total_processed = 0
            errors = []
            
            # Sync each configured collection
            for config_name, config in self.collection_configs.items():
                try:
                    result = self._sync_collection(config, last_sync)
                    total_processed += result.records_processed
                    errors.extend(result.errors)
                    
                except Exception as e:
                    error_msg = f"Error syncing collection {config_name}: {e}"
                    logger.error(error_msg)
                    errors.append(error_msg)
            
            if errors:
                self.update_sync_status('firestore', 'error', total_processed, '; '.join(errors))
                return SyncResult(False, total_processed, errors)
            else:
                self.update_sync_status('firestore', 'success', total_processed)
                return SyncResult(True, total_processed)
                
        except Exception as e:
            error_msg = f"Firestore sync failed: {e}"
            logger.error(error_msg)
            self.update_sync_status('firestore', 'error', 0, error_msg)
            return SyncResult(False, errors=[error_msg])
    
    def _sync_collection(self, config: Dict, since_timestamp: datetime) -> SyncResult:
        """Sync a specific Firestore collection."""
        collection_name = config['collection_name']
        timestamp_field = config['timestamp_field']
        
        try:
            # Query Firestore for recent documents
            query = (self.client.collection(collection_name)
                    .where(timestamp_field, '>=', since_timestamp)
                    .order_by(timestamp_field)
                    .limit(1000))  # Batch limit
            
            docs = query.get()
            logger.info(f"Found {len(docs)} documents in {collection_name}")
            
            processed = 0
            errors = []
            
            # Process documents in batches
            for i in range(0, len(docs), self.batch_size):
                batch_docs = docs[i:i + self.batch_size]
                batch_result = self._process_document_batch(batch_docs, config)
                processed += batch_result.records_processed
                errors.extend(batch_result.errors)
            
            return SyncResult(True, processed, errors)
            
        except Exception as e:
            logger.error(f"Error syncing collection {collection_name}: {e}")
            return SyncResult(False, errors=[str(e)])
    
    def _process_document_batch(self, docs: List, config: Dict) -> SyncResult:
        """Process a batch of Firestore documents with proper transaction management."""
        processed = 0
        errors = []
        
        try:
            with self._database_session() as session:
                for doc in docs:
                    try:
                        doc_data = doc.to_dict()
                        doc_id = doc.id
                        
                        # Transform Firestore document to local format
                        local_record = self._transform_firestore_document(
                            doc_id, doc_data, config
                        )
                        
                        # Insert or update local record
                        self._upsert_local_record_with_session(local_record, config, session)
                        processed += 1
                        
                    except Exception as e:
                        error_msg = f"Error processing document {doc.id}: {e}"
                        logger.warning(error_msg)
                        errors.append(error_msg)
                
                # Commit batch
                session.commit()
                
        except Exception as e:
            error_msg = f"Error processing batch: {e}"
            logger.error(error_msg)
            errors.append(error_msg)
        
        return SyncResult(True, processed, errors)
    
    def _transform_firestore_document(self, doc_id: str, doc_data: Dict, 
                                    config: Dict) -> Dict:
        """Transform Firestore document to local database format."""
        collection_name = config['collection_name']
        
        if collection_name == 'vertigo_traces':
            return {
                'external_trace_id': doc_data.get('trace_id', doc_id),
                'name': doc_data.get('name', 'Unknown Operation'),
                'status': doc_data.get('status', 'unknown'),
                'model': doc_data.get('model'),
                'start_time': self._parse_firestore_timestamp(doc_data.get('start_time')),
                'end_time': self._parse_firestore_timestamp(doc_data.get('end_time')),
                'duration_ms': doc_data.get('duration_ms'),
                'input_text': doc_data.get('input', {}).get('text') if isinstance(doc_data.get('input'), dict) else str(doc_data.get('input', '')),
                'output_text': doc_data.get('output', {}).get('text') if isinstance(doc_data.get('output'), dict) else str(doc_data.get('output', '')),
                'input_tokens': doc_data.get('input_tokens', 0),
                'output_tokens': doc_data.get('output_tokens', 0),
                'cost_usd': float(doc_data.get('cost', 0)),
                'user_id': doc_data.get('user_id'),
                'session_id': doc_data.get('session_id'),
                'tags': json.dumps(doc_data.get('tags', [])),
                'trace_metadata': json.dumps(doc_data.get('metadata', {})),
                'source_updated_at': self._parse_firestore_timestamp(doc_data.get('updated_at')),
                'firestore_doc_id': doc_id,
                'firestore_collection': collection_name
            }
        
        elif collection_name == 'meetings':
            return {
                'external_trace_id': f"meeting_{doc_id}",
                'name': f"Meeting Analysis: {doc_data.get('title', 'Unnamed')}",
                'status': 'success' if doc_data.get('processed') else 'pending',
                'model': doc_data.get('model_used', 'gemini-1.5-pro'),
                'start_time': self._parse_firestore_timestamp(doc_data.get('timestamp')),
                'end_time': self._parse_firestore_timestamp(doc_data.get('processed_at')),
                'input_text': doc_data.get('transcript', ''),
                'output_text': doc_data.get('summary', ''),
                'trace_metadata': json.dumps({
                    'meeting_id': doc_id,
                    'participants': doc_data.get('participants', []),
                    'duration': doc_data.get('duration'),
                    'type': 'meeting_processing'
                }),
                'firestore_doc_id': doc_id,
                'firestore_collection': collection_name
            }
        
        else:
            # Generic transformation
            return {
                'external_trace_id': doc_id,
                'name': doc_data.get('name', f"Firestore Document: {doc_id}"),
                'status': 'unknown',
                'trace_metadata': json.dumps(doc_data),
                'firestore_doc_id': doc_id,
                'firestore_collection': collection_name
            }
    
    def _parse_firestore_timestamp(self, timestamp) -> Optional[datetime]:
        """Parse Firestore timestamp to Python datetime."""
        if timestamp is None:
            return None
        
        try:
            if hasattr(timestamp, 'timestamp'):
                # Firestore Timestamp object
                return datetime.utcfromtimestamp(timestamp.timestamp())
            elif isinstance(timestamp, str):
                # ISO string
                return datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            elif isinstance(timestamp, datetime):
                return timestamp
            else:
                return None
        except Exception as e:
            logger.warning(f"Error parsing timestamp {timestamp}: {e}")
            return None
    
    def _upsert_local_record(self, record: Dict, config: Dict):
        """Insert or update local database record with proper session management."""
        with self._database_session() as session:
            self._upsert_local_record_with_session(record, config, session)
    
    def _upsert_local_record_with_session(self, record: Dict, config: Dict, session):
        """Insert or update local database record with provided session."""
        try:
            # Get Firestore data source ID
            ds_result = session.execute(
                text("SELECT id FROM data_sources WHERE name = 'firestore' LIMIT 1")
            ).fetchone()
            
            if not ds_result:
                session.execute(
                    text("""
                    INSERT INTO data_sources 
                    (name, source_type, connection_config, is_active, sync_enabled, sync_interval_minutes, created_at, updated_at)
                    VALUES ('firestore', 'firestore', '{}', 1, 1, 5, :now, :now)
                    """),
                    {"now": datetime.utcnow()}
                )
                session.commit()
                ds_result = session.execute(
                    text("SELECT id FROM data_sources WHERE name = 'firestore' LIMIT 1")
                ).fetchone()
            
            record['data_source_id'] = ds_result[0]
            
            # Check if record exists
            external_id = record['external_trace_id']
            existing = session.execute(
                text("SELECT id FROM live_traces WHERE external_trace_id = :id"),
                {"id": external_id}
            ).fetchone()
            
            if existing:
                # Update existing record
                update_fields = []
                update_values = {"id": existing[0]}
                
                for key, value in record.items():
                    if key != 'external_trace_id' and value is not None:
                        update_fields.append(f"{key} = :{key}")
                        update_values[key] = value
                
                if update_fields:
                    update_values['updated_at'] = datetime.utcnow()
                    update_fields.append("updated_at = :updated_at")
                    
                    sql = f"UPDATE live_traces SET {', '.join(update_fields)} WHERE id = :id"
                    session.execute(text(sql), update_values)
            else:
                # Insert new record
                record['created_at'] = datetime.utcnow()
                record['updated_at'] = datetime.utcnow()
                
                columns = list(record.keys())
                placeholders = [f":{col}" for col in columns]
                
                sql = f"""
                INSERT INTO live_traces ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
                """
                session.execute(text(sql), record)
                
        except Exception as e:
            logger.error(f"Error upserting record: {e}")
            raise
    
    def get_sync_statistics(self) -> Dict[str, Any]:
        """Get sync statistics and status with proper connection management."""
        try:
            with self._database_session() as session:
                # Get Firestore data source ID
                ds_result = session.execute(
                    text("SELECT id FROM data_sources WHERE name = 'firestore' LIMIT 1")
                ).fetchone()
                
                if not ds_result:
                    return {
                        'sync_statuses': [],
                        'total_records': 0,
                        'latest_record': None,
                        'is_available': self.is_available()
                    }
                
                data_source_id = ds_result[0]
                
                # Get sync status
                sync_statuses = session.execute(
                    text("""
                    SELECT sync_type, sync_status, last_sync_timestamp, records_processed 
                    FROM sync_status 
                    WHERE data_source_id = :ds_id
                    """), 
                    {"ds_id": data_source_id}
                ).fetchall()
                
                # Get record counts
                live_traces_count = session.execute(
                    text("SELECT COUNT(*) FROM live_traces WHERE data_source_id = :ds_id"),
                    {"ds_id": data_source_id}
                ).fetchone()[0]
                
                # Get latest records
                latest_sync = session.execute(
                    text("SELECT MAX(updated_at) FROM live_traces WHERE data_source_id = :ds_id"),
                    {"ds_id": data_source_id}
                ).fetchone()[0]
                
                return {
                    'sync_statuses': [
                        {
                            'type': row[0],
                            'status': row[1],
                            'last_sync': row[2],
                            'records_processed': row[3]
                        }
                        for row in sync_statuses
                    ],
                    'total_records': live_traces_count,
                    'latest_record': latest_sync,
                    'is_available': self.is_available()
                }
                
        except Exception as e:
            logger.error(f"Error getting sync statistics: {e}")
            return {
                'error': str(e),
                'is_available': False
            }
    
    def force_full_sync(self, hours_back: int = 168) -> SyncResult:
        """Force a full sync of data from the last N hours with proper connection management."""
        try:
            with self._database_session() as session:
                # Reset sync timestamps
                cutoff_time = datetime.utcnow() - timedelta(hours=hours_back)
                
                session.execute(
                    text("UPDATE sync_status SET last_sync_timestamp = :cutoff WHERE sync_type = 'firestore'"),
                    {"cutoff": cutoff_time}
                )
                session.commit()
                
            logger.info(f"Starting full sync from {cutoff_time}")
            return self.sync_traces_from_firestore(hours_back)
            
        except Exception as e:
            logger.error(f"Error in force full sync: {e}")
            return SyncResult(False, errors=[str(e)])

# Global service instance
firestore_sync_service = FirestoreSyncService()