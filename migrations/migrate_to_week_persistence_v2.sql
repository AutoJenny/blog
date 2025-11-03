-- Week Persistence Architecture V2 - Data Migration
-- Migrates data from calendar_schedule to new tables

BEGIN;

-- Step 1: Backup calendar_schedule (if not already backed up)
CREATE TABLE IF NOT EXISTS calendar_schedule_v2_backup AS 
    SELECT * FROM calendar_schedule;

-- Step 2: Migrate theme selections to calendar_week_selection
-- Takes the most recent theme_id per (year, week_number)
-- Only migrates entries where theme_id IS NOT NULL
INSERT INTO calendar_week_selection (year, week_number, selected_theme_id, updated_at)
SELECT DISTINCT ON (year, week_number)
    year,
    week_number,
    theme_id as selected_theme_id,
    updated_at
FROM calendar_schedule
WHERE theme_id IS NOT NULL
ORDER BY year, week_number, updated_at DESC
ON CONFLICT (year, week_number) DO NOTHING;

-- Step 3: Migrate post assignments to calendar_week_posts
-- Migrates all entries where post_id IS NOT NULL
INSERT INTO calendar_week_posts (year, week_number, post_id, scheduled_date, created_at, updated_at)
SELECT DISTINCT ON (year, week_number, post_id)
    year,
    week_number,
    post_id,
    scheduled_date,
    created_at,
    updated_at
FROM calendar_schedule
WHERE post_id IS NOT NULL
ON CONFLICT (year, week_number, post_id) DO NOTHING;

-- Step 4: Validation queries (run these to verify migration)
-- Check theme selection counts
-- SELECT 
--     (SELECT COUNT(*) FROM calendar_schedule WHERE theme_id IS NOT NULL) as schedule_themes,
--     (SELECT COUNT(DISTINCT year, week_number) FROM calendar_schedule WHERE theme_id IS NOT NULL) as unique_week_themes,
--     (SELECT COUNT(*) FROM calendar_week_selection) as migrated_selections;

-- Check post assignment counts
-- SELECT 
--     (SELECT COUNT(*) FROM calendar_schedule WHERE post_id IS NOT NULL) as schedule_posts,
--     (SELECT COUNT(DISTINCT year, week_number, post_id) FROM calendar_schedule WHERE post_id IS NOT NULL) as unique_week_posts,
--     (SELECT COUNT(*) FROM calendar_week_posts) as migrated_posts;

COMMIT;

-- Note: calendar_schedule table is kept for now to allow rollback
-- After verification, it can be deprecated or removed in a future migration

