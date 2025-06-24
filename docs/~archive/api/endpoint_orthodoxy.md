# API Endpoint Orthodoxy Review and Implementation Plan

## Overview
This document outlines the current state of our API endpoints, identifies inconsistencies with our canonical API design, and provides a structured plan for bringing all endpoints into alignment with our API standards.

## Current State

### Canonical Endpoint Schema
Our API follows these standard patterns:
- Base URL: `/api/v1/`
- Resource naming: Plural form (e.g., `/posts/` not `/post/`)
- Consistent HTTP methods for CRUD operations
- Standard response formats

### Identified Issues

#### 1. Blueprint Mismatch
- **Issue**: API endpoints intended for `/api/v1/` are incorrectly placed in the `blog` blueprint
- **Affected Endpoints**:
  - `/api/v1/structure/plan`
  - `/api/v1/structure/plan_and_save`
  - `/api/v1/post/<post_id>/structure`

#### 2. Inconsistent Resource Naming
- **Issue**: Mixing singular and plural forms
- **Examples**:
  - `/api/v1/post/` vs `/api/v1/posts/`
  - `/api/v1/post_development/fields` (non-standard pattern)

#### 3. Missing Canonical Endpoints
- **Issue**: Some documented endpoints are not implemented
- **Missing**: `/api/v1/structure/save/<post_id>`

#### 4. Non-Standard Endpoints
- **Issue**: Some endpoints don't follow our canonical schema
- **Example**: `/api/v1/structure/plan_and_save` (not documented)

## Implementation Plan

### Phase 1: Immediate Fixes
1. Move structure-related endpoints to correct blueprint
   - [ ] Move `/api/v1/structure/plan` to `app/api/routes.py`
   - [ ] Move `/api/v1/structure/plan_and_save` to `app/api/routes.py`
   - [ ] Update all imports and dependencies

2. Update endpoint documentation
   - [ ] Update `docs/api/structure_stage.md`
   - [ ] Update `docs/api/structure.md`
   - [ ] Update API README

### Phase 2: Standardization
1. Resource naming standardization
   - [ ] Convert all singular resource names to plural
   - [ ] Update all related documentation
   - [ ] Update frontend API calls

2. Implement missing canonical endpoints
   - [ ] Implement `/api/v1/structure/save/<post_id>`
   - [ ] Add proper validation and error handling
   - [ ] Update documentation

3. Deprecate non-standard endpoints
   - [ ] Mark `/api/v1/structure/plan_and_save` as deprecated
   - [ ] Create migration plan for existing clients
   - [ ] Set deprecation timeline

### Phase 3: Testing and Validation
1. API testing
   - [ ] Create/update test suite for all endpoints
   - [ ] Verify response formats
   - [ ] Test error handling

2. Documentation updates
   - [ ] Update OpenAPI/Swagger documentation
   - [ ] Update API client examples
   - [ ] Update integration guides

## Timeline
- Phase 1: Immediate (1-2 days)
- Phase 2: Short-term (1 week)
- Phase 3: Ongoing (as part of regular development)

## Success Criteria
- All endpoints follow canonical schema
- Documentation is complete and accurate
- All tests pass
- No deprecated endpoints in active use
- Consistent resource naming across all endpoints

## Notes
- Maintain backward compatibility during transition
- Update all related frontend code
- Monitor API usage during changes
- Document any breaking changes 