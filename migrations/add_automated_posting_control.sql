-- Migration: Add Automated Posting Control
-- Date: 2026-01-XX
-- Purpose: Add system-wide control for automated posting (on/off switch)

-- Create system_config table if it doesn't exist (simple key-value store for system-wide settings)
CREATE TABLE IF NOT EXISTS system_config (
    id SERIAL PRIMARY KEY,
    config_key VARCHAR(100) UNIQUE NOT NULL,
    config_value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    updated_by VARCHAR(100)  -- Optional: track who changed it
);

-- Insert default: automated posting enabled
INSERT INTO system_config (config_key, config_value, description)
VALUES ('automated_posting_enabled', 'true', 'Master switch for automated posting to all channels. When false, scheduled_posting_executor.py will not publish any posts.')
ON CONFLICT (config_key) DO NOTHING;

-- Add index for fast lookups
CREATE INDEX IF NOT EXISTS idx_system_config_key ON system_config(config_key);

-- Add comment
COMMENT ON TABLE system_config IS 'System-wide configuration settings. Used for master switches and global settings.';
COMMENT ON COLUMN system_config.config_key IS 'Unique configuration key (e.g., automated_posting_enabled)';
COMMENT ON COLUMN system_config.config_value IS 'Configuration value (stored as text, can be boolean, number, or JSON)';
