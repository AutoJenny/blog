-- Create workflow_field_mapping table
CREATE TABLE IF NOT EXISTS workflow_field_mapping (
    id SERIAL PRIMARY KEY,
    field_name TEXT NOT NULL,
    stage_id INTEGER REFERENCES workflow_stage_entity(id),
    substage_id INTEGER REFERENCES workflow_sub_stage_entity(id),
    order_index INTEGER DEFAULT 0,
    UNIQUE(field_name, stage_id, substage_id)
);

-- Insert initial field mappings
INSERT INTO workflow_field_mapping (field_name, stage_id, substage_id, order_index)
SELECT 'initial_concept', wse.id, wsse.id, 0
FROM workflow_stage_entity wse
JOIN workflow_sub_stage_entity wsse ON wsse.stage_id = wse.id
WHERE wse.name = 'planning' AND wsse.name = 'idea';

INSERT INTO workflow_field_mapping (field_name, stage_id, substage_id, order_index)
SELECT 'research_notes', wse.id, wsse.id, 0
FROM workflow_stage_entity wse
JOIN workflow_sub_stage_entity wsse ON wsse.stage_id = wse.id
WHERE wse.name = 'planning' AND wsse.name = 'research';

INSERT INTO workflow_field_mapping (field_name, stage_id, substage_id, order_index)
SELECT 'structure', wse.id, wsse.id, 0
FROM workflow_stage_entity wse
JOIN workflow_sub_stage_entity wsse ON wsse.stage_id = wse.id
WHERE wse.name = 'planning' AND wsse.name = 'structure'; 