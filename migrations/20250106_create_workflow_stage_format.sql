-- Migration to create workflow_stage_format table
-- This table maps format templates to workflow stages

CREATE TABLE workflow_stage_format (
    id SERIAL PRIMARY KEY,
    stage_id INTEGER NOT NULL,
    template_id INTEGER NOT NULL,
    config JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign key constraints
    FOREIGN KEY (stage_id) REFERENCES workflow_stage_entity(id) ON DELETE CASCADE,
    FOREIGN KEY (template_id) REFERENCES workflow_format_template(id) ON DELETE CASCADE,
    
    -- Ensure one format per stage
    UNIQUE(stage_id)
);

-- Create indexes for performance
CREATE INDEX idx_workflow_stage_format_stage_id ON workflow_stage_format(stage_id);
CREATE INDEX idx_workflow_stage_format_template_id ON workflow_stage_format(template_id);

-- Create trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_workflow_stage_format_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_workflow_stage_format_updated_at
    BEFORE UPDATE ON workflow_stage_format
    FOR EACH ROW
    EXECUTE FUNCTION update_workflow_stage_format_updated_at();

-- Add rollback function
CREATE OR REPLACE FUNCTION rollback_workflow_stage_format()
RETURNS void AS $$
BEGIN
    DROP TABLE IF EXISTS workflow_stage_format CASCADE;
END;
$$ LANGUAGE plpgsql; 