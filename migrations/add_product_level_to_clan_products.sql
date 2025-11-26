-- Migration: Add product_level to clan_products table
-- Purpose: Store product classification (Classic, Luxury, Essential) based on title parsing
-- Date: 2025-11-11

BEGIN;

-- Add product_level column (VARCHAR with CHECK constraint)
ALTER TABLE clan_products
ADD COLUMN IF NOT EXISTS product_level VARCHAR(20) DEFAULT 'classic' 
    CHECK (product_level IN ('classic', 'luxury', 'essential'));

-- Create index for efficient filtering
CREATE INDEX IF NOT EXISTS idx_clan_products_product_level ON clan_products(product_level);

-- Add comment
COMMENT ON COLUMN clan_products.product_level IS 'Product classification: classic (default), luxury (if title contains "luxury"), or essential (if title contains "essential"). Determined by parsing product name.';

-- Populate existing products
-- Note: This will be done by a Python script for better parsing logic
-- The script will update all products based on their current names

COMMIT;

