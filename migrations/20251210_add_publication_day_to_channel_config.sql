-- Migration: Add publication_day column to post_type_channel_config
-- Date: 2025-12-10
-- Purpose: Enable UI-managed day assignments for publication scheduling

-- Step 1: Add publication_day column
ALTER TABLE post_type_channel_config 
ADD COLUMN IF NOT EXISTS publication_day INTEGER 
CHECK (publication_day BETWEEN 1 AND 7);

COMMENT ON COLUMN post_type_channel_config.publication_day IS 
'Day of week for publication (1=Monday, 7=Sunday). NULL means no specific day assigned.';

-- Step 2: Create index for queries
CREATE INDEX IF NOT EXISTS idx_post_type_channel_config_publication_day 
ON post_type_channel_config(publication_day) 
WHERE publication_day IS NOT NULL;

-- Step 3: Set default publication days based on current system behavior
UPDATE post_type_channel_config 
SET publication_day = CASE
    -- Blog channel defaults (from week-view layout)
    WHEN channel = 'blog' AND post_type = 'themed' THEN 1  -- Monday
    WHEN channel = 'blog' AND post_type = 'recipe' THEN 3  -- Wednesday
    WHEN channel = 'blog' AND post_type = 'profile_product' THEN 6  -- Saturday
    WHEN channel = 'blog' AND post_type = 'profile_surname' THEN 5  -- Friday
    
    -- Facebook channel defaults (for weekly content)
    WHEN channel = 'facebook' AND post_type = 'weekly_word' THEN 1  -- Monday
    WHEN channel = 'facebook' AND post_type = 'weekly_phrase' THEN 3  -- Wednesday
    WHEN channel = 'facebook' AND post_type = 'weekly_insult' THEN 5  -- Friday
    
    -- Instagram channel defaults
    WHEN channel = 'instagram' AND post_type = 'weekly_word' THEN 1  -- Monday
    
    -- Twitter channel defaults
    WHEN channel = 'twitter' AND post_type = 'weekly_phrase' THEN 3  -- Wednesday
    WHEN channel = 'twitter' AND post_type = 'weekly_insult' THEN 5  -- Friday
    
    -- Other channels can be NULL (no specific day) or set as needed
    ELSE NULL
END
WHERE publication_day IS NULL;

