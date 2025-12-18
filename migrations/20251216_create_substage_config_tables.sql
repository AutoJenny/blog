-- Migration: Create substage configuration tables
-- Date: 2025-12-16
-- Purpose: Migrate post_type_substages from Python file to database

-- Table 1: substage_metadata
-- Stores metadata for all available substages (replaces SUBSTAGE_METADATA dict)
CREATE TABLE IF NOT EXISTS substage_metadata (
    id SERIAL PRIMARY KEY,
    substage_key VARCHAR(100) NOT NULL UNIQUE,
    label VARCHAR(200) NOT NULL,
    route_function VARCHAR(255),  -- e.g., 'planning.planning_calendar_ideas'
    display_order INTEGER NOT NULL DEFAULT 999,
    stage VARCHAR(50) NOT NULL,  -- 'calendar', 'planning', 'research', 'authoring', 'imaging', 'header', 'content', 'syndication', 'publish'
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT unique_substage_key UNIQUE (substage_key)
);

CREATE INDEX IF NOT EXISTS idx_substage_metadata_stage ON substage_metadata(stage);
CREATE INDEX IF NOT EXISTS idx_substage_metadata_active ON substage_metadata(is_active);
CREATE INDEX IF NOT EXISTS idx_substage_metadata_stage_order ON substage_metadata(stage, display_order);

COMMENT ON TABLE substage_metadata IS 'Metadata for all available substages across the system';
COMMENT ON COLUMN substage_metadata.substage_key IS 'Unique identifier for the substage (e.g., "ideas", "taxonomy")';
COMMENT ON COLUMN substage_metadata.label IS 'Display label for the substage';
COMMENT ON COLUMN substage_metadata.route_function IS 'Flask route function name (e.g., "planning.planning_calendar_ideas")';
COMMENT ON COLUMN substage_metadata.stage IS 'Stage this substage belongs to (calendar, planning, research, etc.)';
COMMENT ON COLUMN substage_metadata.display_order IS 'Default display order within the stage';

-- Table 2: post_type_substages
-- Stores which substages are active for each post type and stage (replaces POST_TYPE_SUBSTAGES dict)
CREATE TABLE IF NOT EXISTS post_type_substages (
    id SERIAL PRIMARY KEY,
    post_type VARCHAR(50) NOT NULL,  -- 'themed', 'recipe', 'profile', 'generated', 'weekly_word', 'weekly_phrase', 'weekly_insult'
    stage VARCHAR(50) NOT NULL,  -- 'calendar', 'planning', 'research', 'authoring', 'imaging', 'header', 'content'
    substage_key VARCHAR(100) NOT NULL,
    display_order INTEGER NOT NULL,  -- Order within this stage for this post type
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_substage_key FOREIGN KEY (substage_key) REFERENCES substage_metadata(substage_key) ON DELETE RESTRICT,
    CONSTRAINT unique_post_type_stage_substage UNIQUE (post_type, stage, substage_key)
);

CREATE INDEX IF NOT EXISTS idx_post_type_substages_post_type ON post_type_substages(post_type);
CREATE INDEX IF NOT EXISTS idx_post_type_substages_stage ON post_type_substages(stage);
CREATE INDEX IF NOT EXISTS idx_post_type_substages_active ON post_type_substages(is_active);
CREATE INDEX IF NOT EXISTS idx_post_type_substages_lookup ON post_type_substages(post_type, stage, is_active, display_order);

COMMENT ON TABLE post_type_substages IS 'Configuration of which substages are active for each post type and stage';
COMMENT ON COLUMN post_type_substages.post_type IS 'Post type identifier (themed, recipe, profile, etc.)';
COMMENT ON COLUMN post_type_substages.display_order IS 'Display order of this substage within the stage for this post type';

-- Table 3: output_channel_substages
-- Stores channel-specific substages (extends config/output_channel_stages.py)
CREATE TABLE IF NOT EXISTS output_channel_substages (
    id SERIAL PRIMARY KEY,
    post_type VARCHAR(50) NOT NULL,
    output_channel VARCHAR(50) NOT NULL,  -- 'blog', 'facebook', 'instagram', 'twitter', 'newsletter'
    stage VARCHAR(50) NOT NULL,  -- 'content', 'imaging', 'publish', 'syndication'
    substage_key VARCHAR(100) NOT NULL,
    display_order INTEGER NOT NULL,
    use_post_type_config BOOLEAN DEFAULT FALSE,  -- If true, fall back to post_type_substages
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    CONSTRAINT fk_channel_substage_key FOREIGN KEY (substage_key) REFERENCES substage_metadata(substage_key) ON DELETE RESTRICT,
    CONSTRAINT unique_channel_substage UNIQUE (post_type, output_channel, stage, substage_key)
);

CREATE INDEX IF NOT EXISTS idx_output_channel_substages_lookup ON output_channel_substages(post_type, output_channel, stage, is_active, display_order);
CREATE INDEX IF NOT EXISTS idx_output_channel_substages_post_type_channel ON output_channel_substages(post_type, output_channel);

COMMENT ON TABLE output_channel_substages IS 'Channel-specific substage configurations (overrides post_type_substages for specific output channels)';
COMMENT ON COLUMN output_channel_substages.use_post_type_config IS 'If true, this combination should use post_type_substages instead of channel-specific config';

