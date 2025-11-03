-- Week Persistence Architecture V2 Migration
-- Creates new tables for clean week persistence

BEGIN;

-- 1. Calendar Week Selection (one selected theme per week)
CREATE TABLE IF NOT EXISTS calendar_week_selection (
    year INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    selected_theme_id INTEGER NOT NULL REFERENCES calendar_themes(id) ON DELETE RESTRICT,
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (year, week_number),
    UNIQUE(year, week_number)
);

CREATE INDEX IF NOT EXISTS idx_calendar_week_selection_theme 
    ON calendar_week_selection(selected_theme_id);

COMMENT ON TABLE calendar_week_selection IS 'Stores the selected theme for each week. One theme must be selected per week.';
COMMENT ON COLUMN calendar_week_selection.year IS 'Year for the week';
COMMENT ON COLUMN calendar_week_selection.week_number IS 'Week number (1-52)';
COMMENT ON COLUMN calendar_week_selection.selected_theme_id IS 'ID of the selected theme for this week (required)';

-- 2. Calendar Week Posts (multiple posts per week allowed)
CREATE TABLE IF NOT EXISTS calendar_week_posts (
    id SERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    post_id INTEGER NOT NULL REFERENCES post(id) ON DELETE CASCADE,
    scheduled_date DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(year, week_number, post_id)
);

CREATE INDEX IF NOT EXISTS idx_calendar_week_posts_year_week 
    ON calendar_week_posts(year, week_number);
CREATE INDEX IF NOT EXISTS idx_calendar_week_posts_post_id 
    ON calendar_week_posts(post_id);

COMMENT ON TABLE calendar_week_posts IS 'Stores post assignments to weeks. Multiple posts can be assigned to the same week.';
COMMENT ON COLUMN calendar_week_posts.year IS 'Year for the week';
COMMENT ON COLUMN calendar_week_posts.week_number IS 'Week number (1-52)';
COMMENT ON COLUMN calendar_week_posts.post_id IS 'ID of the post assigned to this week';
COMMENT ON COLUMN calendar_week_posts.scheduled_date IS 'Optional specific date for post publication';

COMMIT;

