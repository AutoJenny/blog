-- Migration: Add last_chance block type to newsletter_block_type
-- Purpose: Register the new "Last Chance to Grab" block type
-- Date: 2025-11-26

BEGIN;

INSERT INTO newsletter_block_type (type, description) VALUES
    ('last_chance', 'Clearance products with largest discounts, one per category branch')
ON CONFLICT (type) DO UPDATE SET
    description = EXCLUDED.description,
    updated_at = NOW();

COMMIT;

