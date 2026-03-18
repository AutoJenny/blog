# Image Harvesting Additions to Quirky News Plan

This document supplements the main implementation plan with image harvesting, selection, and remote serving functionality.

## Overview

During article harvesting, we collect images from source articles (same-domain only to exclude ads), store captions and credits, provide UI for selecting one image per story, and re-serve images via remote URLs to avoid copyright infringement.

## Phase 1 Additions

### 1.5 Create Image Extraction Service

**File**: `blog-core/newsletter/services/image_extraction_service.py` (new, max 400 lines)

**Purpose**: Extract images from article pages during ingestion

**Input**: 
- Article URL
- Source domain

**Process**:
1. Fetch article HTML page
2. Extract all `<img>` tags using BeautifulSoup
3. Filter images:
   - Must be from same domain as article (exclude ads, trackers, CDNs)
   - Must have `src` attribute (not just data URIs)
   - Prefer images with captions/alt text
4. Extract metadata for each image:
   - Image URL (convert to absolute URL)
   - Caption (from `<figcaption>`, `alt` attribute, or nearby text)
   - Credit (from `data-credit`, `data-photographer`, `class="credit"`, or nearby text)
   - Domain (for validation)

**Output**: 
- Array of image objects: `[{url, caption, credit, domain}, ...]`
- Store in `newsletter_source_item.available_images` JSONB field

**Error Handling**: 
- Gracefully handle missing images, invalid URLs, timeouts
- Log extraction failures but don't block article ingestion

**Checkpoint**: Test image extraction on sample articles, verify images collected with metadata

## Phase 2 Additions

### 2.1 Extend newsletter_source_item Table (Additional Fields)

**File**: `migrations/add_quirky_news_fields.sql` (extend existing migration)

Add to existing ALTER TABLE statement:

```sql
ALTER TABLE newsletter_source_item
ADD COLUMN IF NOT EXISTS available_images JSONB DEFAULT '[]'::jsonb;
```

**Structure**: Array of objects:
```json
[
  {
    "url": "https://example.com/image.jpg",
    "caption": "Local gala event",
    "credit": "Photo: John Smith",
    "domain": "example.com"
  }
]
```

### 2.2 Extend weekly_highlights_items Table (Additional Fields)

**File**: `migrations/create_weekly_highlights_tables.sql` (extend existing migration)

Add to existing CREATE TABLE statement:

```sql
ALTER TABLE weekly_highlights_items
ADD COLUMN IF NOT EXISTS selected_image_url TEXT,
ADD COLUMN IF NOT EXISTS selected_image_caption TEXT,
ADD COLUMN IF NOT EXISTS selected_image_credit TEXT,
ADD COLUMN IF NOT EXISTS remote_image_url TEXT;
```

**Purpose**:
- `selected_image_url`: Original image URL chosen by editor
- `selected_image_caption`: Caption for selected image
- `selected_image_credit`: Credit for selected image
- `remote_image_url`: Re-served URL to avoid copyright issues

## Phase 3 Additions

### 3.3 Integrate Image Extraction into Ingestion Pipeline

**File**: `blog-core/newsletter/jobs/prefetch_sources.py` (extend, keep under 500 lines)

**Integration Point**: After normalizing article, before storing in database

**Process**:
1. Check if article has `access_mode` that permits full HTML fetching
2. If yes, call `image_extraction_service.extract_images(article_url, source_domain)`
3. Store results in `available_images` JSONB field
4. Skip extraction if:
   - Article already has images (deduplication check)
   - Access mode is `rss_only` (no HTML access)
   - Article URL is invalid

**Checkpoint**: Verify images extracted during prefetch job, stored in database

## Phase 8 Additions

### 8.3 Add Image Selection UI

**File**: `templates/newsletter/round_scotland/image_selector.html` (new, max 300 lines)

**Purpose**: Allow editors to select one image per story from available images

**UI Components**:
- Display all available images from `available_images` array
- Show thumbnail previews (lazy-loaded for performance)
- Display caption and credit for each image
- Radio button selection (only one image per item)
- "No image" option
- Save button to persist selection

**File**: `blueprints/newsletter_round_scotland.py` (extend)

Add routes:
- `GET /newsletter/issue/<issue_id>/round-scotland/item/<item_id>/images` - Get available images for item
- `POST /newsletter/issue/<issue_id>/round-scotland/item/<item_id>/select-image` - Save image selection

**Request/Response**:
- GET returns: `{images: [{url, caption, credit}, ...], selected: {url, caption, credit} | null}`
- POST accepts: `{image_url: string | null}` (null = no image)
- POST updates: `selected_image_url`, `selected_image_caption`, `selected_image_credit` in `weekly_highlights_items`

**Integration**: Add image selector to `item_editor.html` template

**Checkpoint**: Verify image selector UI works, selections saved to database

## Phase 9 Additions

### 9.4 Create Remote Image Serving Service

**File**: `blog-core/newsletter/services/remote_image_service.py` (new, max 400 lines)

**Purpose**: Re-serve images via remote URLs to avoid copyright issues

**Process**:
1. Accept original image URL, caption, credit
2. Fetch image from source (with proper user-agent, respect rate limits)
3. Store temporarily (or cache) with metadata:
   - Image binary data
   - Caption
   - Credit
   - Source URL (for attribution)
4. Generate remote URL:
   - Option A: `/newsletter/images/<hash>` (internal serving)
   - Option B: External CDN URL (if configured)
5. Return remote URL for use in newsletter

**Metadata Preservation**: 
- Ensure caption and credit are preserved in remote serving
- Store attribution in database for reference

**Caching**: 
- Cache images to avoid re-fetching
- Use hash of original URL as cache key
- Set appropriate cache headers

**Cleanup**: 
- Periodic cleanup of unused cached images (older than 30 days, not referenced in any issue)

**File**: `blueprints/newsletter_images.py` (new, max 300 lines)

**Route**:
- `GET /newsletter/images/<image_id>` - Serve remote image with proper headers
- Include caption/credit in response headers or metadata
- Set appropriate content-type headers
- Handle 404 gracefully

**Security**:
- Validate image_id to prevent arbitrary file access
- Rate limit requests
- Validate image format (jpg, png, webp only)

**Checkpoint**: Verify remote URLs work, images display correctly in newsletter

### 9.5 Update Configuration Management

**File**: `blog-core/newsletter/config/quirky_news_config.py` (extend)

Add image-related config:
- `IMAGE_EXTRACTION_ENABLED`: Boolean (default: True)
- `MAX_IMAGES_PER_ARTICLE`: Integer (default: 10)
- `IMAGE_EXTRACTION_TIMEOUT`: Seconds (default: 10)
- `IMAGE_CACHE_TTL_DAYS`: Integer (default: 30)
- `REMOTE_IMAGE_BASE_URL`: String (default: `/newsletter/images/`)

## Documentation Updates

### Update Implementation Documentation

**File**: `docs/newsletter/quirky-news-implementation.md` (extend)

Add section:
- Image extraction workflow
- Image selection UI
- Remote serving mechanism
- Copyright compliance approach

### Create Image Handling Documentation

**File**: `docs/newsletter/image-handling.md` (new)

Document:
- Image extraction process
- Domain filtering rules
- Caption and credit extraction heuristics
- Image selection UI workflow
- Remote serving mechanism
- Copyright compliance
- Troubleshooting image issues

## Integration Points Summary

1. **Ingestion**: Extract images during prefetch, store in `available_images`
2. **Selection**: UI allows choosing one image per story
3. **Storage**: Selected image metadata stored in `weekly_highlights_items`
4. **Serving**: Remote URL generated and used in newsletter rendering
5. **Attribution**: Caption and credit preserved throughout pipeline

## Copyright Compliance

- Images are re-served via remote URLs (not hotlinked)
- Captions and credits are preserved and displayed
- Source attribution maintained in database
- Only same-domain images collected (respects source ownership)
- Images cached temporarily, cleaned up after use period

