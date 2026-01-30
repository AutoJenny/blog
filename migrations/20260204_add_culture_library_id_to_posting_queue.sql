-- Migration: Add culture_library_id column to posting_queue
-- Date: 2026-02-04
-- Purpose: CULTURE v1.1 — FK linkage for Mon/Thu culture_fact posts (90-day repeat avoidance, reporting).
-- Notes:
--   - Nullable; existing and language posts have culture_library_id = NULL.
--   - ON DELETE SET NULL so deleting a library row does not break queue rows.

BEGIN;

-- =====================================================
-- 1. ADD culture_library_id COLUMN
-- =====================================================
ALTER TABLE posting_queue
ADD COLUMN IF NOT EXISTS culture_library_id INTEGER REFERENCES culture_library(id) ON DELETE SET NULL;

-- =====================================================
-- 2. CREATE INDEX
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_posting_queue_culture_library_id
ON posting_queue(culture_library_id) WHERE culture_library_id IS NOT NULL;

-- =====================================================
-- 3. ADD COMMENT
-- =====================================================
COMMENT ON COLUMN posting_queue.culture_library_id IS 'Optional reference to culture_library for CULTURE Mon/Thu posts. Used for 90-day repeat avoidance. NULL for language and other posts.';

COMMIT;
