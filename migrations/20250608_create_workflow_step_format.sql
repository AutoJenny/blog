-- Create workflow_step_format table
CREATE TABLE workflow_step_format (
    id SERIAL PRIMARY KEY,
    step_id INTEGER NOT NULL REFERENCES workflow_step_entity(id) ON DELETE CASCADE,
    post_id INTEGER NOT NULL REFERENCES post(id) ON DELETE CASCADE,
    input_format_id INTEGER REFERENCES llm_format_template(id) ON DELETE SET NULL,
    output_format_id INTEGER REFERENCES llm_format_template(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Set proper ownership
ALTER TABLE workflow_step_format OWNER TO nickfiddes;

-- Add indexes
CREATE INDEX idx_workflow_step_format_step ON workflow_step_format(step_id);
CREATE INDEX idx_workflow_step_format_post ON workflow_step_format(post_id);
CREATE INDEX idx_workflow_step_format_input ON workflow_step_format(input_format_id);
CREATE INDEX idx_workflow_step_format_output ON workflow_step_format(output_format_id);

-- Add unique constraint to prevent multiple format configs for same step/post
CREATE UNIQUE INDEX idx_workflow_step_format_unique ON workflow_step_format(step_id, post_id);

-- Rollback
-- DROP TABLE IF EXISTS workflow_step_format; 