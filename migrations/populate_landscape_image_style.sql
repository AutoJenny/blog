-- Populate default_image_style for landscape content types
-- This sets the Photorealistic style as the default for landscape posts

BEGIN;

-- Define the Photorealistic style
-- This will be stored in the default_image_style JSONB column
UPDATE taxonomy_item
SET default_image_style = jsonb_build_object(
    'name', 'Photorealistic',
    'style_json', jsonb_build_object(
        'medium', 'photorealistic digital photography',
        'technique', 'high-resolution, sharp focus, natural lighting',
        'palette', jsonb_build_array(
            'natural earth tones',
            'sky blues',
            'greens',
            'natural colors'
        ),
        'composition', 'rule-of-thirds with natural framing',
        'lighting', 'natural daylight, soft shadows, realistic atmosphere',
        'constraints', jsonb_build_array(
            'no text',
            'no watermark in frame',
            'no artificial elements'
        ),
        'negatives', jsonb_build_array(
            'illustration',
            'watercolour',
            'painting',
            'stylized',
            'artistic interpretation'
        )
    )
)
WHERE LOWER(display_name) LIKE '%landscape%'
   OR LOWER(display_name) LIKE '%landscapes%'
   OR LOWER(slug) LIKE '%landscape%';

-- Log what was updated
DO $$
DECLARE
    updated_count INTEGER;
BEGIN
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RAISE NOTICE 'Updated % taxonomy items with Photorealistic default image style', updated_count;
END $$;

COMMIT;

