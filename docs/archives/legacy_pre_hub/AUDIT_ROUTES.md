# Routes Audit - Week Persistence V2

## Overview

This document audits all route handlers to identify:
1. Routes that accept `post_id` parameter
2. Routes that read year/week from URL params
3. Routes that need to call `resolve_post_for_week()`
4. Routes that need to preserve week context in redirects
5. Routes that need to attach week params to templates

---

## File: `blueprints/planning.py`

### Routes Accepting `post_id` (25+ routes)

All planning routes follow pattern: `/planning/posts/<int:post_id>/...`

**Current Behavior:**
- Routes accept `post_id` as URL parameter
- Some routes read year/week from query params (`?year=X&week=Y`)
- Week context is NOT required, but can be provided
- Templates receive `post_id` but week context may be missing

**Routes Requiring Changes:**

1. **Planning Views (6 routes)**
   - `/planning/posts/<post_id>` - planning_post_overview
   - `/planning/posts/<post_id>/concept` - planning_concept
   - `/planning/posts/<post_id>/calendar` - planning_calendar
   - `/planning/posts/<post_id>/research` - planning_research
   - `/planning/posts/<post_id>/calendar/view` - planning_calendar_view
   - `/planning/posts/<post_id>/calendar/week-view` - planning_calendar_week_view

2. **Calendar Routes (3 routes)**
   - `/planning/posts/<post_id>/calendar/ideas` - planning_calendar_ideas
   - `/planning/posts/<post_id>/calendar/taxonomy` - planning_calendar_taxonomy
   - `/planning/calendar/ideas/week/<week_number>` - planning_calendar_ideas_week (NO post_id, week-based)

3. **Concept Routes (5 routes)**
   - `/planning/posts/<post_id>/concept/brainstorm`
   - `/planning/posts/<post_id>/concept/section-structure`
   - `/planning/posts/<post_id>/concept/topic-allocation`
   - `/planning/posts/<post_id>/concept/titling`
   - `/planning/posts/<post_id>/concept/outline`

4. **Research Routes (4 routes)**
   - `/planning/posts/<post_id>/research/sources`
   - `/planning/posts/<post_id>/research/visuals`
   - `/planning/posts/<post_id>/research/prompts`
   - `/planning/posts/<post_id>/research/verification`

**Required Changes:**
1. **Read year/week from query params** - All routes should read `?year=X&week=Y`
2. **Use resolve_post_for_week()** - If year/week provided, resolve correct post_id
3. **Pass week context to templates** - Always pass year/week to templates
4. **Preserve week context in redirects** - When redirecting, include year/week params

**Example Pattern:**
```python
@bp.route('/posts/<int:post_id>/concept')
def planning_concept(post_id):
    # Read week context from URL
    year = request.args.get('year', type=int)
    week = request.args.get('week', type=int)
    
    # Resolve correct post if week context provided
    if year and week:
        from utils.week_post_resolver import resolve_post_for_week
        resolved_post_id = resolve_post_for_week(year, week)
        if resolved_post_id:
            post_id = resolved_post_id
    
    # Pass to template
    return concept_func(post_id, year=year, week=week)
```

---

## File: `blueprints/planning_calendar_clean.py`

### `planning_calendar(post_id)`
**Current:** Simple template render with post_id
**Required:** Read year/week, resolve post, pass week context

### `planning_calendar_view(post_id)`
**Current:** Simple template render with post_id
**Required:** Read year/week, resolve post, pass week context

### `planning_calendar_week_view(post_id)`
**Current:** Simple template render with post_id
**Required:** Read year/week (required for week view!), resolve post, pass week context

### `planning_calendar_ideas(post_id)`
**Current:** Reads year/week from URL params, defaults to current week
**Required:** Keep existing behavior, but ensure week context is always passed

### `planning_calendar_ideas_week(week_number)`
**Current:** Reads year from URL params, accepts optional post_id
**Required:** Ensure year/week are always in URL, preserve in template

---

## File: `blueprints/authoring.py`

### Routes Accepting `post_id` (5+ routes)

1. `/authoring/posts/<post_id>` - authoring_post_overview
2. `/authoring/posts/<post_id>/sections/drafting` - authoring_sections_drafting
3. `/authoring/posts/<post_id>/sections` - authoring_sections_overview
4. Additional section routes...

**Current Behavior:**
- Simple template renders with post_id
- No week context handling
- No resolve_post_for_week() calls

**Required Changes:**
1. Read year/week from query params
2. Call resolve_post_for_week() if week context provided
3. Pass week context to templates
4. Update templates to use WeekContext

---

## File: `blueprints/authoring_api_imaging.py`

### Routes Already Using `resolve_post_for_week()`

1. `/authoring_imaging/posts/<post_id>/sections/image_concepts`
2. `/authoring_imaging/posts/<post_id>/sections/image_prompts`
3. `/authoring_imaging/posts/<post_id>/sections/image_captions`

**Current Behavior:**
- Reads year/week from URL params
- Calls `resolve_post_for_week(year, week)`
- Uses resolved post_id

**Required Changes:**
- **NO CHANGES** - Already correct
- Ensure year/week are always in URLs (frontend responsibility)

---

## File: `blueprints/imaging.py`

### Routes Already Using `resolve_post_for_week()`

1. `/imaging/posts/<post_id>/sections/image-generation`
2. `/imaging/posts/<post_id>/sections/optimise`
3. `/imaging/posts/<post_id>/sections/photo-selection`

**Current Behavior:**
- Same as authoring_api_imaging.py

**Required Changes:**
- **NO CHANGES** - Already correct

---

## File: `blueprints/header.py`

### Routes Accepting `post_id`
(Need to check if header.py exists and review)

**Required Changes:**
- Read year/week from query params
- Pass to templates
- Preserve in redirects

---

## Summary of Route Changes

### High Priority (Routes that need week resolution)
1. All `/planning/posts/<post_id>/...` routes (20+ routes)
2. All `/authoring/posts/<post_id>/...` routes (5+ routes)
3. Calendar week view routes (must have week context)

### Medium Priority (Routes that should preserve week context)
1. Redirect routes - preserve year/week in redirect URLs
2. API routes that redirect - include year/week in response URLs

### Low Priority (Routes that don't need changes)
1. Routes already using `resolve_post_for_week()` - no changes
2. Routes without post_id - no changes needed
3. Dashboard/index routes - no week context needed

## Common Pattern for Route Updates

```python
@bp.route('/posts/<int:post_id>/...')
def route_handler(post_id):
    # 1. Read week context from query params
    year = request.args.get('year', type=int)
    week = request.args.get('week', type=int)
    
    # 2. Resolve post if week context provided
    if year and week:
        from utils.week_post_resolver import resolve_post_for_week
        resolved_post_id = resolve_post_for_week(year, week)
        if resolved_post_id:
            post_id = resolved_post_id
    
    # 3. Call view function with week context
    return view_func(post_id, year=year, week=week)
```

## Redirect Pattern

```python
# When redirecting, preserve week context
if year and week:
    return redirect(url_for('route', post_id=post_id, year=year, week=week))
else:
    return redirect(url_for('route', post_id=post_id))
```

