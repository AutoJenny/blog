-- Rename taxonomy tier "theme" to "category" to avoid confusion with calendar themes
-- Calendar themes (calendar_themes) are week-based ideas
-- Taxonomy categories (taxonomy_item with tier='category') are classification categories

BEGIN;

-- Update taxonomy_tier name
UPDATE taxonomy_tier 
SET name = 'category', 
    display_name = 'Category',
    updated_at = NOW()
WHERE name = 'theme';

-- Update column comments
COMMENT ON COLUMN post.theme_id IS 'Foreign key to taxonomy_item (Category tier) - classification category, NOT calendar theme';

COMMIT;


