-- Migration: Add 'blog' to calendar_week_items item_type and valid_weekday
-- Purpose: Allow one blog slot per week (first-class weekly slot)
-- Idempotent: drop constraints by name if they exist, then add with new definition

-- Drop existing check constraint for item_type (name from \d calendar_week_items)
ALTER TABLE calendar_week_items
  DROP CONSTRAINT IF EXISTS calendar_week_items_item_type_check1;

-- Re-add with 'blog' included
ALTER TABLE calendar_week_items
  ADD CONSTRAINT calendar_week_items_item_type_check1
  CHECK (item_type IN (
    'theme', 'idea', 'annual_event', 'special_event',
    'recipe', 'profile', 'weekly_word', 'weekly_phrase', 'syndication', 'blog'
  ));

-- valid_weekday: blog is a week-level item (weekday must be NULL)
ALTER TABLE calendar_week_items
  DROP CONSTRAINT IF EXISTS valid_weekday;

ALTER TABLE calendar_week_items
  ADD CONSTRAINT valid_weekday CHECK (
    (item_type IN ('theme', 'weekly_word', 'weekly_phrase', 'blog') AND weekday IS NULL)
    OR
    (item_type NOT IN ('theme', 'weekly_word', 'weekly_phrase', 'blog') AND (weekday IS NULL OR (weekday >= 1 AND weekday <= 7)))
  );
