# Calendar System UI Review

**Date:** 2026-01-XX  
**Purpose:** Comprehensive review of all calendar UIs, identifying overlaps, incomplete features, and documentation gaps

---

## Executive Summary

The calendar system has **multiple overlapping UIs in various states of completeness**, with some legacy views still accessible alongside newer unified views. Documentation in the Knowledge Base is minimal.

**Key Findings:**
- **5+ different calendar UI entry points**
- **New unified calendar** (`/planning/calendar`) with tabs
- **Legacy views** still accessible (`/planning/posts/<id>/calendar/view`, `/week-view`)
- **Incomplete documentation** in Knowledge Base
- **Unclear which UI is the "current" one**

---

## All Calendar UI Routes

### 1. New Unified Calendar (Current?)
**Route:** `/planning/calendar`  
**Template:** `templates/planning/calendar/new_calendar.html`  
**Status:** ⚠️ **Appears to be current but unclear**

**Features:**
- Tab-based interface with shared header
- Tabs: `year-view`, `week-view`, `scheduling`, `publication-schedule`, `day-assignments`
- Uses includes for each tab content
- Links to "Legacy views" suggesting this is the new one

**URL Parameters:**
- `year` - Year to display
- `week` - Week number
- `tab` - Active tab (defaults to `week-view`)

**Access Points:**
- Direct URL: `/planning/calendar?year=2025&week=1&tab=week-view`
- Homepage: Links to `/planning/posts/{id}/calendar/week-view` (old route)

---

### 2. Legacy Calendar View (Year View)
**Route:** `/planning/posts/<int:post_id>/calendar/view`  
**Template:** `templates/planning/calendar/view.html`  
**Status:** ⚠️ **Legacy - Still accessible**

**Features:**
- Year view with 52-week grid
- Month-based columns
- Tabs: "Year View" and "Week View"
- Links to week view via `planning_calendar_week_view`

**Issues:**
- Requires `post_id` parameter (why?)
- Marked as "Year View" but seems redundant with new unified calendar
- Still functional but may be deprecated

---

### 3. Legacy Calendar Week View
**Route:** `/planning/posts/<int:post_id>/calendar/week-view`  
**Template:** `templates/planning/calendar/week_view.html` or `week_view_v2.html`  
**Status:** ⚠️ **Legacy - Still accessible**

**Features:**
- Week-by-week view
- Day-by-day breakdown
- URL parameters: `year`, `week`

**Issues:**
- Requires `post_id` parameter (why?)
- Overlaps with new unified calendar's week-view tab
- Multiple templates (`week_view.html`, `week_view_v2.html`) - which is used?

---

### 4. Calendar Scheduling View
**Route:** `/planning/posts/<int:post_id>/calendar/scheduling`  
**Template:** `templates/planning/calendar/scheduling.html`  
**Status:** ⚠️ **Also available as tab in new unified calendar**

**Features:**
- Year overview with scheduling
- Uses JSON-backed display (`/planning/api/calendar/scheduling/all`)
- Range-based navigation (Year <<, Month <, Month >, Year >>)
- Table format showing weeks

**Issues:**
- Also available as `scheduling` tab in new unified calendar
- Requires `post_id` - why?
- Overlaps with unified calendar

---

### 5. Calendar Ideas Page
**Route:** `/planning/posts/<int:post_id>/calendar/ideas`  
**Template:** `templates/planning/calendar/ideas.html`  
**Status:** ✅ **Standalone page - seems current**

**Features:**
- Manage calendar ideas
- Create/edit/delete ideas
- Week-based idea generation

**Issues:**
- Requires `post_id` - unclear why
- Not integrated into unified calendar tabs
- Separate from other calendar views

---

### 6. Calendar Taxonomy Page
**Route:** `/planning/posts/<int:post_id>/calendar/taxonomy`  
**Template:** `templates/planning/calendar/taxonomy.html`  
**Status:** ✅ **Standalone page - seems current**

**Features:**
- Taxonomy assignment for calendar items
- URL parameters: `year`, `week`

**Issues:**
- Requires `post_id` - unclear why
- Not integrated into unified calendar
- Separate from other views

---

### 7. Sequence Manager
**Route:** `/planning/calendar/sequence-manager`  
**Template:** `templates/planning/calendar/sequence_manager.html`  
**Status:** ✅ **Standalone page - seems current**

**Features:**
- Manage base cyclic sequences (themes, recipes, profiles, words, phrases, insults)
- Reorder/add/delete items in base lists
- Category-based management

**Issues:**
- Not integrated into unified calendar
- Standalone tool
- Well-documented in technical docs

---

### 8. Product Data Review
**Route:** `/planning/posts/<int:post_id>/calendar/product-data-review`  
**Template:** `templates/planning/calendar/product_data_review.html`  
**Status:** ⚠️ **Specialized page - unclear purpose**

**Features:**
- Product data review for generated posts
- Category-based review

**Issues:**
- Requires `post_id`
- Unclear relationship to calendar
- May be specialized tool

---

## Unified Calendar Tabs

The new unified calendar (`/planning/calendar`) has these tabs:

### Tab 1: Year View
**Template:** `templates/planning/calendar/includes/year_view_content.html`  
**Status:** ⚠️ **Incomplete/Unknown**

**Purpose:** Year overview (52-week grid?)

---

### Tab 2: Week View
**Template:** `templates/planning/calendar/includes/week_view_content.html`  
**Status:** ⚠️ **Incomplete/Unknown**

**Purpose:** Week-by-week detailed view

---

### Tab 3: Scheduling
**Template:** `templates/planning/calendar/includes/scheduling_content.html`  
**Status:** ✅ **Likely complete** (uses same system as `/scheduling` route)

**Purpose:** Year overview with scheduling table

---

### Tab 4: Publication Schedule
**Template:** `templates/planning/calendar/includes/publication_schedule_content.html`  
**Status:** ⚠️ **Incomplete/Unknown**

**Purpose:** Publication schedule view (from publication dashboard?)

---

### Tab 5: Day Assignments
**Template:** `templates/planning/calendar/includes/publication_day_assignments_content.html`  
**Status:** ⚠️ **Incomplete/Unknown**

**Purpose:** Day-level assignment view?

---

## Overlaps and Redundancies

### Overlap 1: Week View
- **New Unified:** `/planning/calendar?tab=week-view`
- **Legacy:** `/planning/posts/<id>/calendar/week-view`
- **Status:** Both exist, unclear which is current

### Overlap 2: Year View
- **New Unified:** `/planning/calendar?tab=year-view`
- **Legacy:** `/planning/posts/<id>/calendar/view`
- **Status:** Both exist, unclear which is current

### Overlap 3: Scheduling View
- **New Unified:** `/planning/calendar?tab=scheduling`
- **Legacy:** `/planning/posts/<id>/calendar/scheduling`
- **Status:** Both exist, likely same functionality

### Redundancy: Post ID Requirement
- Most legacy routes require `post_id` parameter
- New unified calendar doesn't require `post_id`
- **Question:** Why do legacy routes need `post_id`? Is it used?

---

## Knowledge Base Documentation Status

### Current KB References
- **Mentioned in:** `getting_started/overview.html` - "Calendar - Scheduling and week planning"
- **Mentioned in:** `content_types/weekly_words_phrases.html` - Links to calendar view
- **Mentioned in:** `content_types/weekly_content.html` - Links to calendar view

### Missing KB Documentation
- ❌ **No dedicated calendar page** in Knowledge Base
- ❌ **No explanation** of different calendar UIs
- ❌ **No guide** on which UI to use
- ❌ **No documentation** of calendar system architecture
- ❌ **No explanation** of calendar → posting workflow

### Technical Documentation (Outside KB)
- ✅ Extensive technical docs in `/docs`:
  - `CALENDAR_SYSTEM_AUDIT.md`
  - `CALENDAR_SCHEDULING_INDEX.md`
  - `CALENDAR_SCHEDULING_NEW_PARADIGM.md`
  - `CALENDAR_SCHEDULING_COMPONENT_STRUCTURE.md`
  - `calendar_system_technical_documentation.md`
- ⚠️ **But not accessible from KB** - users won't find these easily

---

## Questions to Resolve

### 1. Which UI is Current?
- Is `/planning/calendar` the new unified interface?
- Should legacy routes be deprecated/removed?
- Why do legacy routes require `post_id`?

### 2. Post ID Parameter
- Why do most calendar routes require `post_id`?
- Is it actually used in the calendar views?
- Should it be removed for calendar-only views?

### 3. Tab Completeness
- Are all tabs in unified calendar complete?
- What's the status of `year-view`, `publication-schedule`, `day-assignments`?
- Do they work or are they placeholders?

### 4. Integration
- Should `ideas` and `taxonomy` pages be integrated into unified calendar?
- Or are they intentionally separate?
- What's the relationship between calendar and these pages?

### 5. Homepage Links
- Homepage links to `/planning/posts/{id}/calendar/week-view` (legacy)
- Should it link to `/planning/calendar?tab=week-view` instead?
- Which is the "correct" entry point?

---

## Recommended Actions

### Phase 1: Clarify Current State
1. **Determine primary UI:**
   - Is `/planning/calendar` the current unified interface?
   - Or is it still in development?
   - Document which UI is "current"

2. **Audit tab completeness:**
   - Check each tab in unified calendar
   - Document which are complete vs. placeholders
   - Test functionality

3. **Resolve post_id requirement:**
   - Determine if `post_id` is needed for calendar views
   - Remove if not needed
   - Or document why it's required

### Phase 2: Consolidate UIs
1. **Deprecate legacy routes:**
   - Mark legacy routes as deprecated
   - Redirect to unified calendar
   - Or remove if truly obsolete

2. **Integrate standalone pages:**
   - Decide if `ideas` and `taxonomy` should be tabs
   - Or keep separate but link clearly
   - Update navigation

3. **Update homepage links:**
   - Change homepage to link to unified calendar
   - Update all internal links

### Phase 3: KB Documentation
1. **Create calendar section in KB:**
   - Add "Calendar System" to Management Interfaces
   - Document all UIs and their purposes
   - Explain which to use when

2. **Link to technical docs:**
   - Add links from KB to technical documentation
   - Make technical docs discoverable

3. **Create user guide:**
   - Step-by-step guide for common calendar tasks
   - Screenshots/examples
   - Troubleshooting

---

## Files to Review

### Templates
- `templates/planning/calendar/new_calendar.html` - Unified calendar
- `templates/planning/calendar/view.html` - Legacy year view
- `templates/planning/calendar/week_view.html` - Legacy week view
- `templates/planning/calendar/week_view_v2.html` - Which version?
- `templates/planning/calendar/scheduling.html` - Scheduling view
- `templates/planning/calendar/ideas.html` - Ideas page
- `templates/planning/calendar/taxonomy.html` - Taxonomy page
- `templates/planning/calendar/sequence_manager.html` - Sequence manager
- `templates/planning/calendar/includes/*.html` - Tab includes

### Blueprints
- `blueprints/planning.py` - Main planning routes
- `blueprints/planning_calendar.py` - Calendar-specific functions
- `blueprints/planning_api_calendar*.py` - Calendar APIs

### Documentation
- `docs/CALENDAR_SYSTEM_AUDIT.md` - Technical audit
- `docs/CALENDAR_SCHEDULING_INDEX.md` - Documentation index
- `docs/calendar_system_technical_documentation.md` - Technical reference

---

## Summary

The calendar system has **multiple overlapping UIs** with unclear relationships:

1. **New Unified Calendar** (`/planning/calendar`) - Appears to be current but incomplete
2. **Legacy Views** - Still accessible, may be deprecated
3. **Standalone Pages** - Ideas, Taxonomy, Sequence Manager
4. **Poor Documentation** - Not well covered in Knowledge Base

**Immediate Needs:**
- Clarify which UI is current
- Document all UIs and their purposes
- Consolidate or clearly separate overlapping views
- Add comprehensive KB documentation
