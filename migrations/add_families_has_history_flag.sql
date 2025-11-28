-- Migration: Add has_history flag to families table
-- Purpose: Mark families that have at least one history text resource
-- Date: 2025-01-XX

BEGIN;

-- Add has_history column
ALTER TABLE families 
ADD COLUMN IF NOT EXISTS has_history BOOLEAN DEFAULT FALSE;

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_families_has_history ON families(has_history);

-- Set has_history = true for families that have history text resources
UPDATE families
SET has_history = TRUE
WHERE id IN (
    SELECT DISTINCT family_id 
    FROM family_resources
    WHERE resource_type = 'text'
    AND resource_category LIKE 'history_%'
);

-- Set has_history = false for all others (explicit, though DEFAULT is already FALSE)
UPDATE families
SET has_history = FALSE
WHERE id NOT IN (
    SELECT DISTINCT family_id 
    FROM family_resources
    WHERE resource_type = 'text'
    AND resource_category LIKE 'history_%'
);

-- Add comment
COMMENT ON COLUMN families.has_history IS 'TRUE if this family has at least one history text resource (history_scottish, history_legacy, history_english, history_irish, or history_welsh).';

COMMIT;

