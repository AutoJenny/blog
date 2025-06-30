# Workflow Route Migration Guide

## MUST DO RULES FOR AI ASSISTANT

Work through the checklist actions. Tick them off when complete. If you hit ANY snags, CONSULT... DO NOT CODE WITHOUT EXPLICIT INFORMED CONSENT


### Task Execution Rules
1. For EVERY task:
   - Explicitly cite the relevant section of this plan being followed
   - Quote the exact text being followed
   - Wait for user confirmation before proceeding
   - Do not proceed until user confirms correct section is being referenced

2. When Gaps Are Found:
   - Explicitly identify missing details
   - Request user guidance to fill gaps
   - Never make assumptions or invent steps
   - Wait for user direction before proceeding

3. Before Any Changes:
   - Confirm completion of all relevant pre-migration checklist items
   - Verify existence of required backups as specified
   - Ensure testing setup is ready as outlined
   - Get user confirmation of readiness

4. For Each Change:
   - Follow exact patterns shown in examples
   - Use documented rollback procedures precisely
   - Test according to specific listed criteria
   - Document any deviations or issues found

5. Documentation Requirements:
   - Keep track of each completed step
   - Note any deviations from plan
   - Record all test results
   - Flag any concerns immediately

## Overview

This guide outlines the step-by-step process for migrating workflow routes to a standardized format. It focuses on maintaining functionality while transitioning to a cleaner, more consistent API structure.

## Pre-Migration Checklist

### 1. Code Inventory
- [x] List all JavaScript files using workflow routes
- [x] Document all template URL generation patterns
- [x] Map all API endpoint variations
- [x] Identify all navigation implementations

### 2. Backup Requirements
- [x] Git branch for migration
- [x] Backup of all JavaScript files
- [x] Backup of all templates
- [x] Database backup if needed

### 3. Testing Setup
- [x] JavaScript test suite ready
- [x] Template test suite ready
- [x] API test suite ready
- [x] Integration tests prepared

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

## Migration Process

### Phase 1: Blueprint Restructuring

1. **Create New Blueprint Structure**
   ```python
   # app/api/workflow/__init__.py
   from flask import Blueprint
   bp = Blueprint('api_workflow', __name__)
   
   # app/__init__.py
   from .api.workflow import bp as workflow_bp
   app.register_blueprint(workflow_bp, url_prefix='/api/workflow')
   ```

2. **Implement Core Resources**
   ```python
   # app/api/workflow/routes.py
   
   @bp.route('/posts/<int:post_id>')
   def get_post(post_id):
       """Get post details."""
       pass
   
   @bp.route('/posts/<int:post_id>/development')
   def post_development(post_id):
       """Handle post development."""
       pass
   ```

### Phase 2: Frontend Updates

1. **Create API Configuration**
   ```javascript
   // static/js/config/api.js
   const API_CONFIG = {
       BASE_URL: '/api/workflow',
       ENDPOINTS: {
           POSTS: '/posts',
           FIELDS: '/fields',
           PROMPTS: '/prompts',
           LLM: '/llm'
       }
   };
   ```

2. **Update API Calls**
   ```javascript
   // Before
   fetch('/api/field_mappings/')
   
   // After
   fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.FIELDS}/mappings`)
   ```

3. **Fix Navigation**
   ```javascript
   // Before
   window.location.href = `/workflow/posts/${postId}/`
   
   // After
   navigateToWorkflow(postId, stage, substage)
   ```

### Phase 3: Template Updates

1. **Update URL Generation**
   ```html
   <!-- Before -->
   {{ url_for('workflow_nav.stage', ...) }}
   
   <!-- After -->
   {{ url_for('workflow.stage', post_id=post.id, stage=stage, substage=substage) }}
   ```

2. **Fix Includes**
   ```html
   <!-- Before -->
   {% include 'workflow/_workflow_nav.html' %}
   
   <!-- After -->
   {% include 'nav/workflow_nav.html' %}
   ```

### Phase 4: Deprecation & Cleanup

1. **Add Deprecation Warnings**
   ```python
   @deprecated_endpoint('/api/v1/workflow/field-mappings/')
   def deprecated_field_mappings():
       return redirect(url_for('api_workflow.get_field_mappings'))
   ```

2. **Remove Old Routes**
   - Document each removed route
   - Update affected templates
   - Update JavaScript references
   - Run full test suite

## Testing Requirements

### 1. Endpoint Testing
```python
def test_endpoint_standards():
    """Verify all endpoints follow standards"""
    # Test post endpoints
    response = client.get('/api/workflow/posts/1')
    assert response.status_code == 200
    
    # Test stage endpoints
    response = client.get('/api/workflow/posts/1/stages')
    assert response.status_code == 200
```

### 2. Frontend Testing
```javascript
describe('API Configuration', () => {
    it('should use standard endpoints', () => {
        expect(API_CONFIG.BASE_URL).toBe('/api/workflow');
    });
    
    it('should build valid URLs', () => {
        const url = buildWorkflowUrl(1, 'planning');
        expect(url).toBe('/api/workflow/posts/1/stages/planning');
    });
});
```

## Rollback Procedures

### 1. Individual File Rollback
```bash
git checkout HEAD path/to/file.js
./scripts/dev/restart_flask_dev.sh
```

### 2. Full Rollback
```bash
git checkout HEAD app/
./scripts/dev/restart_flask_dev.sh
```

## Success Criteria

1. **Endpoint Structure**
   - All endpoints follow new patterns
   - No duplicate functionality
   - Consistent parameter naming
   - Clear resource hierarchy

2. **Frontend Integration**
   - All JavaScript uses API_CONFIG
   - No direct URL manipulation
   - Consistent template URLs
   - Working navigation

3. **Documentation**
   - Updated API documentation
   - Removed deprecated endpoints
   - Clear migration guide
   - Technical debt documented

4. **Testing**
   - All unit tests passing
   - Integration tests passing
   - No runtime errors
   - Clean error logs 