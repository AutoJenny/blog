# Backend API Endpoints Audit - Week Persistence V2

## Overview

This document audits all backend endpoints that interact with calendar_schedule, theme_id, idea_id, or week context. For each endpoint, we document:
1. Current behavior
2. Calendar_schedule queries used
3. Idea_id/theme_id usage
4. Required changes for V2 architecture

---

## File: `blueprints/planning_api_calendar_schedule.py`

### `api_calendar_schedule(year, week_number)`
**Current Behavior:**
- Queries `calendar_schedule` WHERE year=? AND week_number=?
- Returns ALL schedule entries for the week (can be multiple)
- Joins with `calendar_themes` if theme_id exists
- Returns both idea_id and theme_id if present

**Calendar_Schedule Queries:**
```sql
SELECT cs.id, cs.post_id, cs.idea_id, cs.theme_id, cs.year, cs.week_number, cs.scheduled_date,
       cs.created_at, cs.updated_at,
       p.title as post_title, p.status as post_status,
       pd.idea_seed as post_idea_seed,
       ct.theme_title, ct.id as calendar_theme_id
FROM calendar_schedule cs
LEFT JOIN post p ON cs.post_id = p.id
LEFT JOIN post_development pd ON p.id = pd.post_id
LEFT JOIN calendar_themes ct ON cs.theme_id = ct.id
WHERE cs.year = %s AND cs.week_number = %s
ORDER BY cs.scheduled_date
```

**Issues:**
- Returns multiple entries if duplicates exist
- Includes idea_id (to be deprecated)
- No clear "selected theme" indication

**Required Changes:**
1. Query `calendar_week_selection` for selected theme (one per week)
2. Query `calendar_week_posts` for all posts (multiple allowed)
3. Combine results into unified response
4. Remove idea_id from response
5. Mark selected_theme_id clearly

**New Query Structure:**
```python
# Get selected theme
SELECT cws.selected_theme_id, ct.theme_title, ct.theme_description
FROM calendar_week_selection cws
LEFT JOIN calendar_themes ct ON cws.selected_theme_id = ct.id
WHERE cws.year = %s AND cws.week_number = %s

# Get all posts
SELECT cwp.post_id, cwp.scheduled_date, cwp.created_at,
       p.title as post_title, p.status as post_status,
       pd.idea_seed as post_idea_seed
FROM calendar_week_posts cwp
LEFT JOIN post p ON cwp.post_id = p.id
LEFT JOIN post_development pd ON p.id = pd.post_id
WHERE cwp.year = %s AND cwp.week_number = %s
ORDER BY cwp.scheduled_date
```

---

### `api_select_theme_idea()`
**Current Behavior:**
- Accepts theme_id OR idea_id (backwards compatibility)
- Checks if entry exists for (year, week_number)
- If exists: UPDATE calendar_schedule SET theme_id=? OR idea_id=?
- If not: INSERT INTO calendar_schedule (year, week_number, theme_id/idea_id)

**Issues:**
- Creates/updates calendar_schedule entry (wrong table for theme selection)
- Allows idea_id (to be deprecated)
- No unique constraint prevents duplicates
- Can create multiple entries for same week

**Required Changes:**
1. Remove idea_id support entirely
2. Use `calendar_week_selection` table instead
3. UPDATE if exists, INSERT if not (enforced by PRIMARY KEY)
4. Require theme_id (no fallback)
5. Remove calendar_schedule updates from this function

**New Implementation:**
```python
# UPSERT selected theme
INSERT INTO calendar_week_selection (year, week_number, selected_theme_id, updated_at)
VALUES (%s, %s, %s, NOW())
ON CONFLICT (year, week_number)
DO UPDATE SET selected_theme_id = EXCLUDED.selected_theme_id, updated_at = NOW()
RETURNING year, week_number, selected_theme_id
```

---

### `api_calendar_idea_status(idea_id)`
**Current Behavior:**
- Takes idea_id parameter (but may be theme_id)
- Requires year and week_number query params
- Checks if idea_id is a theme first
- Finds post by theme_id in calendar_schedule WHERE year=? AND week_number=?
- Falls back to idea matching if not found as theme
- Complex backwards-compatibility logic

**Issues:**
- Uses idea_id parameter (deprecated)
- Cross-week theme matching (finds ANY post with theme_id)
- Falls back to idea matching by title (fragile)
- Uses calendar_schedule queries

**Required Changes:**
1. Rename to `api_calendar_theme_status(theme_id)`
2. Remove idea_id fallback logic
3. Query `calendar_week_selection` for selected theme
4. Query `calendar_week_posts` for posts in that week
5. Return post from same week only (no cross-week matching)
6. If multiple posts, return first (or most recent)

**New Implementation:**
```python
# Get selected theme for week
SELECT selected_theme_id FROM calendar_week_selection
WHERE year = %s AND week_number = %s

# Get posts for this week (multiple allowed, return first)
SELECT cwp.post_id, p.title, p.status, cwp.scheduled_date
FROM calendar_week_posts cwp
LEFT JOIN post p ON cwp.post_id = p.id
WHERE cwp.year = %s AND cwp.week_number = %s
ORDER BY cwp.created_at DESC
LIMIT 1
```

---

### `api_schedule_update_theme_to_idea()`
**Current Behavior:**
- Updates calendar_schedule entries
- Converts theme_id to idea_id
- Used for migration/backwards compatibility

**Required Changes:**
1. **DELETE THIS ENDPOINT** - No longer needed
2. Theme_id is the only supported ID type
3. Migration will handle data conversion

---

## File: `utils/week_post_resolver.py`

### `resolve_post_for_week(year, week_number, cursor=None)`
**Current Behavior:**
- Queries `calendar_schedule` WHERE year=? AND week_number=? AND post_id IS NOT NULL
- Returns first post_id found (ORDER BY created_at DESC)
- Returns None if no post found

**Issues:**
- Uses calendar_schedule (wrong table)
- Returns first post if multiple exist (may be wrong one)

**Required Changes:**
1. Query `calendar_week_posts` instead of `calendar_schedule`
2. If multiple posts, return first created (or most recent)
3. Consider adding `is_primary` flag for explicit selection

**New Implementation:**
```python
SELECT post_id
FROM calendar_week_posts
WHERE year = %s AND week_number = %s
ORDER BY created_at DESC
LIMIT 1
```

---

## File: `blueprints/planning_api_post_specific.py`

### `get_post_by_theme(theme_idea_id)`
**Current Behavior:**
- Queries `calendar_schedule` WHERE idea_id=? AND post_id IS NOT NULL
- Returns first post found
- Used to find posts by theme across ALL weeks

**Issues:**
- Uses idea_id (deprecated)
- Cross-week matching (finds post from any week)
- Uses calendar_schedule (wrong table)

**Required Changes:**
1. **RENAME to `get_post_by_theme_id(theme_id)`**
2. Remove idea_id support
3. Query `calendar_week_posts` joined with `calendar_week_selection`
4. Find post in week that has selected theme matching theme_id
5. **OR** keep cross-week matching but use correct tables
6. Document which behavior is desired

**New Implementation (Week-Specific):**
```python
SELECT cwp.post_id
FROM calendar_week_selection cws
JOIN calendar_week_posts cwp ON cws.year = cwp.year AND cws.week_number = cwp.week_number
WHERE cws.selected_theme_id = %s
  AND cwp.post_id IS NOT NULL
ORDER BY cwp.created_at DESC
LIMIT 1
```

---

### `api_posts_expanded_idea(post_id)` - GET
**Current Behavior:**
- Reads year/week from query params (optional)
- If week context provided:
  - STEP 1: Find post scheduled for week with theme_id
  - STEP 2: If no post, find theme for week, then find ANY post with that theme (cross-week)
- If no week context: Fetch expanded_idea for post_id directly

**Issues:**
- Complex cross-week theme matching (STEP 2)
- Uses calendar_schedule queries
- Falls back to post_id if week context missing

**Required Changes:**
1. Require year/week query params (no fallback to post_id)
2. Query `calendar_week_selection` for theme
3. Query `calendar_week_posts` for posts in that week
4. Remove cross-week theme matching (find post in same week only)
5. Return expanded_idea from post in that week

**New Implementation:**
```python
# Get selected theme for week
SELECT selected_theme_id FROM calendar_week_selection
WHERE year = %s AND week_number = %s

# Get expanded_idea from post in this week (first post if multiple)
SELECT pd.expanded_idea, p.id as post_id
FROM calendar_week_posts cwp
LEFT JOIN post_development pd ON cwp.post_id = pd.post_id
WHERE cwp.year = %s AND cwp.week_number = %s
  AND pd.expanded_idea IS NOT NULL AND pd.expanded_idea != ''
ORDER BY cwp.created_at DESC
LIMIT 1
```

---

### `api_posts_expanded_idea(post_id)` - POST
**Current Behavior:**
- Gets theme from calendar_schedule WHERE post_id=?
- If not found, gets year/week from calendar_schedule WHERE post_id=?
- Then looks up schedule by year/week to find theme
- Updates calendar_schedule to link theme_id to post
- Complex backwards-compatibility with idea_id

**Issues:**
- Uses post_id as primary lookup (wrong)
- Updates calendar_schedule directly
- Complex idea_id fallback logic
- Tries to link theme to post after the fact

**Required Changes:**
1. Require year/week in request body (not from post_id lookup)
2. Get selected theme from `calendar_week_selection`
3. Generate expanded idea from theme
4. If post_id provided, ensure post is in `calendar_week_posts` for that week
5. Save expanded_idea to post_development (no schedule updates needed)
6. Remove all idea_id logic

**New Implementation:**
```python
# Get selected theme (required)
SELECT ct.theme_title, ct.theme_description, ct.important_notes
FROM calendar_week_selection cws
JOIN calendar_themes ct ON cws.selected_theme_id = ct.id
WHERE cws.year = %s AND cws.week_number = %s

# If post_id provided, verify it's assigned to this week
SELECT post_id FROM calendar_week_posts
WHERE year = %s AND week_number = %s AND post_id = %s

# Generate and save expanded_idea
# (No schedule updates needed - theme already selected, post already assigned)
```

---

## File: `blueprints/planning_api_posts.py`

### `api_posts(post_id)`
**Current Behavior:**
- Gets post data
- Gets schedule from `calendar_schedule` WHERE post_id=?
- Joins with `calendar_ideas` for theme title (using idea_id)

**Issues:**
- Uses idea_id for theme lookup
- Gets schedule by post_id (should get by year/week)

**Required Changes:**
1. Accept year/week query params
2. Query `calendar_week_posts` WHERE post_id=? AND year=? AND week_number=?
3. Query `calendar_week_selection` for selected theme
4. Remove idea_id references

---

### `confirm_calendar_idea()`
**Current Behavior:**
- Creates post if needed
- Inserts into `calendar_schedule` (post_id, year, week_number)
- Deletes duplicates manually
- No theme_id assignment

**Issues:**
- Uses calendar_schedule (wrong table)
- No theme_id assignment (posts require selected theme)
- Manual duplicate cleanup (should use constraint)

**Required Changes:**
1. **REQUIRE selected theme exists** - Query `calendar_week_selection` first
2. Insert into `calendar_week_posts` instead of `calendar_schedule`
3. Use UNIQUE constraint to prevent duplicates (no manual cleanup)
4. Ensure selected theme exists before allowing post creation

**New Implementation:**
```python
# First check: selected theme must exist
SELECT selected_theme_id FROM calendar_week_selection
WHERE year = %s AND week_number = %s
# If not found, return error

# Create post (existing logic)

# Assign post to week
INSERT INTO calendar_week_posts (year, week_number, post_id, scheduled_date)
VALUES (%s, %s, %s, NULL)
ON CONFLICT (year, week_number, post_id) DO NOTHING
```

---

## File: `blueprints/planning_api_taxonomy.py`

### `assign_post_taxonomy()` - year/week logic
**Current Behavior:**
- Accepts year/week query params
- Finds theme using idea_id from calendar_schedule WHERE year=? AND week_number=?
- Finds ANY post with that theme (cross-week matching)
- Uses calendar_schedule queries

**Issues:**
- Uses idea_id (deprecated)
- Cross-week post matching
- Uses calendar_schedule

**Required Changes:**
1. Get selected theme from `calendar_week_selection`
2. Get post from `calendar_week_posts` for same week
3. Remove idea_id references
4. Remove cross-week matching

---

## File: `blueprints/planning_api_calendar_ideas.py`

### `api_calendar_ideas(week_number)`
**Current Behavior:**
- Gets perpetual ideas for week_number (no year)
- Excludes themes (NOT EXISTS calendar_themes)
- Returns ideas only

**Issues:**
- No year parameter (ideas are perpetual, but scheduling requires year)
- Not related to week persistence directly (ideas are perpetual)

**Required Changes:**
1. **NO CHANGES NEEDED** - Ideas are perpetual, not part of week persistence
2. Ideas can still be queried by week_number for display
3. But ideas should NOT be used in calendar_schedule anymore

---

## File: `blueprints/authoring_api_imaging.py`

### Routes using `resolve_post_for_week()`
**Current Behavior:**
- Read year/week from URL params
- Call `resolve_post_for_week(year, week)` to get correct post_id
- Use resolved post_id instead of URL post_id

**Required Changes:**
1. No changes needed - `resolve_post_for_week()` will be updated internally
2. Ensure year/week params are always passed in URLs

---

## File: `blueprints/imaging.py`

### Routes using `resolve_post_for_week()`
**Current Behavior:**
- Same as authoring_api_imaging.py
- Uses resolve_post_for_week() utility

**Required Changes:**
1. No changes needed - utility handles it

---

## Summary of Required Changes

### High Priority (Core Functionality)
1. **Create new tables** - `calendar_week_selection`, `calendar_week_posts`
2. **Update `api_calendar_schedule()`** - Query new tables
3. **Update `api_select_theme_idea()`** - Use calendar_week_selection
4. **Update `resolve_post_for_week()`** - Use calendar_week_posts
5. **Update `api_posts_expanded_idea()`** - Use new tables, remove cross-week matching

### Medium Priority (Feature Updates)
6. **Update `confirm_calendar_idea()`** - Require selected theme, use calendar_week_posts
7. **Update `api_posts()`** - Use new tables
8. **Update `api_calendar_idea_status()`** - Use new tables, remove idea_id

### Low Priority (Cleanup)
9. **Remove `api_schedule_update_theme_to_idea()`** - No longer needed
10. **Update `get_post_by_theme()`** - Remove idea_id, use new tables
11. **Update taxonomy assignment** - Use new tables

### No Changes Needed
- `api_calendar_ideas()` - Ideas are perpetual, not part of week persistence
- Routes using `resolve_post_for_week()` - Utility handles changes internally

