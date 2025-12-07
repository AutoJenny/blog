# Performance Issue: Calendar Scheduling Endpoint

## Problem
The endpoint `/planning/api/calendar/scheduling/all` is extremely slow, taking many seconds to load.

## Root Cause: N+1 Query Problem

### Endpoint Location
- **File**: `blueprints/planning_api_calendar_scheduling_cache.py`
- **Function**: `api_calendar_scheduling_all()` (line 78)
- **Route**: `GET /planning/api/calendar/scheduling/all`

### Call Chain
1. Frontend calls: `/planning/api/calendar/scheduling/all`
2. Handler calls: `build_year_schedule(year, weeks=52)` (line 208)
3. Location: `utils/calendar_resolver.py::build_year_schedule()` (line 312)

### The Problem
`build_year_schedule()` loops through 52 weeks and for each week calls `resolve_item_for_week()` **7 times**:
- 1x for theme
- 1x for recipe  
- 3x for profiles (product, category, surname)
- 1x for weekly_word
- 1x for weekly_phrase

**Total: 52 weeks × 7 categories = 364 calls to `resolve_item_for_week()`**

### Each `resolve_item_for_week()` Call Makes Multiple Database Queries

**Location**: `utils/calendar_resolver.py::resolve_item_for_week()` (line 215)

Each call performs:
1. `get_week_override()` - Opens cursor, queries `calendar_week_overrides` table
   - Location: `utils/calendar_resolver.py::get_week_override()` (line 171)
   - Query: `SELECT * FROM calendar_week_overrides WHERE year = %s AND week_number = %s AND category = %s`

2. `get_list_length()` - Opens cursor, queries category table for COUNT
   - Location: `utils/calendar_resolver.py::get_list_length()` (line 106)
   - Query: `SELECT COUNT(*) AS cnt FROM {table}` (where table is calendar_themes, calendar_recipes, etc.)

3. `get_cycle_start_week()` - Opens cursor, queries `calendar_category_cycles` table
   - Location: `utils/calendar_resolver.py::get_cycle_start_week()` (line 76)
   - Query: `SELECT cycle_start_week FROM calendar_category_cycles WHERE category = %s`

4. `get_item_by_position()` - Opens cursor, queries category table for item
   - Location: `utils/calendar_resolver.py::get_item_by_position()` (line 132)
   - Query: `SELECT * FROM {table} WHERE {position_column} = %s`

**Total per call: ~4 database queries × 364 calls = ~1,456 database queries**

### Database Connection Pattern
Each function uses `db_manager.get_cursor()` which creates a new cursor and connection context. This means:
- 364 separate cursor contexts
- Each context has connection overhead
- No query batching or connection reuse

### Cache Behavior
**Location**: `blueprints/planning_api_calendar_scheduling_cache.py`

- Cache file: `data/calendar_scheduling_cache.json`
- Cache TTL: 300 seconds (5 minutes) - line 20
- Cache check: Line 119-120 compares `current_year` and `current_week`
- **Problem**: If cache is expired or invalid, it regenerates all 364 calls

### Performance Impact
- **With cache**: Fast (reads JSON file)
- **Without cache**: Very slow (1,456+ database queries)
- **Cache invalidation**: Happens on every override set/remove (line 566, 541 in `planning_api_calendar_cyclic.py`)

## Files Involved

1. **Endpoint Handler**:
   - `blueprints/planning_api_calendar_scheduling_cache.py::api_calendar_scheduling_all()` (line 78)

2. **Schedule Builder**:
   - `utils/calendar_resolver.py::build_year_schedule()` (line 312)

3. **Resolver Functions** (called 364 times):
   - `utils/calendar_resolver.py::resolve_item_for_week()` (line 215)
   - `utils/calendar_resolver.py::get_week_override()` (line 171)
   - `utils/calendar_resolver.py::get_list_length()` (line 106)
   - `utils/calendar_resolver.py::get_cycle_start_week()` (line 76)
   - `utils/calendar_resolver.py::get_item_by_position()` (line 132)

4. **Cache Management**:
   - `blueprints/planning_api_calendar_scheduling_cache.py::load_scheduling_cache()` (line 28)
   - `blueprints/planning_api_calendar_scheduling_cache.py::save_scheduling_cache()` (line 50)
   - `blueprints/planning_api_calendar_scheduling_cache.py::invalidate_scheduling_cache()` (line 64)

5. **Cache Invalidation Triggers**:
   - `blueprints/planning_api_calendar_cyclic.py::api_override_set()` (line 566)
   - `blueprints/planning_api_calendar_cyclic.py::api_override_remove()` (line 541)

## Database Tables Queried

1. `calendar_week_overrides` - Override lookups (364 queries)
2. `calendar_themes` - Theme items (52 queries)
3. `calendar_recipes` - Recipe items (52 queries)
4. `calendar_profile_sequence` - Profile items (156 queries: 52 weeks × 3 types)
5. `calendar_ideas` - Word/phrase items (104 queries: 52 weeks × 2 types)
6. `calendar_category_cycles` - Cycle configuration (364 queries)

## Solution Approaches

### Option 1: Batch Query Optimization
Modify `build_year_schedule()` to:
- Load all overrides for the year in one query
- Load all list lengths once per category (7 queries total)
- Load all cycle start weeks once per category (7 queries total)
- Load all items by position in batch queries

**Estimated reduction**: 1,456 queries → ~50-100 queries

### Option 2: Single Cursor Context
Pass a single cursor context through all resolver functions to reuse connections.

### Option 3: Pre-compute and Cache More Aggressively
- Cache at the database query level, not just the final result
- Use Redis or similar for query result caching

### Option 4: Materialized View
Create a database view that pre-computes the schedule for all weeks.

## Current Cache Status
- Cache file exists: `data/calendar_scheduling_cache.json`
- Cache age: ~112 seconds (within 300s TTL)
- Cache should be valid, but endpoint still slow

## Additional Notes
- Frontend template: `templates/planning/calendar/scheduling.html`
- Frontend calls endpoint on page load (line 243)
- Frontend uses cache-busting parameter `?_t={timestamp}` which doesn't affect backend cache

