-- Migration: Add is_canonical flag to families table
-- Purpose: Mark families that are not spelling variants of another name
-- Date: 2025-01-XX

BEGIN;

-- Add is_canonical column
ALTER TABLE families 
ADD COLUMN IF NOT EXISTS is_canonical BOOLEAN DEFAULT TRUE;

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_families_is_canonical ON families(is_canonical);

-- Set is_canonical = false for families that are spelling variants
UPDATE families
SET is_canonical = FALSE
WHERE id IN (
    SELECT DISTINCT family_id 
    FROM family_spellings
);

-- Set is_canonical = true for all others (explicit, though DEFAULT is already TRUE)
UPDATE families
SET is_canonical = TRUE
WHERE id NOT IN (
    SELECT DISTINCT family_id 
    FROM family_spellings
);

-- Add comment
COMMENT ON COLUMN families.is_canonical IS 'TRUE if this family name is not a spelling variant of another name. FALSE if it is a variant.';

COMMIT;

