-- Migration: Consolidate image table into images table
-- This script migrates all data from the old 'image' table to the new 'images' table
-- and updates all foreign key references.

-- IMPORTANT: Run this in a transaction and verify results before committing
BEGIN;

-- Step 1: Audit current state
DO $$
DECLARE
    image_count INTEGER;
    images_count INTEGER;
    id_conflicts INTEGER;
BEGIN
    -- Count records
    SELECT COUNT(*) INTO image_count FROM image;
    SELECT COUNT(*) INTO images_count FROM images;
    
    -- Check for ID conflicts
    SELECT COUNT(*) INTO id_conflicts
    FROM image i1
    JOIN images i2 ON i1.id = i2.id;
    
    RAISE NOTICE 'Current state:';
    RAISE NOTICE '  image table: % records', image_count;
    RAISE NOTICE '  images table: % records', images_count;
    RAISE NOTICE '  ID conflicts: %', id_conflicts;
    
    IF id_conflicts > 0 THEN
        RAISE WARNING 'ID conflicts detected! Migration may fail.';
    END IF;
END $$;

-- Step 2: Migrate data from image to images
-- Map path -> file_path, handle missing columns
INSERT INTO images (
    id,
    filename,
    original_filename,
    file_path,  -- Maps from image.path
    alt_text,
    caption,
    image_prompt,
    created_at,
    updated_at
)
SELECT 
    id,
    filename,
    COALESCE(original_filename, filename) as original_filename,
    path as file_path,  -- Map path column to file_path
    alt_text,
    caption,
    image_prompt,
    COALESCE(created_at, CURRENT_TIMESTAMP) as created_at,
    COALESCE(updated_at, CURRENT_TIMESTAMP) as updated_at
FROM image
ON CONFLICT (id) DO UPDATE SET
    filename = EXCLUDED.filename,
    file_path = EXCLUDED.file_path,
    alt_text = EXCLUDED.alt_text,
    caption = EXCLUDED.caption,
    image_prompt = EXCLUDED.image_prompt,
    updated_at = CURRENT_TIMESTAMP;

-- Step 3: Verify migration
DO $$
DECLARE
    image_count INTEGER;
    images_count INTEGER;
    difference INTEGER;
BEGIN
    SELECT COUNT(*) INTO image_count FROM image;
    SELECT COUNT(*) INTO images_count FROM images;
    difference := image_count - images_count;
    
    RAISE NOTICE 'Migration verification:';
    RAISE NOTICE '  image table: % records', image_count;
    RAISE NOTICE '  images table: % records', images_count;
    RAISE NOTICE '  difference: %', difference;
    
    IF difference > 0 THEN
        RAISE WARNING 'Not all records migrated! % records missing', difference;
    ELSIF difference < 0 THEN
        RAISE NOTICE 'images table has more records (expected if it had existing data)';
    ELSE
        RAISE NOTICE 'All records migrated successfully';
    END IF;
END $$;

-- Step 4: Update post_images.image_id references
-- (Should already point to images, but verify and fix if needed)
UPDATE post_images pi
SET image_id = i2.id
FROM image i1
JOIN images i2 ON i1.id = i2.id
WHERE pi.image_id = i1.id
  AND pi.image_id != i2.id;  -- Only update if different

-- Step 5: Update post.header_image_id references
UPDATE post p
SET header_image_id = i2.id
FROM image i1
JOIN images i2 ON i1.id = i2.id
WHERE p.header_image_id = i1.id
  AND p.header_image_id != i2.id;  -- Only update if different

-- Step 6: Final verification
DO $$
DECLARE
    post_images_bad INTEGER;
    post_header_bad INTEGER;
BEGIN
    -- Check for post_images pointing to image table
    SELECT COUNT(*) INTO post_images_bad
    FROM post_images pi
    JOIN image i ON pi.image_id = i.id;
    
    -- Check for post.header_image_id pointing to image table
    SELECT COUNT(*) INTO post_header_bad
    FROM post p
    JOIN image i ON p.header_image_id = i.id
    WHERE p.header_image_id IS NOT NULL;
    
    RAISE NOTICE 'Final verification:';
    RAISE NOTICE '  post_images.image_id pointing to image: %', post_images_bad;
    RAISE NOTICE '  post.header_image_id pointing to image: %', post_header_bad;
    
    IF post_images_bad > 0 OR post_header_bad > 0 THEN
        RAISE WARNING 'Some references still point to image table!';
    ELSE
        RAISE NOTICE 'All references updated successfully';
    END IF;
END $$;

-- Step 7: Verify no orphaned records
DO $$
DECLARE
    orphaned_post_images INTEGER;
    orphaned_post_header INTEGER;
BEGIN
    -- Check for post_images.image_id not in images
    SELECT COUNT(*) INTO orphaned_post_images
    FROM post_images pi
    LEFT JOIN images i ON pi.image_id = i.id
    WHERE i.id IS NULL;
    
    -- Check for post.header_image_id not in images
    SELECT COUNT(*) INTO orphaned_post_header
    FROM post p
    LEFT JOIN images i ON p.header_image_id = i.id
    WHERE p.header_image_id IS NOT NULL AND i.id IS NULL;
    
    RAISE NOTICE 'Orphaned records check:';
    RAISE NOTICE '  orphaned post_images.image_id: %', orphaned_post_images;
    RAISE NOTICE '  orphaned post.header_image_id: %', orphaned_post_header;
    
    IF orphaned_post_images > 0 OR orphaned_post_header > 0 THEN
        RAISE WARNING 'Orphaned records detected!';
    ELSE
        RAISE NOTICE 'No orphaned records';
    END IF;
END $$;

-- IMPORTANT: Review the output above before committing
-- If everything looks good, commit the transaction
-- If there are issues, rollback and investigate

-- COMMIT;  -- Uncomment after verification
-- ROLLBACK;  -- Use this if issues found

