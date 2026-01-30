-- Migration: Create heritage_library table
-- Date: 2026-01-29
-- Purpose: Heritage/clans rota — library for heritage/lineage content (separate from culture_library).
-- Notes:
--   - Same structure as culture_library for consistency.
--   - Used for heritage/clans slot in publishing rota (coding to follow).
--   - Seeding via scripts/ingest_heritage_library_csv.py.

BEGIN;

-- =====================================================
-- 1. CREATE heritage_library TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS heritage_library (
    id SERIAL PRIMARY KEY,
    category VARCHAR(100),
    title VARCHAR(500) NOT NULL,
    body_text TEXT NOT NULL,
    source_note TEXT,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- =====================================================
-- 2. INDEXES
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_heritage_library_active ON heritage_library(active) WHERE active = TRUE;
CREATE INDEX IF NOT EXISTS idx_heritage_library_category ON heritage_library(category) WHERE category IS NOT NULL;

-- =====================================================
-- 3. COMMENTS
-- =====================================================
COMMENT ON TABLE heritage_library IS 'Heritage/clans rota: Library of heritage/lineage content for Facebook posts. Separate from culture_library; used for heritage slot.';
COMMENT ON COLUMN heritage_library.category IS 'Optional category for grouping (e.g. lineage_system, diaspora_connection).';
COMMENT ON COLUMN heritage_library.title IS 'Short title for the item.';
COMMENT ON COLUMN heritage_library.body_text IS 'Main content for the post.';
COMMENT ON COLUMN heritage_library.source_note IS 'Optional attribution or source.';
COMMENT ON COLUMN heritage_library.active IS 'If FALSE, item is excluded from selection.';

COMMIT;
