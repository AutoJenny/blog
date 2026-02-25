-- Backfill post.subtitle and post.summary from linked idea (blog slot -> idea_item_id -> calendar_ideas).
-- Run once. Updates any post linked via a blog slot to an idea so subtitle/summary come from the idea.
-- Table: post (not posts). subtitle VARCHAR(300), summary TEXT.

BEGIN;

WITH blog_slots AS (
  SELECT
    (cwi.metadata->>'post_id')::int AS post_id,
    (cwi.metadata->>'idea_item_id')::int AS idea_item_id
  FROM calendar_week_items cwi
  WHERE cwi.item_type = 'blog'
    AND cwi.metadata ? 'post_id'
    AND cwi.metadata ? 'idea_item_id'
    AND (cwi.metadata->>'post_id') ~ '^\d+$'
    AND (cwi.metadata->>'idea_item_id') ~ '^\d+$'
),
idea_text AS (
  SELECT
    bs.post_id,
    LEFT(TRIM(COALESCE(ci.idea_description, ci.idea_title, '')), 300) AS text_300
  FROM blog_slots bs
  JOIN calendar_ideas ci ON ci.id = bs.idea_item_id
  WHERE TRIM(COALESCE(ci.idea_description, ci.idea_title, '')) <> ''
),
-- Prefer one row per post (e.g. latest week item if multiple)
targets AS (
  SELECT DISTINCT ON (it.post_id) it.post_id, it.text_300
  FROM idea_text it
  ORDER BY it.post_id
)
UPDATE post p
SET
  subtitle = t.text_300,
  summary  = t.text_300,
  updated_at = NOW()
FROM targets t
WHERE p.id = t.post_id;

COMMIT;
