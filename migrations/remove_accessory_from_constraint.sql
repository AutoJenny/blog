-- Migration: Remove 'accessory' from product_form constraint
-- Date: 2025-11-12
-- Reason: Accessory category has been eliminated, all items redistributed

-- Drop the existing constraint
ALTER TABLE clan_products
DROP CONSTRAINT IF EXISTS product_form_required;

-- Recreate constraint without 'accessory'
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
        'stationery',
        'toy',
        'voucher'
    )
);

-- Update comment
COMMENT ON CONSTRAINT product_form_required ON clan_products IS 
'Ensures every product has exactly one product_form value from the valid list. '
'Accessory category has been eliminated - all items redistributed to other categories.';

