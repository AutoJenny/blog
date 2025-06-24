-- Add accordion_type column to workflow_field_mapping
ALTER TABLE workflow_field_mapping 
ADD COLUMN accordion_type VARCHAR(32) NOT NULL DEFAULT 'inputs';

-- Add a comment explaining the column
COMMENT ON COLUMN workflow_field_mapping.accordion_type IS 'Records whether this field is in the inputs or outputs accordion (inputs/outputs)';

-- Add constraint to ensure only valid values
ALTER TABLE workflow_field_mapping
ADD CONSTRAINT workflow_field_mapping_accordion_type_check 
CHECK (accordion_type IN ('inputs', 'outputs'));

-- Drop the old unique constraint if it exists
ALTER TABLE workflow_field_mapping
DROP CONSTRAINT IF EXISTS workflow_field_mapping_field_name_substage_id_key;

-- Add new unique constraint that includes accordion_type
ALTER TABLE workflow_field_mapping
ADD CONSTRAINT workflow_field_mapping_unique_field_mapping
UNIQUE (field_name, substage_id, accordion_type);

-- Update existing records based on current usage patterns
-- For now, default all to 'inputs' as that's the safer default
-- We can update specific ones to 'outputs' based on actual usage patterns
UPDATE workflow_field_mapping SET accordion_type = 'inputs'; 