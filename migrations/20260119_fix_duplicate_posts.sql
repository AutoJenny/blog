-- Migration: Fix Duplicate Language Posts
-- Date: 2026-01-19
-- Purpose: Add UNIQUE constraint to prevent duplicate language posts

-- Step 1: Clean up existing duplicates (keep oldest, delete rest)
WITH ranked_posts AS (
    SELECT id,
           idea_id,
           content_type,
           platform,
           scheduled_date,
           ROW_NUMBER() OVER (
               PARTITION BY idea_id, content_type, platform, scheduled_date
               ORDER BY created_at ASC
           ) as rn
    FROM posting_queue
    WHERE content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult')
    AND status = 'draft'
    AND idea_id IS NOT NULL
)
DELETE FROM posting_queue
WHERE id IN (
    SELECT id FROM ranked_posts WHERE rn > 1
);

-- Step 2: Add UNIQUE constraint to prevent future duplicates
-- Note: This uses a partial unique index (PostgreSQL feature)
CREATE UNIQUE INDEX IF NOT EXISTS posting_queue_unique_language_post
ON posting_queue (idea_id, content_type, platform, scheduled_date)
WHERE idea_id IS NOT NULL 
  AND content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult');

-- Step 3: Verify constraint works
-- This should return 0 (no duplicates)
SELECT COUNT(*) as remaining_duplicates
FROM (
    SELECT idea_id, content_type, platform, scheduled_date, COUNT(*) as cnt
    FROM posting_queue
    WHERE content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult')
    AND idea_id IS NOT NULL
    GROUP BY idea_id, content_type, platform, scheduled_date
    HAVING COUNT(*) > 1
) duplicates;
