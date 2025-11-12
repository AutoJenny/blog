-- Migration: Enforce product_form constraint at database level
-- Ensures every product has exactly one product_form from a valid list
-- Date: 2025-11-12

-- First, ensure all products have product_form set (safety check)
-- This should already be done, but verify
DO $$
DECLARE
    missing_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO missing_count
    FROM clan_products
    WHERE product_type_data IS NULL
       OR product_type_data->'disambiguation'->>'product_form' IS NULL;
    
    IF missing_count > 0 THEN
        RAISE EXCEPTION 'Cannot add constraint: % products are missing product_form', missing_count;
    END IF;
END $$;

-- Add CHECK constraint to ensure product_form is always present and valid
-- This constraint checks:
-- 1. product_type_data exists
-- 2. disambiguation exists within product_type_data
-- 3. product_form exists within disambiguation
-- 4. product_form is one of the valid values

ALTER TABLE clan_products
ADD CONSTRAINT product_form_required CHECK (
    product_type_data IS NOT NULL
    AND product_type_data->'disambiguation' IS NOT NULL
    AND product_type_data->'disambiguation'->>'product_form' IS NOT NULL
    AND product_type_data->'disambiguation'->>'product_form' IN (
        'accessory',
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

-- Add a comment explaining the constraint
COMMENT ON CONSTRAINT product_form_required ON clan_products IS 
'Ensures every product has exactly one product_form value from the valid list. '
'This enforces data integrity at the database level.';

-- Create a function to automatically set product_form if missing (for inserts/updates)
CREATE OR REPLACE FUNCTION ensure_product_form()
RETURNS TRIGGER AS $$
BEGIN
    -- If product_type_data exists but product_form is missing, this will fail the constraint
    -- We could set a default here, but it's better to require explicit assignment
    IF NEW.product_type_data IS NOT NULL THEN
        IF NEW.product_type_data->'disambiguation' IS NULL THEN
            NEW.product_type_data := jsonb_set(
                NEW.product_type_data,
                '{disambiguation}',
                '{}'::jsonb
            );
        END IF;
        
        -- If product_form is still missing, raise an error
        IF NEW.product_type_data->'disambiguation'->>'product_form' IS NULL THEN
            RAISE EXCEPTION 'product_form is required when product_type_data is present. Product ID: %', NEW.id;
        END IF;
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to enforce product_form on insert/update
DROP TRIGGER IF EXISTS enforce_product_form_trigger ON clan_products;

CREATE TRIGGER enforce_product_form_trigger
    BEFORE INSERT OR UPDATE ON clan_products
    FOR EACH ROW
    WHEN (NEW.product_type_data IS NOT NULL)
    EXECUTE FUNCTION ensure_product_form();

-- Add comment on trigger
COMMENT ON TRIGGER enforce_product_form_trigger ON clan_products IS 
'Ensures product_form is set when product_type_data is present. '
'Raises an error if product_form is missing.';

