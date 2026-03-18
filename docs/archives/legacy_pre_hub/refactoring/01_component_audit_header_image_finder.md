# Component Audit: header_image_finder.py

## File Location
`blog-launchpad/publish/header_image_finder.py`

## Purpose
Single source of truth for finding header images for posts during publishing.

## Functions

### `find_header_image_filesystem(post_id)`
**Purpose**: Find header image on filesystem when database lookup fails.

**Logic**:
- Checks `project_root/static/content/posts/{post_id}/header/{image_type}/` only
- Image types checked in order: `['optimized', 'watermarked', 'raw']`
- Returns web path (e.g., `/static/content/posts/123/header/optimized/header.jpg`)
- **NO FALLBACKS** - explicitly states "ALL images are in project_root/static/ - no fallbacks"

**Issues Identified**:
1. ✅ Good: Explicitly rejects fallbacks (clear error handling)
2. ⚠️ **RISK**: If path_resolver is used elsewhere, inconsistency could occur
3. ⚠️ **RISK**: No logging of which image_type was found (only logs if found)

### `load_header_image_from_db(post_id)`
**Purpose**: Load header image from database using `post_images` linking table.

**Logic**:
1. **First attempt**: Query `post_images` → `images` table (new schema)
   - Filters: `pi.image_type LIKE 'header%'`
   - Orders by: `header_optimized` (1), `header_watermarked` (2), else (3)
   - Returns first match
2. **Fallback**: Query `post_images` → `image` table (old schema)
   - Same filtering/ordering logic
   - **CRITICAL**: Uses `path` column (not `file_path`)

**Path Normalization**:
```python
header_path = header_path.lstrip('/')
if not header_path.startswith('static/'):
    header_path = 'static/' + header_path.lstrip('/')
header_path = '/' + header_path  # Add leading slash
```

**Issues Identified**:
1. ⚠️ **CRITICAL RISK**: Path normalization happens AFTER database query
   - If database has inconsistent paths, normalization may not fix all cases
   - Example: Database has `blog-images/static/...` → normalized to `/static/blog-images/static/...` (WRONG)
2. ⚠️ **RISK**: Dual schema support (images vs image table) creates complexity
   - No clear migration path documented
   - Could lead to inconsistent data
3. ⚠️ **RISK**: No validation that normalized path actually exists on filesystem
4. ✅ Good: Logging includes repr() for debugging path issues

### `get_header_image(post_id)`
**Purpose**: Main entry point - tries database first, then filesystem.

**Logic**:
1. Call `load_header_image_from_db(post_id)`
2. If None, call `find_header_image_filesystem(post_id)`
3. If filesystem found, return dict with minimal metadata (no alt_text, caption, etc.)

**Issues Identified**:
1. ⚠️ **RISK**: Filesystem fallback returns incomplete metadata
   - Missing: alt_text, caption, width, height
   - Could cause issues in templates that expect these fields
2. ✅ Good: Clear separation of concerns (DB vs filesystem)

## Dependencies
- `config.database.db_manager`
- `os`, `urllib.parse`, `logging`

## Integration Points
- Called by: `publish_orchestrator.py`, `blueprints/launchpad/publishing.py`
- Used in: Publishing workflow, preview generation

## Recipe-Specific Behavior
**NONE** - This module treats all post types identically. Recipe posts are not handled differently.

## Critical Findings

### HIGH RISK
1. **Path Normalization Logic**: The normalization assumes all database paths can be fixed by prepending `static/`. This may not work for:
   - Legacy paths in `blog-images/static/`
   - Absolute paths
   - Paths already starting with `/static/` but in wrong location

2. **Dual Schema Support**: Supporting both `images` and `image` tables indefinitely is a maintenance burden and source of bugs.

### MEDIUM RISK
1. **Incomplete Metadata on Filesystem Fallback**: When falling back to filesystem, metadata is incomplete, which could break templates.

2. **No Validation**: Paths are normalized but never validated against actual filesystem.

## Recommendations
1. **IMMEDIATE**: Add path validation after normalization
2. **SHORT TERM**: Document expected path formats in database
3. **MEDIUM TERM**: Complete migration from `image` to `images` table
4. **ONGOING**: Add unit tests for path normalization edge cases

