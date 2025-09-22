-- Add name column to daily_posts_schedule table
ALTER TABLE daily_posts_schedule 
ADD COLUMN name VARCHAR(255) NOT NULL DEFAULT 'Schedule';

-- Update existing records to have meaningful names based on their day patterns
UPDATE daily_posts_schedule 
SET name = CASE 
    WHEN days::text = '[1,2,3,4,5]' THEN 'Weekdays'
    WHEN days::text = '[6,7]' THEN 'Weekends' 
    WHEN days::text = '[1,2,3,4,5,6,7]' THEN 'Daily'
    ELSE 'Custom Schedule'
END
WHERE name = 'Schedule';

-- Add comment to the new column
COMMENT ON COLUMN daily_posts_schedule.name IS 'Human-readable name for the schedule (e.g., Weekdays, Weekends, Daily)';
