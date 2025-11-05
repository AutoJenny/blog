-- Migration: Add recipe_week_number field to post table
-- Purpose: Support Scottish Recipe Series with perpetual week assignment (1-52)
-- Date: 2025-01-XX

BEGIN;

-- Add recipe week number column (1-52 for perpetual week assignment)
ALTER TABLE post 
ADD COLUMN IF NOT EXISTS recipe_week_number INTEGER CHECK (recipe_week_number >= 1 AND recipe_week_number <= 52);

-- Create index for efficient queries
CREATE INDEX IF NOT EXISTS idx_post_recipe_week ON post(recipe_week_number) WHERE recipe_week_number IS NOT NULL;

-- Add comment
COMMENT ON COLUMN post.recipe_week_number IS 'Perpetual week number (1-52) for Scottish Recipe Series. NULL for non-recipe posts.';

COMMIT;

