-- =====================================================
-- UPDATE POSTING_QUEUE TABLE - PostgreSQL Schema
-- Add platform, channel_type, content_type fields to match current data
-- =====================================================

-- Add missing columns to existing posting_queue table
ALTER TABLE posting_queue 
ADD COLUMN IF NOT EXISTS platform VARCHAR(50) DEFAULT 'facebook',
ADD COLUMN IF NOT EXISTS channel_type VARCHAR(50) DEFAULT 'blog_post',
ADD COLUMN IF NOT EXISTS content_type VARCHAR(50) DEFAULT 'product',
ADD COLUMN IF NOT EXISTS scheduled_timestamp TIMESTAMP,
ADD COLUMN IF NOT EXISTS platform_post_id VARCHAR(100),
ADD COLUMN IF NOT EXISTS error_message TEXT,
ADD COLUMN IF NOT EXISTS product_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS sku VARCHAR(100),
ADD COLUMN IF NOT EXISTS price DECIMAL(10,2),
ADD COLUMN IF NOT EXISTS product_image VARCHAR(500),
ADD COLUMN IF NOT EXISTS post_id INTEGER,
ADD COLUMN IF NOT EXISTS post_title VARCHAR(255),
ADD COLUMN IF NOT EXISTS section_id INTEGER,
ADD COLUMN IF NOT EXISTS section_title VARCHAR(255);

-- Create indexes for new columns
CREATE INDEX IF NOT EXISTS idx_posting_queue_platform ON posting_queue (platform);
CREATE INDEX IF NOT EXISTS idx_posting_queue_channel_type ON posting_queue (channel_type);
CREATE INDEX IF NOT EXISTS idx_posting_queue_content_type ON posting_queue (content_type);
CREATE INDEX IF NOT EXISTS idx_posting_queue_scheduled_timestamp ON posting_queue (scheduled_timestamp);
CREATE INDEX IF NOT EXISTS idx_posting_queue_platform_post_id ON posting_queue (platform_post_id);

-- Add comments for new columns
COMMENT ON COLUMN posting_queue.platform IS 'Social media platform (facebook, instagram, twitter, etc.)';
COMMENT ON COLUMN posting_queue.channel_type IS 'Type of channel (blog_post, story_post, etc.)';
COMMENT ON COLUMN posting_queue.content_type IS 'Type of content (product, blog_post, etc.)';
COMMENT ON COLUMN posting_queue.scheduled_timestamp IS 'Exact timestamp when post should be published';
COMMENT ON COLUMN posting_queue.platform_post_id IS 'ID of the post on the social media platform after publishing';
COMMENT ON COLUMN posting_queue.error_message IS 'Error message if posting failed';
COMMENT ON COLUMN posting_queue.product_name IS 'Name of the product (for product posts)';
COMMENT ON COLUMN posting_queue.sku IS 'Product SKU (for product posts)';
COMMENT ON COLUMN posting_queue.price IS 'Product price (for product posts)';
COMMENT ON COLUMN posting_queue.product_image IS 'Product image URL (for product posts)';
COMMENT ON COLUMN posting_queue.post_id IS 'Blog post ID (for blog posts)';
COMMENT ON COLUMN posting_queue.post_title IS 'Blog post title (for blog posts)';
COMMENT ON COLUMN posting_queue.section_id IS 'Blog post section ID (for blog posts)';
COMMENT ON COLUMN posting_queue.section_title IS 'Blog post section title (for blog posts)';

