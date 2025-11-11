# Navbar Post Type Fix - Remaining Routes

**Date:** 2025-01-10  
**Status:** Ready for Implementation  
**Priority:** High  
**Estimated Time:** 10 minutes

---

## Problem

The navbar substages switch incorrectly when navigating between planning pages for generated posts because some routes don't pass `post_type` to their templates.

**Root Cause:** See `docs/NAVBAR_SUBSTAGE_SWITCHING_BUG.md` for full explanation.

**Quick Summary:** Header template uses `{% if post_type == 'generated' %}` to show correct substages. If `post_type` is missing, it defaults to themed post substages (wrong).

---

## Routes That Need Fixing

### ✅ Already Fixed
- `planning_calendar_product_data_review()` - **FIXED** (all error handlers too)

### ✅ Already Correct (Pass `post_type`)
- `planning_calendar_taxonomy()` - Passes `post_type` (line 120)
- `planning_concept_brainstorm()` - Passes `post_type` (line 57)

### ❌ Need Fixing (3 routes)

#### 1. `planning_concept_section_structure()`
**File:** `blueprints/planning_concept.py`  
**Line:** 60-79

**Current Code:**
```python
def planning_concept_section_structure(post_id):
    """Section structure page"""
    resolved_post_id, year, week = _resolve_post_and_get_week_context(post_id)
    
    # Get content type name for category banner
    content_type_name = None
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT ti.display_name as content_type_name
            FROM post p
            LEFT JOIN taxonomy_item ti ON p.content_type_id = ti.id
            WHERE p.id = %s
        """, (resolved_post_id,))
        result = cursor.fetchone()
        if result:
            content_type_name = result.get('content_type_name')
    
    return render_template('planning/concept/section_structure.html', 
                          post_id=resolved_post_id, year=year, week=week, blueprint_name='planning',
                          content_type_name=content_type_name)
                          # ❌ MISSING: post_type=post_type
```

**Fix Required:**
1. Add `from utils.taxonomy_helpers import get_post_type` at top (if not already imported)
2. Add `post_type = get_post_type(resolved_post_id)` before render_template
3. Add `post_type=post_type` to render_template call

---

#### 2. `planning_concept_topic_allocation()`
**File:** `blueprints/planning_concept.py`  
**Line:** 81-100

**Current Code:**
```python
def planning_concept_topic_allocation(post_id):
    """Topic allocation page"""
    resolved_post_id, year, week = _resolve_post_and_get_week_context(post_id)
    
    # Get content type name for category banner
    content_type_name = None
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT ti.display_name as content_type_name
            FROM post p
            LEFT JOIN taxonomy_item ti ON p.content_type_id = ti.id
            WHERE p.id = %s
        """, (resolved_post_id,))
        result = cursor.fetchone()
        if result:
            content_type_name = result.get('content_type_name')
    
    return render_template('planning/concept/topic_allocation.html', 
                          post_id=resolved_post_id, year=year, week=week, blueprint_name='planning',
                          content_type_name=content_type_name)
                          # ❌ MISSING: post_type=post_type
```

**Fix Required:**
1. Add `post_type = get_post_type(resolved_post_id)` before render_template
2. Add `post_type=post_type` to render_template call

---

#### 3. `planning_concept_titling()`
**File:** `blueprints/planning_concept.py`  
**Line:** 102-121

**Current Code:**
```python
def planning_concept_titling(post_id):
    """Titling page"""
    resolved_post_id, year, week = _resolve_post_and_get_week_context(post_id)
    
    # Get content type name for category banner
    content_type_name = None
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT ti.display_name as content_type_name
            FROM post p
            LEFT JOIN taxonomy_item ti ON p.content_type_id = ti.id
            WHERE p.id = %s
        """, (resolved_post_id,))
        result = cursor.fetchone()
        if result:
            content_type_name = result.get('content_type_name')
    
    return render_template('planning/concept/titling.html', 
                          post_id=resolved_post_id, year=year, week=week, blueprint_name='planning',
                          content_type_name=content_type_name)
                          # ❌ MISSING: post_type=post_type
```

**Fix Required:**
1. Add `post_type = get_post_type(resolved_post_id)` before render_template
2. Add `post_type=post_type` to render_template call

---

## Implementation Pattern

All three routes follow the same pattern. Use `planning_concept_brainstorm()` as a reference (it's already correct):

```python
def planning_concept_brainstorm(post_id):
    """Brainstorm page"""
    from flask import redirect, url_for
    from utils.taxonomy_helpers import get_post_type
    
    # Check post type - redirect recipe/profile posts away from Planning stages
    post_type = get_post_type(post_id)  # ✅ Gets post_type
    if post_type == 'recipe':
        return redirect(url_for('authoring.authoring_sections_drafting', post_id=post_id))
    elif post_type == 'profile':
        return redirect(url_for('authoring.authoring_sections_drafting', post_id=post_id))
    
    resolved_post_id, year, week = _resolve_post_and_get_week_context(post_id)
    
    # ... get content_type_name ...
    
    return render_template('planning/concept/brainstorm.html', 
                          post_id=resolved_post_id, year=year, week=week, blueprint_name='planning',
                          post_type=post_type,  # ✅ Passes post_type
                          content_type_name=content_type_name)
```

**Note:** The three routes that need fixing use `resolved_post_id` (from `_resolve_post_and_get_week_context()`), so they should call `get_post_type(resolved_post_id)` not `get_post_type(post_id)`.

---

## Quick Fix Template

For each of the 3 routes, add these 2 lines:

```python
# After: resolved_post_id, year, week = _resolve_post_and_get_week_context(post_id)
# Add:
from utils.taxonomy_helpers import get_post_type
post_type = get_post_type(resolved_post_id)

# In render_template call, add:
post_type=post_type,
```

---

## Testing Checklist

After fixing all 3 routes:

1. **Navigate through generated post workflow:**
   - Start at Taxonomy page
   - Click "Product Data Review" → Should show correct substages ✅
   - Click "Topic Brainstorming" → Should show correct substages ✅
   - Click "Section Structure Design" → Should show correct substages ✅
   - Click "Section Ideas" → Should show correct substages ✅
   - Click "Section Titling" → Should show correct substages ✅

2. **Verify substages are consistent:**
   - All pages should show: Taxonomy → Product Data Review → Topic Brainstorming → Section Structure Design → Section Ideas → Section Titling
   - Should NOT show: Idea Generation (that's for themed posts only)

3. **Test with different post types:**
   - Generated posts: Should show Product Data Review substages
   - Themed posts: Should show Idea Generation substages
   - Recipe/Profile posts: Should redirect (not applicable)

---

## Files to Modify

**Single File:** `blueprints/planning_concept.py`

**Lines to modify:**
- Line ~60-79: `planning_concept_section_structure()`
- Line ~81-100: `planning_concept_topic_allocation()`
- Line ~102-121: `planning_concept_titling()`

**Estimated Changes:** 6 lines total (2 lines per function)

---

## Related Documentation

- `docs/NAVBAR_SUBSTAGE_SWITCHING_BUG.md` - Full diagnostic report
- `docs/NAVBAR_UNIFICATION_REFACTORING.md` - Broader navbar refactoring plan

