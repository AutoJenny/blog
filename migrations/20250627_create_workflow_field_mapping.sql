-- Create workflow_field_mapping table
CREATE TABLE workflow_field_mapping (
    id SERIAL PRIMARY KEY,
    field_name TEXT NOT NULL,
    stage_id INTEGER REFERENCES workflow_stage_entity(id),
    substage_id INTEGER REFERENCES workflow_sub_stage_entity(id),
    order_index INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add index for faster lookups
CREATE INDEX idx_workflow_field_mapping_stage ON workflow_field_mapping(stage_id);
CREATE INDEX idx_workflow_field_mapping_substage ON workflow_field_mapping(substage_id);

-- Add some initial mappings for testing
INSERT INTO workflow_field_mapping (field_name, stage_id, substage_id, order_index)
SELECT 'idea_seed', id, NULL, 0
FROM workflow_stage_entity
WHERE name = 'planning'
LIMIT 1;

INSERT INTO workflow_field_mapping (field_name, stage_id, substage_id, order_index)
SELECT 'research_notes', id, NULL, 1
FROM workflow_stage_entity
WHERE name = 'planning'
LIMIT 1; 