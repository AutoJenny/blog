-- Audit: Facebook Auto-Posting Duplicates and Wrong-Day Language
-- Date: 2026-01-29
-- Usage: Run read-only against PostgreSQL. Paste or save result excerpts for the report.

-- (1) Facebook posting_queue for Thursday 2026-01-29 and nearby (27–30 Jan)
SELECT id, platform, content_type, status, scheduled_date, scheduled_time,
       idea_id, role, platform_post_id, updated_at
FROM posting_queue
WHERE platform = 'facebook'
  AND scheduled_date >= '2026-01-27' AND scheduled_date <= '2026-01-30'
  AND content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult', 'message', 'product', 'culture_fact', 'authority_short', 'depth_long')
ORDER BY scheduled_date, id;

-- (2) Counts by content_type, status, scheduled_date (same window)
SELECT content_type, status, scheduled_date, COUNT(*) AS cnt
FROM posting_queue
WHERE platform = 'facebook'
  AND scheduled_date >= '2026-01-27' AND scheduled_date <= '2026-01-30'
  AND content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult', 'message', 'product', 'culture_fact', 'authority_short', 'depth_long')
GROUP BY content_type, status, scheduled_date
ORDER BY scheduled_date, content_type, status;

-- (3) Duplicate candidates: same idea_id, content_type, scheduled_date (language) on Thursday
SELECT idea_id, content_type, scheduled_date, COUNT(*) AS cnt, array_agg(id ORDER BY id) AS queue_ids
FROM posting_queue
WHERE platform = 'facebook'
  AND content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult')
  AND scheduled_date = '2026-01-29'
GROUP BY idea_id, content_type, scheduled_date
HAVING COUNT(*) > 1
ORDER BY cnt DESC;

-- (4) Rows published (status = 'published') on 2026-01-29 or scheduled for 2026-01-29
SELECT id, content_type, idea_id, scheduled_date, platform_post_id, updated_at
FROM posting_queue
WHERE platform = 'facebook'
  AND status = 'published'
  AND (updated_at::date = '2026-01-29' OR scheduled_date = '2026-01-29')
ORDER BY id;

-- (5) Platform credentials keys only (no secret values) — for config snapshot
SELECT credential_key
FROM platform_credentials
WHERE platform_id = (SELECT id FROM platforms WHERE name = 'facebook')
  AND is_active = true
ORDER BY credential_key;
