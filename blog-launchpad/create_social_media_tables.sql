-- Create Social Media Platform Tables
-- This script creates the tables needed for social media platform specifications

-- Create platforms table
CREATE TABLE IF NOT EXISTS social_media_platforms (
    id SERIAL PRIMARY KEY,
    platform_name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'undeveloped',
    priority INTEGER DEFAULT 0,
    icon_url TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create specifications table
CREATE TABLE IF NOT EXISTS social_media_platform_specs (
    id SERIAL PRIMARY KEY,
    platform_id INTEGER REFERENCES social_media_platforms(id) ON DELETE CASCADE,
    spec_category VARCHAR(50) NOT NULL,
    spec_key VARCHAR(100) NOT NULL,
    spec_value TEXT NOT NULL,
    spec_type VARCHAR(20) DEFAULT 'text',
    is_required BOOLEAN DEFAULT FALSE,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(platform_id, spec_category, spec_key)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_specs_platform_id ON social_media_platform_specs(platform_id);
CREATE INDEX IF NOT EXISTS idx_specs_category ON social_media_platform_specs(spec_category);
CREATE INDEX IF NOT EXISTS idx_specs_platform_category ON social_media_platform_specs(platform_id, spec_category);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_social_media_platforms_updated_at 
    BEFORE UPDATE ON social_media_platforms 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_social_media_platform_specs_updated_at 
    BEFORE UPDATE ON social_media_platform_specs 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert initial platform data
INSERT INTO social_media_platforms (platform_name, display_name, status, priority, icon_url) VALUES
('facebook', 'Facebook', 'developed', 1, 'https://cdn.simpleicons.org/facebook/white'),
('twitter', 'Twitter', 'undeveloped', 2, 'https://cdn.simpleicons.org/twitter/white'),
('linkedin', 'LinkedIn', 'undeveloped', 3, 'https://cdn.simpleicons.org/linkedin/white'),
('instagram', 'Instagram', 'undeveloped', 4, 'https://cdn.simpleicons.org/instagram/white'),
('youtube', 'YouTube', 'undeveloped', 5, 'https://cdn.simpleicons.org/youtube/white'),
('tiktok', 'TikTok', 'undeveloped', 6, 'https://cdn.simpleicons.org/tiktok/white'),
('pinterest', 'Pinterest', 'undeveloped', 7, 'https://cdn.simpleicons.org/pinterest/white'),
('reddit', 'Reddit', 'undeveloped', 8, 'https://cdn.simpleicons.org/reddit/white'),
('threads', 'Threads', 'undeveloped', 9, 'https://cdn.simpleicons.org/threads/white')
ON CONFLICT (platform_name) DO NOTHING;

-- Insert Facebook specifications (25 total)
INSERT INTO social_media_platform_specs (platform_id, spec_category, spec_key, spec_value, spec_type, is_required, display_order) VALUES
-- Content Requirements (7 specs)
(1, 'content', 'content_type', 'Text posts with images', 'text', TRUE, 1),
(1, 'content', 'character_target', '≤63,206 characters', 'text', TRUE, 2),
(1, 'content', 'style_tone', 'Conversational, engaging, authentic', 'text', TRUE, 3),
(1, 'content', 'posting_frequency', '1-2 posts per day (optimal)', 'text', TRUE, 4),
(1, 'content', 'optimal_timing', '1-3 PM, 7-9 PM (local time)', 'text', TRUE, 5),
(1, 'content', 'priority_level', '1 (Highest)', 'text', TRUE, 6),
(1, 'content', 'example_cta', '"Read the full story in the link below 👇"', 'text', TRUE, 7),

-- Image Requirements (6 specs)
(1, 'image', 'dimensions', '1200×630 (landscape)', 'text', TRUE, 1),
(1, 'image', 'aspect_ratio', '1.91:1', 'text', TRUE, 2),
(1, 'image', 'format', 'JPG, PNG, GIF', 'text', TRUE, 3),
(1, 'image', 'file_size', 'Max 30MB', 'text', TRUE, 4),
(1, 'image', 'quality', 'High resolution, mobile-optimized', 'text', TRUE, 5),
(1, 'image', 'style', 'Authentic, engaging, shareable', 'text', TRUE, 6),

-- Content Adaptation (6 specs)
(1, 'adaptation', 'text_processing', 'Optimize for engagement, not truncation', 'text', TRUE, 1),
(1, 'adaptation', 'tone_adjustment', 'Authentic, conversational, community-focused', 'text', TRUE, 2),
(1, 'adaptation', 'hashtag_strategy', '2-3 relevant hashtags (Facebook prefers fewer)', 'text', TRUE, 3),
(1, 'adaptation', 'cta_generation', 'Ask questions, encourage discussion', 'text', TRUE, 4),
(1, 'adaptation', 'content_focus', 'Scottish heritage, storytelling, community', 'text', TRUE, 5),
(1, 'adaptation', 'engagement', 'Polls, questions, tag friends', 'text', TRUE, 6),

-- API Integration (6 specs)
(1, 'api', 'api_name', 'Facebook Graph API v18.0+', 'text', TRUE, 1),
(1, 'api', 'authentication', 'OAuth 2.0 with App Review', 'text', TRUE, 2),
(1, 'api', 'rate_limits', '200 posts per hour per user', 'text', TRUE, 3),
(1, 'api', 'endpoints', '/me/feed, /page/feed', 'text', TRUE, 4),
(1, 'api', 'permissions', 'pages_manage_posts, publish_to_groups', 'text', TRUE, 5),
(1, 'api', 'status', 'Requires App Review approval', 'text', TRUE, 6)
ON CONFLICT (platform_id, spec_category, spec_key) DO UPDATE SET
    spec_value = EXCLUDED.spec_value,
    updated_at = NOW();

-- Verify the data
SELECT 'Platforms created:' as info, COUNT(*) as count FROM social_media_platforms
UNION ALL
SELECT 'Facebook specifications created:', COUNT(*) FROM social_media_platform_specs WHERE platform_id = 1;
