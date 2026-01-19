-- Increase subtitle column length from 200 to 300 characters
-- This allows for expanded descriptive subtitles (2-4 sentences)

-- Note: If calendar_week_items_summary view exists and depends on subtitle,
-- you may need to recreate it. The view should automatically work with the new column size.
-- If you get an error, run: DROP VIEW IF EXISTS calendar_week_items_summary CASCADE;
-- Then recreate it from create_calendar_week_items_views.sql

ALTER TABLE post 
ALTER COLUMN subtitle TYPE VARCHAR(300);
