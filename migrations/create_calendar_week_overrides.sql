-- Migration: Create calendar_week_overrides table
-- Purpose: Simple override table for manual weekly assignments
-- Date: 2025-12-01

BEGIN;

-- Create the override table
CREATE TABLE IF NOT EXISTS calendar_week_overrides (
    id SERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    week_number INTEGER NOT NULL CHECK (week_number >= 1 AND week_number <= 52),
    category VARCHAR(50) NOT NULL CHECK (category IN (
        'theme', 'recipe', 'profile_product', 'profile_category', 'profile_surname',
        'weekly_word', 'weekly_phrase'
    )),
    item_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE (year, week_number, category)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_calendar_week_overrides_week 
    ON calendar_week_overrides(year, week_number);

CREATE INDEX IF NOT EXISTS idx_calendar_week_overrides_category 
    ON calendar_week_overrides(category);

CREATE INDEX IF NOT EXISTS idx_calendar_week_overrides_item 
    ON calendar_week_overrides(category, item_id);

-- Add comments
COMMENT ON TABLE calendar_week_overrides IS 'Manual overrides for specific weeks. Takes precedence over cycle formula.';
COMMENT ON COLUMN calendar_week_overrides.category IS 'Category: theme, recipe, profile_product, profile_surname, weekly_word, weekly_phrase';
COMMENT ON COLUMN calendar_week_overrides.item_id IS 'ID of item in source table (calendar_themes.id, calendar_recipes.id, post.id, calendar_ideas.id)';

COMMIT;

