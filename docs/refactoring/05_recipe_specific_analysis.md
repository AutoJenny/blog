# Recipe-Specific Header Image Analysis

## Overview
Recipe posts use the same header image publishing system as other post types, but there are some recipe-specific considerations and a known data inconsistency issue.

## Recipe Identification
Recipe posts are identified by:
- `post.recipe_week_number IS NOT NULL` (database query)
- `window.postType === 'recipe'` (JavaScript)

## Recipe Header Image Generation

### Frontend: `static/js/header/recipe-header-image.js`
**Purpose**: JavaScript class for recipe header image generation UI.

**Key Behavior**:
1. Loads hero prompt from `recipe_image_style` section
2. Extracts `hero_image_prompt` from `post_section_elements`
3. Sends generation request to `/header/api/posts/{post_id}/generate-header-image`
4. Uses landscape format only (portrait hidden)

**Issues Identified**:
1. ✅ Good: Recipe-specific UI behavior (landscape only)
2. ⚠️ **RISK**: Depends on `recipe_image_style` section existing
   - If section doesn't exist or is malformed, generation fails silently
3. ⚠️ **RISK**: No validation that hero prompt exists before enabling generate button

### Backend: `blueprints/header.py`
**Route**: `/api/posts/<int:post_id>/generate-header-image`

**Recipe-Specific Behavior**: **NONE**
- The route treats all post types identically
- No special handling for recipe posts
- Uses same image generation, optimization, and database storage logic

**Database Storage** (lines 3005-3016):
1. Creates/updates `images` table record
2. Updates `post.header_image_id`
3. **CRITICAL**: Creates `post_images` record with `image_type = 'header_optimized'`

## Known Data Inconsistency Issue

### The Problem
Recipe posts created before the `post_images` linking table was implemented have:
- `post.header_image_id` set (points to `image` table)
- **Missing** `post_images` record linking to `images` table

### The Fix: `scripts/backfill_recipe_header_post_images.py`
**Purpose**: Backfill missing `post_images` records for recipe posts.

**Logic**:
1. Finds recipe posts with `header_image_id` but no `post_images` record
2. Creates `post_images` record with `image_type = 'header_optimized'`
3. **CRITICAL**: Uses old `image` table (singular), not `images` table (plural)

**Issues Identified**:
1. ⚠️ **HIGH RISK**: Uses old `image` table (line 46)
   - Inconsistent with new schema which uses `images` table
   - May not work for recipe posts created after schema migration
2. ⚠️ **RISK**: Only fixes recipe posts (`recipe_week_number IS NOT NULL`)
   - Other post types with same issue won't be fixed
3. ⚠️ **RISK**: Assumes `image.id` matches what should be in `post_images.image_id`
   - If schema migration changed IDs, this breaks

### Why This Matters for Publishing
The publishing system relies on `post_images` table to find header images:
- `header_image_finder.load_header_image_from_db` queries `post_images` first
- If `post_images` record is missing, falls back to filesystem
- Filesystem fallback may not have complete metadata

**Impact**: Recipe posts without `post_images` records may:
- Publish with incomplete header image metadata
- Use filesystem fallback instead of database
- Have inconsistent behavior compared to other posts

## Recipe-Specific Publishing Behavior

### `clan_publisher.py`
**Recipe-Specific Behavior**: **NONE**
- All post types processed identically
- No special handling for recipe header images

### `publish_orchestrator.py`
**Recipe-Specific Behavior**: **NONE**
- All post types processed identically

### `blueprints/launchpad/publishing.py`
**Recipe-Specific Behavior**: **NONE**
- All post types processed identically

## Critical Findings

### HIGH RISKS
1. **Schema Inconsistency**: Backfill script uses old `image` table while new code uses `images` table
   - Recipe posts created after migration may not be fixed by backfill script
   - Creates two classes of recipe posts: those with old schema, those with new schema

2. **Missing post_images Records**: Recipe posts without `post_images` records will:
   - Use filesystem fallback (less reliable)
   - Have incomplete metadata
   - Behave differently than posts with proper records

3. **No Recipe-Specific Validation**: No checks that recipe posts have required sections/data before publishing

### MEDIUM RISKS
1. **Frontend Dependency**: Recipe header image generation depends on `recipe_image_style` section existing
2. **No Migration Path**: No clear plan to migrate all recipe posts to new schema

## Recommendations

1. **IMMEDIATE**:
   - Update backfill script to check both `image` and `images` tables
   - Add validation that recipe posts have `post_images` records before publishing
   - Document which recipe posts are affected by schema inconsistency

2. **SHORT TERM**:
   - Create migration script to move all recipe posts to `images` table
   - Update backfill script to handle both schemas
   - Add recipe-specific validation in publishing flow

3. **MEDIUM TERM**:
   - Remove dependency on old `image` table
   - Ensure all recipe posts use consistent schema
   - Add integration tests for recipe header image publishing

