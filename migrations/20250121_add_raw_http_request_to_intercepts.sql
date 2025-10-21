-- Migration: Add raw_http_request field to llm_message_intercepts table
-- Date: 2025-01-21
-- Purpose: Store the exact raw HTTP request that gets sent to the LLM

-- Add the raw_http_request field to store the exact HTTP request
ALTER TABLE llm_message_intercepts ADD COLUMN IF NOT EXISTS raw_http_request TEXT;

-- Add index for better performance when querying by raw_http_request
CREATE INDEX IF NOT EXISTS idx_llm_message_intercepts_raw_http_request ON llm_message_intercepts(raw_http_request);

-- Add comment to document the field
COMMENT ON COLUMN llm_message_intercepts.raw_http_request IS 'The exact raw HTTP request that was sent to the LLM, including method, URL, headers, and body';
