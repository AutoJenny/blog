-- Migration: Add raw_messages field to llm_message_intercepts table
-- Date: 2025-01-21
-- Purpose: Store the exact text that gets sent to the LLM

-- Add the raw_messages field to store the complete LLM input
ALTER TABLE llm_message_intercepts ADD COLUMN IF NOT EXISTS raw_messages TEXT;

-- Add index for better performance when querying by raw_messages
CREATE INDEX IF NOT EXISTS idx_llm_message_intercepts_raw_messages ON llm_message_intercepts(raw_messages);

-- Add comment to document the field
COMMENT ON COLUMN llm_message_intercepts.raw_messages IS 'The exact text that was sent to the LLM, including system and user messages';