-- =====================================================
-- SEED FACEBOOK DATA FOR NEW SOCIAL MEDIA SCHEMA
-- Populates the new database structure with Facebook data
-- =====================================================

-- =====================================================
-- 1. INSERT PLATFORMS
-- =====================================================
INSERT INTO platforms (
    name, 
    display_name, 
    description, 
    status, 
    priority, 
    website_url, 
    api_documentation_url,
    development_status,
    is_featured,
    menu_priority,
    development_notes
) VALUES (
    'facebook',
    'Facebook',
    'Meta social media platform for connecting people and sharing content',
    'active',
    1,
    'https://www.facebook.com',
    'https://developers.facebook.com/docs',
    'developed',
    true,
    1,
    'Facebook platform fully implemented with feed posts, stories, and group posts'
);

-- =====================================================
-- 2. INSERT CHANNEL TYPES
-- =====================================================
INSERT INTO channel_types (
    name,
    display_name,
    description,
    content_type,
    media_support,
    default_priority,
    display_order
) VALUES 
('feed_post', 'Feed Post', 'Standard social media posts appearing in user feeds', 'mixed', ARRAY['text', 'image', 'video'], 1, 1),
('story_post', 'Story Post', 'Temporary 24-hour content with vertical format', 'mixed', ARRAY['image', 'video'], 2, 2),
('reels_post', 'Reels Post', 'Short-form vertical video content', 'video', ARRAY['video'], 3, 3),
('group_post', 'Group Post', 'Community-focused content for Facebook groups', 'mixed', ARRAY['text', 'image', 'video'], 4, 4);

-- =====================================================
-- 3. INSERT PLATFORM CAPABILITIES (Facebook-wide)
-- =====================================================
INSERT INTO platform_capabilities (
    platform_id,
    capability_type,
    capability_name,
    capability_value,
    description,
    unit,
    min_value,
    max_value,
    display_order
) VALUES 
(1, 'content', 'max_character_limit', '63206', 'Maximum characters for text posts', 'characters', NULL, '63206', 1),
(1, 'content', 'posting_frequency', 'unlimited', 'No limit on posting frequency', 'posts', NULL, NULL, 2),
(1, 'media', 'supported_image_formats', 'JPG,PNG,GIF,WebP', 'Supported image formats', 'formats', NULL, NULL, 3),
(1, 'media', 'max_file_size_mb', '30', 'Maximum file size for images and videos', 'MB', NULL, '30', 4),
(1, 'media', 'video_duration_limit', '240', 'Maximum video duration in seconds', 'seconds', NULL, '240', 5),
(1, 'api', 'rate_limit_posts_per_hour', '200', 'Maximum posts per hour per user', 'posts/hour', NULL, '200', 6),
(1, 'api', 'api_version', 'v18.0', 'Current Facebook Graph API version', 'version', NULL, NULL, 7);

-- =====================================================
-- 4. INSERT PLATFORM CHANNEL SUPPORT
-- =====================================================
INSERT INTO platform_channel_support (
    platform_id,
    channel_type_id,
    is_supported,
    status,
    development_status,
    priority,
    notes,
    development_notes
) VALUES 
(1, 1, true, 'active', 'developed', 1, 'Fully supported with all features', 'Feed posts fully implemented with image, text, and video support'),
(1, 2, true, 'active', 'developed', 2, 'Stories fully supported', 'Story posts implemented with vertical format and 24-hour expiration'),
(1, 3, true, 'active', 'developed', 3, 'Reels fully supported', 'Reels implementation complete with vertical video and music support'),
(1, 4, true, 'active', 'developed', 4, 'Group posts fully supported', 'Group posting implemented with community features');

-- =====================================================
-- 5. INSERT CHANNEL REQUIREMENTS (Facebook-specific per channel)
-- =====================================================

-- Feed Post Requirements
INSERT INTO channel_requirements (
    platform_id,
    channel_type_id,
    requirement_category,
    requirement_key,
    requirement_value,
    description,
    unit,
    min_value,
    max_value,
    display_order
) VALUES 
(1, 1, 'dimensions', 'image_width', '1200', 'Recommended image width for feed posts', 'pixels', '600', '1200', 1),
(1, 1, 'dimensions', 'image_height', '630', 'Recommended image height for feed posts', 'pixels', '315', '630', 2),
(1, 1, 'dimensions', 'aspect_ratio', '1.91:1', 'Recommended aspect ratio for feed posts', 'ratio', NULL, NULL, 3),
(1, 1, 'content', 'max_hashtags', '3', 'Recommended maximum hashtags for feed posts', 'count', '0', '3', 4),
(1, 1, 'content', 'tone_guidelines', 'Conversational, engaging, authentic', 'Recommended tone for feed posts', 'style', NULL, NULL, 5),
(1, 1, 'engagement', 'cta_strategy', 'Include clear call-to-action', 'Engagement strategy for feed posts', 'strategy', NULL, NULL, 6);

-- Story Post Requirements
INSERT INTO channel_requirements (
    platform_id,
    channel_type_id,
    requirement_category,
    requirement_key,
    requirement_value,
    description,
    unit,
    min_value,
    max_value,
    display_order
) VALUES 
(1, 2, 'dimensions', 'image_width', '1080', 'Required image width for story posts', 'pixels', '1080', '1080', 1),
(1, 2, 'dimensions', 'image_height', '1920', 'Required image height for story posts', 'pixels', '1920', '1920', 2),
(1, 2, 'dimensions', 'aspect_ratio', '9:16', 'Required aspect ratio for story posts', 'ratio', NULL, NULL, 3),
(1, 2, 'content', 'max_hashtags', '1', 'Maximum hashtags for story posts', 'count', '0', '1', 4),
(1, 2, 'content', 'tone_guidelines', 'Casual, personal, behind-the-scenes', 'Recommended tone for story posts', 'style', NULL, NULL, 5),
(1, 2, 'engagement', 'interaction_elements', 'Use stickers, polls, questions', 'Engagement strategy for story posts', 'strategy', NULL, NULL, 6);

-- Reels Post Requirements
INSERT INTO channel_requirements (
    platform_id,
    channel_type_id,
    requirement_category,
    requirement_key,
    requirement_value,
    description,
    unit,
    min_value,
    max_value,
    display_order
) VALUES 
(1, 3, 'dimensions', 'video_width', '1080', 'Required video width for reels', 'pixels', '1080', '1080', 1),
(1, 3, 'dimensions', 'video_height', '1920', 'Required video height for reels', 'pixels', '1920', '1920', 2),
(1, 3, 'dimensions', 'aspect_ratio', '9:16', 'Required aspect ratio for reels', 'ratio', NULL, NULL, 3),
(1, 3, 'content', 'video_duration', '15-60', 'Video duration range for reels', 'seconds', '15', '60', 4),
(1, 3, 'content', 'max_hashtags', '2', 'Maximum hashtags for reels', 'count', '0', '2', 5),
(1, 3, 'engagement', 'music_strategy', 'Use trending music and sounds', 'Engagement strategy for reels', 'strategy', NULL, NULL, 6);

-- Group Post Requirements
INSERT INTO channel_requirements (
    platform_id,
    channel_type_id,
    requirement_category,
    requirement_key,
    requirement_value,
    description,
    unit,
    min_value,
    max_value,
    display_order
) VALUES 
(1, 4, 'dimensions', 'image_width', '1200', 'Recommended image width for group posts', 'pixels', '600', '1200', 1),
(1, 4, 'dimensions', 'image_height', '630', 'Recommended image height for group posts', 'pixels', '315', '630', 2),
(1, 4, 'dimensions', 'aspect_ratio', '1.91:1', 'Recommended aspect ratio for group posts', 'ratio', NULL, NULL, 3),
(1, 4, 'content', 'max_hashtags', '2', 'Maximum hashtags for group posts', 'count', '0', '2', 4),
(1, 4, 'content', 'tone_guidelines', 'Community-focused, helpful, informative', 'Recommended tone for group posts', 'style', NULL, NULL, 5),
(1, 4, 'engagement', 'discussion_strategy', 'Ask questions to encourage discussion', 'Engagement strategy for group posts', 'strategy', NULL, NULL, 6);

-- =====================================================
-- 6. INSERT CONTENT PROCESSES
-- =====================================================
INSERT INTO content_processes (
    platform_id,
    channel_type_id,
    process_name,
    display_name,
    description,
    development_status,
    priority,
    development_notes
) VALUES 
(1, 1, 'facebook_feed_post', 'Facebook Feed Post', 'Standard Facebook text + image posts for user feeds', 'developed', 1, 'Fully implemented with image optimization and engagement tracking'),
(1, 2, 'facebook_story_post', 'Facebook Story Post', 'Facebook Stories with engaging visuals and interactive elements', 'developed', 2, 'Complete implementation with vertical format and 24-hour expiration'),
(1, 3, 'facebook_reels_post', 'Facebook Reels Post', 'Short-form vertical video content with music and effects', 'developed', 3, 'Full reels implementation with video processing and music integration'),
(1, 4, 'facebook_group_post', 'Facebook Group Post', 'Community-focused content for Facebook groups', 'developed', 4, 'Group posting fully implemented with community features');

-- =====================================================
-- 7. INSERT REQUIREMENT CATEGORIES
-- =====================================================
INSERT INTO requirement_categories (
    name,
    display_name,
    description,
    display_order,
    color_theme,
    icon_class
) VALUES 
('dimensions', 'Dimensions', 'Image and video size requirements', 1, 'primary', 'fas fa-expand-arrows-alt'),
('content', 'Content Guidelines', 'Text, hashtag, and tone requirements', 2, 'success', 'fas fa-file-alt'),
('engagement', 'Engagement Strategy', 'Interaction and call-to-action requirements', 3, 'warning', 'fas fa-heart'),
('technical', 'Technical Requirements', 'File format and API requirements', 4, 'info', 'fas fa-cog'),
('style', 'Style Guidelines', 'Visual and aesthetic requirements', 5, 'danger', 'fas fa-palette');

-- =====================================================
-- 8. INSERT CONFIG CATEGORIES
-- =====================================================
INSERT INTO config_categories (
    name,
    display_name,
    description,
    display_order,
    color_theme,
    icon_class
) VALUES 
('content_strategy', 'Content Strategy', 'Content planning and tone guidelines', 1, 'primary', 'fas fa-lightbulb'),
('image_requirements', 'Image Requirements', 'Visual content specifications', 2, 'success', 'fas fa-image'),
('engagement_tactics', 'Engagement Tactics', 'Interaction and response strategies', 3, 'warning', 'fas fa-users'),
('hashtag_strategy', 'Hashtag Strategy', 'Hashtag usage and optimization', 4, 'info', 'fas fa-hashtag'),
('posting_schedule', 'Posting Schedule', 'Timing and frequency guidelines', 5, 'danger', 'fas fa-clock');

-- =====================================================
-- 9. INSERT PROCESS CONFIGURATIONS
-- =====================================================

-- Feed Post Configurations
INSERT INTO process_configurations (
    process_id,
    config_category,
    config_key,
    config_value,
    description,
    display_order
) VALUES 
(1, 'content_strategy', 'tone_guidelines', 'Conversational, engaging, authentic, and relatable', 'Recommended tone for Facebook feed posts', 1),
(1, 'content_strategy', 'content_focus', 'Value-driven content that educates, entertains, or inspires', 'Content focus for feed posts', 2),
(1, 'image_requirements', 'style_guidelines', 'High-quality, authentic, and shareable images that tell a story', 'Image style recommendations for feed posts', 3),
(1, 'engagement_tactics', 'cta_strategy', 'Include clear calls-to-action that encourage likes, comments, and shares', 'Engagement strategy for feed posts', 4),
(1, 'hashtag_strategy', 'hashtag_usage', 'Use 2-3 relevant hashtags that are specific to your content and audience', 'Hashtag strategy for feed posts', 5),
(1, 'posting_schedule', 'optimal_times', 'Post between 1-4 PM on weekdays when engagement is highest', 'Optimal posting times for feed posts', 6);

-- Story Post Configurations
INSERT INTO process_configurations (
    process_id,
    config_category,
    config_key,
    config_value,
    description,
    display_order
) VALUES 
(2, 'content_strategy', 'tone_guidelines', 'Casual, personal, behind-the-scenes, and authentic', 'Recommended tone for Facebook stories', 1),
(2, 'content_strategy', 'content_focus', 'Real-time updates, behind-the-scenes content, and personal moments', 'Content focus for stories', 2),
(2, 'image_requirements', 'style_guidelines', 'Vertical format, high contrast, and text-friendly layouts', 'Image style recommendations for stories', 3),
(2, 'engagement_tactics', 'interaction_elements', 'Use stickers, polls, questions, and music to increase engagement', 'Engagement strategy for stories', 4),
(2, 'hashtag_strategy', 'hashtag_usage', 'Use 1 relevant hashtag maximum to avoid cluttering the story', 'Hashtag strategy for stories', 5),
(2, 'posting_schedule', 'optimal_times', 'Post throughout the day with 3-5 stories per day for maximum visibility', 'Optimal posting frequency for stories', 6);

-- Reels Post Configurations
INSERT INTO process_configurations (
    process_id,
    config_category,
    config_key,
    config_value,
    description,
    display_order
) VALUES 
(3, 'content_strategy', 'tone_guidelines', 'Trendy, entertaining, and visually engaging with quick hooks', 'Recommended tone for Facebook reels', 1),
(3, 'content_strategy', 'content_focus', 'Short-form video content that entertains, educates, or inspires in 15-60 seconds', 'Content focus for reels', 2),
(3, 'image_requirements', 'style_guidelines', 'Vertical video format with high-quality visuals and smooth transitions', 'Video style recommendations for reels', 3),
(3, 'engagement_tactics', 'music_strategy', 'Use trending music and sounds to increase discoverability and engagement', 'Engagement strategy for reels', 4),
(3, 'hashtag_strategy', 'hashtag_usage', 'Use 2 relevant hashtags that are trending in your niche', 'Hashtag strategy for reels', 5),
(3, 'posting_schedule', 'optimal_times', 'Post 2-3 reels per day during peak hours (12-3 PM and 7-9 PM)', 'Optimal posting schedule for reels', 6);

-- Group Post Configurations
INSERT INTO process_configurations (
    process_id,
    config_category,
    config_key,
    config_value,
    description,
    display_order
) VALUES 
(4, 'content_strategy', 'tone_guidelines', 'Community-focused, helpful, informative, and respectful', 'Recommended tone for Facebook group posts', 1),
(4, 'content_strategy', 'content_focus', 'Value-driven content that helps group members and encourages discussion', 'Content focus for group posts', 2),
(4, 'image_requirements', 'style_guidelines', 'Clear, informative images that support the text content and group discussion', 'Image style recommendations for group posts', 3),
(4, 'engagement_tactics', 'discussion_strategy', 'Ask questions, share insights, and encourage group members to participate', 'Engagement strategy for group posts', 4),
(4, 'hashtag_strategy', 'hashtag_usage', 'Use 1-2 relevant hashtags that are specific to the group topic', 'Hashtag strategy for group posts', 5),
(4, 'posting_schedule', 'optimal_times', 'Post during active group hours, typically 9 AM-6 PM on weekdays', 'Optimal posting times for group posts', 6);

-- =====================================================
-- DATA SEEDING COMPLETE
-- =====================================================

