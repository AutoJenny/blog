-- Migration: Add Marion MacLeod as author for recipe posts
-- Purpose: Add new author and set as default for recipe posts
-- Date: 2025-01-XX

BEGIN;

-- Insert Marion MacLeod if she doesn't exist
INSERT INTO author (name, email, bio, is_active)
SELECT 
    'Marion MacLeod',
    'marion.macleod@clan.com',
    'Scottish food heritage writer and recipe developer, specializing in traditional Scottish recipes and culinary history.',
    true
WHERE NOT EXISTS (
    SELECT 1 FROM author WHERE name = 'Marion MacLeod'
);

-- Update all existing recipe posts to use Marion MacLeod as author
UPDATE post
SET author_id = (SELECT id FROM author WHERE name = 'Marion MacLeod' LIMIT 1)
WHERE author_id IS NULL 
  AND id IN (
    SELECT p.id 
    FROM post p
    LEFT JOIN taxonomy_item ti ON p.content_type_id = ti.id
    WHERE ti.display_name = 'Recipe' OR ti.slug = 'recipe'
  );

COMMIT;

