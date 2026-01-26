-- Migration: Add angle_id column to posting_queue
-- Date: 2026-01-25
-- Purpose: Link generated posts to angles (optional, backward compatible)
-- Notes:
--   - Column is nullable (existing posts have angle_id = NULL)
--   - ON DELETE SET NULL (if angle deleted, posts remain valid)
--   - Backward compatible: posts can be generated without angles

BEGIN;

-- =====================================================
-- 1. ADD ANGLE_ID COLUMN
-- =====================================================
ALTER TABLE posting_queue 
ADD COLUMN IF NOT EXISTS angle_id INTEGER REFERENCES content_angles(id) ON DELETE SET NULL;

-- =====================================================
-- 2. CREATE INDEX
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_posting_queue_angle_id ON posting_queue(angle_id) WHERE angle_id IS NOT NULL;

-- =====================================================
-- 3. ADD COMMENT
-- =====================================================
COMMENT ON COLUMN posting_queue.angle_id IS 'Optional reference to content_angles. NULL for posts generated without angles (backward compatible).';

COMMIT;
