-- Create Taxonomy System
-- This migration creates the taxonomy tables and adds taxonomy columns to the post table

-- 1. Create taxonomy_tier table
CREATE TABLE IF NOT EXISTS taxonomy_tier (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL UNIQUE,
    display_name VARCHAR(100) NOT NULL,
    description TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 2. Create taxonomy_item table
CREATE TABLE IF NOT EXISTS taxonomy_item (
    id SERIAL PRIMARY KEY,
    tier_id INTEGER NOT NULL REFERENCES taxonomy_tier(id) ON DELETE CASCADE,
    parent_id INTEGER REFERENCES taxonomy_item(id) ON DELETE SET NULL,
    slug VARCHAR(100) NOT NULL UNIQUE,
    display_name VARCHAR(200) NOT NULL,
    description TEXT,
    common_assets JSONB DEFAULT '[]'::jsonb,
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- 3. Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_taxonomy_item_tier ON taxonomy_item(tier_id);
CREATE INDEX IF NOT EXISTS idx_taxonomy_item_parent ON taxonomy_item(parent_id);
CREATE INDEX IF NOT EXISTS idx_taxonomy_item_slug ON taxonomy_item(slug);
CREATE INDEX IF NOT EXISTS idx_taxonomy_item_active ON taxonomy_item(is_active);

-- 4. Add taxonomy columns to post table
ALTER TABLE post ADD COLUMN IF NOT EXISTS theme_id INTEGER REFERENCES taxonomy_item(id);
ALTER TABLE post ADD COLUMN IF NOT EXISTS content_type_id INTEGER REFERENCES taxonomy_item(id);
ALTER TABLE post ADD COLUMN IF NOT EXISTS format_id INTEGER REFERENCES taxonomy_item(id);

-- 5. Create indexes on post taxonomy columns
CREATE INDEX IF NOT EXISTS idx_post_theme_id ON post(theme_id);
CREATE INDEX IF NOT EXISTS idx_post_content_type_id ON post(content_type_id);
CREATE INDEX IF NOT EXISTS idx_post_format_id ON post(format_id);

-- 6. Add comments for documentation
COMMENT ON TABLE taxonomy_tier IS 'Defines the three taxonomy tiers: theme, content_type, format';
COMMENT ON TABLE taxonomy_item IS 'Stores individual taxonomy items (themes, content types, formats) with hierarchical relationships';
COMMENT ON COLUMN taxonomy_item.parent_id IS 'Reference to parent taxonomy_item (for content types that belong to themes)';
COMMENT ON COLUMN taxonomy_item.common_assets IS 'JSONB array of common asset types for this taxonomy item (e.g., ["Illustrations", "character art", "maps"])';
COMMENT ON COLUMN post.theme_id IS 'Foreign key to taxonomy_item (Theme tier)';
COMMENT ON COLUMN post.content_type_id IS 'Foreign key to taxonomy_item (Content Type tier)';
COMMENT ON COLUMN post.format_id IS 'Foreign key to taxonomy_item (Format tier)';

