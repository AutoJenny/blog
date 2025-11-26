-- Migration: Rename 'toy' to 'recreation' in product_form constraint
-- Date: 2025-11-12
-- Reason: 'toy' category renamed to 'recreation' to include all leisure activities

-- Drop the existing constraint
ALTER TABLE clan_products
DROP CONSTRAINT IF EXISTS product_form_required;

-- Recreate constraint with 'recreation' instead of 'toy'
ALTER TABLE clan_products
ADD CONSTRAINT product_form_required CHECK (
    product_type_data IS NOT NULL
    AND product_type_data->'disambiguation' IS NOT NULL
    AND product_type_data->'disambiguation'->>'product_form' IS NOT NULL
    AND product_type_data->'disambiguation'->>'product_form' IN (
        'artwork',
        'bags',
        'clothing',
        'haberdashery',
        'homeware',
        'jewellery',
        'pets',
        'recreation',
        'stationery',
        'voucher'
    )
);

-- Update comment
COMMENT ON CONSTRAINT product_form_required ON clan_products IS 
'Ensures every product has exactly one product_form value from the valid list. '
'Recreation category includes toys, jigsaws, embroidery kits, games, and other leisure activities.';

