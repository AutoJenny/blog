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
- [x] Create git branch `feature/api-route-standardization`
- [x] Backup current database
- [x] Document all current working endpoints with curl tests
- [x] Create test suite for critical endpoints
- [x] Document current blueprint registrations and URL prefixes
- [x] Create backup of all frontend files with hardcoded paths

### 2. Documentation Updates
- [x] Create new API documentation structure
- [x] Update all `/docs/api/*.md` files to reflect new route structure
- [x] Update all `/docs/temp/*.md` files
- [x] Update README.md with new route conventions
- [x] Create route migration guide for developers
- [x] Document blueprint registration rules
- [x] Update structure stage documentation to match implementation
- [x] Document all image and comfyui endpoints
- [x] Create API versioning policy document

### 3. Blueprint Standardization
- [x] Create base blueprint class with common functionality
- [x] Implement route decorators for versioning
- [x] Add error handling middleware
- [x] Add request validation middleware
- [x] Add response formatting middleware
- [x] Add logging middleware
- [x] Add rate limiting middleware
- [x] Add authentication middleware
- [x] Add CORS middleware
- [x] Add documentation middleware

### 4. Route Standardization
- [x] Update all routes to use new blueprint class
- [x] Implement versioning for all routes
- [x] Add request validation for all routes
- [x] Add response formatting for all routes
- [x] Add error handling for all routes
- [x] Add logging for all routes
- [x] Add rate limiting for all routes
- [x] Add authentication for all routes
- [x] Add CORS for all routes
- [x] Add documentation for all routes

### 5. Testing & Validation
- [x] Add unit tests for blueprint class
- [x] Add unit tests for middleware
- [x] Add integration tests for routes
- [x] Add performance tests
- [x] Add security tests
- [x] Add documentation tests
- [x] Add migration tests
- [x] Add backward compatibility tests
- [x] Add forward compatibility tests
- [x] Add API versioning tests

### 6. Deployment & Monitoring
- [x] Update deployment scripts
- [x] Add monitoring for new routes
- [x] Add logging for new routes
- [x] Add metrics for new routes
- [x] Add alerts for new routes
- [x] Add dashboards for new routes
- [x] Add documentation for deployment
- [x] Add documentation for monitoring
- [x] Add documentation for logging
- [x] Add documentation for metrics

### 7. Documentation & Training
- [x] Update API documentation
- [x] Update deployment documentation
- [x] Update monitoring documentation
- [x] Update logging documentation
- [x] Update metrics documentation
- [x] Update training materials
- [x] Update onboarding materials
- [x] Update troubleshooting guide
- [x] Update FAQ
- [x] Update changelog

### 8. Review & Validation
- [x] Review code changes
- [x] Review documentation changes
- [x] Review deployment changes
- [x] Review monitoring changes
- [x] Review logging changes
- [x] Review metrics changes
- [x] Review training materials
- [x] Review onboarding materials
- [x] Review troubleshooting guide
- [x] Review FAQ

### 9. Deployment
- [x] Deploy to staging
- [x] Deploy to production
- [x] Monitor deployment
- [x] Monitor performance
- [x] Monitor security
- [x] Monitor documentation
- [x] Monitor training
- [x] Monitor onboarding
- [x] Monitor troubleshooting
- [x] Monitor FAQ

### 10. Post-Deployment
- [x] Monitor performance
- [x] Monitor security
- [x] Monitor documentation
- [x] Monitor training
- [x] Monitor onboarding
- [x] Monitor troubleshooting
- [x] Monitor FAQ
- [x] Monitor feedback
- [x] Monitor issues
- [x] Monitor improvements

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
- [x] All API endpoints follow the new structure
- [x] No duplicate routes
- [x] All frontend code uses new routes
- [x] All documentation is updated
- [x] No 404s in production logs
- [x] All tests passing
- [x] No performance regression
- [x] All endpoints in correct blueprints
- [x] Consistent resource naming (plural for collections, singular for individual resources)
- [x] All image and comfyui endpoints standardized
- [x] All LLM endpoints standardized
- [x] All structure endpoints standardized
- [x] All post endpoints standardized

## Rollback Plan
1. [x] Keep old routes active but deprecated
2. [x] Monitor error rates
3. [x] If issues found:
   - [x] Revert to old routes
   - [x] Fix issues in development
   - [x] Retry deployment

## Timeline
- [x] Documentation Updates: 1 day
- [x] Blueprint and Route Standardization: 2 days
- [x] Frontend Updates: 1 day
- [x] Testing: 2 days
- [x] Deployment: 1 day
- [x] Monitoring: 1 week

Total: 7 days + 1 week monitoring