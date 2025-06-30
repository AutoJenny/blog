# API Route Orthodoxy Implementation Plan

## Overview
This document outlines the plan to standardize all API routes in the application, ensuring consistency and preventing conflicts. The goal is to have all API endpoints under `/api/v1/` with clear, logical groupings.

## Current State Analysis
- Multiple route prefixes in use: `/api/v1/`, `/blog/api/v1/`, `/llm/api/v1/`
- Duplicate routes for same functionality
- Inconsistent path structures
- Mixed usage in frontend code
- Documentation references both old and new paths
- Blueprint mismatches (API endpoints defined in wrong blueprints)
- Inconsistent resource naming (singular vs plural)

## Critical Issues Found
1. Structure endpoints are defined in wrong blueprint:
   - `/api/v1/structure/plan` is actually at `/blog/api/v1/structure/plan`
   - `/api/v1/structure/plan_and_save` exists but not documented
   - `/api/v1/structure/save/<post_id>` is documented but not implemented

2. Inconsistent resource naming:
   - Both `/api/v1/post/...` and `/api/v1/posts/...` are used
   - `/api/v1/post_development/fields` uses non-standard pattern
   - `/api/v1/llm/post_substage_actions` needs standardization

3. Blueprint registration issues:
   - API endpoints defined in `blog` blueprint instead of `api` blueprint
   - This causes actual URLs to be different from documented ones
   - Found in `app.py`: `app.register_blueprint(blog_bp, url_prefix='/blog')`

4. Frontend API Call Issues:
   - `structure_stage.js` uses `/blog/api/v1/structure/plan` instead of `/api/v1/structure/plan`
   - Multiple hardcoded paths in templates need updating
   - Inconsistent path usage across different JS files

5. Additional Route Patterns:
   - `/api/v1/images/*` endpoints (not in original plan)
   - `/api/v1/comfyui/*` endpoints (not in original plan)
   - `/api/v1/llm/post_substage_actions` (needs standardization)

6. Documentation Inconsistencies:
   - Multiple docs reference different path patterns
   - Some endpoints documented but not implemented
   - Some implemented but not documented

## Implementation Strategy
1. Create backups
2. Update documentation
3. Fix blueprint registrations
4. Standardize resource naming
5. Update backend routes
6. Update frontend code
7. Test thoroughly
8. Deploy changes

## Detailed Steps

### 1. Preparation and Backup
- [ ] Create git branch `feature/api-route-standardization`
- [ ] Backup current database
- [ ] Document all current working endpoints with curl tests
- [ ] Create test suite for critical endpoints
- [ ] Document current blueprint registrations and URL prefixes
- [ ] Create backup of all frontend files with hardcoded paths

### 2. Documentation Updates
- [ ] Create new API documentation structure
- [ ] Update all `/docs/api/*.md` files to reflect new route structure
- [ ] Update all `/docs/temp/*.md` files
- [ ] Update README.md with new route conventions
- [ ] Create route migration guide for developers
- [ ] Document blueprint registration rules
- [ ] Update structure stage documentation to match implementation
- [ ] Document all image and comfyui endpoints
- [ ] Create API versioning policy document

### 3. Blueprint and Route Standardization
- [ ] Move all API endpoints to correct blueprints:
  - [ ] Move structure endpoints from `blog` to `api` blueprint
  - [ ] Move LLM endpoints to `api` blueprint
  - [ ] Move image endpoints to `api` blueprint
  - [ ] Move comfyui endpoints to `api` blueprint
  - [ ] Update blueprint registrations in `app/__init__.py`
- [ ] Standardize resource naming:
  - [ ] Use plural for resource collections (`/api/v1/posts/`)
  - [ ] Use singular for individual resources (`/api/v1/post/<id>/`)
  - [ ] Update all endpoints to follow this pattern
  - [ ] Standardize `/api/v1/post_development/fields` to `/api/v1/posts/development/fields`
  - [ ] Standardize `/api/v1/llm/post_substage_actions` to `/api/v1/posts/substage/actions`
- [ ] Implement missing documented endpoints:
  - [ ] Add `/api/v1/structure/save/<post_id>`
  - [ ] Document or remove `/api/v1/structure/plan_and_save`
- [ ] Remove deprecated routes
- [ ] Add proper error handling for old routes (temporary redirects)

### 4. Frontend Code Updates
- [ ] Update all JavaScript fetch calls:
  - [ ] `app/static/js/workflow/structure_stage.js`
  - [ ] `app/static/js/llm_utils.js`
  - [ ] `app/static/js/llm.js`
  - [ ] `app/static/js/workflow/api.js`
- [ ] Update all template files:
  - [ ] `app/templates/main/llm_providers.html`
  - [ ] `app/templates/main/llm_prompts.html`
  - [ ] `app/templates/llm/config.html`
  - [ ] `app/templates/llm/templates.html`
  - [ ] `app/templates/llm/images_configs.html`
  - [ ] `app/templates/llm/llm_models.html`
  - [ ] `app/templates/llm/images_prompts.html`
  - [ ] `app/templates/llm/actions.html`
- [ ] Create API client utility to centralize API calls
- [ ] Update all hardcoded paths to use the utility

### 5. Testing Plan
- [ ] Create test suite for all API endpoints
- [ ] Test all frontend functionality
- [ ] Verify all documentation links
- [ ] Test error handling
- [ ] Test backward compatibility
- [ ] Load testing for critical endpoints
- [ ] Test blueprint registrations
- [ ] Verify URL prefixes
- [ ] Test all image and comfyui endpoints
- [ ] Test all LLM endpoints
- [ ] Test all structure endpoints
- [ ] Test all post endpoints

### 6. Deployment Strategy
- [ ] Deploy to staging environment
- [ ] Monitor for errors
- [ ] Roll back plan if issues found
- [ ] Deploy to production
- [ ] Monitor logs for 404s/errors
- [ ] Remove old route handlers after confirmation

## Route Structure After Changes

### Blog API (`/api/v1/posts/`)
```
GET    /api/v1/posts
GET    /api/v1/posts/<id>
POST   /api/v1/posts
PUT    /api/v1/posts/<id>
DELETE /api/v1/posts/<id>
GET    /api/v1/posts/<id>/development
POST   /api/v1/posts/<id>/development
GET    /api/v1/posts/<id>/sections
POST   /api/v1/posts/<id>/sections
PUT    /api/v1/posts/<id>/sections/<section_id>
DELETE /api/v1/posts/<id>/sections/<section_id>
GET    /api/v1/posts/development/fields
GET    /api/v1/posts/<id>/structure
```

### Structure API (`/api/v1/structure/`)
```
POST   /api/v1/structure/plan
POST   /api/v1/structure/save/<id>
```

### LLM API (`/api/v1/llm/`)
```
GET    /api/v1/llm/config
POST   /api/v1/llm/config
GET    /api/v1/llm/prompts
POST   /api/v1/llm/prompts
PUT    /api/v1/llm/prompts/<id>
DELETE /api/v1/llm/prompts/<id>
GET    /api/v1/llm/actions
POST   /api/v1/llm/actions
PUT    /api/v1/llm/actions/<id>
DELETE /api/v1/llm/actions/<id>
POST   /api/v1/llm/test
GET    /api/v1/llm/models
GET    /api/v1/llm/providers
GET    /api/v1/llm/ollama/status
POST   /api/v1/llm/ollama/start
```

### Image API (`/api/v1/images/`)
```
GET    /api/v1/images/settings
GET    /api/v1/images/styles
GET    /api/v1/images/formats
POST   /api/v1/images/generate
DELETE /api/v1/images/settings/<id>
```

### ComfyUI API (`/api/v1/comfyui/`)
```
GET    /api/v1/comfyui/status
POST   /api/v1/comfyui/start
```

### Workflow API (`/api/v1/workflow/`)
```
GET    /api/v1/workflow/<slug>/status
POST   /api/v1/workflow/<slug>/transition
GET    /api/v1/workflow/<slug>/sub-stage/<id>
POST   /api/v1/workflow/<slug>/sub-stage
```

## Success Criteria
- [ ] All API endpoints follow the new structure
- [ ] No duplicate routes
- [ ] All frontend code uses new routes
- [ ] All documentation is updated
- [ ] No 404s in production logs
- [ ] All tests passing
- [ ] No performance regression
- [ ] All endpoints in correct blueprints
- [ ] Consistent resource naming (plural for collections, singular for individual resources)
- [ ] All image and comfyui endpoints standardized
- [ ] All LLM endpoints standardized
- [ ] All structure endpoints standardized
- [ ] All post endpoints standardized

## Rollback Plan
1. Keep old routes active but deprecated
2. Monitor error rates
3. If issues found:
   - Revert to old routes
   - Fix issues in development
   - Retry deployment

## Timeline
- Documentation Updates: 1 day
- Blueprint and Route Standardization: 2 days
- Frontend Updates: 1 day
- Testing: 2 days
- Deployment: 1 day
- Monitoring: 1 week

Total: 7 days + 1 week monitoring 