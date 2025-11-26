# Post ID and Week Resolution - Full Audit Report

## Critical Issue - CONFIRMED

**Problem:** Data for post 96 (Thanksgiving) has vanished. When accessing `/planning/posts/96/calendar/taxonomy?year=2025&week=48`, the system is displaying data for post 97 instead.

**Root Cause:** The codebase extensively uses `resolve_post_for_week()` which **changes the post_id** based on what's scheduled for that week, rather than using the post_id from the URL as the definitive identifier.

### Database Evidence

**Current State:**
- Post 96 exists: "Thanksgiving", Theme: 2, Content Type: 7, Format: 11
- Post 97 exists: "St Andrew's Day", Theme: None, Content Type: None, Format: None
- **Both posts are assigned to week 2025/48:**
  - Post 96: Created 2025-11-24 23:16:11
  - Post 97: Created 2025-11-25 13:38:05 (MORE RECENT)

**The Problem:**
- `resolve_post_for_week(2025, 48)` uses `ORDER BY created_at DESC LIMIT 1`
- This returns **post 97** (most recent assignment)
- When user navigates to `/planning/posts/96/...?year=2025&week=48`, code calls `resolve_post_for_week()` and **changes post_id from 96 to 97**
- All operations (taxonomy, ideas, etc.) are applied to post 97 instead of post 96
- **Result: Post 96's data appears to vanish, post 97 gets the data instead**

## Architecture Problem

### Current (BROKEN) Behavior

1. User navigates to: `/planning/posts/96/calendar/taxonomy?year=2025&week=48`
2. Code calls `resolve_post_for_week(2025, 48)` 
3. Function queries `calendar_week_posts` to find post assigned to week 2025/48
4. If week 2025/48 is assigned to post 97, code **changes post_id from 96 to 97**
5. All operations (taxonomy, ideas, etc.) are applied to post 97 instead of post 96
6. **Result: Post 96's data appears to vanish, post 97 gets the data instead**

### Correct Behavior (What Should Happen)

1. User navigates to: `/planning/posts/96/calendar/taxonomy?year=2025&week=48`
2. **post_id=96 is ALWAYS used** - it's the definitive identifier
3. `year=2025&week=48` is ONLY used for:
   - Displaying week-specific context (calendar view, week selection)
   - Filtering/grouping data by week
   - **NOT for changing which post is being edited**

## Files Using `resolve_post_for_week()` (Problematic)

### High Priority - Data Modification Routes

1. **`blueprints/planning_calendar_clean.py`**
   - `planning_calendar_ideas()` - Line 194: Changes post_id based on week
   - `planning_calendar_week_view()` - Line 127: Changes post_id based on week
   - **Impact:** All planning stages (ideas, taxonomy, etc.) use wrong post_id

2. **`blueprints/planning_api_taxonomy.py`**
   - `generate_taxonomy()` - Previously had redirect logic (fixed, but verify)
   - **Impact:** Taxonomy assignment goes to wrong post

3. **`blueprints/header/routes.py`**
   - Multiple routes use `resolve_target_post_id()` which calls `resolve_post_for_week()`
   - **Impact:** Header generation uses wrong post_id

4. **`blueprints/authoring_api_imaging.py`**
   - `authoring_sections_image_concepts()` - Line 36: Changes post_id
   - `authoring_sections_image_prompts()` - Line 113: Changes post_id
   - **Impact:** Image concepts/prompts assigned to wrong post

5. **`blueprints/imaging_routes.py`**
   - Multiple routes change post_id based on week
   - **Impact:** Image generation uses wrong post_id

### Medium Priority - Display Routes

6. **`blueprints/planning_concept.py`**
   - `_resolve_post_and_get_week_context()` - Changes post_id
   - **Impact:** Concept pages show wrong post data

## Database Schema

### Current Tables

1. **`calendar_week_posts`**
   - Stores: `(year, week_number, post_id)`
   - Purpose: **Schedule posts to weeks** (for publishing calendar)
   - **NOT for determining which post to edit**

2. **`post`**
   - Stores: Post data (title, content, taxonomy, etc.)
   - **post_id is the PRIMARY identifier**

3. **`post_development`**
   - Stores: Development data (expanded_idea, section_structure, etc.)
   - Linked by: `post_id` (NOT by week)

## Correct Architecture

### Principle 1: Post ID is Definitive

- **post_id in URL = definitive identifier**
- Week parameters are **context only**, not identifiers
- Never change post_id based on week context

### Principle 2: Week is Context, Not Identifier

- Week parameters (`?year=2025&week=48`) are used for:
  - Displaying week-specific UI (calendar view)
  - Filtering data by week
  - Scheduling/publishing context
  - **NOT for determining which post to edit**

### Principle 3: Posts Can Be Reallocated to Different Weeks

- A post can be moved from week 48 to week 49
- This should ONLY update `calendar_week_posts` table
- **Should NOT affect the post's data or post_id**

## Required Fixes

### Fix 1: Remove `resolve_post_for_week()` from Data Modification Routes

**Files to Fix:**
- `blueprints/planning_calendar_clean.py`
- `blueprints/planning_api_taxonomy.py`
- `blueprints/authoring_api_imaging.py`
- `blueprints/imaging_routes.py`
- `blueprints/planning_concept.py`

**Change:**
```python
# BEFORE (WRONG):
resolved_post_id = resolve_post_for_week(year, week)
if resolved_post_id:
    target_post_id = resolved_post_id  # Changes post_id!

# AFTER (CORRECT):
target_post_id = post_id  # Always use URL post_id
# Week is only used for context/display
```

### Fix 2: Update `resolve_post_for_week()` Documentation

**File:** `utils/week_post_resolver.py`

**Add Warning:**
```python
"""
WARNING: This function should ONLY be used for:
- Displaying which post is scheduled for a week (calendar view)
- Publishing/scheduling operations
- NOT for determining which post to edit when post_id is in URL

DO NOT use this function in routes that modify post data.
Always use the post_id from the URL parameter.
"""
```

### Fix 3: Create New Helper for Week Context (Display Only)

**New Function:** `get_week_context_for_post(post_id)`

```python
def get_week_context_for_post(post_id):
    """
    Get week context for a post (for display only).
    Does NOT change post_id - only returns week info.
    
    Returns:
        tuple: (year, week_number) or (None, None)
    """
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT year, week_number
            FROM calendar_week_posts
            WHERE post_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (post_id,))
        result = cursor.fetchone()
        if result:
            return result['year'], result['week_number']
    return None, None
```

### Fix 4: Update Route Handlers

**Pattern to Follow:**

```python
@bp.route('/posts/<int:post_id>/calendar/taxonomy')
def planning_calendar_taxonomy(post_id):
    """
    Taxonomy substage for a specific post.
    
    Args:
        post_id: DEFINITIVE post identifier (from URL)
        year, week: Optional query params for context/display only
    """
    # ALWAYS use post_id from URL - never change it
    target_post_id = post_id
    
    # Week params are for context only (calendar display, etc.)
    year = request.args.get('year', type=int)
    week = request.args.get('week', type=int)
    
    # If week not provided, try to get it from post's schedule
    if not (year and week):
        year, week = get_week_context_for_post(post_id)
    
    # Fetch post data using target_post_id (always post_id from URL)
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT * FROM post WHERE id = %s
        """, (target_post_id,))
        post = cursor.fetchone()
    
    # Render with post_id and week context
    return render_template('...', 
                          post_id=target_post_id,  # Always from URL
                          year=year,              # Context only
                          week=week)              # Context only
```

## Verification Steps

### Step 1: Check Database State

```sql
-- Check post 96 exists and has data
SELECT id, title, theme_id, content_type_id, format_id 
FROM post WHERE id = 96;

-- Check post 96's development data
SELECT post_id, expanded_idea, section_structure 
FROM post_development WHERE post_id = 96;

-- Check which post is assigned to week 2025/48
SELECT post_id, year, week_number 
FROM calendar_week_posts 
WHERE year = 2025 AND week_number = 48;

-- Check if post 96 is assigned to any week
SELECT year, week_number 
FROM calendar_week_posts 
WHERE post_id = 96;
```

### Step 2: Test URL Behavior

```bash
# Should ALWAYS show post 96's data, regardless of week assignment
curl "http://localhost:5000/planning/posts/96/calendar/taxonomy?year=2025&week=48"

# Should show post 96's taxonomy, even if week 2025/48 is assigned to post 97
```

### Step 3: Check Server Logs

```bash
# Look for post_id changes
grep "resolved to post_id" unified_app.log
grep "resolve_post_for_week" unified_app.log
```

## Immediate Action Items

1. **STOP using `resolve_post_for_week()` in data modification routes**
2. **Update all routes to use post_id from URL directly**
3. **Add validation to prevent post_id changes**
4. **Create audit log to track post_id changes**
5. **Restore post 96's data if it was overwritten**

## Long-Term Improvements

1. **Separate "scheduling" from "editing"**
   - Scheduling: Use `calendar_week_posts` to assign posts to weeks
   - Editing: Always use post_id from URL

2. **Add database constraints**
   - Ensure post_id cannot be changed by week resolution
   - Add audit trail for post modifications

3. **Update documentation**
   - Document that post_id is definitive
   - Document that week is context only

4. **Add tests**
   - Test that post_id never changes based on week
   - Test that posts can be reallocated to different weeks

