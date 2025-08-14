"""
Background Sync Scheduler for Firestore Data Integration

Handles automated synchronization of data from external sources using APScheduler.
Provides health monitoring, graceful shutdown, and sync status management.
"""

import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from flask import current_app
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR

from app.services.firestore_sync import firestore_sync_service

logger = logging.getLogger(__name__)

class SyncScheduler:
    """
    Background scheduler for managing sync operations.
    
    Features:
    - Automated sync every 5 minutes (configurable)
    - Health monitoring and status tracking
    - Graceful shutdown handling
    - Job error handling and retry logic
    - Performance metrics collection
    """
    
    def __init__(self, app=None):
        """Initialize sync scheduler."""
        self.app = app
        self.scheduler = None
        self.is_running = False
        self._shutdown_lock = threading.Lock()
        
        # Configuration
        self.sync_interval_minutes = 5
        self.max_workers = 2
        self.health_check_interval = 60  # seconds
        
        # Statistics
        self.stats = {
            'sync_count': 0,
            'success_count': 0,
            'error_count': 0,
            'last_sync_time': None,
            'last_success_time': None,
            'last_error_time': None,
            'last_error_message': None,
            'total_records_synced': 0,
            'scheduler_started_at': None
        }
        
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize scheduler with Flask app."""
        self.app = app
        
        # Load configuration from app config
        self.sync_interval_minutes = app.config.get('FIRESTORE_SYNC_INTERVAL_MINUTES', 5)
        self.max_workers = app.config.get('SYNC_MAX_WORKERS', 2)
        
        # Configure APScheduler
        jobstores = {
            'default': MemoryJobStore()
        }
        
        executors = {
            'default': ThreadPoolExecutor(self.max_workers)
        }
        
        job_defaults = {
            'coalesce': True,
            'max_instances': 1,
            'misfire_grace_time': 300  # 5 minutes
        }
        
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='UTC'
        )
        
        # Add event listeners
        self.scheduler.add_listener(
            self._job_executed_listener,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
        )
        
        logger.info("Sync scheduler initialized")
    
    def start(self):
        """Start the background scheduler."""
        if not self.scheduler:
            logger.error("Scheduler not initialized. Call init_app() first.")
            return False
        
        try:
            # Add sync jobs
            self._add_sync_jobs()
            
            # Start scheduler
            self.scheduler.start()
            self.is_running = True
            self.stats['scheduler_started_at'] = datetime.utcnow()
            
            logger.info(f"Sync scheduler started with {self.sync_interval_minutes} minute intervals")
            return True
            
        except Exception as e:
            logger.error(f"Failed to start sync scheduler: {e}")
            return False
    
    def shutdown(self, wait=True):
        """Shutdown the scheduler gracefully."""
        with self._shutdown_lock:
            if self.scheduler and self.is_running:
                try:
                    logger.info("Shutting down sync scheduler...")
                    self.scheduler.shutdown(wait=wait)
                    self.is_running = False
                    logger.info("Sync scheduler shut down successfully")
                except Exception as e:
                    logger.error(f"Error shutting down scheduler: {e}")
    
    def _add_sync_jobs(self):
        """Add sync jobs to the scheduler."""
        try:
            # Main Firestore sync job
            self.scheduler.add_job(
                func=self._run_firestore_sync,
                trigger=IntervalTrigger(minutes=self.sync_interval_minutes),
                id='firestore_sync',
                name='Firestore Data Sync',
                replace_existing=True,
                max_instances=1
            )
            
            # Health check job (every 10 minutes)
            self.scheduler.add_job(
                func=self._health_check,
                trigger=IntervalTrigger(minutes=10),
                id='health_check',
                name='Sync Health Check',
                replace_existing=True,
                max_instances=1
            )
            
            # Daily cleanup job (3 AM UTC)
            self.scheduler.add_job(
                func=self._daily_cleanup,
                trigger=CronTrigger(hour=3, minute=0),
                id='daily_cleanup',
                name='Daily Cleanup',
                replace_existing=True,
                max_instances=1
            )
            
            logger.info("Sync jobs added to scheduler")
            
        except Exception as e:
            logger.error(f"Error adding sync jobs: {e}")
            raise
    
    def _run_firestore_sync(self):
        """Run Firestore sync job with proper Flask application context."""
        if not self.app:
            logger.error("Flask app not available for sync job")
            return
        
        with self.app.app_context():
            if not firestore_sync_service.is_available():
                logger.warning("Firestore sync service not available, skipping sync")
                return
            
            try:
                logger.info("Starting scheduled Firestore sync")
                self.stats['sync_count'] += 1
                self.stats['last_sync_time'] = datetime.utcnow()
                
                # Run sync
                result = firestore_sync_service.sync_traces_from_firestore()
                
                if result.success:
                    self.stats['success_count'] += 1
                    self.stats['last_success_time'] = datetime.utcnow()
                    self.stats['total_records_synced'] += result.records_processed
                    logger.info(f"Firestore sync completed successfully: {result.records_processed} records processed")
                else:
                    self.stats['error_count'] += 1
                    self.stats['last_error_time'] = datetime.utcnow()
                    self.stats['last_error_message'] = '; '.join(result.errors)
                    logger.error(f"Firestore sync failed: {result.errors}")
                    
            except Exception as e:
                self.stats['error_count'] += 1
                self.stats['last_error_time'] = datetime.utcnow()
                self.stats['last_error_message'] = str(e)
                logger.error(f"Error in scheduled Firestore sync: {e}")
    
    def _health_check(self):
        """Perform health check on sync services with proper Flask context."""
        if not self.app:
            logger.error("Flask app not available for health check")
            return
        
        with self.app.app_context():
            try:
                logger.debug("Running sync health check")
                
                # Check Firestore connection
                if firestore_sync_service.is_available():
                    # Get sync statistics
                    stats = firestore_sync_service.get_sync_statistics()
                    logger.debug(f"Firestore sync stats: {stats}")
                else:
                    logger.warning("Firestore sync service is not available")
                    
            except Exception as e:
                logger.error(f"Error in health check: {e}")
    
    def _daily_cleanup(self):
        """Perform daily cleanup tasks with proper Flask context."""
        if not self.app:
            logger.error("Flask app not available for daily cleanup")
            return
        
        with self.app.app_context():
            try:
                logger.info("Running daily cleanup")
                
                # Could implement cleanup logic here:
                # - Remove old sync logs
                # - Archive old performance metrics
                # - Clean up temporary data
                
                logger.info("Daily cleanup completed")
                
            except Exception as e:
                logger.error(f"Error in daily cleanup: {e}")
    
    def _job_executed_listener(self, event):
        """Handle job execution events."""
        job_id = event.job_id
        
        if event.exception:
            logger.error(f"Job {job_id} crashed: {event.exception}")
            
            # Update error stats
            self.stats['error_count'] += 1
            self.stats['last_error_time'] = datetime.utcnow()
            self.stats['last_error_message'] = str(event.exception)
        else:
            logger.debug(f"Job {job_id} executed successfully")
    
    def trigger_manual_sync(self) -> Dict[str, Any]:
        """Trigger manual sync operation with proper Flask context."""
        if not self.app:
            return {
                'success': False,
                'error': 'Flask app not available'
            }
        
        with self.app.app_context():
            try:
                if not firestore_sync_service.is_available():
                    return {
                        'success': False,
                        'error': 'Firestore sync service not available'
                    }
                
                logger.info("Manual sync triggered")
                result = firestore_sync_service.sync_traces_from_firestore()
                
                # Update stats
                self.stats['sync_count'] += 1
                self.stats['last_sync_time'] = datetime.utcnow()
                
                if result.success:
                    self.stats['success_count'] += 1
                    self.stats['last_success_time'] = datetime.utcnow()
                    self.stats['total_records_synced'] += result.records_processed
                else:
                    self.stats['error_count'] += 1
                    self.stats['last_error_time'] = datetime.utcnow()
                    self.stats['last_error_message'] = '; '.join(result.errors)
                
                return {
                    'success': result.success,
                    'records_processed': result.records_processed,
                    'errors': result.errors,
                    'timestamp': datetime.utcnow().isoformat()
                }
                
            except Exception as e:
                logger.error(f"Error in manual sync: {e}")
                return {
                    'success': False,
                    'error': str(e)
                }
    
    def get_scheduler_status(self) -> Dict[str, Any]:
        """Get current scheduler status and statistics."""
        if not self.scheduler:
            return {
                'is_running': False,
                'error': 'Scheduler not initialized'
            }
        
        # Get job information
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                'trigger': str(job.trigger)
            })
        
        return {
            'is_running': self.is_running,
            'jobs': jobs,
            'stats': self.stats.copy(),
            'sync_interval_minutes': self.sync_interval_minutes,
            'max_workers': self.max_workers,
            'firestore_available': firestore_sync_service.is_available()
        }
    
    def get_next_sync_time(self) -> Optional[datetime]:
        """Get the next scheduled sync time."""
        if not self.scheduler or not self.is_running:
            return None
        
        job = self.scheduler.get_job('firestore_sync')
        if job and job.next_run_time:
            return job.next_run_time.replace(tzinfo=None)
        
        return None
    
    def pause_sync(self):
        """Pause sync operations."""
        if self.scheduler and self.is_running:
            try:
                self.scheduler.pause_job('firestore_sync')
                logger.info("Sync operations paused")
                return True
            except Exception as e:
                logger.error(f"Error pausing sync: {e}")
                return False
        return False
    
    def resume_sync(self):
        """Resume sync operations."""
        if self.scheduler and self.is_running:
            try:
                self.scheduler.resume_job('firestore_sync')
                logger.info("Sync operations resumed")
                return True
            except Exception as e:
                logger.error(f"Error resuming sync: {e}")
                return False
        return False

# Global scheduler instance
sync_scheduler = SyncScheduler()