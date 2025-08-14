-- Live Data Integration Complete Schema
-- Version: 001_enhanced
-- Created: 2025-08-09
-- Enhanced with data_sources and cache_entries tables per requirements

-- Live Traces Table (individual trace data from LangWatch/Firestore)
CREATE TABLE IF NOT EXISTS live_traces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    external_trace_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    status VARCHAR(20) NOT NULL CHECK (status IN ('success', 'error', 'pending', 'running')),
    model VARCHAR(100),
    
    -- Timing Information
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    duration_ms INTEGER,
    
    -- Input/Output Data
    input_text TEXT,
    output_text TEXT,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    
    -- Cost Information
    cost_usd DECIMAL(10,6) DEFAULT 0.0,
    
    -- User and Session Data
    user_id VARCHAR(100),
    session_id VARCHAR(100),
    tags JSON,
    trace_metadata JSON,
    
    -- Source Tracking
    data_source_id INTEGER,
    source_updated_at DATETIME,
    
    -- Local Tracking
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Firestore Specific Fields
    firestore_doc_id VARCHAR(200),
    firestore_collection VARCHAR(100),
    
    -- LangWatch Specific Fields
    langwatch_trace_id VARCHAR(100),
    langwatch_project_id VARCHAR(100),
    
    FOREIGN KEY (data_source_id) REFERENCES data_sources (id)
);

-- Performance Metrics Table (aggregated performance data for dashboard)
CREATE TABLE IF NOT EXISTS performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    period_start DATETIME NOT NULL,
    period_end DATETIME NOT NULL,
    period_type VARCHAR(20) NOT NULL CHECK (period_type IN ('hour', 'day', 'week', 'month')),
    
    -- Core Performance Metrics
    total_traces INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2) DEFAULT 0.0,
    error_rate DECIMAL(5,2) DEFAULT 0.0,
    
    -- Latency Metrics (optimized for dashboard queries)
    avg_latency_ms DECIMAL(10,2) DEFAULT 0.0,
    p50_latency_ms DECIMAL(10,2) DEFAULT 0.0,
    p95_latency_ms DECIMAL(10,2) DEFAULT 0.0,
    p99_latency_ms DECIMAL(10,2) DEFAULT 0.0,
    min_latency_ms DECIMAL(10,2) DEFAULT 0.0,
    max_latency_ms DECIMAL(10,2) DEFAULT 0.0,
    
    -- Cost Metrics
    total_cost DECIMAL(10,6) DEFAULT 0.0,
    avg_cost_per_request DECIMAL(10,6) DEFAULT 0.0,
    input_tokens_total INTEGER DEFAULT 0,
    output_tokens_total INTEGER DEFAULT 0,
    
    -- Model Distribution (JSON for flexibility)
    model_distribution JSON,
    operation_distribution JSON,
    
    -- Source Information
    data_source_id INTEGER,
    
    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (data_source_id) REFERENCES data_sources (id)
);

-- Sync Status Table (track sync state and health)
CREATE TABLE IF NOT EXISTS sync_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_source_id INTEGER NOT NULL,
    sync_type VARCHAR(50) NOT NULL,
    last_sync_timestamp DATETIME NOT NULL,
    last_successful_sync DATETIME,
    sync_status VARCHAR(20) DEFAULT 'pending' CHECK (sync_status IN ('success', 'error', 'pending', 'running')),
    records_processed INTEGER DEFAULT 0,
    records_failed INTEGER DEFAULT 0,
    error_message TEXT,
    sync_metadata JSON,
    next_sync_due DATETIME,
    sync_interval_minutes INTEGER DEFAULT 60,
    
    -- Health Metrics
    consecutive_failures INTEGER DEFAULT 0,
    last_error_timestamp DATETIME,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (data_source_id) REFERENCES data_sources (id),
    UNIQUE(data_source_id, sync_type)
);

-- Webhook Events Table (store incoming webhook data)
CREATE TABLE IF NOT EXISTS webhook_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    trace_id VARCHAR(100) NOT NULL,
    event_type VARCHAR(50) NOT NULL,
    source VARCHAR(50) NOT NULL,
    data_source_id INTEGER,
    
    -- Event Data
    event_data JSON NOT NULL,
    
    -- Processing Status
    status VARCHAR(20) DEFAULT 'pending' CHECK (status IN ('success', 'error', 'pending', 'processing')),
    error_message TEXT,
    
    -- Timestamps
    received_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    processed_at DATETIME,
    
    FOREIGN KEY (data_source_id) REFERENCES data_sources (id)
);

-- Data Sources Table (configuration for different data sources)
CREATE TABLE IF NOT EXISTS data_sources (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL UNIQUE,
    source_type VARCHAR(50) NOT NULL CHECK (source_type IN ('firestore', 'langwatch', 'langfuse', 'webhook')),
    
    -- Connection Configuration
    connection_config JSON NOT NULL,
    auth_config JSON,
    
    -- Sync Configuration
    sync_enabled BOOLEAN DEFAULT TRUE,
    sync_interval_minutes INTEGER DEFAULT 60,
    last_sync_timestamp DATETIME,
    
    -- Health Status
    is_active BOOLEAN DEFAULT TRUE,
    health_status VARCHAR(20) DEFAULT 'unknown' CHECK (health_status IN ('healthy', 'degraded', 'unhealthy', 'unknown')),
    last_health_check DATETIME,
    
    -- Metadata
    description TEXT,
    tags JSON,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Cache Entries Table (local caching table for performance)
CREATE TABLE IF NOT EXISTS cache_entries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cache_key VARCHAR(255) NOT NULL UNIQUE,
    cache_value JSON NOT NULL,
    
    -- Cache Metadata
    cache_type VARCHAR(50) NOT NULL,
    data_source_id INTEGER,
    
    -- Expiration Management
    expires_at DATETIME,
    ttl_seconds INTEGER DEFAULT 3600,
    
    -- Usage Tracking
    hit_count INTEGER DEFAULT 0,
    last_accessed DATETIME,
    
    -- Data Integrity
    checksum VARCHAR(64),
    version INTEGER DEFAULT 1,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (data_source_id) REFERENCES data_sources (id)
);

-- Alert Rules Table (enhanced configuration)
CREATE TABLE IF NOT EXISTS alert_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    alert_type VARCHAR(50) NOT NULL,
    data_source_id INTEGER,
    
    -- Threshold Configuration
    threshold_value DECIMAL(10,4) NOT NULL,
    comparison_operator VARCHAR(10) DEFAULT '>' CHECK (comparison_operator IN ('>', '<', '>=', '<=', '=', '!=')),
    time_window_minutes INTEGER DEFAULT 5,
    
    -- Rule Configuration
    is_active BOOLEAN DEFAULT TRUE,
    notification_channels JSON,
    severity VARCHAR(20) DEFAULT 'medium' CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    
    -- Conditions
    condition_query TEXT,
    condition_metadata JSON,
    
    -- State Management
    last_triggered DATETIME,
    trigger_count INTEGER DEFAULT 0,
    cooldown_minutes INTEGER DEFAULT 60,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (data_source_id) REFERENCES data_sources (id)
);

-- Alert Events Table
CREATE TABLE IF NOT EXISTS alert_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_id INTEGER NOT NULL,
    triggered_at DATETIME NOT NULL,
    resolved_at DATETIME,
    status VARCHAR(20) DEFAULT 'active' CHECK (status IN ('active', 'resolved', 'acknowledged', 'suppressed')),
    
    -- Alert Data
    trigger_value DECIMAL(10,4),
    threshold_value DECIMAL(10,4),
    message TEXT,
    severity VARCHAR(20),
    context_data JSON,
    
    -- Notification Tracking
    notifications_sent JSON,
    acknowledgment_user_id INTEGER,
    acknowledgment_note TEXT,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (rule_id) REFERENCES alert_rules (id),
    FOREIGN KEY (acknowledgment_user_id) REFERENCES users (id)
);

-- Performance-Optimized Indexes
-- Live Traces Indexes
CREATE INDEX IF NOT EXISTS idx_live_traces_external_id ON live_traces(external_trace_id);
CREATE INDEX IF NOT EXISTS idx_live_traces_start_time ON live_traces(start_time DESC);
CREATE INDEX IF NOT EXISTS idx_live_traces_status_time ON live_traces(status, start_time DESC);
CREATE INDEX IF NOT EXISTS idx_live_traces_source ON live_traces(data_source_id, updated_at);
CREATE INDEX IF NOT EXISTS idx_live_traces_user ON live_traces(user_id, start_time DESC);
CREATE INDEX IF NOT EXISTS idx_live_traces_model ON live_traces(model, start_time DESC);

-- Performance Metrics Indexes
CREATE INDEX IF NOT EXISTS idx_performance_metrics_period ON performance_metrics(period_start, period_end, period_type);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_source ON performance_metrics(data_source_id, created_at);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_type_period ON performance_metrics(period_type, period_start DESC);

-- Sync Status Indexes
CREATE INDEX IF NOT EXISTS idx_sync_status_source_type ON sync_status(data_source_id, sync_type);
CREATE INDEX IF NOT EXISTS idx_sync_status_timestamp ON sync_status(last_sync_timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_sync_status_health ON sync_status(sync_status, consecutive_failures);

-- Webhook Events Indexes
CREATE INDEX IF NOT EXISTS idx_webhook_events_status ON webhook_events(status, received_at);
CREATE INDEX IF NOT EXISTS idx_webhook_events_source ON webhook_events(source, event_type);
CREATE INDEX IF NOT EXISTS idx_webhook_events_trace ON webhook_events(trace_id, event_type);

-- Data Sources Indexes
CREATE INDEX IF NOT EXISTS idx_data_sources_type ON data_sources(source_type, is_active);
CREATE INDEX IF NOT EXISTS idx_data_sources_health ON data_sources(health_status, last_health_check);

-- Cache Entries Indexes
CREATE INDEX IF NOT EXISTS idx_cache_entries_key ON cache_entries(cache_key);
CREATE INDEX IF NOT EXISTS idx_cache_entries_expires ON cache_entries(expires_at);
CREATE INDEX IF NOT EXISTS idx_cache_entries_type_source ON cache_entries(cache_type, data_source_id);
CREATE INDEX IF NOT EXISTS idx_cache_entries_accessed ON cache_entries(last_accessed DESC);

-- Alert Indexes
CREATE INDEX IF NOT EXISTS idx_alert_rules_active ON alert_rules(is_active, alert_type);
CREATE INDEX IF NOT EXISTS idx_alert_rules_source ON alert_rules(data_source_id, is_active);
CREATE INDEX IF NOT EXISTS idx_alert_events_rule ON alert_events(rule_id, triggered_at DESC);
CREATE INDEX IF NOT EXISTS idx_alert_events_status ON alert_events(status, triggered_at DESC);

-- Automatic Timestamp Update Triggers
CREATE TRIGGER IF NOT EXISTS update_live_traces_timestamp 
    AFTER UPDATE ON live_traces
    BEGIN
        UPDATE live_traces SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_performance_metrics_timestamp 
    AFTER UPDATE ON performance_metrics
    BEGIN
        UPDATE performance_metrics SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_sync_status_timestamp 
    AFTER UPDATE ON sync_status
    BEGIN
        UPDATE sync_status SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_data_sources_timestamp 
    AFTER UPDATE ON data_sources
    BEGIN
        UPDATE data_sources SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_cache_entries_timestamp 
    AFTER UPDATE ON cache_entries
    BEGIN
        UPDATE cache_entries SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_alert_rules_timestamp 
    AFTER UPDATE ON alert_rules
    BEGIN
        UPDATE alert_rules SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

-- Cache Expiration Cleanup Trigger
CREATE TRIGGER IF NOT EXISTS cleanup_expired_cache_entries
    AFTER INSERT ON cache_entries
    BEGIN
        DELETE FROM cache_entries 
        WHERE expires_at < CURRENT_TIMESTAMP 
        AND expires_at IS NOT NULL;
    END;

-- Initial Data Sources Configuration
INSERT OR IGNORE INTO data_sources (name, source_type, connection_config, description, sync_enabled) 
VALUES 
    ('Firestore Primary', 'firestore', 
     '{"project_id": "vertigo-production", "collection": "traces"}', 
     'Primary Firestore database for Vertigo traces', 
     TRUE),
    ('LangWatch Integration', 'langwatch', 
     '{"base_url": "https://langwatch.ai/api", "project_id": "vertigo"}', 
     'LangWatch observability platform integration', 
     TRUE),
    ('Langfuse Local', 'langfuse', 
     '{"base_url": "http://localhost:3000", "project": "vertigo-debug"}', 
     'Local Langfuse instance for development', 
     TRUE);

-- Initial Sync Status Records
INSERT OR IGNORE INTO sync_status (data_source_id, sync_type, last_sync_timestamp, sync_status, sync_interval_minutes) 
SELECT 
    ds.id,
    'full_sync',
    '2025-01-01 00:00:00',
    'pending',
    60
FROM data_sources ds;

-- Default Alert Rules
INSERT OR IGNORE INTO alert_rules (name, alert_type, threshold_value, comparison_operator, time_window_minutes, notification_channels, data_source_id)
SELECT 
    'High Error Rate - ' || ds.name,
    'error_rate',
    5.0,
    '>',
    5,
    '["email"]',
    ds.id
FROM data_sources ds
WHERE ds.is_active = TRUE;

INSERT OR IGNORE INTO alert_rules (name, alert_type, threshold_value, comparison_operator, time_window_minutes, notification_channels)
VALUES 
    ('Global Latency Spike', 'latency_spike', 5000.0, '>', 10, '["email", "slack"]'),
    ('Daily Cost Threshold', 'cost_threshold', 50.0, '>', 1440, '["email"]'),
    ('Cache Hit Rate Low', 'cache_hit_rate', 0.7, '<', 60, '["email"]');