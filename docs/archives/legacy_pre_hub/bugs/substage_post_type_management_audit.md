# Substage Post Type Management Audit

**Date:** 2025-01-15  
**Status:** Audit Complete - Recommendations Provided  
**Issue:** Extensive confusion over which substages appear for which post_types, with differences between the 1-click list, navbar, and settings modal.

---

## Executive Summary

**Problem:** There is **no single source of truth** for which substages belong to which post types. Each location (navbar, 1-click page, settings modal, API) has its own hardcoded logic, leading to:

1. **Inconsistencies** - Different substages shown in different places
2. **Maintenance burden** - Fixes to one post_type break another
3. **Missing substages** - Topic brainstorming disappeared from themed post navbar
4. **Order differences** - Substages appear in different orders across locations
5. **No differentiation** - 1-click page shows all substages regardless of post_type

---

## Current State Analysis

### 1. Navbar (`templates/shared/blog_pipeline_header.html`)

**Location:** Lines 172-286

**How it works:**
- Uses Jinja2 conditionals: `{% if post_type not in ['recipe', 'profile', 'generated'] %}`
- Hardcoded substage lists for each post_type
- **Themed posts** (default): Shows Calendar, Planning, Research stages
- **Profile posts**: Shows Planning only (no Calendar, no Research)
- **Generated posts**: Shows Calendar and Planning (no Research)
- **Recipe posts**: Not explicitly handled in Planning substages

**Planning Substages for Themed Posts:**
```jinja2
<!-- Lines 195-214 -->
Ideas → Taxonomy → Section Structure Design → Section Ideas → Section Titling
```

**Issues Found:**
1. ❌ **Topic Brainstorming is MISSING** from themed post navbar (but exists in 1-click page)
2. ❌ Order differs from 1-click page (Ideas before Taxonomy vs Taxonomy before Ideas)
3. ❌ No conditional logic for recipe posts in Planning substages
4. ❌ Hardcoded in template - requires template edit to change

**Planning Substages for Profile Posts:**
```jinja2
<!-- Lines 243-258 -->
Taxonomy → Section Structure Design → Section Ideas → Section Titling
```

**Planning Substages for Generated Posts:**
```jinja2
<!-- Lines 264-284 -->
Taxonomy → Product Data Review → Section Content Mapping → Section Titling
```

---

### 2. One-Click Blog Page (`templates/launchpad/one_click_blog_minimal.html`)

**Location:** Lines 78-280 (hardcoded HTML table)

**How it works:**
- **Hardcoded HTML table** with all substages
- **NO post_type filtering** - shows same substages for all post types
- Substages are always visible regardless of post_type

**Planning Substages Shown:**
```html
<!-- Lines 109-167 -->
Taxonomy → Idea Generation → Topic Brainstorming → Section Structure Design → Section Ideas → Section Titling
```

**Issues Found:**
1. ❌ **No post_type differentiation** - shows all substages for all post types
2. ❌ Includes "Topic Brainstorming" (missing from navbar for themed posts)
3. ❌ Order: Taxonomy → Idea Generation (navbar has Ideas → Taxonomy)
4. ❌ Hardcoded in HTML - requires template edit to change
5. ❌ Doesn't show post_type-specific substages (e.g., Product Data Review for generated)

**Substages Found in Template:**
- `calendar-view`, `week-ideas`
- `taxonomy`, `idea-generation`, `topic-brainstorming`, `section-structure-design`, `section-ideas`, `section-titling`
- `drafting`, `image-concepts`, `image-prompts`, `image-captions`
- `image-generation`, `optimise`
- `title-summary`, `header-image-generate`, `seo-meta`, `final-review`

---

### 3. Settings Modal (`static/js/shared/post-type-settings.js`)

**Location:** Lines 9-196 (SUBSTAGE_CONFIG_MAP), Lines 199-230 (NAVIGATION_STRUCTURE)

**How it works:**
- JavaScript object `SUBSTAGE_CONFIG_MAP` defines substage configurations
- `NAVIGATION_STRUCTURE` defines which substages belong to which stages
- **NO post_type filtering** - shows all substages for all post types

**Navigation Structure:**
```javascript
// Lines 199-230
'concept': {
    label: 'Planning',
    icon: 'fa-lightbulb',
    substages: ['taxonomy', 'section-structure', 'topic-allocation', 'titling']
}
```

**Issues Found:**
1. ❌ **No post_type differentiation** - same substages for all post types
2. ❌ Missing "Ideas" and "Topic Brainstorming" from Planning substages
3. ❌ Doesn't include post_type-specific substages (Product Data Review, etc.)
4. ❌ Hardcoded in JavaScript - requires code edit to change

---

### 4. Pipeline Status API (`blueprints/automation_pipeline.py`)

**Location:** Lines 126-367

**How it works:**
- Returns completion status for **all substages** regardless of post_type
- Hardcoded substage completion logic
- **NO post_type filtering** - returns all substages for all post types

**Substages Returned:**
```python
# Planning substages (lines 129-138)
- ideas (expanded_idea)
- taxonomy (theme_id, content_type_id, format_id)
- topic_brainstorming (idea_scope)
- section_structure (section_structure)
- topic_allocation (topic_allocation)
- section_titling (sections)
```

**Issues Found:**
1. ❌ **No post_type filtering** - returns all substages for all post types
2. ❌ Doesn't check if substage is valid for post_type before returning
3. ❌ Hardcoded completion logic - requires code edit to change

---

### 5. Template Mappings (`config/template_mappings.py`)

**Location:** Lines 9-111

**How it works:**
- Maps substages to template paths by post_type
- **Does NOT define which substages exist for which post types**
- Only provides template path resolution

**Issues Found:**
1. ❌ **Does not define substage existence** - only template paths
2. ❌ Cannot be used to determine which substages to show
3. ❌ Missing many substages (e.g., topic-brainstorming, ideas)

---

## Comparison Table

| Substage | Navbar (Themed) | 1-Click Page | Settings Modal | API | Template Mappings |
|----------|----------------|--------------|----------------|-----|-------------------|
| **Calendar View** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Week Ideas** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Ideas** | ✅ | ✅ (as "Idea Generation") | ❌ | ✅ | ❌ |
| **Taxonomy** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Topic Brainstorming** | ❌ **MISSING** | ✅ | ❌ | ✅ | ❌ |
| **Section Structure** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Section Ideas** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Section Titling** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Product Data Review** | ✅ (Generated only) | ❌ | ❌ | ❌ | ✅ |
| **Section Content Mapping** | ✅ (Generated only) | ❌ | ❌ | ❌ | ✅ |
| **Research** | ✅ (Themed only) | ❌ | ✅ | ❌ | ✅ |

**Key Findings:**
- ❌ **Topic Brainstorming** missing from navbar for themed posts
- ❌ **1-click page** shows all substages regardless of post_type
- ❌ **Settings modal** missing Ideas and Topic Brainstorming
- ❌ **API** returns all substages regardless of post_type
- ❌ **No consistency** in substage ordering

---

## Order Comparison

### Navbar (Themed Posts)
1. Ideas
2. Taxonomy
3. Section Structure Design
4. Section Ideas
5. Section Titling

### 1-Click Page
1. Taxonomy
2. Idea Generation
3. Topic Brainstorming
4. Section Structure Design
5. Section Ideas
6. Section Titling

### Settings Modal
1. Taxonomy
2. Section Structure
3. Topic Allocation
4. Titling

**Result:** Three different orders, none matching!

---

## Root Causes

### 1. No Single Source of Truth
- Each location maintains its own list
- Changes require updates in multiple places
- Easy to miss updates, causing inconsistencies

### 2. Hardcoded Logic
- Navbar: Jinja2 conditionals in template
- 1-click: Hardcoded HTML table
- Settings: Hardcoded JavaScript objects
- API: Hardcoded Python logic

### 3. No Post Type Awareness
- 1-click page doesn't filter by post_type
- API doesn't filter by post_type
- Settings modal doesn't filter by post_type

### 4. Missing Abstraction Layer
- No configuration file or database table
- No function to "get substages for post_type"
- No validation that substage exists for post_type

---

## Recommendations

### Option 1: Python Configuration File (Recommended)

**Create:** `config/post_type_substages.py`

**Structure:**
```python
POST_TYPE_SUBSTAGES = {
    'themed': {
        'calendar': ['view', 'week-view', 'ideas-week'],
        'planning': ['ideas', 'taxonomy', 'topic_brainstorming', 'section_structure', 'topic_allocation', 'section_titling'],
        'research': ['research', 'sources', 'visuals', 'prompts', 'verification'],
        'authoring': ['drafting', 'image_concepts', 'image_prompts', 'image_captions'],
        'imaging': ['image_generation', 'optimise'],
        'header': ['title_summary', 'header_image', 'seo_meta', 'product_match', 'final_review']
    },
    'profile': {
        'planning': ['taxonomy', 'section_structure', 'topic_allocation', 'section_titling'],
        'authoring': ['drafting', 'image_concepts', 'image_prompts', 'image_captions'],
        'imaging': ['image_generation', 'optimise'],
        'header': ['title_summary', 'header_image', 'seo_meta', 'final_review']
    },
    'generated': {
        'calendar': ['view', 'week-view', 'ideas-week'],
        'planning': ['taxonomy', 'product_data_review', 'section_content_mapping', 'section_titling'],
        'authoring': ['drafting', 'image_concepts', 'image_prompts', 'image_captions'],
        'imaging': ['image_generation', 'optimise'],
        'header': ['title_summary', 'header_image', 'seo_meta', 'final_review']
    },
    'recipe': {
        'planning': ['taxonomy', 'section_structure', 'topic_allocation', 'section_titling'],
        'authoring': ['drafting', 'recipe_image_style_prompt', 'image_captions'],
        'imaging': ['image_generation', 'optimise'],
        'header': ['title_summary', 'header_image', 'seo_meta', 'final_review']
    }
}

def get_substages_for_post_type(post_type, stage=None):
    """Get substages for a post type, optionally filtered by stage"""
    if post_type not in POST_TYPE_SUBSTAGES:
        post_type = 'themed'  # Default fallback
    
    substages = POST_TYPE_SUBSTAGES[post_type]
    
    if stage:
        return substages.get(stage, [])
    
    return substages
```

**Benefits:**
- ✅ Single source of truth
- ✅ Easy to maintain
- ✅ Type-safe (Python)
- ✅ Can be imported by all locations
- ✅ Can be extended with metadata (labels, order, etc.)

**Usage:**
- Navbar: `{% for substage in get_substages_for_post_type(post_type, 'planning') %}`
- 1-click: Filter table rows based on post_type
- Settings: Import and use in JavaScript (via API)
- API: Filter response based on post_type

---

### Option 2: Database Table

**Create:** `post_type_substages` table

**Schema:**
```sql
CREATE TABLE post_type_substages (
    id SERIAL PRIMARY KEY,
    post_type VARCHAR(50) NOT NULL,
    stage VARCHAR(50) NOT NULL,
    substage_key VARCHAR(100) NOT NULL,
    display_order INTEGER NOT NULL,
    display_label VARCHAR(200),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(post_type, stage, substage_key)
);
```

**Benefits:**
- ✅ Can be edited via admin UI
- ✅ No code deployment needed for changes
- ✅ Can track history/audit trail
- ✅ Can be queried dynamically

**Drawbacks:**
- ❌ Requires database migration
- ❌ More complex to query
- ❌ Slower than in-memory config
- ❌ Requires admin UI to manage

---

### Option 3: API Endpoint

**Create:** `GET /api/post-types/<post_type>/substages`

**Response:**
```json
{
  "success": true,
  "post_type": "themed",
  "stages": {
    "calendar": {
      "substages": [
        {"key": "view", "label": "Calendar View", "order": 1},
        {"key": "week-view", "label": "Week View", "order": 2},
        {"key": "ideas-week", "label": "Week Themes", "order": 3}
      ]
    },
    "planning": {
      "substages": [
        {"key": "ideas", "label": "Ideas", "order": 1},
        {"key": "taxonomy", "label": "Taxonomy", "order": 2},
        {"key": "topic_brainstorming", "label": "Topic Brainstorming", "order": 3},
        ...
      ]
    }
  }
}
```

**Benefits:**
- ✅ Single source of truth (backend)
- ✅ Can be cached
- ✅ Frontend can fetch dynamically
- ✅ Can include metadata (labels, routes, etc.)

**Drawbacks:**
- ❌ Requires API call (latency)
- ❌ Still needs backend config (Option 1 or 2)
- ❌ More complex than direct import

---

## Recommended Implementation Plan

### Phase 1: Create Configuration File (Option 1)

1. **Create** `config/post_type_substages.py` with complete substage definitions
2. **Add helper functions:**
   - `get_substages_for_post_type(post_type, stage=None)`
   - `get_substage_label(substage_key)`
   - `get_substage_order(post_type, stage, substage_key)`
   - `is_substage_valid_for_post_type(post_type, stage, substage_key)`

### Phase 2: Update Navbar

1. **Create** Jinja2 helper function to get substages
2. **Replace** hardcoded lists with dynamic generation
3. **Add** Topic Brainstorming back to themed posts
4. **Ensure** consistent ordering

### Phase 3: Update 1-Click Page

1. **Add** post_type detection (from URL parameter or API)
2. **Filter** table rows based on post_type
3. **Hide/show** substages dynamically
4. **Ensure** consistent ordering with navbar

### Phase 4: Update Settings Modal

1. **Create** API endpoint to fetch substages (or import from config)
2. **Update** NAVIGATION_STRUCTURE to be dynamic
3. **Filter** substages by post_type
4. **Ensure** consistent ordering

### Phase 5: Update API

1. **Filter** pipeline status response by post_type
2. **Only return** substages valid for post_type
3. **Add** validation to prevent invalid substages

### Phase 6: Integration & Testing

1. **Test** all post types (themed, profile, generated, recipe)
2. **Verify** consistency across all locations
3. **Verify** ordering matches everywhere
4. **Document** in `/docs`

---

## Immediate Fixes Needed

### 1. Add Topic Brainstorming to Navbar (Themed Posts)

**File:** `templates/shared/blog_pipeline_header.html`  
**Location:** Lines 193-215

**Add after Taxonomy:**
```jinja2
<a href="{{ url_for('planning.planning_concept_brainstorm', post_id=post_id) }}" 
   class="sub-stage-btn sub-stage-shared" data-substage="topic-brainstorming">
    Topic Brainstorming
</a>
```

### 2. Add Post Type Filtering to 1-Click Page

**File:** `templates/launchpad/one_click_blog_minimal.html`  
**Location:** Lines 78-280

**Add JavaScript to:**
- Detect post_type from API response
- Hide/show table rows based on post_type
- Reorder substages to match navbar

### 3. Standardize Order

**Recommended Order (Planning Stage for Themed Posts):**
1. Ideas
2. Taxonomy
3. Topic Brainstorming
4. Section Structure Design
5. Section Ideas
6. Section Titling

**Apply this order to:**
- Navbar
- 1-click page
- Settings modal
- API response

---

## Conclusion

The current system has **no single source of truth** for substage definitions, leading to inconsistencies, maintenance burden, and bugs. The recommended solution is to:

1. **Create** `config/post_type_substages.py` as the single source of truth
2. **Update** all locations to use this configuration
3. **Add** post_type filtering everywhere
4. **Standardize** ordering across all locations

This will ensure consistency, reduce maintenance burden, and prevent future bugs.


