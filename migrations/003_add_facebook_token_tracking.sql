-- Add fields to track Facebook token refresh
-- Migration: 003_add_facebook_token_tracking.sql

-- Add tracking fields to platform_credentials table
ALTER TABLE platform_credentials 
ADD COLUMN IF NOT EXISTS last_refreshed_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS refresh_attempts INTEGER DEFAULT 0;

-- Create index for efficient querying of Facebook credentials
CREATE INDEX IF NOT EXISTS idx_platform_credentials_facebook 
ON platform_credentials(platform_id, credential_key) 
WHERE platform_id = (SELECT id FROM platforms WHERE name = 'facebook');

-- Add comment for documentation
COMMENT ON COLUMN platform_credentials.last_refreshed_at IS 'Timestamp when the credential was last refreshed';
COMMENT ON COLUMN platform_credentials.refresh_attempts IS 'Number of refresh attempts for this credential';
