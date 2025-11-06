-- Migration: Add post_section_elements JSONB column to post_section table
-- Purpose: Store structured JSON data for recipe sections (ingredients, method, etc.)
-- Date: 2025-11-06

BEGIN;

-- Add post_section_elements column to post_section table
ALTER TABLE post_section 
ADD COLUMN IF NOT EXISTS post_section_elements JSONB DEFAULT '{}'::jsonb;

-- Create index for efficient JSON queries
CREATE INDEX IF NOT EXISTS idx_post_section_elements ON post_section USING GIN (post_section_elements);

-- Add comment
COMMENT ON COLUMN post_section.post_section_elements IS 'Structured JSON data for recipe sections (ingredients list, method steps, variants, etc.). Format depends on section_type.';

COMMIT;

