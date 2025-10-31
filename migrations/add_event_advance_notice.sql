-- Add advance_notice field to calendar_events table
-- Stores the promotion lead time in weeks (1, 2, 4, 8, or 12 weeks)

ALTER TABLE calendar_events 
ADD COLUMN IF NOT EXISTS advance_notice INTEGER;

-- Add comment for documentation
COMMENT ON COLUMN calendar_events.advance_notice IS 'Number of weeks before event to start promotion (1, 2, 4, 8, or 12)';

-- Create index for queries filtering by advance notice
CREATE INDEX IF NOT EXISTS idx_calendar_events_advance_notice 
ON calendar_events(advance_notice);

