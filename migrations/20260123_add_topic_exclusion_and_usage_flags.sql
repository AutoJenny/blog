-- Migration: Add exclusion and usage tracking flags to kb_topics
-- Date: 2026-01-23
-- Purpose: Allow topics to be excluded from rota and track when they've been used for content generation

-- Add is_excluded flag (excluded topics won't appear in rota generation)
ALTER TABLE kb_topics
ADD COLUMN IF NOT EXISTS is_excluded BOOLEAN DEFAULT FALSE;

-- Add is_used flag (tracks if topic has been used for content generation)
ALTER TABLE kb_topics
ADD COLUMN IF NOT EXISTS is_used BOOLEAN DEFAULT FALSE;

-- Add used_at timestamp (when topic was marked as used)
ALTER TABLE kb_topics
ADD COLUMN IF NOT EXISTS used_at TIMESTAMP;

-- Add excluded_at timestamp (when topic was excluded)
ALTER TABLE kb_topics
ADD COLUMN IF NOT EXISTS excluded_at TIMESTAMP;

-- Create indexes for efficient filtering
CREATE INDEX IF NOT EXISTS idx_kb_topics_excluded ON kb_topics(is_excluded) WHERE is_excluded = TRUE;
CREATE INDEX IF NOT EXISTS idx_kb_topics_used ON kb_topics(is_used) WHERE is_used = TRUE;
CREATE INDEX IF NOT EXISTS idx_kb_topics_active_not_excluded ON kb_topics(is_active, is_excluded) WHERE is_active = TRUE AND is_excluded = FALSE;

COMMENT ON COLUMN kb_topics.is_excluded IS 'If TRUE, topic is excluded from rota generation (user manually excluded)';
COMMENT ON COLUMN kb_topics.is_used IS 'If TRUE, topic has been used for content generation. Will not be reused until all topics have been used.';
COMMENT ON COLUMN kb_topics.used_at IS 'Timestamp when topic was marked as used for content generation';
COMMENT ON COLUMN kb_topics.excluded_at IS 'Timestamp when topic was excluded from rota';
