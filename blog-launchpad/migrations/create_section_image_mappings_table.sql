-- Create table to store section image upload mappings
-- This maps local image paths to live Clan.com URLs after upload

CREATE TABLE IF NOT EXISTS section_image_mappings (
    id SERIAL PRIMARY KEY,
    post_id INTEGER NOT NULL,
    section_id INTEGER NOT NULL,
    local_image_path TEXT NOT NULL,
    clan_uploaded_url TEXT NOT NULL,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    image_filename TEXT,
    image_size_bytes BIGINT,
    image_dimensions TEXT,
    
    -- Foreign key constraints
    CONSTRAINT fk_section_image_mappings_post 
        FOREIGN KEY (post_id) REFERENCES post(id) ON DELETE CASCADE,
    CONSTRAINT fk_section_image_mappings_section 
        FOREIGN KEY (section_id) REFERENCES post_section(id) ON DELETE CASCADE,
    
    -- Unique constraint to prevent duplicate mappings
    CONSTRAINT unique_section_image_mapping 
        UNIQUE (post_id, section_id, local_image_path)
);

-- Create indexes for efficient lookups
CREATE INDEX IF NOT EXISTS idx_section_image_mappings_post_id ON section_image_mappings(post_id);
CREATE INDEX IF NOT EXISTS idx_section_image_mappings_section_id ON section_image_mappings(section_id);
CREATE INDEX IF NOT EXISTS idx_section_image_mappings_local_path ON section_image_mappings(local_image_path);

-- Add comments for documentation
COMMENT ON TABLE section_image_mappings IS 'Stores mappings between local image paths and live Clan.com URLs for section images';
COMMENT ON COLUMN section_image_mappings.local_image_path IS 'Local development path to the image (e.g., http://localhost:5005/static/...)';
COMMENT ON COLUMN section_image_mappings.clan_uploaded_url IS 'Live Clan.com URL where the image is accessible (e.g., https://static.clan.com/media/blog/...)';
COMMENT ON COLUMN section_image_mappings.image_filename IS 'Filename used when uploading to Clan.com';
COMMENT ON COLUMN section_image_mappings.image_size_bytes IS 'Size of the uploaded image in bytes';
COMMENT ON COLUMN section_image_mappings.image_dimensions IS 'Dimensions of the uploaded image (e.g., 1200x630)';




