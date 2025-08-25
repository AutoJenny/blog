-- Migration: Update workflow terminology to match settings page
-- Date: 2025-01-27
-- Description: Change 'meta' substage to 'post_info' and remove 'Main' step

-- Update substage name from 'meta' to 'post_info'
UPDATE workflow_sub_stage_entity 
SET name = 'post_info' 
WHERE name = 'meta';

-- Remove the 'Main' step (no longer needed)
DELETE FROM workflow_step_entity 
WHERE name = 'Main';

-- Verify changes
-- SELECT id, name, stage_id FROM workflow_sub_stage_entity WHERE stage_id = 54 ORDER BY sub_stage_order;
-- SELECT id, name, sub_stage_id FROM workflow_step_entity WHERE sub_stage_id = 21 ORDER BY step_order; 