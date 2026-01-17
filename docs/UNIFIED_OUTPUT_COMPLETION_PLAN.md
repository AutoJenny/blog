# Unified Output Framework – Completion Plan

**Date:** 2025-12-18  
**Purpose:** Complete the remaining work for the unified Output framework: ensure weekly social post creation flows use proper `idea_id` linkage, clean up documentation, and verify system consistency.

---

## Overview

The unified Output framework is largely complete, with:
- ✅ Schema migration (`idea_id` column added to `posting_queue`)
- ✅ Social Output View helper module
- ✅ Posting queue helpers for weekly social posts
- ✅ Publication dashboard integration
- ✅ Status resolver system

**Remaining work:**
1. Audit and update weekly social post creation flows
2. Documentation cleanup (remove deprecated references)
3. System-wide testing and verification

---

## Phase 1: Audit Weekly Social Post Creation Flows

### 1.1 Identify All Creation Points

**Goal:** Find every place where `posting_queue` rows are created for weekly word/phrase/insult Content Items.

**Activities:**
1. Search codebase for `INSERT INTO posting_queue` statements
2. Identify which ones handle weekly content (`content_type` in `['weekly_word', 'weekly_phrase', 'weekly_insult']`)
3. Check if they currently populate `idea_id`
4. Document each creation point with:
   - File path and function name
   - How `idea_id` is determined (or should be determined)
   - Current behavior (does it set `idea_id`?)
   - Whether it's manual UI flow or automation

**Deliverable:**
- `docs/WEEKLY_SOCIAL_POST_CREATION_AUDIT.md` (new) listing:
  - All creation points found
  - Current state of each (with/without `idea_id`)
  - Recommended changes per point

**Constraints:**
- Keep audit doc under ~400 lines
- No code changes in this phase, only analysis

---

### 1.2 Update Creation Flows

**Goal:** Ensure all weekly social post creation uses `create_weekly_social_post()` helper or explicitly sets `idea_id`.

**Activities:**

For each creation point identified in 1.1:

1. **Determine `idea_id` source:**
   - If from rotation JSON: extract `calendar_ideas.id` from the week's item
   - If from explicit selection: use the provided `idea_id`
   - If from UI: ensure UI passes `idea_id` to backend

2. **Update code:**
   - Replace direct `INSERT INTO posting_queue` with `create_weekly_social_post()` call, OR
   - Add `idea_id` to existing INSERT statement if helper can't be used (e.g., complex transaction logic)

3. **Add validation:**
   - Ensure `content_type` matches the weekly type (`weekly_word`, `weekly_phrase`, `weekly_insult`)
   - Ensure `idea_id` is not NULL for weekly content

**Files likely to need updates:**
- `blueprints/launchpad_content.py` (if it handles weekly content)
- Any automation scripts that create weekly social posts
- UI endpoints that create weekly posts

**Deliverable:**
- Updated code files with `idea_id` properly populated
- Updated `docs/UNIFIED_OUTPUT_IMPLEMENTATION_LOG.md` with changes

**Constraints:**
- Keep each file under ~500 lines (split if necessary)
- No breaking changes to existing APIs (add `idea_id` as optional if needed for backward compatibility during transition)

---

### 1.3 Optional: Backfill Existing Rows

**Goal:** Populate `idea_id` for existing weekly social posts in `posting_queue` where possible.

**Activities:**
1. Query `posting_queue` for rows with:
   - `content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult')`
   - `idea_id IS NULL`
   - `scheduled_date IS NOT NULL` (to determine week)

2. For each row:
   - Determine `(year, week)` from `scheduled_date`
   - Query rotation JSON or `calendar_ideas` to find the `idea_id` for that week's item
   - Use `update_weekly_social_post_idea_id()` to backfill

3. **Caveats:**
   - Only backfill if linkage is unambiguous (e.g., one item per week per type)
   - Document any rows that can't be backfilled (ambiguous or missing data)

**Deliverable:**
- Optional backfill script: `scripts/backfill_weekly_social_post_idea_id.py`
- Report of backfilled vs. unbackfilled rows

**Note:** This is optional because `SocialOutputView` handles `idea_id=NULL` gracefully. Backfilling improves data quality but isn't required for functionality.

---

## Phase 2: Documentation Cleanup

### 2.1 Audit Documentation References

**Goal:** Find all docs that reference deprecated patterns or outdated information.

**Activities:**
1. Search `docs/` for references to:
   - `calendar_schedule` (deprecated table)
   - `calendar_week_items_deprecated` (legacy table)
   - Title-based matching heuristics
   - Old status resolution patterns

2. For each doc found:
   - Note what needs updating
   - Determine if doc is still relevant or should be archived

**Deliverable:**
- `docs/DOCUMENTATION_CLEANUP_AUDIT.md` (new) listing:
  - Files that need updates
  - Specific sections/references to change
  - Recommended actions (update, archive, or mark as historical)

---

### 2.2 Update Key Documentation Files

**Goal:** Ensure core docs reflect current system state.

**Files to update:**

1. **`docs/CALENDAR_SYSTEM_AUDIT.md`**
   - Remove or mark as historical any `calendar_schedule` references
   - Update to note status enrichment via `publication_status_resolver`
   - Clarify that `calendar_week_items` is canonical (not `calendar_week_items_deprecated`)

2. **`docs/CALENDAR_SCHEDULING_ENDPOINTS.md`** (if exists)
   - Document enriched fields from status resolver
   - Note `post_id`, `post_exists`, `post_status` in scheduling API responses

3. **`docs/UNIFIED_ITEM_CARD_AUDIT.md`** (if exists)
   - Note that status comes from resolver (not ad-hoc logic)
   - Document required item structure for `createUnifiedItemCard`

4. **Create `docs/PUBLICATION_STATUS_RESOLVER_REFERENCE.md`** (if not exists)
   - Public API of `utils/publication_status_resolver.py`
   - Status enum values
   - Category→ID mapping rules
   - Usage examples

**Deliverable:**
- Updated documentation files
- New reference doc if needed

**Constraints:**
- Keep each doc under ~500 lines
- Mark deprecated sections clearly (don't delete historical context)

---

## Phase 3: Testing and Verification

### 3.1 Status Display Consistency

**Goal:** Verify that status badges are consistent across all calendar views.

**Test Cases:**

1. **Week View** (`/planning/calendar?year=2025&week=51&tab=week-view`)
   - For each item with a post in `/posts`, verify status badge matches
   - For items without posts, verify "Not Created" badge
   - Test with: themes, recipes, profiles, weekly words/phrases/insults

2. **Future Items / Scheduling** (`/planning/calendar?year=2025&week=51&tab=scheduling`)
   - Verify status matches week view for same items
   - Test Triskelion example (previously had issues)

3. **Publication Schedule** (`/planning/calendar?year=2025&week=51&tab=publication-schedule`)
   - Verify status matches other views
   - Verify social outputs (products, weekly items) show correct status

4. **Edge Cases:**
   - Deleted posts: should show `deleted` or `none` status
   - Published posts: should show `published` status
   - Draft posts: should show `draft` status

**Deliverable:**
- Test report: `docs/STATUS_DISPLAY_VERIFICATION_REPORT.md`
- List of any inconsistencies found (with fixes if needed)

---

### 3.2 Social Output Linkage Verification

**Goal:** Verify that weekly social posts are correctly linked via `idea_id`.

**Test Cases:**

1. **Query verification:**
   - Query `posting_queue` for weekly items with `idea_id IS NOT NULL`
   - Verify `idea_id` points to valid `calendar_ideas.id`
   - Verify `content_type` matches `calendar_ideas.item_classification`

2. **SocialOutputView verification:**
   - Call `get_social_outputs_for_week(2025, 51)` for a known week
   - Verify weekly items appear with correct `content_item_id = idea_id`
   - Verify status normalization works correctly

3. **Publication dashboard verification:**
   - Check `/publication/api/dashboard/schedule?year=2025&week=51`
   - Verify weekly social outputs appear with correct linkage
   - Verify status matches `posting_queue.status` (normalized)

**Deliverable:**
- Verification report with test results
- Any fixes needed for linkage issues

---

### 3.3 End-to-End Flow Testing

**Goal:** Test complete flows from Content Item to Output.

**Test Flows:**

1. **Weekly Word Social Post Creation:**
   - Select a weekly word from rotation JSON
   - Create social post via UI or automation
   - Verify `posting_queue` row has `idea_id` set
   - Verify it appears in publication dashboard with correct status

2. **Theme Blog Post Creation:**
   - Select theme for a week
   - Create blog post
   - Verify `calendar_week_items` links post to week
   - Verify status resolver returns correct status
   - Verify status appears correctly in all calendar views

3. **Product Post Creation:**
   - Create product post (existing flow)
   - Verify `product_id` linkage (already working)
   - Verify status normalization

**Deliverable:**
- End-to-end test report
- Any flow fixes needed

---

## Implementation Order

1. **Phase 1.1** (Audit) – No code changes, just analysis
2. **Phase 1.2** (Update flows) – Code changes, but isolated
3. **Phase 2** (Docs) – Can be done in parallel with Phase 1.2
4. **Phase 3** (Testing) – After code changes are complete
5. **Phase 1.3** (Backfill) – Optional, can be done anytime after 1.2

---

## Success Criteria

- ✅ All weekly social post creation flows populate `idea_id`
- ✅ Documentation is current and accurate
- ✅ Status displays are consistent across all views
- ✅ Social outputs are correctly linked to Content Items
- ✅ No deprecated patterns remain in active code/docs

---

## File Size Constraints

- Keep all new/updated files under ~500 lines
- Split large files rather than bloating
- Extract shared utilities to `utils/` modules

---

## Notes

- **Backward compatibility:** During transition, `idea_id` can be optional (NULL) for existing flows, but new flows must set it
- **Graceful degradation:** `SocialOutputView` handles `idea_id=NULL` gracefully, so missing linkage doesn't break the system
- **Testing priority:** Focus on status consistency first (most visible issue), then linkage verification

