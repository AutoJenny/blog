# Component Audit: clan_publisher.py

## File Location
`blog-launchpad/clan_publisher.py`

## Purpose
Handles publishing blog posts to clan.com, including image uploads, HTML generation, and API communication.

## Key Methods

### `process_images(post, sections)`
**Purpose**: Upload all images (header + sections) and create mapping of local paths to clan.com URLs.

**Header Image Processing** (lines 440-490):
1. Extracts `header_path` from `post.get('header_image', {}).get('path')`
2. Converts web path to filesystem using `path_resolver.convert_web_path_to_filesystem(header_path)`
3. **CRITICAL**: Checks if file exists - if not, logs error but continues
4. Uploads image with unique filename: `header_{post_id}_{timestamp}.jpg`
5. Maps `header_path` → `uploaded_url` in `uploaded_images` dict

**Issues Identified**:
1. ⚠️ **HIGH RISK**: If header image file doesn't exist, logs error but continues
   - This means `uploaded_images` won't have header image mapping
   - HTML generation will use local path instead of clan.com URL
   - **This is a silent failure** - no exception raised
2. ⚠️ **RISK**: Path conversion relies on `path_resolver` - if this fails, entire upload fails
3. ✅ Good: Extensive logging for debugging

**Section Image Processing** (lines 492-587):
- Handles Photo-harvesting URLs (Pexels/Unsplash) - downloads and uploads to clan.com CDN
- Handles local section images
- Maps section paths to uploaded URLs

### `create_or_update_post(post, html_content, is_update, uploaded_images)`
**Purpose**: Create or update post on clan.com via API.

**Header Image Thumbnail Logic** (lines 730-782):
1. Extracts `header_image_path` from `post.get('header_image', {}).get('path')`
2. **CRITICAL**: Looks for EXACT match in `uploaded_images` dict
3. If found, extracts media path for thumbnails
4. If not found, uses placeholder: `/blog/placeholder.jpg`

**Issues Identified**:
1. ⚠️ **HIGH RISK**: Exact string matching for header image path
   - If path normalization differs between `process_images` and `create_or_update_post`, match fails
   - Example: `/static/...` vs `static/...` (leading slash difference)
2. ⚠️ **RISK**: No fallback if exact match fails - immediately uses placeholder
3. ⚠️ **RISK**: Extensive logging shows this has been a problem (lines 736-760 show debugging code)

### `get_preview_html_content(post, sections, uploaded_images)`
**Purpose**: Generate HTML using `clan_post_raw.html` template and replace local paths with clan.com URLs.

**Path Replacement Logic** (lines 1514-1593):
1. Creates `path_mapping` from `uploaded_images`
2. Replaces paths in HTML content
3. **CRITICAL**: Uses exact string matching for replacements
   - `src="{local_path}"` → `src="{clan_url}"`
   - Also handles Photo-harvesting URLs with base URL matching

**Issues Identified**:
1. ⚠️ **HIGH RISK**: Exact string matching for path replacement
   - If HTML template uses different path format, replacement fails
   - Example: Template has `/static/...` but `uploaded_images` has `static/...`
2. ⚠️ **RISK**: Multiple replacement strategies (exact match, base URL match) create complexity
3. ✅ Good: Logs remaining `/static/` paths after replacement for debugging

### `publish_to_clan(post, sections)`
**Purpose**: Main method to publish a post - orchestrates image processing, HTML generation, and API call.

**Header Image Handling** (lines 1074-1134):
1. **CRITICAL**: Preserves `header_image` from `post` dict if it exists
2. If not found, attempts to load from database using local `find_header_image_local` function
3. **RISK**: Duplicates logic from `header_image_finder.py` - violates DRY principle

**Issues Identified**:
1. ⚠️ **HIGH RISK**: Duplicate header image finding logic
   - `find_header_image_local` (lines 1086-1112) duplicates `header_image_finder.find_header_image_filesystem`
   - If one is updated, the other may become inconsistent
2. ⚠️ **RISK**: Complex merge logic (lines 1042-1059) tries to preserve header_image but may overwrite it
3. ⚠️ **RISK**: Fallback logic (lines 1158-1199) attempts "forced uploads" if `uploaded_images` is empty
   - This suggests the normal flow is failing silently

## Dependencies
- `config.paths.path_resolver` (critical for path conversion)
- `config.database.db_manager`
- `jinja2` (for template rendering)
- `requests` (for API calls)

## Integration Points
- **Called by**: `publish_orchestrator.py`, `blueprints/launchpad/publishing.py`
- **Calls**: Path resolver, database manager, template renderer

## Recipe-Specific Behavior
**NONE** - This module treats all post types identically.

## Critical Findings

### CRITICAL RISKS
1. **Silent Failure on Missing Header Image**: If header image file doesn't exist, `process_images` logs error but continues. This means:
   - `uploaded_images` won't have header mapping
   - `create_or_update_post` won't find header in mapping
   - Post publishes with placeholder thumbnail instead of actual header
   - **No error is raised** - publication "succeeds" but with wrong image

2. **Path Matching Fragility**: Exact string matching for header image paths is fragile:
   - Normalization differences break matching
   - Leading slash differences break matching
   - Path format differences break matching

3. **Code Duplication**: `find_header_image_local` duplicates `header_image_finder` logic, creating maintenance burden and inconsistency risk.

### HIGH RISKS
1. **Forced Upload Fallback**: The existence of "forced upload" logic (lines 1158-1199) suggests the normal flow is failing. This is a code smell indicating deeper issues.

2. **Complex Merge Logic**: The header_image preservation logic (lines 1042-1059) is complex and error-prone.

## Recommendations
1. **IMMEDIATE**: 
   - Raise exception if header image file doesn't exist (don't silently continue)
   - Normalize all paths before adding to `uploaded_images` dict
   - Remove duplicate `find_header_image_local` - use `header_image_finder` instead

2. **SHORT TERM**:
   - Add path normalization utility function used consistently everywhere
   - Add unit tests for path matching edge cases
   - Document expected path formats

3. **MEDIUM TERM**:
   - Refactor to remove "forced upload" fallback (fix root cause instead)
   - Simplify header_image preservation logic
   - Add integration tests for full publishing flow

