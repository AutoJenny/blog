# Clan.com API Technical Package Reference

## Overview
This document details the exact technical package structure required for successful uploads to clan.com via their blog API. Based on the working PHP specimen script and current implementation analysis.

## API Endpoints

### 1. Image Upload
**Endpoint:** `POST https://clan.com/clan/blog_api/uploadImage`

**Required Parameters:**
- `api_user`: "blog" (authentication)
- `api_key`: Your API key from environment
- `image`: File upload (multipart/form-data)

**Expected Response:**
```json
{
  "status": "success",
  "message": "File uploaded successfully: https://static.clan.com/media/blog/filename.jpg"
}
```

**Critical:** The response contains the **clan.com media URL** that must be used in thumbnail fields.

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
  "url_key": "post-slug",                   // String - URL-friendly identifier
  "short_content": "Summary text...",       // String - Max 200 characters
  "status": 2,                              // Integer - 2 = enabled, 1 = disabled
  "categories": [14, 15],                   // Array - Category IDs
  "list_thumbnail": "/blog/image.jpg",      // String - Path from /media
  "post_thumbnail": "/blog/image.jpg",      // String - Path from /media
  "meta_title": "SEO Title",                // String - Meta title
  "meta_tags": "tag1,tag2,tag3",           // String - Comma-separated tags
  "meta_description": "SEO description..."  // String - Max 160 characters
}
```

### Field Specifications

#### Title & URL
- **title**: Must match the actual post title exactly
- **url_key**: Must be unique, URL-friendly slug (no spaces, special chars)

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
- **Source**: Must be uploaded via uploadImage API first

#### Meta Fields
- **meta_title**: Usually same as post title
- **meta_tags**: Comma-separated, no spaces after commas
- **meta_description**: Truncated summary, max 160 characters

## HTML Content Requirements

### File Upload
- **Parameter name**: `html_file`
- **Content type**: `text/html`
- **Encoding**: UTF-8
- **Format**: Complete HTML document or post content

### Content Structure
The HTML must include:
1. **Complete post content** with all sections
2. **Working image links** (clan.com URLs, not local paths)
3. **Cross-promotion widgets** (if configured)
4. **Proper HTML structure** (no broken tags)

## Complete Upload Process

### Step 1: Image Preparation
1. **Identify all images** needed for the post
2. **Upload each image** via `uploadImage` API
3. **Extract clan.com URLs** from responses
4. **Map local paths** to clan.com media paths

### Step 2: Content Preparation
1. **Generate complete HTML** with all features
2. **Replace local image paths** with clan.com URLs
3. **Include cross-promotion widgets** if configured
4. **Validate HTML structure** (no broken tags)

### Step 3: Post Creation
1. **Prepare json_args** with all required fields
2. **Use actual thumbnail paths** from uploaded images
3. **Send complete package** via `createPost` API
4. **Handle response** and extract post ID

## Current Implementation Issues

### 1. Thumbnail Paths
- **Problem**: Using placeholder paths (`/blog/default-thumbnail.jpg`)
- **Solution**: Upload images first, use actual clan.com media paths

### 2. Image Processing
- **Problem**: Images not uploaded before post creation
- **Solution**: Process all images first, update paths in HTML

### 3. HTML Content
- **Problem**: Missing cross-promotion widgets and features
- **Solution**: Generate complete HTML matching preview template

### 4. Data Flow
- **Problem**: Image data not populated before publishing
- **Solution**: Find images in file system, upload to clan.com, update paths

## Success Criteria

A successful upload will result in:
1. **All images uploaded** to clan.com media system
2. **Thumbnail fields populated** with actual clan.com paths
3. **Complete HTML content** with working image links
4. **Cross-promotion widgets** displaying correctly
5. **Post published** with all features intact
6. **Frontend receives success** response with clan.com post ID

## Error Handling

### Common Failure Points
1. **Missing required fields** in json_args
2. **Invalid thumbnail paths** (not uploaded to clan.com)
3. **Broken HTML content** (malformed tags, missing images)
4. **Authentication failures** (invalid API key)
5. **Image upload failures** (file not found, upload errors)

### Response Analysis
- **Success**: `{"status": "success", "message": "Blog post created successfully with ID: 123"}`
- **Failure**: `{"status": "error", "message": "Specific error details"}`

## Testing Checklist

Before attempting upload:
- [ ] All required images exist in file system
- [ ] Environment variables configured (CLAN_API_KEY, etc.)
- [ ] HTML content generated and validated
- [ ] Cross-promotion data available (if using widgets)
- [ ] All required fields populated in json_args
- [ ] Image uploads tested and working
- [ ] Thumbnail paths updated with actual clan.com URLs
