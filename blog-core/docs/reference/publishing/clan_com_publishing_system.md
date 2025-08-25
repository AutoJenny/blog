# Clan.com Publishing System

## Overview

This document describes the clan.com publishing system that has been ported from the legacy `blog_old` implementation. The system provides a complete pipeline for publishing blog posts with images to the clan.com website via their API.

## Architecture

The clan.com publishing system consists of several key components:

### 1. Publishing Script (`post_to_clan.py`)
- **Location:** `blog-core/scripts/post_to_clan.py`
- **Purpose:** Main orchestrator for the complete publishing process
- **Function:** Handles content preparation, image uploads, and API submission

### 2. Legacy Flask Integration (`legacy_app.py`)
- **Location:** `blog-core/legacy_app.py`
- **Purpose:** Contains the original Flask endpoints for triggering publishing
- **Function:** Provides `/api/publish_clan/<slug>` endpoint and workflow status management

### 3. API Integration Layer
- **Endpoints:** REST API calls to clan.com
- **Authentication:** API user/key based authentication
- **Content Processing:** HTML extraction and optimization

## API Endpoints

### Image Upload
```
POST https://clan.com/clan/blog_api/uploadImage
```

**Parameters:**
- `api_user`: Authentication user (default: "blog")
- `api_key`: Authentication key (from environment)
- `image_file`: File upload

**Response:**
```json
{
  "status": "success",
  "message": "File uploaded successfully: https://static.clan.com/media/blog/filename.jpg"
}
```

### Post Creation
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

### Post Editing
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

## Configuration

### Environment Variables
The system requires the following environment variables:

```bash
CLAN_API_BASE_URL=https://clan.com/clan/blog_api/
CLAN_API_USER=blog
CLAN_API_KEY=your_api_key_here
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

### Default Configuration
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

## Publishing Process

### Step-by-Step Workflow

1. **Input Validation**
   - Verify markdown file exists
   - Check required environment variables

2. **Front Matter Parsing**
   - Extract metadata from markdown front matter
   - Validate required fields (title, url_key)

3. **Eleventy Build**
   - Run `npm run build` to generate static HTML
   - Ensure `_site` directory is up-to-date

4. **Content Extraction**
   - Load built HTML (`_site/{slug}/index.html`)
   - Extract main content using CSS selector (`article.blog-post`)
   - Remove navigation elements and HTML comments

5. **Image Processing**
   - Identify all referenced images (header, sections)
   - Upload images via `uploadImage` API endpoint
   - Update image library with public URLs
   - Rewrite image paths in HTML content

6. **API Submission**
   - Prepare metadata for clan.com API
   - Call `createPost` or `editPost` endpoint
   - Handle response and extract post ID

7. **Status Update**
   - Update workflow status in JSON file
   - Store post ID for future edits
   - Log success/failure details

### Content Processing Details

#### HTML Content Extraction
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

#### Image Upload Process
```python
def upload_image_to_clan(image_id, image_library_data):
    api_function = "uploadImage"
    url = CONFIG["api_base_url"] + api_function
    
    # Get image file path from library
    img_entry = image_library_data.get(image_id)
    full_local_path = base_dir / local_dir.strip('/') / filename_local
    
    # Upload file
    with open(full_local_path, 'rb') as f:
        files = {'image_file': (filename_local, f)}
        response = requests.post(url, data=payload, files=files, timeout=60)
    
    # Extract public URL from response
    response_data = response.json()
    full_public_url = url_match.group(1).strip()
    
    # Update library with public URL
    image_library_data[image_id]["source_details"]["public_url"] = full_public_url
    image_library_data[image_id]["source_details"]["uploaded_path_relative"] = thumbnail_submit_path
```

## API Field Mapping

### Required Fields
- `title`: Post title (from front matter)
- `url_key`: URL slug (from front matter or derived from filename)

### Optional Fields
- `short_content`: Description/summary (from front matter)
- `status`: Post status (default: 2 = enabled)
- `categories`: Category IDs (from front matter or default)
- `meta_title`: SEO title (from front matter or post title)
- `meta_tags`: SEO tags (from front matter tags)
- `meta_description`: SEO description (from front matter)
- `list_thumbnail`: Header image path for list view
- `post_thumbnail`: Header image path for post view

### Front Matter to API Mapping
```python
def _prepare_api_args(post_metadata, image_library_data):
    args = {}
    
    # Required fields
    args['title'] = post_metadata.get('title')
    args['url_key'] = post_metadata.get('url_key', Path(post_metadata['_input_path']).stem)
    
    # Optional fields
    args['short_content'] = post_metadata.get('short_content', post_metadata.get('description', post_metadata.get('summary', '')))
    args['status'] = post_metadata.get('status', 2)
    args['categories'] = post_metadata.get('categories', CONFIG["default_category_ids"])
    
    # Meta fields
    args['meta_title'] = post_metadata.get('metaTitle', post_metadata.get('meta_title', args['title']))
    args['meta_tags'] = post_metadata.get('metaTags', post_metadata.get('meta_tags', ','.join([t for t in post_metadata.get('tags', []) if t and t.lower() != 'post'])))
    args['meta_description'] = post_metadata.get('metaDescription', post_metadata.get('meta_description', post_metadata.get('description', args['short_content'])))
    
    # Thumbnail handling
    header_image_id = post_metadata.get('headerImageId')
    if header_image_id and header_image_id in image_library_data:
        img_entry = image_library_data[header_image_id]
        uploaded_path = img_entry.get("source_details", {}).get("uploaded_path_relative")
        if uploaded_path:
            args['list_thumbnail'] = uploaded_path
            args['post_thumbnail'] = uploaded_path
    
    return args
```

## Error Handling

### Common Error Scenarios

1. **Missing API Key**
   - Error: "CRITICAL: Missing CLAN_API_KEY in environment/.env file"
   - Solution: Set CLAN_API_KEY environment variable

2. **Markdown File Not Found**
   - Error: "Markdown file not found for slug"
   - Solution: Ensure post markdown file exists in posts directory

3. **Build Failure**
   - Error: "Error during Eleventy build"
   - Solution: Check npm dependencies and build configuration

4. **Image Upload Failure**
   - Error: "Failed to upload image ID"
   - Solution: Check image file paths and API permissions

5. **API Response Errors**
   - Error: HTTP errors from clan.com API
   - Solution: Check API credentials and request format

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

## Integration Requirements

### Current Architecture Compatibility

**⚠️ SIGNIFICANT UPDATES REQUIRED:**

The legacy system was designed for:
- **Eleventy (11ty)** static site generation
- **Markdown-based** content with front matter
- **Image library JSON** file management
- **Workflow status JSON** tracking

**Current blog system uses:**
- **Flask-based** dynamic content
- **PostgreSQL database** for content storage
- **Section-based** content structure
- **Different image handling** system

### Required Adaptations

1. **Content Source**
   - **Legacy:** Markdown files in `posts/` directory
   - **Current:** PostgreSQL database with sections

2. **Build Process**
   - **Legacy:** `npm run build` (Eleventy)
   - **Current:** Dynamic HTML generation (Flask templates)

3. **Image Management**
   - **Legacy:** `image_library.json` file
   - **Current:** Database-stored image metadata

4. **Status Tracking**
   - **Legacy:** `workflow_status.json` file
   - **Current:** Database workflow tracking

5. **Content Processing**
   - **Legacy:** CSS selector-based HTML extraction
   - **Current:** Template-based HTML generation

## Files Copied

### Core Files
- `blog-core/scripts/post_to_clan.py` - Main publishing script
- `blog-core/legacy_app.py` - Legacy Flask integration
- `blog-core/docs/reference/publishing/tech_briefing.md` - Technical overview
- `blog-core/docs/reference/publishing/publish_clan_help.md` - User help documentation

### Reference Documentation
- `blog-core/docs/reference/publishing/clan_com_publishing_system.md` - This comprehensive guide

## Next Steps

1. **Analyze Current Architecture** - Understand how content is stored and managed
2. **Design Integration Points** - Map legacy functionality to current system
3. **Create Content Adapters** - Convert database content to API format
4. **Implement Status Tracking** - Integrate with current workflow system
5. **Update Image Handling** - Adapt to current image management
6. **Test API Integration** - Verify clan.com API connectivity
7. **Create User Interface** - Build publishing controls in blog-launchpad

## Dependencies

### Python Dependencies
```python
import os
import sys
import subprocess
import json
import requests
import frontmatter
from bs4 import BeautifulSoup, Comment
import tempfile
import logging
from pathlib import Path
import re
import argparse
from urllib.parse import urlparse, urlunparse
import datetime
from dotenv import load_dotenv
```

### External Dependencies
- `requests` - HTTP API calls
- `python-frontmatter` - Markdown front matter parsing
- `beautifulsoup4` - HTML parsing and manipulation
- `python-dotenv` - Environment variable management

## Security Considerations

1. **API Key Management**
   - Store API keys in environment variables
   - Never commit API keys to version control
   - Use `.env` files for local development

2. **File Upload Security**
   - Validate file types and sizes
   - Sanitize file names
   - Use secure file upload endpoints

3. **Content Validation**
   - Validate HTML content before submission
   - Sanitize user-generated content
   - Check for malicious scripts or links

## Performance Considerations

1. **Image Upload Optimization**
   - Compress images before upload
   - Use appropriate image formats (WebP, JPEG)
   - Implement upload progress tracking

2. **API Rate Limiting**
   - Respect clan.com API rate limits
   - Implement retry logic with exponential backoff
   - Cache API responses where appropriate

3. **Build Process Optimization**
   - Cache build artifacts
   - Implement incremental builds
   - Parallelize image uploads

## Troubleshooting

### Common Issues

1. **API Authentication Failures**
   - Check API key validity
   - Verify API user permissions
   - Test API connectivity

2. **Image Upload Failures**
   - Verify image file paths
   - Check file permissions
   - Validate image formats

3. **Content Processing Errors**
   - Check HTML structure
   - Verify CSS selectors
   - Validate front matter format

4. **Build Process Issues**
   - Check npm dependencies
   - Verify Eleventy configuration
   - Check file permissions

### Debug Mode
Enable debug logging by setting log level:
```python
logging.basicConfig(level=logging.DEBUG)
```

### API Testing
Test API connectivity independently:
```bash
curl -X POST https://clan.com/clan/blog_api/uploadImage \
  -F "api_user=blog" \
  -F "api_key=your_key" \
  -F "image_file=@test.jpg"
```
