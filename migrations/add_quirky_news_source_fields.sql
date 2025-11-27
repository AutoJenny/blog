-- Extend newsletter_snapshot_source table with fields for quirky news source configuration
-- Phase 1.2: Source Configuration Extensions

BEGIN;

ALTER TABLE newsletter_snapshot_source
ADD COLUMN IF NOT EXISTS region VARCHAR(128),
ADD COLUMN IF NOT EXISTS preferred_sections TEXT[],  -- e.g., ['community', 'lifestyle']
ADD COLUMN IF NOT EXISTS excluded_sections TEXT[],   -- e.g., ['crime', 'court']
ADD COLUMN IF NOT EXISTS access_mode VARCHAR(32) DEFAULT 'rss_only',  -- rss_only|html_list_only|api|blocked
ADD COLUMN IF NOT EXISTS discovery_notes TEXT;

COMMENT ON COLUMN newsletter_snapshot_source.region IS 'Geographic region (e.g., "Argyll & Bute", "Highlands")';
COMMENT ON COLUMN newsletter_snapshot_source.preferred_sections IS 'Array of preferred content sections to prioritize';
COMMENT ON COLUMN newsletter_snapshot_source.excluded_sections IS 'Array of sections to exclude from harvesting';
COMMENT ON COLUMN newsletter_snapshot_source.access_mode IS 'How content can be accessed: rss_only, html_list_only, api, or blocked';
COMMENT ON COLUMN newsletter_snapshot_source.discovery_notes IS 'Notes from automated discovery process';

COMMIT;

