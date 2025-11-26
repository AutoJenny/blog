-- Add default_image_style column to taxonomy_item table
-- This field stores the default image style configuration for content types
-- Follows the same pattern as illustration_method

BEGIN;

-- Add the default_image_style column as JSONB to store complete style definitions
ALTER TABLE taxonomy_item 
    ADD COLUMN IF NOT EXISTS default_image_style JSONB;

-- Create index for performance (though JSONB queries are less common)
CREATE INDEX IF NOT EXISTS idx_taxonomy_item_default_image_style 
    ON taxonomy_item USING GIN (default_image_style);

-- Add comment
COMMENT ON COLUMN taxonomy_item.default_image_style IS 
    'Default image style configuration for this taxonomy item (content type). Stored as JSONB with structure: {"name": "...", "style_json": {...}}';

COMMIT;

