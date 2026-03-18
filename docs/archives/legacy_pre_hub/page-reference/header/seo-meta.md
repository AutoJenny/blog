# SEO & Meta Page - Technical Reference

## Page Overview

**URL**: `/header/posts/<int:post_id>/seo-meta`  
**Blueprint**: `header`  
**Template**: `header/seo_meta.html`  
**Stage**: Header (Stage 5 of 5)  
**Substage**: SEO & Meta (Substage 3 of 5)  
**Purpose**: Generate and manage SEO metadata for blog posts

### Workflow Position
- **Preceded by**: Header Image substage (creates main header image)
- **Current**: SEO & Meta substage (generates SEO metadata)
- **Followed by**: Publishing Details substage (sets author, dates, status)
- **Finally**: Final Review substage (comprehensive review before publishing)

## Technical Architecture

### Flask Route Handler
```python
@bp.route('/posts/<int:post_id>/seo-meta')
def header_seo_meta(post_id):
    """SEO & Meta substage - Generate SEO metadata"""
    return render_template('header/seo_meta.html', post_id=post_id, blueprint_name='header')
```

### Template Structure
- **Base Template**: `base.html` (dark theme)
- **Main Template**: `header/seo_meta.html`
- **Includes**: 4 specialized panel templates
- **JavaScript**: 4 main JavaScript modules

### Panel Structure

The page displays six meta items grouped into two sections:

1. **HTML Meta Tags Panel** (`meta_title_panel.html`)
   - `meta_title`: HTML page title (max 60 characters)
   - `meta_description`: HTML meta description (max 160 characters)
   - `meta_tags`: Comma-separated keywords (5-8 tags)

2. **Open Graph Meta Panel** (`og_meta_panel.html`)
   - `meta_image`: URL to header image
   - `meta_type`: Content type (typically "article")
   - `meta_site_name`: Site name (e.g., "Clan.com Blog")

3. **SEO Analysis Panel** (`seo_analysis_panel.html`)
   - Placeholder for future SEO scoring and recommendations

4. **Output Panel** (`output_panel_seo_meta.html`)
   - Placeholder for output display

## Database Operations

### Core Content Tables

#### `post` Table Operations
```sql
-- Update SEO metadata
UPDATE post 
SET meta_title = %s,
    meta_description = %s,
    meta_tags = %s,
    meta_image = %s,
    updated_at = CURRENT_TIMESTAMP
WHERE id = %s

-- Retrieve SEO metadata
SELECT meta_title, meta_description, meta_tags,
       meta_image, meta_type, meta_site_name
FROM post
WHERE id = %s
```

#### `image` Table Operations
```sql
-- Get header image path for OG image
SELECT i.path 
FROM post p
JOIN image i ON p.header_image_id = i.id
WHERE p.id = %s
```

#### `post_section` Table Operations
```sql
-- Get section headings for context
SELECT section_heading
FROM post_section
WHERE post_id = %s
ORDER BY order_index
```

## API Endpoints

### Generate SEO Meta Data
```http
POST /header/api/posts/<post_id>/generate-seo-meta
Content-Type: application/json

Response:
{
  "success": true,
  "meta_title": "Short compelling title",
  "meta_description": "Brief engaging description",
  "meta_tags": "tag1, tag2, tag3",
  "meta_image": "https://clan.com/path/to/image.jpg",
  "meta_type": "article",
  "meta_site_name": "Clan.com Blog"
}
```

**Description**: 
- Generates SEO metadata using Ollama LLM
- Fetches post title, summary, and section headings for context
- Saves generated data to `post` table

**Input Context**:
- Post title and summary (from "Title & Summary" page)
- Section headings (from "Planning/Concept/Titling" page)

**LLM Output**:
- Generates optimized meta title (≤60 chars)
- Generates meta description (≤160 chars)
- Generates 5-8 relevant meta tags

### Get Meta Data
```http
GET /header/api/posts/<post_id>/get-meta-data

Response:
{
  "meta_title": "...",
  "meta_description": "...",
  "meta_tags": "...",
  "meta_image": "...",
  "meta_type": "...",
  "meta_site_name": "..."
}
```

**Description**: Retrieves existing SEO metadata from `post` table

## JavaScript Modules

### Main Page Script (`seo-meta-page.js`)
- Handles "Generate Meta Data" button click
- Calls `/header/api/posts/${postId}/generate-seo-meta`
- Populates UI fields with generated data
- Error handling and user feedback

### Meta Title Panel Script (`meta-title-panel.js`)
- Loads existing meta title, description, and tags on page load
- Populates input fields with saved data

### OG Meta Panel Script (`og-meta-panel.js`)
- Loads existing meta image, type, and site name on page load
- Populates input fields with saved data

## LLM Integration

### Prompt Structure
The LLM receives:
```
Generate SEO metadata for this blog post:

Post Title: {post_title}

Summary: {post_summary}

Section Structure:
{section_1_heading}
{section_2_heading}
...

Generate:
1. A compelling HTML meta title (max 60 characters)
2. A concise HTML meta description (max 160 characters)
3. Relevant meta tags (comma-separated, 5-8 tags)

Return in JSON format:
{
  "meta_title": "Short compelling title",
  "meta_description": "Brief engaging description",
  "meta_tags": "tag1, tag2, tag3, tag4, tag5"
}
```

### LLM Service Integration
- **Provider**: Ollama
- **Model**: `llama3.2:latest`
- **Context Type**: `seo_meta_generation`
- **Step ID**: 66
- **Interception**: Stores raw LLM request/response for debugging

### JSON Parsing
- Extracts JSON from code blocks (```json ... ```)
- Fallback: Parses JSON without code blocks
- Handles malformed responses gracefully
- Error logging for debugging

## Open Graph Meta

### Required Fields
- **meta_image**: Header image URL
- **meta_type**: Typically "article" for blog posts
- **meta_site_name**: Site identifier

### Auto-population
- `meta_image`: Retrieved from header image path
- `meta_type`: Hardcoded as "article"
- `meta_site_name`: Hardcoded as "Clan.com Blog"

## Key Features

### Automated Generation
- **Single Button**: "Generate Meta Data" button triggers complete generation
- **Context Integration**: Uses post title, summary, and section structure
- **LLM-Powered**: Generates optimized metadata using Ollama
- **Auto-save**: Automatically saves to database on generation

### SEO Optimization
- **Character Limits**: Enforces standard SEO limits
  - Meta title: ≤60 characters
  - Meta description: ≤160 characters
- **Tag Selection**: 5-8 relevant, comma-separated tags
- **Content Analysis**: Uses full post context for accurate tagging

### User Experience
- **Two-Panel Layout**: Clear separation of HTML meta and OG meta
- **Load Existing**: Retrieves and displays saved metadata on page load
- **One-Click Generation**: Single button for complete SEO setup
- **Error Handling**: Comprehensive error messages and logging

## Technical Specifications

### Database Fields
Stored in `post` table:
- `meta_title` (TEXT)
- `meta_description` (TEXT)
- `meta_tags` (TEXT)
- `meta_image` (TEXT)
- `meta_type` (TEXT)
- `meta_site_name` (TEXT)

### API Response Time
- LLM call: ~2-5 seconds
- Database save: <100ms
- Total: ~2-6 seconds

### Error Handling
- **LLM Failures**: Returns 500 with error details
- **JSON Parsing Failures**: Logs error, shows fallback message
- **Database Failures**: Transaction rollback, error logging

## Future Enhancements

### Planned Features
- **SEO Analysis**: Real-time scoring and recommendations
- **Tag Suggestions**: AI-powered tag recommendations
- **Character Counter**: Visual feedback for character limits
- **Preview**: How the meta data will appear in search results
- **Social Media Preview**: How the post will appear when shared

### Technical Improvements
- **Caching**: Cache generated meta data
- **Validation**: Strict character limit enforcement
- **Audit Trail**: Track changes to meta data
- **A/B Testing**: Test different meta variations

## Related Documentation

- **[Header Image Page](./header-image.md)**: Header image generation
- **[System Overview](../system-overview.md)**: Overall system architecture
- **[API Reference](../api_reference.md)**: Complete API documentation
- **[Database Architecture](../database_architecture.md)**: Database structure
