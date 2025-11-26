# Post ID and Week Resolution - Executive Summary

## Problem Confirmed

**Issue:** When accessing `/planning/posts/96/calendar/taxonomy?year=2025&week=48`, the system displays data for post 97 instead of post 96.

**Root Cause:** The code calls `resolve_post_for_week(2025, 48)` which returns post 97 (the most recent post assigned to that week), and then **changes the post_id from 96 to 97**, causing all operations to be applied to the wrong post.

## Database Evidence

- **Post 96:** "Thanksgiving", has taxonomy (Theme: 2, Content Type: 7, Format: 11)
- **Post 97:** "St Andrew's Day", no taxonomy (all None)
- **Both posts assigned to week 2025/48:**
  - Post 96: Created 2025-11-24 23:16:11
  - Post 97: Created 2025-11-25 13:38:05 (MORE RECENT)

**The Bug:**
- `resolve_post_for_week(2025, 48)` uses `ORDER BY created_at DESC LIMIT 1`
- Returns post 97 (most recent)
- Code changes post_id from 96 → 97
- All data operations go to post 97 instead of post 96

## Solution

### Principle: Post ID in URL is Definitive

- **post_id in URL = definitive identifier**
- Week parameters are **context only**, not identifiers
- **Never change post_id based on week context**

### Required Changes

1. **Remove `resolve_post_for_week()` from data modification routes**
   - All routes with `<int:post_id>` in URL should use that post_id directly
   - Week params are for context/display only

2. **Update affected routes:**
   - `blueprints/planning_calendar_clean.py`
   - `blueprints/planning_api_taxonomy.py`
   - `blueprints/authoring_api_imaging.py`
   - `blueprints/imaging_routes.py`
   - `blueprints/planning_concept.py`
   - `blueprints/header/routes.py`

3. **Pattern to follow:**
   ```python
   @bp.route('/posts/<int:post_id>/calendar/taxonomy')
   def taxonomy(post_id):
       # ALWAYS use post_id from URL - never change it
       target_post_id = post_id
       
       # Week params are for context only
       year = request.args.get('year', type=int)
       week = request.args.get('week', type=int)
       
       # Use target_post_id for all operations
       # Week is only for display/context
   ```

## Immediate Actions

1. ✅ Audit document created: `docs/bugs/post_id_week_resolution_audit.md`
2. ✅ Warning added to `resolve_post_for_week()` function
3. ⏳ Fix all routes to use post_id from URL directly
4. ⏳ Test that post 96's data is preserved
5. ⏳ Verify posts can be reallocated to different weeks without data loss

## Files to Fix

See `docs/bugs/post_id_week_resolution_audit.md` for complete list of files and specific line numbers.


