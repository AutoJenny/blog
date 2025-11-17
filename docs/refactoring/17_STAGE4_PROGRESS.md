# Stage 4 Progress - Process Unification

**Date**: 2025-11-09  
**Status**: ✅ Photo-harvesting Removed, Author Assignment Unified

## Completed

### 1. Photo-harvesting Removal ✅
- ✅ Removed from preview (`blueprints/header.py`)
- ✅ Removed from publishing (`blueprints/launchpad/publishing.py`)
- ✅ Removed URL handling from image processing (`blog-launchpad/clan_publisher.py`)
- ✅ Now only uses database links (post_images) and filesystem fallback

### 2. Author Assignment Unification ✅
- ✅ Removed recipe-specific author assignment (Marion MacLeod)
- ✅ Now uses author from database (post.author_id) for all post types
- ✅ Falls back to template default if author not set
- ✅ Recipe and theme posts now use identical author assignment

## Remaining

### 3. Recipe Method Section Skip
- Still has: `if post_type == 'recipe' and section.get('section_type') == 'recipe_method'`
- **Decision needed**: Keep this skip or remove it?

### 4. Title Generation
- Recipe posts use recipe title from `calendar_recipes`
- Theme posts use LLM-generated title
- **Decision needed**: Unify or keep separate?

### 5. Publishing Endpoints
- Recipe posts have separate endpoint `/api/publish/recipe/<post_id>`
- Theme posts use generic endpoint
- Both call same function - **low priority**

## Impact

✅ **Recipe and theme posts now use identical:**
- Image selection process (database → filesystem)
- Author assignment process (database → default)
- Publishing logic (same function)

⚠️ **Still different:**
- Recipe method section image skip (if kept)
- Title generation (if kept separate)




