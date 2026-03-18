# Workflow Endpoint Standardization Plan

## Core Principles
- Single responsibility: Each endpoint serves exactly one purpose
- Clear hierarchy: Resources flow from general to specific
- Consistent naming: Use plural nouns for collections, singular for specific items
- Simple paths: Remove unnecessary segments (like v1)
- RESTful actions: Use HTTP methods instead of action words in URLs

## Current State Analysis

### Identified Issues

1. **Inconsistent Base Paths**
   ```
   /api/workflow/
   /api/v1/workflow/
   /workflow/api/
   /blog/api/v1/
   ```

2. **Mixed Parameter Styles**
   ```
   <post_id> vs <postId>
   <slug> vs <id>
   ```

3. **Duplicate Functionality**
   ```
   /blog/api/v1/post/<post_id>/development
   /api/v1/post/<post_id>/development
   /api/workflow/posts/<post_id>/development
   ```

4. **Inconsistent Resource Naming**
   ```
   /post/ vs /posts/
   /prompt/ vs /prompts/
   ```

## Target Architecture

### API Routes
Base path: `/api/workflow/`

#### 1. Posts (Primary Resource)
Current Variants:
```
/api/v1/post/<post_id>/development
/api/v1/posts/<post_id>/development
/blog/api/v1/post/<post_id>/development
/api/v1/post/<post_id>/structure
/api/v1/posts/<post_id>/structure
```
Standardize To:
```
/api/workflow/posts/
/api/workflow/posts/<post_id>
/api/workflow/posts/<post_id>/development
/api/workflow/posts/<post_id>/structure
```

#### 2. Sections
Current Variants:
```
/api/v1/section/
/api/v1/post/<post_id>/sections/
/api/v1/posts/<post_id>/sections/<section_id>/fields/<field>
```
Standardize To:
```
/api/workflow/posts/<post_id>/sections
/api/workflow/posts/<post_id>/sections/<section_id>
/api/workflow/posts/<post_id>/sections/<section_id>/fields
```

#### 3. Fields
Current Variants:
```
/workflow/api/field_mappings/
/api/field_mappings/
/api/settings/field-mapping
/workflow_field_mapping
/api/v1/post/<post_id>/fields/
/api/v1/fields/
```
Standardize To:
```
/api/workflow/fields
/api/workflow/posts/<post_id>/fields
/api/workflow/fields/mappings
```

#### 4. Workflow Stages
Current Variants:
```
/api/workflow/stages
/workflow/api/stages
/api/v1/workflow/<slug>/status
/api/v1/workflow/<slug>/transition
/api/v1/workflow/<slug>/sub-stage
/workflow/api/sub-stages
```
Standardize To:
```
/api/workflow/posts/<post_id>/stages
/api/workflow/posts/<post_id>/stages/<stage_id>
/api/workflow/posts/<post_id>/stages/<stage_id>/sub-stages
/api/workflow/posts/<post_id>/stages/<stage_id>/transition
```

#### 5. LLM Integration
Current Variants:
```
/api/workflow/llm/
/api/workflow/run_llm/
/api/v1/workflow/run_llm/
/api/v1/llm/ollama/
/api/v1/llm/providers/
/api/v1/llm/actions/
```
Standardize To:
```
/api/workflow/providers
/api/workflow/providers/<provider_id>
/api/workflow/llm/run
```

#### 6. Prompts
Current Variants:
```
/llm/prompts
/prompts
/prompts/<int:prompt_id>
/prompts/order
/images/prompts
/api/prompts/
/api/v1/workflow/prompts/
```
Standardize To:
```
/api/workflow/prompts
/api/workflow/prompts/<prompt_id>
/api/workflow/prompts/order
```

### UI Routes
Base path: `/workflow/`
```
/workflow/
/workflow/posts/<post_id>
/workflow/posts/<post_id>/<stage>/<substage>
```

## Implementation Plan

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
   - Posts endpoints
   - Sections endpoints
   - Fields endpoints
   - Basic error handling

### Phase 2: Frontend Updates

1. **JavaScript Configuration**
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

1. **Standardize URL Generation**
   ```html
   <!-- Before -->
   {{ url_for('workflow_nav.stage', ...) }}
   
   <!-- After -->
   {{ url_for('workflow.stage', post_id=post.id, stage=stage, substage=substage) }}
   ```

2. **Update Includes**
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

## Migration Strategy

### 1. Preparation
- Create comprehensive test suite
- Document all current endpoints
- Map all dependencies
- Create rollback points

### 2. Implementation Steps
1. Create new blueprint structure
2. Implement new endpoints
3. Update JavaScript config
4. Update templates
5. Add deprecation warnings
6. Test thoroughly
7. Remove old endpoints

### 3. Validation
- All endpoints follow new structure
- No duplicate functionality
- Consistent parameter naming
- Clear resource hierarchy
- Working navigation
- All tests passing

## Migration Checkpoints

### Phase 1: Posts Resource Migration ⬜️
Each checkpoint must pass all tests before proceeding.

#### 1.1 Basic Post Endpoints ⬜️
- [ ] Implement `/api/workflow/posts/`
- [ ] Implement `/api/workflow/posts/<post_id>`
- [ ] Add deprecation warnings on old endpoints
- [ ] Test with curl:
  ```bash
  curl http://localhost:5000/api/workflow/posts/
  curl http://localhost:5000/api/workflow/posts/1
  ```
- [ ] Verify response format matches specification
- [ ] Run automated tests
- [ ] Update documentation

**Rollback Point**: 
```bash
git checkout HEAD app/api/workflow/routes.py
./scripts/dev/restart_flask_dev.sh
```

#### 1.2 Post Development Endpoints ⬜️
- [ ] Implement `/api/workflow/posts/<post_id>/development`
- [ ] Implement `/api/workflow/posts/<post_id>/structure`
- [ ] Add deprecation warnings on:
  - `/api/v1/post/<post_id>/development`
  - `/blog/api/v1/post/<post_id>/development`
- [ ] Test with curl:
  ```bash
  curl http://localhost:5000/api/workflow/posts/1/development
  curl http://localhost:5000/api/workflow/posts/1/structure
  ```
- [ ] Verify all development data is accessible
- [ ] Run automated tests
- [ ] Update documentation

**Rollback Point**: 
```bash
git checkout HEAD app/api/workflow/routes.py
./scripts/dev/restart_flask_dev.sh
```

### Phase 2: Sections Resource Migration ⬜️

#### 2.1 Basic Section Endpoints ⬜️
- [ ] Implement `/api/workflow/posts/<post_id>/sections`
- [ ] Implement `/api/workflow/posts/<post_id>/sections/<section_id>`
- [ ] Add deprecation warnings on old endpoints
- [ ] Test with curl:
  ```bash
  curl http://localhost:5000/api/workflow/posts/1/sections
  curl http://localhost:5000/api/workflow/posts/1/sections/1
  ```
- [ ] Verify section data integrity
- [ ] Run automated tests
- [ ] Update documentation

**Rollback Point**: 
```bash
git checkout HEAD app/api/workflow/routes.py
./scripts/dev/restart_flask_dev.sh
```

#### 2.2 Section Fields Endpoints ⬜️
- [ ] Implement `/api/workflow/posts/<post_id>/sections/<section_id>/fields`
- [ ] Add deprecation warnings on old endpoints
- [ ] Test with curl:
  ```bash
  curl http://localhost:5000/api/workflow/posts/1/sections/1/fields
  ```
- [ ] Verify field data integrity
- [ ] Run automated tests
- [ ] Update documentation

**Rollback Point**: 
```bash
git checkout HEAD app/api/workflow/routes.py
./scripts/dev/restart_flask_dev.sh
```

### Phase 3: Fields Resource Migration ⬜️

#### 3.1 Field Mappings ⬜️
- [ ] Implement `/api/workflow/fields/mappings`
- [ ] Add deprecation warnings on:
  - `/workflow/api/field_mappings/`
  - `/api/field_mappings/`
  - `/api/settings/field-mapping`
- [ ] Test with curl:
  ```bash
  curl http://localhost:5000/api/workflow/fields/mappings
  ```
- [ ] Verify mapping data integrity
- [ ] Run automated tests
- [ ] Update documentation

**Rollback Point**: 
```bash
git checkout HEAD app/api/workflow/routes.py
./scripts/dev/restart_flask_dev.sh
```

### Phase 4: Workflow Stages Migration ⬜️

#### 4.1 Stage Management ⬜️
- [ ] Implement `/api/workflow/posts/<post_id>/stages`
- [ ] Implement `/api/workflow/posts/<post_id>/stages/<stage_id>`
- [ ] Add deprecation warnings on old endpoints
- [ ] Test with curl:
  ```bash
  curl http://localhost:5000/api/workflow/posts/1/stages
  curl http://localhost:5000/api/workflow/posts/1/stages/1
  ```
- [ ] Verify stage transitions work
- [ ] Run automated tests
- [ ] Update documentation

**Rollback Point**: 
```bash
git checkout HEAD app/api/workflow/routes.py
./scripts/dev/restart_flask_dev.sh
```

#### 4.2 Sub-stage Management ⬜️
- [ ] Implement `/api/workflow/posts/<post_id>/stages/<stage_id>/sub-stages`
- [ ] Add deprecation warnings on old endpoints
- [ ] Test with curl:
  ```bash
  curl http://localhost:5000/api/workflow/posts/1/stages/1/sub-stages
  ```
- [ ] Verify sub-stage transitions
- [ ] Run automated tests
- [ ] Update documentation

**Rollback Point**: 
```bash
git checkout HEAD app/api/workflow/routes.py
./scripts/dev/restart_flask_dev.sh
```

### Phase 5: LLM Integration Migration ⬜️

#### 5.1 Provider Management ⬜️
- [ ] Implement `/api/workflow/providers`
- [ ] Implement `/api/workflow/providers/<provider_id>`
- [ ] Add deprecation warnings on old endpoints
- [ ] Test with curl:
  ```bash
  curl http://localhost:5000/api/workflow/providers
  curl http://localhost:5000/api/workflow/providers/ollama
  ```
- [ ] Verify provider operations work
- [ ] Run automated tests
- [ ] Update documentation

**Rollback Point**: 
```bash
git checkout HEAD app/api/workflow/routes.py
./scripts/dev/restart_flask_dev.sh
```

#### 5.2 LLM Operations ⬜️
- [ ] Implement `/api/workflow/llm/run`
- [ ] Add deprecation warnings on old endpoints
- [ ] Test with curl:
  ```bash
  curl -X POST http://localhost:5000/api/workflow/llm/run -d '{...}'
  ```
- [ ] Verify LLM processing works
- [ ] Run automated tests
- [ ] Update documentation

**Rollback Point**: 
```bash
git checkout HEAD app/api/workflow/routes.py
./scripts/dev/restart_flask_dev.sh
```

### Phase 6: Prompt Management Migration ⬜️

#### 6.1 Basic Prompt Management ⬜️
- [ ] Implement `/api/workflow/prompts`
- [ ] Implement `/api/workflow/prompts/<prompt_id>`
- [ ] Add deprecation warnings on old endpoints
- [ ] Test with curl:
  ```bash
  curl http://localhost:5000/api/workflow/prompts
  curl http://localhost:5000/api/workflow/prompts/1
  ```
- [ ] Verify prompt operations
- [ ] Run automated tests
- [ ] Update documentation

**Rollback Point**: 
```bash
git checkout HEAD app/api/workflow/routes.py
./scripts/dev/restart_flask_dev.sh
```

#### 6.2 Prompt Ordering ⬜️
- [ ] Implement `/api/workflow/prompts/order`
- [ ] Add deprecation warnings on old endpoints
- [ ] Test with curl:
  ```bash
  curl http://localhost:5000/api/workflow/prompts/order
  ```
- [ ] Verify order management works
- [ ] Run automated tests
- [ ] Update documentation

**Rollback Point**: 
```bash
git checkout HEAD app/api/workflow/routes.py
./scripts/dev/restart_flask_dev.sh
```

### Phase 7: Frontend Updates ⬜️

#### 7.1 API Configuration ⬜️
- [ ] Create `/static/js/config/api.js`
- [ ] Update all JavaScript files to use new config
- [ ] Test in browser
- [ ] Verify no console errors
- [ ] Run automated tests
- [ ] Update documentation

**Rollback Point**: 
```bash
git checkout HEAD app/static/js/
./scripts/dev/restart_flask_dev.sh
```

#### 7.2 Template Updates ⬜️
- [ ] Update all template URL generation
- [ ] Fix navigation includes
- [ ] Test all navigation flows
- [ ] Verify no template errors
- [ ] Run automated tests
- [ ] Update documentation

**Rollback Point**: 
```bash
git checkout HEAD app/templates/
./scripts/dev/restart_flask_dev.sh
```

### Phase 8: Cleanup ⬜️

#### 8.1 Remove Deprecated Routes ⬜️
- [ ] Remove all deprecated route handlers
- [ ] Remove old blueprints
- [ ] Test all endpoints still work
- [ ] Verify no 404 errors
- [ ] Run automated tests
- [ ] Update documentation

**Rollback Point**: 
```bash
git checkout HEAD app/
./scripts/dev/restart_flask_dev.sh
```

## Testing Requirements for Each Phase

1. **Endpoint Testing**
   - Response status codes correct
   - Response format matches specification
   - Error handling works
   - Parameters validated correctly

2. **Integration Testing**
   - Frontend successfully calls new endpoints
   - Data flow works end-to-end
   - State transitions work
   - Error handling works

3. **UI Testing**
   - Navigation works
   - Forms submit correctly
   - Error messages display properly
   - No console errors

## Rollback Procedure

If any phase fails:

1. Execute the rollback command for that phase
2. Verify the system returns to working state
3. Document the failure
4. Review and adjust the migration plan
5. Only proceed after fixing the issue

## Success Criteria for Each Phase

1. All new endpoints return correct data
2. All automated tests pass
3. No JavaScript console errors
4. No Python exceptions in logs
5. All UI functions work
6. Documentation is updated