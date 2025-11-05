-- Migration: Create calendar_recipes table
-- Purpose: Store perpetual recipe definitions (1-52 weeks) separate from calendar_ideas
-- Date: 2025-01-XX

BEGIN;

-- Create calendar_recipes table (perpetual recipes, like calendar_themes)
CREATE TABLE IF NOT EXISTS calendar_recipes (
    id SERIAL PRIMARY KEY,
    week_number INTEGER NOT NULL CHECK (week_number >= 1 AND week_number <= 52),
    recipe_title VARCHAR(255) NOT NULL,
    recipe_description TEXT,
    seasonal_context TEXT,
    priority VARCHAR(20) DEFAULT 'mandatory' CHECK (priority IN ('random', 'mandatory')),
    tags JSONB DEFAULT '[]'::jsonb,
    is_recurring BOOLEAN DEFAULT TRUE,
    can_span_weeks BOOLEAN DEFAULT FALSE,
    max_weeks INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(week_number)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_calendar_recipes_week_number ON calendar_recipes(week_number);
CREATE INDEX IF NOT EXISTS idx_calendar_recipes_priority ON calendar_recipes(priority);

-- Add comments
COMMENT ON TABLE calendar_recipes IS 'Stores perpetual recipe definitions (1-52 weeks) that recur every year. Completely separate from calendar_ideas.';
COMMENT ON COLUMN calendar_recipes.week_number IS 'Perpetual week number (1-52) - this recipe appears in this week every year';
COMMENT ON COLUMN calendar_recipes.recipe_title IS 'Name of the Scottish recipe';
COMMENT ON COLUMN calendar_recipes.seasonal_context IS 'Seasonal or thematic context for this recipe';
COMMENT ON COLUMN calendar_recipes.priority IS 'random or mandatory - recipes are typically mandatory';

COMMIT;

