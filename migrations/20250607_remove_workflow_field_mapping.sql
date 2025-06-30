-- Remove the workflow_field_mapping table as it's now redundant
-- Field mappings are now stored in the config JSON field of workflow_step_entity

DROP TABLE IF EXISTS workflow_field_mapping; 