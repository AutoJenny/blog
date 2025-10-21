-- Migration: Add complete_api_request field to llm_message_intercepts table
-- Date: 2025-01-21
-- Purpose: Store the complete API request data that gets sent to the LLM

-- Add the complete_api_request field to store the full API request
ALTER TABLE llm_message_intercepts ADD COLUMN IF NOT EXISTS complete_api_request TEXT;

-- Add index for better performance when querying by complete_api_request
CREATE INDEX IF NOT EXISTS idx_llm_message_intercepts_complete_api_request ON llm_message_intercepts(complete_api_request);

-- Add comment to document the field
COMMENT ON COLUMN llm_message_intercepts.complete_api_request IS 'The complete API request data including URL, headers, and payload that was sent to the LLM';
