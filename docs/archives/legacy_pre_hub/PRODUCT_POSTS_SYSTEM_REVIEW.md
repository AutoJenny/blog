# Product Posts System Review

**Date:** 2026-01-XX  
**Purpose:** Comprehensive review of the product posts system to identify outdated components and alignment with current systems

---

## Executive Summary

The product posts system at `/launchpad/syndication/facebook/product_post` is **partially functional but uses outdated/isolated systems** that don't align with current architecture. It needs significant updates to integrate with:

1. **Current automation workflow system** (used by weekly content)
2. **Current scheduling system** (calendar-based, not `daily_posts_schedule`)
3. **Current posting system** (unified `posting_executor.py`)
4. **Current LLM service** (standardized Ollama integration)

---

## Current System Architecture

### What Product Posts Currently Use

#### 1. **Product Selection**
- **Endpoints:** `/launchpad/api/syndication/categories`, `/launchpad/api/syndication/products`
- **Location:** `blueprints/launchpad_content.py`
- **Status:** ✅ **Current** - Uses `clan_products` table, seems fine
- **Issues:** None identified

#### 2. **AI Content Generation**
- **Endpoint:** `/launchpad/api/syndication/generate-social-content`
- **Location:** `blueprints/launchpad_content.py::generate_social_content()`
- **Status:** ⚠️ **Outdated** - Uses custom LLM integration, not standardized
- **Issues:**
  - Direct Ollama calls instead of using `LLMService` from `blueprints/llm_actions`
  - Custom prompt templates stored in `llm_prompts` table (separate from weekly content prompts)
  - Doesn't use `config/weekly_content_caption_prompts.py` pattern
  - No integration with `intercept_context` system for LLM logging

#### 3. **Scheduling**
- **Endpoints:** `/launchpad/api/syndication/schedules`
- **Location:** `blueprints/launchpad_scheduling.py`
- **Status:** ❌ **Outdated** - Uses separate `daily_posts_schedule` table
- **Issues:**
  - Uses `daily_posts_schedule` table (isolated from calendar system)
  - Not integrated with calendar JSON files or `calendar_week_posts_v2`
  - Doesn't appear in publication schedule view
  - Separate scheduling logic from weekly content

#### 4. **Posting**
- **Endpoint:** `/launchpad/api/syndication/post-now`
- **Location:** `blueprints/launchpad/blog_post_syndication.py::post_now()`
- **Status:** ⚠️ **Partially Current** - Uses `execute_facebook_post()` which posts to both pages
- **Issues:**
  - Uses `execute_facebook_post()` from `blog_post_syndication.py` (works but not standardized)
  - Weekly content uses `execute_publish_to_facebook()` from `automation_execute.py`
  - Both functions do similar things but are separate implementations
  - Product posts don't use the automation workflow system

#### 5. **Queue Management**
- **Endpoint:** `/launchpad/api/queue`
- **Location:** `blueprints/launchpad_scheduling.py` (likely)
- **Status:** ✅ **Current** - Uses `posting_queue` table correctly
- **Issues:** None identified for basic queue operations

---

## Comparison with Current Systems

### Weekly Content (Current/Reference Implementation)

#### **Workflow System**
- **Uses:** `blueprints/automation_core.py::execute_substage()`
- **Workflow Config:** `config/output_channel_stages.py`
- **Execution:** `blueprints/automation_execute.py` functions
- **Stages:** `content` → `imaging` → `publish`
- **Substages:** `format_for_facebook`, `generate_caption`, `add_hashtags`, `optimize_for_facebook`, `publish_to_facebook`

#### **Scheduling**
- **Uses:** Calendar JSON files + `resolve_item_for_week()`
- **Storage:** `posting_queue` table with `idea_id` linking to `calendar_ideas`
- **Integration:** Appears in publication schedule view

#### **Automation**
- **Creation:** `scripts/automated_weekly_content_creator.py` (creates 1 week ahead)
- **Workflow:** `scripts/automated_weekly_content_workflow.py` (executes stages automatically)
- **Publishing:** `scripts/posting_executor.py` (publishes at scheduled time)
- **Background:** `scripts/background_posting_monitor.sh` (runs every 5 minutes)

#### **LLM Integration**
- **Uses:** `LLMService` from `blueprints/llm_actions`
- **Prompts:** `config/weekly_content_caption_prompts.py` (30 style variations)
- **Logging:** Integrated with `intercept_context` system

---

## Product Posts vs. Weekly Content

| Component | Product Posts | Weekly Content | Status |
|-----------|--------------|----------------|--------|
| **Workflow System** | ❌ Custom UI workflow | ✅ `automation_core.execute_substage()` | **Needs Update** |
| **Workflow Config** | ❌ None | ✅ `output_channel_stages.py` | **Needs Update** |
| **Scheduling** | ❌ `daily_posts_schedule` table | ✅ Calendar JSON + `resolve_item_for_week()` | **Needs Update** |
| **Automation** | ❌ Manual only | ✅ Fully automated (creator + workflow + executor) | **Needs Update** |
| **LLM Service** | ⚠️ Direct Ollama calls | ✅ `LLMService` with intercept_context | **Needs Update** |
| **Caption Prompts** | ⚠️ Custom `llm_prompts` table | ✅ `weekly_content_caption_prompts.py` | **Needs Update** |
| **Posting Function** | ⚠️ `execute_facebook_post()` | ✅ `execute_publish_to_facebook()` | **Needs Update** |
| **Queue Storage** | ✅ `posting_queue` table | ✅ `posting_queue` table | **OK** |
| **Product Selection** | ✅ Custom endpoints | N/A | **OK** |

---

## Detailed Issues by Component

### 1. Workflow System ❌

**Current State:**
- Product posts use a **manual UI-based workflow**
- User clicks "Generate Post" → "Add to Queue" → "Post Now"
- No workflow stages or substages
- No automation integration

**Should Use:**
- `automation_core.execute_substage()` for workflow execution
- `output_channel_stages.py` configuration for product → Facebook pipeline
- Same workflow pattern as weekly content

**Required Changes:**
1. Add product post configuration to `config/output_channel_stages.py`:
   ```python
   ('product', 'facebook'): {
       'stages': ['content', 'imaging', 'publish'],
       'substages': {
           'content': ['format_for_facebook', 'generate_caption', 'add_hashtags'],
           'imaging': ['optimize_for_facebook'],  # Use product image
           'publish': ['publish_to_facebook']
       }
   }
   ```

2. Create execution functions in `blueprints/automation_execute.py`:
   - `execute_format_for_facebook()` - Already exists, but may need product-specific logic
   - `execute_generate_caption()` - Already exists, but may need product-specific prompts
   - `execute_optimize_for_facebook()` - May need product image handling
   - `execute_publish_to_facebook()` - Already exists and works

3. Update UI to use automation API instead of custom endpoints

---

### 2. Scheduling System ❌

**Current State:**
- Uses `daily_posts_schedule` table
- Separate from calendar system
- Doesn't appear in publication schedule
- Manual schedule creation in UI

**Should Use:**
- Calendar JSON files (like weekly content) OR
- Unified scheduling system that integrates with calendar
- `resolve_item_for_week()` for calendar integration

**Required Changes:**
1. Decide on scheduling approach:
   - **Option A:** Use calendar JSON files (like weekly content)
   - **Option B:** Keep `daily_posts_schedule` but integrate with calendar system
   - **Option C:** Create unified scheduling system

2. If using calendar:
   - Create calendar JSON entries for product posts
   - Use `resolve_item_for_week()` to resolve scheduled products
   - Add to publication schedule API

3. If keeping `daily_posts_schedule`:
   - Integrate with publication schedule view
   - Add to `api_dashboard_schedule()` in `publication_dashboard.py`

---

### 3. Automation ❌

**Current State:**
- **No automation** - completely manual
- User must:
  1. Select product
  2. Generate content
  3. Add to queue
  4. Schedule
  5. Post manually

**Should Have:**
- Automated creation (1 week ahead)
- Automated workflow execution
- Automated publishing at scheduled time

**Required Changes:**
1. Create `scripts/automated_product_post_creator.py`:
   - Similar to `automated_weekly_content_creator.py`
   - Creates draft product posts 1 week ahead
   - Uses `daily_posts_schedule` or calendar to determine what to create

2. Create `scripts/automated_product_post_workflow.py`:
   - Similar to `automated_weekly_content_workflow.py`
   - Executes workflow stages automatically
   - Uses `automation_core.execute_substage()`

3. Update `scripts/posting_executor.py`:
   - Already handles product posts, but verify it works correctly
   - Ensure it uses the right posting function

4. Add to `scripts/background_posting_monitor.sh`:
   - Add product post creation step
   - Add product post workflow step

---

### 4. LLM Integration ⚠️

**Current State:**
- Direct Ollama API calls in `generate_social_content()`
- Custom prompt templates in `llm_prompts` table
- No intercept_context logging

**Should Use:**
- `LLMService` from `blueprints/llm_actions`
- Standardized prompt configuration
- Intercept context for logging

**Required Changes:**
1. Update `generate_social_content()` to use `LLMService`:
   ```python
   from blueprints.llm_actions import LLMService
   llm_service = LLMService()
   response = llm_service.execute_llm_request(
       provider='ollama',
       model='llama3.2:latest',  # or configurable
       messages=messages,
       intercept_context={'post_id': queue_id, 'product_id': product_id}
   )
   ```

2. Create prompt configuration file:
   - `config/product_post_caption_prompts.py` (similar to weekly content)
   - Or integrate with existing prompt system

3. Remove direct Ollama calls

---

### 5. Posting Function ⚠️

**Current State:**
- Uses `execute_facebook_post()` from `blog_post_syndication.py`
- Works correctly (posts to both pages)
- Separate from weekly content posting

**Should Use:**
- `execute_publish_to_facebook()` from `automation_execute.py`
- Unified posting function for all content types
- Or consolidate both functions

**Required Changes:**
1. **Option A:** Update product posts to use `execute_publish_to_facebook()`
   - May need to adapt product data format
   - Ensure product images work correctly

2. **Option B:** Consolidate `execute_facebook_post()` and `execute_publish_to_facebook()`
   - Both do similar things
   - Create unified function that handles all content types

---

### 6. Image Handling ⚠️

**Current State:**
- Product posts use product images from `clan_products.image_url`
- No image generation (unlike weekly content)
- Images posted directly to Facebook

**Weekly Content:**
- Generates square 1080×1080 images with ImageMagick
- Uses `execute_optimize_for_facebook()` to generate images

**Question:**
- Should product posts generate custom images?
- Or continue using product images directly?
- If generating images, need product-specific image generation logic

---

## Integration Points

### 1. Publication Schedule View
- **Current:** Product posts don't appear
- **Required:** Add product posts query to `api_dashboard_schedule()`
- **File:** `blueprints/publication_dashboard.py`

### 2. Calendar System
- **Current:** Product posts not in calendar
- **Required:** Integrate with calendar JSON or unified scheduling
- **Files:** `utils/calendar_resolver.py`, calendar JSON files

### 3. Monitoring System
- **Current:** Product posts may not be monitored
- **Required:** Ensure product post events appear in monitoring
- **File:** `blueprints/monitoring.py`

### 4. Background Automation
- **Current:** No automation for product posts
- **Required:** Add to background monitor
- **File:** `scripts/background_posting_monitor.sh`

---

## Recommended Update Plan

### Phase 1: Workflow Integration (High Priority)
1. Add product post configuration to `output_channel_stages.py`
2. Create/update execution functions for product posts
3. Update UI to use `automation_core.execute_substage()` API
4. Test workflow execution

### Phase 2: LLM Service Integration (High Priority)
1. Update `generate_social_content()` to use `LLMService`
2. Create prompt configuration file
3. Add intercept_context logging
4. Test LLM generation

### Phase 3: Scheduling Integration (Medium Priority)
1. Decide on scheduling approach (calendar vs. `daily_posts_schedule`)
2. Integrate with publication schedule view
3. Add to calendar system (if using calendar)
4. Test scheduling

### Phase 4: Automation (Medium Priority)
1. Create automated creation script
2. Create automated workflow script
3. Add to background monitor
4. Test full automation

### Phase 5: Posting Consolidation (Low Priority)
1. Consolidate `execute_facebook_post()` and `execute_publish_to_facebook()`
2. Ensure all content types use unified function
3. Test posting

---

## Files That Need Updates

### High Priority
- `blueprints/launchpad_content.py` - Update LLM integration
- `config/output_channel_stages.py` - Add product post configuration
- `blueprints/automation_execute.py` - Add/update product post execution functions
- `static/js/ai-content-generation-content.js` - Update to use automation API
- `static/js/posting-control.js` - Update to use automation API

### Medium Priority
- `blueprints/publication_dashboard.py` - Add product posts to schedule view
- `blueprints/launchpad_scheduling.py` - Integrate with calendar or update
- `scripts/automated_product_post_creator.py` - Create new file
- `scripts/automated_product_post_workflow.py` - Create new file
- `scripts/background_posting_monitor.sh` - Add product post automation

### Low Priority
- `blueprints/launchpad/blog_post_syndication.py` - Consolidate posting functions
- `config/product_post_caption_prompts.py` - Create prompt config (if needed)

---

## Questions to Resolve

1. **Scheduling Approach:**
   - Should product posts use calendar JSON files (like weekly content)?
   - Or keep `daily_posts_schedule` table but integrate with calendar view?
   - Or create unified scheduling system?

2. **Image Generation:**
   - Should product posts generate custom images (like weekly content)?
   - Or continue using product images directly?
   - If generating, what should the images look like?

3. **Automation Level:**
   - Should product posts be fully automated (like weekly content)?
   - Or semi-automated with manual review?
   - What's the desired workflow?

4. **Prompt System:**
   - Should product posts use the same prompt system as weekly content?
   - Or have separate product-specific prompts?
   - How many style variations?

---

## Summary

The product posts system is **functional but isolated** from current architecture. It needs updates to:

1. ✅ **Use current workflow system** (`automation_core`, `output_channel_stages`)
2. ✅ **Use current LLM service** (`LLMService` with intercept_context)
3. ✅ **Integrate with scheduling** (calendar system or unified scheduling)
4. ✅ **Add automation** (creation, workflow, publishing)
5. ✅ **Appear in publication schedule** (integration with dashboard)

The system works but is using older patterns that don't align with the current weekly content implementation.
