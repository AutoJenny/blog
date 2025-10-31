-- Add description field to newsletter_block and create block_type_description table
BEGIN;

-- Add description field to newsletter_block
ALTER TABLE newsletter_block 
ADD COLUMN IF NOT EXISTS description TEXT NULL;

-- Create table to store default descriptions per block type
CREATE TABLE IF NOT EXISTS newsletter_block_type (
    type VARCHAR(48) PRIMARY KEY,
    description TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Insert default descriptions for each block type
INSERT INTO newsletter_block_type (type, description) VALUES
    ('feature', 'Latest published blog post with header image and excerpt to highlight recent content'),
    ('snapshot', 'Scottish cultural snapshot from approved news or community sources, with brief commentary'),
    ('new_products', 'Recently added products from the catalog, grouped by variant to avoid duplication'),
    ('spotlight', 'Featured single product showcase with detailed description and imagery'),
    ('category', 'Rotating category feature content highlighting topics related to Scottish culture and heritage'),
    ('evergreen', 'Reusable content snippet that can be rotated with seasonal or regional relevance'),
    ('closing', 'Sign-off message and call-to-action to close the newsletter issue')
ON CONFLICT (type) DO UPDATE SET
    description = EXCLUDED.description,
    updated_at = NOW();

COMMIT;

