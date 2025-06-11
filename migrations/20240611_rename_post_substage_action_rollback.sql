-- Rollback: Revert post_workflow_step_action to post_substage_action
-- Date: 2024-06-11
-- Description: Reverts the table rename and structure changes

-- Start transaction
BEGIN;

-- Create old table structure
CREATE TABLE post_substage_action (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES post(id),
    substage VARCHAR(64) NOT NULL,
    action_id INTEGER REFERENCES llm_action(id),
    input_field VARCHAR(128),
    output_field VARCHAR(128),
    button_label TEXT,
    button_order INTEGER DEFAULT 0
);

-- Create indexes
CREATE INDEX idx_post_substage_action_post_id ON post_substage_action(post_id);
CREATE INDEX idx_post_substage_action_action_id ON post_substage_action(action_id);

-- Migrate data back
INSERT INTO post_substage_action (
    post_id,
    substage,
    action_id,
    input_field,
    output_field,
    button_label,
    button_order
)
SELECT 
    pwsa.post_id,
    wsse.name as substage,
    pwsa.action_id,
    pwsa.input_field,
    pwsa.output_field,
    pwsa.button_label,
    pwsa.button_order
FROM post_workflow_step_action pwsa
JOIN workflow_step_entity wse ON wse.id = pwsa.step_id
JOIN workflow_sub_stage_entity wsse ON wsse.id = wse.sub_stage_id;

-- Verify data migration
DO $$
DECLARE
    old_count INTEGER;
    new_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO old_count FROM post_workflow_step_action;
    SELECT COUNT(*) INTO new_count FROM post_substage_action;
    
    IF old_count != new_count THEN
        RAISE EXCEPTION 'Rollback data migration failed: count mismatch (old: %, new: %)', old_count, new_count;
    END IF;
END $$;

-- Drop new table (only if verification passed)
DROP TABLE post_workflow_step_action;

-- Commit transaction
COMMIT; 