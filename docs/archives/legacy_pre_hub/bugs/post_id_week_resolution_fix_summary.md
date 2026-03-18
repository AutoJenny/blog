# Post ID and Week Resolution - Fix Summary

## Fix Applied: 2025-01-15

### Problem
When accessing routes with `post_id` in the URL (e.g., `/planning/posts/96/calendar/taxonomy?year=2025&week=48`), the code was calling `resolve_post_for_week()` which changed the `post_id` from 96 to 97 (the most recent post assigned to that week), causing all data operations to be applied to the wrong post.

### Solution
**Principle:** `post_id` in URL is the definitive identifier. Week parameters are context only, not identifiers.

### Files Fixed

1. **`blueprints/planning_calendar_clean.py`**
   - Removed `resolve_post_for_week()` calls from `planning_calendar_week_view()` and `planning_calendar_ideas()`
   - Always uses `post_id` from URL

2. **`blueprints/planning_concept.py`**
   - Fixed `_resolve_post_and_get_week_context()` helper to always return `post_id` from URL
   - Removed week-based post_id resolution

3. **`blueprints/authoring_api_imaging.py`**
   - Removed `resolve_post_for_week()` calls from:
     - `authoring_sections_image_concepts()`
     - `authoring_sections_image_prompts()`
     - `authoring_sections_image_captions()`
   - Always uses `post_id` from URL

4. **`blueprints/imaging_routes.py`**
   - Removed `resolve_post_for_week()` calls from image generation routes
   - Always uses `post_id` from URL

5. **`blueprints/header/routes.py`**
   - Removed all `resolve_post_for_week()` calls
   - Updated all routes to always use `post_id` from URL:
     - `header_title_summary()`
     - `header_header_image()`
     - `header_seo_meta()`
     - `header_product_match()`

6. **`blueprints/header/helpers.py`**
   - Fixed `resolve_target_post_id()` to always return `post_id` from URL
   - Week parameters are now only for validation/context, never for changing post_id

7. **`utils/week_post_resolver.py`**
   - Added critical warning documentation about when NOT to use this function
   - Function should only be used for display/scheduling, not when post_id is in URL

### Pattern Applied

**Before (WRONG):**
```python
target_post_id = post_id
if year and week:
    resolved = resolve_post_for_week(year, week)
    if resolved:
        target_post_id = resolved  # ❌ Changes post_id!
```

**After (CORRECT):**
```python
# CRITICAL: Always use post_id from URL - it's the definitive identifier
# Week parameters are context only, not for changing post_id
target_post_id = post_id  # ✅ Always use URL post_id
```

### Testing

To verify the fix works:

1. **Test post 96 with week 2025/48:**
   ```bash
   curl "http://localhost:5000/planning/posts/96/calendar/taxonomy?year=2025&week=48"
   ```
   Should show post 96's data, not post 97's.

2. **Check database:**
   ```sql
   SELECT id, title, theme_id FROM post WHERE id = 96;
   SELECT post_id, expanded_idea FROM post_development WHERE post_id = 96;
   ```
   Post 96's data should be intact.

3. **Verify week assignment doesn't change post_id:**
   - Assign post 96 to week 2025/48
   - Assign post 97 to week 2025/48
   - Access `/planning/posts/96/...?year=2025&week=48`
   - Should still show post 96's data (not post 97's)

### Impact

- ✅ Post data is now correctly associated with the post_id in the URL
- ✅ Posts can be reallocated to different weeks without data loss
- ✅ Week parameters are used only for context/display, not for changing post_id
- ✅ All routes now consistently use post_id from URL as definitive identifier

### Notes

- The `resolve_post_for_week()` function still exists but should ONLY be used for:
  - Displaying which post is scheduled for a week (calendar view)
  - Publishing/scheduling operations
  - Finding posts by week when post_id is NOT in URL

- It should NEVER be used when post_id is already in the URL parameter.


