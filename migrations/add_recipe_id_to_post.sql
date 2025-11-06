-- Migration: Add recipe_id to post table (replacing recipe_week_number)
-- Purpose: Use unique recipe ID instead of week_number to prevent data integrity issues
-- Date: 2025-11-06

BEGIN;

-- Add recipe_id column pointing to calendar_recipes.id
ALTER TABLE post 
ADD COLUMN IF NOT EXISTS recipe_id INTEGER REFERENCES calendar_recipes(id) ON DELETE RESTRICT;

-- Create index for efficient queries
CREATE INDEX IF NOT EXISTS idx_post_recipe_id ON post(recipe_id) WHERE recipe_id IS NOT NULL;

-- Migrate existing data: set recipe_id based on recipe_week_number
UPDATE post p
SET recipe_id = cr.id
FROM calendar_recipes cr
WHERE p.recipe_week_number = cr.week_number
  AND p.recipe_week_number IS NOT NULL
  AND p.recipe_id IS NULL;

-- Add comment
COMMENT ON COLUMN post.recipe_id IS 'Unique recipe definition ID from calendar_recipes. This association NEVER changes, even if recipes are reordered. Use this instead of recipe_week_number for data integrity.';
COMMENT ON COLUMN post.recipe_week_number IS 'DEPRECATED: Use recipe_id instead. Kept for backward compatibility during migration.';

COMMIT;

