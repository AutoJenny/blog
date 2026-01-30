-- Migration: Create culture_library table
-- Date: 2026-02-04
-- Purpose: CULTURE v1.1 — first-class library for Mon/Thu culture facts (repeat avoidance, reporting).
-- Notes:
--   - Used by posting_queue.culture_library_id for 90-day repeat checks.
--   - Seeding (250–300 items) is a separate phase.

BEGIN;

-- =====================================================
-- 1. CREATE culture_library TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS culture_library (
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
CREATE INDEX IF NOT EXISTS idx_culture_library_active ON culture_library(active) WHERE active = TRUE;
CREATE INDEX IF NOT EXISTS idx_culture_library_category ON culture_library(category) WHERE category IS NOT NULL;

-- =====================================================
-- 3. COMMENTS
-- =====================================================
COMMENT ON TABLE culture_library IS 'CULTURE v1.1: Library of culture/heritage facts for Mon/Thu Facebook posts. Used for 90-day repeat avoidance via posting_queue.culture_library_id.';
COMMENT ON COLUMN culture_library.category IS 'Optional category for grouping (e.g. heritage, tradition).';
COMMENT ON COLUMN culture_library.title IS 'Short title for the fact.';
COMMENT ON COLUMN culture_library.body_text IS 'Main content for the post.';
COMMENT ON COLUMN culture_library.source_note IS 'Optional attribution or source.';
COMMENT ON COLUMN culture_library.active IS 'If FALSE, item is excluded from selection.';

COMMIT;
