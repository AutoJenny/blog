-- Add fields to newsletter_source_item for suitability scoring and deduplication
-- Phase 8.1: Source Item Extensions

ALTER TABLE newsletter_source_item
ADD COLUMN IF NOT EXISTS suitability_score NUMERIC(3,1),
ADD COLUMN IF NOT EXISTS suitability_notes TEXT,
ADD COLUMN IF NOT EXISTS source_url_hash VARCHAR(64),
ADD COLUMN IF NOT EXISTS is_event BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS calendar_event_id INTEGER;

-- Add index for URL hash lookups (deduplication)
CREATE INDEX IF NOT EXISTS idx_newsletter_source_item_url_hash 
    ON newsletter_source_item(source_url_hash);

-- Add index for suitability scoring queries
CREATE INDEX IF NOT EXISTS idx_newsletter_source_item_suitability 
    ON newsletter_source_item(suitability_score) 
    WHERE suitability_score IS NOT NULL;

-- Add index for calendar_event_id lookups
CREATE INDEX IF NOT EXISTS idx_newsletter_source_item_calendar_event 
    ON newsletter_source_item(calendar_event_id) 
    WHERE calendar_event_id IS NOT NULL;

-- Phase 8.2: Calendar Events Extension
-- Add source_url and source_name fields to calendar_events for deduplication

ALTER TABLE calendar_events
ADD COLUMN IF NOT EXISTS source_url TEXT,
ADD COLUMN IF NOT EXISTS source_name VARCHAR(128),
ADD COLUMN IF NOT EXISTS imported_from VARCHAR(128);

-- Add index for source_url lookups (deduplication)
CREATE INDEX IF NOT EXISTS idx_calendar_events_source_url 
    ON calendar_events(source_url) 
    WHERE source_url IS NOT NULL;

-- Add index for source_name lookups
CREATE INDEX IF NOT EXISTS idx_calendar_events_source_name 
    ON calendar_events(source_name) 
    WHERE source_name IS NOT NULL;

-- Comment explaining the new fields
COMMENT ON COLUMN newsletter_source_item.suitability_score IS 'LLM assessment score (0-10) for content relevance';
COMMENT ON COLUMN newsletter_source_item.suitability_notes IS 'Reasoning from LLM analysis';
COMMENT ON COLUMN newsletter_source_item.source_url_hash IS 'SHA256 hash of URL for deduplication';
COMMENT ON COLUMN newsletter_source_item.is_event IS 'Flag if converted to calendar_event';
COMMENT ON COLUMN newsletter_source_item.calendar_event_id IS 'Link to calendar_events if created';
COMMENT ON COLUMN calendar_events.source_url IS 'Original source URL for deduplication';
COMMENT ON COLUMN calendar_events.source_name IS 'Source organization name';
COMMENT ON COLUMN calendar_events.imported_from IS 'Track import source (e.g., newsletter_source_item)';

