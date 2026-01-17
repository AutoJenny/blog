-- Migration: Add idea_id column to posting_queue for weekly content outputs
-- Date: 2025-12-18
-- Purpose: Enable ID-only linkage between posting_queue rows and
--          weekly Content Items in calendar_ideas (weekly_word/phrase/insult).
-- Notes:
--   - This migration is strictly additive and backwards compatible.
--   - Existing product and other queue rows are unaffected.

BEGIN;

-- 1) Add nullable idea_id column
ALTER TABLE posting_queue
    ADD COLUMN IF NOT EXISTS idea_id INTEGER;

-- 2) Optional index to support lookups by idea_id
CREATE INDEX IF NOT EXISTS idx_posting_queue_idea_id
    ON posting_queue(idea_id)
    WHERE idea_id IS NOT NULL;

COMMIT;


