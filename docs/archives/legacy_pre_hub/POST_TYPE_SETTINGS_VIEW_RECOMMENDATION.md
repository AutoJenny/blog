# Post Type Settings View - Implementation Recommendation

**Date:** 2025-01-XX  
**Purpose:** Recommend how to create a Settings view for viewing and manually controlling post_type configurations, including Action button endpoints, navbar stages/substages, and template selections.

---

## Executive Summary

Post type management is currently distributed across multiple configuration files and hardcoded templates. A centralized Settings view would provide visibility and control over:
1. **Pipeline Steps** (from `config/post_type_pipeline_configs.py`)
2. **Action Button Endpoints** (from `static/js/llm-config.js`)
3. **Navbar Stages/Substages** (from `templates/shared/blog_pipeline_header.html`)
4. **Template Selection** (conditional logic in route functions)
5. **Panel Configurations** (from `config/authoring_panel_configs.py`)

**Recommendation:** Create a read-only Settings view first (Phase 1), then add editing capabilities with database-backed overrides (Phase 2).

---

## Current State Analysis

### 1. Pipeline Steps Configuration

**Location:** `config/post_type_pipeline_configs.py`

**Structure:**
```python
POST_TYPE_PIPELINE_CONFIGS = {
    'themed': {
        'active': True,
        'steps': ['week-ideas', 'taxonomy', 'idea-generation', ...]
    },
    'profile': {
        'active': True,
        'steps': ['profile-selection', 'profile-data-sync', ...]
    },
    ...
}
```

**Usage:**
- Used by launchpad/one-click pipeline
- Defines step order and labels
- Maps to JavaScript function names

**Current Control:** Python file (requires code changes)

---

### 2. Action Button Endpoints (Generate, etc.)

**Location:** `static/js/llm-config.js`

**Structure:**
```javascript
const LLM_CONFIGS = {
    'ideas': {
        promptEndpoint: '/planning/api/posts/{id}/expanded-idea-prompt',
        generateEndpoint: '/planning/api/posts/{id}/expanded-idea',
        resultsField: 'expanded_idea',
        ...
    },
    'author_draft': {
        promptEndpoint: '/authoring/api/llm/prompts/section-drafting',
        generateEndpoint: '/authoring/api/posts/{id}/sections/{section_id}/generate',
        ...
    },
    ...
}
```

**Usage:**
- Controls which API endpoints are called when "Generate" buttons are clicked
- Different endpoints for different page types (ideas, brainstorm, drafting, etc.)
- Some endpoints are post_type-specific (e.g., profile section structure)

**Current Control:** JavaScript file (requires code changes)

**Post Type Variations:**
- Profile posts use different endpoints (e.g., `/planning/api/profile/section-structure`)
- Recipe posts may use different endpoints
- Themed posts use generic endpoints

---

### 3. Navbar Stages/Substages Configuration

**Location:** `templates/shared/blog_pipeline_header.html`

**Structure:**
```jinja2
{% if post_type not in ['recipe', 'profile', 'generated'] %}
    <!-- Calendar sub-stages -->
    <div class="sub-stage-group" data-stage="calendar">
        <a href="..." class="sub-stage-btn" data-substage="view">Calendar View</a>
        ...
    </div>
    
    <!-- Planning sub-stages -->
    <div class="sub-stage-group" data-stage="concept">
        <a href="..." class="sub-stage-btn" data-substage="taxonomy">Taxonomy</a>
        ...
    </div>
{% elif post_type == 'profile' %}
    <!-- Planning sub-stages for profile posts -->
    <div class="sub-stage-group" data-stage="concept">
        <a href="..." class="sub-stage-btn" data-substage="taxonomy">Taxonomy</a>
        ...
    </div>
{% endif %}
```

**Usage:**
- Controls which stages/substages appear in navbar for each post type
- Hardcoded conditional logic in Jinja2 template
- Different substages for different post types

**Current Control:** Template file (requires code changes)

**Key Variations:**
- **Themed:** Calendar + Planning + Research + Authoring + Imaging + Header
- **Profile:** Planning only (no Calendar, no Research) + Authoring + Imaging + Header
- **Recipe:** Calendar + Planning (no Research) + Authoring + Imaging + Header
- **Generated:** Calendar + Planning (simplified) + Authoring + Imaging + Header

---

### 4. Template Selection Logic

**Location:** Route functions in various blueprints

**Pattern:**
```python
def planning_concept_section_structure(post_id):
    post_type = get_post_type(post_id)
    
    # Conditional template selection
    template_name = 'planning/concept/section_structure_profile.html' if post_type == 'profile' else 'planning/concept/section_structure.html'
    
    return render_template(template_name, ...)
```

**Usage:**
- Determines which template is rendered for each route
- Profile posts use `*_profile.html` templates
- Other post types use generic templates

**Current Control:** Route functions (requires code changes)

**Examples:**
- `section_structure.html` vs `section_structure_profile.html`
- `topic_allocation.html` vs `topic_allocation_profile.html`
- `titling.html` vs `titling_profile.html`

---

### 5. Panel Configurations

**Location:** `config/authoring_panel_configs.py`

**Structure:**
```python
POST_TYPE_PANEL_CONFIGS = {
    'themed': {
        'panels': [
            {'type': 'llm_settings', 'include': '...', 'order': 1},
            {'type': 'llm_prompts', 'include': '...', 'order': 2},
            ...
        ],
        'output_panel': 'authoring/includes/output_panel_image_concepts.html',
        'output_script': 'js/authoring/image-concepts-output-panel.js'
    },
    ...
}
```

**Usage:**
- Controls which panels appear in right-hand sidebar for authoring stages
- Defines panel order and output panel/script

**Current Control:** Python file (requires code changes)

---

## Recommended Implementation

### Phase 1: Read-Only Settings View

**Goal:** Display current configurations without editing capability

**Route:** `/settings/post-types`

**Features:**
1. **Post Type Overview Table**
   - List all post types (themed, recipe, profile, generated)
   - Show active status
   - Link to detailed view

2. **Post Type Detail View**
   - **Pipeline Steps:** Display steps in order with labels
   - **Action Buttons:** Show which endpoints are used for each action type
   - **Navbar Configuration:** Show which stages/substages appear
   - **Template Mapping:** Show which templates are used for each route
   - **Panel Configuration:** Show panel order and output settings

3. **Action Button Mapping**
   - For each post type, show:
     - Page type (e.g., 'ideas', 'brainstorm', 'author_draft')
     - Prompt endpoint
     - Generate endpoint
     - Results field
     - Whether it's post_type-specific

4. **Navbar Stage/Substage Tree**
   - Visual tree showing:
     - Main stages (Calendar, Planning, Research, Authoring, Imaging, Header)
     - Substages under each stage
     - Which post types see which substages

**Implementation:**
- Read from existing config files
- Parse JavaScript config file
- Parse Jinja2 template (or extract to separate config)
- Display in organized, readable format

---

### Phase 2: Editable Settings with Database Overrides

**Goal:** Allow manual control with database-backed overrides

**Database Schema:**
```sql
CREATE TABLE post_type_settings (
    id SERIAL PRIMARY KEY,
    post_type VARCHAR(50) NOT NULL,
    setting_category VARCHAR(50) NOT NULL,  -- 'pipeline_steps', 'action_endpoints', 'navbar_stages', 'templates', 'panels'
    setting_key VARCHAR(255) NOT NULL,     -- e.g., 'section_structure_template', 'ideas_generate_endpoint'
    setting_value JSONB NOT NULL,           -- Flexible JSON storage
    is_override BOOLEAN DEFAULT FALSE,      -- True if overriding default
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(post_type, setting_category, setting_key)
);

CREATE INDEX idx_post_type_settings_lookup ON post_type_settings(post_type, setting_category);
```

**Features:**
1. **Override System:**
   - Default values come from config files
   - Database overrides take precedence
   - Visual indicator when override is active

2. **Edit Interface:**
   - Inline editing for simple values
   - JSON editor for complex structures (pipeline steps, panel configs)
   - Validation before saving
   - Preview of changes

3. **Template Selection Override:**
   - Allow changing which template is used for a route
   - Validate template exists
   - Show preview of template path

4. **Endpoint Override:**
   - Allow changing API endpoints for action buttons
   - Validate endpoint exists (or at least format)
   - Show which routes use this endpoint

5. **Navbar Stage/Substage Override:**
   - Toggle visibility of stages/substages per post type
   - Reorder substages
   - Add/remove custom substages (advanced)

**Implementation:**
- Load defaults from config files
- Merge with database overrides
- Save overrides to database
- Update runtime behavior (may require cache invalidation)

---

## File Structure

```
blueprints/
├── settings.py                    # Existing (add post_type routes)
└── settings_api.py                 # NEW: API endpoints for settings CRUD

templates/settings/
├── index.html                      # Existing
├── taxonomy.html                   # Existing
└── post_types/                     # NEW
    ├── index.html                  # Post type overview
    ├── detail.html                 # Post type detail view
    └── edit.html                   # Edit interface

static/js/settings/
└── post-type-settings.js           # NEW: Frontend logic for settings view

static/css/settings/
└── post-type-settings.css          # NEW: Styles for settings view

config/
├── post_type_pipeline_configs.py   # Existing (defaults)
└── post_type_settings_loader.py    # NEW: Load settings with overrides
```

---

## API Endpoints

### Read-Only (Phase 1)
```
GET  /settings/post-types                    # List all post types
GET  /settings/post-types/<post_type>       # Get detailed config for post type
GET  /settings/post-types/<post_type>/pipeline-steps
GET  /settings/post-types/<post_type>/action-endpoints
GET  /settings/post-types/<post_type>/navbar-stages
GET  /settings/post-types/<post_type>/templates
GET  /settings/post-types/<post_type>/panels
```

### Editable (Phase 2)
```
GET    /api/settings/post-types/<post_type>/settings        # Get all settings (with overrides)
POST   /api/settings/post-types/<post_type>/settings       # Create override
PUT    /api/settings/post-types/<post_type>/settings/<key> # Update override
DELETE /api/settings/post-types/<post_type>/settings/<key> # Delete override (revert to default)
POST   /api/settings/post-types/<post_type>/reset          # Reset all overrides to defaults
```

---

## Configuration Loading Logic

**New Utility:** `config/post_type_settings_loader.py`

```python
def get_pipeline_steps(post_type, with_overrides=True):
    """Get pipeline steps, merging defaults with database overrides."""
    defaults = POST_TYPE_PIPELINE_CONFIGS.get(post_type, {})
    
    if not with_overrides:
        return defaults
    
    # Load overrides from database
    overrides = load_settings_overrides(post_type, 'pipeline_steps')
    
    # Merge (overrides take precedence)
    result = defaults.copy()
    if overrides:
        result.update(overrides)
    
    return result
```

**Usage in Routes:**
```python
from config.post_type_settings_loader import get_pipeline_steps

steps = get_pipeline_steps(post_type)  # Automatically includes overrides
```

---

## UI/UX Recommendations

### Overview Page
- **Table View:**
  - Post Type | Active | Pipeline Steps Count | Actions
  - Click row to view details
  - Quick actions: View Details, Edit (if Phase 2)

### Detail Page
- **Tabs:**
  1. **Pipeline Steps** - Ordered list with labels
  2. **Action Buttons** - Table of page types and endpoints
  3. **Navbar** - Visual tree of stages/substages
  4. **Templates** - Mapping of routes to templates
  5. **Panels** - Panel configuration for authoring

- **Visual Indicators:**
  - Green badge: "Using Default"
  - Orange badge: "Override Active"
  - Show source (config file vs database)

### Edit Page (Phase 2)
- **Form Sections:**
  - Each setting category in collapsible section
  - Inline editing with validation
  - JSON editor for complex structures
  - Preview button to see changes
  - Save/Cancel buttons

- **Validation:**
  - Template paths must exist
  - Endpoint paths must be valid format
  - Pipeline steps must have valid function mappings
  - Navbar stages must have valid route functions

---

## Implementation Checklist

### Phase 1: Read-Only View
- [ ] Create database schema (if needed for future)
- [ ] Create `config/post_type_settings_loader.py` utility
- [ ] Add routes to `blueprints/settings.py`
- [ ] Create `templates/settings/post_types/index.html`
- [ ] Create `templates/settings/post_types/detail.html`
- [ ] Parse `post_type_pipeline_configs.py` for display
- [ ] Parse `llm-config.js` for action endpoints
- [ ] Extract navbar config from template (or create separate config)
- [ ] Create frontend JavaScript for settings view
- [ ] Add CSS styling
- [ ] Test with all post types

### Phase 2: Editable Settings
- [ ] Create `post_type_settings` database table
- [ ] Create `blueprints/settings_api.py` for CRUD operations
- [ ] Update `config/post_type_settings_loader.py` to load overrides
- [ ] Create `templates/settings/post_types/edit.html`
- [ ] Add validation logic
- [ ] Add preview functionality
- [ ] Update route functions to use settings loader
- [ ] Add cache invalidation on settings update
- [ ] Test override system end-to-end

---

## Critical Considerations

### 1. Backward Compatibility
- **Default behavior:** Always fall back to config files if no overrides
- **Migration:** Existing configs remain unchanged
- **Rollback:** Can delete all overrides to revert to defaults

### 2. Validation
- **Template paths:** Must exist in filesystem
- **Endpoint paths:** Must match route patterns
- **Pipeline steps:** Must have corresponding function mappings
- **Navbar stages:** Must have valid route functions

### 3. Performance
- **Caching:** Cache loaded settings to avoid repeated database queries
- **Invalidation:** Clear cache when settings are updated
- **Lazy loading:** Only load settings when needed

### 4. Security
- **Access control:** Settings view should be admin-only
- **Validation:** Server-side validation of all inputs
- **Sanitization:** Sanitize all user inputs

### 5. Testing
- **Unit tests:** Test settings loader with/without overrides
- **Integration tests:** Test settings API endpoints
- **E2E tests:** Test full workflow with overrides

---

## Alternative Approaches

### Option A: Database-Only Configuration
- **Pros:** Single source of truth, easier to edit
- **Cons:** Migration required, loses version control benefits

### Option B: Config Files with UI Editor
- **Pros:** Version controlled, easier to review changes
- **Cons:** Requires file system write access, more complex

### Option C: Hybrid (Recommended)
- **Pros:** Best of both worlds - defaults in code, overrides in database
- **Cons:** More complex implementation

**Recommendation:** Option C (Hybrid) - Keep defaults in config files for version control, allow database overrides for runtime customization.

---

## Next Steps

1. **Review this recommendation** with team
2. **Approve approach** before implementation
3. **Implement Phase 1** (read-only view) first
4. **Gather feedback** on what settings need to be editable
5. **Implement Phase 2** (editable settings) based on feedback

---

## References

- **Pipeline Config:** `config/post_type_pipeline_configs.py`
- **Panel Config:** `config/authoring_panel_configs.py`
- **LLM Config:** `static/js/llm-config.js`
- **Navbar Template:** `templates/shared/blog_pipeline_header.html`
- **Settings Blueprint:** `blueprints/settings.py`
- **Post Type Helper:** `utils/taxonomy_helpers.py::get_post_type()`

