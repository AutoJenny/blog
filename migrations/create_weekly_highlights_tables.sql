-- Create weekly highlights tables for quirky news selection
-- Phase 2.2: Weekly Highlights Tables

BEGIN;

CREATE TABLE IF NOT EXISTS weekly_highlights (
    id SERIAL PRIMARY KEY,
    issue_id INTEGER REFERENCES newsletter_issue(id) ON DELETE CASCADE,
    week_start DATE NOT NULL,
    week_end DATE NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(issue_id)  -- One highlights set per issue
);

CREATE TABLE IF NOT EXISTS weekly_highlights_items (
    id SERIAL PRIMARY KEY,
    weekly_highlights_id INTEGER NOT NULL REFERENCES weekly_highlights(id) ON DELETE CASCADE,
    article_id INTEGER NOT NULL REFERENCES newsletter_source_item(id) ON DELETE CASCADE,
    position INTEGER NOT NULL,
    title_internal TEXT,
    summary_newsletter TEXT,
    summary_social TEXT,
    location_label VARCHAR(128),
    source_label VARCHAR(128),
    permalink TEXT,
    selected_image_url TEXT,
    selected_image_caption TEXT,
    selected_image_credit TEXT,
    remote_image_url TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(weekly_highlights_id, position)
);

CREATE INDEX IF NOT EXISTS idx_wh_issue ON weekly_highlights(issue_id);
CREATE INDEX IF NOT EXISTS idx_whi_highlights ON weekly_highlights_items(weekly_highlights_id);
CREATE INDEX IF NOT EXISTS idx_whi_article ON weekly_highlights_items(article_id);

COMMENT ON TABLE weekly_highlights IS 'Weekly collection of quirky news highlights linked to newsletter issue';
COMMENT ON TABLE weekly_highlights_items IS 'Individual stories selected for weekly highlights with formatted content';
COMMENT ON COLUMN weekly_highlights_items.selected_image_url IS 'Original image URL chosen by editor';
COMMENT ON COLUMN weekly_highlights_items.selected_image_caption IS 'Caption for selected image';
COMMENT ON COLUMN weekly_highlights_items.selected_image_credit IS 'Credit for selected image';
COMMENT ON COLUMN weekly_highlights_items.remote_image_url IS 'Re-served URL to avoid copyright issues';

COMMIT;

