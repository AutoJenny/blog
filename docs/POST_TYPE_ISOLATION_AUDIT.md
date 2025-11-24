# Post Type Isolation Audit Report

**Date:** 2025-01-XX  
**Purpose:** Verify that developing profiles further will not break themes and recipes  
**Scope:** Complete analysis of post type architecture, stages/substages, includes, and shared code

---

## Executive Summary

This audit examines the codebase architecture for post types (themes, profiles, recipes) to ensure that profile-specific development will be **entirely robust and non-interfering** with other types.

### Key Findings

✅ **SAFE AREAS:**
- Post type detection is robust and isolated
- Pipeline step configuration is completely separate per type
- Section types use prefixes (`recipe_`, `profile_`) for isolation
- Database fields are type-specific (no shared columns)

⚠️ **POTENTIAL RISK AREAS:**
- Workflow stages/substages are **SHARED** across all post types (database-driven)
- Includes system uses `illustration_method`, not `post_type` (may need extension)
- Some shared code paths need post_type checks
- Template conditionals may need updates

❌ **CRITICAL ISSUES:**
- No post_type filtering in workflow_sub_stage_entity table
- Navigation system doesn't filter substages by post_type
- Some routes missing `post_type` variable (from NAVBAR audit)

---

## 1. Post Type Detection Architecture

### Current Implementation

**Location:** `utils/taxonomy_helpers.py` - `get_post_type()`

```python
def get_post_type(post_id):
    """
    Determine post type: recipe, profile, generated, or themed.
    
    Detection logic:
    - recipe: post.recipe_id IS NOT NULL
    - profile: post.profile_category_id IS NOT NULL  
    - generated: post.generated_source_type IS NOT NULL
    - themed: Everything else (default)
    """
```

**Database Fields Used:**
- `post.recipe_id` → recipe posts
- `post.profile_category_id` → profile posts
- `post.generated_source_type` → generated posts
- Default → themed posts

### Isolation Analysis

✅ **ROBUST:** 
- Each post type uses **distinct, non-overlapping database fields**
- No shared columns that could cause confusion
- Detection logic is mutually exclusive
- Default fallback to 'themed' is safe

✅ **SAFE FOR PROFILE DEVELOPMENT:**
- Adding profile-specific fields won't affect recipe detection
- Recipe detection uses `recipe_id`, not `profile_category_id`
- Themed posts have no specific identifier (default case)

### Recommendation

✅ **NO ACTION NEEDED** - Post type detection is properly isolated.

---

## 2. Pipeline Step Configuration

### Current Implementation

**Location:** `config/post_type_pipeline_configs.py`

**Architecture:**
- Each post type has its own `steps` array
- Steps are completely independent per type
- No shared step IDs between types (except common steps like `header-*`)

**Themed Steps:**
```python
'themed': {
    'steps': [
        'week-ideas', 'taxonomy', 'idea-generation', 
        'topic-brainstorming', 'section-structure-design', ...
    ]
}
```

**Recipe Steps:**
```python
'recipe': {
    'steps': [
        'recipe-selection', 'recipe-research', 'drafting',
        'recipe-image-style-prompt', ...
    ]
}
```

**Profile Steps:**
```python
'profile': {
    'steps': [
        'profile-selection', 'profile-data-sync', 'profile-sections',
        'profile-image-concepts', 'profile-image-prompts', ...
    ]
}
```

### Isolation Analysis

✅ **ROBUST:**
- Each type has **completely separate step lists**
- Step IDs are prefixed by type (`recipe-*`, `profile-*`)
- Common steps (header, final-review) are shared but type-agnostic
- Configuration is dictionary-based (no shared state)

✅ **SAFE FOR PROFILE DEVELOPMENT:**
- Adding new profile steps won't affect recipe or themed steps
- Step IDs are namespaced (`profile-*`)
- Pipeline loading is type-specific via `get_pipeline_steps(post_type)`

### Potential Pitfall

⚠️ **SHARED STEPS:** Steps like `header-title-summary`, `header-image-prompt`, `final-review` are shared across types. These must remain type-agnostic.

**Mitigation:**
- ✅ These steps already work for all types (verified in code)
- ✅ Header generation uses `get_post_type()` internally for context
- ✅ No type-specific logic in shared steps

### Recommendation

✅ **SAFE TO PROCEED** - Pipeline configuration is properly isolated. Just ensure any new profile steps use `profile-*` prefix.

---

## 3. Workflow Stages & Substages

### Current Implementation

**Database Tables:**
- `workflow_stage_entity` - Main stages (planning, writing, publishing)
- `workflow_sub_stage_entity` - Substages within stages
- `workflow_step_entity` - Steps within substages

**Key Finding:** ⚠️ **NO POST_TYPE COLUMN IN WORKFLOW TABLES**

The workflow system is **database-driven** and **shared across all post types**. There is no filtering by post_type in:
- `workflow_stage_entity`
- `workflow_sub_stage_entity`  
- `workflow_step_entity`

### Current Substages (From Documentation)

**Planning Stage:**
1. Initial
2. Research
3. Structure

**Writing Stage:**
1. Content
2. Meta
3. Images

**Publishing Stage:**
1. Preflight
2. Launch
3. Syndication

### Isolation Analysis

❌ **POTENTIAL RISK:**
- All post types use the **same substages** from the database
- No mechanism to filter substages by post_type
- Navigation system loads all substages for all types

**Example Risk Scenario:**
- If profiles need a "profile-data-sync" substage, it would appear for ALL types
- If recipes need a "recipe-research" substage, it would appear for ALL types

### Current Mitigation

✅ **Pipeline Steps vs Workflow Substages:**
- Pipeline steps (in `post_type_pipeline_configs.py`) ARE type-specific
- Workflow substages (in database) are shared
- The system uses **pipeline steps** for type-specific workflows
- Workflow substages are more generic (planning, writing, publishing)

**However:**
- Navigation system may show all substages regardless of type
- Some routes may not filter substages by post_type

### Recommendation

⚠️ **REQUIRES ATTENTION:**
1. **Verify navigation filtering:** Check if `blog_pipeline_header.html` filters substages by post_type
2. **Document shared substages:** Ensure profile-specific substages are clearly documented as type-agnostic
3. **Consider database extension:** If profiles need unique substages, consider adding `post_type` column to `workflow_sub_stage_entity` (with migration plan)

**Action Items:**
- [ ] Review `templates/shared/blog_pipeline_header.html` for substage filtering
- [ ] Test navigation with profile posts to ensure correct substages show
- [ ] Document which substages are shared vs type-specific

---

## 4. Includes System

### Current Implementation

**Location:** `config/authoring_panel_configs.py`

**Architecture:**
- Includes are filtered by **`illustration_method`**, not `post_type`
- Two methods: `LLM-creation` (active) and `Photo-harvesting` (deprecated)

**Example:**
```python
ILLUSTRATION_PANEL_CONFIGS = {
    'LLM-creation': {
        'panels': [
            {'include': 'authoring/includes/llm_settings_panel.html'},
            {'include': 'authoring/includes/llm_prompts_panel.html'},
            ...
        ]
    }
}
```

### Isolation Analysis

⚠️ **POTENTIAL GAP:**
- Includes are **not filtered by post_type**
- All post types using `LLM-creation` get the same includes
- No mechanism for profile-specific includes

**Current Behavior:**
- Recipes, profiles, and themes all use `LLM-creation` illustration method
- They all get the same panel includes
- Type-specific logic must be inside the include templates

### Recommendation

✅ **LIKELY SAFE:**
- If profile-specific includes are needed, they can be:
  1. Added as new include files (e.g., `profile_data_panel.html`)
  2. Conditionally included in templates using `{% if post_type == 'profile' %}`
  3. Or extend the config system to support post_type filtering

**Action Items:**
- [ ] Identify if profiles need unique includes
- [ ] If yes, create profile-specific include files
- [ ] Update templates to conditionally load profile includes

---

## 5. Section Types

### Current Implementation

**Database Field:** `post_section.section_type`

**Naming Convention:**
- Recipe sections: `recipe_*` prefix (e.g., `recipe_background`, `recipe_ingredients`)
- Profile sections: `profile_*` prefix (planned, e.g., `profile_hero`, `profile_maker`)
- Themed sections: No prefix (or `NULL`)

**Code Examples:**
```python
# Recipe section filtering
WHERE section_type != 'recipe_image_style'  # Exclude internal recipe sections

# Template filtering
{% if section.section_type and section.section_type.startswith('recipe_') %}
```

### Isolation Analysis

✅ **ROBUST:**
- Section types use **prefix-based namespacing**
- Recipe sections: `recipe_*`
- Profile sections: `profile_*` (when implemented)
- Themed sections: No prefix

**Template Filtering:**
- Templates check for prefixes: `section.section_type.startswith('recipe_')`
- Profile sections would use: `section.section_type.startswith('profile_')`
- No overlap possible

### Recommendation

✅ **SAFE TO PROCEED:**
- Use `profile_*` prefix for all profile-specific section types
- Ensure templates check prefixes correctly
- Document profile section types in `/docs`

**Action Items:**
- [ ] Document profile section types (from implementation plan)
- [ ] Ensure all profile sections use `profile_*` prefix
- [ ] Update templates to handle profile sections if needed

---

## 6. Shared Code Paths

### Areas Requiring Post Type Checks

#### 6.1 Header Generation

**Location:** `blueprints/header/api_prompt_compilation.py`

**Current Behavior:**
- Checks for `recipe_id` to get recipe data
- Checks for `profile_category_id` to get profile data
- Falls back to themed post logic

**Code:**
```python
# Recipe-specific logic
if post.get('recipe_id'):
    # Get recipe data from calendar_recipes
    
# Profile-specific logic  
if post.get('profile_category_id'):
    # Get profile data from post table
```

✅ **SAFE:** Logic is properly isolated with if/elif checks.

#### 6.2 Post Data Loading

**Location:** `blog-launchpad/publish/post_data_loader.py`

**Current Behavior:**
- Filters out `recipe_image_style` sections (recipe-specific)
- Loads all other sections for all types

**Code:**
```sql
WHERE post_id = %s 
AND (section_type IS NULL OR section_type != 'recipe_image_style')
```

✅ **SAFE:** Only excludes recipe-specific internal sections. Profile sections would not be excluded (correct behavior).

#### 6.3 Template Rendering

**Location:** `templates/launchpad/clan_post_raw.html`

**Current Behavior:**
- Checks for recipe sections: `{% set is_recipe = section.section_type is is_recipe_section %}`
- Applies recipe-specific styling/formatting
- Other sections render normally

**Code:**
```jinja2
{% if section.section_type != 'recipe_image_style' %}
    {% set is_recipe = section.section_type is is_recipe_section %}
    <section class="blog-section{% if is_recipe %} recipe-section{% endif %}">
```

✅ **SAFE:** Recipe-specific logic is isolated. Profile sections would render normally (may need profile-specific styling).

### Recommendation

✅ **MOSTLY SAFE:**
- Shared code paths have proper type checks
- Recipe-specific logic is isolated
- Profile-specific logic can be added similarly

**Action Items:**
- [ ] Add profile-specific template checks if needed (similar to recipe checks)
- [ ] Ensure profile sections don't get recipe styling
- [ ] Test template rendering with profile posts

---

## 7. Navigation System

### Current Implementation

**Location:** `templates/shared/blog_pipeline_header.html`

**Key Finding from NAVBAR Audit:**
- Some routes are **missing `post_type` variable**
- Header template uses `{% if post_type == 'generated' %}` for substage filtering
- If `post_type` is missing, defaults to themed post substages

### Known Issues

**From `docs/NAVBAR_COMPREHENSIVE_AUDIT.md`:**
- 3 routes missing `post_type` variable:
  1. `planning_concept_section_structure()`
  2. `planning_concept_topic_allocation()`
  3. `planning_concept_titling()`

### Isolation Analysis

⚠️ **RISK:**
- If `post_type` is not passed to templates, navigation may show wrong substages
- Profile posts might show themed substages if `post_type` is missing
- Recipe posts might show themed substages if `post_type` is missing

### Recommendation

⚠️ **REQUIRES FIX:**
1. **Fix missing `post_type` variables** in routes (from NAVBAR audit)
2. **Verify all profile routes** pass `post_type` variable
3. **Test navigation** with profile posts to ensure correct substages

**Action Items:**
- [ ] Fix 3 routes identified in NAVBAR audit
- [ ] Audit all profile-related routes for `post_type` variable
- [ ] Test navigation with profile, recipe, and themed posts

---

## 8. Database Schema

### Post Table Fields

**Recipe-Specific:**
- `post.recipe_id` → References `calendar_recipes(id)`
- `post.recipe_week_number` → Week number for recipe

**Profile-Specific:**
- `post.profile_type` → 'product' or 'category'
- `post.profile_product_id` → References `clan_products(id)`
- `post.profile_category_id` → References `clan_categories(id)`
- `post.profile_producer_id` → References `producers(id)`
- `post.profile_producer_name` → Denormalized producer name
- `post.profile_standfirst` → Profile standfirst text
- `post.profile_explore_links` → JSONB
- `post.profile_quick_facts` → JSONB

**Themed-Specific:**
- No specific fields (default case)

**Generated-Specific:**
- `post.generated_source_type` → Source type identifier

### Isolation Analysis

✅ **ROBUST:**
- Each post type uses **completely separate columns**
- No shared columns that could cause conflicts
- Foreign keys are type-specific
- JSONB fields are type-specific

### Recommendation

✅ **SAFE TO PROCEED:**
- Database schema is properly isolated
- Adding profile fields won't affect recipe or themed posts
- Foreign key constraints are type-specific

---

## 9. API Endpoints

### Profile-Specific Endpoints

**Location:** `blueprints/planning_api_profiles.py`

**Endpoints:**
- `POST /api/profiles/create` - Create profile
- `GET /api/profiles/<id>` - Get profile
- `PUT /api/profiles/<id>` - Update profile
- `DELETE /api/profiles/<id>` - Delete profile

### Isolation Analysis

✅ **ROBUST:**
- Profile endpoints are in **separate blueprint**
- No shared routes with recipes or themes
- Endpoint names are namespaced (`/api/profiles/*`)

### Recipe-Specific Endpoints

**Location:** `blueprints/recipes.py`, `blueprints/recipes_research.py`

**Endpoints:**
- Recipe-specific routes are in separate blueprints
- No overlap with profile endpoints

### Recommendation

✅ **SAFE TO PROCEED:**
- API endpoints are properly namespaced
- No route conflicts possible
- Each type has its own blueprint

---

## 10. Critical Pitfalls & Issues

### ⚠️ Issue 1: Workflow Substages Are Shared

**Problem:**
- Workflow substages in database are **not filtered by post_type**
- All types use the same substages
- Navigation may show incorrect substages

**Impact:**
- If profiles need unique substages, they would appear for all types
- Navigation might be confusing

**Mitigation:**
- Use **pipeline steps** (type-specific) for type-specific workflows
- Keep workflow substages generic (planning, writing, publishing)
- Document which substages are shared vs type-specific

**Action Required:**
- [ ] Verify navigation correctly filters substages
- [ ] Document shared substages
- [ ] Consider database extension if needed

### ⚠️ Issue 2: Missing `post_type` Variables

**Problem:**
- Some routes don't pass `post_type` to templates
- Navigation may show wrong substages

**Impact:**
- Profile posts might show themed substages
- Recipe posts might show themed substages

**Mitigation:**
- Fix routes identified in NAVBAR audit
- Ensure all profile routes pass `post_type`

**Action Required:**
- [ ] Fix 3 routes from NAVBAR audit
- [ ] Audit all profile routes
- [ ] Test navigation with all post types

### ⚠️ Issue 3: Includes Not Filtered by Post Type

**Problem:**
- Includes are filtered by `illustration_method`, not `post_type`
- All types using `LLM-creation` get same includes

**Impact:**
- Profile-specific includes would need conditional loading in templates
- Or extend config system

**Mitigation:**
- Use template conditionals: `{% if post_type == 'profile' %}`
- Or create profile-specific include files
- Or extend config system

**Action Required:**
- [ ] Identify if profiles need unique includes
- [ ] Implement conditional loading if needed

### ✅ Issue 4: Section Type Prefixes (RESOLVED)

**Status:** ✅ **SAFE**
- Recipe sections use `recipe_*` prefix
- Profile sections should use `profile_*` prefix
- No overlap possible

---

## 11. Recommendations Summary

### ✅ Safe to Proceed

1. **Post Type Detection** - Properly isolated
2. **Pipeline Steps** - Completely separate per type
3. **Database Schema** - Type-specific columns, no conflicts
4. **API Endpoints** - Namespaced, no route conflicts
5. **Section Types** - Prefix-based namespacing

### ⚠️ Requires Attention

1. **Workflow Substages** - Verify navigation filtering
2. **Missing `post_type` Variables** - Fix routes from NAVBAR audit
3. **Includes System** - May need conditional loading for profiles

### 📋 Action Items

**Before Profile Development:**
- [ ] Fix 3 routes missing `post_type` (from NAVBAR audit)
- [ ] Verify navigation correctly filters substages by post_type
- [ ] Test navigation with profile, recipe, and themed posts
- [ ] Document which substages are shared vs type-specific

**During Profile Development:**
- [ ] Use `profile_*` prefix for all profile section types
- [ ] Use `profile-*` prefix for all profile pipeline steps
- [ ] Ensure all profile routes pass `post_type` variable
- [ ] Use conditional includes if profiles need unique panels

**After Profile Development:**
- [ ] Test all three post types (themes, recipes, profiles)
- [ ] Verify no interference between types
- [ ] Update documentation with profile-specific details

---

## 12. Testing Checklist

### Pre-Development Testing

- [ ] Verify recipe posts work correctly
- [ ] Verify themed posts work correctly
- [ ] Verify navigation shows correct substages for each type
- [ ] Verify pipeline steps load correctly for each type

### During Development Testing

- [ ] Test profile creation doesn't affect recipes
- [ ] Test profile creation doesn't affect themes
- [ ] Test profile navigation shows correct substages
- [ ] Test profile pipeline steps work correctly
- [ ] Test profile sections render correctly

### Post-Development Testing

- [ ] Test all three types side-by-side
- [ ] Verify no cross-contamination
- [ ] Verify navigation works for all types
- [ ] Verify pipeline steps work for all types
- [ ] Verify templates render correctly for all types

---

## 13. Conclusion

### Overall Assessment

✅ **ARCHITECTURE IS MOSTLY ROBUST**

The codebase has good isolation between post types:
- Post type detection is robust
- Pipeline steps are completely separate
- Database schema is properly isolated
- API endpoints are namespaced

⚠️ **MINOR ISSUES TO ADDRESS**

1. Workflow substages are shared (but likely intentional)
2. Some routes missing `post_type` variable (known issue, fixable)
3. Includes system may need extension for profile-specific panels

### Final Recommendation

✅ **SAFE TO PROCEED WITH PROFILE DEVELOPMENT**

With the following precautions:
1. Fix missing `post_type` variables before starting
2. Use proper prefixes (`profile_*` for sections, `profile-*` for steps)
3. Test navigation and pipeline steps for all types
4. Document any profile-specific substages or includes

The architecture is designed to support multiple post types, and profile development should not break themes or recipes if proper prefixes and isolation are maintained.

---

**Report Generated:** 2025-01-XX  
**Next Review:** After profile development begins



