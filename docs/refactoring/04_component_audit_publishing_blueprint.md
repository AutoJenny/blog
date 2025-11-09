# Component Audit: blueprints/launchpad/publishing.py

## File Location
`blueprints/launchpad/publishing.py`

## Purpose
Flask blueprint providing publishing-related routes and functionality.

## Key Functions

### `get_post_with_development(post_id)`
**Purpose**: Fetch post with development data and include image paths.

**Header Image Logic** (lines 39-75):
1. **First attempt**: Query `post_images` → `image` table for `header_optimized`
   - Uses `pi.section_id IS NULL AND pi.image_type = 'header_optimized'`
   - Gets path, alt_text, caption, filename from `image` table
2. **Fallback**: Calls `find_header_image(post_id)` (local function, not from header_image_finder)
3. **RISK**: Uses `image` table (singular, old schema) not `images` table (plural, new schema)

**Issues Identified**:
1. ⚠️ **HIGH RISK**: Uses old `image` table instead of new `images` table
   - Inconsistent with `header_image_finder.py` which uses `images` table
   - May miss header images stored in new schema
2. ⚠️ **RISK**: Fallback uses local `find_header_image` function (line 192) which duplicates logic

### `find_header_image(post_id)` (local function, line 192)
**Purpose**: Find header image for a post (local implementation).

**Logic**:
1. Uses `path_resolver.get_header_image_path(post_id, image_type)`
2. Checks filesystem for image files
3. URL-encodes filename
4. **Fallback**: Checks legacy path `/Users/autojenny/Documents/projects/blog/blog-images/static/images/posts/{post_id}/header.jpg`

**Issues Identified**:
1. ⚠️ **HIGH RISK**: Hardcoded absolute path fallback (line 214)
   - Not portable across environments
   - May not exist in production
2. ⚠️ **RISK**: Duplicates `header_image_finder.find_header_image_filesystem` logic
3. ⚠️ **RISK**: URL-encodes filename (line 210) but `header_image_finder` doesn't (line 40)

### `publish_post_to_clan(post_id)` (Flask route, line 225)
**Purpose**: Publish a post to clan.com (Flask endpoint).

**Header Image Handling** (lines 282-292):
1. Calls local `find_header_image(post_id)` (not from header_image_finder)
2. If found, creates header_image dict with metadata from database
3. **CRITICAL**: Uses different function than `publish_orchestrator.py`

**Issues Identified**:
1. ⚠️ **CRITICAL RISK**: Uses different header image finding logic than orchestrator
   - This route calls local `find_header_image`
   - Orchestrator calls `header_image_finder.get_header_image`
   - **Inconsistent behavior** between Flask route and orchestrator
2. ⚠️ **RISK**: Creates header_image dict manually instead of using `get_header_image`
3. ⚠️ **RISK**: No validation that header_image path exists

### `get_post_sections_with_images(post_id)`
**Purpose**: Fetch sections with complete image metadata.

**Image Priority Logic** (lines 108-186):
1. **Priority 1**: Photo-harvesting route (selected_landscape.json)
2. **Priority 2**: Database link (post_images)
3. **Priority 3**: Filesystem fallback

**Issues Identified**:
1. ✅ Good: Clear priority order
2. ⚠️ **RISK**: Complex logic with multiple fallbacks - hard to debug

## Dependencies
- `config.database.db_manager`
- `config.paths.path_resolver`
- `clan_publisher.ClanPublisher` (imported dynamically, line 389)

## Integration Points
- **Flask routes**: `/publishing`, `/api/publishing/publish/<post_id>`, etc.
- **Calls**: `ClanPublisher`, local `find_header_image`, database queries

## Recipe-Specific Behavior
**NONE** - This module treats all post types identically.

## Critical Findings

### CRITICAL RISKS
1. **Inconsistent Header Image Finding**: 
   - This blueprint uses local `find_header_image` function
   - `publish_orchestrator.py` uses `header_image_finder.get_header_image`
   - **Different implementations = different results**
   - Recipe posts may get different header images depending on which code path is used

2. **Old Schema Usage**: Uses `image` table (singular) instead of `images` table (plural)
   - May miss header images stored in new schema
   - Inconsistent with rest of codebase

3. **Hardcoded Paths**: Absolute path fallback is not portable

### HIGH RISKS
1. **Code Duplication**: Multiple implementations of header image finding logic
2. **No Validation**: Header image paths are not validated before use

## Recommendations
1. **IMMEDIATE**: 
   - Replace local `find_header_image` with `header_image_finder.get_header_image`
   - Update `get_post_with_development` to use `images` table (plural)
   - Remove hardcoded absolute path fallback

2. **SHORT TERM**:
   - Consolidate all header image finding to use `header_image_finder` module
   - Add path validation before use
   - Add unit tests for header image finding consistency

3. **MEDIUM TERM**:
   - Refactor to remove code duplication
   - Document which function is authoritative for header image finding

