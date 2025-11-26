# Post Type Substages Implementation

**Date:** 2025-01-15  
**Status:** Implementation Complete  
**Purpose:** Single source of truth for substage definitions across all post types

---

## Overview

This implementation creates a centralized configuration system for managing which substages appear for which post types. This ensures consistency across:

- Navbar navigation
- 1-click blog page
- Settings modal
- Pipeline status API
- Any other location that displays substages

---

## Architecture

### 1. Configuration File: `config/post_type_substages.py`

**Single source of truth** for all substage definitions.

**Key Components:**
- `SUBSTAGE_METADATA`: Metadata for each substage (label, route_function, order)
- `POST_TYPE_SUBSTAGES`: Mapping of post_type → stage → [substage_keys]
- Helper functions for querying and filtering

**Post Types Supported:**
- `themed` - Standard themed blog posts
- `profile` - Product profile posts
- `generated` - AI-generated posts
- `recipe` - Recipe posts

**Stages:**
- `calendar` - Calendar planning
- `planning` - Content planning
- `research` - Research and sourcing
- `authoring` - Content authoring
- `imaging` - Image generation and optimization
- `header` - Header and metadata

---

## API Endpoints

### `GET /api/post-types/<post_type>/substages?stage=<stage>`

Returns substage configuration for a post type.

**Response:**
```json
{
  "success": true,
  "post_type": "themed",
  "stage": "planning",
  "substages": [
    {
      "key": "ideas",
      "label": "Ideas",
      "route_function": "planning.planning_calendar_ideas",
      "order": 1
    },
    {
      "key": "taxonomy",
      "label": "Taxonomy",
      "route_function": "planning.planning_calendar_taxonomy",
      "order": 2
    },
    ...
  ]
}
```

### `GET /launchpad/one-click-blog/api/pipeline-status/<post_id>`

**Updated:** Now filters substages by post_type automatically.

**Response includes:**
- `post_type` field
- Only substages valid for the post's type
- Consistent ordering based on config

---

## Template Integration

### Jinja2 Helper Function

**Function:** `get_substages_for_navbar(post_type, stage)`

**Usage in templates:**
```jinja2
{% set planning_substages = get_substages_for_navbar(post_type or 'themed', 'planning') %}
{% for substage in planning_substages %}
    <a href="{{ url_for(substage.route_function, post_id=post_id) }}" 
       class="sub-stage-btn sub-stage-shared" 
       data-substage="{{ substage.key.replace('_', '-') }}">
        {{ substage.label }}
    </a>
{% endfor %}
```

**Registered in:** `unified_app.py` as Jinja2 global

---

## Navbar Updates

**File:** `templates/shared/blog_pipeline_header.html`

**Changes:**
- ✅ Replaced hardcoded substage lists with dynamic generation
- ✅ Added Topic Brainstorming to themed posts
- ✅ Consistent ordering across all post types
- ✅ Post-type-specific styling (generated, recipe) preserved

**Before:**
- Hardcoded lists for each post_type
- Missing Topic Brainstorming for themed posts
- Different orders in different sections

**After:**
- Single dynamic generation using config
- All substages from config included
- Consistent ordering everywhere

---

## 1-Click Blog Page

**File:** `templates/launchpad/one_click_blog_minimal.html`

**Status:** ✅ **Complete**

**Implementation:**
1. ✅ Detect post_type from API response (`pipeline-status` endpoint)
2. ✅ Filter table rows based on post_type using `filterSubstagesByPostType()`
3. ✅ Hide/show substages dynamically
4. ✅ Reorder rows to match config order
5. ✅ Update rowspan for stage cells based on visible rows

**How it works:**
- Fetches substage config from `/api/post-types/${postType}/substages`
- Maps config substage keys to HTML `data-substage` attributes
- Hides rows that don't belong to the post_type
- Reorders visible rows to match config order
- Updates stage cell rowspan to match visible substage count

---

## Settings Modal

**File:** `static/js/shared/post-type-settings.js`

**Status:** ✅ **Complete**

**Implementation:**
1. ✅ Fetch substage config from API endpoint (`/api/post-types/${postType}/substages`)
2. ✅ Build navigation tree dynamically from API response
3. ✅ Filter substages by post_type automatically
4. ✅ Ensure consistent ordering with config
5. ✅ Fallback to hardcoded structure if API fails

**How it works:**
- `buildNavigation()` is now async and fetches from API
- Builds navigation tree from API response with proper labels and icons
- Stores `navigationStructure` for use in navigation methods
- Falls back to hardcoded `NAVIGATION_STRUCTURE` if API fails
- Navigation methods updated to use API structure when available

---

## Pipeline Status API

**File:** `blueprints/automation_pipeline.py`

**Changes:**
- ✅ Fetches `post_type` from database
- ✅ Filters substages by post_type using config
- ✅ Returns only valid substages for post_type
- ✅ Includes `post_type` in response

**Before:**
- Returned all substages regardless of post_type
- No filtering

**After:**
- Filters by post_type automatically
- Only returns valid substages
- Consistent with navbar and config

---

## Substage Definitions

### Themed Posts

**Calendar:** view, week-view, ideas-week  
**Planning:** ideas, taxonomy, topic_brainstorming, section_structure, topic_allocation, section_titling  
**Research:** research, sources, visuals, prompts, verification  
**Authoring:** drafting, image_concepts, image_prompts, image_captions  
**Imaging:** image_generation, optimise  
**Header:** title_summary, header_image, seo_meta, product_match, final_review

### Profile Posts

**Planning:** taxonomy, section_structure, topic_allocation, section_titling  
**Authoring:** drafting, image_concepts, image_prompts, image_captions  
**Imaging:** image_generation, optimise  
**Header:** title_summary, header_image, seo_meta, final_review

### Generated Posts

**Calendar:** view, week-view, ideas-week  
**Planning:** taxonomy, product_data_review, section_content_mapping, section_titling  
**Authoring:** drafting, image_concepts, image_prompts, image_captions  
**Imaging:** image_generation, optimise  
**Header:** title_summary, header_image, seo_meta, final_review

### Recipe Posts

**Planning:** taxonomy, section_structure, topic_allocation, section_titling  
**Authoring:** drafting, recipe_image_style_prompt, image_captions  
**Imaging:** image_generation, optimise  
**Header:** title_summary, header_image, seo_meta, final_review

---

## Benefits

1. **Single Source of Truth** - All substage definitions in one place
2. **Consistency** - Same substages and order everywhere
3. **Maintainability** - Easy to add/remove substages
4. **Type Safety** - Python config ensures correctness
5. **Extensibility** - Easy to add new post types or substages

---

## Migration Notes

### Breaking Changes

None - this is a refactoring that maintains backward compatibility.

### Required Updates

1. **Navbar** - ✅ Complete
2. **1-Click Page** - ⚠️ Pending
3. **Settings Modal** - ⚠️ Pending
4. **Pipeline Status API** - ✅ Complete

---

## Testing

### Manual Testing Checklist

- [ ] Navbar shows correct substages for themed posts
- [ ] Navbar shows correct substages for profile posts
- [ ] Navbar shows correct substages for generated posts
- [ ] Navbar shows correct substages for recipe posts
- [ ] Topic Brainstorming appears in themed post navbar
- [ ] Order matches across navbar, 1-click, and API
- [ ] Pipeline status API filters by post_type correctly
- [ ] Settings modal shows correct substages
- [ ] 1-click page filters by post_type correctly
- [ ] 1-click page hides invalid substages for each post_type
- [ ] 1-click page reorders substages to match config

---

## Future Enhancements

1. **Database Storage** - Move config to database for admin UI editing
2. **Substage Dependencies** - Define prerequisites between substages
3. **Custom Ordering** - Allow per-post substage ordering
4. **Substage Metadata** - Add descriptions, icons, tooltips
5. **Validation** - Ensure route_functions exist before rendering

---

## Files Modified

1. `config/post_type_substages.py` - ✅ New file
2. `blueprints/automation_pipeline.py` - ✅ Updated
3. `utils/template_helpers.py` - ✅ Updated
4. `unified_app.py` - ✅ Updated
5. `templates/shared/blog_pipeline_header.html` - ✅ Updated
6. `templates/launchpad/one_click_blog_minimal.html` - ✅ Updated
7. `static/js/shared/post-type-settings.js` - ✅ Updated

---

## Related Documentation

- `docs/bugs/substage_post_type_management_audit.md` - Original audit
- `docs/workflow/substage_completion_tracking_implementation_plan.md` - Completion tracking

