-- Migration: Create post_type_config table for publication scheduling
-- Purpose: Configure publication day and time per post type (Recipe, Themed, Profile)
-- Date: 2025-01-XX

CREATE TABLE IF NOT EXISTS post_type_config (
    id SERIAL PRIMARY KEY,
    post_type VARCHAR(50) NOT NULL UNIQUE,
    default_publication_day INTEGER NOT NULL CHECK (default_publication_day BETWEEN 1 AND 7),
    default_publication_time TIME DEFAULT '14:00:00',
    timezone VARCHAR(50) DEFAULT 'Europe/London',
    is_active BOOLEAN DEFAULT TRUE,
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_post_type_config_active 
ON post_type_config(is_active) 
WHERE is_active = TRUE;

-- Insert default configurations
INSERT INTO post_type_config (post_type, default_publication_day, default_publication_time, description) VALUES
    ('themed', 3, '14:00:00', 'Regular themed blog posts - Wednesday afternoon'),
    ('recipe', 1, '10:00:00', 'Scottish Recipe Series - Monday morning'),
    ('profile', 4, '14:00:00', 'Product/Category Profiles - Thursday afternoon')
ON CONFLICT (post_type) DO UPDATE SET
    default_publication_day = EXCLUDED.default_publication_day,
    default_publication_time = EXCLUDED.default_publication_time,
    description = EXCLUDED.description,
    updated_at = NOW();

COMMENT ON TABLE post_type_config IS 'Configuration for post type publication schedules';
COMMENT ON COLUMN post_type_config.post_type IS 'Type identifier: themed, recipe, profile';
COMMENT ON COLUMN post_type_config.default_publication_day IS 'Day of week (1=Monday, 7=Sunday)';
COMMENT ON COLUMN post_type_config.default_publication_time IS 'Time of day for publication (HH:MM:SS)';
COMMENT ON COLUMN post_type_config.timezone IS 'Timezone for publication time';

