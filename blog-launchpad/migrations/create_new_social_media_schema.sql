-- =====================================================
-- NEW SOCIAL MEDIA DATABASE SCHEMA - PHASE 1
-- Core tables for social media syndication system
-- =====================================================

-- Drop existing tables if they exist (for clean implementation)
-- NOTE: This will remove existing social media data
DROP TABLE IF EXISTS social_media_process_configs CASCADE;
DROP TABLE IF EXISTS social_media_content_processes CASCADE;
DROP TABLE IF EXISTS social_media_platform_specs CASCADE;
DROP TABLE IF EXISTS social_media_platforms CASCADE;

-- =====================================================
-- 1. PLATFORMS TABLE
-- =====================================================
CREATE TABLE platforms (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,                    -- 'facebook', 'instagram', 'twitter'
    display_name VARCHAR(100) NOT NULL,                  -- 'Facebook', 'Instagram', 'Twitter'
    description TEXT,                                     -- Platform description
    status VARCHAR(20) DEFAULT 'active',                 -- 'active', 'inactive', 'deprecated'
    priority INTEGER DEFAULT 0,                          -- Display order priority
    website_url VARCHAR(255),                            -- Platform website
    api_documentation_url VARCHAR(255),                  -- API docs URL
    logo_url VARCHAR(255),                               -- Platform logo image
    development_status VARCHAR(20) DEFAULT 'not_started', -- 'not_started', 'in_progress', 'developed', 'active', 'deprecated'
    is_featured BOOLEAN DEFAULT false,                   -- Show in featured platforms section
    menu_priority INTEGER DEFAULT 0,                     -- Order in navigation menus
    is_visible_in_ui BOOLEAN DEFAULT true,               -- Whether to show in UI
    last_activity_at TIMESTAMP,                          -- Last time platform was used/updated
    last_post_at TIMESTAMP,                              -- Last time content was posted
    last_api_call_at TIMESTAMP,                          -- Last API interaction
    total_posts_count INTEGER DEFAULT 0,                 -- Total posts made
    success_rate_percentage DECIMAL(5,2),                -- Success rate of posts
    average_response_time_ms INTEGER,                    -- Average API response time
    estimated_completion_date DATE,                      -- Target completion date
    actual_completion_date DATE,                         -- Actual completion date
    development_notes TEXT,                              -- Notes about development progress
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 2. PLATFORM CREDENTIALS TABLE
-- =====================================================
CREATE TABLE platform_credentials (
    id SERIAL PRIMARY KEY,
    platform_id INTEGER NOT NULL REFERENCES platforms(id) ON DELETE CASCADE,
    credential_type VARCHAR(50) NOT NULL,                -- 'api_key', 'access_token', 'app_secret', 'webhook_url'
    credential_key VARCHAR(100) NOT NULL,                -- 'facebook_app_id', 'instagram_access_token'
    credential_value TEXT NOT NULL,                      -- Actual credential value
    is_encrypted BOOLEAN DEFAULT false,                  -- Whether value is encrypted
    is_active BOOLEAN DEFAULT true,                      -- Whether credential is active
    expires_at TIMESTAMP,                                -- When credential expires
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform_id, credential_type, credential_key)
);

-- =====================================================
-- 3. PLATFORM CAPABILITIES TABLE
-- =====================================================
CREATE TABLE platform_capabilities (
    id SERIAL PRIMARY KEY,
    platform_id INTEGER NOT NULL REFERENCES platforms(id) ON DELETE CASCADE,
    capability_type VARCHAR(50) NOT NULL,                -- 'content', 'media', 'api', 'limits', 'features'
    capability_name VARCHAR(100) NOT NULL,               -- 'max_character_limit', 'image_formats', 'video_duration'
    capability_value TEXT NOT NULL,                      -- Actual capability value
    description TEXT,                                     -- Human-readable description
    unit VARCHAR(50),                                     -- 'pixels', 'characters', 'seconds', 'MB', 'GB'
    min_value TEXT,                                       -- Minimum value if applicable
    max_value TEXT,                                       -- Maximum value if applicable
    validation_rules JSONB,                               -- JSON validation rules
    is_active BOOLEAN DEFAULT true,
    display_order INTEGER DEFAULT 0,                     -- Order in UI
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform_id, capability_type, capability_name)
);

-- =====================================================
-- 4. CHANNEL TYPES TABLE
-- =====================================================
CREATE TABLE channel_types (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,                    -- 'feed_post', 'story_post', 'video_post', 'reels_post'
    display_name VARCHAR(100) NOT NULL,                  -- 'Feed Post', 'Story Post', 'Video Post', 'Reels Post'
    description TEXT,                                     -- Channel description
    content_type VARCHAR(50) NOT NULL,                   -- 'text', 'image', 'video', 'mixed', 'carousel'
    media_support TEXT[],                                 -- Array of supported media types
    default_priority INTEGER DEFAULT 0,                  -- Default development priority
    is_active BOOLEAN DEFAULT true,
    display_order INTEGER DEFAULT 0,                     -- Order in UI
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 5. PLATFORM CHANNEL SUPPORT TABLE
-- =====================================================
CREATE TABLE platform_channel_support (
    id SERIAL PRIMARY KEY,
    platform_id INTEGER NOT NULL REFERENCES platforms(id) ON DELETE CASCADE,
    channel_type_id INTEGER NOT NULL REFERENCES channel_types(id) ON DELETE CASCADE,
    is_supported BOOLEAN DEFAULT true,                   -- Whether platform supports this channel
    status VARCHAR(20) DEFAULT 'active',                 -- 'active', 'beta', 'deprecated', 'not_implemented'
    development_status VARCHAR(20) DEFAULT 'not_started', -- 'not_started', 'in_progress', 'developed', 'active'
    priority INTEGER DEFAULT 0,                          -- Development priority
    notes TEXT,                                          -- Additional notes about support
    estimated_completion_date DATE,                      -- Target completion date
    actual_completion_date DATE,                         -- Actual completion date
    development_notes TEXT,                              -- Notes about development progress
    last_activity_at TIMESTAMP,                          -- Last time channel was used/updated
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform_id, channel_type_id)
);

-- =====================================================
-- 6. CHANNEL REQUIREMENTS TABLE
-- =====================================================
CREATE TABLE channel_requirements (
    id SERIAL PRIMARY KEY,
    platform_id INTEGER NOT NULL REFERENCES platforms(id) ON DELETE CASCADE,
    channel_type_id INTEGER NOT NULL REFERENCES channel_types(id) ON DELETE CASCADE,
    requirement_category VARCHAR(50) NOT NULL,            -- 'dimensions', 'content', 'engagement', 'technical', 'style'
    requirement_key VARCHAR(100) NOT NULL,                -- 'image_width', 'max_hashtags', 'video_duration', 'tone'
    requirement_value TEXT NOT NULL,                      -- Actual requirement value
    description TEXT,                                     -- Human-readable description
    is_required BOOLEAN DEFAULT true,                    -- Whether this is mandatory
    validation_rules JSONB,                               -- JSON validation rules
    unit VARCHAR(50),                                     -- 'pixels', 'characters', 'seconds', 'MB'
    min_value TEXT,                                       -- Minimum value if applicable
    max_value TEXT,                                       -- Maximum value if applicable
    display_order INTEGER DEFAULT 0,                     -- Order in UI
    is_active BOOLEAN DEFAULT true,                      -- Whether requirement is active
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform_id, channel_type_id, requirement_category, requirement_key)
);

-- =====================================================
-- 7. CONTENT PROCESSES TABLE
-- =====================================================
CREATE TABLE content_processes (
    id SERIAL PRIMARY KEY,
    platform_id INTEGER NOT NULL REFERENCES platforms(id) ON DELETE CASCADE,
    channel_type_id INTEGER NOT NULL REFERENCES channel_types(id) ON DELETE CASCADE,
    process_name VARCHAR(100) NOT NULL,                  -- 'facebook_feed_post', 'instagram_story'
    display_name VARCHAR(100) NOT NULL,                  -- 'Facebook Feed Post', 'Instagram Story'
    description TEXT,                                     -- Process description
    development_status VARCHAR(20) DEFAULT 'not_started', -- 'not_started', 'in_progress', 'developed', 'active', 'deprecated'
    priority INTEGER DEFAULT 0,                          -- Development priority
    is_active BOOLEAN DEFAULT true,
    estimated_completion_date DATE,                      -- Target completion date
    actual_completion_date DATE,                         -- Actual completion date
    development_notes TEXT,                              -- Notes about development progress
    last_activity_at TIMESTAMP,                          -- Last time process was used/updated
    total_executions INTEGER DEFAULT 0,                  -- Total times process has been executed
    success_rate_percentage DECIMAL(5,2),                -- Success rate of process executions
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(platform_id, channel_type_id, process_name)
);

-- =====================================================
-- 8. REQUIREMENT CATEGORIES TABLE
-- =====================================================
CREATE TABLE requirement_categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,                    -- 'dimensions', 'content', 'engagement', 'technical', 'style'
    display_name VARCHAR(100) NOT NULL,                  -- 'Dimensions', 'Content Guidelines', 'Engagement', 'Technical', 'Style'
    description TEXT,                                     -- Category description
    display_order INTEGER DEFAULT 0,                     -- Order in UI
    color_theme VARCHAR(20) DEFAULT 'primary',           -- 'primary', 'success', 'warning', 'danger', 'info'
    icon_class VARCHAR(100),                             -- FontAwesome icon class
    is_active BOOLEAN DEFAULT true,                      -- Whether category is active
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 9. CONFIG CATEGORIES TABLE
-- =====================================================
CREATE TABLE config_categories (
    id SERIAL PRIMARY KEY, 
    name VARCHAR(50) UNIQUE NOT NULL,                    -- 'content_strategy', 'image_requirements', 'engagement_tactics'
    display_name VARCHAR(100) NOT NULL,                  -- 'Content Strategy', 'Image Requirements', 'Engagement Tactics'
    description TEXT,                                     -- Category description
    display_order INTEGER DEFAULT 0,                     -- Order in UI
    color_theme VARCHAR(20) DEFAULT 'primary',           -- 'primary', 'success', 'warning', 'danger', 'info'
    icon_class VARCHAR(100),                             -- FontAwesome icon class
    is_active BOOLEAN DEFAULT true,                      -- Whether category is active
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- 10. PROCESS CONFIGURATIONS TABLE
-- =====================================================
CREATE TABLE process_configurations (
    id SERIAL PRIMARY KEY,
    process_id INTEGER NOT NULL REFERENCES content_processes(id) ON DELETE CASCADE,
    config_category VARCHAR(50) NOT NULL,                 -- 'content_strategy', 'image_requirements', 'engagement_tactics'
    config_key VARCHAR(100) NOT NULL,                    -- 'tone_guidelines', 'hashtag_strategy', 'style_guidelines'
    config_value TEXT NOT NULL,                          -- Actual configuration value
    description TEXT,                                     -- Human-readable description
    display_order INTEGER DEFAULT 0,                     -- Order in UI
    is_active BOOLEAN DEFAULT true,                      -- Whether configuration is active
    validation_rules JSONB,                               -- JSON validation rules
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(process_id, config_category, config_key)
);

-- =====================================================
-- INDEXES FOR PERFORMANCE
-- =====================================================

-- Platform lookups
CREATE INDEX idx_platforms_name ON platforms(name);
CREATE INDEX idx_platforms_status ON platforms(status);
CREATE INDEX idx_platforms_development_status ON platforms(development_status);
CREATE INDEX idx_platforms_priority ON platforms(priority);

-- Credential lookups
CREATE INDEX idx_platform_credentials_platform_id ON platform_credentials(platform_id);
CREATE INDEX idx_platform_credentials_type ON platform_credentials(credential_type);

-- Capability lookups
CREATE INDEX idx_platform_capabilities_platform_id ON platform_capabilities(platform_id);
CREATE INDEX idx_platform_capabilities_type ON platform_capabilities(capability_type);

-- Channel support lookups
CREATE INDEX idx_platform_channel_support_platform_id ON platform_channel_support(platform_id);
CREATE INDEX idx_platform_channel_support_channel_type_id ON platform_channel_support(channel_type_id);
CREATE INDEX idx_platform_channel_support_development_status ON platform_channel_support(development_status);

-- Requirement lookups
CREATE INDEX idx_channel_requirements_platform_id ON channel_requirements(platform_id);
CREATE INDEX idx_channel_requirements_channel_type_id ON channel_requirements(channel_type_id);
CREATE INDEX idx_channel_requirements_category ON channel_requirements(requirement_category);

-- Process lookups
CREATE INDEX idx_content_processes_platform_id ON content_processes(platform_id);
CREATE INDEX idx_content_processes_channel_type_id ON content_processes(channel_type_id);
CREATE INDEX idx_content_processes_development_status ON content_processes(development_status);

-- Configuration lookups
CREATE INDEX idx_process_configurations_process_id ON process_configurations(process_id);
CREATE INDEX idx_process_configurations_category ON process_configurations(config_category);

-- =====================================================
-- COMMENTS FOR DOCUMENTATION
-- =====================================================

COMMENT ON TABLE platforms IS 'Core platform registry for all social media platforms';
COMMENT ON TABLE platform_credentials IS 'API credentials and authentication for each platform';
COMMENT ON TABLE platform_capabilities IS 'What each platform can do (generic features and limits)';
COMMENT ON TABLE channel_types IS 'Generic definitions of content channels across all platforms';
COMMENT ON TABLE platform_channel_support IS 'Which platforms support which channels and their development status';
COMMENT ON TABLE channel_requirements IS 'Specific requirements for each channel on each platform';
COMMENT ON TABLE content_processes IS 'Implementation status and metadata for content processes';
COMMENT ON TABLE requirement_categories IS 'Standardized categories for channel requirements';
COMMENT ON TABLE config_categories IS 'Standardized categories for process configurations';
COMMENT ON TABLE process_configurations IS 'Actual configuration values for content processes';

-- =====================================================
-- MIGRATION COMPLETE
-- =====================================================
