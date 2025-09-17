-- Migration: Create Content Process Registry Tables
-- Date: 2025-01-27
-- Purpose: Store LLM-based content conversion processes for social media syndication

-- Create social_media_content_processes table
CREATE TABLE IF NOT EXISTS social_media_content_processes (
    id SERIAL PRIMARY KEY,
    process_name VARCHAR(100) UNIQUE NOT NULL,
    display_name VARCHAR(150) NOT NULL,
    platform_id INTEGER REFERENCES social_media_platforms(id) ON DELETE CASCADE,
    content_type VARCHAR(50) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT true,
    priority INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create social_media_process_configs table
CREATE TABLE IF NOT EXISTS social_media_process_configs (
    id SERIAL PRIMARY KEY,
    process_id INTEGER REFERENCES social_media_content_processes(id) ON DELETE CASCADE,
    config_category VARCHAR(50) NOT NULL,
    config_key VARCHAR(100) NOT NULL,
    config_value TEXT NOT NULL,
    config_type VARCHAR(20) DEFAULT 'text' CHECK (config_type IN ('text', 'integer', 'json', 'boolean')),
    is_required BOOLEAN DEFAULT false,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(process_id, config_category, config_key)
);

-- Create social_media_process_executions table
CREATE TABLE IF NOT EXISTS social_media_process_executions (
    id SERIAL PRIMARY KEY,
    process_id INTEGER REFERENCES social_media_content_processes(id),
    post_id INTEGER,
    section_id INTEGER,
    input_content TEXT,
    output_content TEXT,
    execution_status VARCHAR(20) DEFAULT 'pending' CHECK (execution_status IN ('pending', 'processing', 'completed', 'failed')),
    error_message TEXT,
    processing_time_ms INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_content_processes_platform_id ON social_media_content_processes(platform_id);
CREATE INDEX IF NOT EXISTS idx_content_processes_content_type ON social_media_content_processes(content_type);
CREATE INDEX IF NOT EXISTS idx_content_processes_active ON social_media_content_processes(is_active);
CREATE INDEX IF NOT EXISTS idx_content_processes_priority ON social_media_content_processes(priority);

CREATE INDEX IF NOT EXISTS idx_process_configs_process_id ON social_media_process_configs(process_id);
CREATE INDEX IF NOT EXISTS idx_process_configs_category ON social_media_process_configs(config_category);
CREATE INDEX IF NOT EXISTS idx_process_configs_process_category ON social_media_process_configs(process_id, config_category);

CREATE INDEX IF NOT EXISTS idx_process_executions_process_id ON social_media_process_executions(process_id);
CREATE INDEX IF NOT EXISTS idx_process_executions_status ON social_media_process_executions(execution_status);
CREATE INDEX IF NOT EXISTS idx_process_executions_post_section ON social_media_process_executions(post_id, section_id);

-- Create updated_at trigger function (if not exists)
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_social_media_content_processes_updated_at 
    BEFORE UPDATE ON social_media_content_processes 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_social_media_process_configs_updated_at 
    BEFORE UPDATE ON social_media_process_configs 
    FOR ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_social_media_process_executions_updated_at 
    BEFORE UPDATE ON social_media_process_executions 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert initial process data for Facebook
INSERT INTO social_media_content_processes (process_name, display_name, platform_id, content_type, description, priority) VALUES
('facebook_feed_post', 'Facebook Feed Post', 1, 'feed_post', 'Standard Facebook text + image posts with conversational tone', 1),
('facebook_story_post', 'Facebook Story Post', 1, 'story_post', 'Facebook Stories with engaging visuals and short text', 2),
('facebook_reels_caption', 'Facebook Reels Caption', 1, 'reels_caption', 'Captions for Facebook Reels video content', 3)
ON CONFLICT (process_name) DO NOTHING;

-- Insert process configurations for Facebook Feed Post
INSERT INTO social_media_process_configs (process_id, config_category, config_key, config_value, config_type, is_required, display_order) VALUES
(1, 'llm_prompt', 'system_prompt', 'You are a social media expert specializing in Facebook content. Convert blog post sections into engaging Facebook posts that encourage interaction and sharing.', 'text', true, 1),
(1, 'llm_prompt', 'user_prompt_template', 'Convert this blog post section into a Facebook post:\n\nSection Title: {section_title}\nSection Content: {section_content}\n\nRequirements:\n- Keep under 63,206 characters\n- Use conversational, engaging tone\n- Include relevant hashtags\n- End with a call-to-action', 'text', true, 2),
(1, 'constraints', 'max_characters', '63206', 'integer', true, 1),
(1, 'constraints', 'hashtag_count', '2-3', 'text', true, 2),
(1, 'style_guide', 'tone', 'Conversational, engaging, authentic', 'text', true, 1),
(1, 'style_guide', 'hashtag_strategy', 'Use 2-3 relevant hashtags related to Scottish heritage, culture, or the specific topic', 'text', true, 2),
(1, 'style_guide', 'cta_examples', 'Read the full story in the link below 👇|Discover more about this fascinating history|Learn more about Scottish heritage', 'text', true, 3)
ON CONFLICT (process_id, config_category, config_key) DO NOTHING;

-- Insert process configurations for Facebook Story Post
INSERT INTO social_media_process_configs (process_id, config_category, config_key, config_value, config_type, is_required, display_order) VALUES
(2, 'llm_prompt', 'system_prompt', 'You are a social media expert specializing in Facebook Stories. Convert blog post sections into engaging story content with short, impactful text.', 'text', true, 1),
(2, 'llm_prompt', 'user_prompt_template', 'Convert this blog post section into a Facebook Story:\n\nSection Title: {section_title}\nSection Content: {section_content}\n\nRequirements:\n- Keep text very short and impactful\n- Use engaging, visual language\n- Include 1-2 relevant hashtags\n- End with a call-to-action', 'text', true, 2),
(2, 'constraints', 'max_characters', '100', 'integer', true, 1),
(2, 'constraints', 'hashtag_count', '1-2', 'text', true, 2),
(2, 'style_guide', 'tone', 'Visual, engaging, concise', 'text', true, 1),
(2, 'style_guide', 'hashtag_strategy', 'Use 1-2 very relevant hashtags', 'text', true, 2),
(2, 'style_guide', 'cta_examples', 'Swipe up for more|Tap for the full story|See more in our bio', 'text', true, 3)
ON CONFLICT (process_id, config_category, config_key) DO NOTHING;

-- Insert process configurations for Facebook Reels Caption
INSERT INTO social_media_process_configs (process_id, config_category, config_key, config_value, config_type, is_required, display_order) VALUES
(3, 'llm_prompt', 'system_prompt', 'You are a social media expert specializing in Facebook Reels. Convert blog post sections into engaging video captions that encourage engagement and sharing.', 'text', true, 1),
(3, 'llm_prompt', 'user_prompt_template', 'Convert this blog post section into a Facebook Reels caption:\n\nSection Title: {section_title}\nSection Content: {section_content}\n\nRequirements:\n- Keep under 150 characters\n- Use trending, engaging language\n- Include 2-3 relevant hashtags\n- End with a call-to-action', 'text', true, 2),
(3, 'constraints', 'max_characters', '150', 'integer', true, 1),
(3, 'constraints', 'hashtag_count', '2-3', 'text', true, 2),
(3, 'style_guide', 'tone', 'Trending, energetic, engaging', 'text', true, 1),
(3, 'style_guide', 'hashtag_strategy', 'Use 2-3 trending hashtags related to Scottish heritage or culture', 'text', true, 2),
(3, 'style_guide', 'cta_examples', 'Follow for more Scottish heritage content!|Like and share if you love Scottish culture!|Comment your thoughts below!', 'text', true, 3)
ON CONFLICT (process_id, config_category, config_key) DO NOTHING;

-- Add comments for documentation
COMMENT ON TABLE social_media_content_processes IS 'Stores LLM-based content conversion processes for social media platforms';
COMMENT ON TABLE social_media_process_configs IS 'Stores configuration settings for each content conversion process';
COMMENT ON TABLE social_media_process_executions IS 'Stores execution history and results of content conversion processes';

COMMENT ON COLUMN social_media_content_processes.process_name IS 'Unique identifier for the process (e.g., facebook_feed_post)';
COMMENT ON COLUMN social_media_content_processes.content_type IS 'Type of content this process generates (e.g., feed_post, story_post, reels_caption)';
COMMENT ON COLUMN social_media_content_processes.is_active IS 'Whether this process is currently available for use';
COMMENT ON COLUMN social_media_content_processes.priority IS 'Priority level for process selection (1=highest)';

COMMENT ON COLUMN social_media_process_configs.config_category IS 'Category of configuration: llm_prompt, constraints, style_guide, etc.';
COMMENT ON COLUMN social_media_process_configs.config_key IS 'Unique key for the configuration within its category';
COMMENT ON COLUMN social_media_process_configs.config_value IS 'The actual configuration value';
COMMENT ON COLUMN social_media_process_configs.config_type IS 'Data type of the configuration value';

COMMENT ON COLUMN social_media_process_executions.execution_status IS 'Current status of the process execution';
COMMENT ON COLUMN social_media_process_executions.processing_time_ms IS 'Time taken to process the content in milliseconds';
COMMENT ON COLUMN social_media_process_executions.error_message IS 'Error details if execution failed';
