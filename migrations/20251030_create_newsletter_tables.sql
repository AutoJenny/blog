-- Newsletter schema (PostgreSQL)
-- Files should remain concise; future alterations must use separate migrations.

BEGIN;

CREATE TABLE IF NOT EXISTS newsletter_issue (
    id SERIAL PRIMARY KEY,
    target_week VARCHAR(16) NOT NULL, -- e.g., 2025W44
    status VARCHAR(32) NOT NULL DEFAULT 'draft', -- draft|approved|sent|failed
    subject TEXT NOT NULL DEFAULT '',
    preheader TEXT NOT NULL DEFAULT '',
    last_sent_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_newsletter_issue_target_week ON newsletter_issue (target_week);
CREATE INDEX IF NOT EXISTS idx_newsletter_issue_status ON newsletter_issue (status);

CREATE TABLE IF NOT EXISTS newsletter_block (
    id SERIAL PRIMARY KEY,
    issue_id INTEGER NOT NULL REFERENCES newsletter_issue(id) ON DELETE CASCADE,
    type VARCHAR(48) NOT NULL, -- feature|snapshot|new_products|spotlight|category|evergreen|closing
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    position INTEGER NOT NULL DEFAULT 0,
    payload_json JSONB NOT NULL DEFAULT '{}',
    pinned_ids TEXT NULL, -- comma-separated ids; simple for now
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_newsletter_block_issue ON newsletter_block (issue_id);
CREATE INDEX IF NOT EXISTS idx_newsletter_block_type ON newsletter_block (type);

CREATE TABLE IF NOT EXISTS newsletter_evergreen (
    id SERIAL PRIMARY KEY,
    topic VARCHAR(128) NOT NULL,
    text TEXT NOT NULL,
    length INTEGER NOT NULL DEFAULT 0, -- word count
    season VARCHAR(32) NULL,
    region_tags VARCHAR(128) NULL,
    last_used_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_newsletter_evergreen_topic ON newsletter_evergreen (topic);

CREATE TABLE IF NOT EXISTS newsletter_category_feature (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    body_html TEXT NOT NULL,
    topic VARCHAR(128) NOT NULL,
    approved BOOLEAN NOT NULL DEFAULT FALSE,
    last_used_at TIMESTAMPTZ NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_newsletter_category_topic ON newsletter_category_feature (topic);
CREATE INDEX IF NOT EXISTS idx_newsletter_category_approved ON newsletter_category_feature (approved);

CREATE TABLE IF NOT EXISTS newsletter_snapshot_source (
    id SERIAL PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    base_url TEXT NOT NULL,
    type VARCHAR(32) NOT NULL, -- news|community|museum|other
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    api_key_ref VARCHAR(128) NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_newsletter_snapshot_enabled ON newsletter_snapshot_source (enabled);

CREATE TABLE IF NOT EXISTS newsletter_rotation (
    id SERIAL PRIMARY KEY,
    topic VARCHAR(128) NOT NULL,
    cooldown_weeks INTEGER NOT NULL DEFAULT 6,
    weight INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_newsletter_rotation_topic ON newsletter_rotation (topic);

CREATE TABLE IF NOT EXISTS newsletter_send_log (
    id SERIAL PRIMARY KEY,
    issue_id INTEGER NOT NULL REFERENCES newsletter_issue(id) ON DELETE CASCADE,
    provider VARCHAR(32) NOT NULL,
    provider_id VARCHAR(128) NOT NULL,
    sent_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    checksum VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_newsletter_send_log_issue ON newsletter_send_log (issue_id);
CREATE INDEX IF NOT EXISTS idx_newsletter_send_log_provider ON newsletter_send_log (provider);

COMMIT;




