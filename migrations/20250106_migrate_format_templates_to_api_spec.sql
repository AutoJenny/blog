-- Migration to update format template table to match API specification
-- This migration renames the table and updates the schema structure

-- Step 1: Create new table with the required schema
CREATE TABLE workflow_format_template (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    fields JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Step 2: Migrate existing data
-- Convert the existing format_spec to the new fields structure
INSERT INTO workflow_format_template (id, name, description, fields, created_at, updated_at)
SELECT 
    id,
    name,
    CASE 
        WHEN format_type = 'input' THEN 'Input format template'
        WHEN format_type = 'output' THEN 'Output format template'
        ELSE 'Format template'
    END as description,
    CASE 
        WHEN format_type = 'input' THEN 
            jsonb_build_object(
                'type', 'input',
                'schema', format_spec::jsonb
            )
        WHEN format_type = 'output' THEN 
            jsonb_build_object(
                'type', 'output',
                'schema', format_spec::jsonb
            )
        ELSE 
            jsonb_build_object(
                'type', 'unknown',
                'schema', format_spec::jsonb
            )
    END as fields,
    created_at,
    updated_at
FROM llm_format_template;

-- Step 3: Update the sequence to continue from the max ID
SELECT setval('workflow_format_template_id_seq', (SELECT MAX(id) FROM workflow_format_template));

-- Step 4: Create indexes for the new table
CREATE INDEX idx_workflow_format_template_name ON workflow_format_template(name);
CREATE INDEX idx_workflow_format_template_fields ON workflow_format_template USING GIN (fields);

-- Step 5: Add trigger to update updated_at timestamp
CREATE TRIGGER update_workflow_format_template_updated_at
    BEFORE UPDATE ON workflow_format_template
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Step 6: Update foreign key references in workflow_step_format table
-- First, drop the existing foreign key constraints
ALTER TABLE workflow_step_format 
    DROP CONSTRAINT IF EXISTS workflow_step_format_input_format_id_fkey,
    DROP CONSTRAINT IF EXISTS workflow_step_format_output_format_id_fkey;

-- Add new foreign key constraints pointing to the new table
ALTER TABLE workflow_step_format 
    ADD CONSTRAINT workflow_step_format_input_format_id_fkey 
    FOREIGN KEY (input_format_id) REFERENCES workflow_format_template(id) ON DELETE SET NULL,
    ADD CONSTRAINT workflow_step_format_output_format_id_fkey 
    FOREIGN KEY (output_format_id) REFERENCES workflow_format_template(id) ON DELETE SET NULL;

-- Step 7: Drop the old table
DROP TABLE llm_format_template;

-- Step 8: Create rollback function (for testing)
CREATE OR REPLACE FUNCTION rollback_format_migration()
RETURNS void AS $$
BEGIN
    -- This function can be used to rollback the migration if needed
    -- It would recreate the old table structure and migrate data back
    RAISE NOTICE 'Rollback function created - use with caution';
END;
$$ LANGUAGE plpgsql; 