-- Seed Taxonomy Data
-- This migration seeds the taxonomy system with the provided taxonomy items

-- 1. Insert taxonomy tiers
INSERT INTO taxonomy_tier (name, display_name, description) VALUES
('theme', 'Theme', 'Top-level thematic grouping'),
('content_type', 'Content Type', 'Specific content categories grouped under themes'),
('format', 'Format', 'Content format types')
ON CONFLICT (name) DO NOTHING;

-- 2. Insert Themes (no parent_id)
INSERT INTO taxonomy_item (tier_id, parent_id, slug, display_name, description, common_assets, display_order) VALUES
(
    (SELECT id FROM taxonomy_tier WHERE name = 'theme'),
    NULL,
    'heritage_history',
    'Heritage & History',
    'Deep cultural storytelling and clan-based content',
    '[]'::jsonb,
    1
),
(
    (SELECT id FROM taxonomy_tier WHERE name = 'theme'),
    NULL,
    'culture_life',
    'Culture & Life',
    'Living Scottish culture, craftsmanship, and festivals',
    '[]'::jsonb,
    2
),
(
    (SELECT id FROM taxonomy_tier WHERE name = 'theme'),
    NULL,
    'scotland_nature',
    'Scotland & Nature',
    'Sense of place through landscape and material culture',
    '[]'::jsonb,
    3
)
ON CONFLICT (slug) DO NOTHING;

-- 3. Insert Content Types (with parent_id references to themes)
INSERT INTO taxonomy_item (tier_id, parent_id, slug, display_name, description, common_assets, display_order) VALUES
(
    (SELECT id FROM taxonomy_tier WHERE name = 'content_type'),
    (SELECT id FROM taxonomy_item WHERE slug = 'heritage_history'),
    'myths-traditions',
    'Myths & Traditions',
    'Folklore, storytelling, and ancestral customs of Scotland',
    '["Illustrations", "character art", "maps"]'::jsonb,
    1
),
(
    (SELECT id FROM taxonomy_tier WHERE name = 'content_type'),
    (SELECT id FROM taxonomy_item WHERE slug = 'heritage_history'),
    'historical-events',
    'Historical Events',
    'Significant Scottish events, battles, and moments that shaped history',
    '["Timelines", "portraits", "archive imagery"]'::jsonb,
    2
),
(
    (SELECT id FROM taxonomy_tier WHERE name = 'content_type'),
    (SELECT id FROM taxonomy_item WHERE slug = 'heritage_history'),
    'families-clans',
    'Families & Clans',
    'Stories and profiles connecting names to clan heritage and symbols',
    '["Crests", "tartans", "lineage visuals"]'::jsonb,
    3
),
(
    (SELECT id FROM taxonomy_tier WHERE name = 'content_type'),
    (SELECT id FROM taxonomy_item WHERE slug = 'culture_life'),
    'modern-celebrations',
    'Modern Celebrations',
    'Contemporary Scottish festivals and cultural expressions worldwide',
    '["Photography", "short video", "event links"]'::jsonb,
    4
),
(
    (SELECT id FROM taxonomy_tier WHERE name = 'content_type'),
    (SELECT id FROM taxonomy_item WHERE slug = 'culture_life'),
    'products-producers',
    'Products & Producers',
    'Features on craftspeople, whisky makers, weavers, and artisans',
    '["Product photography", "maker portraits"]'::jsonb,
    5
),
(
    (SELECT id FROM taxonomy_tier WHERE name = 'content_type'),
    (SELECT id FROM taxonomy_item WHERE slug = 'scotland_nature'),
    'landscapes-seasons',
    'Landscapes & Seasons',
    'Exploration of Scottish nature, weather, and geography across seasons',
    '["Scenic imagery", "landscape photography"]'::jsonb,
    6
),
(
    (SELECT id FROM taxonomy_tier WHERE name = 'content_type'),
    (SELECT id FROM taxonomy_item WHERE slug = 'scotland_nature'),
    'tartans-textiles',
    'Tartans & Textiles',
    'Histories of tartan patterns, weaving techniques, and fabric innovation',
    '["Fabric swatches", "weaving diagrams", "product photos"]'::jsonb,
    7
)
ON CONFLICT (slug) DO NOTHING;

-- 4. Insert Formats (no parent_id)
INSERT INTO taxonomy_item (tier_id, parent_id, slug, display_name, description, common_assets, display_order) VALUES
(
    (SELECT id FROM taxonomy_tier WHERE name = 'format'),
    NULL,
    'article',
    'Article',
    'Standard long-form written piece',
    '[]'::jsonb,
    1
),
(
    (SELECT id FROM taxonomy_tier WHERE name = 'format'),
    NULL,
    'photo-essay',
    'Photo Essay',
    'Visually led story with image captions',
    '[]'::jsonb,
    2
),
(
    (SELECT id FROM taxonomy_tier WHERE name = 'format'),
    NULL,
    'carousel',
    'Carousel',
    'Multi-slide Instagram/blog hybrid visual format',
    '[]'::jsonb,
    3
),
(
    (SELECT id FROM taxonomy_tier WHERE name = 'format'),
    NULL,
    'video',
    'Video',
    'Embedded or hosted video content with supporting text',
    '[]'::jsonb,
    4
),
(
    (SELECT id FROM taxonomy_tier WHERE name = 'format'),
    NULL,
    'interview',
    'Interview',
    'Q&A or profile format highlighting individuals or makers',
    '[]'::jsonb,
    5
)
ON CONFLICT (slug) DO NOTHING;

