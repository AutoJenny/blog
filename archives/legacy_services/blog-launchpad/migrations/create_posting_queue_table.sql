-- Create posting_queue table for managing queued posts
CREATE TABLE IF NOT EXISTS posting_queue (
    id SERIAL PRIMARY KEY,
    product_id INTEGER REFERENCES clan_products(id),
    scheduled_date DATE,
    scheduled_time TIME,
    schedule_name VARCHAR(100),
    timezone VARCHAR(50),
    generated_content TEXT,
    queue_order INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'ready',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_posting_queue_product_id ON posting_queue (product_id);
CREATE INDEX IF NOT EXISTS idx_posting_queue_scheduled_datetime ON posting_queue (scheduled_date, scheduled_time);
CREATE INDEX IF NOT EXISTS idx_posting_queue_order ON posting_queue (queue_order);
CREATE INDEX IF NOT EXISTS idx_posting_queue_status ON posting_queue (status);

-- Add comments
COMMENT ON TABLE posting_queue IS 'Stores product posts queued for future publication.';
COMMENT ON COLUMN posting_queue.product_id IS 'Foreign key to the clan_products table.';
COMMENT ON COLUMN posting_queue.scheduled_date IS 'The date the post is scheduled for (null if unscheduled).';
COMMENT ON COLUMN posting_queue.scheduled_time IS 'The time of day the post is scheduled for (null if unscheduled).';
COMMENT ON COLUMN posting_queue.schedule_name IS 'The name of the schedule that generated this queue item, or null if manually added.';
COMMENT ON COLUMN posting_queue.timezone IS 'The timezone for the scheduled post (null if unscheduled).';
COMMENT ON COLUMN posting_queue.generated_content IS 'The AI-generated content for the post.';
COMMENT ON COLUMN posting_queue.queue_order IS 'The display order of the item in the queue.';
COMMENT ON COLUMN posting_queue.status IS 'Current status of the queue item (e.g., ready, posted, failed).';