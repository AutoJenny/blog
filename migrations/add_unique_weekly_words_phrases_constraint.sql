-- Add unique constraint to ensure one weekly_word and one weekly_phrase per week
-- This prevents duplicate entries from being created

-- First, create a unique index on (week_number, item_classification) 
-- for weekly_word and weekly_phrase entries only
-- This will enforce one of each type per week

CREATE UNIQUE INDEX IF NOT EXISTS idx_calendar_ideas_week_classification_unique
ON calendar_ideas (week_number, item_classification)
WHERE item_classification IN ('weekly_word', 'weekly_phrase');

-- Add comment for documentation
COMMENT ON INDEX idx_calendar_ideas_week_classification_unique IS 
    'Ensures only one weekly_word and one weekly_phrase per week_number';

