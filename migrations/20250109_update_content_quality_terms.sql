-- Migration: Update Content Quality Field Names
-- Date: 2025-01-09
-- Purpose: Simplify content quality field names to reflect unified LLM processing approach

-- Backup current data before making changes
CREATE TABLE post_section_backup_20250109 AS SELECT * FROM post_section;

-- Add new columns
ALTER TABLE post_section ADD COLUMN polished TEXT;
ALTER TABLE post_section ADD COLUMN draft TEXT;

-- Copy data from old fields to new fields
UPDATE post_section SET 
    polished = CASE 
        WHEN optimization IS NOT NULL AND optimization != '' THEN optimization
        WHEN generation IS NOT NULL AND generation != '' THEN generation
        WHEN uk_british IS NOT NULL AND uk_british != '' THEN uk_british
        ELSE NULL
    END,
    draft = CASE 
        WHEN first_draft IS NOT NULL AND first_draft != '' THEN first_draft
        ELSE NULL
    END;

-- Drop old columns
ALTER TABLE post_section DROP COLUMN optimization;
ALTER TABLE post_section DROP COLUMN generation;
ALTER TABLE post_section DROP COLUMN uk_british;
ALTER TABLE post_section DROP COLUMN first_draft;

-- Add comments to document the new structure
COMMENT ON COLUMN post_section.polished IS 'Final publication-ready content after unified LLM processing';
COMMENT ON COLUMN post_section.draft IS 'Initial raw draft content before processing';

-- Update any existing indexes or constraints if needed
-- (No specific indexes needed for these text fields)

-- Verify migration
SELECT 
    COUNT(*) as total_sections,
    COUNT(CASE WHEN polished IS NOT NULL AND polished != '' THEN 1 END) as sections_with_polished,
    COUNT(CASE WHEN draft IS NOT NULL AND draft != '' THEN 1 END) as sections_with_draft
FROM post_section; 