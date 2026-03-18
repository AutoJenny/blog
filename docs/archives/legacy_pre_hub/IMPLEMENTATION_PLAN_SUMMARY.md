# Implementation Plan Summary - One-Click Publication System

**Date:** 2025-01-XX  
**Purpose:** Complete breakdown of stages and substages to deliver a working multi-channel publication platform

---

## Overview

This plan delivers a complete **One-Click Publication** system that:
- Supports all post types (themed, recipe, profile, weekly_word, weekly_phrase, weekly_insult)
- Publishes to multiple channels (blog, Facebook, Instagram, Twitter, Newsletter)
- Provides channel-specific production pipelines
- Includes review gates and manual intervention
- Integrates with the new calendar scheduling system

---

## Phase 1: Foundation & Configuration (CRITICAL - Must Complete First)

**Goal:** Establish configuration infrastructure that all other phases depend on

### Stage 1.1: Add Weekly Content Types to Post Type Config
**File:** `config/post_type_substages.py`

**Substages:**
1. Add `weekly_word` to `POST_TYPE_SUBSTAGES` dict
   - Stages: `calendar`, `content`, `header`
   - Substages: `view`, `format_content`, `title_summary`
2. Add `weekly_phrase` to `POST_TYPE_SUBSTAGES` dict
   - Stages: `calendar`, `content`, `header`
   - Substages: `view`, `format_content`, `title_summary`
3. Add `weekly_insult` to `POST_TYPE_SUBSTAGES` dict
   - Stages: `calendar`, `content`, `header`
   - Substages: `view`, `format_content`, `title_summary`
4. Add substage metadata for new substages (if needed)
5. Test: Verify `get_substages_for_post_type()` returns correct data

**Dependencies:** None  
**Blocks:** Phase 2, Phase 3

---

### Stage 1.2: Create Output Channel Stage Configuration System
**File:** `config/output_channel_stages.py` (NEW FILE)

**Substages:**
1. Create file structure with `OUTPUT_CHANNEL_STAGES` dict
2. Define blog output configs (fallback to post_type_substages)
   - `('themed', 'blog')`: use_post_type_config = True
   - `('recipe', 'blog')`: use_post_type_config = True
   - `('profile', 'blog')`: use_post_type_config = True
   - `('weekly_word', 'blog')`: use_post_type_config = True
   - `('weekly_phrase', 'blog')`: use_post_type_config = True
   - `('weekly_insult', 'blog')`: use_post_type_config = True
3. Define Facebook output configs (minimal pipelines)
   - `('weekly_word', 'facebook')`: stages = ['content', 'imaging', 'publish']
   - `('weekly_phrase', 'facebook')`: stages = ['content', 'imaging', 'publish']
   - `('weekly_insult', 'facebook')`: stages = ['content', 'imaging', 'publish']
   - `('themed', 'facebook')`: stages = ['syndication'] (reuse blog content)
   - `('recipe', 'facebook')`: stages = ['syndication']
   - `('profile', 'facebook')`: stages = ['syndication']
4. Define Instagram output configs
   - `('weekly_word', 'instagram')`: stages = ['content', 'imaging', 'publish']
   - Similar for other weekly content types
5. Define Twitter output configs (minimal)
6. Define Newsletter output configs (syndication)
7. Create `get_stages_for_output(post_type, output_channel)` function
   - Resolves (post_type, output_channel) → stages/substages
   - Falls back to post_type config for blog
   - Returns minimal default for unknown combinations
8. Create `get_minimal_social_media_pipeline()` helper
9. Test: Verify resolution logic for all combinations

**Dependencies:** Stage 1.1  
**Blocks:** Phase 2, Phase 3

---

### Stage 1.3: Update Post Type Pipeline Configs (if needed)
**File:** `config/post_type_pipeline_configs.py`

**Substages:**
1. Review if pipeline configs need channel awareness
2. Add weekly content type pipeline configs (if missing)
3. Test: Verify pipeline steps resolve correctly

**Dependencies:** Stage 1.1  
**Blocks:** None (optional)

---

## Phase 2: Backend Core Functionality

**Goal:** Implement backend APIs and logic for channel-aware pipeline execution

### Stage 2.1: Fix Calendar Sync in One-Click Publication
**File:** `blueprints/automation_calendar.py`

**Substages:**
1. Locate `/next-up` endpoint
2. Replace deprecated table queries (`calendar_weeks`, `calendar_ideas`, etc.)
3. Use `utils/calendar_resolver.py` to resolve items for current week
4. Update response format to match new calendar system
5. Test: Verify endpoint returns correct items from new calendar system
6. Test: Verify no references to deprecated tables

**Dependencies:** None (calendar system already exists)  
**Blocks:** Phase 3 (UI needs correct data)

---

### Stage 2.2: Update Pipeline API for Output Channel Support
**File:** `blueprints/automation_core.py`

**Substages:**
1. Update `GET /launchpad/one-click-publication/api/pipeline-status/<post_id>`
   - Add `output` query parameter (optional, defaults to 'blog')
   - Use `get_stages_for_output()` to resolve stages
   - Return channel-specific stages in response
2. Update `POST /launchpad/one-click-publication/api/execute-substage/<stage>/<substage>`
   - Add `output` parameter to request body
   - Validate substage exists for (post_type, output_channel)
   - Execute substage with channel context
3. Update `POST /launchpad/one-click-publication/api/skip-substage/<post_id>`
   - Add `output` parameter
   - Skip with channel context
4. Create `GET /launchpad/one-click-publication/api/pipeline/<post_id>?output=<channel>` (NEW)
   - Returns full pipeline definition for (post_type, output_channel)
5. Test: Verify all endpoints accept and use `output` parameter
6. Test: Verify channel-specific stages are returned correctly

**Dependencies:** Stage 1.2 (output channel config)  
**Blocks:** Phase 3 (UI needs API support)

---

### Stage 2.3: Create Output Channel Stage Resolution Helpers
**File:** `utils/output_channel_resolver.py` (NEW FILE)

**Substages:**
1. Create helper module
2. Implement `resolve_pipeline_for_output(post_id, output_channel)`
   - Gets post_type from post
   - Calls `get_stages_for_output(post_type, output_channel)`
   - Returns full pipeline with metadata
3. Implement `validate_substage_for_output(post_id, stage, substage, output_channel)`
   - Checks if substage exists for (post_type, output_channel)
4. Implement `get_available_output_channels(post_id)`
   - Returns list of channels available for this post type
5. Test: Verify all helper functions work correctly

**Dependencies:** Stage 1.2  
**Blocks:** Stage 2.2

---

### Stage 2.4: Update Automation Core for Channel-Specific Execution
**File:** `blueprints/automation_core.py`

**Substages:**
1. Update substage execution functions to accept `output_channel` parameter
2. Modify execution logic to use channel-specific stages
3. Update pipeline status tracking to be channel-aware
4. Ensure backward compatibility (default to 'blog' if not specified)
5. Test: Verify channel-specific execution works
6. Test: Verify backward compatibility maintained

**Dependencies:** Stage 2.2, Stage 2.3  
**Blocks:** Phase 3

---

## Phase 3: Database Schema (Can Run in Parallel with Phase 2)

**Goal:** Create database tables for channel assignment, approval, and publication tracking

### Stage 3.1: Create Channel Assignment Tables
**Files:** Database migration scripts

**Substages:**
1. Create `post_type_channel_config` table
   - Columns: id, post_type, channel, is_primary, is_required, publication_delay_hours, publication_time, is_active, timestamps
   - Unique constraint: (post_type, channel)
   - Check constraint: channel IN ('blog', 'facebook', 'instagram', 'twitter', 'newsletter')
2. Create `calendar_item_channels` table
   - Columns: id, category, item_id, year, week_number, channels (JSONB array), is_override, created_at, updated_at
   - Unique constraint: (category, item_id, year, week_number)
3. Populate `post_type_channel_config` with default assignments
   - themed → blog (primary), facebook, newsletter
   - recipe → blog (primary), facebook
   - weekly_word → facebook (primary), instagram
   - weekly_phrase → facebook (primary), twitter
   - weekly_insult → facebook (primary), twitter
   - profile → blog (primary)
4. Test: Verify tables created correctly
5. Test: Verify default data populated

**Dependencies:** None  
**Blocks:** Stage 3.2, Phase 4

---

### Stage 3.2: Create Approval & Publication Tracking Tables
**Files:** Database migration scripts

**Substages:**
1. Create `post_approval` table
   - Columns: id, post_id, stage, substage (nullable), status, approved_by, approved_at, notes, requested_changes, created_at
   - Indexes: (post_id, stage), (post_id, status)
2. Create `scheduled_publications` table
   - Columns: id, post_id, channel, scheduled_at, published_at, status, error_message, retry_count, created_at
   - Indexes: (post_id, channel), (scheduled_at, status)
3. Create `post_publication_status` table
   - Columns: id, post_id, channel, status, external_url, published_at, error_message, created_at, updated_at
   - Unique constraint: (post_id, channel)
   - Indexes: (post_id), (channel, status)
4. Test: Verify all tables created correctly
5. Test: Verify indexes created

**Dependencies:** None  
**Blocks:** Phase 4 (publication features)

---

## Phase 4: Frontend User Interface

**Goal:** Update UI to support output channel selection and channel-specific pipelines

### Stage 4.1: Rename System & Routes
**Files:** Multiple files (blueprints, templates, static JS)

**Substages:**
1. Rename route: `/launchpad/one-click-blog` → `/launchpad/one-click-publication`
   - Update `blueprints/launchpad/one_click_blog.py` (or equivalent)
   - Update route decorators
2. Rename template: `one_click_blog_minimal.html` → `one_click_publication.html`
3. Update all internal references in templates
4. Update all JavaScript references
5. Update navigation links
6. Test: Verify all routes work with new names
7. Test: Verify no broken links

**Dependencies:** None  
**Blocks:** Stage 4.2

---

### Stage 4.2: Add Output Channel Selector to UI
**File:** `templates/launchpad/one_click_publication.html`

**Substages:**
1. Add channel selector dropdown/buttons to UI
   - Options: Blog, Facebook, Instagram, Twitter, Newsletter
   - Default: Blog
   - Show only channels available for current post type
2. Add JavaScript state management for selected channel
3. Add event handlers for channel selection
4. Update UI to show selected channel prominently
5. Test: Verify channel selector appears and works
6. Test: Verify only valid channels shown per post type

**Dependencies:** Stage 4.1, Stage 2.3 (available channels helper)  
**Blocks:** Stage 4.3

---

### Stage 4.3: Update Pipeline Display for Channel-Specific Stages
**File:** `templates/launchpad/one_click_publication.html` + `static/js/launchpad/one-click-publication-controller.js`

**Substages:**
1. Update pipeline loading to include `output` parameter
   - Modify `loadPipeline()` to accept and send `output` parameter
2. Update pipeline rendering to show channel-specific stages
   - Dynamically render stages based on API response
   - Show channel name in stage headers
3. Update substage execution to include `output` parameter
   - Modify all "Run" button handlers
4. Update pipeline status display
   - Show channel-specific completion status
5. Add visual indicator for current output channel
6. Test: Verify pipeline displays correctly for each channel
7. Test: Verify substage execution works with channel context

**Dependencies:** Stage 4.2, Stage 2.2 (API support)  
**Blocks:** Stage 4.4

---

### Stage 4.4: Remove Duplicate Features & Add Navigation
**Files:** `templates/launchpad/one_click_publication.html`

**Substages:**
1. Remove week overview section (dashboard's job)
2. Remove "all items" view (dashboard's job)
3. Add "Back to Dashboard" button/link
   - Links to `/publication/dashboard`
   - Preserves context (post_id, output channel)
4. Update page title and headers
   - Show "One-Click Publication" instead of "One-Click Blog"
5. Test: Verify duplicate features removed
6. Test: Verify navigation works

**Dependencies:** Stage 4.1  
**Blocks:** Phase 5

---

## Phase 5: Integration & Testing

**Goal:** Ensure all components work together and system is production-ready

### Stage 5.1: End-to-End Testing
**Substages:**
1. Test complete workflow for weekly_word → Facebook
   - Calendar sync → Pipeline load → Channel selection → Substage execution → Status update
2. Test complete workflow for themed → Blog
   - Full pipeline with all stages
3. Test complete workflow for themed → Facebook (syndication)
   - Syndication pipeline
4. Test channel switching mid-workflow
   - Switch from blog to facebook, verify stages update
5. Test backward compatibility
   - Old URLs still work (redirect or default to blog)
6. Test error handling
   - Invalid channel, missing post, API errors

**Dependencies:** All previous phases  
**Blocks:** Stage 5.2

---

### Stage 5.2: Integration with Publication Dashboard
**Substages:**
1. Update dashboard to link to One-Click Publication
   - "Work on This" buttons include output channel
   - URL format: `/launchpad/one-click-publication?post_id=X&output=blog`
2. Verify dashboard shows correct channel assignments
3. Test navigation flow: Dashboard → One-Click Publication → Back to Dashboard
4. Verify status updates reflect in dashboard

**Dependencies:** Stage 4.4, Publication Dashboard (existing)  
**Blocks:** Stage 5.3

---

### Stage 5.3: Documentation & Cleanup
**Substages:**
1. Update code comments
2. Update API documentation
3. Update user-facing documentation
4. Remove deprecated code references
5. Clean up unused imports
6. Verify all tests pass
7. Create migration guide (if needed)

**Dependencies:** All previous phases  
**Blocks:** None (final stage)

---

## Critical Path Dependencies

```
Phase 1 (Config)
  ├─ Stage 1.1 (Weekly Content Types)
  │   └─ Blocks: Stage 1.2, Phase 2, Phase 3
  └─ Stage 1.2 (Output Channel Config)
      └─ Blocks: Phase 2, Phase 3

Phase 2 (Backend)
  ├─ Stage 2.1 (Calendar Sync) → Can start immediately
  ├─ Stage 2.2 (Pipeline API) → Depends on Stage 1.2
  ├─ Stage 2.3 (Helpers) → Depends on Stage 1.2
  └─ Stage 2.4 (Execution) → Depends on Stage 2.2, 2.3

Phase 3 (Database) → Can run in parallel with Phase 2

Phase 4 (Frontend)
  ├─ Stage 4.1 (Rename) → Can start immediately
  ├─ Stage 4.2 (Channel Selector) → Depends on Stage 4.1, 2.3
  ├─ Stage 4.3 (Pipeline Display) → Depends on Stage 4.2, 2.2
  └─ Stage 4.4 (Navigation) → Depends on Stage 4.1

Phase 5 (Integration) → Depends on all previous phases
```

---

## Estimated Effort Summary

| Phase | Stages | Complexity | Estimated Time |
|-------|--------|------------|----------------|
| Phase 1: Foundation | 3 stages | Medium | 1-2 days |
| Phase 2: Backend | 4 stages | High | 3-4 days |
| Phase 3: Database | 2 stages | Low | 1 day |
| Phase 4: Frontend | 4 stages | High | 3-4 days |
| Phase 5: Integration | 3 stages | Medium | 1-2 days |
| **Total** | **16 stages** | **High** | **9-13 days** |

---

## Success Criteria

✅ **Phase 1 Complete When:**
- Weekly content types added to config
- Output channel stage system created and tested
- All config functions return correct data

✅ **Phase 2 Complete When:**
- Calendar sync uses new system
- Pipeline API supports output channels
- All endpoints tested and working

✅ **Phase 3 Complete When:**
- All database tables created
- Default data populated
- Tables tested

✅ **Phase 4 Complete When:**
- System renamed throughout
- Channel selector working
- Pipeline displays channel-specific stages
- Navigation integrated

✅ **Phase 5 Complete When:**
- End-to-end workflows tested
- Dashboard integration working
- Documentation updated
- System production-ready

---

## Risk Mitigation

**Risk 1:** Breaking existing functionality  
**Mitigation:** Maintain backward compatibility, default to 'blog' output

**Risk 2:** Complex channel-specific logic  
**Mitigation:** Start with simple config, iterate based on testing

**Risk 3:** Database migration issues  
**Mitigation:** Test migrations on staging first, backup before production

**Risk 4:** Frontend complexity  
**Mitigation:** Build incrementally, test each stage before moving on

---

## Next Steps

1. **Start with Phase 1, Stage 1.1** (Add weekly content types)
2. **Then Phase 1, Stage 1.2** (Create output channel config)
3. **Proceed sequentially** through phases, testing at each stage
4. **Run Phase 3 in parallel** with Phase 2 if possible

**Status:** Ready to begin implementation

---

## Implementation Status Update (2026-01-17)

### ✅ Weekly Content Facebook Implementation - COMPLETE

**Status:** Fully implemented and production-ready

**Completed Components:**
- ✅ Image generation (1080×1080 square images with ImageMagick)
- ✅ Caption generation (Ollama with 30 style variations)
- ✅ Facebook posting (posts to both pages using `/photos` endpoint)
- ✅ Database schema (metadata columns added to `posting_queue`)
- ✅ Workflow configuration (all substages integrated)
- ✅ Error handling and fallbacks

**Documentation:**
- `docs/WEEKLY_CONTENT_SYSTEM_TECHNICAL_REFERENCE.md` - Complete technical reference
- `docs/temp/WEEKLY_CONTENT_IMAGE_CAPTION_IMPLEMENTATION_PLAN.md` - Implementation plan
- `docs/temp/GO_LIVE_CHECKLIST.md` - Go-live checklist

**Remaining Work:**
- Instagram posting (configuration ready, implementation pending)
- Twitter posting (configuration ready, implementation pending)

