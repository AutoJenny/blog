-- Migration: Add heritage data columns to clan_categories
-- Purpose: Store historical and cultural context for Category Profiles
-- Date: 2025-01-XX

BEGIN;

-- Add heritage data columns
ALTER TABLE clan_categories
ADD COLUMN IF NOT EXISTS heritage_data JSONB,
ADD COLUMN IF NOT EXISTS web_researched_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS llm_analyzed_at TIMESTAMP;

-- Create GIN index for efficient JSONB queries
CREATE INDEX IF NOT EXISTS idx_clan_categories_heritage_data ON clan_categories USING GIN (heritage_data);

-- Add comments
COMMENT ON COLUMN clan_categories.heritage_data IS 'JSONB object storing historical/cultural context: {historical_origins: string, cultural_significance: string, hierarchy_context: string, llm_analysis: object, web_research: object}';
COMMENT ON COLUMN clan_categories.web_researched_at IS 'Timestamp when web research was last performed for this category';
COMMENT ON COLUMN clan_categories.llm_analyzed_at IS 'Timestamp when LLM analysis was last performed for this category';

COMMIT;

