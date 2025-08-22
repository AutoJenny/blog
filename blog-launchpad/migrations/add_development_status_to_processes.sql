-- Migration: Add development_status field to content processes
-- Date: 2025-01-27
-- Purpose: Add development status tracking to distinguish between draft, developed, testing, and production processes

-- Add development_status column to social_media_content_processes table
ALTER TABLE social_media_content_processes 
ADD COLUMN IF NOT EXISTS development_status VARCHAR(20) DEFAULT 'draft';

-- Add comment to explain the field
COMMENT ON COLUMN social_media_content_processes.development_status IS 'Process development status: draft, developed, testing, production';

-- Update existing Facebook processes to 'developed' status
UPDATE social_media_content_processes 
SET development_status = 'developed' 
WHERE platform_id = 1 AND process_name IN ('facebook_feed_post', 'facebook_story_post', 'facebook_reels_caption', 'facebook_group_post');

-- Create index for efficient filtering by development status
CREATE INDEX IF NOT EXISTS idx_content_processes_development_status 
ON social_media_content_processes(development_status);

-- Add constraint to ensure valid status values
ALTER TABLE social_media_content_processes 
ADD CONSTRAINT chk_development_status 
CHECK (development_status IN ('draft', 'developed', 'testing', 'production'));
