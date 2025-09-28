-- Cleanup calendar_schedule table to only contain date and post-related fields
-- Remove content-related fields that don't belong in a scheduling table

-- First, backup existing data
CREATE TABLE calendar_schedule_backup AS SELECT * FROM calendar_schedule;

-- Drop the existing table
DROP TABLE calendar_schedule CASCADE;

-- Recreate with only date and post-related fields
CREATE TABLE calendar_schedule (
    id SERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    post_id INTEGER REFERENCES post(id) ON DELETE SET NULL,
    scheduled_date DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_calendar_schedule_year_week ON calendar_schedule(year, week_number);
CREATE INDEX idx_calendar_schedule_post_id ON calendar_schedule(post_id);
CREATE INDEX idx_calendar_schedule_scheduled_date ON calendar_schedule(scheduled_date);

-- Add comment explaining the table's purpose
COMMENT ON TABLE calendar_schedule IS 'Scheduling table that links posts to specific calendar weeks and dates. Contains only date and post-related fields.';
COMMENT ON COLUMN calendar_schedule.year IS 'Year for the scheduled post';
COMMENT ON COLUMN calendar_schedule.week_number IS 'Week number (1-52) for the scheduled post';
COMMENT ON COLUMN calendar_schedule.post_id IS 'ID of the post being scheduled (NULL if not yet created)';
COMMENT ON COLUMN calendar_schedule.scheduled_date IS 'Specific date when the post should be published';
