-- Section Synchronization Triggers Migration
-- Date: 2025-07-02
-- Purpose: Add automatic synchronization between post_development.section_headings and post_section records

-- First, add the missing post_development trigger function if it doesn't exist
CREATE OR REPLACE FUNCTION update_post_development_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Add the post_development trigger if it doesn't exist
DROP TRIGGER IF EXISTS update_post_development_updated_at ON post_development;
CREATE TRIGGER update_post_development_updated_at
    BEFORE UPDATE ON post_development
    FOR EACH ROW
    EXECUTE FUNCTION update_post_development_updated_at_column();

-- Primary Sync Trigger Function (post_development → post_section)
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
            status TEXT;
        BEGIN
            -- Handle different JSON formats
            IF jsonb_typeof(section_item) = 'string' THEN
                heading := section_item::TEXT;
                description := '';
                status := 'draft';
            ELSE
                heading := COALESCE(section_item->>'heading', section_item->>'title', 'Section ' || i);
                description := COALESCE(section_item->>'description', '');
                status := COALESCE(section_item->>'status', 'draft');
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
                    NEW.post_id, i, heading, description, status
                );
            ELSE
                -- Update existing section
                UPDATE post_section 
                SET section_heading = heading,
                    section_description = description,
                    status = status
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

-- Primary Sync Trigger (post_development → post_section)
DROP TRIGGER IF EXISTS trigger_sync_section_headings ON post_development;
CREATE TRIGGER trigger_sync_section_headings
    AFTER UPDATE OF section_headings ON post_development
    FOR EACH ROW
    EXECUTE FUNCTION sync_section_headings_to_sections();

-- Secondary Sync Trigger Function (post_section → post_development) - Optional
CREATE OR REPLACE FUNCTION sync_sections_to_section_headings()
RETURNS TRIGGER AS $$
DECLARE
    section_headings JSONB;
    section_record RECORD;
BEGIN
    -- Build JSON array from current sections
    section_headings := '[]'::JSONB;
    
    FOR section_record IN 
        SELECT section_order, section_heading, section_description, status
        FROM post_section 
        WHERE post_id = COALESCE(NEW.post_id, OLD.post_id)
        ORDER BY section_order
    LOOP
        section_headings := section_headings || jsonb_build_object(
            'order', section_record.section_order,
            'heading', section_record.section_heading,
            'description', COALESCE(section_record.section_description, ''),
            'status', COALESCE(section_record.status, 'draft')
        );
    END LOOP;
    
    -- Update post_development
    UPDATE post_development 
    SET section_headings = section_headings::TEXT
    WHERE post_id = COALESCE(NEW.post_id, OLD.post_id);
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

-- Secondary Sync Triggers (post_section → post_development) - Optional
DROP TRIGGER IF EXISTS trigger_sync_sections_to_headings_insert ON post_section;
CREATE TRIGGER trigger_sync_sections_to_headings_insert
    AFTER INSERT ON post_section
    FOR EACH ROW
    EXECUTE FUNCTION sync_sections_to_section_headings();

DROP TRIGGER IF EXISTS trigger_sync_sections_to_headings_update ON post_section;
CREATE TRIGGER trigger_sync_sections_to_headings_update
    AFTER UPDATE ON post_section
    FOR EACH ROW
    EXECUTE FUNCTION sync_sections_to_section_headings();

DROP TRIGGER IF EXISTS trigger_sections_to_headings_delete ON post_section;
CREATE TRIGGER trigger_sections_to_headings_delete
    AFTER DELETE ON post_section
    FOR EACH ROW
    EXECUTE FUNCTION sync_sections_to_section_headings();

-- Add indexes for performance (skip the JSONB index for now due to invalid data)
CREATE INDEX IF NOT EXISTS idx_post_section_post_order ON post_section(post_id, section_order);

-- Add status column to post_section if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns 
                   WHERE table_name = 'post_section' AND column_name = 'status') THEN
        ALTER TABLE post_section ADD COLUMN status TEXT DEFAULT 'draft';
    END IF;
END $$; 