# Image Generation Standalone Action List

## Overview
The Image Generation page currently has extensive dependencies on authoring/planning stages and needs to be made fully standalone. Additionally, it should be moved from being a sub-stage of Authoring to being part of a new Imaging stage in the main navbar.

## Current Issues
- Heavy integration with authoring/planning workflow
- Shared CSS/JS bundles causing conflicts
- Planning header with navigation to all stages
- Authoring sections panel dependency
- Mixed API endpoints (some old authoring, some new image generation)
- Shared state management (localStorage, window variables)

## Action Items

### Phase 1: Create New Imaging Stage ✅ COMPLETED
- [x] **1.1** Create new `blueprints/imaging.py` blueprint
- [x] **1.2** Register imaging blueprint in `unified_app.py`
- [x] **1.3** Create imaging route structure (`/imaging/posts/<id>/sections/image-generation`)
- [x] **1.4** Update main navbar to include "Imaging" stage
- [x] **1.5** Create unified blog pipeline header used across all stages

### Phase 2: Create Independent CSS/JS Bundles ✅ COMPLETED
- [x] **2.1** Create `static/css/imaging/` directory structure
- [x] **2.2** Create `imaging.css` bundle (extract from authoring)
- [x] **2.3** Create `static/js/imaging/` directory structure
- [x] **2.4** Create `imaging.js` bundle (extract from authoring)
- [x] **2.5** Update `macros/static_assets.html` to support imaging bundles

### Phase 3: Create Independent Components ✅ COMPLETED
- [x] **3.1** Create `templates/imaging/includes/imaging_header.html` (independent header)
- [x] **3.2** Create `templates/imaging/includes/sections_panel.html` (independent sections panel)
- [x] **3.3** Create `templates/imaging/includes/input_details.html` (independent input details)
- [x] **3.4** Create `templates/imaging/includes/llm_accordion_functions.html` (independent accordion)

### Phase 4: Create Independent JavaScript Modules ✅ COMPLETED
- [x] **4.1** Create `static/js/imaging/sections-panel.js` (independent sections panel)
- [x] **4.2** Create `static/js/imaging/image-generation-output-panel.js` (independent output panel)
- [x] **4.3** Create `static/js/imaging/image-generation.js` (independent main JS)
- [x] **4.4** Create `static/js/imaging/api.js` (independent API utilities)

### Phase 5: Create Independent API Endpoints ✅ COMPLETED
- [x] **5.1** Create `modules/image_generation/` directory structure
- [x] **5.2** Move image generation API to `modules/image_generation/api.py`
- [x] **5.3** Create `modules/image_generation/services.py` (independent services)
- [x] **5.4** Create imaging-specific post/section API endpoints
- [x] **5.5** Update all API calls to use imaging endpoints

### Phase 6: Create Independent Templates ✅ COMPLETED
- [x] **6.1** Create `templates/imaging/sections/image_generation.html` (independent main template)
- [x] **6.2** Create `templates/imaging/includes/llm_module_image_generation.html` (independent LLM module)
- [x] **6.3** Create `templates/imaging/includes/debugging_panel_image_generation.html` (independent debugging)
- [x] **6.4** Create `templates/imaging/right/output_panel_image_generation.html` (independent output)

### Phase 7: Update State Management ❌ INCOMPLETE
- [x] **7.1** Create imaging-specific localStorage keys (partially done)
- [ ] **7.2** Remove planning/authoring state dependencies (NOT DONE)
- [x] **7.3** Create independent window variable management (partially done)
- [x] **7.4** Update accordion state management (partially done)

### Phase 8: Remove ALL Dependencies ❌ CRITICAL - NOT STARTED

#### 8.1 API Endpoint Dependencies (BREAKS AUTHORING IF CHANGED)
- [ ] **8.1.1** Change `/authoring/prompts/image-generation` to `/imaging/prompts/image-generation`
  - File: `templates/imaging/includes/llm_module_image_generation.html` line 269
  - Impact: BREAKS authoring LLM prompts if changed
- [ ] **8.1.2** Change `/authoring/api/llm/save-config` to `/imaging/api/llm/save-config`
  - File: `templates/imaging/includes/llm_module_image_generation.html` line 432
  - Impact: BREAKS authoring LLM config saving if changed
- [ ] **8.1.3** Change `/authoring/api/image-generation/posts/...` to `/imaging/api/image-generation/posts/...`
  - File: `static/js/imaging/image-generation-output-panel.js` line 145
  - Impact: BREAKS authoring image generation if changed

#### 8.2 Template Dependencies (BREAKS OTHER STAGES IF CHANGED)
- [ ] **8.2.1** Remove `{% include 'authoring/includes/input_details_accordion.html' %}` from debugging panel
  - File: `templates/imaging/includes/debugging_panel_image_generation.html` line 11
  - Impact: BREAKS authoring input details if changed
- [ ] **8.2.2** Remove `{% include 'planning/includes/data_tab.html' %}` from unified header
  - File: `templates/shared/blog_pipeline_header.html` line 152
  - Impact: BREAKS planning data tab if changed
- [ ] **8.2.3** Create imaging-specific input details accordion
  - File: `templates/imaging/includes/input_details_accordion.html` (NEW)
  - Must be independent copy of authoring version
- [ ] **8.2.4** Create imaging-specific data tab
  - File: `templates/imaging/includes/data_tab.html` (NEW)
  - Must be independent copy of planning version

#### 8.3 JavaScript Dependencies (BREAKS OTHER STAGES IF CHANGED)
- [ ] **8.3.1** Remove `workflow-nav.js` dependency (planning-specific)
  - File: `templates/macros/static_assets.html` line 67
  - Impact: BREAKS planning navigation if changed
- [ ] **8.3.2** Remove `main.js` dependency (may contain authoring functions)
  - File: `templates/macros/static_assets.html` line 66
  - Impact: MAY BREAK multiple stages if changed
- [ ] **8.3.3** Create imaging-specific navigation JavaScript
  - File: `static/js/imaging/navigation.js` (NEW)
  - Must be independent copy of workflow-nav.js functionality
- [ ] **8.3.4** Create imaging-specific main JavaScript
  - File: `static/js/imaging/main.js` (NEW)
  - Must be independent copy of main.js functionality

#### 8.4 CSS Dependencies (BREAKS OTHER STAGES IF CHANGED)
- [ ] **8.4.1** Remove `nav.dist.css` dependency (planning-specific)
  - File: `templates/macros/static_assets.html` line 27
  - Impact: BREAKS planning navigation styles if changed
- [ ] **8.4.2** Remove `main.css` dependency (may contain authoring styles)
  - File: `templates/macros/static_assets.html` line 26
  - Impact: MAY BREAK multiple stages if changed
- [ ] **8.4.3** Create imaging-specific navigation CSS
  - File: `static/css/imaging/navigation.css` (NEW)
  - Must be independent copy of nav.dist.css
- [ ] **8.4.4** Create imaging-specific main CSS
  - File: `static/css/imaging/main.css` (NEW)
  - Must be independent copy of main.css

#### 8.5 Create Imaging-Specific API Endpoints (NEW ENDPOINTS NEEDED)
- [ ] **8.5.1** Create `/imaging/prompts/image-generation` endpoint
  - File: `blueprints/imaging.py` (NEW route)
  - Must duplicate authoring functionality independently
- [ ] **8.5.2** Create `/imaging/api/llm/save-config` endpoint
  - File: `blueprints/imaging.py` (NEW route)
  - Must duplicate authoring functionality independently
- [ ] **8.5.3** Create `/imaging/api/image-generation/posts/...` endpoint
  - File: `blueprints/imaging.py` (NEW route)
  - Must duplicate authoring functionality independently
- [ ] **8.5.4** Create imaging-specific LLM configuration storage
  - File: `modules/imaging/` (NEW module)
  - Must be independent from authoring LLM config

#### 8.6 Database Dependencies (BREAKS OTHER STAGES IF CHANGED)
- [ ] **8.6.1** Audit database table dependencies
  - Check if imaging uses authoring-specific tables
  - Check if imaging uses planning-specific tables
- [ ] **8.6.2** Create imaging-specific database schema if needed
  - File: `migrations/imaging_*.sql` (NEW)
  - Must be independent from authoring/planning schemas

#### 8.7 Configuration Dependencies (BREAKS OTHER STAGES IF CHANGED)
- [ ] **8.7.1** Audit environment variable dependencies
  - Check if imaging uses authoring-specific env vars
  - Check if imaging uses planning-specific env vars
- [ ] **8.7.2** Create imaging-specific configuration
  - File: `config/imaging.py` (NEW)
  - Must be independent from authoring/planning config

#### 8.8 File System Dependencies (BREAKS OTHER STAGES IF CHANGED)
- [ ] **8.8.1** Audit file path dependencies
  - Check if imaging writes to authoring-specific directories
  - Check if imaging writes to planning-specific directories
- [ ] **8.8.2** Create imaging-specific file structure
  - Directory: `static/content/imaging/` (NEW)
  - Must be independent from authoring/planning file structure

#### 8.9 Test Complete Independence
- [ ] **8.9.1** Verify imaging works without any authoring/planning files
  - Test with authoring files temporarily renamed
  - Test with planning files temporarily renamed
- [ ] **8.9.2** Verify changes to imaging don't break other stages
  - Test authoring functionality after imaging changes
  - Test planning functionality after imaging changes
- [ ] **8.9.3** Verify changes to other stages don't break imaging
  - Test imaging functionality after authoring changes
  - Test imaging functionality after planning changes
- [ ] **8.9.4** Verify imaging can be deployed independently
  - Test imaging without authoring/planning modules
  - Test imaging with minimal dependencies

### Phase 9: Testing & Cleanup
- [ ] **9.1** Test all imaging functionality independently
- [ ] **9.2** Verify no authoring/planning dependencies remain
- [ ] **9.3** Update navigation links throughout the application
- [ ] **9.4** Remove old image generation code from authoring
- [ ] **9.5** Update documentation

## Priority Order
1. **Phase 1** - Create new Imaging stage (immediate)
2. **Phase 2** - Independent CSS/JS bundles (high priority)
3. **Phase 3** - Independent components (high priority)
4. **Phase 4** - Independent JavaScript modules (medium priority)
5. **Phase 5** - Independent API endpoints (medium priority)
6. **Phase 6** - Independent templates (medium priority)
7. **Phase 7** - State management (low priority)
8. **Phase 8** - Testing & cleanup (low priority)

## Notes
- Each phase should be completed before moving to the next
- Test functionality after each phase
- Keep old code until new code is fully tested
- Update all references to image generation throughout the application
