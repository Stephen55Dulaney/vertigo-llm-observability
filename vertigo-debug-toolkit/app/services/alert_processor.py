"""
Alert Processor - Background task processor for real-time alert evaluation

Uses APScheduler to continuously monitor alert rules and trigger notifications.
Provides:
- Real-time alert rule evaluation
- Background job management
- Automatic failure recovery
- Performance monitoring of alert system itself
"""

import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from flask import current_app
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED
from sqlalchemy import text

from app.models import db, AlertRule, AlertEvent, DataSource
from app.services.alert_service import alert_service

logger = logging.getLogger(__name__)

class AlertProcessor:
    """
    Background alert processor using APScheduler.
    
    Manages continuous evaluation of alert rules and handles:
    - Scheduled rule evaluation
    - Job failure recovery
    - Performance monitoring
    - System health checks
    """
    
    def __init__(self, app=None):
        """Initialize alert processor."""
        self.app = app
        self.scheduler = None
        self.is_running = False
        self._stats = {
            'evaluations_completed': 0,
            'alerts_triggered': 0,
            'evaluation_errors': 0,
            'last_evaluation': None,
            'started_at': None,
            'job_failures': 0,
            'missed_jobs': 0
        }
        self._lock = threading.RLock()
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize with Flask app."""
        self.app = app
        
        # Configure scheduler
        job_store_url = app.config.get('DATABASE_URL', 'sqlite:///vertigo_debug.db')
        
        jobstores = {
            'default': SQLAlchemyJobStore(url=job_store_url, tablename='apscheduler_jobs')
        }
        
        executors = {
            'default': ThreadPoolExecutor(max_workers=2),  # Limited for resource efficiency
        }
        
        job_defaults = {
            'coalesce': True,  # Combine multiple missed jobs into one
            'max_instances': 1,  # Only one instance of each job at a time
            'misfire_grace_time': 30  # 30 seconds grace period for missed jobs
        }
        
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='UTC'
        )
        
        # Add event listeners
        self.scheduler.add_listener(self._job_executed_listener, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(self._job_error_listener, EVENT_JOB_ERROR)
        self.scheduler.add_listener(self._job_missed_listener, EVENT_JOB_MISSED)
        
        logger.info("Alert processor initialized")
    
    def start(self):
        """Start the alert processor."""
        if self.is_running:
            logger.warning("Alert processor is already running")
            return
        
        try:
            with self._lock:
                if not self.scheduler:
                    raise RuntimeError("Alert processor not initialized")
                
                # Start the scheduler
                self.scheduler.start()
                self.is_running = True
                self._stats['started_at'] = datetime.utcnow()
                
                # Schedule the main evaluation job
                self._schedule_evaluation_job()
                
                # Schedule system health check
                self._schedule_health_check_job()
                
                # Schedule cleanup job
                self._schedule_cleanup_job()
                
                logger.info("Alert processor started successfully")
                
        except Exception as e:
            logger.error(f"Failed to start alert processor: {e}")
            self.is_running = False
            raise
    
    def stop(self, wait_for_jobs: bool = True):
        """Stop the alert processor."""
        if not self.is_running:
            logger.info("Alert processor is not running")
            return
        
        try:
            with self._lock:
                if self.scheduler and self.scheduler.running:
                    self.scheduler.shutdown(wait=wait_for_jobs)
                
                self.is_running = False
                logger.info("Alert processor stopped")
                
        except Exception as e:
            logger.error(f"Error stopping alert processor: {e}")
    
    def restart(self):
        """Restart the alert processor."""
        logger.info("Restarting alert processor...")
        self.stop(wait_for_jobs=False)
        self.start()
    
    def _schedule_evaluation_job(self):
        """Schedule the main alert evaluation job."""
        try:
            # Get evaluation interval from config (default 1 minute)
            interval_seconds = self.app.config.get('ALERT_EVALUATION_INTERVAL_SECONDS', 60)
            
            # Remove existing job if it exists
            if self.scheduler.get_job('evaluate_alerts'):
                self.scheduler.remove_job('evaluate_alerts')
            
            # Schedule new job
            self.scheduler.add_job(
                func=self._evaluate_all_alerts,
                trigger='interval',
                seconds=interval_seconds,
                id='evaluate_alerts',
                name='Alert Rule Evaluation',
                replace_existing=True
            )
            
            logger.info(f"Alert evaluation job scheduled (every {interval_seconds} seconds)")
            
        except Exception as e:
            logger.error(f"Error scheduling evaluation job: {e}")
            raise
    
    def _schedule_health_check_job(self):
        """Schedule system health check job."""
        try:
            # Health check every 5 minutes
            self.scheduler.add_job(
                func=self._system_health_check,
                trigger='interval',
                minutes=5,
                id='system_health_check',
                name='Alert System Health Check',
                replace_existing=True
            )
            
            logger.info("System health check job scheduled")
            
        except Exception as e:
            logger.error(f"Error scheduling health check job: {e}")
    
    def _schedule_cleanup_job(self):
        """Schedule cleanup job for old alert events."""
        try:
            # Cleanup daily at 2 AM UTC
            self.scheduler.add_job(
                func=self._cleanup_old_events,
                trigger='cron',
                hour=2,
                minute=0,
                id='cleanup_old_events',
                name='Cleanup Old Alert Events',
                replace_existing=True
            )
            
            logger.info("Cleanup job scheduled")
            
        except Exception as e:
            logger.error(f"Error scheduling cleanup job: {e}")
    
    def _evaluate_all_alerts(self):
        """Main job function - evaluate all alert rules."""
        evaluation_start = datetime.utcnow()
        
        try:
            # Use app context for database operations
            with self.app.app_context():
                # Get evaluation results
                results = alert_service.evaluate_all_rules(test_mode=False)
                
                # Update statistics
                with self._lock:
                    self._stats['evaluations_completed'] += 1
                    self._stats['alerts_triggered'] += sum(1 for r in results if r.triggered)
                    self._stats['last_evaluation'] = evaluation_start
                
                logger.debug(f"Evaluated {len(results)} alert rules, "
                           f"{sum(1 for r in results if r.triggered)} triggered")
                
        except Exception as e:
            logger.error(f"Error during alert evaluation: {e}")
            with self._lock:
                self._stats['evaluation_errors'] += 1
            raise
    
    def _system_health_check(self):
        """System health check job."""
        try:
            with self.app.app_context():
                # Check database connectivity
                db.session.execute(text("SELECT 1")).fetchone()
                
                # Check for stale alert rules (not evaluated recently)
                stale_threshold = datetime.utcnow() - timedelta(minutes=10)
                
                if self._stats['last_evaluation'] and self._stats['last_evaluation'] < stale_threshold:
                    logger.warning("Alert evaluation appears stale - last evaluation was more than 10 minutes ago")
                
                # Check for excessive failures
                if self._stats['evaluation_errors'] > 10:
                    logger.warning(f"High number of evaluation errors: {self._stats['evaluation_errors']}")
                
                # Check active data sources
                inactive_sources = DataSource.query.filter(
                    DataSource.is_active == True,
                    DataSource.health_status == 'unhealthy'
                ).count()
                
                if inactive_sources > 0:
                    logger.warning(f"{inactive_sources} data sources are unhealthy")
                
                logger.debug("Alert system health check completed")
                
        except Exception as e:
            logger.error(f"Error during system health check: {e}")
    
    def _cleanup_old_events(self):
        """Cleanup old alert events."""
        try:
            with self.app.app_context():
                # Keep events for configured number of days (default 30 days)
                retention_days = self.app.config.get('ALERT_EVENT_RETENTION_DAYS', 30)
                cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
                
                # Delete old resolved events
                deleted_count = AlertEvent.query.filter(
                    AlertEvent.status == 'resolved',
                    AlertEvent.triggered_at < cutoff_date
                ).delete()
                
                # Keep active/acknowledged alerts regardless of age
                db.session.commit()
                
                if deleted_count > 0:
                    logger.info(f"Cleaned up {deleted_count} old alert events")
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            db.session.rollback()
    
    def _job_executed_listener(self, event):
        """Handle job execution events."""
        logger.debug(f"Job executed: {event.job_id}")
    
    def _job_error_listener(self, event):
        """Handle job error events."""
        logger.error(f"Job error: {event.job_id} - {event.exception}")
        with self._lock:
            self._stats['job_failures'] += 1
        
        # Auto-restart on critical failures
        if event.job_id == 'evaluate_alerts':
            failure_count = self._stats['job_failures']
            if failure_count % 5 == 0:  # Every 5 failures
                logger.warning(f"Alert evaluation job has failed {failure_count} times, attempting restart...")
                try:
                    self._schedule_evaluation_job()
                except Exception as e:
                    logger.error(f"Failed to restart evaluation job: {e}")
    
    def _job_missed_listener(self, event):
        """Handle missed job events."""
        logger.warning(f"Job missed: {event.job_id}")
        with self._lock:
            self._stats['missed_jobs'] += 1
    
    # Public API methods
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of alert processor."""
        with self._lock:
            status = {
                'running': self.is_running,
                'scheduler_running': self.scheduler.running if self.scheduler else False,
                'statistics': self._stats.copy(),
                'jobs': []
            }
            
            if self.scheduler and self.is_running:
                try:
                    jobs = self.scheduler.get_jobs()
                    status['jobs'] = [
                        {
                            'id': job.id,
                            'name': job.name,
                            'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                            'trigger': str(job.trigger)
                        }
                        for job in jobs
                    ]
                except Exception as e:
                    logger.error(f"Error getting job list: {e}")
            
            return status
    
    def force_evaluation(self) -> Dict[str, Any]:
        """Force immediate evaluation of all alert rules."""
        if not self.is_running:
            return {
                'success': False,
                'message': 'Alert processor is not running'
            }
        
        try:
            # Schedule immediate evaluation
            self.scheduler.add_job(
                func=self._evaluate_all_alerts,
                id='force_evaluation',
                name='Forced Alert Evaluation',
                replace_existing=True
            )
            
            return {
                'success': True,
                'message': 'Forced evaluation scheduled'
            }
            
        except Exception as e:
            logger.error(f"Error forcing evaluation: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def pause_evaluation(self):
        """Pause alert evaluation."""
        try:
            if self.scheduler and self.scheduler.get_job('evaluate_alerts'):
                self.scheduler.pause_job('evaluate_alerts')
                logger.info("Alert evaluation paused")
                return {'success': True, 'message': 'Alert evaluation paused'}
        except Exception as e:
            logger.error(f"Error pausing evaluation: {e}")
            return {'success': False, 'message': str(e)}
    
    def resume_evaluation(self):
        """Resume alert evaluation."""
        try:
            if self.scheduler and self.scheduler.get_job('evaluate_alerts'):
                self.scheduler.resume_job('evaluate_alerts')
                logger.info("Alert evaluation resumed")
                return {'success': True, 'message': 'Alert evaluation resumed'}
        except Exception as e:
            logger.error(f"Error resuming evaluation: {e}")
            return {'success': False, 'message': str(e)}
    
    def modify_evaluation_interval(self, interval_seconds: int) -> Dict[str, Any]:
        """Modify the evaluation interval."""
        if interval_seconds < 30 or interval_seconds > 3600:
            return {
                'success': False,
                'message': 'Interval must be between 30 seconds and 1 hour'
            }
        
        try:
            # Update app config
            self.app.config['ALERT_EVALUATION_INTERVAL_SECONDS'] = interval_seconds
            
            # Reschedule the job
            self._schedule_evaluation_job()
            
            logger.info(f"Alert evaluation interval updated to {interval_seconds} seconds")
            return {
                'success': True,
                'message': f'Evaluation interval updated to {interval_seconds} seconds'
            }
            
        except Exception as e:
            logger.error(f"Error modifying evaluation interval: {e}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def get_job_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent job execution history."""
        # Note: This would require storing job execution history
        # For now, return basic statistics
        try:
            with self._lock:
                return [{
                    'timestamp': self._stats['last_evaluation'].isoformat() if self._stats['last_evaluation'] else None,
                    'job_type': 'alert_evaluation',
                    'status': 'completed',
                    'evaluations_completed': self._stats['evaluations_completed'],
                    'alerts_triggered': self._stats['alerts_triggered'],
                    'errors': self._stats['evaluation_errors']
                }]
        except Exception as e:
            logger.error(f"Error getting job history: {e}")
            return []
    
    def reset_statistics(self):
        """Reset processor statistics."""
        with self._lock:
            self._stats.update({
                'evaluations_completed': 0,
                'alerts_triggered': 0,
                'evaluation_errors': 0,
                'job_failures': 0,
                'missed_jobs': 0
            })
            logger.info("Alert processor statistics reset")

# Global instance
alert_processor = AlertProcessor()