-- Create daily_posts_schedule table for storing posting schedules
-- This table stores the schedule configuration for daily product posts

CREATE TABLE IF NOT EXISTS daily_posts_schedule (
    id SERIAL PRIMARY KEY,
    time TIME NOT NULL DEFAULT '17:00',
    timezone VARCHAR(50) NOT NULL DEFAULT 'GMT',
    days JSONB NOT NULL DEFAULT '[]',
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create index for active schedules
CREATE INDEX IF NOT EXISTS idx_daily_posts_schedule_active 
ON daily_posts_schedule(is_active) 
WHERE is_active = true;

-- Add comment
COMMENT ON TABLE daily_posts_schedule IS 'Stores posting schedule configuration for daily product posts';
COMMENT ON COLUMN daily_posts_schedule.time IS 'Time of day for posting (HH:MM format)';
COMMENT ON COLUMN daily_posts_schedule.timezone IS 'Timezone for the posting time';
COMMENT ON COLUMN daily_posts_schedule.days IS 'JSON array of day numbers (1=Monday, 7=Sunday)';
COMMENT ON COLUMN daily_posts_schedule.is_active IS 'Whether this schedule is currently active';
