DROP TABLE IF EXISTS workflow_field_mapping;

CREATE TABLE workflow_field_mapping (
    id SERIAL PRIMARY KEY,
    field_name TEXT NOT NULL,
    stage_id INTEGER NOT NULL REFERENCES workflow_stage_entity(id),
    substage_id INTEGER NOT NULL REFERENCES workflow_sub_stage_entity(id),
    order_index INTEGER NOT NULL DEFAULT 0,
    UNIQUE (field_name, substage_id)
);

-- Insert canonical field mappings if not already present
INSERT INTO workflow_field_mapping (field_name, stage_id, substage_id, order_index)
SELECT * FROM (
    VALUES
    ('idea_seed', 10, (SELECT id FROM workflow_sub_stage_entity WHERE name = 'idea'), 1),
    ('basic_idea', 10, (SELECT id FROM workflow_sub_stage_entity WHERE name = 'idea'), 2),
    ('idea_scope', 10, (SELECT id FROM workflow_sub_stage_entity WHERE name = 'idea'), 3),
    ('provisional_title', 10, (SELECT id FROM workflow_sub_stage_entity WHERE name = 'idea'), 4),
    ('research_notes', 10, (SELECT id FROM workflow_sub_stage_entity WHERE name = 'research'), 1),
    ('interesting_facts', 10, (SELECT id FROM workflow_sub_stage_entity WHERE name = 'research'), 2),
    ('topics_to_cover', 10, (SELECT id FROM workflow_sub_stage_entity WHERE name = 'research'), 3),
    ('section_planning', 10, (SELECT id FROM workflow_sub_stage_entity WHERE name = 'structure'), 1),
    ('section_headings', 10, (SELECT id FROM workflow_sub_stage_entity WHERE name = 'structure'), 2),
    ('section_order', 10, (SELECT id FROM workflow_sub_stage_entity WHERE name = 'structure'), 3),
    ('structure', 10, (SELECT id FROM workflow_sub_stage_entity WHERE name = 'structure'), 4)
) AS v(field_name, stage_id, substage_id, order_index)
WHERE NOT EXISTS (
    SELECT 1 FROM workflow_field_mapping w WHERE w.field_name = v.field_name AND w.substage_id = v.substage_id
); 