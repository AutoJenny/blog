-- Add multiple sources field to calendar_ideas table
-- Sources will be stored as JSONB array of objects with: title, url, author, date, notes

ALTER TABLE calendar_ideas 
ADD COLUMN IF NOT EXISTS sources JSONB DEFAULT '[]'::jsonb;

-- Add index for efficient source queries
CREATE INDEX IF NOT EXISTS idx_calendar_ideas_sources ON calendar_ideas USING GIN (sources);

-- Example structure for sources:
-- [
--   {
--     "title": "Celtic History Documentation",
--     "url": "https://example.com/celtic-history",
--     "author": "John Smith",
--     "date": "2024-01-15",
--     "notes": "Primary source for Samhain traditions"
--   },
--   {
--     "title": "Academic Paper on Halloween Origins",
--     "url": null,
--     "author": "Dr. Jane Doe",
--     "date": "2023-11-01",
--     "notes": "Historical analysis"
--   }
-- ]

