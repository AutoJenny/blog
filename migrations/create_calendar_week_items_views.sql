-- Migration: Create compatibility views for calendar_week_items
-- Purpose: Provide backward-compatible views for existing code during migration
-- Date: 2025-01-26
-- Phase: 1 - Foundation (Non-Breaking)

BEGIN;

-- View for theme selection (replaces calendar_week_selection queries)
CREATE OR REPLACE VIEW calendar_week_selection_v2 AS
SELECT 
    year,
    week_number,
    item_id as selected_theme_id,
    scheduled_at as updated_at,
    created_at
FROM calendar_week_items
WHERE item_type = 'theme' AND is_selected = TRUE;

COMMENT ON VIEW calendar_week_selection_v2 IS 'Compatibility view for calendar_week_selection. Shows selected themes from calendar_week_items.';

-- View for posts (replaces calendar_week_posts queries)
CREATE OR REPLACE VIEW calendar_week_posts_v2 AS
SELECT 
    id,
    year,
    week_number,
    item_id as post_id,
    weekday,
    scheduled_date,
    created_at,
    updated_at,
    metadata
FROM calendar_week_items
WHERE item_type IN ('recipe', 'profile');

COMMENT ON VIEW calendar_week_posts_v2 IS 'Compatibility view for calendar_week_posts. Shows recipe and profile posts from calendar_week_items.';

-- View for all scheduled items (for unified queries)
CREATE OR REPLACE VIEW calendar_week_items_summary AS
SELECT 
    cwi.id,
    cwi.item_type,
    cwi.item_id,
    cwi.year,
    cwi.week_number,
    cwi.weekday,
    cwi.scheduled_date,
    cwi.is_selected,
    cwi.priority,
    cwi.position,
    cwi.is_active,
    cwi.metadata,
    cwi.created_at,
    cwi.updated_at,
    -- Join with source tables for additional data
    CASE 
        WHEN cwi.item_type = 'theme' THEN ct.theme_title
        WHEN cwi.item_type IN ('idea', 'weekly_word', 'weekly_phrase') THEN ci.idea_title
        WHEN cwi.item_type IN ('annual_event', 'special_event') THEN ce.event_title
        WHEN cwi.item_type = 'recipe' THEN p.title
        WHEN cwi.item_type = 'profile' THEN p.title
        ELSE NULL
    END as title,
    CASE 
        WHEN cwi.item_type = 'theme' THEN ct.theme_description
        WHEN cwi.item_type IN ('idea', 'weekly_word', 'weekly_phrase') THEN ci.idea_description
        WHEN cwi.item_type IN ('annual_event', 'special_event') THEN ce.event_description
        WHEN cwi.item_type IN ('recipe', 'profile') THEN p.subtitle
        ELSE NULL
    END as description
FROM calendar_week_items cwi
LEFT JOIN calendar_themes ct ON cwi.item_type = 'theme' AND cwi.item_id = ct.id
LEFT JOIN calendar_ideas ci ON cwi.item_type IN ('idea', 'weekly_word', 'weekly_phrase') AND cwi.item_id = ci.id
LEFT JOIN calendar_events ce ON cwi.item_type IN ('annual_event', 'special_event') AND cwi.item_id = ce.id
LEFT JOIN post p ON cwi.item_type IN ('recipe', 'profile') AND cwi.item_id = p.id
WHERE cwi.is_active = TRUE;

COMMENT ON VIEW calendar_week_items_summary IS 'Summary view of all calendar week items with joined source table data for display purposes.';

COMMIT;

