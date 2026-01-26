-- Migration: Add Content Roles Framework to posting_queue
-- Date: 2026-01-24
-- Purpose: Add role-based content classification system and link to KB Topic Rota
-- Notes:
--   - This migration is strictly additive and backwards compatible
--   - All new columns are nullable to support existing rows
--   - Existing post creation processes are NOT changed by this migration
--   - Framework is documented in docs/ and KB for reference

BEGIN;

-- =====================================================
-- 1. CREATE CONTENT ROLES TABLE
-- =====================================================
-- Defines the canonical content roles that determine post purpose/intent
CREATE TABLE IF NOT EXISTS content_roles (
    role_code VARCHAR(50) PRIMARY KEY,
    role_name VARCHAR(100) NOT NULL,
    description TEXT,
    requires_topic BOOLEAN DEFAULT FALSE,
    typical_length_min INTEGER,
    typical_length_max INTEGER,
    constraints_json JSONB,  -- Hard constraints as structured data
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert canonical content roles
INSERT INTO content_roles (role_code, role_name, description, requires_topic, typical_length_min, typical_length_max, constraints_json) VALUES
('REASSURANCE', 'Reassurance / Permission', 'Reduce anxiety and friction. Give people permission to engage comfortably.', FALSE, NULL, NULL, 
 '{"forbidden_phrases": ["buy", "purchase", "order", "sale", "discount"], "must_not_contain": ["product promotion", "sales language", "technical depth"], "characteristics": ["human", "patient", "calm"], "mentions": ["availability", "time", "flexibility", "phone", "conversation"]}'::jsonb),

('AUTHORITY_SHORT', 'Authority / Context (Short)', 'Establish quiet credibility through factual context or reframing.', TRUE, 1, 3, 
 '{"forbidden_phrases": ["we", "our", "contact us", "call us"], "must_not_contain": ["reassurance language", "service mentions", "calls to action"], "characteristics": ["declarative", "calm", "factual"], "tone": "myth-correcting or context-setting"}'::jsonb),

('DEPTH_LONG', 'Depth / Expertise (Long Form)', 'Demonstrate embedded knowledge and judgement.', TRUE, 120, 220, 
 '{"forbidden_phrases": ["buy", "purchase", "order", "contact us", "visit"], "must_not_contain": ["selling", "service mentions", "product mentions"], "must_contain": ["grounded in Clan Info Centre source material"], "characteristics": ["narrow scope", "explanatory", "structured with white space"], "close": "reflective (not a conclusion)"}'::jsonb),

('CULTURE', 'Culture / Texture', 'Provide personality, rhythm, and familiarity.', FALSE, NULL, NULL, 
 '{"forbidden_phrases": ["buy", "purchase", "order", "contact us"], "must_not_contain": ["selling", "authority claims", "deep explanation"], "characteristics": ["light", "repeatable formats", "familiar cadence"]}'::jsonb),

('COMMERCE', 'Commerce / Visibility', 'Make products visible and concrete.', FALSE, NULL, NULL, 
 '{"forbidden_phrases": ["heritage explanation", "deep explanation"], "must_not_contain": ["deep heritage explanation", "reassurance language", "long-form content"], "characteristics": ["visual or descriptive", "straightforward", "non-educational"]}'::jsonb)

ON CONFLICT (role_code) DO UPDATE SET
    role_name = EXCLUDED.role_name,
    description = EXCLUDED.description,
    requires_topic = EXCLUDED.requires_topic,
    typical_length_min = EXCLUDED.typical_length_min,
    typical_length_max = EXCLUDED.typical_length_max,
    constraints_json = EXCLUDED.constraints_json,
    updated_at = CURRENT_TIMESTAMP;

-- Add comments
COMMENT ON TABLE content_roles IS 'Canonical content roles that determine post purpose/intent. Roles are channel-agnostic, format-agnostic, and mutually exclusive.';
COMMENT ON COLUMN content_roles.role_code IS 'Unique role identifier (REASSURANCE, AUTHORITY_SHORT, DEPTH_LONG, CULTURE, COMMERCE)';
COMMENT ON COLUMN content_roles.requires_topic IS 'If TRUE, this role must reference a KB Topic Rota topic (e.g., DEPTH_LONG, AUTHORITY_SHORT)';
COMMENT ON COLUMN content_roles.constraints_json IS 'Hard constraints, forbidden phrases, and characteristics as structured JSON';

-- =====================================================
-- 2. ADD ROLE AND TOPIC_ID TO POSTING_QUEUE
-- =====================================================
-- Add role column (references content_roles)
ALTER TABLE posting_queue
ADD COLUMN IF NOT EXISTS role VARCHAR(50) REFERENCES content_roles(role_code);

-- Add topic_id column (references kb_topics for DEPTH_LONG and AUTHORITY_SHORT)
ALTER TABLE posting_queue
ADD COLUMN IF NOT EXISTS topic_id INTEGER REFERENCES kb_topics(id);

-- Add rota_year and rota_week for tracking which rota entry this post came from
ALTER TABLE posting_queue
ADD COLUMN IF NOT EXISTS rota_year INTEGER,
ADD COLUMN IF NOT EXISTS rota_week INTEGER;

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_posting_queue_role ON posting_queue(role) WHERE role IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_posting_queue_topic_id ON posting_queue(topic_id) WHERE topic_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_posting_queue_rota_year_week ON posting_queue(rota_year, rota_week) WHERE rota_year IS NOT NULL AND rota_week IS NOT NULL;

-- Composite index for role + topic queries (common pattern)
CREATE INDEX IF NOT EXISTS idx_posting_queue_role_topic ON posting_queue(role, topic_id) WHERE role IS NOT NULL AND topic_id IS NOT NULL;

-- Add comments
COMMENT ON COLUMN posting_queue.role IS 'Content role (purpose/intent): REASSURANCE, AUTHORITY_SHORT, DEPTH_LONG, CULTURE, COMMERCE. NULL for legacy posts.';
COMMENT ON COLUMN posting_queue.topic_id IS 'Foreign key to kb_topics. Required for DEPTH_LONG and AUTHORITY_SHORT roles. NULL for other roles.';
COMMENT ON COLUMN posting_queue.rota_year IS 'Year of the KB Topic Rota entry this post was generated from (ISO year)';
COMMENT ON COLUMN posting_queue.rota_week IS 'Week number of the KB Topic Rota entry this post was generated from (ISO week 1-53)';

-- =====================================================
-- 3. ADD CONSTRAINT: ROLE REQUIRES TOPIC CHECK
-- =====================================================
-- Ensure that roles requiring topics have topic_id set
-- Note: This is a soft constraint (we'll enforce in application logic)
-- We don't add a hard DB constraint because existing posts won't have roles yet

COMMIT;
