-- Add end_date and date_qualifier columns to newsletter_source_item
-- Phase: Event Date Processing Enhancement

ALTER TABLE newsletter_source_item
ADD COLUMN IF NOT EXISTS end_date TIMESTAMPTZ NULL,
ADD COLUMN IF NOT EXISTS date_qualifier VARCHAR(32) NULL;

-- Add index for end_date filtering
CREATE INDEX IF NOT EXISTS idx_nsi_end_date 
    ON newsletter_source_item(end_date) 
    WHERE end_date IS NOT NULL;

-- Add index for date_qualifier filtering
CREATE INDEX IF NOT EXISTS idx_nsi_date_qualifier 
    ON newsletter_source_item(date_qualifier) 
    WHERE date_qualifier IS NOT NULL;

-- Comments explaining the new fields
COMMENT ON COLUMN newsletter_source_item.end_date IS 'Event end date (for date ranges or "until" dates)';
COMMENT ON COLUMN newsletter_source_item.date_qualifier IS 'Which dates are available: start_only, end_only, both, or NULL (unknown/none)';









