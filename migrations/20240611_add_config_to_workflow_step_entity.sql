ALTER TABLE workflow_step_entity ADD COLUMN config JSONB;

-- Add an index for faster JSON operations
CREATE INDEX idx_workflow_step_entity_config ON workflow_step_entity USING GIN (config); 