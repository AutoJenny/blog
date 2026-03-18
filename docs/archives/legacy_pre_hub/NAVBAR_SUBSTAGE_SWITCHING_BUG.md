# Navbar Substage Switching Bug - Diagnostic Report

**Date:** 2025-01-10  
**Status:** Root Cause Identified  
**Priority:** High  
**Severity:** Medium (breaks user experience but doesn't crash)

---

## Problem Statement

When navigating from the Taxonomy page to the Product Data Review page for a generated post (post_id 88), the navbar substages switch from the correct set (Taxonomy → Product Data Review → Topic Brainstorming...) to the wrong set (Taxonomy → Idea Generation → Topic Brainstorming...).

**Expected Behavior:**
- Taxonomy page shows: Taxonomy → **Product Data Review** → Topic Brainstorming → Section Structure Design → Section Ideas → Section Titling
- Product Data Review page should show: **Taxonomy** → Product Data Review → Topic Brainstorming → Section Structure Design → Section Ideas → Section Titling

**Actual Behavior:**
- Taxonomy page shows: Taxonomy → **Product Data Review** → Topic Brainstorming → Section Structure Design → Section Ideas → Section Titling ✅
- Product Data Review page shows: Taxonomy → **Idea Generation** → Topic Brainstorming → Section Structure Design → Section Ideas → Section Titling ❌

---

## Root Cause

**Missing Template Variable: `post_type`**

The `planning_calendar_product_data_review()` route in `blueprints/planning_calendar_product_data_review.py` does **NOT** pass the `post_type` variable to the template.

### Current Route Implementation

**File:** `blueprints/planning_calendar_product_data_review.py`  
**Lines:** 105-111

```python
return render_template('planning/calendar/product_data_review.html',
                     post_id=post_id,
                     product_id=product_id,
                     product_data=product_data,
                     validation=validation,
                     content_type_name=content_type_name,
                     blueprint_name='planning')
# ❌ MISSING: post_type=post_type
```

### Header Template Conditional Logic

**File:** `templates/shared/blog_pipeline_header.html`  
**Lines:** 125-199

The header template uses Jinja2 conditionals to determine which substages to render:

```jinja2
{% if post_type not in ['recipe', 'profile', 'generated'] %}
    <!-- Shows themed post substages: Taxonomy → Idea Generation → ... -->
{% elif post_type == 'generated' %}
    <!-- Shows generated post substages: Taxonomy → Product Data Review → ... -->
{% endif %}
```

**Problem:** When `post_type` is undefined (not passed to template), the Jinja2 conditional evaluates to `False` for both conditions, causing it to fall back to the default (themed post substages with "Idea Generation").

---

## Evidence

### 1. Route Does Not Pass `post_type`

**File:** `blueprints/planning_calendar_product_data_review.py`

The route:
- ✅ Gets `post_type` using `get_post_type(post_id)` (line 23)
- ✅ Uses it to check if post is generated (line 24)
- ❌ Does NOT pass it to `render_template()` (line 105)

### 2. Template Expects `post_type`

**File:** `templates/planning/calendar/product_data_review.html`

The template includes the header:
```jinja2
{% include 'shared/blog_pipeline_header.html' %}
```

But `post_type` is not in the template context, so the header's conditional logic fails.

### 3. HTML Output Shows Wrong Substages

When fetching the Product Data Review page, the rendered HTML shows:
- Calendar substages (correct)
- **Planning substages with "Idea Generation"** (wrong - should be "Product Data Review")

This confirms that the `{% elif post_type == 'generated' %}` condition is not being met.

---

## Solution

### Fix: Pass `post_type` to Template

**File:** `blueprints/planning_calendar_product_data_review.py`  
**Line:** 105

**Change:**
```python
return render_template('planning/calendar/product_data_review.html',
                     post_id=post_id,
                     product_id=product_id,
                     product_data=product_data,
                     validation=validation,
                     content_type_name=content_type_name,
                     post_type=post_type,  # ✅ ADD THIS
                     blueprint_name='planning')
```

**Note:** The `post_type` variable is already available in the function scope (line 23), so this is a simple one-line addition.

---

## Verification Steps

After applying the fix:

1. **Navigate to Taxonomy page:**
   - URL: `http://localhost:5000/planning/posts/88/calendar/taxonomy`
   - Verify substages show: Taxonomy → **Product Data Review** → Topic Brainstorming → ...

2. **Click "Product Data Review" tab:**
   - URL: `http://localhost:5000/planning/posts/88/calendar/product-data-review`
   - Verify substages still show: **Taxonomy** → Product Data Review → Topic Brainstorming → ...
   - Verify "Product Data Review" tab is highlighted/active

3. **Check browser console:**
   - Open DevTools → Console
   - Verify no errors related to `post_type`
   - Check that `window.currentStage = 'concept'` and `window.currentSubstage = 'product-data-review'`

4. **Verify HTML source:**
   - View page source
   - Search for "Product Data Review"
   - Verify it appears in the Planning substages section
   - Verify "Idea Generation" does NOT appear

---

## Related Issues

This is likely not an isolated issue. Other routes may also be missing `post_type`:

### Routes to Audit

1. ✅ `planning_calendar_taxonomy()` - **VERIFIED:** Passes `post_type` (line 120)
2. ❌ `planning_calendar_product_data_review()` - **MISSING:** Does not pass `post_type`
3. ⚠️ `planning_calendar_ideas()` - **NEEDS CHECK:** Verify passes `post_type`
4. ⚠️ `planning_concept_brainstorm()` - **NEEDS CHECK:** Verify passes `post_type`
5. ⚠️ `planning_concept_section_structure()` - **NEEDS CHECK:** Verify passes `post_type`
6. ⚠️ `planning_concept_topic_allocation()` - **NEEDS CHECK:** Verify passes `post_type`
7. ⚠️ `planning_concept_titling()` - **NEEDS CHECK:** Verify passes `post_type`

**Recommendation:** Create a comprehensive audit of all planning routes to ensure they all pass `post_type` to templates.

---

## Impact Assessment

### User Impact
- **Severity:** Medium
- **Frequency:** 100% (happens every time user navigates to Product Data Review)
- **User Confusion:** High (wrong navigation options shown)
- **Workaround:** User can still navigate manually, but sees incorrect options

### Technical Impact
- **Risk:** Low (doesn't crash, just shows wrong UI)
- **Fix Complexity:** Very Low (one line change)
- **Testing Required:** Minimal (visual verification)

---

## Files to Modify

### Primary Fix
- **File:** `blueprints/planning_calendar_product_data_review.py`
- **Line:** 105
- **Change:** Add `post_type=post_type` to `render_template()` call

### Optional: Comprehensive Audit
- Audit all planning routes in:
  - `blueprints/planning_calendar_clean.py`
  - `blueprints/planning_calendar.py`
  - `blueprints/planning.py`
  - `blueprints/planning_concept.py` (if exists)

---

## Testing Checklist

After fix is applied:

- [ ] Taxonomy page shows correct substages for generated posts
- [ ] Product Data Review page shows correct substages for generated posts
- [ ] Navigation between Taxonomy and Product Data Review maintains correct substages
- [ ] Active substage highlighting works correctly
- [ ] No JavaScript console errors
- [ ] HTML source shows correct substages (Product Data Review, not Idea Generation)
- [ ] Test with other post types (themed, recipe, profile) to ensure no regressions

---

## Additional Notes

1. **Why This Happened:**
   - The route was created before the header template's conditional logic was fully implemented
   - The `post_type` variable was used for routing logic but not passed to template
   - Template assumes `post_type` is always available (which is correct, but route didn't provide it)

2. **Prevention:**
   - Add `post_type` to a standard template context helper/mixin
   - Or create a decorator that automatically adds `post_type` to all planning routes
   - Or add a linting rule to check that routes pass required variables

3. **Related Documentation:**
   - See `docs/NAVBAR_UNIFICATION_REFACTORING.md` for broader navbar issues
   - See `docs/NAVBAR_AUDIT_REPORT.md` (if exists) for comprehensive template audit

---

## Quick Fix Summary

**One-line fix in `blueprints/planning_calendar_product_data_review.py` line 105:**

```python
# BEFORE:
return render_template('planning/calendar/product_data_review.html',
                     post_id=post_id,
                     product_id=product_id,
                     product_data=product_data,
                     validation=validation,
                     content_type_name=content_type_name,
                     blueprint_name='planning')

# AFTER:
return render_template('planning/calendar/product_data_review.html',
                     post_id=post_id,
                     product_id=product_id,
                     product_data=product_data,
                     validation=validation,
                     content_type_name=content_type_name,
                     post_type=post_type,  # ✅ ADD THIS LINE
                     blueprint_name='planning')
```

**Estimated Time:** 2 minutes to fix + 5 minutes to test

