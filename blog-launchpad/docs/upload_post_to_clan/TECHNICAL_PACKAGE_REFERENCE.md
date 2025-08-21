# Clan.com API Technical Package Reference

## Overview
This document details the exact technical package structure and implementation for successful uploads to clan.com via their blog API. Based on the current `clan_publisher.py` implementation and working API integration.

## System Architecture

### Core Components
- **`ClanPublisher` Class**: Main orchestrator for the upload process
- **Template System**: Uses `clan_post_raw.html` for HTML generation
- **Image Processing**: Automatic discovery and upload of images
- **Data Integration**: Unified data loading via `get_post_sections_with_images`

### File Structure
```
blog/blog-launchpad/
├── clan_publisher.py          # Main upload logic
├── templates/
│   └── clan_post_raw.html    # HTML template for uploads
└── app.py                     # Database and utility functions
```

## API Endpoints

### 1. Image Upload
**Endpoint:** `POST https://clan.com/clan/blog_api/uploadImage`

**Required Parameters:**
- `api_user`: "blog" (authentication)
- `api_key`: Your API key from environment
- `image`: File upload (multipart/form-data)
- `json_args`: "[]" (empty array, required by clan.com API)

**Expected Response:**
```json
{
  "status": "success",
  "message": "File uploaded successfully: https://static.clan.com/media/blog/filename.jpg"
}
```

**Critical:** The response contains the **clan.com media URL** that must be used in thumbnail fields and HTML content.

### 2. Post Creation
**Endpoint:** `POST https://clan.com/clan/blog_api/createPost`

**Required Parameters:**
- `api_user`: "blog" (authentication)
- `api_key`: Your API key from environment
- `json_args`: JSON string with post metadata
- `html_file`: HTML content file (multipart upload)

## Required JSON Args Structure

### Mandatory Fields (All Required)
```json
{
  "title": "Post Title",                    // String - Post title
  "url_key": "post-slug-53-1755600000",     // String - Generated URL-friendly identifier
  "short_content": "Summary text...",       // String - Max 200 characters
  "status": 2,                              // Integer - 2 = enabled, 1 = disabled
  "categories": [14, 15],                   // Array - Category IDs
  "list_thumbnail": "/blog/header_53_1703123456.jpg",  // String - Path from /media
  "post_thumbnail": "/blog/header_53_1703123456.jpg",  // String - Path from /media
  "meta_title": "SEO Title",                // String - Meta title
  "meta_tags": "tag1,tag2,tag3",           // String - Comma-separated tags
  "meta_description": "SEO description..."  // String - Max 160 characters
}
```

### Field Specifications

#### Title & URL
- **title**: Must match the actual post title exactly
- **url_key**: Auto-generated using `_generate_url_key()` method with format: `{slug}-{post_id}-{fixed_timestamp}`

#### Content
- **short_content**: Truncated summary, max 200 characters
- **status**: Always 2 for published posts

#### Categories
- **categories**: Array of integer category IDs
- **Default**: [14, 15] (Scottish Heritage, Blog)

#### Thumbnails (CRITICAL)
- **list_thumbnail**: Path to image in clan.com media system
- **post_thumbnail**: Path to image in clan.com media system
- **Format**: `/blog/filename.jpg` (relative to /media)
- **Source**: Automatically extracted from uploaded header image
- **Fallback**: `/blog/placeholder.jpg` if no images available

#### Meta Fields
- **meta_title**: Usually same as post title
- **meta_tags**: Auto-generated from title and summary content
- **meta_description**: Truncated summary, max 160 characters

## Complete Upload Process

### Step 0: Data Preparation and Image Discovery
```python
# Load sections from DB using unified function
from app import get_post_sections_with_images
sections_list = get_post_sections_with_images(post['id'])

# Discover images in file system
from app import find_header_image, find_section_image
header_image_path = find_header_image(full_post_data['id'])

# Attach image paths to sections
for i, section in enumerate(sections_list):
    section_image_path = find_section_image(full_post_data['id'], section['id'])
    if section_image_path:
        section['image'] = {'path': section_image_path}
```

**Image Discovery:**
- **Header Images**: Located in `/static/content/posts/{post_id}/header/optimized/` or `/raw/`
- **Section Images**: Located in `/static/content/posts/{post_id}/sections/{section_id}/optimized/` or `/raw/`
- **File Extensions**: Supports .png, .jpg, .jpeg, .gif, .webp, .bmp
- **Priority**: Optimized versions preferred over raw versions

### Step 1: Image Processing and Upload
```python
# Process and upload all images
uploaded_images = self.process_images(full_post_data, sections_list)
```

**Image Processing Pipeline:**
1. **File Validation**: Check if image files exist in file system
2. **Path Conversion**: Convert web paths (`/static/...`) to file system paths
3. **Filename Generation**: Create unique filenames with timestamps for cache busting
4. **MIME Type Detection**: Auto-detect image type based on file extension
5. **Upload to Clan.com**: Send via `uploadImage` API endpoint
6. **URL Extraction**: Parse response to extract clan.com media URLs
7. **Path Mapping**: Create mapping from local paths to clan.com URLs

**Image Upload Details:**
- **Header Images**: `header_{post_id}_{timestamp}.jpg`
- **Section Images**: `section_{post_id}_{section_index}_{timestamp}.jpg`
- **File System Path**: `/Users/nickfiddes/Code/projects/blog/blog-images/static/...`
- **Timeout**: 15 seconds per upload
- **Error Handling**: Graceful fallback if individual images fail

### Step 2: Cross-Promotion Data Mapping
```python
if full_post_data.get('cross_promotion_category_id'):
    full_post_data['cross_promotion'] = {
        'category_id': full_post_data['cross_promotion_category_id'],
        'category_title': full_post_data.get('cross_promotion_category_title', ''),
        'product_id': full_post_data.get('cross_promotion_product_id'),
        'product_title': full_post_data.get('cross_promotion_product_title', '')
    }
```

**Cross-Promotion Features:**
- **Category Widgets**: Inserted at specified section positions
- **Product Widgets**: Inserted at specified section positions
- **End-of-Post**: Widgets can be positioned after all sections
- **Conditional Rendering**: Only displays if widget HTML exists

### Step 3: HTML Content Generation
```python
# Generate HTML using clan_post_raw.html template
html_content = self.get_preview_html_content(full_post_data, sections_list, uploaded_images)
```

**HTML Generation Process:**
1. **Template Loading**: Read `clan_post_raw.html` template file
2. **Jinja2 Rendering**: Create environment with custom filters
3. **Data Binding**: Render template with post and section data
4. **URL Translation**: Replace local image paths with clan.com URLs
5. **Content Cleaning**: Remove localhost references and clean HTML
6. **Debug Output**: Save HTML to `/tmp/upload_html_post_{id}_{timestamp}.html`

**Template Features:**
- **Post Header**: Subtitle, metadata, summary with proper HTML5 elements
- **Content Sections**: Priority-based content system (polished → draft → content)
- **Image Handling**: Conditional display with captions, lightbox integration
- **Cross-Promotion**: Widget positioning and conditional rendering
- **No Inline CSS**: Relies on clan.com's external CSS system

### Step 4: Post Creation/Update
```python
# Create or update post on clan.com
result = self.create_or_update_post(full_post_data, html_content, is_update, uploaded_images)
```

**Post Creation Process:**
1. **Metadata Preparation**: Build `json_args` with all required fields
2. **Thumbnail Assignment**: Use actual uploaded image paths for thumbnails
3. **HTML File Creation**: Write HTML content to temporary file
4. **API Request**: Send complete package via `createPost` API
5. **Response Handling**: Parse success/failure and extract post ID

## Image Processing Details

### File System Integration
```python
# Convert web paths to file system paths
if header_path.startswith('/static/'):
    fs_path = f"/Users/nickfiddes/Code/projects/blog/blog-images{header_path}"
    if os.path.exists(fs_path):
        logger.info(f"✅ Header image file exists at: {fs_path}")
        logger.info(f"File size: {os.path.getsize(fs_path)} bytes")
```

**Path Resolution:**
- **Web Paths**: `/static/content/posts/{post_id}/header/optimized/image.jpg`
- **File System Paths**: `/Users/nickfiddes/Code/projects/blog/blog-images/static/content/posts/{post_id}/header/optimized/image.jpg`
- **URL Encoding**: Handles spaces and special characters in filenames
- **Existence Validation**: Verifies files exist before attempting upload

### MIME Type Detection
```python
# Determine MIME type based on file extension
import mimetypes
mime_type, _ = mimetypes.guess_type(filename)
if not mime_type or not mime_type.startswith('image/'):
    # Fallback to common image types
    if filename.lower().endswith('.png'):
        mime_type = 'image/png'
    elif filename.lower().endswith('.jpg') or filename.lower().endswith('.jpeg'):
        mime_type = 'image/jpeg'
    elif filename.lower().endswith('.webp'):
        mime_type = 'image/webp'
    else:
        mime_type = 'image/jpeg'  # Default fallback
```

**Supported Formats:**
- **PNG**: `image/png`
- **JPEG**: `image/jpeg`
- **WebP**: `image/webp`
- **Fallback**: Defaults to `image/jpeg` for unknown types

### URL Translation
```python
# Translate local image paths to uploaded clan.com URLs
if uploaded_images:
    path_mapping = {}
    for local_path, clan_url in uploaded_images.items():
        if local_path.startswith('/static/'):
            path_mapping[local_path] = clan_url
        if 'content/posts' in local_path:
            rel = local_path.split('content/posts/')[-1] if 'content/posts/' in local_path else local_path
            path_mapping[f'/static/content/posts/{rel}'] = clan_url
    
    for local_path, clan_url in path_mapping.items():
        html_content = html_content.replace(f'src="{local_path}"', f'src="{clan_url}"')
        html_content = html_content.replace(f'href="{local_path}"', f'href="{clan_url}"')
```

**Path Mapping:**
- **Local Paths**: `/static/content/posts/53/sections/1/optimized/image.jpg`
- **Clan.com URLs**: `https://static.clan.com/media/blog/section_53_1_1703123456.jpg`
- **HTML Updates**: Both `src` and `href` attributes updated
- **Multiple Formats**: Handles various path formats and structures

## Error Handling and Validation

### Pre-Upload Validation
```python
# Validate required fields
required_fields = ['title', 'url_key', 'short_content', 'status', 'categories', 
                  'list_thumbnail', 'post_thumbnail', 'meta_title', 'meta_tags', 'meta_description']
missing_fields = []

for field in required_fields:
    value = json_args.get(field)
    if value is None:
        missing_fields.append(field)
    elif isinstance(value, str) and value.strip() == '':
        logger.warning(f"Field '{field}' is empty string, but proceeding anyway")

if missing_fields:
    return {
        'success': False,
        'error': f"Missing required fields: {', '.join(missing_fields)}"
    }
```

**Validation Checks:**
- **Required Fields**: All mandatory fields must be present
- **Field Types**: Ensures correct data types for each field
- **Content Length**: Validates summary and description length limits
- **Image Paths**: Verifies thumbnail paths are valid clan.com media paths

### Error Recovery
**Image Upload Failures:**
- Individual image failures don't stop the entire process
- Logs detailed error information for debugging
- Continues with available images
- Uses fallback thumbnails if needed

**Template Rendering Failures:**
- Falls back to raw template rendering if preview HTML fails
- Logs template errors for debugging
- Returns meaningful error messages

**API Failures:**
- Detailed logging of API responses
- Timeout handling (15 seconds per request)
- Retry logic for transient failures

## Success Criteria

A successful upload will result in:
1. **All Images Uploaded**: Successfully uploaded to clan.com media system
2. **Thumbnail Fields Populated**: Actual clan.com media paths (not placeholders)
3. **HTML Content Generated**: Complete HTML with working image links
4. **Cross-Promotion Widgets**: Embedded and positioned correctly
5. **Post Published**: Successfully created/updated on clan.com
6. **Response Received**: Success response with clan.com post ID

## Debugging and Testing

### Local Preview Routes
- **`/preview/{post_id}`**: Full preview with styling and images
- **`/clan-post-html/{post_id}`**: Raw HTML that will be uploaded
- **`/clan-post/{post_id}`**: Formatted post display

### Logging and Debug Output
```python
# Debug HTML saved to temporary file
debug_file = f'/tmp/upload_html_post_{post["id"]}_{int(time.time())}.html'
with open(debug_file, 'w', encoding='utf-8') as f:
    f.write(html_content)
logger.info(f"Upload HTML saved to: {debug_file}")
```

**Debug Information:**
- **HTML Content**: Saved to `/tmp/upload_html_post_{id}_{timestamp}.html`
- **Image Processing**: Detailed logs of file discovery and upload
- **API Requests**: Full request/response logging
- **Error Traces**: Complete stack traces for debugging

### Testing Checklist
Before attempting upload:
- [ ] All required images exist in file system
- [ ] Environment variables configured (CLAN_API_KEY, CLAN_API_USER)
- [ ] HTML content generated and validated via `/clan-post-html/{post_id}`
- [ ] Cross-promotion data available (if using widgets)
- [ ] All required fields populated in json_args
- [ ] Image uploads tested and working
- [ ] Thumbnail paths updated with actual clan.com URLs

## Environment Configuration

### Required Environment Variables
```bash
CLAN_API_KEY=your_api_key_here
CLAN_API_USER=blog
CLAN_API_BASE_URL=https://clan.com/clan/blog_api/
```

### File System Requirements
- **Blog Images Directory**: `/Users/nickfiddes/Code/projects/blog/blog-images/static/`
- **Image Structure**: `content/posts/{post_id}/{header|sections}/{section_id}/{optimized|raw}/`
- **File Permissions**: Read access to image files
- **Disk Space**: Sufficient space for temporary HTML files

## Performance Considerations

### Upload Optimization
- **Parallel Processing**: Images uploaded sequentially (can be optimized)
- **File Size Limits**: No explicit limits, but large files may timeout
- **Cache Busting**: Timestamp-based filenames prevent caching issues
- **Error Recovery**: Individual failures don't stop the entire process

### Memory Management
- **Streaming Uploads**: Files read in chunks during upload
- **Temporary Files**: Cleaned up after processing
- **HTML Generation**: Content processed in memory (consider streaming for large posts)

## Conclusion

The current upload system provides a robust, automated solution for publishing blog posts to clan.com. Key features include:

1. **Automated Image Processing**: Discovers, uploads, and integrates images automatically
2. **Template-Based HTML**: Uses `clan_post_raw.html` for consistent, maintainable output
3. **Comprehensive Validation**: Ensures all required data is present before upload
4. **Error Handling**: Graceful degradation and detailed logging for debugging
5. **Integration**: Seamlessly integrates with existing blog infrastructure

The system handles the complexity of image management, HTML generation, and API integration while providing clear feedback and debugging capabilities for developers.


