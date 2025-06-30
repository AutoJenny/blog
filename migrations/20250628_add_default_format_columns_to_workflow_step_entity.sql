-- Migration: Add default format columns to workflow_step_entity
-- Date: 2025-06-28
-- Adds support for default input/output format templates at the step level

ALTER TABLE workflow_step_entity
ADD COLUMN default_input_format_id INTEGER REFERENCES workflow_format_template(id),
ADD COLUMN default_output_format_id INTEGER REFERENCES workflow_format_template(id); 