-- Create workflow_stage_entity table
CREATE TABLE IF NOT EXISTS workflow_stage_entity (
    id SERIAL PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    description TEXT,
    stage_order INTEGER NOT NULL DEFAULT 0
);

-- Insert default stages
INSERT INTO workflow_stage_entity (name, description, stage_order) VALUES
    ('planning', 'Initial planning and research phase', 1),
    ('writing', 'Content creation and development phase', 2),
    ('publishing', 'Final review and publication phase', 3);

-- Add foreign key constraints
ALTER TABLE workflow_sub_stage_entity
    ADD CONSTRAINT fk_stage_id
    FOREIGN KEY (stage_id)
    REFERENCES workflow_stage_entity(id)
    ON DELETE CASCADE; 