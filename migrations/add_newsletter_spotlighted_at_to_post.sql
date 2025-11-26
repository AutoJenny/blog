-- Add newsletter_spotlighted_at field to post table for tracking profile posts used in spotlight blocks
-- Similar to newsletter_launched_at in clan_products table

ALTER TABLE post ADD COLUMN IF NOT EXISTS newsletter_spotlighted_at TIMESTAMPTZ NULL;

CREATE INDEX IF NOT EXISTS idx_post_newsletter_spotlighted_at ON post(newsletter_spotlighted_at);

COMMENT ON COLUMN post.newsletter_spotlighted_at IS 'Timestamp when this profile post was featured in a newsletter spotlight block. NULL means not yet used.';

