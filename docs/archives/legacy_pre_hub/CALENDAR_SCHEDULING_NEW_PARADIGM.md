# Calendar Scheduling – New JSON-Centric Paradigm

## Overview

This document describes the new architectural model for the calendar scheduling system. It is purely conceptual and contains **no implementation code**.

This paradigm replaces the previous database-heavy approach that suffered from N+1 query problems and slow page loads.

## Objectives

### Primary Goals

1. **Fast Page Load**
   - The planning view must load instantly without hitting the database repeatedly
   - Zero database queries required on page load

2. **Clear System Separation**
   - Simple, clean separation between:
     - Cyclic lists (core data)
     - Per-year plans (calendar layouts)
     - View ranges (what the UI displays)

3. **Scalable for Future Features**
   - Designed to later support:
     - Manual reassignments
     - Drag and drop
     - Override rules
     - Automatic "never run out" repeating when moving into future years
     - Regeneration of plans when the base list changes

4. **Improved User Experience**
   - The planning page should initially show **the next 12 months from today**, not fixed-year boundaries
   - Navigation must allow stepping forward/backward by **months** or **years**

## System Architecture: Five Layers

The system is structured into **five clearly separated layers**.

### Layer 1 — Base Database Lists (Cyclic Sequences)

**Purpose**: Store the core cyclic lists that repeat indefinitely.

**Categories**:
- `theme`
- `recipe`
- `profile_product`
- `profile_surname`
- `weekly_word`
- `weekly_phrase`
- `weekly_insult`

**Structure**: For each category, a simple database table stores:
- `id` - Unique identifier
- `title` (or post reference) - Display name
- `position` - Position in the cycle (1..N)

**Behavior**: These lists define the core cyclic sequences that repeat indefinitely. They are the source of truth for what items exist and their order.

**Modification**: Changes to these lists (add/delete/reorder) will trigger regeneration of affected year plans (Layer 2).

---

### Layer 2 — Per-Category, Per-Year Plans (Logical Calendar)

**Purpose**: Define the intended output for each year and category.

**Structure**: For every year and category, the backend can compute a 52-week plan.

**Example** for `recipe`, 2026:
- Week 1 → recipe #7
- Week 2 → recipe #8
- Week 3 → recipe #9
- ...
- Week 52 → recipe #6

**Computation**: These plans are **not dynamically generated on page load**. They are computed:
- On demand (when first needed)
- When the base list changes (Layer 1)
- When the user performs reassignments
- During scheduled regeneration tasks

**Storage**: These represent the *intended* output for that year. They are stored as JSON files (Layer 3).

---

### Layer 3 — JSON Cache Files (Lightweight Storage)

**Purpose**: Fast, file-based storage for yearly plans. This is what the frontend consumes.

**Location**: `data/calendar/schedule/`

**File Naming Convention**:
```
data/calendar/schedule/theme_2026.json
data/calendar/schedule/recipe_2026.json
data/calendar/schedule/profile_product_2026.json
data/calendar/schedule/profile_surname_2026.json
data/calendar/schedule/weekly_word_2026.json
data/calendar/schedule/weekly_phrase_2026.json
```

**Content**: Each file contains 52 entries, one per ISO week.

**Format**: Standardized JSON structure (see below).

**Benefits**:
- Zero database queries needed on page load
- Fast file system reads
- Easy to inspect and debug
- Version control friendly
- Can be regenerated independently

---

### Layer 4 — Range-Based Scheduling API (View Assembly)

**Purpose**: Assemble and return a week range for the frontend, not a fixed year.

**Endpoint**: Same URL as today for backward compatibility (e.g., `/planning/api/calendar/scheduling/all`)

**Behavior**:
1. Accepts requested range parameters (start_year, start_week, window_length)
2. Determines which years are covered by the range
3. Loads the appropriate JSON files (Layer 3)
4. Merges them into a unified list
5. Sends back a 52-week block in the exact structure the UI expects

**Example Flow**:
- User loads page → server determines `(current_year, current_week)`
- Server returns **52 weeks starting from current week**
- Can cross year boundaries transparently (e.g., Nov 2025 → Oct 2026)

**Characteristics**:
- **Read-only** - Does not alter any scheduling logic
- **Fast** - Only reads JSON files, no database access
- **Flexible** - Can return any range, not just full years

---

### Layer 5 — Frontend View (Dynamic Week Window)

**Purpose**: Display a rolling window of weeks, not fixed year boundaries.

**State Management**: Frontend logic holds:
- `start_year` - Starting year for the view
- `start_week` - Starting ISO week number
- `window_length` - Number of weeks to display (default: 52 weeks)

**Initial Behavior**:
1. Compute current ISO week
2. Request next 52 weeks from backend (Layer 4)
3. Render the resulting rows

**Navigation**:
- **Next month** → add ~4 weeks
- **Previous month** → subtract ~4 weeks
- **Next year** → add 52 weeks
- **Previous year** → subtract 52 weeks

**Action Flow**: Each navigation action:
1. Recalculates `(start_year, start_week)`
2. Requests a new range from the backend (Layer 4)
3. Updates the display

---

## JSON File Structure (Standardized Format)

Each JSON file consists of 52 entries, one per ISO week.

### Standard Format

```json
[
  {
    "week": 1,
    "item": {
      "id": <item id>,
      "title": <string>,
      "position": <integer>
    }
  },
  {
    "week": 2,
    "item": {
      "id": <item id>,
      "title": <string>,
      "position": <integer>
    }
  },
  ...
  {
    "week": 52,
    "item": {
      "id": <item id>,
      "title": <string>,
      "position": <integer>
    }
  }
]
```

### Category Semantics

All categories use this layout, with their own semantics for:
- `id` - Category-specific identifier
- `title` - Display name or reference
- `position` - Position in the base cyclic list (Layer 1)

The frontend does **not** need any extra metadata beyond this structure.

---

## Data Lifecycle

### 1. Initial Generation
- Developer (or background process) builds the JSONs for a year
- They are stored under `data/calendar/schedule/`

### 2. View Consumption
- The view endpoint (Layer 4) reads only these JSONs
- No database queries are performed

### 3. Display
- The page displays a moving window of 52 weeks
- Navigation updates the window without regenerating data

### 4. Modification (Future Phase)
- Changes (add/delete/move) will update:
  - The base DB list (Layer 1)
  - The affected year's JSON file (Layer 3)
- Regeneration logic will ensure consistency

---

## Implementation Phases

### Phase 1 — Display (Current Priority)

**Tasks**:
- Create the JSON structure for each category/year
- Build the range-based display API (Layer 4)
- Build the updated planning page with month/year navigation (Layer 5)
- Validate that the page loads instantly

**Success Criteria**:
- Page loads in < 500ms
- Zero database queries on page load
- Smooth month/year navigation
- Correct display of 12-month rolling window

### Phase 2 — Modification Logic (Future)

**Tasks**:
- Functions to modify base lists (Layer 1)
- Functions to regenerate JSON for a category/year (Layer 2 → Layer 3)
- Rules for "never run out" future filling
- Reassignment UI and endpoints

**Note**: This is intentionally **postponed** until the display is stable.

---

## Key Architectural Principles

### 1. Separation of Concerns
- **Data Storage** (Layer 1) - Database tables
- **Plan Computation** (Layer 2) - Business logic
- **Plan Storage** (Layer 3) - JSON files
- **View Assembly** (Layer 4) - API endpoint
- **User Interface** (Layer 5) - Frontend

### 2. Performance Optimization
- **No database queries in hot path** - All reads from JSON files
- **Pre-computed plans** - Generated once, read many times
- **Range-based requests** - Only load what's needed

### 3. Scalability
- **Independent regeneration** - Each year/category can be regenerated separately
- **Future-proof structure** - Ready for reassignments, overrides, drag-and-drop
- **Clear boundaries** - Each layer has a single responsibility

### 4. User Experience
- **12-month rolling window** - Shows next year from today, not calendar year
- **Flexible navigation** - Month or year steps
- **Fast response** - Instant page loads

---

## Summary: What Developers Must Understand

1. **The UI loads a rolling 12-month window**, not a fixed Jan‑Dec year.

2. **JSON files are the backbone** for the display view. They are pre-computed and stored, not generated on-demand.

3. **The backend API simply merges these JSONs** and returns the requested range. No complex scheduling logic in the view path.

4. **No database access is required** in the hot path (page load).

5. **All complex scheduling logic** will be built on top later, in Phase 2.

6. **This architecture reduces**:
   - The N+1 DB query problem
   - Complexity in "resolve item for week"
   - Load times
   - Cache invalidation bugs

---

## Next Steps

This document serves as the required high-level blueprint. Next steps will be to provide:
- The drop-in backend endpoint file
- The drop-in display template
- The JSON builder skeleton
- The later update/reassignment logic

**DO NOT ATTEMPT TO CODE THIS** until explicit code examples and implementation guidance are provided.

---

## Related Documentation

### Core Architecture
- `CALENDAR_SCHEDULING_COMPONENT_STRUCTURE.md` - Complete component and file structure reference
- `CALENDAR_SCHEDULING_JSON_FORMAT.md` - Detailed JSON file format specification
- `CALENDAR_SCHEDULING_BUILDER.md` - Builder usage and maintenance guide

### Problem Context
- `PERFORMANCE_ISSUE_SCHEDULING_ENDPOINT.md` - Documents the problems this paradigm solves
- `CALENDAR_REASSIGNMENT_SYSTEM_REPORT.md` - Previous system documentation (may be superseded)
- `CALENDAR_SCHEDULING_ENDPOINTS.md` - Current endpoint documentation (may be superseded)

---

*Document created: 2025-01-XX*
*Status: Architectural blueprint - Implementation pending*

