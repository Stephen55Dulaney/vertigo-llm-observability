#!/usr/bin/env python3
"""
Deployment script for live data integration features.
Handles deployment, configuration, and health checks.
"""

import os
import sys
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path

# Add the app directory to Python path
current_dir = Path(__file__).parent
app_dir = current_dir.parent
sys.path.insert(0, str(app_dir))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LiveDataDeployment:
    """Manages deployment of live data integration features."""
    
    def __init__(self):
        self.app_dir = Path(__file__).parent.parent
        self.deployment_config = self._load_deployment_config()
    
    def _load_deployment_config(self) -> dict:
        """Load deployment configuration."""
        config_file = self.app_dir / "deploy" / "config.json"
        
        default_config = {
            "environment": "production",
            "features": {
                "firestore_sync": True,
                "webhook_endpoints": True,
                "cache_optimization": True,
                "real_time_updates": False  # WebSocket support comes later
            },
            "security": {
                "webhook_signature_verification": True,
                "admin_only_sync_triggers": True,
                "rate_limiting": True
            },
            "performance": {
                "redis_caching": False,  # Will be enabled if Redis available
                "batch_size": 100,
                "sync_interval_minutes": 15
            }
        }
        
        if config_file.exists():
            try:
                with open(config_file) as f:
                    user_config = json.load(f)
                
                # Merge with defaults
                default_config.update(user_config)
            except Exception as e:
                logger.warning(f"Could not load config file: {e}")
        
        return default_config
    
    def deploy(self) -> bool:
        """Deploy live data integration features."""
        try:
            logger.info("Starting live data integration deployment...")
            
            # Step 1: Apply database migrations
            if not self._apply_migrations():
                return False
            
            # Step 2: Update application configuration
            if not self._update_app_config():
                return False
            
            # Step 3: Install additional requirements
            if not self._install_requirements():
                return False
            
            # Step 4: Configure background services
            if not self._setup_background_services():
                return False
            
            # Step 5: Run health checks
            if not self._run_health_checks():
                return False
            
            # Step 6: Generate deployment report
            self._generate_deployment_report()
            
            logger.info("Live data integration deployment completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"Deployment failed: {e}")
            return False
    
    def _apply_migrations(self) -> bool:
        """Apply database migrations."""
        try:
            logger.info("Applying database migrations...")
            
            migration_script = self.app_dir / "migrations" / "apply_migration.py"
            
            result = subprocess.run([
                sys.executable, str(migration_script)
            ], capture_output=True, text=True, cwd=str(self.app_dir))
            
            if result.returncode == 0:
                logger.info("Database migrations applied successfully")
                return True
            else:
                logger.error(f"Migration failed: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Error applying migrations: {e}")
            return False
    
    def _update_app_config(self) -> bool:
        """Update Flask application configuration."""
        try:
            logger.info("Updating application configuration...")
            
            # Create or update environment file
            env_file = self.app_dir / ".env"
            env_updates = []
            
            # Add live data configuration
            if self.deployment_config["features"]["webhook_endpoints"]:
                env_updates.extend([
                    "# Live Data Integration Settings",
                    "ENABLE_LIVE_DATA=true",
                    "WEBHOOK_SIGNATURE_VERIFICATION=true"
                ])
            
            if self.deployment_config["features"]["firestore_sync"]:
                env_updates.extend([
                    "ENABLE_FIRESTORE_SYNC=true",
                    f"SYNC_BATCH_SIZE={self.deployment_config['performance']['batch_size']}",
                    f"SYNC_INTERVAL_MINUTES={self.deployment_config['performance']['sync_interval_minutes']}"
                ])
            
            # Check for Redis availability
            if self._check_redis_availability():
                env_updates.append("REDIS_CACHING=true")
                self.deployment_config["performance"]["redis_caching"] = True
            
            # Append to .env file
            if env_updates:
                with open(env_file, "a") as f:
                    f.write("\n" + "\n".join(env_updates) + "\n")
                
                logger.info("Environment configuration updated")
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating app config: {e}")
            return False
    
    def _install_requirements(self) -> bool:
        """Install additional Python requirements."""
        try:
            logger.info("Installing additional requirements...")
            
            # Additional packages for live data integration
            additional_packages = [
                "google-cloud-firestore>=2.11.0",
                "redis>=4.5.0",
                "celery>=5.3.0"  # For background tasks
            ]
            
            for package in additional_packages:
                try:
                    result = subprocess.run([
                        sys.executable, "-m", "pip", "install", package
                    ], capture_output=True, text=True)
                    
                    if result.returncode == 0:
                        logger.info(f"Installed {package}")
                    else:
                        logger.warning(f"Failed to install {package}: {result.stderr}")
                
                except Exception as e:
                    logger.warning(f"Error installing {package}: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error installing requirements: {e}")
            return False
    
    def _setup_background_services(self) -> bool:
        """Setup background services for sync and monitoring."""
        try:
            logger.info("Setting up background services...")
            
            # Create systemd service file for periodic sync (Linux)
            if os.path.exists("/etc/systemd/system"):
                service_file = Path("/etc/systemd/system/vertigo-sync.service")
                timer_file = Path("/etc/systemd/system/vertigo-sync.timer")
                
                service_content = f"""[Unit]
Description=Vertigo Data Sync Service
After=network.target

[Service]
Type=oneshot
User={os.getenv('USER', 'vertigo')}
WorkingDirectory={self.app_dir}
ExecStart={sys.executable} -c "
from app.services.firestore_sync import firestore_sync_service
result = firestore_sync_service.sync_traces_from_firestore()
print(f'Sync completed: {{result.records_processed}} records')
"
Environment=FLASK_APP=app.py

[Install]
WantedBy=multi-user.target
"""
                
                timer_content = f"""[Unit]
Description=Run Vertigo Data Sync every {self.deployment_config['performance']['sync_interval_minutes']} minutes
Requires=vertigo-sync.service

[Timer]
OnCalendar=*:0/{self.deployment_config['performance']['sync_interval_minutes']}
Persistent=true

[Install]
WantedBy=timers.target
"""
                
                try:
                    with open(service_file, 'w') as f:
                        f.write(service_content)
                    
                    with open(timer_file, 'w') as f:
                        f.write(timer_content)
                    
                    # Enable services
                    subprocess.run(["systemctl", "daemon-reload"], check=True)
                    subprocess.run(["systemctl", "enable", "vertigo-sync.timer"], check=True)
                    subprocess.run(["systemctl", "start", "vertigo-sync.timer"], check=True)
                    
                    logger.info("Systemd services configured and started")
                
                except PermissionError:
                    logger.warning("No permission to create systemd services. Run with sudo for production deployment.")
                except subprocess.CalledProcessError as e:
                    logger.warning(f"Systemd service setup failed: {e}")
            
            # Create cron job as fallback
            else:
                self._create_cron_job()
            
            return True
            
        except Exception as e:
            logger.error(f"Error setting up background services: {e}")
            return False
    
    def _create_cron_job(self):
        """Create cron job for periodic sync."""
        try:
            sync_interval = self.deployment_config['performance']['sync_interval_minutes']
            
            cron_entry = f"""# Vertigo Data Sync
*/{sync_interval} * * * * cd {self.app_dir} && {sys.executable} -c "
from app.services.firestore_sync import firestore_sync_service
firestore_sync_service.sync_traces_from_firestore()
" >> /tmp/vertigo-sync.log 2>&1
"""
            
            logger.info("Cron job entry created (manual installation required):")
            logger.info(cron_entry)
            
        except Exception as e:
            logger.warning(f"Could not create cron job: {e}")
    
    def _check_redis_availability(self) -> bool:
        """Check if Redis is available."""
        try:
            import redis
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            client = redis.from_url(redis_url, socket_connect_timeout=5)
            client.ping()
            logger.info("Redis is available and will be used for caching")
            return True
        except Exception:
            logger.info("Redis not available, using in-memory caching")
            return False
    
    def _run_health_checks(self) -> bool:
        """Run post-deployment health checks."""
        try:
            logger.info("Running health checks...")
            
            # Import app components
            from app import create_app
            from app.services import firestore_sync_service, webhook_handler, cache_manager
            
            app = create_app()
            
            with app.app_context():
                # Check database connectivity
                from app.models import db
                db.session.execute("SELECT 1").fetchone()
                logger.info("✓ Database connectivity")
                
                # Check Firestore sync service
                if self.deployment_config["features"]["firestore_sync"]:
                    stats = firestore_sync_service.get_sync_statistics()
                    if 'error' not in stats:
                        logger.info("✓ Firestore sync service")
                    else:
                        logger.warning("⚠ Firestore sync service has issues")
                
                # Check webhook handler
                if self.deployment_config["features"]["webhook_endpoints"]:
                    webhook_stats = webhook_handler.get_webhook_statistics()
                    if 'error' not in webhook_stats:
                        logger.info("✓ Webhook handler")
                    else:
                        logger.warning("⚠ Webhook handler has issues")
                
                # Check cache manager
                cache_stats = cache_manager.get_statistics()
                if 'error' not in cache_stats:
                    logger.info("✓ Cache manager")
                else:
                    logger.warning("⚠ Cache manager has issues")
                
                logger.info("Health checks completed")
                return True
                
        except Exception as e:
            logger.error(f"Health checks failed: {e}")
            return False
    
    def _generate_deployment_report(self):
        """Generate deployment report."""
        try:
            report = {
                "deployment_timestamp": datetime.utcnow().isoformat(),
                "configuration": self.deployment_config,
                "features_deployed": [
                    feature for feature, enabled in self.deployment_config["features"].items()
                    if enabled
                ],
                "next_steps": [
                    "Configure webhook endpoints in external services (LangWatch, Langfuse)",
                    "Set up monitoring alerts for sync failures",
                    "Configure Redis if high-performance caching is needed",
                    "Test webhook endpoints with actual data"
                ],
                "monitoring_endpoints": [
                    "/live-data/api/sync-status",
                    "/live-data/api/live-metrics", 
                    "/performance/api/metrics"
                ]
            }
            
            report_file = self.app_dir / "deployment_report.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            logger.info(f"Deployment report saved to: {report_file}")
            
            # Print summary
            print("\n" + "="*60)
            print("LIVE DATA INTEGRATION DEPLOYMENT SUMMARY")
            print("="*60)
            print(f"Deployment Time: {report['deployment_timestamp']}")
            print(f"Features Deployed: {', '.join(report['features_deployed'])}")
            print(f"Configuration: {self.deployment_config['environment']}")
            
            print("\nNext Steps:")
            for step in report['next_steps']:
                print(f"  • {step}")
            
            print("\nMonitoring Endpoints:")
            for endpoint in report['monitoring_endpoints']:
                print(f"  • {endpoint}")
            
            print("="*60)
            
        except Exception as e:
            logger.error(f"Error generating deployment report: {e}")

def main():
    """Main deployment function."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Deploy live data integration features')
    parser.add_argument('--config', help='Path to deployment configuration file')
    parser.add_argument('--dry-run', action='store_true', help='Perform dry run without making changes')
    
    args = parser.parse_args()
    
    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be made")
        return
    
    deployment = LiveDataDeployment()
    
    if deployment.deploy():
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()