# Unified Plan Summary: Schema Migration + Process Unification + Photo-harvesting Deprecation

## Overview
This comprehensive plan addresses **three related issues** in a single coordinated effort:

1. **Dual Table Migration**: Consolidate `image` → `images` table
2. **Process Unification**: Make recipe and theme posts use identical preview/publishing
3. **Photo-harvesting Deprecation**: Archive and remove Photo-harvesting entirely

## Why Unified Approach?

**Benefits**:
- ✅ Fixes schema foundation first (enables process unification)
- ✅ Removes Photo-harvesting (simplifies process unification)
- ✅ Single coordinated effort (reduces risk of inconsistencies)
- ✅ Comprehensive testing at end (catches all issues together)

**Risks if Done Separately**:
- Process unification might break if schema issues remain
- Photo-harvesting removal might break if process differences remain
- Multiple deployments increase risk

## Plan Structure

### Phase 1: Data Migration (2-4 hours)
**Goal**: Migrate all data from `image` to `images` table safely

**Steps**:
1. Audit current data state
2. Migrate records (`path` → `file_path`)
3. Update FK references

**Outcome**: Database schema unified, ready for code changes

---

### Phase 2: Code Migration (4-8 hours)
**Goal**: Update all code to use `images` table

**Steps**:
1. Find all `image` table references
2. Update to `images` table
3. Update column names (`path` → `file_path`)
4. Update path normalization

**Outcome**: All code uses unified schema

---

### Phase 3: Testing (4-6 hours)
**Goal**: Verify schema migration works

**Steps**:
1. Unit tests
2. Integration tests
3. Data validation

**Outcome**: Schema migration verified

---

### Phase 4: Process Unification (6-10 hours)
**Goal**: Remove recipe/theme post differences in preview/publishing

**Changes**:

1. **Remove Photo-harvesting from Preview** (`blueprints/header.py`)
   - Remove lines 462-487 (recipe conditionals + Photo-harvesting)
   - Use same image selection for all post types
   - Priority: Database → Filesystem (no Photo-harvesting)

2. **Remove Photo-harvesting from Publishing** (`blueprints/launchpad/publishing.py`)
   - Remove lines 108-156 (Photo-harvesting check)
   - Use same image selection for all post types

3. **Remove Photo-harvesting from Image Processing** (`clan_publisher.py`)
   - Remove lines 502-558 (Photo-harvesting URL handling)
   - Only process local file paths

4. **Unify Author Assignment**
   - Remove recipe-specific author assignment
   - Use `post.author_id` from database

5. **Unify Title Generation** (Optional)
   - Remove recipe-specific title generation
   - Use same logic for all post types

6. **Consolidate Publishing Endpoints**
   - Remove separate `/recipe/<post_id>` endpoint
   - Use single endpoint for all post types

**Outcome**: Recipe and theme posts use identical processes

---

### Phase 5: Photo-harvesting Deprecation (4-6 hours)
**Goal**: Archive and remove all Photo-harvesting functionality

**Steps**:

1. **Archive Files** (using provided scripts):
   - Code: `utils/photo_*.py`, `blueprints/authoring_api_photography.py`
   - Templates: Photo search/selection panels
   - Static: Photo-harvesting JS/CSS files
   - Data: All `selected_*.json` and `photo_search_results*.json` files

2. **Remove Code**:
   - Delete Photo-harvesting utility files
   - Remove Photo-harvesting routes from blueprints
   - Remove Photo-harvesting logic from preview/publishing

3. **Clean Database**:
   - Check for Photo-harvesting metadata
   - Archive if found

4. **Remove Environment Variables**:
   - `PEXELS_API_KEY`
   - `UNSPLASH_ACCESS_KEY`

**Outcome**: Photo-harvesting completely removed, all files archived

---

### Phase 6: Cleanup (1-2 hours)
**Goal**: Final cleanup and validation

**Steps**:
1. Remove `image` table
2. Update documentation
3. Final validation

**Outcome**: Clean, unified system

---

## Key Changes Summary

### Files to Modify

**Schema Migration**:
- `blog-launchpad/publish/header_image_finder.py`
- `blueprints/header.py` (api_generate_header_image, api_optimize_header_image)
- `blueprints/launchpad/publishing.py`
- `scripts/backfill_recipe_header_post_images.py`
- ~150+ other files with `image` table references

**Process Unification**:
- `blueprints/header.py` (remove Photo-harvesting, remove recipe conditionals)
- `blueprints/launchpad/publishing.py` (remove Photo-harvesting)
- `blog-launchpad/clan_publisher.py` (remove Photo-harvesting URL handling)
- `blog-launchpad/publish/publish_endpoint.py` (consolidate endpoints)

**Photo-harvesting Removal**:
- Delete: `utils/photo_*.py` (4 files)
- Delete: `blueprints/authoring_api_photography.py`
- Delete: Photo-harvesting templates (3 files)
- Delete: Photo-harvesting static files (7+ files)
- Modify: Remove Photo-harvesting routes from `blueprints/header.py`, `blueprints/imaging.py`

### Files to Archive

**Before Deletion**:
- All Photo-harvesting code files
- All Photo-harvesting templates
- All Photo-harvesting static files
- All Photo-harvesting data files (JSON)
- Photo-harvesting migrations

**Archive Location**: `ARCHIVED_PHOTO_HARVESTING/`

---

## Success Criteria

### Schema Migration ✅
- All data in `images` table
- All code uses `images` table
- `image` table removed

### Process Unification ✅
- Recipe and theme posts use identical preview construction
- Recipe and theme posts use identical publishing process
- No recipe-specific conditionals in preview/publishing
- Author assignment unified

### Photo-harvesting Deprecation ✅
- All Photo-harvesting code archived
- All Photo-harvesting code removed
- All Photo-harvesting data archived
- No Photo-harvesting references remain

### Testing ✅
- All tests pass
- Recipe workflow = Theme workflow
- No regressions
- No Photo-harvesting accessible

---

## Timeline

**Total**: 21-36 hours

- Phase 1: 2-4 hours
- Phase 2: 4-8 hours
- Phase 3: 4-6 hours
- Phase 4: 6-10 hours
- Phase 5: 4-6 hours
- Phase 6: 1-2 hours

---

## Risk Mitigation

1. **Full database backup** before Phase 1
2. **Archive Photo-harvesting** before removal (Phase 5)
3. **Comprehensive testing** after each phase
4. **Rollback plan** for each phase

---

## Scripts Provided

1. **`migrations/migrate_image_to_images.sql`** - Data migration script
2. **`scripts/archive_photo_harvesting.sh`** - Archive Photo-harvesting files
3. **`scripts/archive_photo_harvesting_data.py`** - Archive Photo-harvesting JSON data

---

## Next Steps

1. **Review plan** - Get approval
2. **Backup database** - Before starting
3. **Run Phase 1** - Data migration
4. **Test Phase 1** - Verify migration
5. **Continue through phases** - Systematic execution
6. **Final validation** - Ensure all success criteria met

---

## Answer to Your Question

**Does this resolve recipe/theme post process differences?**

**YES** - Phase 4 (Process Unification) specifically addresses this:
- Removes all recipe-specific conditionals
- Removes Photo-harvesting (which was only for theme posts)
- Unifies author assignment
- Consolidates publishing endpoints
- Makes recipe and theme posts use **identical processes** after creation prompts

**Does this deprecate Photo-harvesting?**

**YES** - Phase 5 (Photo-harvesting Deprecation) completely removes it:
- Archives all Photo-harvesting files
- Removes all Photo-harvesting code
- Archives all Photo-harvesting data
- Removes Photo-harvesting from all processes

The plan is comprehensive and addresses all three issues in a coordinated way.

