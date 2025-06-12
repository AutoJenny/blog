-- Add config column to workflow_step_entity
ALTER TABLE workflow_step_entity ADD COLUMN IF NOT EXISTS config JSONB DEFAULT '{}'::jsonb; 