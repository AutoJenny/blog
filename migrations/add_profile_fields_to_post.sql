-- Migration: Add profile fields to post table
-- Purpose: Support Product and Category Profiles with extended metadata
-- Date: 2025-01-XX

BEGIN;

-- Add profile type column
ALTER TABLE post 
ADD COLUMN IF NOT EXISTS profile_type VARCHAR(20) CHECK (profile_type IN ('product', 'category', NULL));

-- Add product/category references
ALTER TABLE post 
ADD COLUMN IF NOT EXISTS profile_product_id INTEGER REFERENCES clan_products(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS profile_category_id INTEGER REFERENCES clan_categories(id) ON DELETE SET NULL;

-- Add producer reference
ALTER TABLE post 
ADD COLUMN IF NOT EXISTS profile_producer_id INTEGER REFERENCES producers(id) ON DELETE SET NULL;

-- Add profile metadata fields
ALTER TABLE post 
ADD COLUMN IF NOT EXISTS profile_producer_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS profile_standfirst TEXT,
ADD COLUMN IF NOT EXISTS profile_explore_links JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS profile_quick_facts JSONB DEFAULT '{}';

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_post_profile_type ON post(profile_type) WHERE profile_type IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_post_profile_product ON post(profile_product_id) WHERE profile_product_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_post_profile_category ON post(profile_category_id) WHERE profile_category_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_post_profile_producer ON post(profile_producer_id) WHERE profile_producer_id IS NOT NULL;

-- Add comments
COMMENT ON COLUMN post.profile_type IS 'Type of profile: product or category';
COMMENT ON COLUMN post.profile_product_id IS 'Reference to clan_products table for Product Profiles';
COMMENT ON COLUMN post.profile_category_id IS 'Reference to clan_categories table for Category Profiles';
COMMENT ON COLUMN post.profile_producer_id IS 'Reference to producers table for Product Profiles';
COMMENT ON COLUMN post.profile_producer_name IS 'Producer name for display (denormalized for performance)';
COMMENT ON COLUMN post.profile_standfirst IS 'Short summary displayed in hero and used for meta description';
COMMENT ON COLUMN post.profile_explore_links IS 'JSONB object storing CTA links: {product: {url, text}, producer: {url, text}, category: {url, text}}';
COMMENT ON COLUMN post.profile_quick_facts IS 'JSONB object storing quick facts: {producer: string, material: string, category: string}';

COMMIT;










