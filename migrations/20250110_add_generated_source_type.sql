-- Migration: Add generated_source_type column to post table
-- Purpose: Identify AI-generated posts and their source (product, category, kb)
-- Date: 2025-01-10

-- Add generated_source_type column
ALTER TABLE post ADD COLUMN IF NOT EXISTS generated_source_type VARCHAR(20) 
    CHECK (generated_source_type IN ('product', 'category', 'kb'));

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_post_generated_source_type 
    ON post(generated_source_type) 
    WHERE generated_source_type IS NOT NULL;

-- Add comment
COMMENT ON COLUMN post.generated_source_type IS 
    'Source type for AI-generated posts: product, category, or kb (knowledge base)';

