-- Add imaging_model_parameters column to post_development table
-- This stores the JSON parameters for the selected imaging model per post

ALTER TABLE post_development 
ADD COLUMN imaging_model_parameters TEXT;

-- Add comment
COMMENT ON COLUMN post_development.imaging_model_parameters IS 'JSON string storing imaging model parameters (size, quality, etc.) for this post';
