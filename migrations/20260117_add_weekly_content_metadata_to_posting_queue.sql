-- Migration: Add weekly content metadata columns to posting_queue
-- Date: 2026-01-17
-- Purpose: Store generation metadata for weekly word/phrase/insult social posts
--          including generated captions, image paths, and Ollama generation details
-- Notes:
--   - This migration is strictly additive and backwards compatible
--   - All new columns are nullable to support existing rows
--   - Indexes added for efficient querying by generation metadata

BEGIN;

-- Add columns for caption generation metadata
ALTER TABLE posting_queue
ADD COLUMN IF NOT EXISTS generated_caption TEXT,
ADD COLUMN IF NOT EXISTS pinned_comment TEXT,
ADD COLUMN IF NOT EXISTS chosen_prompt_style_id INTEGER,
ADD COLUMN IF NOT EXISTS image_path TEXT,
ADD COLUMN IF NOT EXISTS ollama_model VARCHAR(100),
ADD COLUMN IF NOT EXISTS generation_timestamp TIMESTAMPTZ;

-- Add index for querying by generation timestamp
CREATE INDEX IF NOT EXISTS idx_posting_queue_generation_timestamp 
ON posting_queue(generation_timestamp) 
WHERE generation_timestamp IS NOT NULL;

-- Add index for querying by prompt style (for analytics)
CREATE INDEX IF NOT EXISTS idx_posting_queue_prompt_style_id 
ON posting_queue(chosen_prompt_style_id) 
WHERE chosen_prompt_style_id IS NOT NULL;

-- Add comments for documentation
COMMENT ON COLUMN posting_queue.generated_caption IS 'AI-generated caption text for weekly content posts';
COMMENT ON COLUMN posting_queue.pinned_comment IS 'Optional pinned comment for social media post';
COMMENT ON COLUMN posting_queue.chosen_prompt_style_id IS 'ID of the prompt variation used for caption generation';
COMMENT ON COLUMN posting_queue.image_path IS 'File system path to generated square image (1080x1080)';
COMMENT ON COLUMN posting_queue.ollama_model IS 'Ollama model used for caption generation (e.g., llama3.2:latest)';
COMMENT ON COLUMN posting_queue.generation_timestamp IS 'Timestamp when caption/image were generated';

COMMIT;
