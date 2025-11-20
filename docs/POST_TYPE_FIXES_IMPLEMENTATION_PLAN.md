# Post Type Fixes Implementation Plan

**Date:** 2025-01-XX  
**Purpose:** Address all issues identified in POST_TYPE_ISOLATION_AUDIT.md  
**Status:** Planning Phase

---

## Executive Summary

This plan addresses three critical areas:
1. **Missing `post_type` variables** in routes (from NAVBAR audit)
2. **Workflow substages visibility** - making shared vs type-specific substages clearly distinguished
3. **`illustration_method` deprecation** - migrate to `post_type`-based system

---

## Phase 1: Fix Missing `post_type` Variables

### Issue
Some routes don't pass `post_type` to templates, causing navigation to show incorrect substages.

### Routes Status

#### ✅ Already Fixed (Verified)
- `planning_concept_brainstorm()` - ✅ Has `post_type`
- `planning_concept_section_structure()` - ✅ Has `post_type`  
- `planning_concept_topic_allocation()` - ✅ Has `post_type`
- `planning_concept_titling()` - ✅ Has `post_type`
- `planning_calendar_view()` - ✅ Has `post_type`

**Note:** The NAVBAR audit appears to be outdated. Most routes already have `post_type`.

#### ⚠️ Routes to Verify (Quick Audit Needed)

**File:** `blueprints/planning_calendar.py`
- `planning_calendar_week_view()` - Verify `post_type` is passed

**File:** `blueprints/planning_calendar_clean.py`
- `planning_calendar()` - Verify `post_type` is passed

**Other planning routes:**
- All routes in `blueprints/planning_*.py` should be audited

### Implementation Steps

1. **Quick audit of remaining routes** - Verify all planning routes have `post_type`
2. **Create helper function** (optional, for consistency) to ensure `post_type` is always available:
   ```python
   def get_template_vars_with_post_type(post_id):
       """Get standard template variables including post_type"""
       from utils.taxonomy_helpers import get_post_type
       post_type = get_post_type(post_id)
       # ... get other vars ...
       return {
           'post_id': post_id,
           'post_type': post_type,
           # ... other vars ...
       }
   ```
3. **Update routes** to use helper function
4. **Test navigation** with all post types

### Files to Modify
- `blueprints/planning_calendar.py`
- `blueprints/planning_calendar_clean.py`
- Create: `utils/template_helpers.py` (helper function)

### Testing
- [ ] Test navigation with recipe posts
- [ ] Test navigation with profile posts
- [ ] Test navigation with themed posts
- [ ] Test navigation with generated posts

---

## Phase 2: Workflow Substages Visibility & Naming

### Issue
Workflow substages are shared across all post types, but there's no visual distinction between:
- **Shared substages** (used by all types)
- **Type-specific substages** (only for certain types)

### Current State
- Substages are hardcoded in `templates/shared/blog_pipeline_header.html`
- Some substages are conditionally shown based on `post_type`
- No naming convention to distinguish shared vs type-specific

### Solution: Naming Convention & Visual Indicators

#### 2.1 Naming Convention

**Shared Substages** (no prefix):
- `drafting` - Used by all types
- `image-captions` - Used by all types
- `optimise` - Used by all types
- `title-summary` - Used by all types
- `header-image` - Used by all types
- `seo-meta` - Used by all types
- `final-review` - Used by all types

**Type-Specific Substages** (with type prefix):
- `recipe-image-style-prompt` - Recipe only
- `profile-data-sync` - Profile only (when implemented)
- `profile-sections` - Profile only (when implemented)
- `generated-product-data-review` - Generated only
- `generated-section-content-mapping` - Generated only

#### 2.2 Visual Indicators in Navigation

Add CSS classes and icons to distinguish substage types:

```html
<!-- Shared substage -->
<a href="..." class="sub-stage-btn sub-stage-shared" data-substage="drafting">
    <i class="fas fa-circle" style="font-size: 0.5rem; color: #94a3b8;"></i>
    Drafting
</a>

<!-- Type-specific substage -->
<a href="..." class="sub-stage-btn sub-stage-recipe" data-substage="recipe-image-style-prompt">
    <i class="fas fa-utensils" style="font-size: 0.75rem;"></i>
    Image Style & Prompts
</a>
```

#### 2.3 CSS Styling

Add to `static/css/shared/blog-pipeline-header.css`:

```css
/* Shared substages - subtle styling */
.sub-stage-shared {
    opacity: 1;
}

.sub-stage-shared::before {
    content: '○';
    font-size: 0.5rem;
    color: #94a3b8;
    margin-right: 0.25rem;
    vertical-align: middle;
}

/* Type-specific substages - more prominent */
.sub-stage-recipe {
    border-left: 3px solid #fcd34d;
    padding-left: 0.5rem;
}

.sub-stage-profile {
    border-left: 3px solid #a5b4fc;
    padding-left: 0.5rem;
}

.sub-stage-generated {
    border-left: 3px solid #a78bfa;
    padding-left: 0.5rem;
}
```

### Implementation Steps

1. **Audit all substages** in `blog_pipeline_header.html`
2. **Categorize substages** as shared vs type-specific
3. **Add CSS classes** to substage buttons
4. **Add visual indicators** (icons, borders)
5. **Update documentation** with substage categorization

### Files to Modify
- `templates/shared/blog_pipeline_header.html`
- `static/css/shared/blog-pipeline-header.css`
- `docs/POST_TYPE_ISOLATION_AUDIT.md` (update with categorization)

### Testing
- [ ] Verify shared substages appear for all types
- [ ] Verify type-specific substages only appear for correct types
- [ ] Verify visual indicators are clear
- [ ] Test navigation with all post types

---

## Phase 3: Migrate from `illustration_method` to `post_type`

### Issue
The includes system uses `illustration_method` (currently unused, defaults to 'LLM-creation'), but should use `post_type` instead.

### Current State

**Files using `illustration_method`:**
1. `config/authoring_panel_configs.py` - Panel configs
2. `templates/shared/blog_pipeline_header.html` - Navigation (lines 95, 239)
3. `blueprints/header/routes.py` - Route handlers
4. `blueprints/header/api_prompt_compilation.py` - API endpoints
5. `utils/taxonomy_helpers.py` - Helper functions

**Current Behavior:**
- `illustration_method` defaults to 'LLM-creation' everywhere
- 'Photo-harvesting' is deprecated/unused
- All post types currently use 'LLM-creation'

### Solution: Two-Phase Migration

#### Phase 3.1: Update Config System

**Current:**
```python
ILLUSTRATION_PANEL_CONFIGS = {
    'LLM-creation': { ... },
    'Photo-harvesting': { ... }  # Deprecated
}
```

**New:**
```python
POST_TYPE_PANEL_CONFIGS = {
    'themed': {
        'panels': [
            {'include': 'authoring/includes/llm_settings_panel.html'},
            {'include': 'authoring/includes/llm_prompts_panel.html'},
            ...
        ],
        'output_panel': 'authoring/includes/output_panel_image_concepts.html'
    },
    'recipe': {
        'panels': [
            {'include': 'authoring/includes/llm_settings_panel.html'},
            {'include': 'authoring/includes/llm_prompts_panel.html'},
            ...
        ],
        'output_panel': 'authoring/includes/output_panel_image_concepts.html'
    },
    'profile': {
        'panels': [
            {'include': 'authoring/includes/llm_settings_panel.html'},
            {'include': 'authoring/includes/llm_prompts_panel.html'},
            # Future: profile-specific panels can be added here
            ...
        ],
        'output_panel': 'authoring/includes/output_panel_image_concepts.html'
    },
    'generated': {
        'panels': [
            {'include': 'authoring/includes/llm_settings_panel.html'},
            {'include': 'authoring/includes/llm_prompts_panel.html'},
            ...
        ],
        'output_panel': 'authoring/includes/output_panel_image_concepts.html'
    }
}
```

#### Phase 3.2: Update Helper Functions

**File:** `utils/taxonomy_helpers.py`

**Deprecate:**
```python
def get_illustration_method(post_id, default='LLM-creation'):
    # DEPRECATED: Use get_post_type() instead
    # This function now always returns 'LLM-creation' for backward compatibility
    return 'LLM-creation'
```

**Add:**
```python
def get_panel_config(post_id):
    """
    Get panel configuration for a post based on post_type.
    
    Replaces get_illustration_method() + get_panel_config(illustration_method)
    """
    post_type = get_post_type(post_id)
    from config.authoring_panel_configs import get_panel_config_by_post_type
    return get_panel_config_by_post_type(post_type)
```

#### Phase 3.3: Update Config Module

**File:** `config/authoring_panel_configs.py`

**Add:**
```python
# New post_type-based configs
POST_TYPE_PANEL_CONFIGS = {
    # ... as defined above ...
}

def get_panel_config_by_post_type(post_type):
    """
    Get panel configuration for a post type.
    
    Args:
        post_type (str): Post type ('themed', 'recipe', 'profile', 'generated')
    
    Returns:
        dict: Panel configuration
    """
    return POST_TYPE_PANEL_CONFIGS.get(
        post_type,
        POST_TYPE_PANEL_CONFIGS['themed']  # Default to themed
    )

# Keep old function for backward compatibility (deprecated)
def get_panel_config(illustration_method):
    """
    DEPRECATED: Use get_panel_config_by_post_type() instead.
    
    This function now always returns LLM-creation config for backward compatibility.
    """
    return ILLUSTRATION_PANEL_CONFIGS.get(
        'LLM-creation',
        ILLUSTRATION_PANEL_CONFIGS['LLM-creation']
    )
```

#### Phase 3.4: Update Templates

**File:** `templates/shared/blog_pipeline_header.html`

**Replace:**
```jinja2
{% if illustration_method|default('LLM-creation') == 'Photo-harvesting' %}
```

**With:**
```jinja2
{% if post_type is defined and post_type == 'photo-harvesting' %}
{# Note: photo-harvesting is deprecated, but kept for backward compatibility #}
```

**Or better:**
```jinja2
{# Always use LLM-creation imaging for now (photo-harvesting is deprecated) #}
```

#### Phase 3.5: Update Route Handlers

**File:** `blueprints/header/routes.py`

**Replace:**
```python
illustration_method = get_illustration_method(target_post_id)
```

**With:**
```python
from utils.taxonomy_helpers import get_post_type
post_type = get_post_type(target_post_id)
# illustration_method is deprecated, always use 'LLM-creation'
illustration_method = 'LLM-creation'  # For backward compatibility only
```

#### Phase 3.6: Update API Endpoints

**File:** `blueprints/header/api_prompt_compilation.py`

**Replace:**
```python
illustration_method = request.args.get('illustration_method', 'LLM-creation')
if illustration_method == 'Photo-harvesting':
    # ...
```

**With:**
```python
# Get post_type from post_id instead
post_id = request.args.get('post_id')
if post_id:
    from utils.taxonomy_helpers import get_post_type
    post_type = get_post_type(int(post_id))
else:
    post_type = 'themed'  # Default

# Photo-harvesting is deprecated, always use LLM-creation logic
# (Remove Photo-harvesting conditionals)
```

### Implementation Steps

1. **Create new config structure** (`POST_TYPE_PANEL_CONFIGS`)
2. **Update helper functions** to use `post_type`
3. **Update templates** to remove `illustration_method` references
4. **Update route handlers** to use `post_type`
5. **Update API endpoints** to use `post_type`
6. **Add deprecation warnings** to old functions
7. **Test all includes** work correctly
8. **Remove deprecated code** (in future phase)

### Files to Modify
- `config/authoring_panel_configs.py` - New config structure
- `utils/taxonomy_helpers.py` - Update helpers
- `templates/shared/blog_pipeline_header.html` - Remove `illustration_method`
- `blueprints/header/routes.py` - Use `post_type`
- `blueprints/header/api_prompt_compilation.py` - Use `post_type`
- `blueprints/header/api_photo_harvesting.py` - Mark as deprecated

### Testing
- [ ] Test authoring panels load correctly for all post types
- [ ] Test imaging navigation works for all types
- [ ] Test header generation works for all types
- [ ] Verify no `illustration_method` errors in logs
- [ ] Test backward compatibility (old code still works)

---

## Phase 4: Documentation Updates

### Files to Update

1. **`docs/POST_TYPE_ISOLATION_AUDIT.md`**
   - Mark issues as resolved
   - Add substage categorization
   - Document migration completion

2. **`docs/NAVBAR_COMPREHENSIVE_AUDIT.md`**
   - Mark routes as fixed
   - Update status

3. **`docs/DEVELOPMENT_RULES.md`** (if exists)
   - Add guidelines for substage naming
   - Document `post_type` usage

4. **Create:** `docs/POST_TYPE_SUBSTAGE_REFERENCE.md`
   - List all substages
   - Categorize as shared vs type-specific
   - Document visual indicators

---

## Implementation Timeline

### Week 1: Phase 1 & 2
- **Day 1-2:** Fix missing `post_type` variables
- **Day 3-4:** Implement substage visibility/naming
- **Day 5:** Testing & documentation

### Week 2: Phase 3
- **Day 1-2:** Update config system
- **Day 3-4:** Update templates & routes
- **Day 5:** Testing & cleanup

### Week 3: Phase 4 & Final Testing
- **Day 1-2:** Documentation updates
- **Day 3-4:** Comprehensive testing
- **Day 5:** Bug fixes & polish

---

## Risk Mitigation

### Backward Compatibility
- Keep old `illustration_method` functions with deprecation warnings
- Old code continues to work (returns 'LLM-creation')
- Gradual migration path

### Testing Strategy
- Test each phase independently
- Test all post types after each phase
- Verify no regressions

### Rollback Plan
- Each phase is independent
- Can rollback individual phases if needed
- Git commits per phase for easy rollback

---

## Success Criteria

### Phase 1 Complete When:
- [ ] All routes pass `post_type` variable
- [ ] Navigation shows correct substages for all types
- [ ] No missing `post_type` errors in logs

### Phase 2 Complete When:
- [ ] Shared substages are visually distinguished
- [ ] Type-specific substages are clearly marked
- [ ] Documentation lists all substages with categories

### Phase 3 Complete When:
- [ ] All `illustration_method` references removed/updated
- [ ] Config system uses `post_type`
- [ ] All includes work correctly
- [ ] No deprecation warnings in production

### Overall Complete When:
- [ ] All three phases complete
- [ ] Documentation updated
- [ ] All tests passing
- [ ] No regressions in existing functionality

---

## Next Steps

1. **Review this plan** with team
2. **Prioritize phases** (can be done in parallel if needed)
3. **Create GitHub issues** for each phase
4. **Begin Phase 1** implementation

---

**Plan Status:** Ready for Review  
**Estimated Effort:** 2-3 weeks  
**Priority:** High (blocks profile development)

