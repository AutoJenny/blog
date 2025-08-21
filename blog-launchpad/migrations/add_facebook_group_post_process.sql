-- Migration: Add Facebook Group Post Process
-- Date: 2025-01-27
-- Purpose: Add the fourth Facebook content process type for Group posts

-- Insert Facebook Group Post process
INSERT INTO social_media_content_processes (process_name, display_name, platform_id, content_type, description, priority) VALUES
('facebook_group_post', 'Facebook Group Post', 1, 'group_post', 'Community-focused content for Facebook Groups with discussion prompts', 4)
ON CONFLICT (process_name) DO NOTHING;

-- Insert process configurations for Facebook Group Post
INSERT INTO social_media_process_configs (process_id, config_category, config_key, config_value, config_type, is_required, display_order) VALUES
(4, 'llm_prompt', 'system_prompt', 'You are a social media expert specializing in Facebook Group content. Convert blog post sections into engaging group posts that encourage community discussion and engagement.', 'text', true, 1),
(4, 'llm_prompt', 'user_prompt_template', 'Convert this blog post section into a Facebook Group post:\n\nSection Title: {section_title}\nSection Content: {section_content}\n\nRequirements:\n- Keep under 63,206 characters\n- Use community-oriented, discussion-focused tone\n- Include relevant hashtags\n- End with a call-to-action that encourages discussion', 'text', true, 2),
(4, 'constraints', 'max_characters', '63206', 'integer', true, 1),
(4, 'constraints', 'hashtag_count', '2-3', 'text', true, 2),
(4, 'style_guide', 'tone', 'Community-oriented, discussion-focused, conversational', 'text', true, 1),
(4, 'style_guide', 'hashtag_strategy', 'Use 2-3 relevant hashtags related to Scottish heritage, culture, or the specific topic', 'text', true, 2),
(4, 'style_guide', 'cta_examples', 'What do you think about this?|Share your thoughts below|How does this relate to your experience?|What questions do you have?', 'text', true, 3)
ON CONFLICT (process_id, config_category, config_key) DO NOTHING;
