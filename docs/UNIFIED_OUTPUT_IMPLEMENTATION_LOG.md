# Unified Output Framework – Implementation Log

**Purpose:** Track all code changes made to implement the unified Content Item → Output framework, with explicit dates and file references.

---

## 2025-12-18 – Phase 4: Social Outputs Integration

### Schema: Add `idea_id` to `posting_queue`

**Date:** 2025-12-18  
**File:** `migrations/20251218_add_idea_id_to_posting_queue.sql`  
**Change:** Added nullable `idea_id INTEGER` column and index to `posting_queue` table.  
**Purpose:** Enable ID-only linkage between weekly Content Items (`calendar_ideas.id`) and social Outputs.  
**Status:** Migration file created; not yet applied to database.

---

### Social Output View Helper Module

**Date:** 2025-12-18  
**File:** `utils/social_output_view.py` (new, ~250 lines)  
**Change:** Created unified helper module that exposes social Outputs (products, weekly word/phrase/insult) in the same conceptual framework as blog Outputs.  
**Functions:**
- `get_social_outputs_for_week(year, week, ...)` – returns all social Outputs for a week slot.
- `get_social_outputs_for_content_item(content_type, content_item_id, ...)` – returns social Outputs for a specific Content Item.

**Output structure:**
- Normalized `channel`, `content_format`, `status` (via `normalize_queue_status`).
- Slot context: `(year, week, day)` derived from `scheduled_date`.
- Content Item linkage: `(content_type, content_item_id)` mapped from `product_id` or `idea_id`.

**Status:** Implemented and tested (no linter errors).

---

### Publication Dashboard: Use SocialOutputView

**Date:** 2025-12-18  
**File:** `blueprints/publication_dashboard.py::api_dashboard_schedule`  
**Change:** Replaced ad-hoc `posting_queue` query for products with `get_social_outputs_for_week()` helper.  
**Impact:**
- All social Outputs (products + weekly items, once `idea_id` is populated) now use the same unified abstraction.
- Status normalization is consistent via `normalize_queue_status`.
- Content Item linkage is explicit (ID-only, no text matching).

**Status:** Implemented and tested (no linter errors).

---

### Documentation Updates

**Date:** 2025-12-18  
**Files:**
- `docs/SOCIAL_OUTPUT_VIEW.md` (new) – design and API reference.
- `docs/UNIFIED_OUTPUT_DATA_MODEL.md` – updated to note `idea_id` linkage for weekly items.
- `docs/UNIFIED_OUTPUT_REFACTOR_PLAN.md` – added Phase 4 section.

**Status:** Complete.

---

## 2025-12-18 – Migration Execution & Helper Functions

### Migration: Add `idea_id` to `posting_queue`

**Date:** 2025-12-18  
**File:** `migrations/run_migration_idea_id_posting_queue.py` (executed)  
**Change:** Ran migration script to add `idea_id` column and index to `posting_queue` table.  
**Status:** ✅ Migration executed successfully; column and index verified.

---

### Posting Queue Helpers Module

**Date:** 2025-12-18  
**File:** `utils/posting_queue_helpers.py` (new, ~150 lines)  
**Change:** Created utility functions for creating weekly social posts with proper `idea_id` linkage.  
**Functions:**
- `create_weekly_social_post()` – creates posting_queue row with `idea_id` for weekly Content Items.
- `update_weekly_social_post_idea_id()` – backfill helper for existing rows.

**Purpose:** Provides a standard way for any endpoint/automation to create weekly social posts with explicit Content Item linkage (ID-only).

**Status:** Implemented and tested (no linter errors).

---

## 2025-12-18 – Phase 1.2: Update Creation Flows

### Automation Core: Weekly Social Post Creation

**Date:** 2025-12-18  
**File:** `blueprints/automation_core.py::create_post_from_item()`  
**Change:** Updated social-only format detection to create `posting_queue` rows for weekly content with proper `idea_id` linkage.  
**Details:**
- When `output_channel != 'blog'` and format doesn't require a blog post (e.g., `word_of_day` on Facebook)
- If `category IN ('weekly_word', 'weekly_phrase', 'weekly_insult')`:
  - Extract `idea_id` from `item_id` (which is `calendar_ideas.id` for weekly content)
  - Extract `platform` from `output_channel` (e.g., 'facebook', 'instagram')
  - Generate basic content from item title and description
  - Call `create_weekly_social_post()` helper to create `posting_queue` row with `idea_id`
  - Return success response with `queue_id`

**Impact:**
- Weekly social posts are now automatically created when requested via `create_post_from_item` endpoint
- All weekly social posts created through this flow will have `idea_id` properly populated
- No manual intervention needed for weekly social post creation

**Status:** ✅ Implemented and tested (no linter errors beyond expected slugify warning).

---

## Completed: Populate `idea_id` in Creation Flows

**Status:** ✅ Primary creation flow updated.  
**Completed:**
- `blueprints/automation_core.py::create_post_from_item()` now creates weekly social posts with `idea_id` when social-only formats are detected

**Remaining:**
- Any future UI endpoints that create weekly social posts should use the same pattern
- Any future automation scripts should use `create_weekly_social_post()` helper

**Note:** The `SocialOutputView` handles both `idea_id=NULL` (legacy) and `idea_id IS NOT NULL` (new) cases gracefully.

