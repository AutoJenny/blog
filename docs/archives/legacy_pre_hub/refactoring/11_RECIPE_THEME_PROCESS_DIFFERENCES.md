# Recipe vs Theme Post Process Differences Analysis

## Question
Does the dual table migration (`image` → `images`) resolve the issue of recipe posts having different preview/publishing processes than theme posts?

## Answer: **NO**

The dual table migration only fixes the **database schema inconsistency**. It does **NOT** address the **code logic differences** in preview construction and publishing.

## Current Process Differences

### Preview Construction Differences

**Location**: `blueprints/header.py::header_preview()` (lines 463-503)

1. **Photo-harvesting Skip for Recipes** (line 467)
   ```python
   # For recipe posts, skip Photo-harvesting entirely - only use LLM-generated images
   elif post_type != 'recipe':
       # Priority 1: Check Photo-harvesting route (selected_landscape.json) - ONLY for non-recipe posts
   ```
   - **Recipe posts**: Skip Photo-harvesting, only use LLM-generated images
   - **Theme posts**: Use Photo-harvesting as Priority 1

2. **Recipe Method Section Image Skip** (line 463)
   ```python
   # Skip images for recipe_method section (method image deprecated)
   if post_type == 'recipe' and section.get('section_type') == 'recipe_method':
       # Don't add image for method section
       pass
   ```
   - **Recipe posts**: Skip images for `recipe_method` sections
   - **Theme posts**: No such skip

3. **Author Name Assignment** (lines 340, 1449)
   ```python
   # blueprints/header.py line 340
   if not post.get('author_name') and post_type == 'recipe':
       post['author_name'] = 'Marion MacLeod'
   
   # clan_publisher.py line 1449
   if post_type == 'recipe':
       post_for_template['author_name'] = 'Marion MacLeod'
   else:
       post_for_template['author_name'] = 'Caitrin Stewart'
   ```
   - **Recipe posts**: Get "Marion MacLeod" as author
   - **Theme posts**: Get "Caitrin Stewart" as author

4. **Title Generation Logic** (line 666)
   ```python
   # For recipe posts, use recipe title directly and generate subtitle only
   if post_type == 'recipe':
       # Different title generation logic
   ```
   - **Recipe posts**: Use recipe title directly from `calendar_recipes`
   - **Theme posts**: Generate title using LLM

### Publishing Differences

**Location**: `blog-launchpad/publish/publish_endpoint.py`

1. **Separate Endpoint** (line 16)
   ```python
   @bp.route('/recipe/<int:post_id>', methods=['POST'])
   def publish_recipe_post(post_id):
       # Validates post is recipe type
       # Then calls same publish_post_to_clan() function
   ```
   - **Recipe posts**: Have separate endpoint `/api/publish/recipe/<post_id>`
   - **Theme posts**: Use generic endpoint
   - **BUT**: Both call the same `publish_post_to_clan()` function
   - **Impact**: The actual publishing logic is identical, just different entry point

2. **Publishing Logic** (Same for both)
   - `publish_orchestrator.py` treats all posts identically ✅
   - `clan_publisher.py` treats all posts identically ✅
   - Only difference is author name (handled in template rendering)

## What Dual Table Migration Fixes

✅ **Fixes**:
- Database schema inconsistency (`image` vs `images` table)
- Column name mismatch (`path` vs `file_path`)
- FK constraint ambiguity

❌ **Does NOT Fix**:
- Preview construction code differences
- Photo-harvesting skip logic
- Recipe method section image skip
- Author name assignment differences
- Title generation differences
- Separate publishing endpoints

## Required Changes for Unified Process

To achieve your goal of "recipe and theme posts share single process after creation prompts", you need:

### 1. Unify Preview Construction

**File**: `blueprints/header.py::header_preview()`

**Changes Needed**:
- Remove Photo-harvesting skip for recipes (line 467)
- Remove recipe_method section image skip (line 463)
- Make image selection logic identical for all post types

**Current Logic**:
```python
if post_type == 'recipe' and section.get('section_type') == 'recipe_method':
    pass  # Skip
elif post_type != 'recipe':
    # Photo-harvesting logic
```

**Unified Logic**:
```python
# Same logic for all post types
# Check Photo-harvesting for all (or none)
# Check database for all
# Check filesystem for all
```

### 2. Unify Author Assignment

**Files**: 
- `blueprints/header.py` (line 340)
- `clan_publisher.py` (line 1449)

**Changes Needed**:
- Remove recipe-specific author assignment
- Use `post.author_id` or default author for all posts
- Or: Make author assignment based on taxonomy, not post type

### 3. Unify Title Generation

**File**: `blueprints/header.py::api_compile_header_prompt()` (line 666)

**Changes Needed**:
- Remove recipe-specific title generation
- Use same LLM-based title generation for all posts
- Or: Make title source configurable via taxonomy

### 4. Unify Publishing Endpoints

**File**: `blog-launchpad/publish/publish_endpoint.py`

**Changes Needed**:
- Remove separate `/recipe/<post_id>` endpoint
- Use single endpoint for all post types
- Validation can check post type but use same logic

## Recommendation

### Phase 1: Dual Table Migration (Current Plan)
- ✅ Fixes database schema
- ✅ Necessary foundation
- ⚠️ Does NOT unify processes

### Phase 2: Process Unification (New Requirement)
- Unify preview construction
- Unify author assignment
- Unify title generation
- Unify publishing endpoints

### Priority

**High Priority**: Process unification should happen **AFTER** dual table migration because:
1. Dual table migration is a prerequisite (fixes schema)
2. Process unification requires stable schema
3. But they are **separate issues** - migration doesn't solve unification

## Conclusion

**The dual table migration does NOT resolve recipe/theme post process differences.**

These are **two separate problems**:
1. **Database schema issue** → Fixed by dual table migration
2. **Code logic differences** → Requires separate process unification work

You need **both**:
- ✅ Dual table migration (fixes schema)
- ✅ Process unification (fixes code differences)

The migration is a necessary foundation, but process unification requires additional work to remove the conditional logic that treats recipes differently.

