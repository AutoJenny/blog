-- Migration: Add section_type column to post_section table
-- Purpose: Support recipe and profile section types (recipe_background, recipe_ingredients, etc.)
-- Date: 2025-11-06

BEGIN;

-- Add section_type column to post_section table
ALTER TABLE post_section 
ADD COLUMN IF NOT EXISTS section_type VARCHAR(100);

-- Create index for efficient queries by section type
CREATE INDEX IF NOT EXISTS idx_post_section_section_type ON post_section(section_type) WHERE section_type IS NOT NULL;

-- Add comment
COMMENT ON COLUMN post_section.section_type IS 'Section type identifier (e.g., recipe_background, recipe_ingredients, recipe_method, recipe_variants, recipe_serving, recipe_further_reading) for recipe/profile posts. NULL for themed posts.';

COMMIT;

