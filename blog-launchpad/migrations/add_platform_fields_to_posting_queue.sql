-- =====================================================
-- ADD PLATFORM FIELDS TO POSTING_QUEUE TABLE
-- Extend existing posting_queue to support unified timeline
-- =====================================================

-- Add platform, channel, and content type fields to posting_queue
ALTER TABLE posting_queue ADD COLUMN platform VARCHAR(50) DEFAULT 'facebook';
ALTER TABLE posting_queue ADD COLUMN channel_type VARCHAR(50) DEFAULT 'feed_post';
ALTER TABLE posting_queue ADD COLUMN content_type VARCHAR(50) DEFAULT 'product';
ALTER TABLE posting_queue ADD COLUMN scheduled_timestamp TIMESTAMP;
ALTER TABLE posting_queue ADD COLUMN platform_post_id VARCHAR(100);
ALTER TABLE posting_queue ADD COLUMN error_message TEXT;

-- Create indexes for the new fields
CREATE INDEX IF NOT EXISTS idx_posting_queue_platform ON posting_queue(platform);
CREATE INDEX IF NOT EXISTS idx_posting_queue_channel_type ON posting_queue(channel_type);
CREATE INDEX IF NOT EXISTS idx_posting_queue_content_type ON posting_queue(content_type);
CREATE INDEX IF NOT EXISTS idx_posting_queue_scheduled_timestamp ON posting_queue(scheduled_timestamp);
CREATE INDEX IF NOT EXISTS idx_posting_queue_platform_post_id ON posting_queue(platform_post_id);

-- Update existing records to have proper platform/channel info
UPDATE posting_queue 
SET platform = 'facebook', 
    channel_type = 'feed_post', 
    content_type = 'product',
    scheduled_timestamp = CASE 
        WHEN scheduled_date IS NOT NULL AND scheduled_time IS NOT NULL 
        THEN (scheduled_date + scheduled_time)::timestamp
        ELSE created_at
    END
WHERE platform IS NULL;

-- Add comments for documentation
COMMENT ON COLUMN posting_queue.platform IS 'Social media platform (facebook, instagram, twitter, linkedin)';
COMMENT ON COLUMN posting_queue.channel_type IS 'Type of post channel (feed_post, story_post, video_post, etc.)';
COMMENT ON COLUMN posting_queue.content_type IS 'Type of content (product, blog, tartan, event)';
COMMENT ON COLUMN posting_queue.scheduled_timestamp IS 'Combined scheduled date and time as timestamp';
COMMENT ON COLUMN posting_queue.platform_post_id IS 'ID returned by the platform after posting';
COMMENT ON COLUMN posting_queue.error_message IS 'Error message if posting failed';