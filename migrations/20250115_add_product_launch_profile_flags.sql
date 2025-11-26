-- Migration: Add newsletter launch and blog profile tracking to clan_products
-- Purpose: Track which products have been launched in newsletters and profiled as blog posts
-- Date: 2025-01-15

BEGIN;

-- Add timestamp fields for tracking newsletter launches and blog profiles
ALTER TABLE clan_products 
ADD COLUMN IF NOT EXISTS newsletter_launched_at TIMESTAMPTZ NULL,
ADD COLUMN IF NOT EXISTS blog_profiled_at TIMESTAMPTZ NULL;

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_clan_products_newsletter_launched 
  ON clan_products(newsletter_launched_at) 
  WHERE newsletter_launched_at IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_clan_products_blog_profiled 
  ON clan_products(blog_profiled_at) 
  WHERE blog_profiled_at IS NOT NULL;

-- Add comments for documentation
COMMENT ON COLUMN clan_products.newsletter_launched_at IS 'Timestamp when product was first launched in a newsletter (Products Spotlight or Spotlight Product block)';
COMMENT ON COLUMN clan_products.blog_profiled_at IS 'Timestamp when product was first profiled as a blog post (post.profile_product_id)';

-- Backfill blog_profiled_at from existing published posts
UPDATE clan_products cp
SET blog_profiled_at = (
  SELECT MIN(p.created_at)
  FROM post p
  WHERE p.profile_product_id = cp.id
    AND p.status = 'published'
    AND p.created_at IS NOT NULL
)
WHERE EXISTS (
  SELECT 1 
  FROM post p 
  WHERE p.profile_product_id = cp.id 
    AND p.status = 'published'
)
AND blog_profiled_at IS NULL;

-- Note: newsletter_launched_at will be populated when products are selected for newsletter blocks
-- This requires application-level logic to update the field when a product is added to a newsletter

COMMIT;

