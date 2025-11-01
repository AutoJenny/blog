-- Add image_search_terms field to post_section for photography-based workflows
ALTER TABLE post_section ADD COLUMN IF NOT EXISTS image_search_terms JSONB DEFAULT '[]'::jsonb;

COMMENT ON COLUMN post_section.image_search_terms IS 'JSONB array of search terms for photography-based image workflows (when content_type uses photography instead of AI generation)';

