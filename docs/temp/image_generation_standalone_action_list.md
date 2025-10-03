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
- [ ] **1.4** Update main navbar to include "Imaging" stage
- [ ] **1.5** Update planning header to include Imaging stage navigation

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

### Phase 7: Update State Management
- [ ] **7.1** Create imaging-specific localStorage keys
- [ ] **7.2** Remove planning/authoring state dependencies
- [ ] **7.3** Create independent window variable management
- [ ] **7.4** Update accordion state management

### Phase 8: Testing & Cleanup
- [ ] **8.1** Test all imaging functionality independently
- [ ] **8.2** Verify no authoring/planning dependencies remain
- [ ] **8.3** Update navigation links throughout the application
- [ ] **8.4** Remove old image generation code from authoring
- [ ] **8.5** Update documentation

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
