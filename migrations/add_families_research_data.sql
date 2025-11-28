-- Migration: Add research_data JSONB column to families table
-- Purpose: Store comprehensive research framework for surname research
-- Date: 2025-01-XX

BEGIN;

-- Add research_data column as JSONB for efficient querying
ALTER TABLE families 
ADD COLUMN IF NOT EXISTS research_data JSONB;

-- Create GIN index for efficient JSON queries
CREATE INDEX IF NOT EXISTS idx_families_research_data ON families USING GIN (research_data);

-- Add comment explaining the structure
COMMENT ON COLUMN families.research_data IS 'Comprehensive research framework JSON containing: surname, primary_language_region, metadata, etymology, early_records, distribution_historic, distribution_modern, clan_association, heraldry, variants, migration, notables, cultural_notes, and genealogy_resources. See documentation for full schema.';

COMMIT;

