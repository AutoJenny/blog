# Image Storage System Migration Summary

## Completed Tasks

### 1. Database Backups
- **blog database**: `backups/blog_backup_20250724_181647.sql` (582KB)
- **blog_test database**: `backups/blog_test_backup_20250724_181649.sql` (541KB)

### 2. New Database Structure

#### Images Table
```sql
CREATE TABLE images (
    id SERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    original_filename VARCHAR(255),
    file_path VARCHAR(500) NOT NULL,
    file_size INTEGER,
    mime_type VARCHAR(100),
    width INTEGER,
    height INTEGER,
    alt_text TEXT,
    caption TEXT,
    image_prompt TEXT,
    notes TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### Post Images Linking Table
```sql
CREATE TABLE post_images (
    id SERIAL PRIMARY KEY,
    post_id INTEGER REFERENCES post(id) ON DELETE CASCADE,
    image_id INTEGER REFERENCES images(id) ON DELETE CASCADE,
    image_type VARCHAR(50) NOT NULL, -- 'header_raw', 'header_optimized', 'section_raw', 'section_optimized'
    section_id INTEGER REFERENCES post_section(id) ON DELETE CASCADE, -- NULL for header images
    sort_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(post_id, image_type, section_id)
);
```

### 3. Removed Old Fields from post_section
The following fields were removed from the `post_section` table:
- `image_prompt_example_id`
- `generated_image_url`
- `image_generation_metadata`
- `image_id`
- `watermarking`

### 4. File System Structure
Created organized directory structure in `blog-core/static/images/`:

```
blog-core/static/images/
├── raw/                    # Original LLM output images
│   └── posts/
│       ├── header/         # Post header images
│       └── sections/       # Section images
└── optimized/              # Processed/optimized images
    └── posts/
        ├── header/         # Optimized header images
        └── sections/       # Optimized section images
```

### 5. Database Indexes
Created performance indexes:
- `idx_post_images_post_id` on `post_images(post_id)`
- `idx_post_images_section_id` on `post_images(section_id)`
- `idx_post_images_image_type` on `post_images(image_type)`
- `idx_images_created_at` on `images(created_at)`

### 6. Automatic Timestamp Updates
Created trigger to automatically update `updated_at` timestamp when images are modified.

## Usage Examples

### Store a Section Image
```sql
-- 1. Insert image record
INSERT INTO images (filename, file_path, mime_type, alt_text, image_prompt) 
VALUES ('section_1_raw.jpg', '/static/images/raw/posts/53/sections/1/section_1_raw.jpg', 'image/jpeg', 'Section 1 image', 'Generate an image about...');

-- 2. Link to section
INSERT INTO post_images (post_id, image_id, image_type, section_id) 
VALUES (53, 1, 'section_raw', 1);
```

### Get All Images for a Section
```sql
SELECT i.*, pi.image_type 
FROM images i 
JOIN post_images pi ON i.id = pi.image_id 
WHERE pi.post_id = 53 AND pi.section_id = 1;
```

### Get Header Images for a Post
```sql
SELECT i.*, pi.image_type 
FROM images i 
JOIN post_images pi ON i.id = pi.image_id 
WHERE pi.post_id = 53 AND pi.image_type LIKE 'header%';
```

## Benefits

1. **Scalable**: Easy to add multiple images per section
2. **Organized**: Clear separation between raw and optimized images
3. **Flexible**: JSONB metadata field for future extensions
4. **Clean**: Removed image clutter from post_section table
5. **Future-proof**: Ready for social media variants and multiple images

## Next Steps

1. Update LLM Actions service to save images to new structure
2. Update Sections service to display images from new structure
3. Create image optimization pipeline
4. Add image management UI in workflow

## Migration Files

- **Migration Script**: `migrations/image_storage_restructure.sql`
- **Backups**: `backups/` directory
- **File Structure**: `blog-core/static/images/` directory 