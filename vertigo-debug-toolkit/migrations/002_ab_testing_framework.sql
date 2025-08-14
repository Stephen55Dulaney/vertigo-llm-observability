-- Migration 002: A/B Testing Framework
-- Automated prompt optimization with statistical analysis
-- Created: 2025-08-11

-- A/B Tests table
CREATE TABLE IF NOT EXISTS ab_tests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    test_id VARCHAR(100) NOT NULL UNIQUE,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    
    -- Test Configuration
    test_type VARCHAR(50) DEFAULT 'prompt_optimization',  -- prompt_optimization, model_comparison, etc.
    traffic_split TEXT NOT NULL,  -- JSON: {variant_id: percentage}
    hypothesis TEXT,  -- What we're testing
    success_metrics TEXT,  -- JSON: [latency, cost, accuracy, etc.]
    
    -- Test Parameters
    min_sample_size INTEGER DEFAULT 100,
    confidence_level DECIMAL(3, 2) DEFAULT 0.95,  -- 95% confidence
    statistical_power DECIMAL(3, 2) DEFAULT 0.80,  -- 80% power
    max_duration_hours INTEGER DEFAULT 168,  -- 1 week default
    
    -- Test State
    status VARCHAR(20) DEFAULT 'draft',  -- draft, running, paused, completed, cancelled
    start_time DATETIME,
    end_time DATETIME,
    actual_duration_hours DECIMAL(8, 2),
    
    -- Results
    winning_variant_id VARCHAR(100),
    statistical_significance DECIMAL(5, 4),  -- p-value
    results_summary TEXT,  -- JSON
    
    -- Automation Settings
    auto_conclude BOOLEAN DEFAULT TRUE,
    auto_implement BOOLEAN DEFAULT FALSE,
    
    -- Audit
    creator_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (creator_id) REFERENCES users(id)
);

-- A/B Test Variants table
CREATE TABLE IF NOT EXISTS ab_test_variants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    variant_id VARCHAR(100) NOT NULL UNIQUE,
    ab_test_id INTEGER NOT NULL,
    
    -- Variant Configuration
    name VARCHAR(200) NOT NULL,
    description TEXT,
    variant_type VARCHAR(50) DEFAULT 'prompt',  -- prompt, model, parameters
    is_control BOOLEAN DEFAULT FALSE,
    traffic_percentage DECIMAL(5, 2) NOT NULL,
    
    -- Content Configuration
    prompt_content TEXT,  -- For prompt variants
    model_config TEXT,  -- JSON: For model variants
    parameters TEXT,  -- JSON: Additional parameters
    
    -- Generation Context (for AI-generated variants)
    generation_method VARCHAR(100),  -- manual, ml_enhanced, template_based, etc.
    generation_context TEXT,  -- JSON: Context about how variant was generated
    
    -- Performance Tracking
    requests_served INTEGER DEFAULT 0,
    success_count INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    total_latency_ms DECIMAL(15, 2) DEFAULT 0.0,
    total_cost_usd DECIMAL(10, 6) DEFAULT 0.0,
    
    -- Computed Metrics (updated periodically)
    avg_latency_ms DECIMAL(10, 2) DEFAULT 0.0,
    avg_cost_usd DECIMAL(10, 6) DEFAULT 0.0,
    success_rate DECIMAL(5, 4) DEFAULT 0.0,
    
    -- Audit
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (ab_test_id) REFERENCES ab_tests(id) ON DELETE CASCADE
);

-- A/B Test Results table (individual test entries)
CREATE TABLE IF NOT EXISTS ab_test_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ab_test_id INTEGER NOT NULL,
    variant_id VARCHAR(100) NOT NULL,
    
    -- Request Details
    request_id VARCHAR(100) UNIQUE NOT NULL,
    user_session VARCHAR(100),  -- For user-based analysis
    timestamp DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Performance Metrics
    latency_ms DECIMAL(10, 2),
    cost_usd DECIMAL(10, 6),
    success BOOLEAN NOT NULL,
    error_message TEXT,
    
    -- Input/Output Tracking (hashed for privacy)
    input_text_hash VARCHAR(64),  -- SHA-256 hash for privacy
    output_text_hash VARCHAR(64),
    input_tokens INTEGER,
    output_tokens INTEGER,
    
    -- Quality Metrics (if available)
    quality_score DECIMAL(5, 2),
    user_satisfaction INTEGER,  -- 1-5 rating
    task_completion BOOLEAN,
    
    -- Context
    request_context TEXT,  -- JSON: Additional context
    external_trace_id VARCHAR(100),  -- Link to Langfuse/external trace
    
    FOREIGN KEY (ab_test_id) REFERENCES ab_tests(id) ON DELETE CASCADE
);

-- A/B Test Analysis table (statistical analysis results)
CREATE TABLE IF NOT EXISTS ab_test_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ab_test_id INTEGER NOT NULL,
    analysis_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Sample Size Analysis
    current_sample_size INTEGER DEFAULT 0,
    required_sample_size INTEGER,
    sample_size_adequate BOOLEAN DEFAULT FALSE,
    
    -- Statistical Analysis
    statistical_significance DECIMAL(8, 6),  -- p-value
    effect_size DECIMAL(8, 6),  -- Cohen's d or similar
    confidence_level DECIMAL(3, 2) DEFAULT 0.95,
    statistical_power DECIMAL(3, 2),
    
    -- Variant Comparisons
    variant_comparisons TEXT,  -- JSON: Detailed variant vs variant comparisons
    metric_improvements TEXT,  -- JSON: % improvement for each metric
    confidence_intervals TEXT,  -- JSON: CI for improvements
    
    -- Test Quality Metrics
    balance_check TEXT,  -- JSON: Traffic balance analysis
    novelty_effect DECIMAL(5, 4),  -- Detected novelty bias
    contamination_risk DECIMAL(5, 4),  -- Cross-contamination risk
    
    -- Recommendations
    recommendation VARCHAR(100) NOT NULL,  -- continue, stop_winner, stop_no_effect, extend
    recommendation_confidence DECIMAL(5, 4),
    recommended_actions TEXT,  -- JSON: List of specific actions
    analysis_method VARCHAR(50) DEFAULT 'frequentist',  -- frequentist, bayesian
    
    FOREIGN KEY (ab_test_id) REFERENCES ab_tests(id) ON DELETE CASCADE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_ab_tests_status ON ab_tests(status);
CREATE INDEX IF NOT EXISTS idx_ab_tests_creator ON ab_tests(creator_id);
CREATE INDEX IF NOT EXISTS idx_ab_tests_created ON ab_tests(created_at);

CREATE INDEX IF NOT EXISTS idx_ab_test_variants_test_id ON ab_test_variants(ab_test_id);
CREATE INDEX IF NOT EXISTS idx_ab_test_variants_variant_id ON ab_test_variants(variant_id);

CREATE INDEX IF NOT EXISTS idx_ab_test_results_test_id ON ab_test_results(ab_test_id);
CREATE INDEX IF NOT EXISTS idx_ab_test_results_variant ON ab_test_results(variant_id);
CREATE INDEX IF NOT EXISTS idx_ab_test_results_timestamp ON ab_test_results(timestamp);
CREATE INDEX IF NOT EXISTS idx_ab_test_results_user_session ON ab_test_results(user_session);

CREATE INDEX IF NOT EXISTS idx_ab_test_analysis_test_id ON ab_test_analysis(ab_test_id);
CREATE INDEX IF NOT EXISTS idx_ab_test_analysis_date ON ab_test_analysis(analysis_date);

-- Migration metadata table (if it doesn't exist)
CREATE TABLE IF NOT EXISTS migration_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    migration_id VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    applied_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Migration metadata
INSERT OR IGNORE INTO migration_history (migration_id, description, applied_at) 
VALUES ('002_ab_testing_framework', 'A/B Testing Framework for automated prompt optimization', CURRENT_TIMESTAMP);