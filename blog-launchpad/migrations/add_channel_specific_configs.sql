-- Migration: Add Channel-Specific Configuration Categories
-- Date: 2025-01-27
-- Purpose: Separate platform-wide settings from channel-specific settings by adding new configuration categories
-- and migrating channel-specific data from platform specs to process configs

-- Step 1: Add new configuration categories to existing process configs
-- This will allow us to store channel-specific settings like image dimensions, content strategies, etc.

-- Add channel-specific configuration categories for Facebook processes
-- We'll add these to the existing social_media_process_configs table

-- For Facebook Feed Post (process_id = 1)
INSERT INTO social_media_process_configs (process_id, config_category, config_key, config_value, config_type, is_required, display_order) VALUES
-- Channel-specific constraints
(1, 'channel_constraints', 'image_dimensions', '1200×630 (landscape)', 'text', true, 3),
(1, 'channel_constraints', 'aspect_ratio', '1.91:1', 'text', true, 4),
(1, 'channel_constraints', 'image_style', 'Authentic, engaging, shareable', 'text', true, 5),

-- Channel-specific strategy
(1, 'channel_strategy', 'content_focus', 'Scottish heritage, storytelling, community engagement', 'text', true, 1),
(1, 'channel_strategy', 'engagement_tactics', 'Polls, questions, tag friends', 'text', true, 2),
(1, 'channel_strategy', 'visual_style', 'Authentic, engaging, shareable', 'text', true, 3),

-- Channel-specific adaptation (migrated from platform specs)
(1, 'channel_adaptation', 'text_processing', 'Optimize for engagement, not truncation', 'text', true, 1),
(1, 'channel_adaptation', 'tone_adjustment', 'Authentic, conversational, community-focused', 'text', true, 2),
(1, 'channel_adaptation', 'hashtag_strategy', '2-3 relevant hashtags for feed posts', 'text', true, 3),
(1, 'channel_adaptation', 'cta_generation', 'Ask questions, encourage discussion', 'text', true, 4),
(1, 'channel_adaptation', 'content_focus', 'Scottish heritage, storytelling, community', 'text', true, 5),
(1, 'channel_adaptation', 'engagement', 'Polls, questions, tag friends', 'text', true, 6)
ON CONFLICT (process_id, config_category, config_key) DO NOTHING;

-- For Facebook Story Post (process_id = 2)
INSERT INTO social_media_process_configs (process_id, config_category, config_key, config_value, config_type, is_required, display_order) VALUES
-- Channel-specific constraints
(2, 'channel_constraints', 'image_dimensions', '1080×1920 (portrait)', 'text', true, 3),
(2, 'channel_constraints', 'aspect_ratio', '9:16', 'text', true, 4),
(2, 'channel_constraints', 'image_style', 'Visual, engaging, concise', 'text', true, 5),

-- Channel-specific strategy
(2, 'channel_strategy', 'content_focus', 'Visual storytelling, Scottish heritage highlights', 'text', true, 1),
(2, 'channel_strategy', 'engagement_tactics', 'Swipe up, tap for more', 'text', true, 2),
(2, 'channel_strategy', 'visual_style', 'Visual, engaging, concise', 'text', true, 3),

-- Channel-specific adaptation (migrated from platform specs)
(2, 'channel_adaptation', 'text_processing', 'Keep text very short and impactful', 'text', true, 1),
(2, 'channel_adaptation', 'tone_adjustment', 'Visual, engaging, concise', 'text', true, 2),
(2, 'channel_adaptation', 'hashtag_strategy', '1-2 very relevant hashtags for stories', 'text', true, 3),
(2, 'channel_adaptation', 'cta_generation', 'Swipe up for more, tap for the full story', 'text', true, 4),
(2, 'channel_adaptation', 'content_focus', 'Visual storytelling, Scottish heritage highlights', 'text', true, 5),
(2, 'channel_adaptation', 'engagement', 'Swipe up, tap for more', 'text', true, 6)
ON CONFLICT (process_id, config_category, config_key) DO NOTHING;

-- For Facebook Reels Caption (process_id = 3)
INSERT INTO social_media_process_configs (process_id, config_category, config_key, config_value, config_type, is_required, display_order) VALUES
-- Channel-specific constraints
(3, 'channel_constraints', 'image_dimensions', '1080×1920 (portrait)', 'text', true, 3),
(3, 'channel_constraints', 'aspect_ratio', '9:16', 'text', true, 4),
(3, 'channel_constraints', 'image_style', 'Trending, energetic, engaging', 'text', true, 5),

-- Channel-specific strategy
(3, 'channel_strategy', 'content_focus', 'Trending Scottish culture, energetic content', 'text', true, 1),
(3, 'channel_strategy', 'engagement_tactics', 'Follow, like, share, comment', 'text', true, 2),
(3, 'channel_strategy', 'visual_style', 'Trending, energetic, engaging', 'text', true, 3),

-- Channel-specific adaptation (migrated from platform specs)
(3, 'channel_adaptation', 'text_processing', 'Use trending, engaging language', 'text', true, 1),
(3, 'channel_adaptation', 'tone_adjustment', 'Trending, energetic, engaging', 'text', true, 2),
(3, 'channel_adaptation', 'hashtag_strategy', '2-3 trending hashtags for reels', 'text', true, 3),
(3, 'channel_adaptation', 'cta_generation', 'Follow for more Scottish heritage content', 'text', true, 4),
(3, 'channel_adaptation', 'content_focus', 'Trending Scottish culture, energetic content', 'text', true, 5),
(3, 'channel_adaptation', 'engagement', 'Follow, like, share, comment', 'text', true, 6)
ON CONFLICT (process_id, config_category, config_key) DO NOTHING;

-- For Facebook Group Post (process_id = 4)
INSERT INTO social_media_process_configs (process_id, config_category, config_key, config_value, config_type, is_required, display_order) VALUES
-- Channel-specific constraints
(4, 'channel_constraints', 'image_dimensions', '1200×630 (landscape)', 'text', true, 3),
(4, 'channel_constraints', 'aspect_ratio', '1.91:1', 'text', true, 4),
(4, 'channel_constraints', 'image_style', 'Community-oriented, discussion-focused', 'text', true, 5),

-- Channel-specific strategy
(4, 'channel_strategy', 'content_focus', 'Community discussion, Scottish heritage questions', 'text', true, 1),
(4, 'channel_strategy', 'engagement_tactics', 'Questions, discussion prompts, community interaction', 'text', true, 2),
(4, 'channel_strategy', 'visual_style', 'Community-oriented, discussion-focused', 'text', true, 3),

-- Channel-specific adaptation (migrated from platform specs)
(4, 'channel_adaptation', 'text_processing', 'Focus on community discussion and questions', 'text', true, 1),
(4, 'channel_adaptation', 'tone_adjustment', 'Community-oriented, discussion-focused, conversational', 'text', true, 2),
(4, 'channel_adaptation', 'hashtag_strategy', '2-3 community hashtags for groups', 'text', true, 3),
(4, 'channel_adaptation', 'cta_generation', 'What do you think about this? Share your thoughts below', 'text', true, 4),
(4, 'channel_adaptation', 'content_focus', 'Community discussion, Scottish heritage questions', 'text', true, 5),
(4, 'channel_adaptation', 'engagement', 'Questions, discussion prompts, community interaction', 'text', true, 6)
ON CONFLICT (process_id, config_category, config_key) DO NOTHING;

-- Step 2: Clean up platform specs by removing channel-specific data
-- Remove adaptation category entirely (all moved to process configs)
DELETE FROM social_media_platform_specs 
WHERE platform_id = 1 AND spec_category = 'adaptation';

-- Remove channel-specific content settings
DELETE FROM social_media_platform_specs 
WHERE platform_id = 1 AND spec_key IN ('style_tone', 'example_cta');

-- Remove channel-specific image settings
DELETE FROM social_media_platform_specs 
WHERE platform_id = 1 AND spec_key = 'style';

-- Step 3: Update remaining platform specs to be more generic and platform-wide
UPDATE social_media_platform_specs 
SET spec_value = 'Facebook supports text posts with images, videos, and various media types'
WHERE platform_id = 1 AND spec_key = 'content_type';

UPDATE social_media_platform_specs 
SET spec_value = 'Facebook supports various image formats and dimensions. See individual channel requirements for specific dimensions.'
WHERE platform_id = 1 AND spec_key = 'dimensions';

UPDATE social_media_platform_specs 
SET spec_value = 'Facebook supports multiple aspect ratios. See individual channel requirements for specific ratios.'
WHERE platform_id = 1 AND spec_key = 'aspect_ratio';

-- Step 4: Add comments to document the new structure
COMMENT ON TABLE social_media_process_configs IS 'Stores configuration settings for each content conversion process, including channel-specific constraints, strategies, and adaptation rules';

-- Add comments for new configuration categories
COMMENT ON COLUMN social_media_process_configs.config_category IS 'Category of configuration: llm_prompt, constraints, style_guide, channel_constraints, channel_strategy, channel_adaptation, etc.';

-- Step 5: Create indexes for better performance on new categories
CREATE INDEX IF NOT EXISTS idx_process_configs_channel_constraints ON social_media_process_configs(process_id, config_category) WHERE config_category IN ('channel_constraints', 'channel_strategy', 'channel_adaptation');

-- Step 6: Verify the migration
-- This query should show the new structure
-- SELECT process_name, config_category, COUNT(*) as config_count 
-- FROM social_media_process_configs pc 
-- JOIN social_media_content_processes p ON pc.process_id = p.id 
-- WHERE p.platform_id = 1 
-- GROUP BY process_name, config_category 
-- ORDER BY process_name, config_category;
