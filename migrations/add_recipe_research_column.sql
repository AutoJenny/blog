-- Migration: Add recipe_research column to post_development
-- Purpose: Store recipe research data (authentic ingredients, method, sources)
-- Date: 2025-11-06

BEGIN;

-- Add recipe_research column (JSONB for structured data)
ALTER TABLE post_development 
ADD COLUMN IF NOT EXISTS recipe_research JSONB;

-- Add comment
COMMENT ON COLUMN post_development.recipe_research IS 'Structured research data for recipe posts: authentic ingredients, method, sources, regional variations, etc.';

COMMIT;

