-- Migration: Add specifications column to clan_products
-- Purpose: Store product specifications (dimensions, materials, etc.) scraped from product pages
-- Date: 2025-01-XX

BEGIN;

-- Add specifications JSONB column
ALTER TABLE clan_products
ADD COLUMN IF NOT EXISTS specifications JSONB;

-- Create GIN index for efficient JSONB queries
CREATE INDEX IF NOT EXISTS idx_clan_products_specifications ON clan_products USING GIN (specifications);

-- Add comment
COMMENT ON COLUMN clan_products.specifications IS 'JSONB object storing product specifications scraped from product pages. Structure: {dimensions: string, material: string, emblem: string, weight: string, care_instructions: string, etc.}';

COMMIT;







