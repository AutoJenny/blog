-- Phase 3.1: Extend post_required_idea with metadata for diversity + curation.

ALTER TABLE post_required_idea
  ADD COLUMN IF NOT EXISTS category TEXT,
  ADD COLUMN IF NOT EXISTS rationale TEXT,
  ADD COLUMN IF NOT EXISTS source_urls JSONB,
  ADD COLUMN IF NOT EXISTS rank INT,
  ADD COLUMN IF NOT EXISTS is_selected BOOLEAN NOT NULL DEFAULT TRUE,
  ADD COLUMN IF NOT EXISTS created_by TEXT,
  ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW();

CREATE INDEX IF NOT EXISTS idx_post_required_idea_post_id_selected
  ON post_required_idea(post_id, is_selected);

CREATE INDEX IF NOT EXISTS idx_post_required_idea_post_id_category
  ON post_required_idea(post_id, category);

