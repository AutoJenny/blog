-- Add product_focus column to posting_queue table
-- This stores the AI content type (feature, benefit, story) separately from content_type

ALTER TABLE posting_queue 
ADD COLUMN IF NOT EXISTS product_focus VARCHAR(50);

-- Update existing 'pending' status to 'ready' for consistency
UPDATE posting_queue 
SET status = 'ready' 
WHERE status = 'pending';

-- Update existing entries to have product_focus based on content_type
UPDATE posting_queue 
SET product_focus = content_type 
WHERE content_type IN ('feature', 'benefit', 'story') 
AND product_focus IS NULL;

-- Update content_type to 'product' for AI-generated content
UPDATE posting_queue 
SET content_type = 'product' 
WHERE content_type IN ('feature', 'benefit', 'story');
