-- Seed workflow_stage_entity
INSERT INTO workflow_stage_entity (name, description, stage_order) VALUES
    ('planning', 'Planning phase', 1),
    ('authoring', 'Authoring phase', 2),
    ('publishing', 'Publishing phase', 3)
ON CONFLICT (name) DO NOTHING;

-- Seed workflow_sub_stage_entity
INSERT INTO workflow_sub_stage_entity (stage_id, name, description, sub_stage_order)
SELECT s.id, v.name, v.description, v.sub_stage_order
FROM workflow_stage_entity s
CROSS JOIN (VALUES
    ('planning', 'idea', 'Initial concept', 1),
    ('planning', 'research', 'Research and fact-finding', 2),
    ('planning', 'structure', 'Outline and structure', 3),
    ('authoring', 'content', 'Content authoring', 1),
    ('authoring', 'meta_info', 'Metadata and SEO', 2),
    ('authoring', 'images', 'Image creation', 3),
    ('publishing', 'preflight', 'Pre-publication checks', 1),
    ('publishing', 'launch', 'Publishing', 2),
    ('publishing', 'syndication', 'Syndication and distribution', 3)
) AS v(stage_name, name, description, sub_stage_order)
WHERE s.name = v.stage_name
ON CONFLICT (stage_id, name) DO NOTHING;

-- Seed workflow_step_entity
INSERT INTO workflow_step_entity (name, sub_stage_id, description, step_order)
SELECT 'Main', id, 'Main step for this substage', 1
FROM workflow_sub_stage_entity
ON CONFLICT (sub_stage_id, name) DO NOTHING; 