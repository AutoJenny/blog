-- Add item_classification field to calendar_ideas to distinguish:
-- 'theme' - Selected or unselected theme ideas (week-wide concepts)
-- 'idea' - Regular ideas (specific content ideas, not themes)
-- Default to 'idea' for existing records

ALTER TABLE calendar_ideas ADD COLUMN IF NOT EXISTS item_classification VARCHAR(20) DEFAULT 'idea' CHECK (item_classification IN ('theme', 'idea'));

-- Create index for efficient filtering
CREATE INDEX IF NOT EXISTS idx_calendar_ideas_classification ON calendar_ideas(item_classification);

-- Update existing ideas that are marked as selected in calendar_schedule to be themes
UPDATE calendar_ideas ci
SET item_classification = 'theme'
WHERE EXISTS (
    SELECT 1 FROM calendar_schedule cs
    WHERE cs.idea_id = ci.id
    AND cs.status IN ('planned', 'in_progress', 'published')
);

