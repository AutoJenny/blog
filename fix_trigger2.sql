-- Drop existing function and trigger
DROP FUNCTION IF EXISTS sync_sections_to_section_headings() CASCADE;

-- Create corrected trigger function
CREATE OR REPLACE FUNCTION sync_sections_to_section_headings() 
RETURNS TRIGGER AS $$
DECLARE 
    sections_json JSONB;
    section_record RECORD;
BEGIN
    -- Build JSON array from current sections
    sections_json := '[]'::JSONB;

    FOR section_record IN
        SELECT section_order, section_heading, section_description, status
        FROM post_section
        WHERE post_id = COALESCE(NEW.post_id, OLD.post_id)
        ORDER BY section_order
    LOOP
        sections_json := sections_json || jsonb_build_object(
            'order', section_record.section_order,
            'heading', section_record.section_heading,
            'description', COALESCE(section_record.section_description, ''),
            'status', COALESCE(section_record.status, 'draft')
        );
    END LOOP;

    -- Update post_development
    UPDATE post_development
    SET section_headings = sections_json::TEXT
    WHERE post_id = COALESCE(NEW.post_id, OLD.post_id);

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Recreate the trigger
CREATE TRIGGER trigger_sync_sections_to_headings
    AFTER INSERT OR UPDATE OR DELETE ON post_section
    FOR EACH ROW
    EXECUTE FUNCTION sync_sections_to_section_headings(); 