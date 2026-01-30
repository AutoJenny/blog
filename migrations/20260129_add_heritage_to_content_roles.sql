-- Migration: Add HERITAGE role to content_roles (Phase H1)
-- Date: 2026-01-29
-- Purpose: Allow posting_queue.role = 'HERITAGE' (FK to content_roles.role_code).
-- Notes: HERITAGE is Thursday-only, text-led, library-driven (heritage_library). No schema change to content_roles table.

BEGIN;

INSERT INTO content_roles (role_code, role_name, description, purpose, characteristics, hard_constraints, typical_length_min, typical_length_max, source_type, requires_topic, requires_source_page, display_order) VALUES
('HERITAGE', 'Heritage / Lineage',
 'Provide personality and familiarity through heritage/clan facts (Thursday slot).',
 'Provide personality and familiarity through heritage/clan facts.',
 'Light, repeatable formats; text-led; non-promotional.',
 '{"forbidden_phrases": ["buy", "purchase", "order"], "forbidden_elements": ["selling", "authority_claims", "deep_explanation"], "required_elements": []}'::jsonb,
 10, 100, 'pool', FALSE, FALSE, 6)
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
    display_order = EXCLUDED.display_order,
    updated_at = CURRENT_TIMESTAMP;

COMMIT;
