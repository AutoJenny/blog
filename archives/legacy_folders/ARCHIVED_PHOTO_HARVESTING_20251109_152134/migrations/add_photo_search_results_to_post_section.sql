-- Add photo_search_results field to post_section for photography-based workflows
ALTER TABLE post_section ADD COLUMN IF NOT EXISTS photo_search_results JSONB DEFAULT '[]'::jsonb;

COMMENT ON COLUMN post_section.photo_search_results IS 
    'JSONB array of photo search results from Pexels/Unsplash including URLs, credits, and selection status';

