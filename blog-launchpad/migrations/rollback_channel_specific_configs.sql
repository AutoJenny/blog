-- Rollback: Remove Channel-Specific Configuration Categories
-- Date: 2025-01-27
-- Purpose: Revert the separation of platform-wide vs channel-specific settings

-- Step 1: Remove the new channel-specific configuration categories
DELETE FROM social_media_process_configs 
WHERE config_category IN ('channel_constraints', 'channel_strategy', 'channel_adaptation');

-- Step 2: Restore the original platform specs data
-- Restore adaptation category
INSERT INTO social_media_platform_specs (platform_id, spec_category, spec_key, spec_value, spec_type, is_required, display_order) VALUES
(1, 'adaptation', 'text_processing', 'Optimize for engagement, not truncation', 'text', true, 1),
(1, 'adaptation', 'tone_adjustment', 'Authentic, conversational, community-focused', 'text', true, 2),
(1, 'adaptation', 'hashtag_strategy', '2-3 relevant hashtags (Facebook prefers fewer)', 'text', true, 3),
(1, 'adaptation', 'cta_generation', 'Ask questions, encourage discussion', 'text', true, 4),
(1, 'adaptation', 'content_focus', 'Scottish heritage, storytelling, community', 'text', true, 5),
(1, 'adaptation', 'engagement', 'Polls, questions, tag friends', 'text', true, 6);

-- Restore channel-specific content settings
INSERT INTO social_media_platform_specs (platform_id, spec_category, spec_key, spec_value, spec_type, is_required, display_order) VALUES
(1, 'content', 'style_tone', 'Conversational, engaging, authentic', 'text', true, 8),
(1, 'content', 'example_cta', '"Read the full story in the link below 👇"', 'text', true, 9);

-- Restore channel-specific image settings
INSERT INTO social_media_platform_specs (platform_id, spec_category, spec_key, spec_value, spec_type, is_required, display_order) VALUES
(1, 'image', 'style', 'Authentic, engaging, shareable', 'text', true, 7);

-- Step 3: Restore original platform spec values
UPDATE social_media_platform_specs 
SET spec_value = 'Text posts with images'
WHERE platform_id = 1 AND spec_key = 'content_type';

UPDATE social_media_platform_specs 
SET spec_value = '1200×630 (landscape)'
WHERE platform_id = 1 AND spec_key = 'dimensions';

UPDATE social_media_platform_specs 
SET spec_value = '1.91:1'
WHERE platform_id = 1 AND spec_key = 'aspect_ratio';

-- Step 4: Remove the new index
DROP INDEX IF EXISTS idx_process_configs_channel_constraints;

-- Step 5: Remove the new comments
COMMENT ON TABLE social_media_process_configs IS 'Stores configuration settings for each content conversion process';
COMMENT ON COLUMN social_media_process_configs.config_category IS 'Category of configuration: llm_prompt, constraints, style_guide, etc.';
