-- Migration: Add Facebook Product Post LLM Prompts
-- Date: 2025-01-27
-- Purpose: Add LLM prompt configuration for Facebook Product Post process

-- Insert LLM prompt configurations for Facebook Product Post (process_id = 1)
INSERT INTO process_configurations (process_id, config_category, config_key, config_value, description, display_order) VALUES
-- System prompt for product posts
(1, 'llm_prompt', 'system_prompt', 'You are a social media content specialist specializing in Facebook product marketing. Create engaging, authentic product posts that highlight features and benefits while maintaining a conversational, trustworthy tone.', 'System prompt for Facebook product posts', 1),

-- User prompt template for product posts
(1, 'llm_prompt', 'user_prompt_template', 'Create a Facebook post for the product "{product_name}" (SKU: {product_sku}). Price: {product_price}.

Product Description: {product_description}

Content Type: {content_type}
- Feature Focus: Highlight key features and what makes this product unique
- Benefit Focus: Emphasize how this product improves the customer''s life
- Story Focus: Tell an engaging, relatable story about the product

Requirements:
- Use conversational, engaging, and authentic tone
- Include a clear call-to-action
- Use EXACTLY 3 relevant hashtags at the end
- Keep post length between 150-200 characters
- Avoid the word "delve"
- Output ONLY the final post text - no explanations or commentary', 'User prompt template for Facebook product posts', 2)

ON CONFLICT (process_id, config_category, config_key) DO UPDATE SET 
    config_value = EXCLUDED.config_value,
    updated_at = CURRENT_TIMESTAMP;

-- Add comment to document the new structure
COMMENT ON TABLE process_configurations IS 'Stores configuration settings for each content conversion process, including LLM prompts, channel-specific constraints, strategies, and adaptation rules';
