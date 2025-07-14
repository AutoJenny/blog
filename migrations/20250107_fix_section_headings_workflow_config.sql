-- Migration: Fix section_headings workflow configuration
-- Date: 2025-01-07
-- Purpose: Fix workflow step configuration to use correct database table/field for section_headings

-- The issue was that workflow_step_entity id 24 ("Section Headings") was configured to write to
-- post_section.section_headings, but the post_section table has a column called section_heading (singular).
-- The correct approach is to write to post_development.section_headings (plural) and let the database
-- triggers handle synchronization to post_section.

-- Fix the workflow step configuration
UPDATE workflow_step_entity 
SET config = jsonb_set(config, '{settings,llm,user_output_mapping}', '{"field": "section_headings", "table": "post_development"}') 
WHERE id = 24 AND name = 'Section Headings';

-- Verify the fix
SELECT id, name, config->'settings'->'llm'->'user_output_mapping' as output_mapping 
FROM workflow_step_entity 
WHERE id = 24; 