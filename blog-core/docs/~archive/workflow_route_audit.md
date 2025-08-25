# Workflow Route Audit

## Current Progress (PAUSED FOR INVESTIGATION)

### ✅ Completed
1. Removed toxic files:
   - `app/workflow/navigation.py` (toxic duplicate)
   - `app/templates/workflow/_workflow_nav.html` (toxic template)
   
2. Updated blueprint registration:
   - Removed `init_workflow()` function
   - Simplified `app/workflow/__init__.py`
   - Reorganized blueprint registration order in `app/__init__.py`

### ❌ Current Issue (UNDER INVESTIGATION)
After removing toxic navigation code, encountered BuildError in nav module:
```
BuildError: Could not build url for endpoint 'workflow_nav.stage' 
with values ['post_id']. 
Did you forget to specify values ['stage', 'substage']?
```

This error needs careful investigation as it suggests:
1. Possible missing route parameters in nav module
2. Potential dependency on removed code we didn't catch
3. Route registration order issues we didn't account for

### 🔄 Pending (ON HOLD)
- API route consolidation
- Frontend updates
- Template resolution fixes
- Route migration
- Testing implementation

## Investigation Plan

### 1. Nav Module Analysis
Need to investigate:
- Current nav module route definitions
- Compare with reference implementation
- Check template dependencies
- Verify URL generation in templates
- Map out all navigation-related endpoints

### 2. Dependency Check
Need to audit:
- Which components depend on nav module
- How routes are being called
- Where URL generation is happening
- Template inheritance chain

### 3. Reference Implementation Review
Need to review:
- `backups/nav_reference_DO_NOT_MODIFY/`
- Compare with current implementation
- Document any discrepancies
- Identify potential fixes

### 4. Risk Assessment
Before proceeding with any fixes, need to:
- Document current working functionality
- Identify potential impact areas
- Create backup points
- Plan verification steps

## Next Steps
1. Complete full investigation
2. Report findings
3. Propose specific fixes
4. Wait for explicit approval before any code changes

## Working Functionality (DO NOT BREAK)
- Main workflow routes still accessible
- Basic navigation structure intact
- Template resolution working
- Blueprint registration successful

## Rollback Point
Current state saved in git status:
- Toxic files removed
- Blueprint registration updated
- Basic structure working
- Nav module partially functional

## Current State Analysis

### 1. JavaScript Route Usage

#### Direct URL Manipulation (MUST FIX)
```javascript
// Found in multiple files
window.location.href = `/workflow/posts/${postId}/`;
window.location.href = `{{ url_for('workflow_nav.stage', post_id=0) }}`.replace('/0/', `/${postId}/`);
```

#### API Endpoint Patterns (INCONSISTENT)
```javascript
// Multiple base paths in use
/api/v1/post/${postId}/development
/blog/api/v1/post/${postId}/development
/workflow/api/field_mappings/
/api/settings/field-mapping
```

#### Navigation Handling (FRAGMENTED)
- Direct URL manipulation in JavaScript
- Template URL injection into JavaScript
- Multiple navigation implementation patterns
- Inconsistent parameter handling

### 2. Template URL Generation

#### Navigation Templates
```html
<!-- Multiple patterns in use -->
{{ url_for('workflow_nav.stage', ...) }}
{{ url_for('workflow.workflow_index', ...) }}
{{ url_for('workflow.stage', ...) }}
```

#### Include Patterns
```html
<!-- Inconsistent include paths -->
{% include 'workflow/_workflow_nav.html' %}
{% include 'nav/workflow_nav.html' %}
```

### 3. API Route Inventory

#### Field Mapping Routes (4 variants)
```python
/workflow/api/field_mappings/
/api/field_mappings/
/api/settings/field-mapping
/workflow_field_mapping
```

#### Prompt Routes (10 variants)
```python
/llm/prompts
/prompts
/prompts/<int:prompt_id>
/prompts/order
/images/prompts
/api/prompts/
/api/v1/workflow/prompts/
/api/v1/workflow/prompts/<int:prompt_id>
/api/v1/workflow/prompts/order
/api/v1/workflow/step-prompts/<int:post_id>/<int:step_id>
```

#### LLM Routes (3 variants)
```python
/api/workflow/llm/
/api/workflow/run_llm/
/api/v1/workflow/run_llm/
```

#### Post Development Routes (5 variants)
```python
/api/v1/post/${postId}/development
/api/v1/posts/${postId}/development
/blog/api/v1/post/${postId}/development
/api/v1/post/${postId}/structure
/api/v1/posts/${postId}/structure
```

## Required Changes

### 1. JavaScript Standardization

#### Create API Configuration
```javascript
// New file: static/js/config/api.js
const API_CONFIG = {
    BASE_URL: '/api/v1/workflow',
    ENDPOINTS: {
        FIELD_MAPPINGS: '/field-mappings',
        PROMPTS: '/prompts',
        POSTS: '/posts',
        LLM: '/llm'
    }
};
```

#### Update API Calls
```javascript
// Before
fetch('/api/field_mappings/')

// After
fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.FIELD_MAPPINGS}`)
```

#### Fix Navigation
```javascript
// Before
window.location.href = `/workflow/posts/${postId}/`;

// After
navigateToWorkflow(postId, stage, substage);
```

### 2. Template Standardization

#### Update URL Generation
```html
<!-- Before -->
{{ url_for('workflow_nav.stage', ...) }}

<!-- After -->
{{ url_for('workflow.stage', post_id=post.id, stage=stage, substage=substage) }}
```

#### Fix Includes
```html
<!-- Before -->
{% include 'workflow/_workflow_nav.html' %}

<!-- After -->
{% include 'nav/workflow_nav.html' %}
```

### 3. API Consolidation

#### New Route Structure
```python
# app/api/v1/workflow/routes.py

@bp.route('/field-mappings/')
def get_field_mappings():
    """Get all field mappings."""
    pass

@bp.route('/prompts/')
def get_prompts():
    """Get all prompts."""
    pass

@bp.route('/posts/<int:post_id>/development')
def post_development(post_id):
    """Handle post development."""
    pass
```

#### Deprecation Handlers
```python
@deprecated_endpoint('/api/v1/workflow/field-mappings/')
def deprecated_field_mappings():
    return redirect(url_for('api_v1_workflow.get_field_mappings'))
```

## Testing Requirements

### 1. JavaScript Tests
```javascript
describe('API Configuration', () => {
    it('should use standard API_CONFIG', () => {
        expect(API_CONFIG.BASE_URL).toBe('/api/v1/workflow');
    });
});

describe('Navigation', () => {
    it('should use navigation utility', () => {
        const url = buildWorkflowUrl(1, 'planning', 'idea');
        expect(url).toBe('/workflow/posts/1/planning/idea');
    });
});
```

### 2. Template Tests
```python
def test_url_generation():
    """Test template URL generation."""
    url = url_for('workflow.stage', post_id=1, stage='planning')
    assert url.startswith('/workflow/posts/')
    assert 'workflow_nav' not in url
```

### 3. API Tests
```python
def test_api_endpoints():
    """Test API endpoint standards."""
    response = client.get('/api/v1/workflow/field-mappings/')
    assert response.status_code == 200
    assert response.json['success'] is True
```

## Verification Steps

### 1. JavaScript Verification
- [ ] All API calls use API_CONFIG
- [ ] No direct URL manipulation
- [ ] Navigation uses utilities
- [ ] Parameters properly encoded

### 2. Template Verification
- [ ] All URLs use workflow blueprint
- [ ] Navigation includes standardized
- [ ] Parameters consistent
- [ ] No deprecated patterns

### 3. API Verification
- [ ] All endpoints follow standards
- [ ] Error responses consistent
- [ ] Parameters validated
- [ ] JSON schemas valid

## Rollback Points

### JavaScript Changes
```bash
git checkout HEAD app/static/js/
./scripts/dev/restart_flask_dev.sh
```

### Template Changes
```bash
git checkout HEAD app/templates/
./scripts/dev/restart_flask_dev.sh
```

### API Changes
```bash
git checkout HEAD app/api/
./scripts/dev/restart_flask_dev.sh
```

## Next Steps

1. Create API configuration module
2. Update JavaScript files one at a time
3. Fix template URL generation
4. Consolidate API routes
5. Add deprecation handlers
6. Run full test suite
7. Document all changes

## JavaScript Implementation Issues

### Module System Inconsistencies
- **Files Using ES6 Modules**:
  - `workflow_output.html`: Uses import statements
  - `app/templates/modules/llm_panel/templates/panel.html`: Uses import statements
- **Files Using Traditional Scripts**:
  - `app/templates/base.html`: Global script include
  - Other templates: Mixed usage

### API Endpoint Usage Patterns
- Direct URL manipulation in JavaScript
- Inconsistent base paths
- Mixed API version references
- Varied error handling approaches

### Implementation Strategy
1. Document all problematic files with TODO comments
2. Only update JavaScript files when required for endpoint standardization
3. Maintain compatibility with both module systems
4. Flag for future full modernization project

### Files Requiring Attention
- `app/static/js/llm_utils.js`: Multiple endpoint patterns
- `app/templates/base.html`: Global script loading
- `app/templates/modules/llm_panel/templates/panel.html`: Module imports
- `workflow_output.html`: Module imports

## JavaScript Endpoint Patterns

### API Base Path Variations
1. Workflow-specific paths:
   - `/api/v1/workflow/`
   - `/workflow/api/`
   - `/api/v1/workflow/llm/`

2. LLM-related paths:
   - `/api/v1/llm/`
   - `/api/v1/workflow/llm/`
   - `/api/v1/llm/actions/`
   - `/api/v1/llm/ollama/`

3. Post-related paths:
   - `/api/v1/post/`
   - `/blog/api/v1/post/`
   - `/api/v1/posts/`

4. Settings paths:
   - `/api/settings/`
   - `/workflow/api/field_mappings/`

### Navigation Pattern Issues
1. Direct URL Manipulation:
   ```javascript
   window.location.href = '/workflow/template/?post_id=${id}'
   window.location.href = `/workflow/edit/?section=${section}&post_id=${id}`
   ```

2. Path Parsing:
   ```javascript
   window.location.pathname.split('/')
   window.location.pathname.match(/\/workflow\/\w+\/(\w+)/)
   ```

3. Query Parameter Handling:
   ```javascript
   new URLSearchParams(window.location.search)
   ```

### Files Requiring Updates

#### High Priority (Active Workflow Files)
1. `app/static/js/llm_utils.js`:
   - Multiple endpoint patterns
   - Direct URL manipulation
   - Mixed API version usage

2. `modules/llm_panel/static/js/field_selector.js`:
   - Inconsistent API paths
   - Direct path parsing
   - Mixed endpoint versions

3. `app/static/js/config/api.js`:
   - New file, needs integration testing
   - URL building utilities
   - Navigation helpers

#### Secondary Priority
1. Template View Files:
   - Multiple direct URL manipulations
   - Inconsistent routing patterns
   - Query parameter handling

2. Structure Stage Files:
   - Mixed API versions
   - Inconsistent base paths
   - Direct navigation code

### Implementation Concerns

1. **API Version Consistency**:
   - Multiple `/api/v1/` vs `/blog/api/v1/` usage
   - Some endpoints missing version prefix
   - Mixed usage within same files

2. **URL Construction**:
   - Direct string interpolation
   - Inconsistent parameter handling
   - No central URL building

3. **Navigation Handling**:
   - Direct window.location manipulation
   - Multiple URL parsing approaches
   - No standardized navigation utilities

4. **Error Handling**:
   - Inconsistent response processing
   - Mixed success checking patterns
   - Varied error reporting

## Module System Impact

### Current State
- Mixed module patterns affecting endpoint standardization
- Import/export inconsistencies
- Global vs module-scoped utilities

### Required Changes
1. Maintain current module system where possible
2. Document technical debt
3. Update endpoint patterns without full module conversion
4. Add TODO markers for future cleanup

## Next Steps

1. **Immediate Actions**:
   - Add TODO comments to affected files
   - Document all non-compliant patterns
   - Create endpoint migration tracking

2. **Planning Required**:
   - API version standardization approach
   - URL construction utilities
   - Navigation helper implementation
   - Error handling standardization