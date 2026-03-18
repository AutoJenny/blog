-- Update daily_posts_schedule table to support multiple schedule entries
-- Add name field and remove unique constraints to allow multiple active schedules

-- Add name field for schedule identification
ALTER TABLE daily_posts_schedule 
ADD COLUMN IF NOT EXISTS name VARCHAR(100) DEFAULT 'Default Schedule';

-- Add display_order for sorting schedules
ALTER TABLE daily_posts_schedule 
ADD COLUMN IF NOT EXISTS display_order INTEGER DEFAULT 0;

-- Update existing records to have a default name
UPDATE daily_posts_schedule 
SET name = 'Default Schedule' 
WHERE name IS NULL OR name = '';

-- Add comment for new fields
COMMENT ON COLUMN daily_posts_schedule.name IS 'Human-readable name for the schedule entry';
COMMENT ON COLUMN daily_posts_schedule.display_order IS 'Order for displaying schedules (lower numbers first)';
