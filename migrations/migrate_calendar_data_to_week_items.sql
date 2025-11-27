-- Migration: Migrate existing calendar data to calendar_week_items
-- Purpose: Populate the unified calendar_week_items table with existing data
-- Date: 2025-01-26
-- Phase: 3 - Data Migration

BEGIN;

-- 1. Migrate Themes from calendar_week_selection (if table exists)
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'calendar_week_selection') THEN
        INSERT INTO calendar_week_items (
            item_type, item_id, year, week_number, is_selected, is_active, 
            scheduled_at, created_at, updated_at
        )
        SELECT 
            'theme' as item_type,
            selected_theme_id as item_id,
            year,
            week_number,
            TRUE as is_selected,
            TRUE as is_active,
            updated_at as scheduled_at,
            updated_at as created_at,
            updated_at
        FROM calendar_week_selection
        ON CONFLICT (year, week_number, item_type, item_id) DO NOTHING;
    END IF;
END $$;

-- 2. Migrate Recipes from calendar_week_posts (if table exists)
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'calendar_week_posts') THEN
        INSERT INTO calendar_week_items (
            item_type, item_id, year, week_number, weekday, scheduled_date,
            is_active, metadata, created_at, updated_at
        )
        SELECT 
            'recipe' as item_type,
            cwp.post_id as item_id,
            cwp.year,
            cwp.week_number,
            cwp.weekday,
            cwp.scheduled_date,
            TRUE as is_active,
            jsonb_build_object(
                'recipe_definition_id', p.recipe_id,
                'recipe_week_number', p.recipe_week_number
            ) as metadata,
            cwp.created_at,
            cwp.updated_at
        FROM calendar_week_posts cwp
        JOIN post p ON cwp.post_id = p.id
        WHERE p.post_type = 'recipe'
        ON CONFLICT (year, week_number, item_type, item_id) DO NOTHING;
    END IF;
END $$;

-- 3. Migrate Profiles from calendar_week_posts (if table exists)
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'calendar_week_posts') THEN
        INSERT INTO calendar_week_items (
            item_type, item_id, year, week_number, weekday, scheduled_date,
            is_active, metadata, created_at, updated_at
        )
        SELECT 
            'profile' as item_type,
            cwp.post_id as item_id,
            cwp.year,
            cwp.week_number,
            cwp.weekday,
            cwp.scheduled_date,
            TRUE as is_active,
            jsonb_build_object(
                'profile_type', p.profile_type,
                'profile_product_id', p.profile_product_id,
                'profile_category_id', p.profile_category_id
            ) as metadata,
            cwp.created_at,
            cwp.updated_at
        FROM calendar_week_posts cwp
        JOIN post p ON cwp.post_id = p.id
        WHERE p.profile_type IS NOT NULL
        ON CONFLICT (year, week_number, item_type, item_id) DO NOTHING;
    END IF;
END $$;

-- 4. Migrate Ideas from calendar_ideas (for current year, if table exists)
DO $$
DECLARE
    current_year INTEGER;
    idea_record RECORD;
    item_classification_value VARCHAR(50);
    item_type_value VARCHAR(50);
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'calendar_ideas') THEN
        current_year := EXTRACT(YEAR FROM CURRENT_DATE);
        
        FOR idea_record IN 
            SELECT id, week_number, item_classification
            FROM calendar_ideas
            WHERE item_classification IN ('idea', 'weekly_word', 'weekly_phrase')
        LOOP
            -- Determine item_type from item_classification
            item_classification_value := idea_record.item_classification;
            IF item_classification_value = 'weekly_word' THEN
                item_type_value := 'weekly_word';
            ELSIF item_classification_value = 'weekly_phrase' THEN
                item_type_value := 'weekly_phrase';
            ELSE
                item_type_value := 'idea';
            END IF;
            
            -- Insert into calendar_week_items
            INSERT INTO calendar_week_items (
                item_type, item_id, year, week_number, is_active, created_at, updated_at
            ) VALUES (
                item_type_value,
                idea_record.id,
                current_year,
                idea_record.week_number,
                TRUE,
                NOW(),
                NOW()
            )
            ON CONFLICT (year, week_number, item_type, item_id) DO NOTHING;
        END LOOP;
    END IF;
END $$;

-- 5. Migrate Events from calendar_events (if table exists)
DO $$
BEGIN
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'calendar_events') THEN
        INSERT INTO calendar_week_items (
            item_type, item_id, year, week_number, weekday, scheduled_date,
            is_active, metadata, created_at, updated_at
        )
        SELECT 
            CASE 
                WHEN is_recurring = TRUE THEN 'annual_event'
                ELSE 'special_event'
            END as item_type,
            id as item_id,
            year,
            week_number,
            CASE 
                WHEN start_date IS NOT NULL THEN EXTRACT(DOW FROM start_date)::INTEGER + 1
                ELSE NULL
            END as weekday,
            start_date as scheduled_date,
            TRUE as is_active,
            jsonb_build_object(
                'is_recurring', is_recurring,
                'start_date', start_date::text,
                'end_date', end_date::text,
                'advance_notice', advance_notice
            ) as metadata,
            created_at,
            updated_at
        FROM calendar_events
        WHERE year IS NOT NULL AND week_number IS NOT NULL
        ON CONFLICT (year, week_number, item_type, item_id) DO NOTHING;
    END IF;
END $$;

COMMIT;
