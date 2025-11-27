-- Migration: Create calendar_week_items table
-- Purpose: Unified table for all calendar content types (themes, ideas, events, recipes, profiles, words, phrases, syndication)
-- Date: 2025-01-26
-- Phase: 1 - Foundation (Non-Breaking)

BEGIN;

-- Create the unified calendar_week_items table
CREATE TABLE IF NOT EXISTS calendar_week_items (
    id SERIAL PRIMARY KEY,
    
    -- Unified identification
    item_type VARCHAR(50) NOT NULL CHECK (item_type IN (
        'theme', 'idea', 'annual_event', 'special_event', 
        'recipe', 'profile', 'weekly_word', 'weekly_phrase', 'syndication'
    )),
    item_id INTEGER NOT NULL,  -- References source table (themes.id, ideas.id, post.id, etc.)
    
    -- Week association
    year INTEGER NOT NULL,
    week_number INTEGER NOT NULL CHECK (week_number >= 1 AND week_number <= 52),
    
    -- Day-level scheduling (NULL for week-level items like themes)
    weekday INTEGER CHECK (weekday >= 1 AND weekday <= 7),  -- 1=Monday, 7=Sunday
    scheduled_date DATE,  -- Optional specific date
    
    -- Scheduling metadata
    scheduled_at TIMESTAMPTZ DEFAULT NOW(),
    scheduled_by INTEGER,  -- Optional user tracking (references users.id if users table exists)
    position INTEGER DEFAULT 0,  -- For ordering within same day/type
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Selection/priority flags
    is_selected BOOLEAN DEFAULT FALSE,  -- For themes (one selected per week)
    priority VARCHAR(20) DEFAULT 'normal' CHECK (priority IN ('normal', 'mandatory', 'random')),
    
    -- Metadata
    metadata JSONB DEFAULT '{}',  -- Type-specific data (e.g., syndication platform, recipe definition ID)
    notes TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(year, week_number, item_type, item_id),  -- Prevent duplicates
    CONSTRAINT valid_weekday CHECK (
        (item_type IN ('theme', 'weekly_word', 'weekly_phrase') AND weekday IS NULL) OR  -- Week-level items
        (item_type NOT IN ('theme', 'weekly_word', 'weekly_phrase') AND (weekday IS NULL OR (weekday >= 1 AND weekday <= 7)))
    ),
    CONSTRAINT valid_theme_selection CHECK (
        (item_type = 'theme' AND is_selected = TRUE) OR  -- Themes must be selected if present
        (item_type != 'theme')
    )
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_calendar_week_items_type_id 
    ON calendar_week_items(item_type, item_id);

CREATE INDEX IF NOT EXISTS idx_calendar_week_items_week 
    ON calendar_week_items(year, week_number);

CREATE INDEX IF NOT EXISTS idx_calendar_week_items_type_week 
    ON calendar_week_items(item_type, year, week_number);

CREATE INDEX IF NOT EXISTS idx_calendar_week_items_selected 
    ON calendar_week_items(year, week_number, is_selected) 
    WHERE is_selected = TRUE;

CREATE INDEX IF NOT EXISTS idx_calendar_week_items_active 
    ON calendar_week_items(is_active) 
    WHERE is_active = TRUE;

CREATE INDEX IF NOT EXISTS idx_calendar_week_items_weekday 
    ON calendar_week_items(weekday) 
    WHERE weekday IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_calendar_week_items_scheduled_date 
    ON calendar_week_items(scheduled_date) 
    WHERE scheduled_date IS NOT NULL;

-- GIN index for metadata JSONB queries
CREATE INDEX IF NOT EXISTS idx_calendar_week_items_metadata 
    ON calendar_week_items USING GIN (metadata);

-- Add table comments
COMMENT ON TABLE calendar_week_items IS 'Unified table for all calendar content types. Provides consistent identification and scheduling for themes, ideas, events, recipes, profiles, words, phrases, and syndication.';
COMMENT ON COLUMN calendar_week_items.item_type IS 'Type of calendar item: theme, idea, annual_event, special_event, recipe, profile, weekly_word, weekly_phrase, syndication';
COMMENT ON COLUMN calendar_week_items.item_id IS 'ID of the item in its source table (calendar_themes.id, calendar_ideas.id, post.id, etc.)';
COMMENT ON COLUMN calendar_week_items.year IS 'Year for the week (e.g., 2025)';
COMMENT ON COLUMN calendar_week_items.week_number IS 'ISO week number (1-52)';
COMMENT ON COLUMN calendar_week_items.weekday IS 'Day of week (1=Monday, 7=Sunday). NULL for week-level items like themes.';
COMMENT ON COLUMN calendar_week_items.scheduled_date IS 'Optional specific date for scheduling (overrides weekday calculation)';
COMMENT ON COLUMN calendar_week_items.is_selected IS 'For themes: indicates this is the selected theme for the week';
COMMENT ON COLUMN calendar_week_items.metadata IS 'JSONB field storing type-specific data (recipe_definition_id, profile_type, syndication platform, etc.)';
COMMENT ON COLUMN calendar_week_items.position IS 'Ordering position for items scheduled on the same day/type';

COMMIT;

