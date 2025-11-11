-- Migration: Add producer_id to clan_products table
-- Purpose: Link products to normalized producers table
-- Date: 2025-01-XX

BEGIN;

-- Add producer_id column
ALTER TABLE clan_products
ADD COLUMN IF NOT EXISTS producer_id INTEGER REFERENCES producers(id) ON DELETE SET NULL;

-- Create index for efficient lookups
CREATE INDEX IF NOT EXISTS idx_clan_products_producer ON clan_products(producer_id) WHERE producer_id IS NOT NULL;

-- Add comment
COMMENT ON COLUMN clan_products.producer_id IS 'Reference to normalized producers table. Populated by migrating supplier_name values.';

COMMIT;





