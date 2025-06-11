-- ⚠️ DEPRECATED: LEGACY WORKFLOW DATABASE SCHEMA ⚠️
-- This file is maintained for historical reference only. Do not use for active development.
-- The workflow system has been completely redesigned. For current workflow documentation, please refer to /docs/workflow/

-- Original file: migrations/20240528_create_workflow_sub_stage_entity.sql
-- Date: 2024-05-28

CREATE TABLE IF NOT EXISTS workflow_sub_stage_entity (
    id SERIAL PRIMARY KEY,
    stage_id INTEGER NOT NULL,
    name VARCHAR(64) NOT NULL,
    description TEXT,
    sub_stage_order INTEGER NOT NULL
);

-- Insert canonical substages if not already present
INSERT INTO workflow_sub_stage_entity (stage_id, name, description, sub_stage_order)
SELECT * FROM (
    VALUES
    (10, 'idea', 'Initial concept', 1),
    (10, 'research', 'Research and fact-finding', 2),
    (10, 'structure', 'Outline and structure', 3),
    (11, 'content', 'Content authoring', 1),
    (11, 'meta_info', 'Metadata and SEO', 2),
    (11, 'images', 'Image creation', 3),
    (8, 'preflight', 'Pre-publication checks', 1),
    (8, 'launch', 'Publishing', 2),
    (8, 'syndication', 'Syndication and distribution', 3)
) AS v(stage_id, name, description, sub_stage_order)
WHERE NOT EXISTS (
    SELECT 1 FROM workflow_sub_stage_entity w WHERE w.stage_id = v.stage_id AND w.name = v.name
); 