# Dual Table Resolution Plan: `image` → `images` Migration

## Current State Analysis

### Schema Comparison

**`image` Table (OLD - Singular)**
- Columns: `id`, `filename`, `path`, `alt_text`, `caption`, `image_prompt`, `original_filename` (maybe)
- Status: Currently used by all code
- Column name: `path` (not `file_path`)

**`images` Table (NEW - Plural)**
- Columns: `id`, `filename`, `original_filename`, `file_path`, `file_size`, `mime_type`, `width`, `height`, `alt_text`, `caption`, `image_prompt`, `notes`, `metadata`, `created_at`, `updated_at`
- Status: Created by migration but not fully adopted
- Column name: `file_path` (not `path`)
- Better schema: Has width/height, metadata, timestamps

### Current Usage

**Code Using `image` Table:**
- `api_generate_header_image` (blueprints/header.py)
- `api_optimize_header_image` (blueprints/header.py)
- `header_image_finder.py` (blog-launchpad/publish/)
- `blueprints/launchpad/publishing.py`
- `backfill_recipe_header_post_images.py`
- Multiple other files (157 matches found)

**Code Using `images` Table:**
- Migration script created it
- `post_images` FK constraint points to `images.id` (but code uses `image.id`)

**Problem:**
- Migration created `images` table with FK constraint
- But all code still uses `image` table
- This creates inconsistency and potential FK constraint violations

## Resolution Strategy

### Decision: Migrate to `images` Table (Plural)

**Rationale:**
1. ✅ Better schema (width, height, metadata, timestamps)
2. ✅ Already created by migration
3. ✅ `post_images` FK already points to it
4. ✅ More future-proof

**Alternative Considered:** Keep `image` table
- ❌ Would require changing FK constraint
- ❌ Would lose better schema features
- ❌ Goes against migration direction

## Migration Plan

### Overview
This plan addresses **three related issues**:
1. **Dual table migration**: `image` → `images` table consolidation
2. **Process unification**: Remove recipe/theme post differences in preview/publishing
3. **Photo-harvesting deprecation**: Archive and remove Photo-harvesting functionality

### Phase 1: Data Migration (Safe - No Code Changes)

**Step 1.1: Audit Current Data**
```sql
-- Count records in each table
SELECT 'image table' as table_name, COUNT(*) as record_count FROM image
UNION ALL
SELECT 'images table' as table_name, COUNT(*) as record_count FROM images;

-- Check for ID conflicts
SELECT i1.id 
FROM image i1
JOIN images i2 ON i1.id = i2.id;

-- Check post_images references
SELECT 
    'post_images pointing to image' as source,
    COUNT(*) as count
FROM post_images pi
JOIN image i ON pi.image_id = i.id
UNION ALL
SELECT 
    'post_images pointing to images' as source,
    COUNT(*) as count
FROM post_images pi
JOIN images i ON pi.image_id = i.id;

-- Check post.header_image_id references
SELECT 
    'post.header_image_id pointing to image' as source,
    COUNT(*) as count
FROM post p
JOIN image i ON p.header_image_id = i.id
UNION ALL
SELECT 
    'post.header_image_id pointing to images' as source,
    COUNT(*) as count
FROM post p
JOIN images i ON p.header_image_id = i.id;
```

**Step 1.2: Migrate Data from `image` to `images`**
```sql
-- Migration script: migrate_image_to_images.sql
BEGIN;

-- Step 1: Handle ID conflicts (if any exist)
-- If images table has records with same IDs, we need to remap
-- For now, assume no conflicts (verify in Step 1.1)

-- Step 2: Insert all records from image to images
-- Map path -> file_path, handle missing columns
INSERT INTO images (
    id,
    filename,
    original_filename,
    file_path,  -- Maps from image.path
    alt_text,
    caption,
    image_prompt,
    created_at,
    updated_at
)
SELECT 
    id,
    filename,
    COALESCE(original_filename, filename) as original_filename,
    path as file_path,  -- Map path column to file_path
    alt_text,
    caption,
    image_prompt,
    COALESCE(created_at, CURRENT_TIMESTAMP) as created_at,
    COALESCE(updated_at, CURRENT_TIMESTAMP) as updated_at
FROM image
ON CONFLICT (id) DO UPDATE SET
    filename = EXCLUDED.filename,
    file_path = EXCLUDED.file_path,
    alt_text = EXCLUDED.alt_text,
    caption = EXCLUDED.caption,
    image_prompt = EXCLUDED.image_prompt,
    updated_at = CURRENT_TIMESTAMP;

-- Step 3: Verify migration
SELECT 
    (SELECT COUNT(*) FROM image) as image_count,
    (SELECT COUNT(*) FROM images) as images_count,
    (SELECT COUNT(*) FROM image) - (SELECT COUNT(*) FROM images) as difference;

-- If difference is 0, migration successful
-- If difference > 0, investigate missing records

COMMIT;
```

**Step 1.3: Update Foreign Key References**
```sql
-- Update post_images.image_id to ensure all point to images table
-- (They should already, but verify)
UPDATE post_images pi
SET image_id = i2.id
FROM image i1
JOIN images i2 ON i1.id = i2.id
WHERE pi.image_id = i1.id
  AND pi.image_id != i2.id;  -- Only update if different

-- Update post.header_image_id to point to images table
UPDATE post p
SET header_image_id = i2.id
FROM image i1
JOIN images i2 ON i1.id = i2.id
WHERE p.header_image_id = i1.id
  AND p.header_image_id != i2.id;  -- Only update if different
```

### Phase 2: Code Migration (Update All References)

**Step 2.1: Create Migration Helper Script**
```python
# scripts/migrate_code_image_to_images.py
"""
Script to find and report all code references to 'image' table
to help with migration to 'images' table.
"""
import os
import re
from pathlib import Path

def find_image_table_references(root_dir):
    """Find all code references to image table."""
    references = []
    
    # Patterns to find
    patterns = [
        r'FROM image\b',
        r'JOIN image\b',
        r'INSERT INTO image\b',
        r'UPDATE image\b',
        r'DELETE FROM image\b',
        r'image\.id\b',
        r'image\.path\b',
        r'image\.filename\b',
    ]
    
    for root, dirs, files in os.walk(root_dir):
        # Skip certain directories
        if any(skip in root for skip in ['venv', '__pycache__', '.git', 'node_modules']):
            continue
            
        for file in files:
            if not file.endswith(('.py', '.sql')):
                continue
                
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                    for i, line in enumerate(lines, 1):
                        for pattern in patterns:
                            if re.search(pattern, line):
                                references.append({
                                    'file': filepath,
                                    'line': i,
                                    'content': line.strip(),
                                    'pattern': pattern
                                })
            except Exception as e:
                print(f"Error reading {filepath}: {e}")
    
    return references

if __name__ == '__main__':
    root = '/Users/autojenny/Documents/projects/blog'
    refs = find_image_table_references(root)
    
    print(f"Found {len(refs)} references to 'image' table:")
    for ref in refs:
        print(f"  {ref['file']}:{ref['line']} - {ref['content']}")
```

**Step 2.2: Update Code Files (Systematic)**

**Priority 1: Core Publishing Files**
1. `blog-launchpad/publish/header_image_finder.py`
   - Change: `JOIN image i` → `JOIN images i`
   - Change: `i.path` → `i.file_path`

2. `blueprints/header.py` - `api_generate_header_image`
   - Change: `UPDATE image` → `UPDATE images`
   - Change: `INSERT INTO image` → `INSERT INTO images`
   - Change: `path` → `file_path` in column names

3. `blueprints/header.py` - `api_optimize_header_image`
   - Change: `UPDATE image` → `UPDATE images`
   - Change: `INSERT INTO image` → `INSERT INTO images`
   - Change: `path` → `file_path`

4. `blueprints/launchpad/publishing.py`
   - Change: `JOIN image i` → `JOIN images i`
   - Change: `i.path` → `i.file_path`

**Priority 2: Supporting Files**
5. `scripts/backfill_recipe_header_post_images.py`
   - Change: `JOIN image i` → `JOIN images i`
   - Change: `i.path` → `i.file_path`

6. All other files found by migration script

**Step 2.3: Update Path Normalization**
- All code that normalizes `path` should normalize `file_path` instead
- Ensure consistent normalization logic

### Phase 3: Testing & Validation

**Step 3.1: Unit Tests**
- Test header image finding with `images` table
- Test header image generation writes to `images` table
- Test publishing reads from `images` table

**Step 3.2: Integration Tests**
- Test full workflow: generate → optimize → publish
- Verify `post_images` records work correctly
- Verify `post.header_image_id` works correctly

**Step 3.3: Data Validation**
```sql
-- Verify all references point to images table
SELECT 'post_images.image_id not in images' as issue, COUNT(*) as count
FROM post_images pi
LEFT JOIN images i ON pi.image_id = i.id
WHERE i.id IS NULL;

SELECT 'post.header_image_id not in images' as issue, COUNT(*) as count
FROM post p
LEFT JOIN images i ON p.header_image_id = i.id
WHERE p.header_image_id IS NOT NULL AND i.id IS NULL;
```

### Phase 4: Process Unification (Remove Recipe/Theme Differences)

**Goal**: Make recipe and theme posts use identical preview/publishing processes after creation prompts.

**Step 4.1: Remove Photo-harvesting from Preview Construction**

**File**: `blueprints/header.py::header_preview()` (lines 462-487)

**Current Code**:
```python
# Skip images for recipe_method section (method image deprecated)
if post_type == 'recipe' and section.get('section_type') == 'recipe_method':
    pass
# For recipe posts, skip Photo-harvesting entirely - only use LLM-generated images
elif post_type != 'recipe':
    # Priority 1: Check Photo-harvesting route (selected_landscape.json)
    # ... Photo-harvesting logic ...
```

**Unified Code**:
```python
# REMOVED: Recipe-specific conditionals
# REMOVED: Photo-harvesting check (lines 467-487)
# Priority 1: Database link (post_images) - for ALL post types
# Priority 2: Filesystem check - for ALL post types
```

**Changes**:
- Remove lines 462-487 (recipe conditionals + Photo-harvesting)
- Use same image selection logic for all post types
- Priority: Database → Filesystem (no Photo-harvesting)

**Step 4.2: Remove Photo-harvesting from Publishing**

**File**: `blueprints/launchpad/publishing.py::get_post_sections_with_images()` (lines 108-156)

**Current Code**:
```python
# Priority 1: Check Photo-harvesting route (selected_landscape.json)
try:
    photo_json_path = f"static/content/posts/{post_id}/sections/{section_dict['id']}/optimized/selected_landscape.json"
    if os.path.exists(photo_json_path):
        # ... Photo-harvesting logic ...
```

**Unified Code**:
```python
# REMOVED: Photo-harvesting check (lines 108-156)
# Priority 1: Database link (post_images)
# Priority 2: Filesystem check
```

**Changes**:
- Remove lines 108-156 (Photo-harvesting logic)
- Use same image selection for all post types

**Step 4.3: Remove Photo-harvesting from Publishing Image Processing**

**File**: `blog-launchpad/clan_publisher.py::process_images()` (lines 502-558)

**Current Code**:
```python
# Handle Photo-harvesting URLs (Pexels/Unsplash) - download and upload to clan.com CDN
if section_path.startswith(('http://', 'https://')):
    # ... Photo-harvesting download/upload logic ...
```

**Unified Code**:
```python
# REMOVED: Photo-harvesting URL handling (lines 502-558)
# Only process local file paths
# If URL detected, log warning and skip (or raise error)
```

**Changes**:
- Remove Photo-harvesting URL handling
- Only process local file paths
- Add validation to reject URLs

**Step 4.4: Unify Author Assignment**

**Files**:
- `blueprints/header.py` (line 340)
- `blog-launchpad/clan_publisher.py` (line 1449)

**Current Code**:
```python
if post_type == 'recipe':
    post['author_name'] = 'Marion MacLeod'
else:
    post['author_name'] = 'Caitrin Stewart'
```

**Unified Code**:
```python
# Use post.author_id from database
# Or: Use taxonomy-based author assignment (not post-type based)
# Remove recipe-specific conditional
```

**Changes**:
- Remove recipe-specific author assignment
- Use `post.author_id` from database
- Or: Make author assignment based on taxonomy, not post type

**Step 4.5: Unify Title Generation (Optional)**

**File**: `blueprints/header.py::api_compile_header_prompt()` (line 666)

**Current Code**:
```python
if post_type == 'recipe':
    # Use recipe title directly from calendar_recipes
    # Different generation logic
```

**Unified Code**:
```python
# Use same LLM-based title generation for all posts
# Or: Make title source configurable via taxonomy
```

**Changes**:
- Remove recipe-specific title generation
- Use same logic for all post types
- Or: Make configurable via taxonomy

**Step 4.6: Consolidate Publishing Endpoints**

**File**: `blog-launchpad/publish/publish_endpoint.py`

**Current Code**:
```python
@bp.route('/recipe/<int:post_id>', methods=['POST'])
def publish_recipe_post(post_id):
    # Validates recipe type
    # Calls same publish_post_to_clan()
```

**Unified Code**:
```python
# Remove separate recipe endpoint
# Use single endpoint for all post types
# Validation can check post type but use same logic
```

**Changes**:
- Remove `/recipe/<post_id>` endpoint
- Use single endpoint for all post types
- Keep validation but use same publishing logic

### Phase 5: Photo-harvesting Deprecation & Archival

**Goal**: Completely remove Photo-harvesting functionality and archive related files.

**Step 5.1: Identify All Photo-harvesting Components**

**Code Files**:
- `utils/photo_apis.py` - Photo API clients
- `utils/photo_apis_adapter.py` - Photo API adapter
- `utils/photo_harvesting_storage.py` - Photo storage utilities
- `utils/photo_search_store.py` - Photo search storage
- `blueprints/authoring_api_photography.py` - Photo-harvesting API routes
- `blueprints/header.py` - Photo-search endpoints (lines 3418-3706+)
- `blueprints/imaging.py` - Photo selection routes

**Templates**:
- `templates/imaging/includes/photo_search_panel.html`
- `templates/authoring/includes/output_panel_photo_harvesting.html`
- `templates/imaging/sections/photo_selection.html`

**Static Files**:
- `static/js/imaging/photo-search-panel.js`
- `static/js/imaging/photo-results-panel.js`
- `static/js/imaging/photo-selection-panel.js`
- `static/js/header/header-photo-harvesting.js`
- `static/js/header/header-image-photo-harvesting.js`
- `static/js/authoring/photo-harvesting-output-panel.js`
- `static/css/imaging/photo-selection.css`

**Data Files**:
- `static/content/posts/*/sections/*/optimized/selected_landscape.json`
- `static/content/posts/*/sections/*/optimized/selected_portrait.json`
- `static/content/posts/*/sections/*/raw/photo_search_results*.json`
- `static/content/posts/*/header/optimized/selected_*.json`
- `static/content/posts/*/header/raw/photo_search_results*.json`

**Database**:
- Check for any Photo-harvesting related columns/tables
- Check for Photo-harvesting metadata in `post_section` or `images` tables

**Step 5.2: Archive Photo-harvesting Files**

**Create Archive Structure**:
```
ARCHIVED_PHOTO_HARVESTING/
├── code/
│   ├── utils/
│   │   ├── photo_apis.py
│   │   ├── photo_apis_adapter.py
│   │   ├── photo_harvesting_storage.py
│   │   └── photo_search_store.py
│   ├── blueprints/
│   │   ├── authoring_api_photography.py
│   │   └── header.py (photo-search routes only)
│   └── blueprints/imaging.py (photo selection routes)
├── templates/
│   ├── imaging/includes/photo_search_panel.html
│   ├── authoring/includes/output_panel_photo_harvesting.html
│   └── imaging/sections/photo_selection.html
├── static/
│   ├── js/imaging/photo-*.js
│   ├── js/header/*photo*.js
│   ├── js/authoring/photo-*.js
│   └── css/imaging/photo-selection.css
├── migrations/
│   └── [Photo-harvesting related migrations]
└── README.md (explains what was archived and why)
```

**Archive Script**:
```bash
#!/bin/bash
# scripts/archive_photo_harvesting.sh

ARCHIVE_DIR="ARCHIVED_PHOTO_HARVESTING"
mkdir -p "$ARCHIVE_DIR"/{code/utils,code/blueprints,templates,static/js,static/css,migrations}

# Archive code files
cp utils/photo_apis.py "$ARCHIVE_DIR/code/utils/"
cp utils/photo_apis_adapter.py "$ARCHIVE_DIR/code/utils/"
cp utils/photo_harvesting_storage.py "$ARCHIVE_DIR/code/utils/"
cp utils/photo_search_store.py "$ARCHIVE_DIR/code/utils/"
cp blueprints/authoring_api_photography.py "$ARCHIVE_DIR/code/blueprints/"

# Archive templates
cp templates/imaging/includes/photo_search_panel.html "$ARCHIVE_DIR/templates/"
cp templates/authoring/includes/output_panel_photo_harvesting.html "$ARCHIVE_DIR/templates/"
cp templates/imaging/sections/photo_selection.html "$ARCHIVE_DIR/templates/"

# Archive static files
cp static/js/imaging/photo-*.js "$ARCHIVE_DIR/static/js/" 2>/dev/null
cp static/js/header/*photo*.js "$ARCHIVE_DIR/static/js/" 2>/dev/null
cp static/js/authoring/photo-*.js "$ARCHIVE_DIR/static/js/" 2>/dev/null
cp static/css/imaging/photo-selection.css "$ARCHIVE_DIR/static/css/" 2>/dev/null

# Create README
cat > "$ARCHIVE_DIR/README.md" << 'EOF'
# Photo-harvesting Archive

## What Was Archived
This directory contains Photo-harvesting functionality that was deprecated and removed.

## Why Archived
Photo-harvesting (Pexels/Unsplash integration) was deprecated to:
- Unify recipe and theme post processes
- Simplify image pipeline (LLM-generated images only)
- Reduce external dependencies
- Eliminate code duplication

## When Archived
[Date]

## Recovery
If Photo-harvesting functionality is needed:
1. Review archived files
2. Identify required functionality
3. Re-implement if necessary (don't just restore)
EOF

echo "Photo-harvesting files archived to $ARCHIVE_DIR"
```

**Step 5.3: Remove Photo-harvesting Code**

**Files to Delete/Modify**:
1. **Delete Files**:
   - `utils/photo_apis.py`
   - `utils/photo_apis_adapter.py`
   - `utils/photo_harvesting_storage.py`
   - `utils/photo_search_store.py`
   - `blueprints/authoring_api_photography.py`
   - `static/js/imaging/photo-*.js`
   - `static/js/header/*photo*.js`
   - `static/js/authoring/photo-*.js`
   - `static/css/imaging/photo-selection.css`
   - `templates/imaging/includes/photo_search_panel.html`
   - `templates/authoring/includes/output_panel_photo_harvesting.html`
   - `templates/imaging/sections/photo_selection.html`

2. **Modify Files** (Remove Photo-harvesting routes/logic):
   - `blueprints/header.py` - Remove photo-search routes (lines 3418-3706+)
   - `blueprints/imaging.py` - Remove photo selection routes
   - `blueprints/launchpad/publishing.py` - Remove Photo-harvesting check (lines 108-156)
   - `blog-launchpad/clan_publisher.py` - Remove Photo-harvesting URL handling (lines 502-558)
   - `blueprints/header.py` - Remove Photo-harvesting from preview (lines 467-487)

**Step 5.4: Archive Photo-harvesting Data Files**

**Script to Archive JSON Files**:
```python
# scripts/archive_photo_harvesting_data.py
"""
Archive Photo-harvesting JSON files to archive directory.
"""
import os
import shutil
import json
from pathlib import Path

def archive_photo_harvesting_data():
    """Archive all Photo-harvesting JSON files."""
    archive_dir = Path("ARCHIVED_PHOTO_HARVESTING/data")
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    static_dir = Path("static/content/posts")
    archived_count = 0
    
    # Find all Photo-harvesting JSON files
    patterns = [
        "**/selected_landscape.json",
        "**/selected_portrait.json",
        "**/photo_search_results*.json"
    ]
    
    for pattern in patterns:
        for json_file in static_dir.glob(pattern):
            # Create archive path preserving structure
            relative_path = json_file.relative_to(static_dir)
            archive_path = archive_dir / relative_path
            archive_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Copy file
            shutil.copy2(json_file, archive_path)
            archived_count += 1
            print(f"Archived: {json_file} -> {archive_path}")
    
    print(f"\nArchived {archived_count} Photo-harvesting JSON files")
    return archived_count

if __name__ == '__main__':
    archive_photo_harvesting_data()
```

**Step 5.5: Remove Photo-harvesting from Database**

**Check for Photo-harvesting Metadata**:
```sql
-- Check if any columns reference Photo-harvesting
SELECT column_name, data_type 
FROM information_schema.columns 
WHERE table_name IN ('post_section', 'images', 'post')
  AND (column_name LIKE '%photo%' OR column_name LIKE '%harvest%');

-- Check for Photo-harvesting data in JSONB columns
SELECT id, section_type, post_section_elements
FROM post_section
WHERE post_section_elements::text LIKE '%photo%'
   OR post_section_elements::text LIKE '%pexels%'
   OR post_section_elements::text LIKE '%unsplash%';
```

**If Found**: Document and optionally migrate to archive format.

**Step 5.6: Remove Photo-harvesting Environment Variables**

**Check `.env` files**:
- `PEXELS_API_KEY`
- `UNSPLASH_ACCESS_KEY`

**Action**: Document in archive README, remove from `.env` files.

**Step 5.7: Update Documentation**

**Files to Update**:
- Remove Photo-harvesting references from all docs
- Update pipeline documentation
- Update image generation documentation

### Phase 6: Cleanup (After Validation)

**Step 6.1: Remove `image` Table**
```sql
-- ONLY after confirming all data migrated and code updated
BEGIN;

-- Verify no remaining references
SELECT 'post_images still pointing to image' as issue, COUNT(*) as count
FROM post_images pi
JOIN image i ON pi.image_id = i.id;

SELECT 'post.header_image_id still pointing to image' as issue, COUNT(*) as count
FROM post p
JOIN image i ON p.header_image_id = i.id;

-- If both return 0, safe to drop
DROP TABLE IF EXISTS image CASCADE;

COMMIT;
```

**Step 4.2: Update Documentation**
- Update schema documentation
- Update code comments
- Update migration notes

## Implementation Checklist

### Pre-Migration
- [ ] Backup database
- [ ] Run audit queries (Step 1.1)
- [ ] Verify no ID conflicts
- [ ] Document current state
- [ ] Identify all Photo-harvesting components (Step 5.1)

### Data Migration (Phase 1)
- [ ] Run migration script (Step 1.2)
- [ ] Verify data migrated correctly
- [ ] Update FK references (Step 1.3)
- [ ] Verify all references point to `images`

### Code Migration (Phase 2)
- [ ] Run migration helper script (Step 2.1)
- [ ] Update Priority 1 files (`image` → `images`)
- [ ] Update Priority 2 files
- [ ] Update all other files
- [ ] Update path normalization logic

### Process Unification (Phase 4)
- [ ] Remove Photo-harvesting from preview (Step 4.1)
- [ ] Remove Photo-harvesting from publishing (Step 4.2)
- [ ] Remove Photo-harvesting from image processing (Step 4.3)
- [ ] Unify author assignment (Step 4.4)
- [ ] Unify title generation (Step 4.5) - Optional
- [ ] Consolidate publishing endpoints (Step 4.6)

### Photo-harvesting Deprecation (Phase 5)
- [ ] Archive Photo-harvesting files (Step 5.2)
- [ ] Remove Photo-harvesting code (Step 5.3)
- [ ] Archive Photo-harvesting data (Step 5.4)
- [ ] Remove Photo-harvesting from database (Step 5.5)
- [ ] Remove Photo-harvesting env variables (Step 5.6)
- [ ] Update documentation (Step 5.7)

### Testing (Phase 3)
- [ ] Run unit tests
- [ ] Run integration tests
- [ ] Test recipe post workflow (should match theme workflow)
- [ ] Test theme post workflow
- [ ] Verify no Photo-harvesting references remain
- [ ] Verify data validation queries

### Cleanup (Phase 6)
- [ ] Verify no remaining `image` references
- [ ] Drop `image` table (Step 6.1)
- [ ] Update documentation (Step 6.2)
- [ ] Commit changes

## Risk Mitigation

### Risks
1. **Data Loss**: If migration fails
   - **Mitigation**: Full database backup before migration
   - **Rollback**: Restore from backup

2. **ID Conflicts**: If `images` table has conflicting IDs
   - **Mitigation**: Audit in Step 1.1
   - **Solution**: Remap IDs or use sequence

3. **Code Misses**: Some files not updated
   - **Mitigation**: Comprehensive search script
   - **Validation**: Test all code paths

4. **FK Constraint Violations**: If references point to wrong table
   - **Mitigation**: Update FK references in Step 1.3
   - **Validation**: Run validation queries

### Rollback Plan
1. Restore database from backup
2. Revert code changes
3. Investigate what went wrong
4. Fix issues and retry

## Timeline Estimate

- **Phase 1 (Data Migration)**: 2-4 hours
- **Phase 2 (Code Migration)**: 4-8 hours
- **Phase 3 (Testing)**: 4-6 hours
- **Phase 4 (Process Unification)**: 6-10 hours
- **Phase 5 (Photo-harvesting Deprecation)**: 4-6 hours
- **Phase 6 (Cleanup)**: 1-2 hours

**Total**: 21-36 hours

## Success Criteria

### Schema Migration
1. ✅ All data migrated from `image` to `images`
2. ✅ All code uses `images` table
3. ✅ All FK references point to `images`
4. ✅ `image` table removed

### Process Unification
5. ✅ Recipe and theme posts use identical preview construction
6. ✅ Recipe and theme posts use identical publishing process
7. ✅ No recipe-specific conditionals in preview/publishing code
8. ✅ Author assignment unified (not post-type based)

### Photo-harvesting Deprecation
9. ✅ All Photo-harvesting code archived
10. ✅ All Photo-harvesting code removed
11. ✅ All Photo-harvesting data files archived
12. ✅ No Photo-harvesting references in codebase

### Testing
13. ✅ All tests pass
14. ✅ Recipe post workflow matches theme post workflow
15. ✅ No regressions in functionality
16. ✅ No Photo-harvesting functionality accessible

## Next Steps

1. **Review this plan** - Get approval
2. **Use implementation plan** - Follow `/docs/refactoring/13_IMPLEMENTATION_PLAN.md` for step-by-step execution
3. **Create migration scripts** - Implement Phase 1
4. **Test on staging** - Verify migration works
5. **Execute on production** - With backup
6. **Monitor** - Watch for issues

## Implementation Guide

**For step-by-step execution**, use: `/docs/refactoring/13_IMPLEMENTATION_PLAN.md`

The implementation plan includes:
- Detailed checkpoints at each step
- Testing reminders
- Commit points
- Rollback procedures
- Validation steps
- Success criteria

**Use the implementation plan during execution** to ensure nothing is missed.

