-- Migration: Add Content Roles Framework to posting_queue
-- Date: 2026-01-23
-- Purpose: Add role-based content classification system and link to KB Topic Rota
-- Notes:
--   - This migration is strictly additive and backwards compatible
--   - All new columns are nullable to support existing rows
--   - Existing post creation processes are NOT changed by this migration
--   - Framework will be implemented incrementally

BEGIN;

-- =====================================================
-- 1. CREATE CONTENT ROLES TABLE
-- =====================================================
-- Defines the canonical content roles that every post must have
CREATE TABLE IF NOT EXISTS content_roles (
    role_code VARCHAR(50) PRIMARY KEY,
    role_name VARCHAR(100) NOT NULL,
    description TEXT,
    purpose TEXT,
    characteristics TEXT,
    hard_constraints JSONB,  -- Structured constraints for validation
    typical_length_min INTEGER,
    typical_length_max INTEGER,
    source_type VARCHAR(50),  -- 'topic_rota', 'pool', 'product_catalogue', 'reassurance_pool'
    requires_topic BOOLEAN DEFAULT FALSE,
    requires_source_page BOOLEAN DEFAULT FALSE,
    display_order INTEGER DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Insert canonical roles
INSERT INTO content_roles (role_code, role_name, description, purpose, characteristics, hard_constraints, typical_length_min, typical_length_max, source_type, requires_topic, requires_source_page, display_order) VALUES
('REASSURANCE', 'Reassurance / Permission', 
 'Reduce anxiety and friction. Give people permission to engage comfortably.',
 'Reduce anxiety and friction. Give people permission to engage comfortably.',
 'Human, patient, calm. Mentions availability, time, flexibility. Often references phone or conversation.',
 '{"forbidden_phrases": ["buy", "purchase", "order", "sale", "discount", "limited time"], "forbidden_elements": ["product_promotion", "sales_language", "technical_depth"], "required_elements": []}'::jsonb,
 50, 300, 'reassurance_pool', FALSE, FALSE, 1),

('AUTHORITY_SHORT', 'Authority / Context (Short)',
 'Establish quiet credibility through factual context or reframing.',
 'Establish quiet credibility through factual context or reframing.',
 'Declarative, calm and factual. Usually avoids first-person ("we"). Often myth-correcting or context-setting.',
 '{"forbidden_phrases": ["we", "our", "contact us", "call", "visit"], "forbidden_elements": ["reassurance_language", "service_mentions", "calls_to_action"], "required_elements": ["one_idea_only"]}'::jsonb,
 20, 150, 'topic_rota', FALSE, TRUE, 2),

('DEPTH_LONG', 'Depth / Expertise (Long Form)',
 'Demonstrate embedded knowledge and judgement.',
 'Demonstrate embedded knowledge and judgement.',
 'Narrow scope, explanatory (not summarising), structured with white space, reflective close (not a conclusion).',
 '{"forbidden_phrases": ["buy", "purchase", "order", "visit our", "contact us"], "forbidden_elements": ["selling", "service_mentions", "product_mentions"], "required_elements": ["grounded_in_source", "structured_paragraphs"]}'::jsonb,
 120, 220, 'topic_rota', TRUE, TRUE, 3),

('CULTURE', 'Culture / Texture',
 'Provide personality, rhythm, and familiarity.',
 'Provide personality, rhythm, and familiarity.',
 'Light, repeatable formats, familiar cadence.',
 '{"forbidden_phrases": ["buy", "purchase", "order"], "forbidden_elements": ["selling", "authority_claims", "deep_explanation"], "required_elements": []}'::jsonb,
 10, 100, 'pool', FALSE, FALSE, 4),

('COMMERCE', 'Commerce / Visibility',
 'Make products visible and concrete.',
 'Make products visible and concrete.',
 'Visual or descriptive, straightforward, non-educational.',
 '{"forbidden_phrases": ["heritage", "tradition", "history", "ancient"], "forbidden_elements": ["deep_heritage_explanation", "reassurance_language", "long_form_content"], "required_elements": []}'::jsonb,
 50, 200, 'product_catalogue', FALSE, FALSE, 5)

ON CONFLICT (role_code) DO UPDATE SET
    role_name = EXCLUDED.role_name,
    description = EXCLUDED.description,
    purpose = EXCLUDED.purpose,
    characteristics = EXCLUDED.characteristics,
    hard_constraints = EXCLUDED.hard_constraints,
    typical_length_min = EXCLUDED.typical_length_min,
    typical_length_max = EXCLUDED.typical_length_max,
    source_type = EXCLUDED.source_type,
    requires_topic = EXCLUDED.requires_topic,
    requires_source_page = EXCLUDED.requires_source_page,
    updated_at = CURRENT_TIMESTAMP;

-- Add comments
COMMENT ON TABLE content_roles IS 'Canonical content roles that define the purpose and constraints of social media posts. Every post must have exactly one role.';
COMMENT ON COLUMN content_roles.role_code IS 'Unique role identifier (REASSURANCE, AUTHORITY_SHORT, DEPTH_LONG, CULTURE, COMMERCE)';
COMMENT ON COLUMN content_roles.hard_constraints IS 'JSONB object containing forbidden phrases, forbidden elements, and required elements for validation';
COMMENT ON COLUMN content_roles.source_type IS 'Where content for this role comes from: topic_rota, pool, product_catalogue, reassurance_pool';
COMMENT ON COLUMN content_roles.requires_topic IS 'If TRUE, this role must reference the active weekly topic from kb_topic_rota';
COMMENT ON COLUMN content_roles.requires_source_page IS 'If TRUE, this role must reference a specific KB article/page';

-- =====================================================
-- 2. ADD ROLE AND TOPIC COLUMNS TO posting_queue
-- =====================================================
-- Add role column (references content_roles)
ALTER TABLE posting_queue
ADD COLUMN IF NOT EXISTS role VARCHAR(50) REFERENCES content_roles(role_code);

-- Add topic_id column (references kb_topics for DEPTH_LONG and other topic-bound roles)
ALTER TABLE posting_queue
ADD COLUMN IF NOT EXISTS topic_id INTEGER REFERENCES kb_topics(id);

-- Add source_page_id column (for AUTHORITY_SHORT and DEPTH_LONG that require specific KB articles)
ALTER TABLE posting_queue
ADD COLUMN IF NOT EXISTS source_page_id INTEGER;

-- Add rota_year and rota_week columns (to track which week's topic was used, even if topic changes)
ALTER TABLE posting_queue
ADD COLUMN IF NOT EXISTS rota_year INTEGER,
ADD COLUMN IF NOT EXISTS rota_week INTEGER;

-- =====================================================
-- 3. CREATE INDEXES
-- =====================================================
-- Index for querying by role
CREATE INDEX IF NOT EXISTS idx_posting_queue_role 
ON posting_queue(role) 
WHERE role IS NOT NULL;

-- Index for querying by topic
CREATE INDEX IF NOT EXISTS idx_posting_queue_topic_id 
ON posting_queue(topic_id) 
WHERE topic_id IS NOT NULL;

-- Index for querying by rota week (for tracking topic usage)
CREATE INDEX IF NOT EXISTS idx_posting_queue_rota_week 
ON posting_queue(rota_year, rota_week) 
WHERE rota_year IS NOT NULL AND rota_week IS NOT NULL;

-- Composite index for role + platform queries
CREATE INDEX IF NOT EXISTS idx_posting_queue_role_platform 
ON posting_queue(role, platform) 
WHERE role IS NOT NULL;

-- =====================================================
-- 4. ADD COMMENTS
-- =====================================================
COMMENT ON COLUMN posting_queue.role IS 'Content role (REASSURANCE, AUTHORITY_SHORT, DEPTH_LONG, CULTURE, COMMERCE). Defines the purpose and constraints of the post.';
COMMENT ON COLUMN posting_queue.topic_id IS 'Reference to kb_topics.id for topic-bound roles (e.g., DEPTH_LONG). Links post to the weekly topic from KB Topic Rota.';
COMMENT ON COLUMN posting_queue.source_page_id IS 'Reference to specific KB article/page for roles that require source material (AUTHORITY_SHORT, DEPTH_LONG).';
COMMENT ON COLUMN posting_queue.rota_year IS 'Year of the rota week when this post was generated. Used to track topic usage even if weekly topic changes mid-week.';
COMMENT ON COLUMN posting_queue.rota_week IS 'ISO week number of the rota week when this post was generated. Used to track topic usage even if weekly topic changes mid-week.';

COMMIT;
