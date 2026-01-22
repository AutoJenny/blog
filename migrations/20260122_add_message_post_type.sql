-- Migration: Add message post type to post_type_channel_config
-- Date: 2026-01-22
-- Purpose: Add Facebook Messages post type for Saturday posts (replaces Saturday product posts)

-- Add message post type configuration for Facebook
-- Use 'syndication' as content_format (message is not in allowed list, but syndication is appropriate)
INSERT INTO post_type_channel_config (
    post_type,
    channel,
    content_format,
    publication_day,
    publication_time,
    is_primary,
    is_required,
    is_active,
    created_at,
    updated_at
)
VALUES (
    'message',
    'facebook',
    'syndication',  -- Use syndication format (message not in allowed list)
    6,  -- Saturday (1=Monday, 7=Sunday)
    '14:30:00',  -- 2:30 PM UK time
    FALSE,
    TRUE,
    TRUE,
    NOW(),
    NOW()
)
ON CONFLICT (post_type, channel, content_format) 
DO UPDATE SET
    publication_day = EXCLUDED.publication_day,
    publication_time = EXCLUDED.publication_time,
    is_active = EXCLUDED.is_active,
    updated_at = NOW();

-- Add comment
COMMENT ON COLUMN post_type_channel_config.publication_day IS 
'Day of week for publication (1=Monday, 7=Sunday). NULL means no specific day assigned.';
