-- Live Data Integration Schema Migration
-- Version: 001
-- Created: 2025-08-09

-- Performance Metrics Aggregation Table
CREATE TABLE IF NOT EXISTS performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    period_start DATETIME NOT NULL,
    period_end DATETIME NOT NULL,
    period_type VARCHAR(20) NOT NULL, -- 'hour', 'day', 'week'
    
    -- Core Metrics
    total_traces INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2) DEFAULT 0.0,
    error_rate DECIMAL(5,2) DEFAULT 0.0,
    
    -- Latency Metrics
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
    
    -- Model Breakdown (JSON)
    model_distribution JSON,
    
    -- Meta
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    data_source VARCHAR(50) DEFAULT 'firestore' -- 'firestore', 'langwatch', 'webhook'
);

-- Sync Status Tracking
CREATE TABLE IF NOT EXISTS sync_status (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sync_type VARCHAR(50) NOT NULL, -- 'firestore', 'langwatch'
    last_sync_timestamp DATETIME NOT NULL,
    last_successful_sync DATETIME,
    sync_status VARCHAR(20) DEFAULT 'pending', -- 'success', 'error', 'pending', 'running'
    records_processed INTEGER DEFAULT 0,
    error_message TEXT,
    sync_metadata JSON, -- Additional sync details
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Webhook Events Log
CREATE TABLE IF NOT EXISTS webhook_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id VARCHAR(100) UNIQUE,
    event_type VARCHAR(50) NOT NULL, -- 'trace.created', 'trace.updated', etc.
    source VARCHAR(50) NOT NULL, -- 'langwatch', 'langfuse'
    payload JSON NOT NULL,
    processed BOOLEAN DEFAULT FALSE,
    processing_error TEXT,
    received_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    processed_at DATETIME
);

-- Live Trace Cache (for real-time updates)
CREATE TABLE IF NOT EXISTS live_traces (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    external_trace_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(200) NOT NULL,
    status VARCHAR(20) NOT NULL,
    model VARCHAR(100),
    
    -- Timing
    start_time DATETIME NOT NULL,
    end_time DATETIME,
    duration_ms INTEGER,
    
    -- Input/Output
    input_text TEXT,
    output_text TEXT,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    
    -- Cost
    cost_usd DECIMAL(10,6) DEFAULT 0.0,
    
    -- Metadata
    user_id VARCHAR(100),
    session_id VARCHAR(100),
    tags JSON,
    metadata JSON,
    
    -- Source tracking
    data_source VARCHAR(50) DEFAULT 'firestore',
    source_updated_at DATETIME,
    
    -- Local tracking
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Firestore specific
    firestore_doc_id VARCHAR(200),
    firestore_collection VARCHAR(100)
);

-- Real-time Alerts Configuration
CREATE TABLE IF NOT EXISTS alert_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(100) NOT NULL,
    alert_type VARCHAR(50) NOT NULL, -- 'error_rate', 'latency_spike', 'cost_threshold'
    
    -- Thresholds
    threshold_value DECIMAL(10,4) NOT NULL,
    comparison_operator VARCHAR(10) DEFAULT '>', -- '>', '<', '>=', '<=', '='
    time_window_minutes INTEGER DEFAULT 5,
    
    -- Configuration
    is_active BOOLEAN DEFAULT TRUE,
    notification_channels JSON, -- ['email', 'slack', 'webhook']
    severity VARCHAR(20) DEFAULT 'medium', -- 'low', 'medium', 'high', 'critical'
    
    -- State
    last_triggered DATETIME,
    trigger_count INTEGER DEFAULT 0,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Alert Events Log
CREATE TABLE IF NOT EXISTS alert_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rule_id INTEGER NOT NULL,
    triggered_at DATETIME NOT NULL,
    resolved_at DATETIME,
    status VARCHAR(20) DEFAULT 'active', -- 'active', 'resolved', 'acknowledged'
    
    -- Alert data
    trigger_value DECIMAL(10,4),
    message TEXT,
    severity VARCHAR(20),
    
    -- Notification tracking
    notifications_sent JSON,
    acknowledgment_user_id INTEGER,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (rule_id) REFERENCES alert_rules (id),
    FOREIGN KEY (acknowledgment_user_id) REFERENCES users (id)
);

-- Enhanced Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_performance_metrics_period ON performance_metrics(period_start, period_end, period_type);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_source ON performance_metrics(data_source, created_at);

CREATE INDEX IF NOT EXISTS idx_sync_status_type ON sync_status(sync_type, sync_status);
CREATE INDEX IF NOT EXISTS idx_sync_status_timestamp ON sync_status(last_sync_timestamp);

CREATE INDEX IF NOT EXISTS idx_webhook_events_processed ON webhook_events(processed, received_at);
CREATE INDEX IF NOT EXISTS idx_webhook_events_source ON webhook_events(source, event_type);

CREATE INDEX IF NOT EXISTS idx_live_traces_external_id ON live_traces(external_trace_id);
CREATE INDEX IF NOT EXISTS idx_live_traces_start_time ON live_traces(start_time DESC);
CREATE INDEX IF NOT EXISTS idx_live_traces_status ON live_traces(status, start_time);
CREATE INDEX IF NOT EXISTS idx_live_traces_source ON live_traces(data_source, updated_at);

CREATE INDEX IF NOT EXISTS idx_alert_rules_active ON alert_rules(is_active, alert_type);
CREATE INDEX IF NOT EXISTS idx_alert_events_rule ON alert_events(rule_id, triggered_at);
CREATE INDEX IF NOT EXISTS idx_alert_events_status ON alert_events(status, triggered_at);

-- Triggers for automatic timestamp updates
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

CREATE TRIGGER IF NOT EXISTS update_live_traces_timestamp 
    AFTER UPDATE ON live_traces
    BEGIN
        UPDATE live_traces SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

-- Insert initial sync status records
INSERT OR IGNORE INTO sync_status (sync_type, last_sync_timestamp, sync_status) 
VALUES 
    ('firestore', '2025-01-01 00:00:00', 'pending'),
    ('langwatch', '2025-01-01 00:00:00', 'pending');

-- Insert default alert rules
INSERT OR IGNORE INTO alert_rules (name, alert_type, threshold_value, comparison_operator, time_window_minutes, notification_channels)
VALUES 
    ('High Error Rate', 'error_rate', 5.0, '>', 5, '["email"]'),
    ('Latency Spike', 'latency_spike', 5000.0, '>', 10, '["email"]'),
    ('Cost Threshold', 'cost_threshold', 10.0, '>', 60, '["email"]');