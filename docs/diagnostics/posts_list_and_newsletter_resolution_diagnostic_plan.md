# Posts List and Newsletter Post Resolution Diagnostic Plan

**Date:** 2025-11-26  
**Status:** Fixes Implemented  
**Priority:** High

---

## Problem Summary

1. **Post in development not appearing in Posts list**: Post 96 (status='draft') should appear but may be filtered incorrectly
2. **Newsletter protocol selecting deleted post**: Post 97 (status='deleted') is being selected for week 2025W48 instead of Post 96 (status='draft')
3. **Multiple posts scheduled for same week**: Week 2025W48 has both post 96 (draft) and post 97 (deleted) in calendar_schedule

## Current State

### Database Query Results

**Current week: 2025W48**

**Posts in calendar_schedule for 2025W48:**
- post_id=97, created=2025-11-25 13:38:05, **Status='deleted'**
- post_id=96, created=2025-11-24 23:16:11, **Status='draft'**

**All post statuses in database:**
- 'deleted': 38 posts
- 'draft': 7 posts
- 'published': 6 posts

### Root Causes

1. **`resolve_post_for_week()` returns deleted posts**: The function in `utils/week_post_resolver.py` returns the most recent post_id from `calendar_schedule` without checking if that post is deleted. It orders by `created_at DESC`, so it returns post 97 (deleted) instead of post 96 (draft).

2. **`confirm_calendar_idea()` reuses deleted posts**: The function in `blueprints/planning_api_posts.py` checks for existing posts by title/idea_seed but doesn't filter out deleted posts. When creating a new post for "St Andrew's Day", it finds the deleted post 97 and reuses it instead of creating a new post with a new ID.

## Investigation Phase

### Task 1: Verify Posts List Filtering

**Script**: `scripts/diagnostic/check_posts_list_filtering.py`

**Purpose**: Verify which posts are returned by the `/posts` route and why post 96 might not appear

**Key Checks**:
- Simulate exact query from `blueprints/posts.py` lines 178-192
- Verify post 96 appears in results
- Check if any additional filtering is happening

### Task 2: Investigate Week/Post Resolution

**Script**: `scripts/diagnostic/check_week_post_resolution.py`

**Purpose**: Check why `resolve_post_for_week()` returns deleted post 97 instead of draft post 96

**Key Checks**:
- Query `calendar_schedule` for week 2025W48
- Check post statuses for resolved post_id
- Test `resolve_post_for_week()` function directly

### Task 3: Check Calendar Schedule Cleanup

**Script**: `scripts/diagnostic/check_calendar_schedule_cleanup.py`

**Purpose**: Verify if deleted posts should be removed from calendar_schedule

**Key Checks**:
- Find all deleted posts still in calendar_schedule
- Identify weeks with multiple posts (one deleted, one active)
- Determine if cleanup is needed

## Fix Phase

### Task 4: Fix `resolve_post_for_week()` to Filter Deleted Posts

**File**: `utils/week_post_resolver.py`

**Location**: `_resolve_with_cursor()` function (lines 69-111)

**Change Required**: Add JOIN with `post` table and filter `WHERE p.status != 'deleted'`

**Before**:
```python
cursor.execute("""
    SELECT post_id
    FROM calendar_schedule
    WHERE year = %s 
      AND week_number = %s
      AND post_id IS NOT NULL
    ORDER BY created_at DESC
    LIMIT 1
""", (year, week_number))
```

**After**:
```python
cursor.execute("""
    SELECT cs.post_id
    FROM calendar_schedule cs
    JOIN post p ON cs.post_id = p.id
    WHERE cs.year = %s 
      AND cs.week_number = %s
      AND cs.post_id IS NOT NULL
      AND p.status != 'deleted'
    ORDER BY cs.created_at DESC
    LIMIT 1
""", (year, week_number))
```

**Rationale**: Ensures only active (non-deleted) posts are returned for week resolution.

### Task 5: Fix `confirm_calendar_idea()` to Not Reuse Deleted Posts

**File**: `blueprints/planning_api_posts.py`

**Location**: `confirm_calendar_idea()` function (lines 141-153)

**Change Required**: Add status filter to existing post lookup query

**Before**:
```python
cursor.execute("""
    SELECT p.id
    FROM post p
    LEFT JOIN post_development pd ON pd.post_id = p.id
    WHERE (p.title = %s OR pd.idea_seed ILIKE %s)
    ORDER BY p.updated_at DESC
    LIMIT 1
""", (topic, f"%{topic}%"))
```

**After**:
```python
cursor.execute("""
    SELECT p.id
    FROM post p
    LEFT JOIN post_development pd ON pd.post_id = p.id
    WHERE (p.title = %s OR pd.idea_seed ILIKE %s)
      AND p.status != 'deleted'
    ORDER BY p.updated_at DESC
    LIMIT 1
""", (topic, f"%{topic}%"))
```

**Rationale**: When a deleted post exists for a theme, the system should create a NEW post with a new ID, not reuse the deleted one. This ensures deleted posts remain deleted and new work starts fresh.

### Task 6: Add Status Validation to Newsletter Protocol

**File**: `blueprints/newsletter.py`

**Location**: `view_issue()` function (lines 190-222)

**Change Required**: Add status check after resolving post_id

**After**:
```python
if post_row:
    # Validate post is not deleted before using it
    if post_row['status'] != 'deleted':
        themed_post = dict(post_row)
    else:
        # Log warning if deleted post was resolved
        import logging
        logging.getLogger(__name__).warning(
            f"resolve_post_for_week returned deleted post {post_id} "
            f"for week {target_week}. This should not happen after fix."
        )
```

**Rationale**: Defense-in-depth - even after fixing `resolve_post_for_week()`, add safety check.

### Task 7: Clean Up Calendar Schedule (Optional but Recommended)

**Script**: `scripts/maintenance/cleanup_deleted_posts_from_schedule.py`

**Purpose**: Remove deleted posts from calendar_schedule to prevent future issues

**Action**: Delete all `calendar_schedule` entries where `post.status = 'deleted'`

## Testing Phase

### Task 8: Test Week/Post Resolution

**Test Cases**:
1. Week with only deleted post → should return None
2. Week with deleted and draft posts → should return draft post
3. Week with multiple non-deleted posts → should return most recent non-deleted
4. Week with no posts → should return None

### Task 9: Test Newsletter Protocol

**Procedure**:
1. Navigate to Newsletter issue for current week (2025W48)
2. Verify `themed_post` shows post 96 (draft), not post 97 (deleted)
3. Check browser console for any warnings
4. Verify post 96 appears in Posts list at `/posts`

### Task 10: Test Post Creation for Theme with Deleted Post

**Procedure**:
1. Navigate to `http://localhost:5000/planning/calendar/ideas/week/48?year=2025&week=48`
2. Select the "St Andrew's Day" theme (which has deleted post 97)
3. Click "Create Post"
4. Verify a NEW post is created with a new ID (not post 97)
5. Verify the new post has status='draft' (not 'deleted')
6. Verify post 97 remains deleted

### Task 11: Manual Verification

**Steps**:
1. Navigate to `http://localhost:5000/posts`
2. Verify post 96 (Thanksgiving, status='draft') appears in the list
3. Navigate to Newsletter issue for week 2025W48
4. Verify the themed post shown is post 96, not post 97
5. Check logs for any warnings about deleted posts

## Success Criteria

1. ✅ Post 96 (draft) appears in Posts list at `/posts` - **VERIFIED: Posts list query already filters correctly**
2. ✅ `resolve_post_for_week()` returns post 96 for week 2025W48, not post 97 - **FIXED: Test confirms post 96 is returned**
3. ✅ Newsletter protocol displays post 96 as themed post, not post 97 - **FIXED: Status validation added**
4. ✅ No deleted posts are returned by `resolve_post_for_week()` - **FIXED: JOIN with post table filters deleted posts**
5. ⏳ Calendar schedule cleanup removes deleted post entries (optional) - **PENDING: Cleanup script not yet created**

## Implementation Status

### Completed Fixes

**Task 4: Fixed `resolve_post_for_week()` to Filter Deleted Posts**
- ✅ Updated `utils/week_post_resolver.py` to JOIN with `post` table
- ✅ Added `WHERE p.status != 'deleted'` filter to both calendar_week_posts and calendar_schedule queries
- ✅ Tested: Returns post 96 (draft) for week 2025W48 instead of post 97 (deleted)

**Task 5: Fixed `confirm_calendar_idea()` to Not Reuse Deleted Posts**
- ✅ Updated `blueprints/planning_api_posts.py` to filter out deleted posts when checking for existing posts
- ✅ Tested: Query now returns None for deleted posts, causing new post creation ✓

**Task 6: Added Status Validation to Newsletter Protocol**
- ✅ Updated `blueprints/newsletter.py` to validate post status before using
- ✅ Added warning log if deleted post is somehow resolved (defense-in-depth)

### Test Results

**Week Resolution Fix:**
```
Testing week resolution for 2025W48
Resolved post_id: 96
Post details: ID=96, Title='Thanksgiving', Status='draft'
✓ SUCCESS: Resolved post is active (not deleted)
```

**Post Creation Fix:**
```
OLD query result (without status filter):
  Found post_id=97, status='deleted'

NEW query result (with status filter):
  No active post found - would create new post ✓
```

This confirms that when creating a new post for "St Andrew's Day", the system will now create a NEW post instead of reusing the deleted post 97.

### Remaining Tasks

- ⏳ Task 7: Create cleanup script for calendar_schedule (optional)
- ⏳ Task 8-11: Manual testing of fixes
  - Test week/post resolution
  - Test Newsletter protocol
  - Test post creation for theme with deleted post
  - Verify Posts list

## Files to Modify

1. `utils/week_post_resolver.py` - Add status filtering to `_resolve_with_cursor()` ✅ FIXED
2. `blueprints/planning_api_posts.py` - Add status filtering to `confirm_calendar_idea()` ✅ FIXED
3. `blueprints/newsletter.py` - Add status validation in `view_issue()` ✅ FIXED

## Files to Create

1. `scripts/diagnostic/check_posts_list_filtering.py`
2. `scripts/diagnostic/check_week_post_resolution.py`
3. `scripts/diagnostic/check_calendar_schedule_cleanup.py`
4. `scripts/maintenance/cleanup_deleted_posts_from_schedule.py`
5. `scripts/test/test_week_post_resolution.py`

## Execution Order

1. Run investigation scripts (Tasks 1-3) to gather data
2. Review diagnostic output to confirm root causes
3. Implement fixes (Tasks 4-5)
4. Run cleanup script if needed (Task 6)
5. Run tests (Tasks 7-8)
6. Manual verification (Task 9)

## Related Files

- `blueprints/posts.py` - Posts list route (lines 132-325)
- `utils/week_post_resolver.py` - Week/post resolution function
- `blueprints/newsletter.py` - Newsletter issue view (lines 190-222)
- `blueprints/planning_api_calendar_utils.py` - Related resolution helpers

