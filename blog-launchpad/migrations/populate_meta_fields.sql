-- Populate the new meta fields with appropriate values based on existing post data
-- This will ensure all posts have proper OG tag metadata

-- Update meta_title (use title if not set)
UPDATE post 
SET meta_title = title 
WHERE meta_title IS NULL OR meta_title = '';

-- Update meta_description (use summary if not set, fallback to subtitle)
UPDATE post 
SET meta_description = COALESCE(summary, subtitle, 'Discover fascinating insights into Scottish culture, history, and traditions.')
WHERE meta_description IS NULL OR meta_description = '';

-- Update meta_type (set to 'article' for all blog posts)
UPDATE post 
SET meta_type = 'article' 
WHERE meta_type IS NULL OR meta_type = '';

-- Update meta_site_name (set to 'Clan.com Blog' for all posts)
UPDATE post 
SET meta_site_name = 'Clan.com Blog' 
WHERE meta_site_name IS NULL OR meta_site_name = '';

-- Update meta_image with a default Scottish-themed image if none set
-- Note: This is a placeholder - you may want to set specific images per post
UPDATE post 
SET meta_image = 'https://clan.com/images/default-scottish-heritage.jpg'
WHERE meta_image IS NULL OR meta_image = '';

-- Show the results
SELECT id, title, meta_title, meta_type, meta_site_name, 
       CASE WHEN LENGTH(meta_description) > 100 THEN LEFT(meta_description, 100) || '...' ELSE meta_description END as meta_description_preview
FROM post 
WHERE status != 'deleted' 
ORDER BY id;







