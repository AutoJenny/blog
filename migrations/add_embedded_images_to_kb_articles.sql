-- Migration: Add embedded_images field to clan_kb_articles
-- Purpose: Store extracted image URLs from article HTML content
-- Date: 2025-11-11

BEGIN;

-- Add embedded_images column (JSONB array of image URLs)
ALTER TABLE clan_kb_articles
ADD COLUMN IF NOT EXISTS embedded_images JSONB DEFAULT '[]'::jsonb;

-- Create GIN index for efficient querying
CREATE INDEX IF NOT EXISTS idx_clan_kb_articles_embedded_images 
ON clan_kb_articles USING GIN(embedded_images);

-- Add comment
COMMENT ON COLUMN clan_kb_articles.embedded_images IS 'Array of image URLs extracted from article HTML content (img tags)';

COMMIT;

