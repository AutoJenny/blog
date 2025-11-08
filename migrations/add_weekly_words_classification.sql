-- Extend item_classification to support weekly words and phrases
-- These are distinct from regular ideas - they're weekly recurring content snippets

-- Drop the existing CHECK constraint
ALTER TABLE calendar_ideas DROP CONSTRAINT IF EXISTS calendar_ideas_item_classification_check;

-- Add new CHECK constraint with weekly_word and weekly_phrase
ALTER TABLE calendar_ideas ADD CONSTRAINT calendar_ideas_item_classification_check 
    CHECK (item_classification IN ('theme', 'idea', 'weekly_word', 'weekly_phrase'));

-- Add comment for documentation
COMMENT ON COLUMN calendar_ideas.item_classification IS 
    'Classification: theme (week-wide concepts), idea (regular content ideas), weekly_word (Scottish word of the week), weekly_phrase (Scots phrase of the week)';




