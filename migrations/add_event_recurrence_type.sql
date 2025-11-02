-- Add event_recurrence_type column to newsletter_source_item
-- Values: 'annual' (annually recurring) or 'one_off' (one-time special occasion)

ALTER TABLE newsletter_source_item
ADD COLUMN IF NOT EXISTS event_recurrence_type VARCHAR(20);

-- Add index for filtering
CREATE INDEX IF NOT EXISTS idx_event_recurrence_type ON newsletter_source_item(event_recurrence_type)
WHERE category = 'event' AND event_recurrence_type IS NOT NULL;

