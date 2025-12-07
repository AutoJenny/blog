# Calendar Scheduling - Component Structure Reference

This document lists all components, files, and their responsibilities in the new JSON-centric calendar scheduling system.

## Quick Summary

### Data Files
- `data/schedule/theme/YYYY.json`
- `data/schedule/recipe/YYYY.json`
- `data/schedule/profile_product/YYYY.json`
- `data/schedule/profile_surname/YYYY.json`
- `data/schedule/weekly_word/YYYY.json`
- `data/schedule/weekly_phrase/YYYY.json`
- `data/schedule/meta/YYYY.json`

### Backend - Display Layer
- `blueprints/planning_api_calendar_scheduling_cache.py` (rewritten to be JSON-backed, range-based)
- `utils/calendar_json_loader.py` (optional helper)

### Backend - Builder/Maintenance
- `utils/calendar_schedule_builder.py`
- `scripts/build_calendar_schedules.py` or CLI integration

### Backend - Base List Management
- `blueprints/planning_api_calendar_cyclic.py` (already present but should be "pure list")

### Backend - Future Overrides/Reassignments
- `blueprints/planning_api_calendar_overrides.py` (future phase)

### Frontend
- `templates/planning/calendar/scheduling.html` (updated JS + navigation)

### Config/Docs
- `config/calendar_settings.py` (or equivalent)
- `docs/CALENDAR_SCHEDULING_JSON_FORMAT.md`
- `docs/CALENDAR_SCHEDULING_BUILDER.md`

---

## 1. JSON Data Files (Per Category, Per Year)

### Directory
**Location**: `data/calendar/schedule/`

### Files (One Per Category Per Year)
- `data/calendar/schedule/theme_YYYY.json`
- `data/calendar/schedule/recipe_YYYY.json`
- `data/calendar/schedule/profile_product_YYYY.json`
- `data/calendar/schedule/profile_surname_YYYY.json`
- `data/calendar/schedule/weekly_word_YYYY.json`
- `data/calendar/schedule/weekly_phrase_YYYY.json`

**Format**: See `docs/CALENDAR_SCHEDULING_JSON_FORMAT.md` for exact structure.

**Content**: Each file contains metadata (`category`, `year`, `generated_at`) and a `weeks` object mapping week numbers (1-52) to item objects.

**Generation**: Created by the builder script (see `docs/CALENDAR_SCHEDULING_BUILDER.md`).

---

## 2. Backend: Display API (JSON-Backed, Range-Based)

### 2.1 Main Endpoint Blueprint

**File**: `blueprints/planning_api_calendar_scheduling_cache.py`

**Status**: Existing file to replace or heavily rewrite

**Responsibilities**:
- Expose `GET /planning/api/calendar/scheduling/all`
- Accept parameters:
  - `start_year` (optional, defaults to current year)
  - `start_week` (optional, defaults to current ISO week)
  - `weeks` (optional, defaults to 52)
- Default behavior: "current ISO week + next 52 weeks"
- Read the relevant JSON files for all categories and years touched by that range
- Merge them into the shape expected by `scheduling.html` (existing frontend format)
- Return JSON structure:
  ```json
  {
    "success": true,
    "data": {
      "current_year": <int>,
      "current_week": <int>,
      "range_start_year": <int>,
      "range_start_week": <int>,
      "range_weeks": <int>,
      "weeks": [
        {
          "year": <int>,
          "week": <int>,
          "schedule": [
            { "category": "theme", "item": {...} },
            { "category": "recipe", "item": {...} },
            ...
          ]
        },
        ...
      ]
    }
  }
  ```

**Key Characteristics**:
- **Read-only** - Does not modify any scheduling logic
- **Fast** - Only reads JSON files, no database access
- **Range-based** - Can return any week range, not just full years
- **Year-boundary aware** - Handles ranges that cross year boundaries

### 2.2 Backend Helpers

**File**: `utils/calendar_json_loader.py` (optional, but cleaner separation)

**Alternative**: Can be inside the same blueprint file if preferred

**Responsibilities**:
- Resolve project root and JSON directory path
- Given `(category, year)` → load JSON, validate it, and return `week → item` map
- Handles both new format (object with metadata and weeks dict) and legacy format (flat list) for backward compatibility
- Basic error handling:
  - Missing files → return empty map
  - Malformed JSON → return empty map with logging
- Utility functions:
  - `load_category_year_schedule(category, year)` → returns dict mapping week numbers (int) to item dicts
  - `get_schedule_base_dir()` → returns absolute path to `data/calendar/schedule/`
  - `get_schedule_json_path(category, year)` → returns full path to JSON file

---

## 3. Backend: JSON Builder / Maintenance

**Note**: These are **not** hit on page load. They're tools for developers, cron jobs, or scripts.

### 3.1 JSON Builder Module

**File**: `utils/calendar_schedule_builder.py`

**Status**: ✅ Implemented

**Responsibilities**:

**For a given `(category, year)`**:
- Read base DB list (e.g. `calendar_themes`, `calendar_recipes`, etc.)
- Apply cyclic logic to fill 52 weeks for that year
- Respect any override rules once we add them (future phase)
- Produce the in-memory structure that matches the JSON format
- Return the 52-week schedule as a list

**For a given `year`**:
- Build JSON for all categories for that year
- Write all category files plus meta to `data/schedule/`

**Key Functions**:
- `build_category_year(category, year)` → returns list of 52 week entries
- `write_category_year_json(category, year)` → builds and writes JSON file
- `build_year_all_categories(year)` → builds all categories for a year
- `build_multiple_years(years)` → builds multiple years

**Dependencies**:
- Database access (reads from Layer 1 - base lists)
- May need cycle start week configuration
- May need override rules (future)

### 3.2 Management Script / CLI Command

**Choose one pattern** that matches your project:

**Option A - Flask CLI**:
- `manage_calendar_schedules.py` or extend existing `manage.py`

**Option B - Standalone Script**:
- `scripts/build_calendar_schedules.py` ✅ Implemented

**Responsibilities**:
- CLI interface to:
  - `build-year --year 2025` → builds all categories for 2025
  - `build-category --category theme --year 2025` → builds one category/year
  - `rebuild-all --start-year 2025 --end-year 2027` → rebuilds year range (inclusive)
- Calls into `utils/calendar_schedule_builder.py`
- Writes the JSON files to `data/calendar/schedule/{category}_{year}.json`
- Provides progress feedback
- Handles errors gracefully
- Exits with appropriate status codes (0 = success, non-zero = failure)

**Example Usage**:
```bash
python scripts/build_calendar_schedules.py --year 2025
python scripts/build_calendar_schedules.py --year 2025 --category theme
python scripts/build_calendar_schedules.py --year 2025 --extra-years 2
```

---

## 4. Backend: List Management (Base Cyclic Lists)

**File**: `blueprints/planning_api_calendar_cyclic.py`

**Status**: Already exists, may need cleanup

**Responsibilities**:
- APIs for base lists only (Layer 1):
  - `POST /planning/api/calendar/list/reorder` - Reorder items in a list
  - `POST /planning/api/calendar/list/add` - Add item to a list
  - `POST /planning/api/calendar/list/delete` - Delete item from a list
- **No override/week-logic in here** - This is pure list management
- After any change:
  - Optionally trigger or queue rebuild of affected JSON files
  - e.g., rebuild same-year JSON or mark as stale
  - Could call the builder script or queue a background task

**Key Principle**: This module should be "list-only" and not week-aware. It manages the base cyclic sequences (Layer 1), not the calendar assignments.

---

## 5. Backend: Optional Override / Reassignment Layer (Future Phase)

**File**: `blueprints/planning_api_calendar_overrides.py`

**Status**: Future phase - not needed for initial display implementation

**Responsibilities** (later):
- `POST /planning/api/calendar/override/set` - Set an override for a specific week
- `POST /planning/api/calendar/override/remove` - Remove an override
- Update either:
  - DB override tables, OR
  - Directly patch per-year JSON and rewrite the file
- Optionally provide an endpoint to:
  - "Recompute year from base lists + overrides"

**Note**: For now, you don't need this implemented to get the fast display working. This is Phase 2 functionality.

---

## 6. Frontend: Display Template & JS

**File**: `templates/planning/calendar/scheduling.html`

**Status**: Already exists, will need updating

**Responsibilities**:

### Table UI
- Weeks × categories table (existing structure)
- Render returned `weeks[]` into the table

### On Load
- Compute "initial" `start_year`, `start_week` (or just rely on backend defaults)
- Call `/planning/api/calendar/scheduling/all` with the proper query string
- Render returned `weeks[]` into the table

### New UI Elements/Logic

#### 1. Navigation Controls
- Buttons or controls for:
  - `<< Year` (previous year)
  - `< Month` (previous month)
  - `Month >` (next month)
  - `Year >>` (next year)
- Maintain a small JS state:
  - `viewStartYear`
  - `viewStartWeek`
- On click, adjust that state and refetch from the same endpoint

#### 2. Range Awareness (Optional but Helpful)
- Display: "Showing weeks Wxx–Wyy (YYYY–YYYY)"
- Uses the metadata returned by the endpoint (`range_start_year`, `range_start_week`, `range_weeks`)

#### 3. (Later) Reassignment UI
- Keep the modal structure (if it exists)
- But change the logic to:
  - Talk to override/reassignment endpoints (Phase 2)
  - Trigger JSON rebuild or flag stale

---

## 7. Configuration / Docs

### 7.1 Config

**File**: `config/calendar_settings.py` or part of your general config

**Status**: Optional but useful

**Responsibilities**:
- **Paths**:
  - Base directory for JSON schedule files (`data/calendar/schedule/`)
- **Defaults**:
  - Default window length in weeks (e.g., 52)
  - Default start behavior (current week vs. year start)
- **Category Names**:
  - List of supported categories
  - Category display names
  - Category-to-table mappings
- **Constraints**:
  - Max years ahead to pre-generate
  - Min/max weeks in a range request

**Example Structure**:
```python
CALENDAR_SCHEDULE_DIR = "data/calendar/schedule"
CALENDAR_DEFAULT_WEEKS = 52
CALENDAR_CATEGORIES = [
    "theme",
    "recipe",
    "profile_product",
    "profile_surname",
    "weekly_word",
    "weekly_phrase"
]
```

### 7.2 Documentation Files

#### `docs/CALENDAR_SCHEDULING_JSON_FORMAT.md`
- Exact JSON structure per category
- Example file contents
- Field descriptions
- Validation rules

#### `docs/CALENDAR_SCHEDULING_BUILDER.md`
- How to run the builder
- What triggers rebuilds
- What to do when adding/removing list items
- Troubleshooting guide

---

## 8. (Optional but Recommended) Tests

**Files**:
- `tests/test_calendar_schedule_builder.py`
- `tests/test_calendar_scheduling_endpoint.py`

### Test: Schedule Builder
**File**: `tests/test_calendar_schedule_builder.py`

**Verify**:
- Given a small base list, JSON output has correct cyclic behavior
- Week 1 starts at the correct position
- Week 52 wraps correctly
- All 52 weeks are present

### Test: Scheduling Endpoint
**File**: `tests/test_calendar_scheduling_endpoint.py`

**Verify**:
- Given some JSON fixtures, the API returns the expected merged week range
- Year boundary crossing works correctly
- Missing JSON files are handled gracefully
- Range parameters are respected

---

## Component Dependencies

```
Frontend (scheduling.html)
    ↓
Backend API (planning_api_calendar_scheduling_cache.py)
    ↓
JSON Loader (calendar_json_loader.py) [optional]
    ↓
JSON Files (data/schedule/**/*.json)
    ↑
Builder (calendar_schedule_builder.py)
    ↑
Base Lists (planning_api_calendar_cyclic.py)
    ↑
Database Tables (Layer 1)
```

---

## Implementation Order

### Phase 1: Display (Current Priority)
1. Create JSON format documentation
2. Create builder module and script
3. Generate initial JSON files for current year + next year
4. Rewrite display API to read JSON files
5. Update frontend with navigation controls
6. Test page load performance

### Phase 2: Modification (Future)
1. Clean up list management API
2. Add rebuild triggers on list changes
3. Implement override/reassignment layer
4. Add UI for reassignments

---

## Related Documentation

- `CALENDAR_SCHEDULING_NEW_PARADIGM.md` - High-level architectural overview
- `CALENDAR_SCHEDULING_JSON_FORMAT.md` - JSON file structure details
- `CALENDAR_SCHEDULING_BUILDER.md` - Builder usage and maintenance
- `PERFORMANCE_ISSUE_SCHEDULING_ENDPOINT.md` - Problems this solves

---

*Document created: 2025-01-XX*
*Status: Component structure reference - Implementation pending*

