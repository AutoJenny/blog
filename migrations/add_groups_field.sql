-- Add groups field to post_development table for two-stage section planning
-- This field stores the thematic groups created in Stage 1

ALTER TABLE post_development 
ADD COLUMN IF NOT EXISTS groups TEXT;

-- Add comment to explain the field
COMMENT ON COLUMN post_development.groups IS 'JSON string storing thematic topic groups from Stage 1 of section planning';
