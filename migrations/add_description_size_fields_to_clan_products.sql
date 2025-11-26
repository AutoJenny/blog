-- Migration: Add description size fields to clan_products table
-- Purpose: Store word and character counts for product descriptions
-- Date: 2025-01-XX

BEGIN;

-- Add description size fields
ALTER TABLE clan_products
ADD COLUMN IF NOT EXISTS description_word_count INTEGER;

ALTER TABLE clan_products
ADD COLUMN IF NOT EXISTS description_char_count INTEGER;

ALTER TABLE clan_products
ADD COLUMN IF NOT EXISTS short_description_word_count INTEGER;

ALTER TABLE clan_products
ADD COLUMN IF NOT EXISTS short_description_char_count INTEGER;

-- Add comments
COMMENT ON COLUMN clan_products.description_word_count IS 'Word count of full description (HTML stripped)';
COMMENT ON COLUMN clan_products.description_char_count IS 'Character count of full description (HTML stripped, clean text)';
COMMENT ON COLUMN clan_products.short_description_word_count IS 'Word count of short description (HTML stripped)';
COMMENT ON COLUMN clan_products.short_description_char_count IS 'Character count of short description (HTML stripped, clean text)';

COMMIT;



