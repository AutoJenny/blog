-- Add important_notes JSONB field to calendar_ideas and calendar_events
-- Stores an array of note objects: [{"id": "uuid", "text": "note text", "created_at": "timestamp"}]

ALTER TABLE calendar_ideas 
ADD COLUMN IF NOT EXISTS important_notes JSONB DEFAULT '[]'::jsonb;

ALTER TABLE calendar_events 
ADD COLUMN IF NOT EXISTS important_notes JSONB DEFAULT '[]'::jsonb;

-- Add comments for documentation
COMMENT ON COLUMN calendar_ideas.important_notes IS 'Array of important notes: [{"id": "uuid", "text": "note text", "created_at": "timestamp"}]';
COMMENT ON COLUMN calendar_events.important_notes IS 'Array of important notes: [{"id": "uuid", "text": "note text", "created_at": "timestamp"}]';

-- Create GIN indexes for efficient JSONB queries
CREATE INDEX IF NOT EXISTS idx_calendar_ideas_important_notes 
ON calendar_ideas USING GIN (important_notes);

CREATE INDEX IF NOT EXISTS idx_calendar_events_important_notes 
ON calendar_events USING GIN (important_notes);

