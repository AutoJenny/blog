-- Migration: Add heritage_library_id column to posting_queue
-- Date: 2026-01-29
-- Purpose: Phase H1 — HERITAGE (Thursday) slot; FK linkage for heritage_fact posts (90-day repeat avoidance).
-- Notes:
--   - Nullable; existing and other posts have heritage_library_id = NULL.
--   - ON DELETE SET NULL so deleting a library row does not break queue rows.
--   - heritage_library table must exist (migrations/20260129_create_heritage_library.sql).

BEGIN;

-- 1. ADD heritage_library_id COLUMN
ALTER TABLE posting_queue
ADD COLUMN IF NOT EXISTS heritage_library_id INTEGER REFERENCES heritage_library(id) ON DELETE SET NULL;

-- 2. CREATE INDEX
CREATE INDEX IF NOT EXISTS idx_posting_queue_heritage_library_id
ON posting_queue(heritage_library_id) WHERE heritage_library_id IS NOT NULL;

-- 3. ADD COMMENT
COMMENT ON COLUMN posting_queue.heritage_library_id IS 'Optional reference to heritage_library for HERITAGE Thursday posts. Used for 90-day repeat avoidance. NULL for other posts.';

COMMIT;
