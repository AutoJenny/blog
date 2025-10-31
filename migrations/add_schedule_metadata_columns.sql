-- Add schedule metadata columns for syndication scheduling

-- Add human-readable name for schedule
ALTER TABLE daily_posts_schedule
ADD COLUMN IF NOT EXISTS name VARCHAR(255) NOT NULL DEFAULT 'Schedule';

-- Add platform/content type to scope schedules (e.g., facebook/product)
ALTER TABLE daily_posts_schedule
ADD COLUMN IF NOT EXISTS platform VARCHAR(50),
ADD COLUMN IF NOT EXISTS content_type VARCHAR(50);

-- Optional: page identification for logging/auditing (e.g., FB page)
ALTER TABLE daily_posts_schedule
ADD COLUMN IF NOT EXISTS page_id VARCHAR(100),
ADD COLUMN IF NOT EXISTS page_name VARCHAR(200);

-- Backfill reasonable defaults
UPDATE daily_posts_schedule
SET platform = COALESCE(platform, 'facebook'),
    content_type = COALESCE(content_type, 'product')
WHERE platform IS NULL OR content_type IS NULL;

-- Comments
COMMENT ON COLUMN daily_posts_schedule.name IS 'Human-readable schedule name';
COMMENT ON COLUMN daily_posts_schedule.platform IS 'Platform (e.g., facebook)';
COMMENT ON COLUMN daily_posts_schedule.content_type IS 'Content type (e.g., product, blog_post)';
COMMENT ON COLUMN daily_posts_schedule.page_id IS 'Platform page/account identifier';
COMMENT ON COLUMN daily_posts_schedule.page_name IS 'Platform page/account display name';


