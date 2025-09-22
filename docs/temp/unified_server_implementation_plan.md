# Unified Server Implementation Plan

## Overview
This document outlines the step-by-step implementation plan for reunifying all microservices into a single Flask application, with benchmarks and checkboxes for tracking progress.

## Current Architecture Status
- **blog-core** (Port 5000) - ✅ Running
- **blog-launchpad** (Port 5001) - ✅ Running  
- **blog-llm-actions** (Port 5002) - ✅ Running
- **blog-post-sections** (Port 5003) - ❌ Not running
- **blog-post-info** (Port 5004) - ❌ Not running
- **blog-images** (Port 5005) - ❌ Not running
- **blog-clan-api** (Port 5007) - ❌ Not running

## Phase 1: Foundation Setup

### 1.1 Create Unified Application Structure
- [ ] Create `unified_app.py` main application file
- [ ] Create `blueprints/` directory structure
- [ ] Create `services/` directory for shared business logic
- [ ] Create `utils/` directory for shared utilities
- [ ] Create `config/` directory for configuration files

**Benchmark**: Directory structure created and main app file exists
**Test**: `ls -la unified_app.py blueprints/ services/ utils/ config/`

### 1.2 Consolidate Dependencies
- [ ] Create unified `requirements.txt` with all dependencies
- [ ] Resolve version conflicts (Flask 2.3.3 vs 3.0.0)
- [ ] Update psycopg2 to psycopg3 consistently
- [ ] Install all dependencies in unified environment

**Benchmark**: Single requirements.txt with resolved versions
**Test**: `pip install -r requirements.txt` succeeds without conflicts

### 1.3 Database Connection Unification
- [ ] Create `services/database.py` with unified connection logic
- [ ] Update all services to use unified database connection
- [ ] Test database connectivity from unified app
- [ ] Verify all database operations work

**Benchmark**: All services can connect to database through unified service
**Test**: `python -c "from services.database import get_db_conn; conn = get_db_conn(); print('Connected')"`

## Phase 2: Blueprint Migration

### 2.1 Core Blueprint (blog-core)
- [ ] Create `blueprints/core.py` with all core routes
- [ ] Move workflow routes from `blog-core/app.py`
- [ ] Move database routes from `blog-core/routes.py`
- [ ] Move settings routes from `blog-core/settings.py`
- [ ] Test all core functionality

**Benchmark**: All core routes accessible via `/core/` prefix
**Test**: `curl http://localhost:5000/core/` returns homepage

### 2.2 Launchpad Blueprint (blog-launchpad)
- [ ] Create `blueprints/launchpad.py` with syndication routes
- [ ] Move all API routes from `blog-launchpad/app.py`
- [ ] Move social media functionality
- [ ] Test syndication features

**Benchmark**: All launchpad routes accessible via `/launchpad/` prefix
**Test**: `curl http://localhost:5000/launchpad/syndication` returns syndication page

### 2.3 LLM Actions Blueprint (blog-llm-actions)
- [ ] Create `blueprints/llm_actions.py` with LLM routes
- [ ] Move all API routes from `blog-llm-actions/app.py`
- [ ] Move LLM processing logic
- [ ] Test LLM functionality

**Benchmark**: All LLM routes accessible via `/llm-actions/` prefix
**Test**: `curl http://localhost:5000/llm-actions/api/run-llm` returns LLM response

### 2.4 Additional Blueprints
- [ ] Create `blueprints/post_sections.py` (blog-post-sections)
- [ ] Create `blueprints/post_info.py` (blog-post-info)
- [ ] Create `blueprints/images.py` (blog-images)
- [ ] Create `blueprints/clan_api.py` (blog-clan-api)

**Benchmark**: All service blueprints created and registered
**Test**: All blueprint routes return 200 status codes

## Phase 3: Static Assets Consolidation

### 3.1 CSS Consolidation
- [ ] Merge all CSS files into `static/css/`
- [ ] Resolve CSS conflicts between services
- [ ] Update template references to use unified paths
- [ ] Test visual consistency

**Benchmark**: All CSS files consolidated and templates render correctly
**Test**: All pages load with proper styling

### 3.2 JavaScript Consolidation
- [ ] Merge all JavaScript files into `static/js/`
- [ ] Update API calls to use unified endpoints
- [ ] Remove hardcoded port references
- [ ] Test JavaScript functionality

**Benchmark**: All JavaScript files consolidated and API calls work
**Test**: All interactive features work without cross-origin errors

### 3.3 Template Consolidation
- [ ] Move all templates to `templates/` with service subdirectories
- [ ] Update template inheritance and includes
- [ ] Resolve template conflicts
- [ ] Test template rendering

**Benchmark**: All templates consolidated and render correctly
**Test**: All pages render without template errors

## Phase 4: Configuration Unification

### 4.1 Environment Configuration
- [ ] Create `config/settings.py` with unified configuration
- [ ] Create `config/assistant_config.env` with all settings
- [ ] Update all services to use unified configuration
- [ ] Test configuration loading

**Benchmark**: Single configuration system for all services
**Test**: All services load configuration without errors

### 4.2 CORS Removal
- [ ] Remove all CORS configurations
- [ ] Update JavaScript to use same-origin requests
- [ ] Remove cross-origin headers
- [ ] Test same-origin functionality

**Benchmark**: No CORS configurations needed
**Test**: All API calls work without CORS errors

## Phase 5: Testing and Validation

### 5.1 Unit Tests
- [ ] Test each blueprint independently
- [ ] Test database connections
- [ ] Test API endpoints
- [ ] Test template rendering

**Benchmark**: All unit tests pass
**Test**: `python -m pytest tests/` returns 100% pass rate

### 5.2 Integration Tests
- [ ] Test workflow functionality end-to-end
- [ ] Test LLM processing workflow
- [ ] Test syndication features
- [ ] Test database operations

**Benchmark**: All integration tests pass
**Test**: Complete user workflows work without errors

### 5.3 Performance Tests
- [ ] Load testing with multiple concurrent users
- [ ] Memory usage monitoring
- [ ] Response time validation
- [ ] Database query optimization

**Benchmark**: Performance meets or exceeds current microservices
**Test**: Load test results show acceptable performance

## Phase 6: Deployment and Migration

### 6.1 Staging Deployment
- [ ] Deploy unified app to staging environment
- [ ] Test all functionality in staging
- [ ] Compare performance with current setup
- [ ] Fix any issues found

**Benchmark**: Unified app running in staging
**Test**: All features work in staging environment

### 6.2 Production Migration
- [ ] Backup current microservices
- [ ] Deploy unified app to production
- [ ] Switch traffic to unified app
- [ ] Monitor for issues

**Benchmark**: Unified app running in production
**Test**: All production features work correctly

### 6.3 Cleanup
- [ ] Remove old microservice code
- [ ] Update documentation
- [ ] Update deployment scripts
- [ ] Archive old services

**Benchmark**: Clean codebase with only unified app
**Test**: No references to old microservices remain

## Success Criteria

### Functional Requirements
- [ ] All current functionality preserved
- [ ] All API endpoints working
- [ ] All templates rendering correctly
- [ ] All JavaScript functionality working
- [ ] Database operations working
- [ ] LLM processing working
- [ ] Syndication features working

### Performance Requirements
- [ ] Response times ≤ current microservices
- [ ] Memory usage ≤ sum of all microservices
- [ ] CPU usage ≤ sum of all microservices
- [ ] Database connections ≤ current total

### Maintainability Requirements
- [ ] Single codebase to maintain
- [ ] Unified configuration system
- [ ] Consistent error handling
- [ ] Comprehensive logging
- [ ] Easy deployment process

## Risk Mitigation

### Backup Strategy
- [ ] Full database backup before migration
- [ ] Code repository backup
- [ ] Configuration file backup
- [ ] Static assets backup

### Rollback Plan
- [ ] Keep existing services running during migration
- [ ] Database rollback procedures
- [ ] Configuration rollback procedures
- [ ] Code rollback procedures

### Monitoring
- [ ] Application performance monitoring
- [ ] Error rate monitoring
- [ ] Database performance monitoring
- [ ] User experience monitoring

## Timeline

- **Phase 1**: 1 day
- **Phase 2**: 2 days
- **Phase 3**: 1 day
- **Phase 4**: 0.5 days
- **Phase 5**: 1 day
- **Phase 6**: 1 day
- **Total**: 6.5 days

## Next Steps

1. Start with Phase 1.1 - Create unified application structure
2. Set up development environment
3. Begin blueprint migration
4. Test each phase thoroughly before proceeding
5. Document any issues or changes encountered

---

**Last Updated**: 2025-09-22
**Status**: Ready to begin implementation
**Assigned**: AI Assistant
