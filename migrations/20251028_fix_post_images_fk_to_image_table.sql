-- Fix foreign key constraint in post_images to reference image table correctly
-- The table is actually named "image" (singular), not "images" (plural)

ALTER TABLE post_images 
DROP CONSTRAINT IF EXISTS post_images_image_id_fkey;

ALTER TABLE post_images 
ADD CONSTRAINT post_images_image_id_fkey 
FOREIGN KEY (image_id) REFERENCES image(id) ON DELETE CASCADE;

