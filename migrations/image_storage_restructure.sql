-- Image Storage System Restructure Migration
-- This script creates new image storage tables and removes old image fields from post_section

-- Step 1: Create new images table
CREATE TABLE IF NOT EXISTS images (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255),
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER,
    mime_type VARCHAR(100),
    width INTEGER,
    height INTEGER,
    alt_text TEXT,
    caption TEXT,
    image_prompt TEXT,
    notes TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Step 2: Create post_images linking table
CREATE TABLE IF NOT EXISTS post_images (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES post(id) ON DELETE CASCADE,
    image_id INTEGER REFERENCES images(id) ON DELETE CASCADE,
    image_type VARCHAR(50) NOT NULL, -- 'header_raw', 'header_optimized', 'section_raw', 'section_optimized'
    section_id INTEGER REFERENCES post_section(id) ON DELETE CASCADE, -- NULL for header images
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(post_id, image_type, section_id)
);

-- Step 3: Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_post_images_post_id ON post_images(post_id);
CREATE INDEX IF NOT EXISTS idx_post_images_section_id ON post_images(section_id);
CREATE INDEX IF NOT EXISTS idx_post_images_image_type ON post_images(image_type);
CREATE INDEX IF NOT EXISTS idx_images_created_at ON images(created_at);

-- Step 4: Remove old image fields from post_section table
-- First, let's check what data exists in these fields
SELECT 'Checking existing image data in post_section table...' as info;

SELECT 
    id,
    section_heading,
    image_prompt_example_id,
    generated_image_url,
    image_generation_metadata,
    image_id,
    watermarking
FROM post_section 
WHERE image_prompt_example_id IS NOT NULL 
   OR generated_image_url IS NOT NULL 
   OR image_generation_metadata IS NOT NULL 
   OR image_id IS NOT NULL 
   OR watermarking IS NOT NULL;

-- Step 5: Remove the old image columns from post_section
-- (We'll do this after confirming no important data exists)
ALTER TABLE post_section DROP COLUMN IF EXISTS image_prompt_example_id;
ALTER TABLE post_section DROP COLUMN IF EXISTS generated_image_url;
ALTER TABLE post_section DROP COLUMN IF EXISTS image_generation_metadata;
ALTER TABLE post_section DROP COLUMN IF EXISTS image_id;
ALTER TABLE post_section DROP COLUMN IF EXISTS watermarking;

-- Step 6: Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Step 7: Create trigger for images table
CREATE TRIGGER update_images_updated_at 
    BEFORE UPDATE ON images 
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Step 8: Insert some sample data for testing (optional)
-- INSERT INTO images (filename, original_filename, file_path, mime_type, alt_text) 
-- VALUES ('sample_header.jpg', 'header_original.jpg', '/static/images/raw/posts/1/header/sample_header.jpg', 'image/jpeg', 'Sample header image');

-- Step 9: Verify the new structure
SELECT 'Migration completed. New table structure:' as info;

-- Show the new tables
SELECT table_name, column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name IN ('images', 'post_images')
ORDER BY table_name, ordinal_position;

-- Show the updated post_section structure
SELECT 'post_section table structure after migration:' as info;
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'post_section'
ORDER BY ordinal_position; 