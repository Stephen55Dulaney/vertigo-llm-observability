-- Migration 003: LangFuse to LangWatch Platform Migration
-- Date: 2025-08-12
-- Purpose: Replace all LangFuse references with LangWatch equivalents

-- 1. Rename langfuse_prompt_id column to langwatch_prompt_id in prompts table
ALTER TABLE prompts 
ADD COLUMN langwatch_prompt_id VARCHAR(100);

-- Copy existing data from langfuse_prompt_id to langwatch_prompt_id
UPDATE prompts 
SET langwatch_prompt_id = langfuse_prompt_id 
WHERE langfuse_prompt_id IS NOT NULL;

-- Drop the old langfuse_prompt_id column (after data verification)
-- Note: Commented out for safety - can be run manually after verification
-- ALTER TABLE prompts DROP COLUMN langfuse_prompt_id;

-- 2. Update data_sources table to remove 'langfuse' source type
-- First, migrate any existing 'langfuse' entries to 'langwatch'
UPDATE data_sources 
SET source_type = 'langwatch' 
WHERE source_type = 'langfuse';

-- 3. Update any traces that might reference langfuse in metadata
-- Check if traces table has any JSON fields that might contain langfuse references
UPDATE traces 
SET metadata = json_replace(metadata, '$.source', 'langwatch') 
WHERE json_extract(metadata, '$.source') = 'langfuse'
AND metadata IS NOT NULL;

-- 4. Create index on new langwatch_prompt_id column for performance
CREATE INDEX IF NOT EXISTS idx_prompts_langwatch_id 
ON prompts (langwatch_prompt_id);

-- 5. Add constraint to ensure data_sources.source_type only accepts valid values
-- Note: SQLite doesn't support CHECK constraints in ALTER TABLE, so this is informational
-- Valid source types are now: 'firestore', 'langwatch', 'webhook'

-- 6. Log migration completion
INSERT INTO migration_log (migration_name, applied_at, description) 
VALUES (
    '003_langfuse_to_langwatch_migration', 
    datetime('now'), 
    'Migrated all LangFuse references to LangWatch'
)
ON CONFLICT DO NOTHING;

-- Create migration_log table if it doesn't exist
CREATE TABLE IF NOT EXISTS migration_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    migration_name VARCHAR(100) NOT NULL UNIQUE,
    applied_at DATETIME NOT NULL,
    description TEXT
);

-- Verification queries (run these manually to verify migration success)
-- SELECT COUNT(*) FROM prompts WHERE langwatch_prompt_id IS NOT NULL;
-- SELECT COUNT(*) FROM prompts WHERE langfuse_prompt_id IS NOT NULL;
-- SELECT DISTINCT source_type FROM data_sources;
-- SELECT * FROM migration_log WHERE migration_name = '003_langfuse_to_langwatch_migration';