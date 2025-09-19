-- =====================================================
-- CREATE POSTING_QUEUE TABLE WITH PLATFORM FIELDS
-- Create posting_queue table with all necessary fields for unified timeline
-- =====================================================

-- Create posting_queue table with platform/channel/type support
CREATE TABLE IF NOT EXISTS posting_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER REFERENCES products(id),
    platform VARCHAR(50) DEFAULT 'facebook',
    channel_type VARCHAR(50) DEFAULT 'feed_post',
    content_type VARCHAR(50) DEFAULT 'product',
    scheduled_date DATE,
    scheduled_time TIME,
    scheduled_timestamp TIMESTAMP,
    schedule_name VARCHAR(100),
    timezone VARCHAR(50),
    generated_content TEXT,
    queue_order INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'pending',
    platform_post_id VARCHAR(100),
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_posting_queue_product_id ON posting_queue(product_id);
CREATE INDEX IF NOT EXISTS idx_posting_queue_platform ON posting_queue(platform);
CREATE INDEX IF NOT EXISTS idx_posting_queue_channel_type ON posting_queue(channel_type);
CREATE INDEX IF NOT EXISTS idx_posting_queue_content_type ON posting_queue(content_type);
CREATE INDEX IF NOT EXISTS idx_posting_queue_scheduled_timestamp ON posting_queue(scheduled_timestamp);
CREATE INDEX IF NOT EXISTS idx_posting_queue_status ON posting_queue(status);
CREATE INDEX IF NOT EXISTS idx_posting_queue_order ON posting_queue(queue_order);

