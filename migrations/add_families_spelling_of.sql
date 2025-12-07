-- Migration: Add spelling_of column and remove is_canonical flag
-- This replaces the is_canonical flag with a direct relationship to the canonical form

-- Add spelling_of column (nullable, references families.id)
ALTER TABLE families 
ADD COLUMN IF NOT EXISTS spelling_of INTEGER REFERENCES families(id);

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_families_spelling_of ON families(spelling_of);

-- Note: We're not dropping is_canonical yet to allow for a transition period
-- It can be removed in a future migration once we've verified the new system works

