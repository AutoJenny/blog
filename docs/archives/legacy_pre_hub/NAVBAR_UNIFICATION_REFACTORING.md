# Navbar Unification Refactoring Project Brief

**Date:** 2025-01-10  
**Status:** Planning  
**Priority:** High  
**Estimated Complexity:** Medium

---

## Problem Statement

The blog pipeline navigation header (`blog_pipeline_header.html`) has inconsistent behavior across different pages:

1. **Main Stage Buttons Inconsistency:**
   - Week View (`/planning/posts/0/calendar/week-view`) shows both "Calendar" and "Planning" buttons
   - Taxonomy page (`/planning/posts/88/calendar/taxonomy`) for generated posts only shows "Planning" button (Calendar is hidden)
   - This creates confusion and breaks user expectations

2. **Sub-stage Navigation Inconsistency:**
   - Sub-stages are controlled by JavaScript that matches `data-stage` attributes
   - Taxonomy page sets `window.currentStage = 'planning'` but Planning substages use `data-stage="concept"`
   - This mismatch causes substages to not display correctly

3. **Multiple Header Systems:**
   - Some pages use `blog_pipeline_header.html` (unified system)
   - Some pages may use other header includes
   - Need to verify all pages use the same system

---

## Current Architecture

### Header Template Location
- **File:** `templates/shared/blog_pipeline_header.html`
- **CSS:** `static/css/shared/blog-pipeline-header.css`
- **JavaScript:** `static/js/shared/blog-pipeline-header.js`

### Pages Using the Header
All planning calendar pages include the header:
- `templates/planning/calendar/taxonomy.html`
- `templates/planning/calendar/week_view.html`
- `templates/planning/calendar/ideas.html`
- `templates/planning/calendar/ideas_week.html`
- `templates/planning/calendar/view.html`
- `templates/planning/calendar/product_data_review.html`

### Current Conditional Logic

**Main Stage Buttons (lines 58-75):**
```jinja2
{% if post_type not in ['recipe', 'profile', 'generated'] %}
    <!-- Shows Calendar + Planning -->
{% elif post_type == 'generated' %}
    <!-- Shows ONLY Planning (no Calendar) -->
{% endif %}
```

**Sub-stage Groups:**
- Calendar substages: `data-stage="calendar"`
- Planning substages: `data-stage="concept"` (NOT "planning"!)
- Authoring substages: `data-stage="authoring"`
- Imaging substages: `data-stage="imaging"`
- Header substages: `data-stage="header"`

### JavaScript Visibility Control

**File:** `static/js/shared/blog-pipeline-header.js`

**Function:** `updateNavigationHighlighting()` (lines 327-383)

Shows/hides substage groups based on:
```javascript
if (group.getAttribute('data-stage') === currentStage) {
    group.style.display = 'flex';
}
```

**Problem:** Taxonomy page sets `window.currentStage = 'planning'` but Planning substages use `data-stage="concept"`, so they never match!

---

## Root Causes

1. **Stage Naming Mismatch:**
   - JavaScript expects `currentStage` to match `data-stage` attribute
   - Taxonomy page sets `currentStage = 'planning'` (FIXED: now uses 'concept')
   - But Planning substages have `data-stage="concept"`
   - **Fix:** Change all templates to use `currentStage = 'concept'` (matches existing `data-stage`)
   - **AUDIT FINDING:** 2 templates still use incorrect `'planning'` - see `NAVBAR_AUDIT_REPORT.md`

2. **Inconsistent Button Visibility:**
   - Generated posts hide Calendar button, but week-view shows it
   - **Decision needed:** Should generated posts show Calendar button? (User expects yes)

3. **Template Variable Passing:**
   - All templates should pass `post_type` to header
   - Verified: `planning_calendar_taxonomy()` does pass `post_type`
   - But need to verify all other routes do too

---

## Requirements

### Functional Requirements

1. **Consistent Main Stage Buttons:**
   - All pages should show the same main stage buttons for the same post type
   - Generated posts should show "Calendar" button (user expectation)
   - Generated posts should show "Planning" button (already working)

2. **Consistent Sub-stage Display:**
   - Sub-stages should display when on the corresponding stage
   - Taxonomy page should show Planning substages when `currentStage` is set correctly
   - Week-view should show Calendar substages when appropriate

3. **Single Source of Truth:**
   - All pages must use `blog_pipeline_header.html`
   - No duplicate or alternative header systems
   - Consistent variable passing (`post_type`, `post_id`, `post_title`)

### Technical Requirements

1. **Fix Stage Naming:**
   - Standardize on either `'concept'` or `'planning'` for Planning stage
   - Update all templates to use the same value
   - Update JavaScript to match

2. **Fix Button Visibility:**
   - Remove conditional hiding of Calendar button for generated posts
   - OR add explicit logic if Calendar should be hidden for specific reasons

3. **Verify Template Variables:**
   - Audit all routes that render planning templates
   - Ensure all pass: `post_type`, `post_id`, `post_title`
   - Document required variables

---

## Implementation Plan

### Phase 1: Investigation & Documentation

1. **Audit All Routes:**
   - List all Flask routes that render planning templates
   - Check which variables they pass to templates
   - Document any missing variables

2. **Audit All Templates:**
   - List all templates that include `blog_pipeline_header.html`
   - Check what `window.currentStage` and `window.currentSubstage` they set
   - Document inconsistencies

3. **Document Stage Naming:**
   - Decide on standard stage names:
     - `'calendar'` for Calendar stage
     - `'concept'` OR `'planning'` for Planning stage (choose one!)
     - `'authoring'` for Authoring stage
     - `'imaging'` for Imaging stage
     - `'header'` for Header stage

### Phase 2: Standardization

1. **Fix Stage Naming:**
   - Choose standard name for Planning stage (recommend `'concept'` to match existing `data-stage`)
   - Update all templates to use standard name
   - Update JavaScript if needed

2. **Fix Button Visibility:**
   - Update header template to show Calendar button for generated posts
   - Test that navigation works correctly

3. **Fix Sub-stage Display:**
   - Ensure all templates set `window.currentStage` correctly
   - Ensure JavaScript matches `data-stage` attributes
   - Test that substages show/hide correctly

### Phase 3: Verification & Testing

1. **Test All Pages:**
   - Test each planning page with different post types:
     - Themed posts
     - Generated posts
     - Recipe posts (should redirect, but test)
     - Profile posts (should redirect, but test)

2. **Test Navigation:**
   - Click through all main stage buttons
   - Click through all substage buttons
   - Verify correct pages load
   - Verify correct substages highlight

3. **Cross-browser Testing:**
   - Test in Chrome, Firefox, Safari
   - Verify JavaScript works correctly
   - Verify CSS displays correctly

---

## Files to Modify

### Templates
- `templates/shared/blog_pipeline_header.html` - Fix button visibility and stage logic
- `templates/planning/calendar/taxonomy.html` - Fix `window.currentStage` value
- `templates/planning/calendar/week_view.html` - Verify `window.currentStage` value
- `templates/planning/calendar/ideas.html` - Verify `window.currentStage` value
- `templates/planning/calendar/ideas_week.html` - Verify `window.currentStage` value
- `templates/planning/calendar/view.html` - Verify `window.currentStage` value
- `templates/planning/calendar/product_data_review.html` - Verify `window.currentStage` value

### JavaScript
- `static/js/shared/blog-pipeline-header.js` - Verify stage matching logic

### Python Routes (if needed)
- `blueprints/planning_calendar.py` - Verify variable passing
- `blueprints/planning_calendar_clean.py` - Verify variable passing
- `blueprints/planning.py` - Verify variable passing

---

## Decision Points

### Decision 1: Planning Stage Name
**Question:** Should Planning stage be called `'concept'` or `'planning'`?

**Current State:**
- `data-stage="concept"` in header template
- `window.currentStage = 'planning'` in taxonomy template
- Mismatch causes substages not to display

**Recommendation:** Use `'concept'` to match existing `data-stage` attribute (less changes needed)

**Action:** Update all templates to use `window.currentStage = 'concept'` for Planning pages

---

### Decision 2: Calendar Button for Generated Posts
**Question:** Should generated posts show the Calendar button?

**Current State:**
- Calendar button is hidden for generated posts
- Week-view shows Calendar button
- User expects Calendar button to be visible

**Recommendation:** Show Calendar button for generated posts (user expectation)

**Action:** Remove conditional hiding of Calendar button for generated posts

---

## Testing Checklist

- [ ] Taxonomy page shows Calendar button for generated posts
- [ ] Taxonomy page shows Planning button for generated posts
- [ ] Taxonomy page shows Planning substages (Taxonomy, Product Data Review, Topic Brainstorming, etc.)
- [ ] Week-view page shows Calendar button
- [ ] Week-view page shows Planning button
- [ ] Week-view page shows Calendar substages when on Calendar stage
- [ ] Week-view page shows Planning substages when on Planning stage
- [ ] All substage links navigate to correct pages
- [ ] Active substage is highlighted correctly
- [ ] Post type badge displays correctly for all post types
- [ ] Title displays correctly for all post types

---

## Success Criteria

1. **Consistency:** All pages show the same navigation structure for the same post type
2. **Visibility:** All relevant buttons and substages are visible when appropriate
3. **Functionality:** All navigation links work correctly
4. **User Experience:** No confusion about where to navigate next

---

## Notes

- The header system is already unified (`blog_pipeline_header.html`), but the conditional logic and JavaScript need fixing
- This is primarily a template and JavaScript fix, not a major architectural change
- Estimated time: 2-4 hours for investigation + fixes + testing

---

## Related Documentation

- `docs/NAVBAR_AUDIT_REPORT.md` - **Comprehensive audit of all templates** (READ THIS FIRST)
- `docs/unified_architecture_overview.md` - Overall architecture
- `templates/shared/blog_pipeline_header.html` - Current header implementation
- `static/js/shared/blog-pipeline-header.js` - Current JavaScript logic

