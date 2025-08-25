# Legacy clan.com Publishing API Integration

## Overview

This document analyzes the clan.com publishing system from the previous blog implementation (`/Users/nickfiddes/Code/projects/blog_old`). The system provided a complete pipeline for publishing blog posts with images to the clan.com website via their API.

## Architecture Overview

The clan.com publishing system consisted of:

1. **Main Publishing Script** (`scripts/post_to_clan.py`)
2. **API Integration Layer** (REST API calls)
3. **Content Processing** (HTML extraction and optimization)
4. **Image Upload Pipeline** (Automatic image processing)
5. **Workflow Integration** (Status tracking and error handling)

## Core Components

### 1. Publishing Script (`post_to_clan.py`)

#### Purpose
The main orchestrator that handles the complete publishing process: content preparation, image uploads, and API submission to clan.com.

#### Key Features

**Configuration Management:**
```python
config = {
    "api_base_url": "https://clan.com/clan/blog_api/",
    "api_user": "blog",
    "api_key": os.getenv("CLAN_API_KEY"),
    "image_library_file": BASE_DIR / "_data/image_library.json",
    "workflow_status_file": BASE_DIR / "_data/workflow_status.json",
    "posts_dir_name": "posts",
    "html_content_selector": "article.blog-post",
    "html_back_link_selector": "nav.post-navigation-top",
    "image_public_base_url": "https://static.clan.com/media/blog/",
    "media_url_prefix_expected": "/media/blog/",
    "media_url_submit_prefix": "/blog/",
    "default_category_ids": [14, 15]
}
```

**Processing Pipeline:**
1. **Input Validation**: Verify markdown file exists
2. **Front Matter Parsing**: Extract metadata and content
3. **Eleventy Build**: Generate static HTML
4. **Content Extraction**: Extract main content using CSS selectors
5. **Image Processing**: Upload and update image URLs
6. **API Submission**: Create or edit post via clan.com API
7. **Status Update**: Update workflow status

### 2. Content Processing

#### HTML Content Extraction

**Selector-Based Extraction:**
```python
def extract_html_content(built_html_path, header_image_filename=None):
    selector = CONFIG["html_content_selector"]  # "article.blog-post"
    back_link_selector = CONFIG["html_back_link_selector"]  # "nav.post-navigation-top"
    
    # Find main content element
    content_element = soup.select_one(selector)
    
    # Remove navigation elements
    back_link_element = soup.select_one(back_link_selector)
    if back_link_element:
        back_link_element.decompose()
    
    # Remove header image figure if specified
    if header_image_filename:
        img_tag = content_element.find('img', src=lambda s: s and s.endswith(header_image_filename))
        if img_tag:
            figure_to_remove = img_tag.find_parent('figure', class_='section-image')
            if figure_to_remove:
                figure_to_remove.decompose()
    
    # Rewrite image paths to full URLs
    for img_tag in content_element.find_all('img'):
        original_src = img_tag.get('src')
        if original_src and original_src.startswith(('/images/', 'images/')):
            filename = os.path.basename(original_src)
            new_src = image_public_base_url.rstrip('/') + '/' + filename
            img_tag['src'] = new_src
```

**Content Cleaning:**
- Removes HTML comments
- Removes navigation elements
- Removes header image figures
- Rewrites relative image paths to absolute URLs
- Preserves main content structure

### 3. Image Upload Pipeline

#### Image Upload Process

**Gathering Image IDs:**
```python
image_ids_to_upload = []

# Header image
header_id = metadata.get('headerImageId')
if header_id:
    image_ids_to_upload.append(header_id)

# Section images
for section in metadata.get('sections', []):
    section_id = section.get('imageId')
    if section_id:
        image_ids_to_upload.append(section_id)

# Conclusion image
conclusion_id = metadata.get('conclusion', {}).get('imageId')
if conclusion_id:
    image_ids_to_upload.append(conclusion_id)
```

**Upload Function:**
```python
def upload_image_to_clan(image_id, image_library_data):
    url = CONFIG["api_base_url"] + "uploadImage"
    
    # Get image details from library
    img_entry = image_library_data.get(image_id)
    local_dir = img_entry.get("source_details", {}).get("local_dir")
    filename_local = img_entry.get("source_details", {}).get("filename_local")
    
    # Prepare upload
    payload = {'api_user': api_user, 'api_key': api_key}
    files = {'image_file': (filename_local, open(full_local_path, 'rb'))}
    
    # Upload and process response
    response = requests.post(url, data=payload, files=files, timeout=60)
    response_data = response.json()
    
    # Extract public URL from success message
    if "File uploaded successfully:" in response_data.get("message", ""):
        url_match = re.search(r"File uploaded successfully:\s*(https://\S+)", response_data["message"])
        if url_match:
            full_public_url = url_match.group(1).strip()
            # Convert to relative path for API submission
            path_part = urlparse(full_public_url).path
            thumbnail_submit_path = media_url_submit_prefix.rstrip('/') + '/' + path_part[len(media_url_prefix_expected):]
            
            # Update library with new URLs
            image_library_data[image_id]["source_details"]["public_url"] = full_public_url
            image_library_data[image_id]["source_details"]["uploaded_path_relative"] = thumbnail_submit_path
```

### 4. API Integration

#### Authentication
```python
payload = {
    'api_user': (None, api_user),
    'api_key': (None, api_key),
    'json_args': (None, json.dumps(args))
}
```

#### Post Creation API
```python
def create_blog_post(post_metadata, post_content_html_path, image_library_data):
    args = _prepare_api_args(post_metadata, image_library_data)
    
    payload = {
        'api_user': (None, api_user),
        'api_key': (None, api_key),
        'json_args': (None, json.dumps(args))
    }
    
    files_payload = {'html_file': (os.path.basename(temp_html_file_path), file_handle, 'text/html')}
    
    response = requests.post(url, data=payload, files=files_payload, timeout=120)
    response_data = response.json()
    
    # Extract post ID from success message
    if response_data.get("status") == "success":
        message = response_data.get("message", "")
        id_match = re.search(r'(\d+)$', message)
        if id_match:
            post_id = int(id_match.group(1))
            return True, post_id, None
```

#### Post Editing API
```python
def edit_blog_post(post_id, post_metadata, post_content_html_path, image_library_data):
    args = _prepare_api_args(post_metadata, image_library_data)
    args['post_id'] = post_id  # Required for editing
    
    # Same API call structure as creation
    response = requests.post(url, data=payload, files=files_payload, timeout=120)
    
    # Handle specific error cases
    if "invalid post id" in error_msg.lower() or "post not found" in error_msg.lower():
        return False, "PostNotFound"
```

### 5. API Arguments Preparation

#### Required Fields
```python
def _prepare_api_args(post_metadata, image_library_data):
    args = {}
    
    # Required fields
    args['title'] = post_metadata.get('title')
    args['url_key'] = post_metadata.get('url_key', Path(post_metadata['_input_path']).stem)
    
    # Optional fields
    args['short_content'] = post_metadata.get('short_content', post_metadata.get('description', ''))
    args['status'] = post_metadata.get('status', 2)  # Default to enabled=2
    args['categories'] = post_metadata.get('categories', CONFIG["default_category_ids"])
    
    # Meta fields
    args['meta_title'] = post_metadata.get('metaTitle', args['title'])
    args['meta_tags'] = post_metadata.get('metaTags', ','.join([t for t in post_metadata.get('tags', []) if t and t.lower() != 'post']))
    args['meta_description'] = post_metadata.get('metaDescription', args['short_content'])
    
    # Thumbnail handling
    header_image_id = post_metadata.get('headerImageId')
    if header_image_id:
        img_entry = image_library_data.get(header_image_id)
        if img_entry:
            uploaded_path = img_entry.get("source_details", {}).get("uploaded_path_relative")
            if uploaded_path:
                args['list_thumbnail'] = uploaded_path
                args['post_thumbnail'] = uploaded_path
    
    # Publish date
    publish_date = post_metadata.get('date')
    if isinstance(publish_date, (datetime.date, datetime.datetime)):
        args['publish_date_iso'] = publish_date.isoformat()
    
    return {k: v for k, v in args.items() if v is not None}
```

## API Endpoints

### 1. Image Upload
```
POST https://clan.com/clan/blog_api/uploadImage
```

**Parameters:**
- `api_user`: Authentication user
- `api_key`: Authentication key
- `image_file`: File upload

**Response:**
```json
{
  "status": "success",
  "message": "File uploaded successfully: https://static.clan.com/media/blog/filename.jpg"
}
```

### 2. Post Creation
```
POST https://clan.com/clan/blog_api/createPost
```

**Parameters:**
- `api_user`: Authentication user
- `api_key`: Authentication key
- `json_args`: JSON string with post metadata
- `html_file`: HTML content file

**Response:**
```json
{
  "status": "success",
  "message": "Blog post created successfully with ID: 123"
}
```

### 3. Post Editing
```
POST https://clan.com/clan/blog_api/editPost
```

**Parameters:**
- `api_user`: Authentication user
- `api_key`: Authentication key
- `json_args`: JSON string with post metadata (including post_id)
- `html_file`: HTML content file

**Response:**
```json
{
  "status": "success",
  "message": "Post ID 123 updated."
}
```

## Workflow Integration

### Status Tracking
```python
# Update workflow status after publishing
update_time = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds') + 'Z'

if script_success:
    workflow_data[post_slug]['stages']['publishing_clancom']['status'] = 'complete'
    workflow_data[post_slug]['stages']['publishing_clancom']['post_id'] = new_post_id
    workflow_data[post_slug]['stages']['publishing_clancom']['last_error'] = None
else:
    workflow_data[post_slug]['stages']['publishing_clancom']['status'] = 'error'
    workflow_data[post_slug]['stages']['publishing_clancom']['last_error'] = error_message

workflow_data[post_slug]['last_updated'] = update_time
workflow_data[post_slug]['stages']['publishing_clancom']['last_publish_attempt'] = update_time
```

### Error Handling
- **Post Not Found**: Clears stale post ID from workflow
- **Upload Failures**: Continues with missing images
- **API Errors**: Detailed error logging and status updates
- **Network Issues**: Timeout handling and retry logic

## Key Features

### 1. Automatic Image Processing
- Uploads all referenced images automatically
- Updates image library with public URLs
- Rewrites image paths in content
- Handles header images as thumbnails

### 2. Content Optimization
- Removes navigation and header elements
- Rewrites relative URLs to absolute
- Preserves content structure
- Handles HTML comments

### 3. Flexible Publishing
- Create new posts or edit existing
- Force creation option available
- Automatic post ID tracking
- Error recovery mechanisms

### 4. Status Management
- Comprehensive workflow integration
- Detailed error tracking
- Timestamp logging
- Post ID persistence

## Technical Specifications

### Configuration Requirements
```bash
# Environment variables
CLAN_API_BASE_URL=https://clan.com/clan/blog_api/
CLAN_API_USER=blog
CLAN_API_KEY=<api_key>
IMAGE_LIBRARY_FILENAME=_data/image_library.json
WORKFLOW_STATUS_FILENAME=_data/workflow_status.json
POSTS_DIR_NAME=posts
HTML_CONTENT_SELECTOR=article.blog-post
HTML_BACK_LINK_SELECTOR=nav.post-navigation-top
IMAGE_PUBLIC_BASE_URL=https://static.clan.com/media/blog/
MEDIA_URL_PREFIX_EXPECTED=/media/blog/
MEDIA_URL_SUBMIT_PREFIX=/blog/
DEFAULT_CATEGORY_IDS=14,15
```

### File Dependencies
- Markdown post files in `posts/` directory
- Image library JSON file
- Workflow status JSON file
- Eleventy build system
- Watermark image file

### Error Scenarios
1. **Missing API Key**: Script exits with error
2. **Invalid Post ID**: Clears ID and attempts creation
3. **Upload Failures**: Continues with missing images
4. **Build Failures**: Exits with detailed error
5. **Network Timeouts**: Configurable timeout handling

## Migration Considerations

When adapting to the new blog structure:

1. **Database Integration**: Replace JSON files with database tables
2. **API Modernization**: Update to current clan.com API version
3. **Workflow Alignment**: Integrate with new workflow stages
4. **Error Handling**: Improve retry and recovery mechanisms
5. **Content Processing**: Adapt to new content structure
6. **Image Pipeline**: Integrate with new image processing system
7. **Authentication**: Update to current authentication methods
8. **Configuration**: Move to environment-based configuration

## Suggested Improvements for New System

### Database Integration
- Replace workflow status JSON with database tables
- Implement proper foreign key relationships for posts, images, and workflow stages
- Add database transactions for data integrity
- Enable concurrent access and better performance

### API Modernization
- Update to current clan.com API version and endpoints
- Implement proper API versioning and backward compatibility
- Add API rate limiting and retry mechanisms
- Implement API response caching where appropriate

### Enhanced Content Processing
- Adapt content extraction to new HTML structure
- Implement more flexible content selectors
- Add content validation and sanitization
- Support for additional content formats

### Improved Error Handling
- Implement comprehensive retry mechanisms with exponential backoff
- Add detailed error logging and monitoring
- Implement graceful degradation for failed operations
- Add recovery mechanisms for partial failures

### Workflow Integration
- Integrate with new workflow stage system
- Implement proper status tracking and transitions
- Add workflow validation and error recovery
- Support for workflow branching and conditional logic

### Performance Optimization
- Add content caching and optimization
- Implement background processing for non-critical operations
- Add progress tracking and status updates
- Optimize image upload and processing pipeline 