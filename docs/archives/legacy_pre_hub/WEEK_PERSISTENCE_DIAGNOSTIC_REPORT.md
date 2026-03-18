# Week Persistence Diagnostic Report

## Executive Summary

The week persistence system has **fundamental architectural issues** that cause confusion between dates, post IDs, and week numbers. The system lacks proper constraints, has inconsistent data models, and uses multiple conflicting resolution strategies.

**Severity: CRITICAL** - These issues cause incorrect data associations and display errors throughout the application.

---

## Critical Issues Identified

### 1. **NO UNIQUE CONSTRAINT ON calendar_schedule (year, week_number)**

**Location**: `migrations/create_calendar_system.sql`, `blueprints/planning_api_calendar_schedule.py`

**Problem**: The `calendar_schedule` table allows multiple entries for the same `year` and `week_number` combination. There is no unique constraint preventing:
- Multiple themes/ideas for the same week
- Multiple posts for the same week
- Conflicting schedule entries

**Evidence**:
```sql
-- From create_calendar_system.sql - NO unique constraint on (year, week_number)
CREATE TABLE calendar_schedule (
    id SERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    -- ... no unique constraint here
);
```

**Impact**: 
- `resolve_post_for_week()` returns the first match with `ORDER BY created_at DESC`, but if multiple posts exist for the same week, the "correct" one is ambiguous
- `api_calendar_schedule()` returns ALL matches, leading to confusion in the frontend
- Theme selection can create new entries without removing old ones

**Example Problematic Query** (from `blueprints/planning_api_calendar_schedule.py:14`):
```python
# Returns ALL schedule entries for a week - could be multiple posts!
WHERE cs.year = %s AND cs.week_number = %s
ORDER BY cs.scheduled_date
```

---

### 2. **Inconsistent Year Handling - calendar_ideas vs calendar_schedule**

**Location**: `migrations/create_calendar_system.sql`, `blueprints/planning_api_calendar_ideas.py`

**Problem**: 
- `calendar_ideas` has `week_number` but **NO `year`** (perpetual ideas)
- `calendar_schedule` requires **BOTH `year` and `week_number`**
- `calendar_events` has **BOTH `year` and `week_number`**

**Evidence**:
```sql
-- calendar_ideas - NO YEAR COLUMN
CREATE TABLE calendar_ideas (
    week_number INTEGER NOT NULL, -- 1-52 (perpetual)
    -- NO year column!
);

-- calendar_schedule - REQUIRES YEAR
CREATE TABLE calendar_schedule (
    year INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
);
```

**Impact**:
- Ideas API endpoint `/planning/api/calendar/ideas/week/{week_number}` only takes `week_number`, ignoring year context
- When selecting an idea for a week, the system must infer which year to use
- Perpetual ideas (same week_number every year) can conflict when scheduled

**Example Problematic Code** (`blueprints/planning_api_calendar_ideas.py:14`):
```python
def api_calendar_ideas(week_number):
    # Only takes week_number - no year context!
    WHERE ci.week_number = %s
```

---

### 3. **Multiple Conflicting Post Resolution Strategies**

**Location**: `utils/week_post_resolver.py`, `blueprints/planning_api_post_specific.py`, `static/js/shared/blog-pipeline-header.js`

**Problem**: There are **at least 5 different ways** the system tries to resolve `post_id` for a week:

1. **Direct post_id lookup** (from URL parameter)
2. **year/week lookup** via `calendar_schedule` (`resolve_post_for_week()`)
3. **theme_id lookup** - find any post with matching theme_id
4. **idea_id lookup** - find any post with matching idea_id  
5. **Post's scheduled week lookup** - get post's year/week from schedule, then find theme

**Evidence**:

**Strategy 1**: Direct lookup (`blueprints/planning_api_post_specific.py:45`)
```python
# Uses post_id directly from URL, ignores year/week
cursor.execute("SELECT expanded_idea FROM post_development WHERE post_id = %s", (post_id,))
```

**Strategy 2**: Year/week lookup (`utils/week_post_resolver.py:43`)
```python
# Gets post_id from calendar_schedule by year/week
SELECT post_id FROM calendar_schedule
WHERE year = %s AND week_number = %s AND post_id IS NOT NULL
ORDER BY created_at DESC LIMIT 1
```

**Strategy 3**: Theme matching across ALL weeks (`blueprints/planning_api_post_specific.py:99`)
```python
# Finds ANY post with this theme_id, regardless of week!
WHERE cs2.theme_id = %s AND cs2.post_id IS NOT NULL
```

**Impact**:
- Different parts of the system use different strategies, leading to mismatches
- Post shown in header may not match post shown in content panel
- Week context in URL can be ignored if post_id is also in URL
- "Week mismatch" detection code in `blog-pipeline-header.js` tries to fix this but adds complexity

---

### 4. **theme_id vs idea_id Confusion**

**Location**: `blueprints/planning_api_calendar_schedule.py`, `blueprints/planning_api_post_specific.py`

**Problem**: `calendar_schedule` has BOTH `theme_id` and `idea_id` columns, with complex backwards-compatibility logic trying to match either.

**Evidence** (`blueprints/planning_api_calendar_schedule.py:190`):
```python
# Tries theme first, then idea (backwards compatibility)
if has_themes_table:
    cursor.execute("SELECT id FROM calendar_themes WHERE id = %s", (idea_id,))
    # ... complex fallback logic
```

**Impact**:
- Schedule entries can have theme_id OR idea_id (or both?)
- Queries must check both columns
- No clear priority - theme_id checked first, but what if both exist?
- Backwards compatibility code makes resolution unpredictable

---

### 5. **Week Number Calculation Can Drift from Dates**

**Location**: `blueprints/planning_api_calendar_events.py`, `migrations/create_calendar_system.sql`

**Problem**: `calendar_events` stores both `start_date`/`end_date` AND `week_number`, but week_number is only "calculated" and not validated against dates.

**Evidence**:
```sql
-- calendar_events schema
week_number INTEGER, -- Calculated from start_date
start_date DATE NOT NULL,
-- NO constraint ensuring week_number matches start_date!
```

**Impact**:
- If week_number is manually updated or calculated incorrectly, it can become out of sync
- Queries that filter by week_number may miss events that actually fall in that week
- No database-level validation ensures consistency

---

### 6. **No Single Source of Truth for Week Context**

**Location**: `static/js/shared/week-context.js`, `static/js/shared/blog-pipeline-header.js`

**Problem**: While `WeekContext` module attempts to be the "single source of truth" for URL parameters, the system still:
- Uses `post_id` from URLs as primary identifier
- Falls back to various resolution strategies when week context is missing
- Has localStorage references (though WeekContext tries to avoid this)

**Evidence** (`static/js/shared/blog-pipeline-header.js:204`):
```javascript
// Still checks post's scheduled week and compares to viewed week
if (viewedYear && viewedWeek) {
    const scheduleResp = await fetch(`/planning/api/posts/${postId}`);
    // ... complex mismatch detection logic
}
```

**Impact**:
- URL parameters (`?year=X&week=Y`) can be ignored if `post_id` is also present
- Complex fallback logic in multiple places
- "Week mismatch" detection tries to fix issues but shouldn't be necessary

---

## Specific Problem Scenarios

### Scenario 1: Multiple Posts for Same Week
1. User selects Theme A for Week 44/2025 → creates `calendar_schedule` entry with `theme_id`
2. User creates Post 1 for Week 44 → updates same schedule entry with `post_id=1`
3. User selects Theme B for Week 44/2025 → creates NEW `calendar_schedule` entry with `theme_id` (old one still exists!)
4. User creates Post 2 for Week 44 → creates another schedule entry
5. **Result**: Week 44 has TWO posts. Which one should `resolve_post_for_week()` return?

### Scenario 2: Post Created Before Theme Selection
1. User creates Post 1 with `post_id=1`
2. Schedule entry created with `post_id=1`, `year=2025`, `week_number=44`, but NO `theme_id`
3. User later selects Theme A for Week 44
4. System tries to find post's schedule entry and update it (`planning_api_post_specific.py:180`)
5. **Result**: Race condition - which entry gets updated? Multiple entries possible.

### Scenario 3: Perpetual Idea Conflict
1. `calendar_ideas` has Idea "Spring Gardening" with `week_number=14` (perpetual)
2. User schedules this for 2025 Week 14 → creates schedule entry
3. User schedules this for 2026 Week 14 → creates ANOTHER schedule entry
4. Both point to same `idea_id`, different years
5. **Result**: System works, but if idea is updated, both years are affected (is this desired?)

---

## Database Schema Issues

### Missing Constraints

1. **No unique constraint on `calendar_schedule(year, week_number, post_id)`**
   - Should prevent same post being scheduled twice for same week
   - Should prevent multiple posts for same week (unless explicitly allowed)

2. **No unique constraint on `calendar_schedule(year, week_number)`**
   - Should ensure only ONE theme/idea selected per week
   - Currently allows multiple selections

3. **No check constraint ensuring `calendar_events.week_number` matches `start_date`**
   - Week number should be calculated and validated against start_date

4. **No foreign key from `calendar_schedule.post_id` to validate post exists**
   - Actually has FK: `post_id INTEGER REFERENCES post(id) ON DELETE SET NULL` ✓
   - But allows NULL, so schedule entries can exist without posts

### Redundant/Confusing Columns

1. **`calendar_schedule` has both `theme_id` and `idea_id`**
   - Should be one or the other, not both
   - Complex backwards-compatibility logic tries to handle both

2. **`calendar_schedule` has `idea_id` AND `event_id`**
   - Original schema allows both
   - Cleanup migration removed this, but code still references it

---

## API Endpoint Inconsistencies

### Endpoints That Don't Require Year

1. `/planning/api/calendar/ideas/week/{week_number}` - Only week_number
2. `/planning/api/calendar/themes/week/{week_number}` - Only week_number
3. `/planning/api/social-focus/week` - Only week (assumes current year?)

### Endpoints That Require Both Year and Week

1. `/planning/api/calendar/events/{year}/{week_number}` - Both required
2. `/planning/api/calendar/schedule/{year}/{week_number}` - Both required

### Endpoints With Mixed Requirements

1. `/planning/api/posts/{post_id}/expanded-idea` - Takes `?year=X&week=Y` as optional params
2. `/planning/api/posts/{post_id}` - May infer week from post's schedule

---

## Frontend Issues

### Multiple Week Context Sources

1. **URL Parameters** (`?year=X&week=Y`) - Primary source per `WeekContext` module
2. **Post ID from URL** (`/posts/{post_id}/...`) - Secondary, can override week context
3. **localStorage** - Some code still references (should be removed per `WeekContext` design)
4. **Window variables** - Legacy code uses `window.year`, `window.weekNumber`

### Week Mismatch Detection

The `blog-pipeline-header.js` has complex logic to detect when:
- Post's scheduled week ≠ viewed week
- Tries to find "correct" post for viewed week
- This should NOT be necessary if system worked correctly

---

## Recommendations

### Priority 1: CRITICAL - Add Database Constraints

1. **Add unique constraint** on `calendar_schedule(year, week_number)` to ensure one schedule entry per week
   - OR allow multiple if needed, but add constraint on `(year, week_number, post_id)` to prevent duplicate posts
   
2. **Add check constraint** on `calendar_events` to ensure `week_number` matches `start_date`
   - Calculate week_number on insert/update using ISO week calculation

3. **Enforce theme_id OR idea_id (not both)** in `calendar_schedule`
   - Add check constraint: `CHECK ((theme_id IS NOT NULL AND idea_id IS NULL) OR (theme_id IS NULL AND idea_id IS NOT NULL) OR (theme_id IS NULL AND idea_id IS NULL AND post_id IS NOT NULL))`

### Priority 2: HIGH - Standardize Resolution Strategy

1. **Establish clear priority order** for post resolution:
   ```
   1. If year/week in URL → use resolve_post_for_week(year, week)
   2. If post_id in URL → get post's scheduled year/week from calendar_schedule
   3. If both → validate they match, error if not
   ```

2. **Make `resolve_post_for_week()` the SINGLE source of truth**
   - Remove all other resolution strategies
   - Update all endpoints to use this function
   - Return clear errors when week has no post (don't fall back silently)

3. **Remove theme_id/idea_id cross-week matching**
   - Don't search for posts with matching theme_id across different weeks
   - Week context should ALWAYS be required

### Priority 3: MEDIUM - Fix Data Model Inconsistencies

1. **Add year column to calendar_ideas queries** (even though ideas are perpetual)
   - When querying ideas for a week, always specify year context
   - Ideas are perpetual, but scheduling them requires year

2. **Remove backwards-compatibility theme_id/idea_id logic**
   - Choose one: either theme_id OR idea_id
   - Migrate all idea_id references to theme_id (or vice versa)
   - Remove dual-checking code

3. **Standardize API endpoints**
   - ALL week-related endpoints should require both `year` and `week_number`
   - Remove endpoints that only take `week_number`

### Priority 4: LOW - Clean Up Frontend

1. **Remove all localStorage week persistence** (already mostly done via WeekContext)
2. **Remove window variable fallbacks** (`window.year`, `window.weekNumber`)
3. **Simplify week mismatch detection** - should not be necessary if backend is fixed

---

## Migration Path

### Phase 1: Add Constraints (Non-Breaking)
1. Add unique constraint on `calendar_schedule(year, week_number)` - may fail if duplicates exist
2. Clean up duplicate schedule entries first
3. Add check constraint on `calendar_events.week_number`
4. Recalculate week_numbers for existing events

### Phase 2: Standardize Resolution (Breaking Changes)
1. Update `resolve_post_for_week()` to enforce strict rules
2. Update all endpoints to use `resolve_post_for_week()`
3. Remove alternative resolution strategies
4. Update frontend to handle "no post for week" errors gracefully

### Phase 3: Data Model Cleanup
1. Decide on theme_id vs idea_id (recommend: keep theme_id, migrate idea_id)
2. Migrate all idea_id references to theme_id
3. Remove idea_id column (or keep for backwards compatibility but mark deprecated)
4. Update all queries to only check theme_id

### Phase 4: API Standardization
1. Update all endpoints to require year + week_number
2. Remove week_number-only endpoints
3. Update frontend to always pass year context

---

## Testing Checklist

After fixes, verify:

- [ ] Only ONE schedule entry can exist per (year, week_number)
- [ ] `resolve_post_for_week(2025, 44)` always returns same result
- [ ] Post created for Week 44 cannot be scheduled for Week 45 without explicit change
- [ ] Theme selection updates existing schedule entry, doesn't create new one
- [ ] Week context in URL always takes precedence over post_id
- [ ] No cross-week theme matching (post for Week 44 theme doesn't appear in Week 45)
- [ ] calendar_events.week_number always matches start_date

---

## Files Requiring Changes

### Database Migrations
- `migrations/create_calendar_system.sql` - Add constraints
- `migrations/cleanup_calendar_schedule_table.sql` - Review for issues

### Backend
- `utils/week_post_resolver.py` - Make it strict, no fallbacks
- `blueprints/planning_api_calendar_schedule.py` - Fix duplicate entry creation
- `blueprints/planning_api_calendar_ideas.py` - Add year context
- `blueprints/planning_api_post_specific.py` - Remove cross-week matching
- `blueprints/planning_api_calendar_events.py` - Add week_number validation

### Frontend
- `static/js/shared/blog-pipeline-header.js` - Simplify, remove mismatch detection
- `static/js/shared/week-context.js` - Already good, ensure all code uses it
- `static/js/planning/calendar-week-view.js` - Ensure year always passed

---

## Conclusion

The week persistence system suffers from **architectural inconsistencies** rather than simple bugs. The lack of database constraints allows invalid states, and multiple resolution strategies create ambiguity. 

**Root Cause**: The system evolved incrementally without a clear data model for how weeks, posts, themes, and ideas should relate. Multiple "fixes" added complexity instead of solving the underlying issues.

**Solution**: Add database constraints to enforce data integrity, standardize on a single resolution strategy, and remove backwards-compatibility code that creates ambiguity.

