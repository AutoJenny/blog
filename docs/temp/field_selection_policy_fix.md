# Field Selection Mapping Policy Fix

## Summary

**CANONICAL POLICY: Field selection mappings are per-step only, never per-post.**

This document outlines the policy fix for field selection mappings to ensure they operate on a per-step basis only, removing all post ID dependencies.

## Current Issues

### 1. **API Endpoints Using Post ID**
- **GET**: `/api/workflow/steps/<step_id>/field_selection/<post_id>` 
- **POST**: `/api/workflow/steps/<step_id>/field_selection` (requires `post_id` in payload)
- **Problem**: These endpoints incorrectly require post ID when field selection should be global per step

### 2. **Frontend Logic Using Post ID**
- Frontend fetches field selection using: `/api/workflow/steps/${stepId}/field_selection/${this.postId}`
- Frontend saves field selection with `post_id` in payload
- **Problem**: Creates unnecessary post-specific field selection mappings

### 3. **404 Errors in Workflow**
- Console errors: `Failed to load resource: 404 (NOT FOUND) http://localhost:5000/api/workflow/steps/15/field_selection/22`
- **Root Cause**: Frontend trying to load post-specific field selection that doesn't exist

## Canonical Policy

### Field Selection Mappings Are:
- **Per-step only**: Each workflow step has one global field selection mapping
- **Global for all posts**: The same step uses the same output field regardless of post
- **Stored in step config**: `workflow_step_entity.config.settings.llm.user_output_mapping`
- **Accessed by step ID only**: No post ID required

### Field Selection Mappings Are NOT:
- Per-post configurations
- Post-specific mappings
- Dependent on individual post context

## Technical Changes Required

### 1. **Backend API Changes**
```python
# Current (INCORRECT)
@bp.route('/steps/<int:step_id>/field_selection/<int:post_id>', methods=['GET'])
def get_field_selection(step_id, post_id):

# Fixed (CORRECT)
@bp.route('/steps/<int:step_id>/field_selection', methods=['GET'])
def get_field_selection(step_id):
```

```python
# Current (INCORRECT) - requires post_id in payload
def save_field_selection(step_id):
    data = request.get_json()
    post_id = data.get('post_id')  # Remove this

# Fixed (CORRECT) - only output_field and output_table
def save_field_selection(step_id):
    data = request.get_json()
    output_field = data.get('output_field')
    output_table = data.get('output_table')
```

### 2. **Frontend Changes**
```javascript
// Current (INCORRECT)
const response = await fetch(`/api/workflow/steps/${stepId}/field_selection/${this.postId}`);

// Fixed (CORRECT)
const response = await fetch(`/api/workflow/steps/${stepId}/field_selection`);
```

```javascript
// Current (INCORRECT) - includes post_id in payload
const payload = {
    post_id: this.postId,
    output_field: fieldName,
    output_table: 'post_development'
};

// Fixed (CORRECT) - only field and table
const payload = {
    output_field: fieldName,
    output_table: 'post_development'
};
```

## Implementation Plan

### Phase 1: Documentation (COMPLETED)
- ✅ Updated `docs/reference/database/schema.md` with canonical policy
- ✅ Updated `docs/reference/api/current/fields.md` with correct endpoints
- ✅ Updated `docs/README.md` with policy summary

### Phase 2: Backend Changes (PENDING)
- Update `/api/workflow/steps/<step_id>/field_selection` endpoints
- Remove all post ID references from field selection logic
- Ensure field selection is stored/retrieved from step config only

### Phase 3: Frontend Changes (PENDING)
- Update `app/static/modules/llm_panel/js/field_selector.js`
- Remove post ID from all field selection fetch/save operations
- Test field selection loading and saving

### Phase 4: Testing (PENDING)
- Verify field selection works across multiple posts
- Confirm 404 errors are resolved
- Test workflow navigation and field persistence

## Related But Different Systems

### Per-Post Field Mappings (UNCHANGED)
These systems correctly remain post-specific and are NOT affected:

1. **LLM Action Button Settings** (`post_workflow_step_action`)
   - `input_field`, `output_field`, `button_label`, `button_order`
   - Correctly per-post for UI customization

2. **Stage-Level Field Persistence** (`post_workflow_stage`)
   - `input_field`, `output_field` for stage-level settings
   - Correctly per-post for stage-specific configuration

## Benefits of This Fix

1. **Consistency**: All posts use the same field selection for each step
2. **Simplicity**: No per-post field selection configuration complexity
3. **Reliability**: Eliminates 404 errors from missing post-specific mappings
4. **Maintainability**: Single source of truth for step field mappings
5. **Performance**: No need to create/check post-specific field selection records

## Migration Notes

- Existing field selection mappings in `workflow_step_entity.config` will continue to work
- No database migration required - only API and frontend changes
- All posts will automatically use the step's global field selection mapping 