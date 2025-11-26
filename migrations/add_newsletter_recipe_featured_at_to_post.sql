-- Add newsletter_recipe_featured_at field to post table for tracking recipe posts used in newsletters
-- Similar to newsletter_spotlighted_at for profile posts

ALTER TABLE post ADD COLUMN IF NOT EXISTS newsletter_recipe_featured_at TIMESTAMPTZ NULL;

CREATE INDEX IF NOT EXISTS idx_post_newsletter_recipe_featured_at ON post(newsletter_recipe_featured_at);

COMMENT ON COLUMN post.newsletter_recipe_featured_at IS 'Timestamp when this recipe post was featured in a newsletter seasonal recipe block. NULL means not yet used.';

