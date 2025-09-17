-- Update posting_queue table to allow null values for scheduling fields
-- This allows items to be added to queue without immediate scheduling

-- Make scheduled fields nullable
ALTER TABLE posting_queue 
ALTER COLUMN scheduled_date DROP NOT NULL;

ALTER TABLE posting_queue 
ALTER COLUMN scheduled_time DROP NOT NULL;

-- Add comments
COMMENT ON COLUMN posting_queue.scheduled_date IS 'Date when the post should be published (null if unscheduled)';
COMMENT ON COLUMN posting_queue.scheduled_time IS 'Time when the post should be published (null if unscheduled)';
COMMENT ON COLUMN posting_queue.schedule_name IS 'Name of the schedule that triggered this post (null if manually added)';
COMMENT ON COLUMN posting_queue.timezone IS 'Timezone for the scheduled time (null if unscheduled)';
