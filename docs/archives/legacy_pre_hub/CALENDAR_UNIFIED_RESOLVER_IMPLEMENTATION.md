# Calendar Unified Resolver Implementation

**Date:** 2026-01-19  
**Status:** ✅ **IMPLEMENTED**  
**Purpose:** Document the unified resolver architecture that ensures all calendar views use the same single source of truth

---

## Problem Statement

Previously, the calendar system had **two conflicting data sources**:

1. **Scheduling View** (`/planning/api/calendar/scheduling/all`):
   - Read from JSON files (`data/calendar/schedule/`)
   - Generated from base lists + cyclic logic (but didn't include overrides)
   - Showed: "Balfour" for week 4

2. **Week View** (`/planning/api/calendar/profiles/{year}/{week}`):
   - Queried `calendar_week_items` table directly
   - Showed actual database assignments
   - Showed: "Broun" for week 3 (different week, but also inconsistent)

**Result:** Different views showed different data for the same week.

---

## Solution: Unified Resolver Pattern

### Architecture

```
┌─────────────────────────────────────────────────────────┐
│         SINGLE SOURCE OF TRUTH                          │
│  Base Lists (DB) + Cyclic Logic + Overrides            │
│  ↓                                                       │
│  resolve_item_for_week() (utils/calendar_resolver.py)  │
└─────────────────────────────────────────────────────────┘
         ↓                    ↓                    ↓
    Scheduling View      Week View         All Other Views
    (JSON cache)      (Direct call)      (Direct call)
```

### Key Principle

**`resolve_item_for_week()` is the single source of truth for "what should be scheduled" for any given week.**

All views and APIs must use this resolver to ensure consistency.

---

## Implementation Changes

### 1. Profiles Endpoint (`blueprints/planning_api_calendar_profiles.py`)

**Before:**
- Queried `calendar_week_items` table directly
- Showed actual database assignments (which could differ from cyclic schedule)

**After:**
- Uses `resolve_item_for_week("profile_surname", year, week)` and `resolve_item_for_week("profile_product", year, week)`
- Returns the same data as scheduling view
- Includes overrides automatically

**Code:**
```python
profile_product = resolve_item_for_week("profile_product", year, week_number)
profile_surname = resolve_item_for_week("profile_surname", year, week_number)
```

### 2. JSON Builder (`utils/calendar_schedule_builder.py`)

**Before:**
- Built schedule from base lists using cyclic logic only
- Did not include overrides
- JSON files could be out of sync with resolver

**After:**
- Uses `resolve_item_for_week()` for each week
- Automatically includes overrides in JSON files
- JSON files now match what resolver returns

**Code:**
```python
for w in range(1, 53):
    resolved_item = resolve_item_for_week(category, year, w)
    # Build entry from resolved_item (includes overrides)
```

### 3. Schedule Endpoint (`blueprints/planning_api_calendar_schedule.py`)

**Status:** ✅ Already using resolver (no changes needed)

This endpoint was already updated to use `resolve_item_for_week()` for all categories.

---

## Data Flow

### For Display (Read-Only)

1. **Week View** → Calls `resolve_item_for_week()` directly
2. **Scheduling View** → Reads JSON files (which are generated using `resolve_item_for_week()`)
3. **All Other Views** → Use resolver or read JSON files

### For Updates (Write)

1. **Base List Changes** → Triggers JSON rebuild (which uses resolver)
2. **Override Changes** → Triggers JSON rebuild (which uses resolver)
3. **JSON Files** → Regenerated to match resolver output

---

## Benefits

✅ **Single Source of Truth:** All views show the same data  
✅ **Consistency:** Scheduling view and week-view always match  
✅ **Maintainability:** One resolver to update  
✅ **Performance:** JSON cache still works for fast display  
✅ **Robustness:** No sync issues between JSON and database  
✅ **Override Support:** Overrides automatically included in all views

---

## Data Sources Clarification

### Source of Truth (What Should Be Scheduled)
- **Resolver:** `resolve_item_for_week()` from `utils/calendar_resolver.py`
- **Inputs:** Base lists (DB) + Cyclic logic + Overrides
- **Used by:** All calendar views and APIs

### Output Tracking (What Posts Exist)
- **Table:** `calendar_week_items` / `calendar_week_posts_v2`
- **Purpose:** Track which posts have been created for which weeks
- **Used by:** Status resolution, publication tracking

### Performance Cache
- **JSON Files:** `data/calendar/schedule/{category}/{year}.json`
- **Purpose:** Fast display without database queries
- **Generated from:** Resolver output (includes overrides)
- **Regenerated:** When base lists or overrides change

---

## Migration Notes

### JSON Files Regeneration

After this implementation, JSON files were regenerated to include overrides:

```bash
python scripts/build_calendar_schedules.py --year 2026
```

This ensures JSON files match resolver output.

### Backward Compatibility

- Old JSON files (without overrides) will still work but may show outdated data
- Regenerate JSON files after deploying this change
- All APIs continue to work, just with consistent data

---

## Testing

### Verification Steps

1. **Check Resolver Output:**
   ```python
   from utils.calendar_resolver import resolve_item_for_week
   result = resolve_item_for_week('profile_surname', 2026, 4)
   ```

2. **Check JSON File:**
   ```bash
   cat data/calendar/schedule/profile_surname/2026.json | jq '.[] | select(.week == 4)'
   ```

3. **Check API Endpoints:**
   - `/planning/api/calendar/profiles/2026/4`
   - `/planning/api/calendar/scheduling/all?start_year=2026&start_week=4&weeks=1`
   - `/planning/api/calendar/schedule/2026/4`

All should return the same profile for week 4.

---

## Related Documentation

- `docs/CALENDAR_SYSTEM_AUDIT.md` - System architecture overview
- `docs/CALENDAR_SCHEDULING_NEW_PARADIGM.md` - Architectural paradigm
- `docs/CALENDAR_SCHEDULING_COMPONENT_STRUCTURE.md` - Component reference
- `utils/calendar_resolver.py` - Resolver implementation

---

## Future Improvements

1. **Automatic JSON Regeneration:** Trigger rebuilds automatically when overrides change
2. **Cache Invalidation:** Clear JSON cache when base lists change
3. **Validation:** Add checks to ensure JSON files match resolver output
4. **Monitoring:** Alert if JSON files become stale

---

*Implementation completed: 2026-01-19*
