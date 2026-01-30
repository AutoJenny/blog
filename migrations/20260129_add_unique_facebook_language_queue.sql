-- Phase C2: Partial unique index to prevent duplicate Facebook language queue rows.
-- One row per (platform, content_type, idea_id, scheduled_date) for language types.
-- Run only after confirming no existing duplicates (Phase C2 analysis reported 0).

CREATE UNIQUE INDEX IF NOT EXISTS idx_posting_queue_facebook_language_unique
ON posting_queue (platform, content_type, idea_id, scheduled_date)
WHERE platform = 'facebook'
  AND content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult')
  AND idea_id IS NOT NULL
  AND scheduled_date IS NOT NULL;

COMMENT ON INDEX idx_posting_queue_facebook_language_unique IS
  'Phase C2: Prevents duplicate language rows (same platform, content_type, idea_id, scheduled_date).';
