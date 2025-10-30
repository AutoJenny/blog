-- Add first_published_at to post to retain the original publication date
ALTER TABLE post
ADD COLUMN IF NOT EXISTS first_published_at TIMESTAMP NULL;

-- Optional: backfill for already published posts without this set
-- UPDATE post SET first_published_at = updated_at
-- WHERE status = 'published' AND first_published_at IS NULL;


