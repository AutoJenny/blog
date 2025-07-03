-- Drop existing function and trigger
DROP FUNCTION IF EXISTS sync_section_headings_to_sections() CASCADE;

-- Create corrected trigger function
CREATE OR REPLACE FUNCTION sync_section_headings_to_sections() 
RETURNS TRIGGER AS $$
DECLARE 
    section_data JSONB;
    section_item JSONB;
    section_id INTEGER;
    i INTEGER := 0;
BEGIN
    -- Only proceed if section_headings was updated
    IF OLD.section_headings IS NOT DISTINCT FROM NEW.section_headings THEN
        RETURN NEW;
    END IF;

    -- Parse the section_headings JSON
    IF NEW.section_headings IS NULL OR NEW.section_headings = '' THEN
        -- Clear all sections for this post
        DELETE FROM post_section WHERE post_id = NEW.post_id;
        RETURN NEW;
    END IF;

    BEGIN
        section_data := NEW.section_headings::JSONB;
    EXCEPTION WHEN OTHERS THEN
        -- Handle invalid JSON - log error but don't fail
        RAISE WARNING 'Invalid JSON in section_headings for post %: %', NEW.post_id, NEW.section_headings;
        RETURN NEW;
    END;

    -- Process each section in the array
    FOR section_item IN SELECT * FROM jsonb_array_elements(section_data)
    LOOP
        i := i + 1;

        -- Extract section data
        DECLARE
            heading TEXT;
            description TEXT;
            section_status TEXT;
        BEGIN
            -- Handle different JSON formats
            IF jsonb_typeof(section_item) = 'string' THEN
                heading := section_item::TEXT;
                description := '';
                section_status := 'draft';
            ELSE
                heading := COALESCE(section_item->>'heading', section_item->>'title', 'Section ' || i);
                description := COALESCE(section_item->>'description', '');
                section_status := COALESCE(section_item->>'status', 'draft');
            END IF;

            -- Find existing section or create new one
            SELECT id INTO section_id
            FROM post_section
            WHERE post_id = NEW.post_id AND section_order = i;

            IF section_id IS NULL THEN
                -- Create new section
                INSERT INTO post_section (
                    post_id, section_order, section_heading, 
                    section_description, status
                ) VALUES (
                    NEW.post_id, i, heading, description, section_status
                );
            ELSE
                -- Update existing section
                UPDATE post_section
                SET section_heading = heading,
                    section_description = description,
                    status = section_status
                WHERE id = section_id;
            END IF;
        END;
    END LOOP;

    -- Remove sections that are no longer in the list
    DELETE FROM post_section
    WHERE post_id = NEW.post_id AND section_order > i;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Recreate the trigger
CREATE TRIGGER trigger_sync_section_headings
    AFTER UPDATE OF section_headings ON post_development
    FOR EACH ROW
    EXECUTE FUNCTION sync_section_headings_to_sections(); 