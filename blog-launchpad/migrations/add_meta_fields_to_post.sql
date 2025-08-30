-- Add meta fields to post table for OG tags
-- These fields are core post data needed for proper social media sharing

ALTER TABLE post ADD COLUMN meta_title VARCHAR(200);
ALTER TABLE post ADD COLUMN meta_description TEXT;
ALTER TABLE post ADD COLUMN meta_image VARCHAR(500);
ALTER TABLE post ADD COLUMN meta_type VARCHAR(50) DEFAULT 'article';
ALTER TABLE post ADD COLUMN meta_site_name VARCHAR(100) DEFAULT 'Clan.com Blog';

-- Add comments for documentation
COMMENT ON COLUMN post.meta_title IS 'Meta title for OG tags (og:title)';
COMMENT ON COLUMN post.meta_description IS 'Meta description for OG tags (og:description)';
COMMENT ON COLUMN post.meta_image IS 'Meta image URL for OG tags (og:image)';
COMMENT ON COLUMN post.meta_type IS 'Meta type for OG tags (default: article)';
COMMENT ON COLUMN post.meta_site_name IS 'Site name for OG tags (default: Clan.com Blog)';
