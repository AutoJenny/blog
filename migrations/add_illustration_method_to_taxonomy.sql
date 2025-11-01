-- Add illustration_method column to taxonomy_item table
-- This field determines how images are produced for different taxonomy items

BEGIN;

-- Add the illustration_method column
ALTER TABLE taxonomy_item 
    ADD COLUMN IF NOT EXISTS illustration_method VARCHAR(50);

-- Add a check constraint to ensure only valid values
ALTER TABLE taxonomy_item 
    ADD CONSTRAINT check_illustration_method 
    CHECK (illustration_method IS NULL OR illustration_method IN ('LLM-creation', 'Photo-harvesting'));

-- Create index for performance
CREATE INDEX IF NOT EXISTS idx_taxonomy_item_illustration_method 
    ON taxonomy_item(illustration_method);

-- Add comment
COMMENT ON COLUMN taxonomy_item.illustration_method IS 
    'Method for producing illustrations: LLM-creation (AI-generated) or Photo-harvesting (photography-based)';

COMMIT;

