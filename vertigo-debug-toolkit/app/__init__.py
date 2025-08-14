"""
Vertigo Debug Toolkit - Application Factory

Flask application factory with configuration, database setup, and Langfuse integration.
"""

import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
csrf = CSRFProtect()

# Import services
from app.services.langwatch_client import LangWatchClient
from app.services.vertigo_client import VertigoClient
# from app.services.workflow_simulator import WorkflowSimulator
from app.services.sample_data import SampleDataLoader
from app.services.cloud_monitor import CloudServiceMonitor
from app.services.sync_scheduler import sync_scheduler

def create_app(config_name=None):
    """Application factory function."""
    
    # Create Flask app with correct template and static directories
    template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
    static_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static'))
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    
    # Load configuration directly from environment
    secret_key = os.getenv('FLASK_SECRET_KEY')
    if not secret_key or secret_key == 'dev-secret-key':
        import secrets
        secret_key = secrets.token_hex(32)
        print("WARNING: Using generated secret key. Set FLASK_SECRET_KEY environment variable for production.")
    
    app.config['SECRET_KEY'] = secret_key
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///vertigo_debug.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['DEBUG'] = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Security configurations
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hour
    app.config['SESSION_COOKIE_SECURE'] = not app.config['DEBUG']
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Initialize LangWatch
    app.langwatch = LangWatchClient()
    
    # Register user loader
    from app.models import User
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Initialize core services
    try:
        from app.services.rate_limiter import rate_limiter
    except ImportError:
        pass
        
    try:
        from app.services.auth_service import init_auth_service
        auth_service = init_auth_service(app)
    except ImportError:
        pass
        
    try:
        from app.services.api_key_service import api_key_service
    except ImportError:
        pass
        
    try:
        from app.services.security_monitor import security_monitor
        from app.middleware.security_middleware import security_middleware
        security_middleware.init_app(app)
    except ImportError:
        logger.warning("Security monitoring disabled - models not available")
        # Create a mock security monitor
        class MockSecurityMonitor:
            def record_login_attempt(self, *args, **kwargs):
                pass
            def record_security_event(self, *args, **kwargs):
                pass
            def record_rate_limit_violation(self, *args, **kwargs):
                pass
            def get_security_statistics(self):
                return {'status': 'disabled'}
        
        security_monitor = MockSecurityMonitor()
    
    # Initialize rate limiter (will use Redis if available, fallback to memory)
    try:
        # Test Redis connection for rate limiter
        rate_limiter.redis_client.ping()
        app.logger.info("Rate limiter initialized with Redis backend")
    except Exception as e:
        app.logger.warning(f"Rate limiter using memory fallback: {e}")
    
    # Register blueprints
    from app.blueprints.dashboard import dashboard_bp
    from app.blueprints.prompts import prompts_bp
    from app.blueprints.performance import performance_bp
    from app.blueprints.costs import costs_bp
    from app.blueprints.live_data import live_data_bp
    from app.blueprints.sync import sync_bp
    from app.blueprints.webhooks import webhooks_bp
    from app.blueprints.analytics import analytics_bp
    from app.blueprints.tenant import tenant_bp
    from app.blueprints.websocket import websocket_bp
    from app.blueprints.visualizations import visualizations_bp
    from app.blueprints.security import security_bp
    from app.blueprints.ml_optimization import ml_optimization
    from app.blueprints.anomaly_response import anomaly_response_bp
    from app.blueprints.predictive_scaling import predictive_scaling_bp
    from app.blueprints.health import health_bp
    from app.auth import auth_bp
    
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(prompts_bp, url_prefix='/prompts')
    app.register_blueprint(performance_bp, url_prefix='/performance')
    app.register_blueprint(costs_bp, url_prefix='/costs')
    app.register_blueprint(live_data_bp, url_prefix='/live-data')
    app.register_blueprint(sync_bp)  # Already has /api/sync prefix in blueprint
    app.register_blueprint(webhooks_bp)  # Already has /api/webhooks prefix in blueprint
    app.register_blueprint(analytics_bp)  # Already has /analytics prefix in blueprint
    app.register_blueprint(tenant_bp)  # Already has /tenant prefix in blueprint
    app.register_blueprint(websocket_bp)  # Already has /ws prefix in blueprint
    app.register_blueprint(visualizations_bp)  # Already has /viz prefix in blueprint
    app.register_blueprint(security_bp)  # Security management endpoints
    app.register_blueprint(ml_optimization)  # ML optimization endpoints with /ml prefix
    app.register_blueprint(anomaly_response_bp)  # Already has /anomaly-response prefix in blueprint
    app.register_blueprint(predictive_scaling_bp, url_prefix='/predictive-scaling')  # Predictive scaling endpoints
    app.register_blueprint(health_bp)  # Health check endpoints
    app.register_blueprint(auth_bp)
    
    # Add rate limiting to API endpoints
    @app.before_request
    def check_rate_limits():
        # Skip rate limiting for static files and certain paths
        from flask import request, jsonify, g
        
        if (request.path.startswith('/static/') or 
            request.path.startswith('/favicon.ico') or
            request.path.startswith('/health')):
            return
        
        # Check rate limits for API endpoints
        if request.path.startswith('/api/') or request.path.startswith('/security/api/'):
            try:
                rate_limit_result = rate_limiter.check_rate_limit(request.path)
                g.rate_limit_result = rate_limit_result
                
                if not rate_limit_result.allowed:
                    # Record rate limit violation
                    from app.services.security_monitor import security_monitor
                    from flask_login import current_user
                    
                    security_monitor.record_rate_limit_violation(
                        identifier=f"user:{current_user.id}" if current_user.is_authenticated else f"ip:{request.remote_addr}",
                        identifier_type="user" if current_user.is_authenticated else "ip",
                        limit_type="requests_per_minute",
                        limit_value=rate_limit_result.limit,
                        current_count=rate_limit_result.limit - rate_limit_result.remaining,
                        user_id=current_user.id if current_user.is_authenticated else None
                    )
                    
                    return jsonify({
                        'error': 'Rate limit exceeded',
                        'message': 'Too many requests. Please try again later.',
                        'retry_after': rate_limit_result.retry_after
                    }), 429
                    
            except Exception as e:
                app.logger.error(f"Error checking rate limits: {e}")
                # Continue without rate limiting if there's an error
    
    # Enhanced security headers (now handled by security middleware)
    # Keep this minimal version as backup
    @app.after_request
    def add_basic_security_headers(response):
        if not hasattr(response, 'headers'):
            return response
            
        # Only add headers if not already set by security middleware
        if 'X-Content-Type-Options' not in response.headers:
            response.headers['X-Content-Type-Options'] = 'nosniff'
        if 'X-Frame-Options' not in response.headers:
            response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        if 'X-XSS-Protection' not in response.headers:
            response.headers['X-XSS-Protection'] = '1; mode=block'
            
        return response
    
    # Initialize SocketIO
    from app.extensions import socketio
    socketio.init_app(app, cors_allowed_origins="*")
    
    # Initialize WebSocket service
    from app.services.websocket_service import init_websocket_service
    init_websocket_service(socketio)
    
    # Create database tables
    with app.app_context():
        db.create_all()
        
        # Initialize and start sync scheduler if enabled
        if app.config.get('ENABLE_FIRESTORE_SYNC', True):
            try:
                sync_scheduler.init_app(app)
                sync_scheduler.start()
                app.logger.info("Firestore sync scheduler started successfully")
            except Exception as e:
                app.logger.error(f"Failed to start sync scheduler: {e}")
    
    # Register shutdown handler
    @app.teardown_appcontext
    def shutdown_scheduler(exception):
        """Shutdown scheduler on app teardown."""
        if sync_scheduler.is_running:
            sync_scheduler.shutdown(wait=False)
    
    return app

class Config:
    """Base configuration."""
    
    SECRET_KEY = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///vertigo_debug.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # LangWatch configuration
    LANGWATCH_API_KEY = os.getenv('LANGWATCH_API_KEY')
    LANGWATCH_PROJECT_ID = os.getenv('LANGWATCH_PROJECT_ID', 'vertigo-llm-observability-3Jujjc')
    LANGWATCH_HOST = os.getenv('LANGWATCH_HOST', 'https://app.langwatch.ai')
    
    # Vertigo configuration
    VERTIGO_API_URL = os.getenv('VERTIGO_API_URL')
    GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
    
    # Live Data Integration
    ENABLE_LIVE_DATA = os.getenv('ENABLE_LIVE_DATA', 'true').lower() == 'true'
    ENABLE_FIRESTORE_SYNC = os.getenv('ENABLE_FIRESTORE_SYNC', 'true').lower() == 'true'
    FIRESTORE_SYNC_INTERVAL_MINUTES = int(os.getenv('FIRESTORE_SYNC_INTERVAL_MINUTES', '5'))
    FIRESTORE_SYNC_BATCH_SIZE = int(os.getenv('FIRESTORE_SYNC_BATCH_SIZE', '100'))
    SYNC_MAX_WORKERS = int(os.getenv('SYNC_MAX_WORKERS', '2'))
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    WEBHOOK_SIGNATURE_VERIFICATION = os.getenv('WEBHOOK_SIGNATURE_VERIFICATION', 'true').lower() == 'true'
    
    # Webhook secrets
    LANGWATCH_WEBHOOK_SECRET = os.getenv('LANGWATCH_WEBHOOK_SECRET')
    CUSTOM_WEBHOOK_SECRET = os.getenv('CUSTOM_WEBHOOK_SECRET', 'dev-secret-key')
    
    # Google Cloud
    GOOGLE_CLOUD_PROJECT = os.getenv('GOOGLE_CLOUD_PROJECT')
    
    # Pagination
    POSTS_PER_PAGE = 25
    
    # File upload
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'uploads'
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

class DevelopmentConfig(Config):
    """Development configuration."""
    
    DEBUG = True
    SQLALCHEMY_ECHO = True

class ProductionConfig(Config):
    """Production configuration."""
    
    DEBUG = False
    SQLALCHEMY_ECHO = False
    
    # Security headers
    SECURE_HEADERS = {
        'STRICT_TRANSPORT_SECURITY': 'max-age=31536000; includeSubDomains',
        'X_CONTENT_TYPE_OPTIONS': 'nosniff',
        'X_FRAME_OPTIONS': 'SAMEORIGIN',
        'X_XSS_PROTECTION': '1; mode=block'
    }

class TestingConfig(Config):
    """Testing configuration."""
    
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False 