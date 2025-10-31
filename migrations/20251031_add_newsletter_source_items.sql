-- Newsletter source aggregation and block suggestion support
BEGIN;

-- Store normalized external items for intro/snapshot (and others) selection
CREATE TABLE IF NOT EXISTS newsletter_source_item (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(128) NOT NULL, -- e.g., Met Office, BBC Scotland, Reddit
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    published_at TIMESTAMPTZ NULL,
    event_date TIMESTAMPTZ NULL,
    location TEXT NULL,
    category VARCHAR(32) NOT NULL, -- weather|event|community|news|other
    raw_data JSONB NULL,
    signal_score NUMERIC(8,3) DEFAULT 0,
    freshness_score NUMERIC(8,3) DEFAULT 0,
    combined_score NUMERIC(8,3) GENERATED ALWAYS AS (COALESCE(signal_score,0) + COALESCE(freshness_score,0)) STORED,
    cached_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_nsi_category ON newsletter_source_item (category);
CREATE INDEX IF NOT EXISTS idx_nsi_published_at ON newsletter_source_item (published_at);
CREATE INDEX IF NOT EXISTS idx_nsi_combined_score ON newsletter_source_item (combined_score DESC);

-- Optional cache/meta table for source fetch bookkeeping
CREATE TABLE IF NOT EXISTS newsletter_source_cache (
    id SERIAL PRIMARY KEY,
    source_name VARCHAR(128) NOT NULL,
    last_fetched_at TIMESTAMPTZ NULL,
    last_status VARCHAR(32) NULL,
    notes TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS uq_nsc_source_name ON newsletter_source_cache (source_name);

-- Extend newsletter_block to store suggestions and selection state
ALTER TABLE newsletter_block
    ADD COLUMN IF NOT EXISTS suggested_items JSONB NULL,
    ADD COLUMN IF NOT EXISTS auto_selected_item_id INTEGER NULL,
    ADD COLUMN IF NOT EXISTS manual_override BOOLEAN NOT NULL DEFAULT FALSE;

-- We do not hard FK auto_selected_item_id to source table to allow internal suggestions too

COMMIT;


