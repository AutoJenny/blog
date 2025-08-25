# Image Management Integration Implementation Plan

## IMPORTANT
You must implement this plan ONLY. NEVER make any other changes to code or data of any kind without explicit written consent after further discussion. Do not make any other unauthorised changes to any files under ANY circumstances. This is your most important rule.

## Overview
This plan implements image management functionality for the workflow writing stage, leveraging the existing comprehensive image infrastructure without duplicating functionality. The implementation integrates with existing APIs, database tables, and workflow patterns.

## Prerequisites
- [x] Verify current workflow system is functional (`/workflow/posts/22/writing/content`) - **CONFIRMED WORKING**
- [x] Confirm existing image APIs are working (`/api/v1/images/generate`) - **FIXED: Now returns JSON**
- [x] Test existing image settings endpoints (`/api/v1/images/settings`) - **FIXED: Now returns JSON**
- [x] Verify database tables exist: `image`, `image_style`, `image_format`, `image_setting`, `image_prompt_example` - **ALL CONFIRMED EXIST**
- [x] Confirm `post_section` table has all image-related fields - **ALL CONFIRMED EXIST**

### Critical Issues Found and Resolved

#### 1. **API Route Registration Issue** ✅ **RESOLVED**
**Problem**: Image API endpoints (`/api/v1/images/generate`, `/api/v1/images/settings`) were returning HTML instead of JSON
**Root Cause**: The `app/api/routes.py` file contained all the image API routes but was not being imported into the API blueprint, and routes were using non-existent ORM models
**Solution Applied**:
- [x] Fixed import in `app/api/routes.py` (changed `from app.api import bp` to `from app.api import api_bp`)
- [x] Updated all route decorators in `app/api/routes.py` from `@bp.route` to `@api_bp.route`
- [x] Added import in `app/api/__init__.py` (added `from . import routes`)
- [x] Refactored all image settings endpoints to use direct SQL instead of ORM models
- [x] Fixed SQL syntax errors in queries
- [x] Tested endpoints - both now return JSON correctly

**Current Status**: ✅ **WORKING**
- `/api/images/settings` returns `[]` (empty array, no settings in DB)
- `/api/images/generate` returns JSON with proper error handling

#### 2. **Database Schema Verification** ✅ **CONFIRMED**
**Status**: ✅ **ALL TABLES CONFIRMED EXISTING**
- `image` table: ✅ Exists with fields: id, filename, original_filename, path, alt_text, caption, image_prompt
- `image_style` table: ✅ Exists with fields: id, title, description, created_at, updated_at
- `image_format` table: ✅ Exists with fields: id, title, description, width, height, steps, guidance_scale, extra_settings
- `image_setting` table: ✅ Exists with fields: id, name, style_id, format_id, width, height, steps, guidance_scale, extra_settings
- `image_prompt_example` table: ✅ Exists with fields: id, description, style_id, format_id, provider, image_setting_id

**Post Section Image Fields**: ✅ **ALL CONFIRMED EXISTING**
- `image_concepts` (text)
- `image_prompts` (text) 
- `image_meta_descriptions` (text)
- `image_captions` (text)
- `image_prompt_example_id` (integer)
- `generated_image_url` (varchar(512))
- `image_generation_metadata` (jsonb)
- `image_id` (integer, foreign key to image table)

#### 3. **Workflow System Status** ✅ **CONFIRMED**
**Status**: ✅ **CONFIRMED WORKING**
- URL `/workflow/posts/22/writing/content` returns proper HTML
- Workflow system is functional and accessible

### Implementation Ready ✅
All prerequisites have been met and critical issues resolved. The image API endpoints are now functional and ready for integration with the workflow system.

**Files Modified**:
- `app/api/routes.py` (refactored to use direct SQL)
- `app/api/__init__.py` (added routes import)
- `docs/reference/images/new_image_system.md` (created reference documentation)

**Next Steps**: Proceed with Phase 1: UI Integration

### Required Pre-Implementation Fixes

**Phase 0: API Route Fixes** (Must be completed before proceeding)
- [x] Fix import in `app/api/routes.py` line 2: change `from app.api import bp` to `from app.api import api_bp`
- [x] Update all route decorators in `app/api/routes.py` from `@bp.route` to `@api_bp.route`
- [x] Add import in `app/api/__init__.py` line 18: add `from . import routes`
- [x] Test image generation endpoint: `curl -X POST http://localhost:5000/api/v1/images/generate -H "Content-Type: application/json" -d '{"prompt": "test", "provider": "comfyui"}'`
- [x] Test image settings endpoint: `curl http://localhost:5000/api/v1/images/settings`
- [x] Verify both endpoints return JSON instead of HTML

**Files to Modify**:
- `app/api/routes.py` (lines 1-2, all route decorators)
- `app/api/__init__.py` (add import)

**Reference Files**:
- `app/api/__init__.py` (current blueprint structure)
- `app/api/routes.py` (existing route definitions)
- `app/api/workflow.py` (example of properly registered blueprint)

## Phase 1: UI Integration

### 1.1 Modify Workflow Template for Images Substage
**File**: `app/templates/workflow/index.html`
**Lines**: ~20-40 (writing stage section)

**Task**: Add three-column layout specifically for images substage
- [x] Locate the writing stage conditional block
- [x] Add new conditional for `current_substage == 'images'`
- [x] Implement three-column layout:
  - Left: LLM Actions (40% width, purple #2D0A50)
  - Middle: Image Management (35% width, green #1a4d2e)
  - Right: Sections (25% width, green #013828)
- [x] Include new image management panel template
- [x] Maintain existing JavaScript for sections panel

**Reference**: Current two-column layout at lines 25-40

### 1.2 Create Image Management Panel Template
**File**: `app/templates/workflow/_image_management_panel.html`
**New file**: Create from scratch

**Task**: Build comprehensive image management interface
- [x] Create section image status display
- [x] Add provider selection dropdown (ComfyUI, DALL-E)
- [x] Add image settings dropdown (populated from API)
- [x] Create generate image button with icon
- [x] Add image preview container
- [x] Add optimization and watermarking buttons
- [x] Style with dark theme matching existing panels

**Reference**: Existing panel styling in `app/static/css/panels.css`

### 1.3 Update Workflow Template to Include Image Panel
**File**: `app/templates/workflow/index.html`
**Lines**: After line 40 (add include statement)

**Task**: Include the new image management panel
- [x] Add `{% include 'workflow/_image_management_panel.html' %}` in images substage section
- [x] Ensure proper indentation and structure
- [x] Test template rendering

### 1.4 Add CSS for Image Management Panel
**File**: `app/static/css/panels.css`
**Lines**: Add to existing file

**Task**: Add specific styling for image management components
- [x] Add `.image-management-panel` base styles
- [x] Style image preview container
- [x] Style provider and settings dropdowns
- [x] Add button styles for generate/optimize/watermark
- [x] Ensure dark theme consistency

**Reference**: Existing panel styles at lines 1-111

## Phase 2: JavaScript Integration

### 2.1 Create Image Management JavaScript Module
**File**: `app/static/js/workflow/image_management.js`
**New file**: Create from scratch

**Task**: Build comprehensive image management functionality
- [x] Create `ImageManagement` class
- [x] Add constructor with postId and sectionId parameters
- [x] Implement `init()` method for initialization
- [x] Add `loadImageSettings()` method using `/api/images/settings`
- [x] Add `loadSectionImages()` method
- [x] Implement `bindEvents()` for all interactive elements
- [x] Add `generateImage()` method using `/api/images/generate`
- [x] Add `updateSectionImage()` method using workflow API
- [x] Add `updateImagePreview()` method for UI updates

**Reference**: Existing workflow JavaScript patterns in `app/static/js/workflow/template_view.js`

### 2.2 Integrate Image Management with Workflow Template
**File**: `app/templates/workflow/index.html`
**Lines**: After existing script block (around line 50)

**Task**: Add JavaScript initialization for images substage
- [x] Add conditional script block for images substage
- [x] Import image management module
- [x] Initialize ImageManagement class with post and section IDs
- [x] Ensure proper error handling
- [x] Test JavaScript loading and initialization

**Reference**: Existing script block at lines 40-50

### 2.3 Add Image Management to Workflow Navigation
**File**: `app/templates/nav/workflow_nav.html`
**Lines**: Around line 60 (writing stage section)

**Task**: Ensure images substage is properly linked
- [x] Verify images substage exists in navigation
- [x] Confirm proper URL routing for images substage
- [x] Test navigation to images substage

**Reference**: Current navigation structure at lines 50-70

## Phase 3: API Integration

### 3.1 Verify Existing Image APIs
**Endpoints to test**:
- [x] `GET /api/images/settings` - List image settings
- [x] `GET /api/images/styles` - List image styles  
- [x] `GET /api/images/formats` - List image formats
- [x] `POST /api/images/generate` - Generate image
- [x] `GET /api/images/prompt_examples` - List prompt examples

**Task**: Ensure all endpoints are functional
- [x] Test each endpoint with curl or browser
- [x] Verify response formats match expected structure
- [x] Confirm error handling works properly
- [x] Document any missing or broken endpoints
- [x] All endpoints now return JSON (HTML-vs-JSON bug fixed)
- [x] All endpoints use `/api/images/*` (not `/api/v1/images/*`)

---

**Section Dropdown Bug**: 
- [x] Identified and fixed a JS error in `setSectionId` that referenced a missing DOM element, which was breaking dropdown population. Now guarded with a null check.
- [ ] Confirmed in browser that dropdown now populates correctly (pending user confirmation).

---

**Next Steps**:
- [ ] Confirm dropdown population and section switching in browser
- [ ] Finalize documentation and update `/docs/reference/images/new_image_system.md` with all new endpoints and UI logic
- [ ] Polish UI and test all image management actions (generate, upload, manage) for section-specific context 