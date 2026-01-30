-- Phase P1: Enforce "one slot = one row" at DB level.
-- Partial unique indexes per Matrix slot. Run after Phase C2 (language index may coexist).

-- Monday: one row per (platform, scheduled_date) for culture_fact
CREATE UNIQUE INDEX IF NOT EXISTS idx_posting_queue_culture_fact_slot
ON posting_queue (platform, scheduled_date)
WHERE content_type = 'culture_fact'
  AND platform = 'facebook'
  AND scheduled_date IS NOT NULL;

-- Tuesday: one row per (platform, scheduled_date) for language types
CREATE UNIQUE INDEX IF NOT EXISTS idx_posting_queue_tuesday_language_slot
ON posting_queue (platform, scheduled_date)
WHERE content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult')
  AND platform = 'facebook'
  AND scheduled_date IS NOT NULL;

-- Wednesday: one row per (platform, scheduled_date) for message
CREATE UNIQUE INDEX IF NOT EXISTS idx_posting_queue_message_slot
ON posting_queue (platform, scheduled_date)
WHERE content_type = 'message'
  AND platform = 'facebook'
  AND scheduled_date IS NOT NULL;

-- Thursday: one row per (platform, scheduled_date) for HERITAGE
CREATE UNIQUE INDEX IF NOT EXISTS idx_posting_queue_heritage_slot
ON posting_queue (platform, scheduled_date)
WHERE role = 'HERITAGE'
  AND platform = 'facebook'
  AND scheduled_date IS NOT NULL;

-- Friday: one row per (platform, scheduled_date) for AUTHORITY_SHORT
CREATE UNIQUE INDEX IF NOT EXISTS idx_posting_queue_authority_short_slot
ON posting_queue (platform, scheduled_date)
WHERE role = 'AUTHORITY_SHORT'
  AND platform = 'facebook'
  AND scheduled_date IS NOT NULL;

-- Saturday: one row per (platform, scheduled_date, scheduled_time) for product
CREATE UNIQUE INDEX IF NOT EXISTS idx_posting_queue_product_slot
ON posting_queue (platform, scheduled_date, scheduled_time)
WHERE content_type = 'product'
  AND platform = 'facebook'
  AND scheduled_date IS NOT NULL
  AND scheduled_time IS NOT NULL;

-- Sunday: one row per (platform, scheduled_date) for depth_long
CREATE UNIQUE INDEX IF NOT EXISTS idx_posting_queue_depth_long_slot
ON posting_queue (platform, scheduled_date)
WHERE content_type = 'depth_long'
  AND platform = 'facebook'
  AND scheduled_date IS NOT NULL;
