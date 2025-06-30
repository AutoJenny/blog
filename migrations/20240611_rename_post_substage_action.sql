-- Migration: Rename post_substage_action to post_workflow_step_action
-- Date: 2024-06-11
-- Description: Updates the post_substage_action table to use workflow_step_entity as the basis for LLM actions

-- Start transaction
BEGIN;

-- Create new table with updated structure
CREATE TABLE post_workflow_step_action (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES post(id),
    step_id INTEGER REFERENCES workflow_step_entity(id),
    action_id INTEGER REFERENCES llm_action(id) NULL,  -- Make nullable to handle orphaned actions
    input_field VARCHAR(128),
    output_field VARCHAR(128),
    button_label TEXT,
    button_order INTEGER DEFAULT 0
);

-- Create indexes for performance
CREATE INDEX idx_post_workflow_step_action_post_id ON post_workflow_step_action(post_id);
CREATE INDEX idx_post_workflow_step_action_step_id ON post_workflow_step_action(step_id);
CREATE INDEX idx_post_workflow_step_action_action_id ON post_workflow_step_action(action_id);

-- Migrate data from old table to new table
INSERT INTO post_workflow_step_action (
    post_id,
    step_id,
    action_id,
    input_field,
    output_field,
    button_label,
    button_order
)
SELECT 
    psa.post_id,
    wse.id as step_id,  -- Get the 'Main' step for each substage
    CASE 
        WHEN EXISTS (SELECT 1 FROM llm_action WHERE id = psa.action_id) 
        THEN psa.action_id 
        ELSE NULL 
    END as action_id,
    psa.input_field,
    psa.output_field,
    psa.button_label,
    psa.button_order
FROM post_substage_action psa
JOIN workflow_sub_stage_entity wsse ON wsse.name = psa.substage
JOIN workflow_step_entity wse ON wse.sub_stage_id = wsse.id
WHERE wse.name = 'Main';  -- Initially map to 'Main' step;

-- Verify data migration
DO $$
DECLARE
    old_count INTEGER;
    new_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO old_count FROM post_substage_action;
    SELECT COUNT(*) INTO new_count FROM post_workflow_step_action;
    
    IF old_count != new_count THEN
        RAISE EXCEPTION 'Data migration failed: count mismatch (old: %, new: %)', old_count, new_count;
    END IF;
END $$;

-- Drop old table (only if verification passed)
DROP TABLE post_substage_action;

-- Commit transaction
COMMIT; 