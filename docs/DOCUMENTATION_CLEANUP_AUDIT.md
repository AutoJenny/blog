# Documentation Cleanup Audit

**Date:** 2025-12-18  
**Purpose:** Identify all documentation files that reference deprecated patterns or outdated information, and determine what needs updating.

---

## Summary

**Files Audited:** 41 files found with `calendar_schedule` or `calendar_week_items_deprecated` references  
**Files Needing Updates:** 8 key files identified  
**Action:** Update core documentation files; mark historical references clearly

---

## Key Files Requiring Updates

### 1. `docs/CALENDAR_SYSTEM_AUDIT.md`
- **Status:** ⚠️ Needs update
- **Issues:**
  - References `calendar_week_items` as "old table" (line 142) - but `calendar_week_items` is actually the canonical table now
  - Mentions status enrichment but doesn't reference `publication_status_resolver`
  - References legacy code that may have been removed
- **Action:** Update to reflect current system state, note status resolver usage

### 2. `docs/PUBLICATION_STATUS_RESOLVER_IMPLEMENTATION_PLAN.md`
- **Status:** ✅ Mostly current
- **Issues:** None significant - this is a planning doc that's been implemented
- **Action:** Mark as "Implemented" or archive if no longer needed

### 3. `docs/UNIFIED_OUTPUT_SYSTEM_AUDIT.md`
- **Status:** ⚠️ Needs update
- **Issues:**
  - References `calendar_week_items_deprecated` (should clarify current state)
  - Mentions old status resolution patterns
- **Action:** Update to reflect unified framework implementation

### 4. `docs/UNIFIED_OUTPUT_REFACTOR_PLAN.md`
- **Status:** ✅ Current
- **Issues:** None - this is a forward-looking plan document
- **Action:** None needed

### 5. `docs/UNIFIED_OUTPUT_DATA_MODEL.md`
- **Status:** ✅ Current
- **Issues:** None - already updated with `idea_id` linkage
- **Action:** None needed

### 6. `docs/CHANGELOG.md`
- **Status:** ✅ Current
- **Issues:** None - regularly updated
- **Action:** None needed

### 7. Historical/Archive Files
- **Files:** Many files in `docs/` reference deprecated patterns
- **Status:** ⚠️ Historical context
- **Action:** Leave as-is (historical documentation), but ensure core docs are current

---

## Recommended Updates

### Priority 1: Core System Documentation

1. **`docs/CALENDAR_SYSTEM_AUDIT.md`**
   - Update to clarify `calendar_week_items` is canonical (not deprecated)
   - Add note about `publication_status_resolver` for status enrichment
   - Mark legacy sections clearly as historical

2. **`docs/UNIFIED_OUTPUT_SYSTEM_AUDIT.md`**
   - Update to reflect that unified framework is implemented
   - Clarify `calendar_week_items` vs `calendar_week_items_deprecated` status
   - Note that status resolution now uses `publication_status_resolver`

### Priority 2: Reference Documentation

3. **Create `docs/PUBLICATION_STATUS_RESOLVER_REFERENCE.md`** (if not exists)
   - Public API of `utils/publication_status_resolver.py`
   - Status enum values
   - Category→ID mapping rules
   - Usage examples

4. **Update `docs/CALENDAR_SCHEDULING_ENDPOINTS.md`** (if exists)
   - Document enriched fields from status resolver
   - Note `post_id`, `post_exists`, `post_status` in scheduling API responses

### Priority 3: Historical Context

5. **Leave historical docs as-is**
   - Files in `docs/archive/`, `docs/diagnostics/`, etc. are historical
   - No need to update unless actively referenced
   - Consider adding header note: "⚠️ Historical - May contain deprecated patterns"

---

## Implementation Plan

1. Update `CALENDAR_SYSTEM_AUDIT.md` with current system state
2. Update `UNIFIED_OUTPUT_SYSTEM_AUDIT.md` to reflect implementation
3. Create/update status resolver reference doc
4. Verify core docs are current

---

## Notes

- **Deprecated Patterns:** References to `calendar_schedule` are historical and can remain in historical docs
- **Current System:** Core docs should only reference current patterns (`calendar_week_items`, `calendar_week_posts_v2`, `publication_status_resolver`)
- **File Size:** Keep updates focused; don't bloat files beyond ~500 lines

