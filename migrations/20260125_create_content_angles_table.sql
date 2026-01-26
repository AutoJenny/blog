-- Migration: Create content_angles table
-- Date: 2026-01-25
-- Purpose: Store persistent, reusable editorial interpretations of topics (Angles layer)
-- Notes:
--   - Angles are topic-bound, not week-bound
--   - Angles can be reused across weeks, roles, and channels
--   - All fields support Phase 3 scope (Sunday Deep Dive only)
--   - No hard database constraints (per spec)

BEGIN;

-- =====================================================
-- 1. CREATE CONTENT_ANGLES TABLE
-- =====================================================
CREATE TABLE IF NOT EXISTS content_angles (
    id SERIAL PRIMARY KEY,
    
    -- Core Identity
    angle_name TEXT NOT NULL,  -- "What 'official tartan' really means (and why it's often modern)"
    angle_description TEXT,    -- Optional: Extended description of the angle
    
    -- Narrative Intent (Editorial Layer)
    narrative_intent TEXT NOT NULL,  -- What story this angle tells (editorial interpretation)
    
    -- Topic Relationship (Many-to-One)
    topic_id INTEGER NOT NULL REFERENCES kb_topics(id) ON DELETE RESTRICT,
    
    -- Source Bundle (KB Articles)
    source_article_ids INTEGER[] NOT NULL DEFAULT '{}',  -- KB articles in bundle
    source_chunk_ids INTEGER[],  -- Optional: Specific chunks (for future precision)
    
    -- Reuse Tracking (Logical, Not DB-Enforced)
    is_active BOOLEAN DEFAULT TRUE,  -- Can be deactivated without deletion
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by VARCHAR(100),  -- Optional: Track who created (for audit)
    
    -- Optional Metadata (Future Extensibility)
    recommended_roles TEXT[],  -- ['DEPTH_LONG', 'AUTHORITY_SHORT'] (suggestions only)
    suggested_channels TEXT[],  -- ['facebook', 'x'] (suggestions only)
    notes TEXT,  -- Manual editorial notes
    
    -- Lifecycle Flags
    usage_count INTEGER DEFAULT 0,  -- Track how many times used (for reuse visibility)
    last_used_at TIMESTAMP,  -- Last time this angle was used for generation
    last_used_year INTEGER,  -- Year of last use (for reuse tracking)
    last_used_week INTEGER   -- ISO week of last use (for reuse tracking)
);

-- =====================================================
-- 2. CREATE INDEXES
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_content_angles_topic_id ON content_angles(topic_id);
CREATE INDEX IF NOT EXISTS idx_content_angles_active ON content_angles(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_content_angles_source_articles ON content_angles USING GIN(source_article_ids);
CREATE INDEX IF NOT EXISTS idx_content_angles_last_used ON content_angles(last_used_year, last_used_week);

-- =====================================================
-- 3. ADD COMMENTS
-- =====================================================
COMMENT ON TABLE content_angles IS 'Reusable editorial interpretations of topics. Angles are topic-bound, not week-bound, and can be reused across roles and channels.';
COMMENT ON COLUMN content_angles.angle_name IS 'Human-readable angle name (e.g., "What official tartan really means")';
COMMENT ON COLUMN content_angles.narrative_intent IS 'Editorial interpretation: what story this angle tells about the topic';
COMMENT ON COLUMN content_angles.topic_id IS 'FK to kb_topics - each angle belongs to one topic, topics can have multiple angles';
COMMENT ON COLUMN content_angles.source_article_ids IS 'Array of KB article IDs that form the source bundle for this angle';
COMMENT ON COLUMN content_angles.is_active IS 'Can be deactivated without deletion (soft delete)';
COMMENT ON COLUMN content_angles.usage_count IS 'Track reuse frequency (for visibility, not enforcement)';
COMMENT ON COLUMN content_angles.last_used_year IS 'Year of last use (for reuse tracking across weeks)';
COMMENT ON COLUMN content_angles.last_used_week IS 'ISO week of last use (for reuse tracking)';

COMMIT;
