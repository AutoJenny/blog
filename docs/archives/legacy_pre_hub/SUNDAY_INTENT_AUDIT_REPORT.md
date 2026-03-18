# Sunday Intent Audit Report

**Date:** 2026-01-25  
**Purpose:** Full intent audit for Facebook Sunday scheduling as required by Single Source of Truth directive  
**Status:** Complete - All sources identified

---

## Executive Summary

**CONFLICT IDENTIFIED:** Multiple systems assign intent to Facebook Sunday 15:00 slot.

- **Authoritative System (Content Control Board):** Sunday 15:00 = DEPTH_LONG (Deep Dive)
- **Legacy System (daily_posts_schedule):** Sunday 15:00 = Product
- **Current State:** Product post exists in `posting_queue` scheduled for Sunday 2026-02-01 15:00

**Resolution Required:** Legacy product scheduling for Sunday must be suppressed or explicitly flagged as conflicting.

---

## 1. Canonical Authority (Policy Decision)

**Content Control Board** is the canonical authority for slot intent.

**Facebook Sunday Intent (LOCKED):**
- **Day:** Sunday (ISO day 7)
- **Time:** 15:00 UK (Europe/London)
- **Role:** DEPTH_LONG (Deep Dive)
- **Source:** `config/content_roles_schedule_rails.py` → `FACEBOOK_SCHEDULE_RAILS`

**Implementation:**
- File: `config/content_roles_schedule_rails.py`
- Rail definition: `{'platform': 'facebook', 'day': 6, 'time': '15:00', 'role': 'DEPTH_LONG', ...}`
- Note: Uses day=6 (0-indexed: 0=Monday, 6=Sunday) but ISO standard is 1-7 (1=Monday, 7=Sunday)

---

## 2. All Identified Sources of Sunday Intent

### 2.1 Authoritative Source ✅

**System:** Content Roles Schedule Rails  
**File:** `config/content_roles_schedule_rails.py`  
**Status:** ✅ **AUTHORITATIVE** (canonical)  
**Intent:** Sunday 15:00 = DEPTH_LONG

**Code Paths:**
- `blueprints/content_roles_api.py::schedule_post()` - Schedules DEPTH_LONG posts for Sunday 15:00
- `blueprints/planning_api_content_control_board.py` - Reads rails to display Sunday slot
- `utils/content_roles/depth_long_generator.py` - Generates DEPTH_LONG content
- `static/js/kb_topics/sunday_slot.js` - UI for Sunday Deep Dive generation

**Database:**
- No database table (Python config file only)
- Posts stored in `posting_queue` with `role='DEPTH_LONG'`

**Day Numbering:**
- Uses `day: 6` (0-indexed: 0=Monday, 6=Sunday)
- Conversion to ISO (1-7) happens in scheduling logic

---

### 2.2 Legacy Source #1: daily_posts_schedule Table ⚠️

**System:** Automated Product Post Scheduling  
**Table:** `daily_posts_schedule`  
**Status:** ⚠️ **LEGACY** (conflicts with authoritative)  
**Intent:** Sunday 15:00 = Product

**Database Entry:**
```
ID: 9
Name: "Weekends"
Time: 15:00:00
Days: [7]  (Sunday only - note: Saturday was removed)
Platform: facebook
Content Type: product
Active: TRUE
```

**Code Paths:**
- `scripts/automated_product_post_creator.py` - Creates product posts based on schedule
  - Line 84: `weekday = check_date.weekday() + 1  # 1=Monday, 7=Sunday`
  - Line 87: Checks if `weekday in schedule_days` (includes 7 = Sunday)
- `blueprints/launchpad_utils.py::get_next_posting_slot()` - Calculates next available slot
- `blueprints/launchpad_scheduling.py::get_next_posting_slot()` - Similar slot calculation
- `scripts/automated_posting.py` - May use this for scheduling

**Current Impact:**
- **ACTIVE CONFLICT:** Product post ID 10727 scheduled for Sunday 2026-02-01 15:00
- Status: `ready` (will be published if not blocked)

**Day Numbering:**
- Uses ISO standard: 1=Monday, 7=Sunday
- Stored as JSONB array: `[7]`

---

### 2.3 Legacy Source #2: post_type_channel_config Table ✅

**System:** Post Type Channel Configuration  
**Table:** `post_type_channel_config`  
**Status:** ✅ **NO CONFLICT** (no Sunday entries)  
**Intent:** None for Sunday

**Database Query Result:**
- **Zero entries** for `publication_day = 7` (Sunday) on Facebook
- This system does NOT assign Sunday intent

**Code Paths:**
- `blueprints/posts.py::api_posts_timeline()` - Reads config to build timeline
  - Line 444-454: Queries `post_type_channel_config` for schedule configs
  - Line 487: Uses `isoweekday()` (1=Monday, 7=Sunday)
  - **Note:** Only processes configs with `publication_day IS NOT NULL`
  - Since no Sunday config exists, this is not a conflict source

**Day Numbering:**
- Uses ISO standard: 1=Monday, 7=Sunday

---

### 2.4 Display-Only Systems (No Intent Assignment)

These systems **display** scheduled posts but do **not assign intent**:

#### 2.4.1 planning_api_calendar_schedule.py
**File:** `blueprints/planning_api_calendar_schedule.py`  
**Status:** 📊 **DISPLAY ONLY** (reads, doesn't assign)  
**Function:** Shows product posts in calendar view

**Code:**
- Line 207-230: Queries `posting_queue` for product posts
- Line 227: **Excludes Saturday (day 6)** but **includes Sunday (day 7)**
- **Issue:** Shows product posts on Sunday if they exist (but doesn't create them)

**Day Numbering:**
- Uses ISO: `EXTRACT(ISODOW FROM scheduled_date)` (1=Monday, 7=Sunday)

---

#### 2.4.2 publication_dashboard.py
**File:** `blueprints/publication_dashboard.py`  
**Status:** 📊 **DISPLAY ONLY** (reads, doesn't assign)  
**Function:** Shows publication schedule dashboard

**Code:**
- Line 457-467: Queries `daily_posts_schedule` for product schedules
- Line 375: **Excludes Saturday (day 6)** but **includes Sunday (day 7)**
- **Issue:** Shows product schedule on Sunday if it exists in `daily_posts_schedule`

**Day Numbering:**
- Uses ISO: 1=Monday, 7=Sunday

---

#### 2.4.3 posts.py::api_posts_timeline()
**File:** `blueprints/posts.py`  
**Status:** 📊 **DISPLAY ONLY** (reads, doesn't assign)  
**Function:** Shows posts timeline

**Code:**
- Line 497-520: Processes `daily_posts_schedule` for product posts
- Line 510-520: Calculates dates for matching weekdays
- **Issue:** Will show product posts on Sunday if `daily_posts_schedule` includes day 7

**Day Numbering:**
- Uses ISO: `current_date.isoweekday()` (1=Monday, 7=Sunday)

---

## 3. Conflict Resolution Analysis

### 3.1 Current Conflict State

**Active Conflict:**
- `daily_posts_schedule` ID 9 ("Weekends") schedules products for Sunday 15:00
- Product post ID 10727 exists in `posting_queue` for Sunday 2026-02-01 15:00
- Content Roles Framework requires DEPTH_LONG for Sunday 15:00

**How Conflicts Currently Resolve:**
- **Implicitly:** Both systems can create posts for the same slot
- **No explicit conflict detection:** Systems operate independently
- **Last writer wins:** Whichever post is scheduled last will be the one that publishes
- **Silent coexistence:** Both posts can exist in `posting_queue` simultaneously

**This is UNACCEPTABLE per directive requirements.**

---

### 3.2 Required Resolution Strategy

Per directive Section 4.3, one of the following must be implemented **explicitly**:

**Option A: Suppress Legacy Sunday Scheduling (RECOMMENDED)**
- Modify `automated_product_post_creator.py` to exclude Sunday (day 7) from product scheduling
- Update `daily_posts_schedule` query logic to filter out Sunday
- Add explicit check: "If Content Roles rail exists for Sunday, skip product scheduling"

**Option B: Flag Conflicts in UI**
- Add conflict detection in Content Control Board
- Show warning when product post exists for Sunday slot
- Allow manual resolution (delete product post or move it)

**Option C: Prevent Legacy Sunday Scheduling Entirely**
- Add database constraint or application-level check
- Block creation of product posts for Sunday 15:00
- Return error if attempted

**Recommendation:** **Option A** (suppress) + **Option B** (flag) for safety.

---

## 4. Code Paths Requiring Changes

### 4.1 Product Post Creation (CRITICAL)

**File:** `scripts/automated_product_post_creator.py`  
**Change Required:** Exclude Sunday (day 7) from product scheduling

**Current Logic:**
```python
# Line 84: weekday = check_date.weekday() + 1  # 1=Monday, 7=Sunday
# Line 87: if schedule_days and weekday in schedule_days:
```

**Required Change:**
```python
# Check if Content Roles rail exists for this day/time
# If so, skip product scheduling
if weekday == 7:  # Sunday
    # Check if DEPTH_LONG rail exists
    from config.content_roles_schedule_rails import get_rails_for_platform
    rails = get_rails_for_platform('facebook', role='DEPTH_LONG')
    if rails and any(r['day'] == 6 for r in rails):  # day=6 is Sunday in 0-indexed
        continue  # Skip - this slot is reserved for DEPTH_LONG
```

---

### 4.2 Slot Calculation (CRITICAL)

**Files:**
- `blueprints/launchpad_utils.py::get_next_posting_slot()`
- `blueprints/launchpad_scheduling.py::get_next_posting_slot()`

**Change Required:** Exclude Sunday slots when calculating next available product post slot

**Current Logic:**
- Queries `daily_posts_schedule` for active schedules
- Includes all days in schedule (including Sunday)

**Required Change:**
- Filter out Sunday (day 7) from available slots
- Or check Content Roles rails before assigning slot

---

### 4.3 Display Systems (INFORMATIONAL)

**Files:**
- `blueprints/planning_api_calendar_schedule.py`
- `blueprints/publication_dashboard.py`
- `blueprints/posts.py::api_posts_timeline()`

**Change Required:** Show conflict warnings when product posts exist for Sunday

**Current Behavior:**
- Shows product posts on Sunday if they exist
- No indication of conflict

**Required Change:**
- Add conflict detection
- Flag Sunday product posts as "CONFLICT - Reserved for Deep Dive"
- Or hide them entirely (preferred)

---

## 5. Forward Planning Requirements

### 5.1 Current State

**Sunday Deep Dive Planning:**
- ✅ Supports week selection (rota_year, rota_week)
- ✅ Supports topic and source article selection
- ✅ Supports generation, validation, approval, scheduling
- ⚠️ **Missing:** Multi-week forward planning (4+ weeks ahead)

**Current Limitation:**
- Sunday slot UI (`sunday_slot.js`) loads current week by default
- Can manually select future weeks, but no bulk view of 4+ weeks

---

### 5.2 Required Enhancements

**Content Control Board:**
- ✅ Already shows weekly matrix
- ⚠️ **Needs:** Ability to navigate 4+ weeks ahead
- ⚠️ **Needs:** Show all future Sunday slots with status

**Sunday Slot Panel:**
- ⚠️ **Needs:** Week selector that shows 4+ weeks ahead
- ⚠️ **Needs:** Bulk status view for all future Sundays

**Generation API:**
- ✅ Already supports explicit rota_year/rota_week binding
- ✅ Prevents automatic shifting between weeks
- ✅ **Status:** Meets requirement

---

## 6. Uncertainty & Risks

### 6.1 Day Numbering Inconsistency

**Issue:** Content Roles uses 0-indexed days (0=Monday, 6=Sunday) while database uses ISO (1=Monday, 7=Sunday).

**Risk:** Conversion errors could cause incorrect slot matching.

**Mitigation:** Standardize on ISO (1-7) everywhere, or document conversion clearly.

**Recommendation:** Update `content_roles_schedule_rails.py` to use ISO standard (1-7) for consistency.

---

### 6.2 Background Job Timing

**Issue:** `background_posting_monitor.sh` runs every 5 minutes and may create product posts before conflict check.

**Risk:** Product posts could be created for Sunday before DEPTH_LONG post exists.

**Mitigation:** Add conflict check in `automated_product_post_creator.py` before creating posts.

---

### 6.3 Existing Product Post

**Issue:** Product post ID 10727 already exists for Sunday 2026-02-01 15:00.

**Risk:** This post will publish if not handled.

**Required Action:** 
- Delete or reschedule this post
- Add to conflict resolution plan

---

## 7. Implementation Checklist

### Phase 1: Conflict Suppression (CRITICAL)
- [ ] Update `automated_product_post_creator.py` to exclude Sunday
- [ ] Update `launchpad_utils.py::get_next_posting_slot()` to exclude Sunday
- [ ] Update `launchpad_scheduling.py::get_next_posting_slot()` to exclude Sunday
- [ ] Handle existing product post (ID 10727) - delete or reschedule
- [ ] Test: Verify no new product posts created for Sunday

### Phase 2: Conflict Detection (SAFETY)
- [ ] Add conflict detection in Content Control Board
- [ ] Flag Sunday product posts as conflicts
- [ ] Update display systems to show conflicts
- [ ] Add conflict resolution UI (delete/move product post)

### Phase 3: Forward Planning (REQUIREMENT)
- [ ] Add 4+ week navigation to Content Control Board
- [ ] Add bulk Sunday slot view (all future Sundays)
- [ ] Enhance Sunday slot panel for multi-week planning
- [ ] Test: Verify 4+ weeks can be planned ahead

### Phase 4: Documentation
- [ ] Update `daily_posts_schedule` documentation (note Sunday exclusion)
- [ ] Document conflict resolution in Content Roles Framework docs
- [ ] Add migration notes for existing product post handling

---

## 8. Summary

**Sources Identified:** 4 systems (1 authoritative, 1 legacy conflict, 2 display-only)

**Conflicts Found:** 1 active conflict (product post scheduled for Sunday 15:00)

**Resolution Strategy:** Suppress legacy + flag conflicts + forward planning

**Uncertainty Level:** Low (all sources identified, conflict clear)

**Risk Level:** Medium (existing product post needs handling)

**Estimated Effort:** 
- Phase 1 (suppression): 2-3 hours
- Phase 2 (detection): 2-3 hours  
- Phase 3 (planning): 3-4 hours
- Phase 4 (documentation): 1 hour
- **Total: 8-11 hours**

---

**End of Report**
