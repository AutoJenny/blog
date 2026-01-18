# Product Posts Automation - Current Status

**Date:** 2026-01-18  
**Status:** 🔴 **NOT AUTOMATED** - Product posts are completely manual

---

## Where We Are

### ✅ What's Working (Manual)
- Product selection UI works
- Content generation works (but uses outdated LLM integration)
- Posting queue management works
- Manual posting to Facebook works
- Product posts appear in calendar view (recently added)

### ❌ What's Missing (Automation)
- **No automated creation** - Must manually create posts
- **No automated workflow** - Must manually run each step
- **No automated scheduling** - Uses outdated `daily_posts_schedule` table
- **No background automation** - Not integrated with `background_posting_monitor.sh`

---

## What Needs to Be Done

Based on `PRODUCT_POSTS_SYSTEM_REVIEW.md`, here's the plan:

### Phase 1: Workflow Integration ⚠️ **NOT STARTED**
**Priority:** High

1. ✅ Add product post config to `config/output_channel_stages.py`
   - Status: **NOT DONE** - No `('product', 'facebook')` entry exists
   
2. ✅ Create/update execution functions for product posts
   - Status: **PARTIALLY DONE** - Functions exist but only handle weekly content
   - Need: Product-specific logic in `execute_format_for_facebook()`, `execute_generate_caption()`, etc.
   
3. ✅ Update UI to use automation API
   - Status: **NOT DONE** - UI still uses custom endpoints
   
4. ✅ Test workflow execution
   - Status: **NOT DONE**

### Phase 2: LLM Service Integration ⚠️ **NOT STARTED**
**Priority:** High

1. ✅ Update `generate_social_content()` to use `LLMService`
   - Status: **NOT DONE** - Still uses direct Ollama calls
   - File: `blueprints/launchpad_content.py`
   
2. ✅ Create prompt configuration file
   - Status: **NOT DONE** - No `config/product_post_caption_prompts.py`
   
3. ✅ Add intercept_context logging
   - Status: **NOT DONE**

### Phase 3: Scheduling Integration 🟡 **PARTIALLY DONE**
**Priority:** Medium

1. ✅ Decide on scheduling approach
   - Status: **PARTIALLY DONE** - Product posts appear in calendar, but still use `daily_posts_schedule`
   - Question: Use calendar JSON files (like weekly content) or keep `daily_posts_schedule`?
   
2. ✅ Integrate with publication schedule view
   - Status: **PARTIALLY DONE** - Product posts appear in calendar view
   - File: `blueprints/planning_api_calendar_schedule.py` (already queries product posts)
   
3. ✅ Add to calendar system
   - Status: **PARTIALLY DONE** - Product posts appear in calendar, but not fully integrated

### Phase 4: Automation 🔴 **NOT STARTED**
**Priority:** Medium

1. ✅ Create `scripts/automated_product_post_creator.py`
   - Status: **NOT DONE** - Script doesn't exist
   - Should: Create draft product posts 1 week ahead (like `automated_weekly_content_creator.py`)
   
2. ✅ Create `scripts/automated_product_post_workflow.py`
   - Status: **NOT DONE** - Script doesn't exist
   - Should: Execute workflow stages automatically (like `automated_weekly_content_workflow.py`)
   
3. ✅ Add to `scripts/background_posting_monitor.sh`
   - Status: **NOT DONE** - Product post automation not in monitor
   - Should: Add product post creation and workflow steps

### Phase 5: Posting Consolidation ⚠️ **NOT STARTED**
**Priority:** Low

1. ✅ Consolidate `execute_facebook_post()` and `execute_publish_to_facebook()`
   - Status: **NOT DONE** - Still using separate functions
   - Product posts use `execute_facebook_post()` (works but not standardized)
   - Weekly content uses `execute_publish_to_facebook()` (standardized)

---

## Current Architecture Gaps

### 1. Workflow System
- **Current:** Manual UI workflow (click buttons)
- **Needed:** Automated workflow using `automation_core.execute_substage()`
- **Gap:** No product post config in `output_channel_stages.py`

### 2. LLM Integration
- **Current:** Direct Ollama calls in `launchpad_content.py`
- **Needed:** Standardized `LLMService` with intercept_context
- **Gap:** `generate_social_content()` needs refactoring

### 3. Scheduling
- **Current:** `daily_posts_schedule` table (isolated)
- **Needed:** Calendar integration or unified scheduling
- **Gap:** Decision needed on approach

### 4. Automation Scripts
- **Current:** None exist
- **Needed:** Creator + workflow scripts
- **Gap:** Scripts need to be created from scratch

---

## Next Steps

**Recommended starting point:** Phase 1 (Workflow Integration)

1. Add product post config to `output_channel_stages.py`
2. Extend execution functions to handle product posts
3. Test workflow execution manually
4. Then move to Phase 2 (LLM integration)
5. Then Phase 4 (Automation scripts)

---

## Reference Implementation

Weekly content is the **reference implementation** for how product posts should work:
- ✅ Fully automated
- ✅ Uses workflow system
- ✅ Uses standardized LLM service
- ✅ Integrated with calendar
- ✅ Background automation

Product posts should follow the same pattern.
