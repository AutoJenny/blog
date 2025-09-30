-- Migration: Sync planning sections to post_section table
-- This creates individual post_section records for each section from post_development.sections

-- Step 1: Create post_section records for post 60 based on planning data
INSERT INTO post_section (post_id, section_order, section_heading, section_description, status)
SELECT 
    60 as post_id,
    (section_data->>'order')::integer as section_order,
    section_data->>'title' as section_heading,
    section_data->>'description' as section_description,
    'draft' as status
FROM post_development,
     jsonb_array_elements(sections::jsonb->'sections') as section_data
WHERE post_id = 60 
  AND sections IS NOT NULL
  AND sections::jsonb->'sections' IS NOT NULL
ON CONFLICT (post_id, section_order) 
DO UPDATE SET
    section_heading = EXCLUDED.section_heading,
    section_description = EXCLUDED.section_description,
    status = EXCLUDED.status;

-- Step 2: Verify the sync
SELECT 'Synced sections for post 60:' as info;
SELECT id, section_order, section_heading, status 
FROM post_section 
WHERE post_id = 60 
ORDER BY section_order;
