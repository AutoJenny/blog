-- Migration: Add post_workflow_step_prompt table
-- Description: Stores prompt selections (both system and task) for each workflow step of a post

CREATE TABLE IF NOT EXISTS post_workflow_step_prompt (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES post(id) ON DELETE CASCADE,
    step_id INTEGER REFERENCES workflow_step_entity(id) ON DELETE CASCADE,
    system_prompt_id INTEGER REFERENCES llm_prompt(id) ON DELETE SET NULL,
    task_prompt_id INTEGER REFERENCES llm_prompt(id) ON DELETE SET NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(post_id, step_id)
);

-- Add indexes for performance
CREATE INDEX IF NOT EXISTS idx_post_workflow_step_prompt_post_id ON post_workflow_step_prompt(post_id);
CREATE INDEX IF NOT EXISTS idx_post_workflow_step_prompt_step_id ON post_workflow_step_prompt(step_id);

-- Add comment
COMMENT ON TABLE post_workflow_step_prompt IS 'Stores the selected system and task prompts for each workflow step of a post'; 