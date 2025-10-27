-- Migration: Allow NULL section_id in llm_message_intercepts table
-- This enables post-level LLM operations (like SEO meta generation) that don't have a section_id

-- Drop the unique constraint that includes section_id
ALTER TABLE llm_message_intercepts 
DROP CONSTRAINT llm_message_intercepts_post_id_section_id_key;

-- Drop the index
DROP INDEX IF EXISTS idx_llm_message_intercepts_post_section;

-- Make section_id nullable
ALTER TABLE llm_message_intercepts
ALTER COLUMN section_id DROP NOT NULL;

-- Recreate index with NULL handling
CREATE INDEX idx_llm_message_intercepts_post_section ON llm_message_intercepts(post_id, section_id);

-- Create a unique constraint that allows NULL section_id
-- Note: PostgreSQL doesn't support NULLS DISTINCT in CREATE UNIQUE CONSTRAINT
-- We'll create a partial unique index for non-NULL section_ids instead
CREATE UNIQUE INDEX llm_message_intercepts_post_id_section_id_uniq 
ON llm_message_intercepts(post_id, section_id) 
WHERE section_id IS NOT NULL;

-- For NULL section_ids, we want only one record per post_id
CREATE UNIQUE INDEX llm_message_intercepts_post_id_null_section_uniq 
ON llm_message_intercepts(post_id) 
WHERE section_id IS NULL;

