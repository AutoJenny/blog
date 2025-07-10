-- Migration: Create workflow_step_context_config table for LLM context management UI

CREATE TABLE IF NOT EXISTS workflow_step_context_config (
    id SERIAL PRIMARY KEY,
    step_id INTEGER NOT NULL REFERENCES workflow_step_entity(id) ON DELETE CASCADE,
    config JSONB NOT NULL,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now()
);

-- Index for fast lookup by step_id
CREATE INDEX IF NOT EXISTS idx_workflow_step_context_config_step_id
    ON workflow_step_context_config (step_id); 