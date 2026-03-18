# Comprehensive Navbar Template Audit

**Date:** 2025-01-10  
**Status:** Complete Audit - Ready for Review  
**Scope:** All templates using `blog_pipeline_header.html` and their routes

---

## Executive Summary

This audit examines **33 templates** using the unified header system for:
1. **Missing `post_type` variable** (causes incorrect substage display for generated posts)
2. **Inconsistent header setup patterns** (script blocks, variable initialization)
3. **Missing optional variables** (post_title, post_status, post_created, post_updated)
4. **Inconsistent stage/substage naming** (already fixed in previous audit)

---

## Issue 1: Missing `post_type` Variable

### Problem
The header template uses `{% if post_type == 'generated' %}` to show correct substages. If `post_type` is missing, it defaults to themed post substages, causing incorrect navigation for generated posts.

### Routes Missing `post_type` (3 routes - from NAVBAR_POST_TYPE_FIX_REMAINING_ROUTES.md)

#### ❌ 1. `planning_concept_section_structure()`
**File:** `blueprints/planning_concept.py`  
**Line:** 60-79  
**Template:** `templates/planning/concept/section_structure.html`  
**Status:** ❌ MISSING `post_type`

**Current Code:**
```python
def planning_concept_section_structure(post_id):
    resolved_post_id, year, week = _resolve_post_and_get_week_context(post_id)
    # ... gets content_type_name ...
    return render_template('planning/concept/section_structure.html', 
                          post_id=resolved_post_id, year=year, week=week, 
                          blueprint_name='planning',
                          content_type_name=content_type_name)
                          # ❌ MISSING: post_type=post_type
```

#### ❌ 2. `planning_concept_topic_allocation()`
**File:** `blueprints/planning_concept.py`  
**Line:** 81-100  
**Template:** `templates/planning/concept/topic_allocation.html`  
**Status:** ❌ MISSING `post_type`

**Current Code:**
```python
def planning_concept_topic_allocation(post_id):
    resolved_post_id, year, week = _resolve_post_and_get_week_context(post_id)
    # ... gets content_type_name ...
    return render_template('planning/concept/topic_allocation.html', 
                          post_id=resolved_post_id, year=year, week=week, 
                          blueprint_name='planning',
                          content_type_name=content_type_name)
                          # ❌ MISSING: post_type=post_type
```

#### ❌ 3. `planning_concept_titling()`
**File:** `blueprints/planning_concept.py`  
**Line:** 102-121  
**Template:** `templates/planning/concept/titling.html`  
**Status:** ❌ MISSING `post_type`

**Current Code:**
```python
def planning_concept_titling(post_id):
    resolved_post_id, year, week = _resolve_post_and_get_week_context(post_id)
    # ... gets content_type_name ...
    return render_template('planning/concept/titling.html', 
                          post_id=resolved_post_id, year=year, week=week, 
                          blueprint_name='planning',
                          content_type_name=content_type_name)
                          # ❌ MISSING: post_type=post_type
```

### Routes That May Be Missing `post_type` (Need Verification)

#### ⚠️ 4. `planning_calendar_view()`
**File:** `blueprints/planning_calendar.py`  
**Line:** 14-26  
**Template:** `templates/planning/calendar/view.html`  
**Status:** ⚠️ LIKELY MISSING `post_type`

**Current Code:**
```python
def planning_calendar_view(post_id):
    year = datetime.now().year
    week_number = datetime.now().isocalendar()[1]
    return render_template('planning/calendar/view.html', 
                          post_id=post_id, year=year, week_number=week_number,
                          blueprint_name='planning')
                          # ⚠️ LIKELY MISSING: post_type
```

#### ⚠️ 5. `planning_calendar()`
**File:** `blueprints/planning_calendar_clean.py`  
**Line:** 14-18  
**Template:** `templates/planning/calendar.html`  
**Status:** ⚠️ LIKELY MISSING `post_type`

**Current Code:**
```python
def planning_calendar(post_id):
    return render_template('planning/calendar.html', 
                          post_id=post_id,
                          blueprint_name='planning')
                          # ⚠️ LIKELY MISSING: post_type
```

#### ⚠️ 6. `planning_calendar_ideas()`
**File:** `blueprints/planning_calendar.py`  
**Line:** 61-90  
**Template:** `templates/planning/calendar/ideas.html`  
**Status:** ⚠️ LIKELY MISSING `post_type` (but route checks post_type for redirects)

**Current Code:**
```python
def planning_calendar_ideas(post_id):
    # ... checks post_type for redirects but doesn't pass to template ...
    return render_template('planning/calendar/ideas.html', 
                          post_id=post_id, year=year, week_number=week_number,
                          blueprint_name='planning',
                          mode='post-based',
                          content_type_name=content_type_name)
                          # ⚠️ LIKELY MISSING: post_type
```

#### ⚠️ 7. `planning_calendar_ideas_week()`
**File:** `blueprints/planning_calendar_clean.py`  
**Line:** 141-224  
**Template:** `templates/planning/calendar/ideas_week.html`  
**Status:** ⚠️ LIKELY MISSING `post_type` (week-based, may not need it)

**Note:** This is week-based (not post-based), so `post_type` may not be applicable.

#### ⚠️ 8. `authoring_sections_ideas_to_include()`
**File:** `blueprints/authoring.py`  
**Line:** 297-321  
**Template:** `templates/authoring/sections/ideas_to_include.html`  
**Status:** ⚠️ LIKELY MISSING `post_type`

**Current Code:**
```python
def authoring_sections_ideas_to_include(post_id):
    # ... gets post ...
    return render_template('authoring/sections/ideas_to_include.html', 
                         post_id=post_id,
                         post=post,
                         page_title="Ideas to Include",
                         blueprint_name='authoring')
                         # ⚠️ LIKELY MISSING: post_type
```

#### ⚠️ 9. `authoring_sections_image_concepts()`
**File:** `blueprints/authoring_api_imaging.py`  
**Line:** 24-77  
**Template:** `templates/authoring/sections/image_concepts.html`  
**Status:** ⚠️ LIKELY MISSING `post_type`

**Current Code:**
```python
def authoring_sections_image_concepts(post_id):
    # ... gets post, illustration_method ...
    return render_template('authoring/sections/image_concepts.html', 
                         post_id=post_id,
                         post=post,
                         page_title="Image Concepts",
                         blueprint_name='authoring',
                         illustration_method=illustration_method,
                         panel_config=panel_config)
                         # ⚠️ LIKELY MISSING: post_type
```

#### ⚠️ 10. `authoring_sections_image_prompts()`
**File:** `blueprints/authoring_api_imaging.py`  
**Line:** 79-133  
**Template:** `templates/authoring/sections/image_prompts.html`  
**Status:** ⚠️ LIKELY MISSING `post_type`

**Current Code:**
```python
def authoring_sections_image_prompts(post_id):
    # ... gets post, illustration_method ...
    return render_template('authoring/sections/image_prompts.html', 
                         post_id=post_id,
                         post=post,
                         page_title="Image Prompts",
                         blueprint_name='authoring',
                         illustration_method=illustration_method)
                         # ⚠️ LIKELY MISSING: post_type
```

#### ⚠️ 11. `authoring_sections_image_captions()`
**File:** `blueprints/authoring_api_imaging.py`  
**Line:** 135-159  
**Template:** `templates/authoring/sections/image_captions.html`  
**Status:** ⚠️ LIKELY MISSING `post_type`

**Current Code:**
```python
def authoring_sections_image_captions(post_id):
    # ... gets post ...
    return render_template('authoring/sections/image_captions.html', 
                         post_id=post_id,
                         post=post,
                         page_title="Image Captions",
                         blueprint_name='authoring')
                         # ⚠️ LIKELY MISSING: post_type
```

### ✅ Routes That Correctly Pass `post_type`

1. ✅ `planning_calendar_taxonomy()` - Passes `post_type` (line 120)
2. ✅ `planning_concept_brainstorm()` - Passes `post_type` (line 57)
3. ✅ `planning_concept_outline()` - Passes `post_type` (line 130)
4. ✅ `planning_research_sources()` - Passes `post_type` (line 139)
5. ✅ `planning_calendar_week_view()` - Passes `post_type` (line 55)
6. ✅ `planning_calendar_product_data_review()` - Passes `post_type` (all error handlers)
7. ✅ `authoring_sections_drafting()` - Passes `post_type` (line 257)
8. ✅ `imaging_sections_image_generation()` - Passes `post_type` (line 102)
9. ✅ `imaging_sections_optimise()` - Passes `post_type` (line 158)
10. ✅ `header_header_title_summary()` - Passes `post_type` (line 210)
11. ✅ `header_header_image()` - Passes `post_type` (line 252)
12. ✅ `header_seo_meta()` - Passes `post_type` (line 301)

---

## Issue 2: Inconsistent Header Setup Patterns

### Pattern Analysis

Templates set `window.currentStage` and `window.currentSubstage` in different ways:

#### Pattern A: Script Block Before Header Include (Most Common)
```html
<script>
window.postId = {{ post_id }};
window.currentStage = 'concept';
window.currentSubstage = 'taxonomy';
</script>
{% include 'shared/blog_pipeline_header.html' %}
```
**Used by:** taxonomy.html, product_data_review.html, outline.html, sources.html

#### Pattern B: Script Block After Header Include
```html
{% include 'shared/blog_pipeline_header.html' %}
<script>
window.postId = {{ post_id }};
window.currentStage = 'calendar';
window.currentSubstage = 'view';
</script>
```
**Used by:** view.html, week_view.html

#### Pattern C: DOMContentLoaded Handler
```html
{% include 'shared/blog_pipeline_header.html' %}
<script>
document.addEventListener('DOMContentLoaded', function() {
    window.currentStage = 'concept';
    window.currentSubstage = 'brainstorm';
    window.postId = {{ post_id }};
});
</script>
```
**Used by:** brainstorm.html, titling.html, topic_allocation.html, section_structure.html

#### Pattern D: Mixed (Initial + DOMContentLoaded)
```html
<script>
window.postId = {{ post_id }};
window.currentSubstage = 'ideas';
// window.currentStage will be set in DOMContentLoaded to 'concept'
</script>
{% include 'shared/blog_pipeline_header.html' %}
<script>
document.addEventListener('DOMContentLoaded', function() {
    window.currentStage = 'concept';
    window.currentSubstage = 'ideas';
    // ... more code ...
});
</script>
```
**Used by:** ideas.html (confusing pattern)

### Inconsistencies Found

1. **Timing Issues:**
   - Pattern C (DOMContentLoaded) may cause delay in navigation highlighting
   - Pattern D (ideas.html) has redundant assignments

2. **Location Inconsistency:**
   - Some templates set variables before header include
   - Some set after header include
   - Some use DOMContentLoaded

3. **Missing `window.postId`:**
   - Some templates don't explicitly set `window.postId` (rely on header JS to extract from URL)

### Recommendation

**Standard Pattern (Recommended):**
```html
<script>
window.postId = {{ post_id }};
window.currentStage = 'concept';  // Must match data-stage in header
window.currentSubstage = 'taxonomy';
</script>
{% include 'shared/blog_pipeline_header.html' %}
```

**Rationale:**
- Variables set before header loads
- Header JavaScript can access them immediately
- No DOMContentLoaded delay
- Consistent across all templates

---

## Issue 3: Missing Optional Variables

### Variables Header Template Uses (Optional but Recommended)

1. **`post_type`** - Required for correct substage display (see Issue 1)
2. **`post_title`** - Used for generated posts title display (line 22)
3. **`post_status`** - Displayed in header (line 48)
4. **`post_created`** - Displayed in header (line 50)
5. **`post_updated`** - Displayed in header (line 52)

### Current State

**Routes That Pass All Optional Variables:**
- ✅ `imaging_sections_image_generation()` - Passes: post_type, post_title, post_status, post_created, post_updated
- ✅ `imaging_sections_optimise()` - Passes: post_type, post_title, post_status, post_created, post_updated
- ✅ `header_header_image()` - Passes: post_type (others loaded via JS)

**Routes That Pass Some:**
- ⚠️ `authoring_sections_drafting()` - Passes: post_type (missing: post_title, post_status, post_created, post_updated)
- ⚠️ `planning_calendar_taxonomy()` - Passes: post_type, post_title (missing: post_status, post_created, post_updated)

**Routes That Pass None:**
- ❌ Most planning routes - Only pass post_type (if at all)
- ❌ Most authoring routes - Only pass post_type (if at all)

### Impact

**Low Impact:** Missing `post_status`, `post_created`, `post_updated` is not critical because:
- Header JavaScript (`blog-pipeline-header.js`) fetches post data via API if not provided
- Falls back to "Unknown" if missing

**Medium Impact:** Missing `post_title` for generated posts:
- Header shows "Generated Post" instead of actual title
- Not critical but affects UX

---

## Issue 4: Header Template Data Tab Inconsistency

### Problem Found

**File:** `templates/shared/blog_pipeline_header.html`  
**Line:** 296

```jinja2
<div id="data-tab" class="tab-panel">
    {% if currentStage == 'planning' %}
        {% include 'planning/includes/data_tab.html' %}
    {% elif currentStage == 'imaging' %}
        {% include 'shared/data_display.html' %}
    {% elif currentStage == 'authoring' and currentSubstage == 'author-first-drafts' %}
        {% include 'shared/data_display.html' %}
    {% endif %}
</div>
```

**Issue:** Uses `currentStage == 'planning'` but:
- All templates set `window.currentStage = 'concept'` (not 'planning')
- Planning substages use `data-stage="concept"` (not 'planning')
- This means the data tab will NEVER show for Planning pages!

**Root Cause:** Legacy naming - "planning" was the old name, now it's "concept".

**Fix Required:** Change `currentStage == 'planning'` to `currentStage == 'concept'`

---

## Issue 5: Inconsistent `window.postId` Default Values

### Pattern Analysis

**Most Templates:**
```javascript
window.postId = {{ post_id }};
```

**Some Templates:**
```javascript
window.postId = {{ post_id|default(0) }};
```

**Templates Using `default(0)`:**
- `templates/imaging/sections/image_generation.html` (line 23)
- `templates/authoring/sections/image_captions.html` (line 20)
- `templates/authoring/sections/image_concepts.html` (line 21)
- `templates/authoring/sections/image_prompts.html` (line 20)
- `templates/imaging/sections/optimise.html` (line 19)
- `templates/imaging/sections/photo_selection.html` (line 22)

**Impact:** Low - `default(0)` is defensive but inconsistent. Should standardize.

---

## Issue 6: Missing `post_id` in Script Blocks

### Templates Missing Explicit `window.postId` or Stage Variables

**Templates Missing Stage Variables:**
- ❌ `templates/planning/concept/grouping.html` - **MISSING** `window.currentStage` and `window.currentSubstage`
  - Uses header but doesn't set navigation context
  - Navigation highlighting will not work correctly

**Templates Using Pattern C (DOMContentLoaded):**
- These templates set `window.postId` inside DOMContentLoaded, which may cause timing issues

**Recommendation:** Always set `window.postId`, `window.currentStage`, and `window.currentSubstage` before header include, even if also set in DOMContentLoaded.

---

## Issue 7: Header Template Variable Name Inconsistency

### Problem

**File:** `templates/shared/blog_pipeline_header.html`  
**Line:** 296

The template uses `currentStage` (Jinja2 variable) but templates set `window.currentStage` (JavaScript variable).

**These are DIFFERENT:**
- `currentStage` (Jinja2) - Set by route via `render_template(currentStage='...')`
- `window.currentStage` (JavaScript) - Set by template script blocks

**Current State:**
- No routes pass `currentStage` as Jinja2 variable
- All templates rely on `window.currentStage` (JavaScript)
- Data tab check uses Jinja2 `currentStage` which is always undefined!

**Fix Required:** Change data tab check to use JavaScript `window.currentStage` or pass `currentStage` from routes.

---

## Summary of Issues

### Critical Issues (Must Fix)

1. **3 routes missing `post_type`** (from NAVBAR_POST_TYPE_FIX_REMAINING_ROUTES.md)
   - `planning_concept_section_structure()`
   - `planning_concept_topic_allocation()`
   - `planning_concept_titling()`

2. **Data tab never shows for Planning pages**
   - Header template checks `currentStage == 'planning'` but should be `'concept'`
   - OR: Data tab should check `window.currentStage` via JavaScript
   - **Impact:** Planning data tab is completely broken

3. **Template missing navigation variables**
   - `templates/planning/concept/grouping.html` - Missing `window.currentStage` and `window.currentSubstage`
   - **Impact:** Navigation highlighting won't work on this page

### High Priority Issues

4. **10+ routes likely missing `post_type`**
   - Need verification and fixes

5. **Inconsistent header setup patterns**
   - 4 different patterns used across templates
   - Should standardize to Pattern A (script before include)

### Medium Priority Issues

6. **Missing optional variables** (post_title, post_status, etc.)
   - Low impact (header JS fetches via API)
   - But affects initial page load UX

7. **Inconsistent `window.postId` defaults**
   - Some use `default(0)`, some don't
   - Should standardize

### Low Priority Issues

8. **Mixed timing patterns** (DOMContentLoaded vs immediate)
   - Works but inconsistent
   - Could cause subtle timing issues

---

## Recommendations

### Immediate Fixes (Critical)

1. **Fix 3 routes missing `post_type`:**
   - Add `post_type = get_post_type(resolved_post_id)` to each route
   - Add `post_type=post_type` to render_template calls

2. **Fix data tab display:**
   - Change `currentStage == 'planning'` to `currentStage == 'concept'` in header template
   - OR: Use JavaScript to check `window.currentStage` instead

### Short-term Fixes (High Priority)

3. **Audit and fix all routes missing `post_type`:**
   - Verify each route that renders templates with header
   - Add `post_type` where missing

4. **Standardize header setup pattern:**
   - Convert all templates to Pattern A (script before include)
   - Remove DOMContentLoaded where not needed

### Long-term Improvements (Medium/Low Priority)

5. **Standardize variable passing:**
   - Create helper function to get all post variables
   - Use consistently across all routes

6. **Document header requirements:**
   - Create template for new routes
   - Document required vs optional variables

---

## Files Requiring Changes

### Routes (Python)
- `blueprints/planning_concept.py` - 3 routes need `post_type`
- `blueprints/planning_calendar.py` - Verify `post_type` passing
- `blueprints/planning_calendar_clean.py` - Verify `post_type` passing
- `blueprints/authoring.py` - Verify `post_type` passing
- `blueprints/authoring_api_imaging.py` - Verify `post_type` passing

### Templates (HTML)
- `templates/shared/blog_pipeline_header.html` - Fix data tab check (line 296)
- `templates/planning/concept/grouping.html` - Add missing `window.currentStage` and `window.currentSubstage`
- All templates using Pattern C/D - Convert to Pattern A

---

## Testing Checklist

After fixes:

- [ ] Generated posts show correct substages on all Planning pages
- [ ] Data tab displays for Planning pages
- [ ] All templates use consistent header setup pattern
- [ ] Navigation highlighting works immediately (no delay)
- [ ] Post type badge displays correctly for all post types
- [ ] Post status/dates display correctly (or "Unknown" if not provided)

---

## Related Documentation

- `docs/NAVBAR_POST_TYPE_FIX_REMAINING_ROUTES.md` - Specific fix for 3 routes
- `docs/NAVBAR_AUDIT_REPORT.md` - Previous audit (stage naming)
- `docs/NAVBAR_UNIFICATION_REFACTORING.md` - Original refactoring plan

