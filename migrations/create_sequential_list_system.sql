-- Migration: Create Sequential List System for Calendar Items
-- Purpose: Implement position-based sequential lists with cycling for themes, recipes, profiles, words, phrases
-- Date: 2025-12-01
-- 
-- This migration:
-- 1. Creates cycle configuration table
-- 2. Adds position fields to source tables
-- 3. Creates profile sequence table
-- 4. Initializes positions from existing data

BEGIN;

-- ============================================================================
-- 1. Create Cycle Configuration Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS calendar_category_cycles (
    category VARCHAR(50) PRIMARY KEY CHECK (category IN (
        'theme', 'recipe', 'profile_product', 'profile_category', 'profile_surname',
        'weekly_word', 'weekly_phrase'
    )),
    cycle_start_week INTEGER NOT NULL DEFAULT 1 CHECK (cycle_start_week >= 1 AND cycle_start_week <= 52),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Initialize with default cycle_start_week = 1 for all categories
INSERT INTO calendar_category_cycles (category) VALUES 
    ('theme'), ('recipe'), ('profile_product'), ('profile_category'), ('profile_surname'),
    ('weekly_word'), ('weekly_phrase')
ON CONFLICT (category) DO NOTHING;

COMMENT ON TABLE calendar_category_cycles IS 'Configuration for sequential list cycling. Each category has an independent cycle start point.';
COMMENT ON COLUMN calendar_category_cycles.category IS 'Category name: theme, recipe, profile_product, profile_category, weekly_word, weekly_phrase';
COMMENT ON COLUMN calendar_category_cycles.cycle_start_week IS 'Week number (1-52) where position 1 starts. Default is 1.';

-- ============================================================================
-- 2. Add Position Field to calendar_themes
-- ============================================================================
ALTER TABLE calendar_themes ADD COLUMN IF NOT EXISTS position INTEGER;

-- Initialize positions: assign sequential positions 1, 2, 3... based on week_number (or id if week_number is NULL)
-- This ensures unique positions even if week_number has duplicates
DO $$
DECLARE
    theme_rec RECORD;
    new_pos INTEGER := 1;
BEGIN
    -- First, assign positions based on week_number (ordering by id for ties)
    FOR theme_rec IN 
        SELECT id, week_number FROM calendar_themes 
        WHERE position IS NULL 
        ORDER BY COALESCE(week_number, 999), id
    LOOP
        UPDATE calendar_themes SET position = new_pos WHERE id = theme_rec.id;
        new_pos := new_pos + 1;
    END LOOP;
END $$;

-- Create unique index on position
CREATE UNIQUE INDEX IF NOT EXISTS idx_themes_position 
    ON calendar_themes(position) 
    WHERE position IS NOT NULL;

COMMENT ON COLUMN calendar_themes.position IS 'Sequential position in themes list (1, 2, 3, ...). Used for cycling through weeks.';

-- ============================================================================
-- 3. Add Position Field to calendar_recipes
-- ============================================================================
ALTER TABLE calendar_recipes ADD COLUMN IF NOT EXISTS position INTEGER;

-- Initialize positions: use existing week_number (should be 1-52)
UPDATE calendar_recipes 
SET position = week_number 
WHERE position IS NULL AND week_number IS NOT NULL;

-- Ensure all recipes have positions (should already be 1-52)
DO $$
DECLARE
    recipe_rec RECORD;
    new_pos INTEGER := 1;
BEGIN
    FOR recipe_rec IN 
        SELECT id FROM calendar_recipes WHERE position IS NULL ORDER BY id
    LOOP
        UPDATE calendar_recipes SET position = new_pos WHERE id = recipe_rec.id;
        new_pos := new_pos + 1;
    END LOOP;
END $$;

-- Create unique index on position
CREATE UNIQUE INDEX IF NOT EXISTS idx_recipes_position 
    ON calendar_recipes(position) 
    WHERE position IS NOT NULL;

COMMENT ON COLUMN calendar_recipes.position IS 'Sequential position in recipes list (1, 2, 3, ...). Used for cycling through weeks.';

-- ============================================================================
-- 4. Create Profile Sequence Table
-- ============================================================================
CREATE TABLE IF NOT EXISTS calendar_profile_sequence (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL REFERENCES post(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    profile_type VARCHAR(20) NOT NULL CHECK (profile_type IN ('product', 'category', 'surname')),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(position, profile_type)
);

CREATE INDEX IF NOT EXISTS idx_profile_sequence_post_id ON calendar_profile_sequence(post_id);
CREATE INDEX IF NOT EXISTS idx_profile_sequence_position ON calendar_profile_sequence(position);
CREATE INDEX IF NOT EXISTS idx_profile_sequence_type ON calendar_profile_sequence(profile_type);

COMMENT ON TABLE calendar_profile_sequence IS 'Sequential ordering for profile posts. Separate sequences for product and category profiles.';
COMMENT ON COLUMN calendar_profile_sequence.position IS 'Sequential position in profile list (1, 2, 3, ...). Used for cycling through weeks.';
COMMENT ON COLUMN calendar_profile_sequence.profile_type IS 'Type of profile: product or category. Each type has its own independent sequence.';

-- Populate from existing calendar_week_items if available
-- This is a best-effort migration - may need manual adjustment
INSERT INTO calendar_profile_sequence (post_id, position, profile_type)
SELECT DISTINCT
    cwi.item_id as post_id,
    ROW_NUMBER() OVER (PARTITION BY 
        (SELECT profile_type FROM post WHERE id = cwi.item_id) 
        ORDER BY cwi.year, cwi.week_number, cwi.item_id
    ) as position,
    COALESCE(p.profile_type, 'product') as profile_type
FROM calendar_week_items cwi
LEFT JOIN post p ON cwi.item_id = p.id
WHERE cwi.item_type = 'profile' 
    AND cwi.is_active = TRUE
    AND p.profile_type IS NOT NULL
    AND NOT EXISTS (
        SELECT 1 FROM calendar_profile_sequence cps 
        WHERE cps.post_id = cwi.item_id
    )
ON CONFLICT (position, profile_type) DO NOTHING;

-- ============================================================================
-- 5. Add Position Field to calendar_ideas (for words/phrases)
-- ============================================================================
ALTER TABLE calendar_ideas ADD COLUMN IF NOT EXISTS position INTEGER;

-- Initialize positions for weekly_word: use existing week_number
UPDATE calendar_ideas 
SET position = week_number 
WHERE position IS NULL 
    AND item_classification = 'weekly_word' 
    AND week_number IS NOT NULL;

-- Initialize positions for weekly_phrase: use existing week_number
UPDATE calendar_ideas 
SET position = week_number 
WHERE position IS NULL 
    AND item_classification = 'weekly_phrase' 
    AND week_number IS NOT NULL;

-- Create unique indexes on position per classification
CREATE UNIQUE INDEX IF NOT EXISTS idx_ideas_position_word 
    ON calendar_ideas(position) 
    WHERE item_classification = 'weekly_word' AND position IS NOT NULL;

CREATE UNIQUE INDEX IF NOT EXISTS idx_ideas_position_phrase 
    ON calendar_ideas(position) 
    WHERE item_classification = 'weekly_phrase' AND position IS NOT NULL;

COMMENT ON COLUMN calendar_ideas.position IS 'Sequential position in words/phrases list (1, 2, 3, ...). Used for cycling through weeks. Separate sequences for weekly_word and weekly_phrase.';

-- ============================================================================
-- 6. Create Helper Functions
-- ============================================================================

-- Function to get item count for a category
CREATE OR REPLACE FUNCTION get_category_item_count(category_name VARCHAR(50))
RETURNS INTEGER AS $$
DECLARE
    item_count INTEGER;
BEGIN
    CASE category_name
        WHEN 'theme' THEN
            SELECT COUNT(*) INTO item_count FROM calendar_themes WHERE position IS NOT NULL;
        WHEN 'recipe' THEN
            SELECT COUNT(*) INTO item_count FROM calendar_recipes WHERE position IS NOT NULL;
        WHEN 'profile_product' THEN
            SELECT COUNT(*) INTO item_count FROM calendar_profile_sequence WHERE profile_type = 'product';
        WHEN 'profile_category' THEN
            SELECT COUNT(*) INTO item_count FROM calendar_profile_sequence WHERE profile_type = 'category';
        WHEN 'weekly_word' THEN
            SELECT COUNT(*) INTO item_count FROM calendar_ideas 
                WHERE item_classification = 'weekly_word' AND position IS NOT NULL;
        WHEN 'weekly_phrase' THEN
            SELECT COUNT(*) INTO item_count FROM calendar_ideas 
                WHERE item_classification = 'weekly_phrase' AND position IS NOT NULL;
        ELSE
            item_count := 0;
    END CASE;
    
    RETURN item_count;
END;
$$ LANGUAGE plpgsql;

COMMENT ON FUNCTION get_category_item_count IS 'Returns the total number of items in a category''s sequential list.';

COMMIT;

