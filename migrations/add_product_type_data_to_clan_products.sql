-- Migration: Add product_type_data to clan_products table
-- Purpose: Store structured product type identifiers (core_type, subtype, materials, etc.)
-- Date: 2025-11-11

BEGIN;

-- Add product_type_data column (JSONB)
ALTER TABLE clan_products
ADD COLUMN IF NOT EXISTS product_type_data JSONB DEFAULT '{}';

-- Create GIN index for efficient JSONB queries
CREATE INDEX IF NOT EXISTS idx_clan_products_product_type_data 
ON clan_products USING GIN (product_type_data);

-- Create index on confidence for filtering low-confidence products
CREATE INDEX IF NOT EXISTS idx_clan_products_type_confidence 
ON clan_products ((product_type_data->>'confidence'));

-- Add comment
COMMENT ON COLUMN clan_products.product_type_data IS 'Structured product type identifiers: core_type, subtype, materials, patterns, decorations, occasions, styles, attributes, disambiguation flags, confidence score, and parsing metadata.';

COMMIT;

