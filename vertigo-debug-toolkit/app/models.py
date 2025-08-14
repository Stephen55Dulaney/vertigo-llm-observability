"""
Database models for the Vertigo Debug Toolkit.
"""

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app import db
import re

class User(UserMixin, db.Model):
    """User model for authentication and authorization."""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Relationships
    prompts = db.relationship('Prompt', backref='creator', lazy='dynamic')
    traces = db.relationship('Trace', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        """Set user password with validation."""
        if not self._validate_password(password):
            raise ValueError("Password does not meet security requirements")
        self.password_hash = generate_password_hash(password)
    
    def _validate_password(self, password):
        """Validate password strength."""
        if len(password) < 12:
            return False
        
        # Check for required character types
        has_upper = bool(re.search(r'[A-Z]', password))
        has_lower = bool(re.search(r'[a-z]', password))
        has_digit = bool(re.search(r'\d', password))
        has_special = bool(re.search(r'[!@#$%^&*()_+\-=\[\]{}|;:,.<>?]', password))
        
        if not (has_upper and has_lower and has_digit and has_special):
            return False
        
        # Check for common weak patterns
        weak_patterns = ['password', '123456', 'admin', 'qwerty', 'letmein']
        if any(pattern in password.lower() for pattern in weak_patterns):
            return False
        
        return True
    
    def check_password(self, password):
        """Check user password."""
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def password_needs_update(self):
        """Check if password needs to be updated (for legacy weak passwords)."""
        # This can be used to force password updates for existing users
        # You could implement logic here to check password age, etc.
        return False
    
    def __repr__(self):
        return f'<User {self.username}>'

class Prompt(db.Model):
    """Prompt model for storing and versioning prompts."""
    
    __tablename__ = 'prompts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    version = db.Column(db.String(20), nullable=False)
    content = db.Column(db.Text, nullable=False)
    prompt_type = db.Column(db.String(50), nullable=False)  # 'summary', 'status', etc.
    tags = db.Column(db.JSON)  # Store tags as JSON
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # LangWatch integration
    langwatch_prompt_id = db.Column(db.String(100))
    
    # Relationships
    traces = db.relationship('Trace', backref='prompt', lazy='dynamic')
    
    def __repr__(self):
        return f'<Prompt {self.name} v{self.version}>'

class Trace(db.Model):
    """Trace model for storing Langfuse traces."""
    
    __tablename__ = 'traces'
    
    id = db.Column(db.Integer, primary_key=True)
    trace_id = db.Column(db.String(100), unique=True, nullable=False)  # Langfuse trace ID
    name = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # 'success', 'error', 'pending'
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    duration_ms = db.Column(db.Integer)  # Duration in milliseconds
    trace_metadata = db.Column(db.JSON)  # Additional trace metadata
    error_message = db.Column(db.Text)
    
    # Relationships
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    prompt_id = db.Column(db.Integer, db.ForeignKey('prompts.id'))
    costs = db.relationship('Cost', backref='trace', lazy='dynamic')
    
    # Vertigo-specific fields
    vertigo_operation = db.Column(db.String(50))  # 'email_processing', 'summary_generation', etc.
    project = db.Column(db.String(100))
    meeting_id = db.Column(db.String(100))
    
    def __repr__(self):
        return f'<Trace {self.trace_id}>'

class Cost(db.Model):
    """Cost model for tracking LLM usage costs."""
    
    __tablename__ = 'costs'
    
    id = db.Column(db.Integer, primary_key=True)
    trace_id = db.Column(db.Integer, db.ForeignKey('traces.id'), nullable=False)
    model = db.Column(db.String(100), nullable=False)  # 'gemini-1.5-pro', 'gpt-4', etc.
    input_tokens = db.Column(db.Integer, default=0)
    output_tokens = db.Column(db.Integer, default=0)
    total_tokens = db.Column(db.Integer, default=0)
    cost_usd = db.Column(db.Numeric(10, 6), default=0)  # Cost in USD
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Cost {self.model}: ${self.cost_usd}>'

class Alert(db.Model):
    """Alert model for monitoring and notifications."""
    
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)  # 'error_rate', 'latency', 'cost'
    threshold = db.Column(db.Float, nullable=False)
    current_value = db.Column(db.Float)
    is_active = db.Column(db.Boolean, default=True)
    is_triggered = db.Column(db.Boolean, default=False)
    triggered_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Alert {self.name}>'

class SampleData(db.Model):
    """Sample data model for testing and demonstrations."""
    
    __tablename__ = 'sample_data'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    data_type = db.Column(db.String(50), nullable=False)  # 'meeting_transcript', 'status_request'
    content = db.Column(db.Text, nullable=False)
    sample_metadata = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<SampleData {self.name}>'

class DataSource(db.Model):
    """Data source model for managing different observability platforms."""
    
    __tablename__ = 'data_sources'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    source_type = db.Column(db.String(50), nullable=False)  # 'firestore', 'langwatch', 'webhook'
    
    # Connection Configuration
    connection_config = db.Column(db.JSON, nullable=False)
    auth_config = db.Column(db.JSON)
    
    # Sync Configuration
    sync_enabled = db.Column(db.Boolean, default=True)
    sync_interval_minutes = db.Column(db.Integer, default=60)
    last_sync_timestamp = db.Column(db.DateTime)
    
    # Health Status
    is_active = db.Column(db.Boolean, default=True)
    health_status = db.Column(db.String(20), default='unknown')  # 'healthy', 'degraded', 'unhealthy', 'unknown'
    last_health_check = db.Column(db.DateTime)
    
    # Metadata
    description = db.Column(db.Text)
    tags = db.Column(db.JSON)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    live_traces = db.relationship('LiveTrace', backref='data_source', lazy='dynamic')
    performance_metrics = db.relationship('PerformanceMetric', backref='data_source', lazy='dynamic')
    sync_statuses = db.relationship('SyncStatus', backref='data_source', lazy='dynamic')
    webhook_events = db.relationship('WebhookEvent', backref='data_source', lazy='dynamic')
    cache_entries = db.relationship('CacheEntry', backref='data_source', lazy='dynamic')
    alert_rules = db.relationship('AlertRule', backref='data_source', lazy='dynamic')
    
    def __repr__(self):
        return f'<DataSource {self.name}>'

class LiveTrace(db.Model):
    """Live trace model for real-time trace data from external sources."""
    
    __tablename__ = 'live_traces'
    
    id = db.Column(db.Integer, primary_key=True)
    external_trace_id = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(200), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # 'success', 'error', 'pending', 'running'
    model = db.Column(db.String(100))
    
    # Timing Information
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    duration_ms = db.Column(db.Integer)
    
    # Input/Output Data
    input_text = db.Column(db.Text)
    output_text = db.Column(db.Text)
    input_tokens = db.Column(db.Integer, default=0)
    output_tokens = db.Column(db.Integer, default=0)
    
    # Cost Information
    cost_usd = db.Column(db.Numeric(10, 6), default=0)
    
    # User and Session Data
    user_id = db.Column(db.String(100))
    session_id = db.Column(db.String(100))
    tags = db.Column(db.JSON)
    trace_metadata = db.Column(db.JSON)
    
    # Source Tracking
    data_source_id = db.Column(db.Integer, db.ForeignKey('data_sources.id'))
    source_updated_at = db.Column(db.DateTime)
    
    # Local Tracking
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # External Source Specific Fields
    firestore_doc_id = db.Column(db.String(200))
    firestore_collection = db.Column(db.String(100))
    langwatch_trace_id = db.Column(db.String(100))
    langwatch_project_id = db.Column(db.String(100))
    
    def __repr__(self):
        return f'<LiveTrace {self.external_trace_id}>'

class PerformanceMetric(db.Model):
    """Performance metrics model for aggregated dashboard data."""
    
    __tablename__ = 'performance_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    period_start = db.Column(db.DateTime, nullable=False)
    period_end = db.Column(db.DateTime, nullable=False)
    period_type = db.Column(db.String(20), nullable=False)  # 'hour', 'day', 'week', 'month'
    
    # Core Performance Metrics
    total_traces = db.Column(db.Integer, default=0)
    success_count = db.Column(db.Integer, default=0)
    error_count = db.Column(db.Integer, default=0)
    success_rate = db.Column(db.Numeric(5, 2), default=0.0)
    error_rate = db.Column(db.Numeric(5, 2), default=0.0)
    
    # Latency Metrics
    avg_latency_ms = db.Column(db.Numeric(10, 2), default=0.0)
    p50_latency_ms = db.Column(db.Numeric(10, 2), default=0.0)
    p95_latency_ms = db.Column(db.Numeric(10, 2), default=0.0)
    p99_latency_ms = db.Column(db.Numeric(10, 2), default=0.0)
    min_latency_ms = db.Column(db.Numeric(10, 2), default=0.0)
    max_latency_ms = db.Column(db.Numeric(10, 2), default=0.0)
    
    # Cost Metrics
    total_cost = db.Column(db.Numeric(10, 6), default=0.0)
    avg_cost_per_request = db.Column(db.Numeric(10, 6), default=0.0)
    input_tokens_total = db.Column(db.Integer, default=0)
    output_tokens_total = db.Column(db.Integer, default=0)
    
    # Distribution Data
    model_distribution = db.Column(db.JSON)
    operation_distribution = db.Column(db.JSON)
    
    # Source Information
    data_source_id = db.Column(db.Integer, db.ForeignKey('data_sources.id'))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<PerformanceMetric {self.period_start} - {self.period_end}>'

class SyncStatus(db.Model):
    """Sync status model for tracking data synchronization health."""
    
    __tablename__ = 'sync_status'
    
    id = db.Column(db.Integer, primary_key=True)
    data_source_id = db.Column(db.Integer, db.ForeignKey('data_sources.id'), nullable=False)
    sync_type = db.Column(db.String(50), nullable=False)
    last_sync_timestamp = db.Column(db.DateTime, nullable=False)
    last_successful_sync = db.Column(db.DateTime)
    sync_status = db.Column(db.String(20), default='pending')  # 'success', 'error', 'pending', 'running'
    records_processed = db.Column(db.Integer, default=0)
    records_failed = db.Column(db.Integer, default=0)
    error_message = db.Column(db.Text)
    sync_metadata = db.Column(db.JSON)
    next_sync_due = db.Column(db.DateTime)
    sync_interval_minutes = db.Column(db.Integer, default=60)
    
    # Health Metrics
    consecutive_failures = db.Column(db.Integer, default=0)
    last_error_timestamp = db.Column(db.DateTime)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    __table_args__ = (db.UniqueConstraint('data_source_id', 'sync_type', name='_data_source_sync_type_uc'),)
    
    def __repr__(self):
        return f'<SyncStatus {self.data_source.name if self.data_source else "Unknown"} - {self.sync_type}>'

class WebhookEvent(db.Model):
    """Webhook event model for storing incoming webhook data."""
    
    __tablename__ = 'webhook_events'
    
    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.String(100), unique=True, nullable=False)
    event_type = db.Column(db.String(50), nullable=False)
    source = db.Column(db.String(50), nullable=False)
    data_source_id = db.Column(db.Integer, db.ForeignKey('data_sources.id'))
    
    # Event Data
    payload = db.Column(db.JSON, nullable=False)
    headers = db.Column(db.JSON)
    
    # Processing Status
    processed = db.Column(db.Boolean, default=False)
    processing_error = db.Column(db.Text)
    retry_count = db.Column(db.Integer, default=0)
    max_retries = db.Column(db.Integer, default=3)
    
    # Timestamps
    received_at = db.Column(db.DateTime, default=datetime.utcnow)
    processed_at = db.Column(db.DateTime)
    next_retry_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<WebhookEvent {self.event_id}>'

class CacheEntry(db.Model):
    """Cache entry model for local caching."""
    
    __tablename__ = 'cache_entries'
    
    id = db.Column(db.Integer, primary_key=True)
    cache_key = db.Column(db.String(255), nullable=False, unique=True)
    cache_value = db.Column(db.JSON, nullable=False)
    
    # Cache Metadata
    cache_type = db.Column(db.String(50), nullable=False)
    data_source_id = db.Column(db.Integer, db.ForeignKey('data_sources.id'))
    
    # Expiration Management
    expires_at = db.Column(db.DateTime)
    ttl_seconds = db.Column(db.Integer, default=3600)
    
    # Usage Tracking
    hit_count = db.Column(db.Integer, default=0)
    last_accessed = db.Column(db.DateTime)
    
    # Data Integrity
    checksum = db.Column(db.String(64))
    version = db.Column(db.Integer, default=1)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def is_expired(self):
        """Check if cache entry is expired."""
        if self.expires_at:
            return datetime.utcnow() > self.expires_at
        return False
    
    def __repr__(self):
        return f'<CacheEntry {self.cache_key}>'

class AlertRule(db.Model):
    """Alert rule model for monitoring and notifications."""
    
    __tablename__ = 'alert_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)
    data_source_id = db.Column(db.Integer, db.ForeignKey('data_sources.id'))
    
    # Threshold Configuration
    threshold_value = db.Column(db.Numeric(10, 4), nullable=False)
    comparison_operator = db.Column(db.String(10), default='>')  # '>', '<', '>=', '<=', '=', '!='
    time_window_minutes = db.Column(db.Integer, default=5)
    
    # Rule Configuration
    is_active = db.Column(db.Boolean, default=True)
    notification_channels = db.Column(db.JSON)
    severity = db.Column(db.String(20), default='medium')  # 'low', 'medium', 'high', 'critical'
    
    # Conditions
    condition_query = db.Column(db.Text)
    condition_metadata = db.Column(db.JSON)
    
    # State Management
    last_triggered = db.Column(db.DateTime)
    trigger_count = db.Column(db.Integer, default=0)
    cooldown_minutes = db.Column(db.Integer, default=60)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    alert_events = db.relationship('AlertEvent', backref='alert_rule', lazy='dynamic')
    
    def __repr__(self):
        return f'<AlertRule {self.name}>'

class AlertEvent(db.Model):
    """Alert event model for triggered alerts."""
    
    __tablename__ = 'alert_events'
    
    id = db.Column(db.Integer, primary_key=True)
    rule_id = db.Column(db.Integer, db.ForeignKey('alert_rules.id'), nullable=False)
    triggered_at = db.Column(db.DateTime, nullable=False)
    resolved_at = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='active')  # 'active', 'resolved', 'acknowledged', 'suppressed'
    
    # Alert Data
    trigger_value = db.Column(db.Numeric(10, 4))
    threshold_value = db.Column(db.Numeric(10, 4))
    message = db.Column(db.Text)
    severity = db.Column(db.String(20))
    context_data = db.Column(db.JSON)
    
    # Notification Tracking
    notifications_sent = db.Column(db.JSON)
    acknowledgment_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    acknowledgment_note = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AlertEvent {self.alert_rule.name if self.alert_rule else "Unknown"} - {self.triggered_at}>'

# Indexes for better performance (existing)
db.Index('idx_traces_trace_id', Trace.trace_id)
db.Index('idx_traces_start_time', Trace.start_time)
db.Index('idx_traces_status', Trace.status)
db.Index('idx_costs_timestamp', Cost.timestamp)
db.Index('idx_prompts_type', Prompt.prompt_type)
db.Index('idx_prompts_active', Prompt.is_active)

# New indexes for live data tables
db.Index('idx_live_traces_external_id', LiveTrace.external_trace_id)
db.Index('idx_live_traces_start_time', LiveTrace.start_time)
db.Index('idx_live_traces_status_time', LiveTrace.status, LiveTrace.start_time)
db.Index('idx_live_traces_data_source', LiveTrace.data_source_id, LiveTrace.updated_at)

db.Index('idx_performance_metrics_period', PerformanceMetric.period_start, PerformanceMetric.period_end, PerformanceMetric.period_type)
db.Index('idx_performance_metrics_data_source', PerformanceMetric.data_source_id, PerformanceMetric.created_at)

db.Index('idx_sync_status_data_source', SyncStatus.data_source_id, SyncStatus.sync_type)
db.Index('idx_sync_status_timestamp', SyncStatus.last_sync_timestamp)

db.Index('idx_webhook_events_processed', WebhookEvent.processed, WebhookEvent.received_at)
db.Index('idx_webhook_events_source', WebhookEvent.source, WebhookEvent.event_type)

db.Index('idx_cache_entries_key', CacheEntry.cache_key)
db.Index('idx_cache_entries_expires', CacheEntry.expires_at)
db.Index('idx_cache_entries_type_source', CacheEntry.cache_type, CacheEntry.data_source_id)

db.Index('idx_data_sources_type', DataSource.source_type, DataSource.is_active)
db.Index('idx_data_sources_health', DataSource.health_status, DataSource.last_health_check)

db.Index('idx_alert_rules_active', AlertRule.is_active, AlertRule.alert_type)
db.Index('idx_alert_events_rule', AlertEvent.rule_id, AlertEvent.triggered_at)

# Tenant Models for Multi-Tenant Architecture
from enum import Enum


class TenantStatus(Enum):
    """Tenant status enumeration."""
    ACTIVE = "active"
    SUSPENDED = "suspended" 
    INACTIVE = "inactive"
    TRIAL = "trial"
    ENTERPRISE = "enterprise"


class AccessLevel(Enum):
    """Access level enumeration."""
    READ = "read"
    WRITE = "write"
    ADMIN = "admin"
    OWNER = "owner"


class TenantModel(db.Model):
    """Tenant model for multi-tenant data isolation."""
    
    __tablename__ = 'tenants'
    
    id = db.Column(db.String(36), primary_key=True)  # UUID
    name = db.Column(db.String(100), nullable=False)
    domain = db.Column(db.String(100), nullable=False, unique=True)
    status = db.Column(db.String(20), nullable=False, default='active')
    
    # Owner relationship
    owner_id = db.Column(db.String(36), nullable=False)  # User ID as string for flexibility
    
    # Security
    api_key = db.Column(db.String(128), nullable=False, unique=True)
    webhook_secret = db.Column(db.String(128), nullable=False)
    
    # Isolation
    database_schema = db.Column(db.String(100), nullable=False)
    storage_prefix = db.Column(db.String(200), nullable=False)
    
    # Configuration
    max_users = db.Column(db.Integer, default=25)
    max_projects = db.Column(db.Integer, default=10)
    max_storage_gb = db.Column(db.Float, default=5.0)
    max_api_calls_per_hour = db.Column(db.Integer, default=5000)
    retention_days = db.Column(db.Integer, default=90)
    features_enabled = db.Column(db.JSON)
    custom_settings = db.Column(db.JSON)
    tenant_metadata = db.Column(db.JSON)
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    tenant_users = db.relationship('TenantUserModel', backref='tenant', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<TenantModel {self.name}>'


class TenantUserModel(db.Model):
    """Tenant user association model."""
    
    __tablename__ = 'tenant_users'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.String(36), db.ForeignKey('tenants.id'), nullable=False)
    user_id = db.Column(db.String(36), nullable=False)  # String for flexibility
    access_level = db.Column(db.String(20), nullable=False, default='read')
    
    # Permissions and metadata
    permissions = db.Column(db.JSON)
    tenant_metadata = db.Column(db.JSON)
    
    # Expiration
    expires_at = db.Column(db.DateTime)
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Constraints
    __table_args__ = (
        db.UniqueConstraint('tenant_id', 'user_id', name='_tenant_user_uc'),
    )
    
    def __repr__(self):
        return f'<TenantUserModel {self.tenant_id}:{self.user_id}>'


# Add tenant indexes for performance
db.Index('idx_tenants_domain', TenantModel.domain)
db.Index('idx_tenants_status', TenantModel.status)
db.Index('idx_tenants_api_key', TenantModel.api_key)
db.Index('idx_tenant_users_tenant', TenantUserModel.tenant_id)
db.Index('idx_tenant_users_user', TenantUserModel.user_id)
db.Index('idx_tenant_users_access', TenantUserModel.tenant_id, TenantUserModel.access_level)


# ML Optimization Models
class PromptPerformanceAnalysis(db.Model):
    """Prompt performance analysis results storage."""
    
    __tablename__ = 'prompt_performance_analysis'
    
    id = db.Column(db.Integer, primary_key=True)
    prompt_id = db.Column(db.String(100), nullable=False)
    analysis_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Performance Metrics
    total_executions = db.Column(db.Integer, default=0)
    avg_latency_ms = db.Column(db.Numeric(10, 2), default=0.0)
    avg_cost_usd = db.Column(db.Numeric(10, 6), default=0.0)
    success_rate = db.Column(db.Numeric(5, 4), default=0.0)
    error_rate = db.Column(db.Numeric(5, 4), default=0.0)
    p95_latency_ms = db.Column(db.Numeric(10, 2), default=0.0)
    cost_per_success = db.Column(db.Numeric(10, 6), default=0.0)
    
    # ML Analysis Results
    optimization_potential = db.Column(db.Numeric(5, 4), default=0.0)
    quality_score = db.Column(db.Numeric(5, 2), default=0.0)
    performance_trends = db.Column(db.JSON)
    
    # Analysis Period
    analysis_period_days = db.Column(db.Integer, default=30)
    data_sources = db.Column(db.JSON)  # Which data sources were analyzed
    
    # Metadata
    analysis_version = db.Column(db.String(20), default='1.0')
    confidence_score = db.Column(db.Numeric(5, 4), default=0.0)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<PromptPerformanceAnalysis {self.prompt_id} - {self.analysis_date}>'


class PromptQualityAssessment(db.Model):
    """Prompt quality assessment results storage."""
    
    __tablename__ = 'prompt_quality_assessments'
    
    id = db.Column(db.Integer, primary_key=True)
    prompt_id = db.Column(db.String(100), nullable=False)
    prompt_text_hash = db.Column(db.String(64))  # Hash of prompt text for change detection
    assessment_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Overall Quality Metrics
    overall_score = db.Column(db.Numeric(5, 2), default=0.0)
    grade = db.Column(db.String(5))  # A+, A, B+, B, C+, C, D, F
    
    # Individual Quality Metrics
    clarity_specificity_score = db.Column(db.Numeric(5, 2), default=0.0)
    structure_organization_score = db.Column(db.Numeric(5, 2), default=0.0)
    performance_consistency_score = db.Column(db.Numeric(5, 2), default=0.0)
    token_efficiency_score = db.Column(db.Numeric(5, 2), default=0.0)
    error_resilience_score = db.Column(db.Numeric(5, 2), default=0.0)
    context_appropriateness_score = db.Column(db.Numeric(5, 2), default=0.0)
    
    # Assessment Results
    strengths = db.Column(db.JSON)  # List of identified strengths
    weaknesses = db.Column(db.JSON)  # List of identified weaknesses
    optimization_priority = db.Column(db.String(20), default='low')  # high, medium, low
    estimated_improvement_potential = db.Column(db.Numeric(5, 4), default=0.0)
    
    # Detailed Analysis
    quality_evidence = db.Column(db.JSON)  # Supporting evidence for scores
    recommendations = db.Column(db.JSON)  # Specific improvement recommendations
    
    # Metadata
    assessment_version = db.Column(db.String(20), default='1.0')
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<PromptQualityAssessment {self.prompt_id} - {self.overall_score}>'


class PerformancePattern(db.Model):
    """Detected performance patterns storage."""
    
    __tablename__ = 'performance_patterns'
    
    id = db.Column(db.Integer, primary_key=True)
    pattern_id = db.Column(db.String(100), nullable=False, unique=True)
    pattern_type = db.Column(db.String(50), nullable=False)  # high_latency_spikes, cost_inefficiency, etc.
    detection_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Pattern Details
    pattern_description = db.Column(db.Text, nullable=False)
    frequency = db.Column(db.Integer, default=0)
    avg_latency = db.Column(db.Numeric(10, 2), default=0.0)
    avg_cost = db.Column(db.Numeric(10, 6), default=0.0)
    success_rate = db.Column(db.Numeric(5, 4), default=0.0)
    confidence_score = db.Column(db.Numeric(5, 4), default=0.0)
    
    # Affected Resources
    affected_prompts = db.Column(db.JSON)  # List of affected prompt IDs
    affected_models = db.Column(db.JSON)  # List of affected models
    
    # Pattern Evidence
    sample_data = db.Column(db.JSON)  # Sample traces that demonstrate the pattern
    statistical_evidence = db.Column(db.JSON)  # Statistical analysis supporting the pattern
    
    # Analysis Period
    detection_period_start = db.Column(db.DateTime)
    detection_period_end = db.Column(db.DateTime)
    analysis_period_days = db.Column(db.Integer, default=30)
    
    # Pattern Status
    is_active = db.Column(db.Boolean, default=True)
    resolved_at = db.Column(db.DateTime)
    resolution_notes = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<PerformancePattern {self.pattern_type} - {self.detection_date}>'


class OptimizationRecommendation(db.Model):
    """ML-generated optimization recommendations storage."""
    
    __tablename__ = 'optimization_recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    recommendation_id = db.Column(db.String(100), nullable=False, unique=True)
    category = db.Column(db.String(50), nullable=False)  # performance, quality, cost, reliability
    priority = db.Column(db.String(20), nullable=False)  # critical, high, medium, low
    
    # Recommendation Details
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    rationale = db.Column(db.Text)
    
    # Expected Impact
    expected_impact = db.Column(db.JSON)  # metrics -> expected improvement
    implementation_effort = db.Column(db.String(20), default='medium')  # low, medium, high
    timeframe = db.Column(db.String(20), default='short-term')  # immediate, short-term, long-term
    
    # Implementation Details
    specific_actions = db.Column(db.JSON)  # List of specific action items
    prerequisites = db.Column(db.JSON)  # List of prerequisites
    success_metrics = db.Column(db.JSON)  # List of success criteria
    confidence_score = db.Column(db.Numeric(5, 4), default=0.0)
    
    # Applicability
    applicable_prompts = db.Column(db.JSON)  # List of prompt IDs this applies to
    applicable_models = db.Column(db.JSON)  # List of models this applies to
    tags = db.Column(db.JSON)  # Categorization tags
    
    # Recommendation Status
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected, implemented
    implemented_at = db.Column(db.DateTime)
    implementation_notes = db.Column(db.Text)
    
    # Generation Context
    generated_from_analysis_id = db.Column(db.Integer, db.ForeignKey('prompt_performance_analysis.id'))
    generated_from_pattern_id = db.Column(db.Integer, db.ForeignKey('performance_patterns.id'))
    generation_context = db.Column(db.JSON)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<OptimizationRecommendation {self.title} - {self.priority}>'


class MLAnalysisRun(db.Model):
    """ML analysis execution tracking."""
    
    __tablename__ = 'ml_analysis_runs'
    
    id = db.Column(db.Integer, primary_key=True)
    run_id = db.Column(db.String(100), nullable=False, unique=True)
    analysis_type = db.Column(db.String(50), nullable=False)  # comprehensive, targeted, quality_only, etc.
    
    # Execution Details
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    duration_seconds = db.Column(db.Numeric(10, 2))
    status = db.Column(db.String(20), default='running')  # running, completed, failed, cancelled
    
    # Analysis Parameters
    analysis_parameters = db.Column(db.JSON)  # Parameters used for the analysis
    data_period_days = db.Column(db.Integer, default=30)
    prompts_analyzed = db.Column(db.Integer, default=0)
    patterns_detected = db.Column(db.Integer, default=0)
    recommendations_generated = db.Column(db.Integer, default=0)
    
    # Results Summary
    results_summary = db.Column(db.JSON)
    quality_insights = db.Column(db.JSON)
    performance_insights = db.Column(db.JSON)
    
    # Error Information
    error_message = db.Column(db.Text)
    error_traceback = db.Column(db.Text)
    
    # Resource Usage
    memory_usage_mb = db.Column(db.Numeric(10, 2))
    cpu_usage_percent = db.Column(db.Numeric(5, 2))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<MLAnalysisRun {self.run_id} - {self.status}>'


class ModelPerformanceComparison(db.Model):
    """Model performance comparison results."""
    
    __tablename__ = 'model_performance_comparisons'
    
    id = db.Column(db.Integer, primary_key=True)
    comparison_id = db.Column(db.String(100), nullable=False, unique=True)
    model_name = db.Column(db.String(100), nullable=False)
    comparison_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Performance Metrics
    avg_latency = db.Column(db.Numeric(10, 2), default=0.0)
    avg_cost = db.Column(db.Numeric(10, 6), default=0.0)
    success_rate = db.Column(db.Numeric(5, 4), default=0.0)
    
    # Efficiency Scores
    cost_efficiency_score = db.Column(db.Numeric(5, 4), default=0.0)
    latency_efficiency_score = db.Column(db.Numeric(5, 4), default=0.0)
    overall_score = db.Column(db.Numeric(5, 4), default=0.0)
    
    # Comparison Context
    total_requests = db.Column(db.Integer, default=0)
    analysis_period_days = db.Column(db.Integer, default=30)
    comparison_group = db.Column(db.String(100))  # Group ID for related comparisons
    
    # Statistical Significance
    confidence_interval = db.Column(db.JSON)  # Statistical confidence intervals
    statistical_significance = db.Column(db.Numeric(5, 4))  # p-value or similar
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ModelPerformanceComparison {self.model_name} - {self.overall_score}>'


# ML Optimization Indexes
db.Index('idx_prompt_performance_prompt', PromptPerformanceAnalysis.prompt_id, PromptPerformanceAnalysis.analysis_date)
db.Index('idx_prompt_performance_optimization', PromptPerformanceAnalysis.optimization_potential.desc())

db.Index('idx_quality_assessment_prompt', PromptQualityAssessment.prompt_id, PromptQualityAssessment.assessment_date)
db.Index('idx_quality_assessment_score', PromptQualityAssessment.overall_score.desc())
db.Index('idx_quality_assessment_priority', PromptQualityAssessment.optimization_priority)

db.Index('idx_performance_patterns_type', PerformancePattern.pattern_type, PerformancePattern.detection_date)
db.Index('idx_performance_patterns_active', PerformancePattern.is_active, PerformancePattern.confidence_score.desc())

db.Index('idx_optimization_recommendations_priority', OptimizationRecommendation.priority, OptimizationRecommendation.created_at.desc())
db.Index('idx_optimization_recommendations_status', OptimizationRecommendation.status, OptimizationRecommendation.category)
db.Index('idx_optimization_recommendations_confidence', OptimizationRecommendation.confidence_score.desc())

db.Index('idx_ml_analysis_runs_type_status', MLAnalysisRun.analysis_type, MLAnalysisRun.status)
db.Index('idx_ml_analysis_runs_start_time', MLAnalysisRun.start_time.desc())

db.Index('idx_model_performance_model_date', ModelPerformanceComparison.model_name, ModelPerformanceComparison.comparison_date)
db.Index('idx_model_performance_overall_score', ModelPerformanceComparison.overall_score.desc())


# A/B Testing Models for Automated Prompt Optimization
class ABTest(db.Model):
    """A/B test model for automated prompt optimization."""
    
    __tablename__ = 'ab_tests'
    
    id = db.Column(db.Integer, primary_key=True)
    test_id = db.Column(db.String(100), nullable=False, unique=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    
    # Test Configuration
    test_type = db.Column(db.String(50), default='prompt_optimization')  # prompt_optimization, model_comparison, etc.
    traffic_split = db.Column(db.JSON, nullable=False)  # {variant_id: percentage}
    hypothesis = db.Column(db.Text)  # What we're testing
    success_metrics = db.Column(db.JSON)  # [latency, cost, accuracy, etc.]
    
    # Test Parameters
    min_sample_size = db.Column(db.Integer, default=100)
    confidence_level = db.Column(db.Numeric(3, 2), default=0.95)  # 95% confidence
    statistical_power = db.Column(db.Numeric(3, 2), default=0.80)  # 80% power
    max_duration_hours = db.Column(db.Integer, default=168)  # 1 week default
    
    # Test State
    status = db.Column(db.String(20), default='draft')  # draft, running, paused, completed, cancelled
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    actual_duration_hours = db.Column(db.Numeric(8, 2))
    
    # Results
    winning_variant_id = db.Column(db.String(100))
    statistical_significance = db.Column(db.Numeric(5, 4))  # p-value
    confidence_interval = db.Column(db.JSON)  # confidence intervals for metrics
    results_summary = db.Column(db.JSON)  # detailed results
    
    # Automation
    auto_conclude = db.Column(db.Boolean, default=True)  # Auto-conclude when significant
    auto_implement = db.Column(db.Boolean, default=False)  # Auto-implement winner
    early_stopping_enabled = db.Column(db.Boolean, default=True)
    
    # Creator and Context
    creator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    context_data = db.Column(db.JSON)  # Additional context
    tags = db.Column(db.JSON)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    variants = db.relationship('ABTestVariant', backref='ab_test', lazy='dynamic', cascade='all, delete-orphan')
    results = db.relationship('ABTestResult', backref='ab_test', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ABTest {self.name} - {self.status}>'


class ABTestVariant(db.Model):
    """A/B test variant model for different prompt/model configurations."""
    
    __tablename__ = 'ab_test_variants'
    
    id = db.Column(db.Integer, primary_key=True)
    variant_id = db.Column(db.String(100), nullable=False, unique=True)
    ab_test_id = db.Column(db.Integer, db.ForeignKey('ab_tests.id'), nullable=False)
    
    # Variant Configuration
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    variant_type = db.Column(db.String(50), default='prompt')  # prompt, model, parameters
    is_control = db.Column(db.Boolean, default=False)
    
    # Content Configuration
    prompt_content = db.Column(db.Text)  # For prompt variants
    model_config = db.Column(db.JSON)  # For model variants
    parameters = db.Column(db.JSON)  # Additional parameters
    
    # Performance Tracking
    requests_served = db.Column(db.Integer, default=0)
    success_count = db.Column(db.Integer, default=0)
    error_count = db.Column(db.Integer, default=0)
    total_latency_ms = db.Column(db.Numeric(15, 2), default=0.0)
    total_cost_usd = db.Column(db.Numeric(10, 6), default=0.0)
    
    # Computed Metrics (updated periodically)
    avg_latency_ms = db.Column(db.Numeric(10, 2), default=0.0)
    avg_cost_usd = db.Column(db.Numeric(10, 6), default=0.0)
    success_rate = db.Column(db.Numeric(5, 4), default=0.0)
    confidence_intervals = db.Column(db.JSON)  # CI for each metric
    
    # Traffic Assignment
    traffic_percentage = db.Column(db.Numeric(5, 2), default=50.0)
    current_load = db.Column(db.Numeric(5, 2), default=0.0)
    
    # Metadata
    generation_method = db.Column(db.String(50))  # manual, ml_generated, template_based
    generation_context = db.Column(db.JSON)  # Context used for generation
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ABTestVariant {self.name} - {self.success_rate}>'


class ABTestResult(db.Model):
    """Individual A/B test result entries for detailed tracking."""
    
    __tablename__ = 'ab_test_results'
    
    id = db.Column(db.Integer, primary_key=True)
    ab_test_id = db.Column(db.Integer, db.ForeignKey('ab_tests.id'), nullable=False)
    variant_id = db.Column(db.String(100), nullable=False)
    
    # Request Details
    request_id = db.Column(db.String(100), unique=True, nullable=False)
    user_session = db.Column(db.String(100))  # For user-based analysis
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Performance Metrics
    latency_ms = db.Column(db.Numeric(10, 2))
    cost_usd = db.Column(db.Numeric(10, 6))
    success = db.Column(db.Boolean, nullable=False)
    error_message = db.Column(db.Text)
    
    # Input/Output Tracking
    input_text_hash = db.Column(db.String(64))  # Hash for privacy
    output_text_hash = db.Column(db.String(64))
    input_tokens = db.Column(db.Integer)
    output_tokens = db.Column(db.Integer)
    
    # Quality Metrics (if available)
    quality_score = db.Column(db.Numeric(5, 2))
    user_satisfaction = db.Column(db.Integer)  # 1-5 rating
    task_completion = db.Column(db.Boolean)
    
    # Context
    request_context = db.Column(db.JSON)  # Additional request context
    model_used = db.Column(db.String(100))
    
    # Data Source Integration
    external_trace_id = db.Column(db.String(100))  # Link to external traces
    data_source_id = db.Column(db.Integer, db.ForeignKey('data_sources.id'))
    
    def __repr__(self):
        return f'<ABTestResult {self.request_id} - {self.variant_id}>'


class ABTestAnalysis(db.Model):
    """A/B test analysis results and statistical calculations."""
    
    __tablename__ = 'ab_test_analysis'
    
    id = db.Column(db.Integer, primary_key=True)
    ab_test_id = db.Column(db.Integer, db.ForeignKey('ab_tests.id'), nullable=False)
    analysis_date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Sample Size Analysis
    current_sample_size = db.Column(db.Integer, default=0)
    required_sample_size = db.Column(db.Integer)
    sample_size_adequate = db.Column(db.Boolean, default=False)
    
    # Statistical Analysis
    statistical_significance = db.Column(db.Numeric(8, 6))  # p-value
    effect_size = db.Column(db.Numeric(8, 6))  # Cohen's d or similar
    confidence_level = db.Column(db.Numeric(3, 2), default=0.95)
    statistical_power = db.Column(db.Numeric(3, 2))
    
    # Variant Comparisons
    variant_comparisons = db.Column(db.JSON)  # Detailed variant vs variant comparisons
    metric_improvements = db.Column(db.JSON)  # % improvement for each metric
    confidence_intervals = db.Column(db.JSON)  # CI for improvements
    
    # Test Quality Metrics
    balance_check = db.Column(db.JSON)  # Traffic balance analysis
    novelty_effect = db.Column(db.Numeric(5, 4))  # Detected novelty bias
    contamination_risk = db.Column(db.Numeric(5, 4))  # Cross-contamination risk
    
    # Recommendations
    recommendation = db.Column(db.String(50))  # continue, stop_winner, stop_no_effect, extend
    recommendation_confidence = db.Column(db.Numeric(3, 2))
    recommended_actions = db.Column(db.JSON)
    
    # Analysis Context
    analysis_method = db.Column(db.String(50), default='frequentist')  # frequentist, bayesian
    analysis_parameters = db.Column(db.JSON)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<ABTestAnalysis {self.ab_test_id} - {self.statistical_significance}>'


# A/B Testing Indexes
db.Index('idx_ab_tests_status', ABTest.status, ABTest.start_time)
db.Index('idx_ab_tests_creator', ABTest.creator_id, ABTest.created_at)
db.Index('idx_ab_tests_duration', ABTest.start_time, ABTest.end_time)

db.Index('idx_ab_test_variants_test', ABTestVariant.ab_test_id, ABTestVariant.is_control)
db.Index('idx_ab_test_variants_performance', ABTestVariant.success_rate.desc(), ABTestVariant.avg_latency_ms)

db.Index('idx_ab_test_results_test_variant', ABTestResult.ab_test_id, ABTestResult.variant_id, ABTestResult.timestamp)
db.Index('idx_ab_test_results_success', ABTestResult.success, ABTestResult.timestamp)
db.Index('idx_ab_test_results_external', ABTestResult.external_trace_id)

db.Index('idx_ab_test_analysis_test', ABTestAnalysis.ab_test_id, ABTestAnalysis.analysis_date.desc())
db.Index('idx_ab_test_analysis_significance', ABTestAnalysis.statistical_significance, ABTestAnalysis.recommendation)


# Cross-Tenant Learning Models for Privacy-Preserving Optimization Insights
class CrossTenantPattern(db.Model):
    """Cross-tenant optimization pattern storage with privacy preservation."""
    
    __tablename__ = 'cross_tenant_patterns'
    
    id = db.Column(db.Integer, primary_key=True)
    pattern_id = db.Column(db.String(100), nullable=False, unique=True)
    
    # Pattern characteristics
    pattern_type = db.Column(db.String(50), nullable=False)  # 'performance_improvement', 'cost_reduction', etc.
    pattern_signature = db.Column(db.String(500), nullable=False)  # Anonymized signature
    pattern_description = db.Column(db.Text)
    
    # Success metrics (anonymized aggregates)
    success_count = db.Column(db.Integer, default=0)
    failure_count = db.Column(db.Integer, default=0)
    success_rate = db.Column(db.Numeric(5, 4), default=0.0)
    confidence_score = db.Column(db.Numeric(5, 4), default=0.0)
    
    # Performance metrics (anonymized)
    avg_improvement_percent = db.Column(db.Numeric(8, 2), default=0.0)
    median_improvement_percent = db.Column(db.Numeric(8, 2), default=0.0)
    std_improvement = db.Column(db.Numeric(8, 2), default=0.0)
    
    # Context information (anonymized)
    applicable_categories = db.Column(db.JSON)  # List of applicable categories
    model_types = db.Column(db.JSON)  # List of model types where pattern works
    complexity_ranges = db.Column(db.JSON)  # List of complexity ranges
    
    # Learning metadata
    first_observed = db.Column(db.DateTime, default=datetime.utcnow)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    tenant_count = db.Column(db.Integer, default=0)  # Number of tenants contributing
    total_applications = db.Column(db.Integer, default=0)  # Total times applied
    
    # Privacy compliance
    anonymization_level = db.Column(db.String(20), default='high')
    min_tenant_threshold_met = db.Column(db.Boolean, default=False)
    privacy_audit_hash = db.Column(db.String(64))  # Hash for audit verification
    
    def __repr__(self):
        return f'<CrossTenantPattern {self.pattern_type} - {self.success_rate:.2%}>'


class TenantOptimizationSummary(db.Model):
    """Anonymized tenant optimization summary for cross-tenant learning."""
    
    __tablename__ = 'tenant_optimization_summaries'
    
    id = db.Column(db.Integer, primary_key=True)
    tenant_hash = db.Column(db.String(64), nullable=False, unique=True)  # Anonymized tenant ID
    
    # Anonymized tenant characteristics
    category_focus = db.Column(db.JSON)  # General categories, not specific content
    optimization_patterns = db.Column(db.JSON)  # Pattern signatures only
    
    # Performance tier and maturity
    performance_tier = db.Column(db.String(20))  # 'high', 'medium', 'low'
    optimization_maturity = db.Column(db.String(20))  # 'advanced', 'intermediate', 'beginner'
    
    # Anonymized metrics
    success_metrics = db.Column(db.JSON)  # Anonymized aggregate metrics
    improvement_trends = db.Column(db.JSON)  # Anonymized trends
    
    # Temporal patterns
    active_months = db.Column(db.Integer, default=0)
    optimization_frequency = db.Column(db.Numeric(8, 2), default=0.0)  # Tests per month
    pattern_diversity_score = db.Column(db.Numeric(5, 4), default=0.0)
    
    # Privacy and audit
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    privacy_consent_verified = db.Column(db.Boolean, default=False)
    audit_trail_hash = db.Column(db.String(64))
    
    def __repr__(self):
        return f'<TenantOptimizationSummary {self.tenant_hash[:8]}... - {self.performance_tier}>'


class CrossTenantRecommendation(db.Model):
    """Cross-tenant learning-based recommendations."""
    
    __tablename__ = 'cross_tenant_recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    recommendation_id = db.Column(db.String(100), nullable=False, unique=True)
    
    # Recommendation details
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    
    # Evidence from cross-tenant learning
    supporting_evidence = db.Column(db.JSON)  # Anonymized supporting data
    confidence_level = db.Column(db.String(20))  # 'high', 'medium', 'low'
    expected_improvement = db.Column(db.JSON)  # Expected improvement metrics
    
    # Pattern-based insights
    similar_tenant_count = db.Column(db.Integer, default=0)
    pattern_success_rate = db.Column(db.Numeric(5, 4), default=0.0)
    adaptation_guidance = db.Column(db.Text)
    
    # Implementation details
    implementation_complexity = db.Column(db.String(20))  # 'high', 'medium', 'low'
    estimated_effort = db.Column(db.String(50))
    prerequisites = db.Column(db.JSON)  # List of prerequisites
    risks = db.Column(db.JSON)  # List of identified risks
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    # Privacy compliance
    privacy_compliant = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<CrossTenantRecommendation {self.title} - {self.confidence_level}>'


class LearningInsight(db.Model):
    """Cross-tenant learning insights."""
    
    __tablename__ = 'learning_insights'
    
    id = db.Column(db.Integer, primary_key=True)
    insight_id = db.Column(db.String(100), nullable=False, unique=True)
    
    # Insight details
    insight_type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    confidence = db.Column(db.Numeric(5, 4), default=0.0)
    impact_level = db.Column(db.String(20))  # 'high', 'medium', 'low'
    
    # Supporting data (anonymized)
    supporting_data = db.Column(db.JSON)
    recommendation_ids = db.Column(db.JSON)  # List of related recommendation IDs
    applicable_tenant_types = db.Column(db.JSON)  # List of applicable tenant types
    
    # Metadata
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    view_count = db.Column(db.Integer, default=0)
    
    # Privacy and audit
    privacy_level = db.Column(db.String(20), default='high')
    audit_hash = db.Column(db.String(64))
    
    def __repr__(self):
        return f'<LearningInsight {self.insight_type} - {self.confidence:.2f}>'


class CrossTenantAuditLog(db.Model):
    """Audit log for cross-tenant learning activities."""
    
    __tablename__ = 'cross_tenant_audit_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    audit_id = db.Column(db.String(100), nullable=False, unique=True)
    
    # Audit event details
    event_type = db.Column(db.String(50), nullable=False)  # 'pattern_created', 'recommendation_generated', etc.
    event_description = db.Column(db.Text)
    
    # Privacy compliance verification
    privacy_checks_passed = db.Column(db.Boolean, default=False)
    anonymization_verified = db.Column(db.Boolean, default=False)
    consent_verified = db.Column(db.Boolean, default=False)
    min_threshold_met = db.Column(db.Boolean, default=False)
    
    # Data involved (hashed references only)
    tenant_hashes_involved = db.Column(db.JSON)  # List of anonymized tenant hashes
    pattern_ids_involved = db.Column(db.JSON)  # List of pattern IDs
    data_types_processed = db.Column(db.JSON)  # Types of data processed
    
    # Audit metadata
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    auditor_hash = db.Column(db.String(64))  # System or user hash
    compliance_score = db.Column(db.Numeric(5, 4), default=1.0)
    
    # Verification signatures
    privacy_signature = db.Column(db.String(128))  # Cryptographic signature for privacy compliance
    integrity_hash = db.Column(db.String(64))  # Data integrity hash
    
    def __repr__(self):
        return f'<CrossTenantAuditLog {self.event_type} - {self.timestamp}>'


# Cross-Tenant Learning Indexes for Performance
db.Index('idx_cross_tenant_patterns_type', CrossTenantPattern.pattern_type, CrossTenantPattern.confidence_score.desc())
db.Index('idx_cross_tenant_patterns_success', CrossTenantPattern.success_rate.desc(), CrossTenantPattern.tenant_count.desc())
db.Index('idx_cross_tenant_patterns_updated', CrossTenantPattern.last_updated.desc())
db.Index('idx_cross_tenant_patterns_threshold', CrossTenantPattern.min_tenant_threshold_met, CrossTenantPattern.pattern_type)

db.Index('idx_tenant_summaries_hash', TenantOptimizationSummary.tenant_hash)
db.Index('idx_tenant_summaries_performance', TenantOptimizationSummary.performance_tier, TenantOptimizationSummary.optimization_maturity)
db.Index('idx_tenant_summaries_updated', TenantOptimizationSummary.last_updated.desc())

db.Index('idx_cross_tenant_recs_confidence', CrossTenantRecommendation.confidence_level, CrossTenantRecommendation.created_at.desc())
db.Index('idx_cross_tenant_recs_category', CrossTenantRecommendation.category, CrossTenantRecommendation.is_active)
db.Index('idx_cross_tenant_recs_active', CrossTenantRecommendation.is_active, CrossTenantRecommendation.expires_at)

db.Index('idx_learning_insights_type', LearningInsight.insight_type, LearningInsight.confidence.desc())
db.Index('idx_learning_insights_active', LearningInsight.is_active, LearningInsight.generated_at.desc())
db.Index('idx_learning_insights_impact', LearningInsight.impact_level, LearningInsight.expires_at)

db.Index('idx_cross_tenant_audit_type', CrossTenantAuditLog.event_type, CrossTenantAuditLog.timestamp.desc())
db.Index('idx_cross_tenant_audit_compliance', CrossTenantAuditLog.privacy_checks_passed, CrossTenantAuditLog.anonymization_verified)
db.Index('idx_cross_tenant_audit_timestamp', CrossTenantAuditLog.timestamp.desc())


# Import security models to ensure they're registered with the database
try:
    from app.models.security_models import (
        APIKey, APIKeyUsage, SecurityEvent, LoginAttempt, 
        SessionSecurity, RateLimitViolation, SecurityConfiguration
    )
except ImportError:
    # Security models not available - development mode
    pass 