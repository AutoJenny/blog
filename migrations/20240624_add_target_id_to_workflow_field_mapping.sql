-- Add target_id column to workflow_field_mapping
ALTER TABLE workflow_field_mapping ADD COLUMN target_id VARCHAR(50);

-- Initially populate target_id based on existing mappings
-- This assumes a default pattern of "input1", "input2" etc. based on order_index
UPDATE workflow_field_mapping 
SET target_id = CASE 
    WHEN accordion_type = 'inputs' THEN 'input' || order_index::text
    WHEN accordion_type = 'outputs' THEN 'output' || order_index::text
    ELSE 'field' || order_index::text
END;

-- Make target_id NOT NULL after population
ALTER TABLE workflow_field_mapping ALTER COLUMN target_id SET NOT NULL;

-- Add unique constraint to prevent duplicates
ALTER TABLE workflow_field_mapping 
ADD CONSTRAINT unique_mapping 
UNIQUE (substage_id, accordion_type, target_id); 