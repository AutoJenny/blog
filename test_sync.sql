-- Test script to manually test section synchronization logic
-- This simulates what the trigger would do without actually running the trigger

-- First, let's see what we're working with
SELECT 'Current post_development.section_headings:' as info;
SELECT section_headings FROM post_development WHERE post_id = 22;

SELECT 'Current post_section records:' as info;
SELECT id, post_id, section_order, section_heading, section_description, status 
FROM post_section WHERE post_id = 22 ORDER BY section_order;

-- Now let's test the JSON parsing logic
SELECT 'Testing JSON parsing:' as info;
WITH section_data AS (
    SELECT section_headings::JSONB as data FROM post_development WHERE post_id = 22
),
parsed_sections AS (
    SELECT 
        jsonb_array_elements(data) as section_item,
        generate_series(1, jsonb_array_length(data)) as i
    FROM section_data
)
SELECT 
    i as section_order,
    CASE 
        WHEN jsonb_typeof(section_item) = 'string' THEN section_item::TEXT
        ELSE COALESCE(section_item->>'heading', section_item->>'title', 'Section ' || i)
    END as heading,
    CASE 
        WHEN jsonb_typeof(section_item) = 'string' THEN ''
        ELSE COALESCE(section_item->>'description', '')
    END as description,
    CASE 
        WHEN jsonb_typeof(section_item) = 'string' THEN 'draft'
        ELSE COALESCE(section_item->>'status', 'draft')
    END as status
FROM parsed_sections
ORDER BY i;

-- Test what would be inserted/updated
SELECT 'What would be synced to post_section:' as info;
WITH section_data AS (
    SELECT section_headings::JSONB as data FROM post_development WHERE post_id = 22
),
parsed_sections AS (
    SELECT 
        jsonb_array_elements(data) as section_item,
        generate_series(1, jsonb_array_length(data)) as i
    FROM section_data
),
new_sections AS (
    SELECT 
        i as section_order,
        CASE 
            WHEN jsonb_typeof(section_item) = 'string' THEN section_item::TEXT
            ELSE COALESCE(section_item->>'heading', section_item->>'title', 'Section ' || i)
        END as heading,
        CASE 
            WHEN jsonb_typeof(section_item) = 'string' THEN ''
            ELSE COALESCE(section_item->>'description', '')
        END as description,
        CASE 
            WHEN jsonb_typeof(section_item) = 'string' THEN 'draft'
            ELSE COALESCE(section_item->>'status', 'draft')
        END as status
    FROM parsed_sections
)
SELECT 
    ns.section_order,
    ns.heading,
    ns.description,
    ns.status,
    CASE 
        WHEN ps.id IS NULL THEN 'INSERT'
        WHEN ps.section_heading != ns.heading OR 
             COALESCE(ps.section_description, '') != ns.description OR
             COALESCE(ps.status, 'draft') != ns.status THEN 'UPDATE'
        ELSE 'NO CHANGE'
    END as action
FROM new_sections ns
LEFT JOIN post_section ps ON ps.post_id = 22 AND ps.section_order = ns.section_order
ORDER BY ns.section_order;

UPDATE post_development SET section_headings = '[{"heading": "Test Section 1", "description": "Test description", "status": "draft"}, {"heading": "Test Section 2", "description": "Another test", "status": "draft"}]' WHERE post_id = 1; 