-- Migration: Add trigger to automatically set blog_profiled_at when post is published
-- Purpose: Automatically track when products are profiled as blog posts
-- Date: 2025-01-15

BEGIN;

-- Create function to update blog_profiled_at when a post with profile_product_id is published
CREATE OR REPLACE FUNCTION update_product_blog_profiled()
RETURNS TRIGGER AS $$
BEGIN
    -- Only update if post is being published and has a profile_product_id
    IF NEW.status = 'published' 
       AND NEW.profile_product_id IS NOT NULL
       AND (OLD.status IS NULL OR OLD.status != 'published') THEN
        -- Update blog_profiled_at only if not already set (first profile only)
        UPDATE clan_products
        SET blog_profiled_at = COALESCE(NEW.created_at, NOW())
        WHERE id = NEW.profile_product_id
          AND blog_profiled_at IS NULL;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger on post table
DROP TRIGGER IF EXISTS trigger_update_product_blog_profiled ON post;
CREATE TRIGGER trigger_update_product_blog_profiled
    AFTER INSERT OR UPDATE OF status, profile_product_id ON post
    FOR EACH ROW
    EXECUTE FUNCTION update_product_blog_profiled();

COMMIT;

