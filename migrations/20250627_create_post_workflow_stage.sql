-- Create post_workflow_stage table
CREATE TABLE post_workflow_stage (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES post(id),
    stage_id INTEGER REFERENCES workflow_stage_entity(id),
    status VARCHAR(32) DEFAULT 'not_started',
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    input_field VARCHAR(128),
    output_field VARCHAR(128),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(post_id, stage_id)
);

-- Add indexes for faster lookups
CREATE INDEX idx_post_workflow_stage_post ON post_workflow_stage(post_id);
CREATE INDEX idx_post_workflow_stage_stage ON post_workflow_stage(stage_id);

-- Add some initial data for testing
INSERT INTO workflow_stage_entity (name, description, stage_order)
VALUES 
    ('planning', 'Initial planning and research phase', 1),
    ('authoring', 'Content creation and editing phase', 2),
    ('publishing', 'Final review and publication phase', 3)
ON CONFLICT (name) DO NOTHING;

-- Add a test stage status for post ID 1
INSERT INTO post_workflow_stage (post_id, stage_id, status)
SELECT 1, id, 'not_started'
FROM workflow_stage_entity
WHERE name = 'planning'
ON CONFLICT DO NOTHING; 