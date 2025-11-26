-- Rename image table to image_archive to test for remaining references
-- This is a safe way to identify any code still using the old table

BEGIN;

-- Rename the table
ALTER TABLE image RENAME TO image_archive;

-- Verify the rename
DO $$
DECLARE
    table_exists BOOLEAN;
BEGIN
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'image_archive'
    ) INTO table_exists;
    
    IF table_exists THEN
        RAISE NOTICE '✅ Table renamed successfully: image -> image_archive';
    ELSE
        RAISE WARNING '❌ Table rename failed!';
    END IF;
END $$;

-- Note: We're NOT committing yet - this is a test
-- If everything works, we can commit
-- If something breaks, we'll rollback and fix the issues

-- COMMIT;  -- Uncomment after verification
-- ROLLBACK;  -- Use this if issues found






