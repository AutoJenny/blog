# Change Log - Week Persistence Architecture V2

## Executive Summary

This document consolidates all findings from the comprehensive audit and provides a detailed change log for migrating to the new week persistence architecture.

**New Architecture:**
- Year/week_id is primary identifier (sticky throughout navigation)
- Deprecate idea_id from week persistence
- Multiple theme_ids per week allowed, but ONE must be "selected"
- Multiple post_ids per week allowed
- Posts require a selected theme

**New Tables:**
- `calendar_week_selection` - One selected theme per week
- `calendar_week_posts` - Multiple posts per week

---

## Phase 1: Database Changes

### 1.1 Create New Tables

**File:** `migrations/create_week_persistence_v2_tables.sql` (NEW)

```sql
-- Calendar week selection (one theme per week)
CREATE TABLE calendar_week_selection (
    year INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    selected_theme_id INTEGER NOT NULL REFERENCES calendar_themes(id) ON DELETE RESTRICT,
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (year, week_number),
    UNIQUE(year, week_number)
);

CREATE INDEX idx_calendar_week_selection_theme ON calendar_week_selection(selected_theme_id);

-- Calendar week posts (multiple posts per week)
CREATE TABLE calendar_week_posts (
    id SERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    post_id INTEGER NOT NULL REFERENCES post(id) ON DELETE CASCADE,
    scheduled_date DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(year, week_number, post_id)
);

CREATE INDEX idx_calendar_week_posts_year_week ON calendar_week_posts(year, week_number);
CREATE INDEX idx_calendar_week_posts_post_id ON calendar_week_posts(post_id);
```

**Changes Required:**
- Create migration file
- Run migration
- Verify constraints

---

### 1.2 Migrate Data

**File:** `migrations/migrate_to_week_persistence_v2.sql` (NEW)

**Migration Steps:**
1. Backup calendar_schedule table
2. Migrate theme selections (take most recent theme_id per week)
3. Migrate post assignments (all post_id entries)
4. Validate data integrity
5. Rollback plan

**Query to Migrate Themes:**
```sql
INSERT INTO calendar_week_selection (year, week_number, selected_theme_id, updated_at)
SELECT DISTINCT ON (year, week_number)
    year, week_number, theme_id, MAX(updated_at) as updated_at
FROM calendar_schedule
WHERE theme_id IS NOT NULL
GROUP BY year, week_number, theme_id
ORDER BY year, week_number, MAX(updated_at) DESC
ON CONFLICT (year, week_number) DO NOTHING;
```

**Query to Migrate Posts:**
```sql
INSERT INTO calendar_week_posts (year, week_number, post_id, scheduled_date, created_at, updated_at)
SELECT DISTINCT ON (year, week_number, post_id)
    year, week_number, post_id, scheduled_date, created_at, updated_at
FROM calendar_schedule
WHERE post_id IS NOT NULL
ON CONFLICT (year, week_number, post_id) DO NOTHING;
```

---

## Phase 2: Backend API Changes

### 2.1 Core Schedule Endpoints

#### `blueprints/planning_api_calendar_schedule.py`

**`api_calendar_schedule(year, week_number)`**
- **Current:** Queries calendar_schedule, returns all entries
- **Change:** Query calendar_week_selection + calendar_week_posts
- **New Query:**
  ```python
  # Get selected theme
  SELECT cws.selected_theme_id, ct.theme_title, ct.theme_description
  FROM calendar_week_selection cws
  JOIN calendar_themes ct ON cws.selected_theme_id = ct.id
  WHERE cws.year = %s AND cws.week_number = %s
  
  # Get all posts
  SELECT cwp.post_id, cwp.scheduled_date, p.title, p.status
  FROM calendar_week_posts cwp
  LEFT JOIN post p ON cwp.post_id = p.id
  WHERE cwp.year = %s AND cwp.week_number = %s
  ```
- **Response:** Combine theme + posts into unified schedule object
- **Testing:** Verify theme selection, multiple posts

**`api_select_theme_idea()` → `api_select_theme()`**
- **Current:** Creates/updates calendar_schedule entry
- **Change:** Use calendar_week_selection (UPSERT)
- **New Implementation:**
  ```python
  INSERT INTO calendar_week_selection (year, week_number, selected_theme_id, updated_at)
  VALUES (%s, %s, %s, NOW())
  ON CONFLICT (year, week_number)
  DO UPDATE SET selected_theme_id = EXCLUDED.selected_theme_id, updated_at = NOW()
  ```
- **Remove:** idea_id support entirely
- **Testing:** Verify one theme per week, updates work

**`api_calendar_idea_status()` → `api_calendar_theme_status()`**
- **Current:** Complex idea_id/theme_id fallback logic
- **Change:** Query calendar_week_selection + calendar_week_posts
- **Remove:** idea_id parameter, cross-week matching
- **Testing:** Verify post resolution for week

**`api_schedule_update_theme_to_idea()`**
- **Action:** DELETE - No longer needed

---

### 2.2 Post Resolution

#### `utils/week_post_resolver.py`

**`resolve_post_for_week(year, week_number)`**
- **Current:** Queries calendar_schedule
- **Change:** Query calendar_week_posts
- **New Query:**
  ```python
  SELECT post_id
  FROM calendar_week_posts
  WHERE year = %s AND week_number = %s
  ORDER BY created_at DESC
  LIMIT 1
  ```
- **Testing:** Verify returns first post if multiple

---

### 2.3 Post-Specific Endpoints

#### `blueprints/planning_api_post_specific.py`

**`get_post_by_theme()` → `get_post_by_theme_id()`**
- **Current:** Finds post by idea_id across all weeks
- **Change:** Find post in week that has selected theme matching theme_id
- **Remove:** idea_id support
- **Testing:** Verify week-specific matching

**`api_posts_expanded_idea()` - GET**
- **Current:** Cross-week theme matching (finds ANY post with theme)
- **Change:** Require year/week, find post in same week only
- **New Query:**
  ```python
  SELECT pd.expanded_idea
  FROM calendar_week_posts cwp
  JOIN post_development pd ON cwp.post_id = pd.post_id
  WHERE cwp.year = %s AND cwp.week_number = %s
    AND pd.expanded_idea IS NOT NULL
  ORDER BY cwp.created_at DESC
  LIMIT 1
  ```
- **Testing:** Verify week-specific lookup

**`api_posts_expanded_idea()` - POST**
- **Current:** Gets theme from calendar_schedule by post_id
- **Change:** Require year/week in request, get theme from calendar_week_selection
- **Remove:** post_id-based theme lookup, idea_id fallback
- **Testing:** Verify theme requirement, week context required

---

### 2.4 Post Creation

#### `blueprints/planning_api_posts.py`

**`api_posts(post_id)`**
- **Current:** Gets schedule from calendar_schedule by post_id
- **Change:** Accept year/week params, query calendar_week_posts + calendar_week_selection
- **Testing:** Verify schedule data returned correctly

**`confirm_calendar_idea()`**
- **Current:** Inserts into calendar_schedule, no theme requirement
- **Change:** 
  1. Require selected theme exists (query calendar_week_selection)
  2. Insert into calendar_week_posts instead
  3. Use UNIQUE constraint (no manual duplicate cleanup)
- **New Logic:**
  ```python
  # Check theme exists
  SELECT selected_theme_id FROM calendar_week_selection
  WHERE year = %s AND week_number = %s
  # If not found, return error
  
  # Create post (existing)
  
  # Assign to week
  INSERT INTO calendar_week_posts (year, week_number, post_id, scheduled_date)
  VALUES (%s, %s, %s, NULL)
  ON CONFLICT (year, week_number, post_id) DO NOTHING
  ```
- **Testing:** Verify theme requirement enforced, post assignment works

---

### 2.5 Taxonomy

#### `blueprints/planning_api_taxonomy.py`

**`assign_post_taxonomy()`**
- **Current:** Uses idea_id from calendar_schedule
- **Change:** Get selected theme from calendar_week_selection
- **Testing:** Verify theme lookup works

---

## Phase 3: Route Handler Changes

### 3.1 Planning Routes

**File:** `blueprints/planning.py`

**All routes with pattern `/planning/posts/<post_id>/...`**

**Required Pattern:**
```python
@bp.route('/posts/<int:post_id>/...')
def route_handler(post_id):
    # Read week context
    year = request.args.get('year', type=int)
    week = request.args.get('week', type=int)
    
    # Resolve post if week context provided
    if year and week:
        from utils.week_post_resolver import resolve_post_for_week
        resolved_post_id = resolve_post_for_week(year, week)
        if resolved_post_id:
            post_id = resolved_post_id
    
    # Pass to view function
    return view_func(post_id, year=year, week=week)
```

**Routes to Update (20+ routes):**
- All planning views, concept, research, calendar routes
- See `docs/AUDIT_ROUTES.md` for complete list

---

### 3.2 Authoring Routes

**File:** `blueprints/authoring.py`

**Required Changes:**
- Same pattern as planning routes
- Read year/week, resolve post, pass context

**Routes to Update (5+ routes):**
- All authoring section routes

---

### 3.3 Routes Already Correct

**Files:**
- `blueprints/authoring_api_imaging.py` - Already uses resolve_post_for_week()
- `blueprints/imaging.py` - Already uses resolve_post_for_week()

**Action:** No changes needed

---

## Phase 4: Frontend Changes

### 4.1 JavaScript Updates Needed

#### `static/js/shared/blog-pipeline-header.js`

**Current Issues:**
- Complex week mismatch detection logic
- Tries to find "correct" post when week doesn't match
- Uses post_id as fallback

**Required Changes:**
1. Simplify - rely on week context from URL only
2. Remove week mismatch detection (shouldn't be necessary)
3. Ensure all links include year/week params
4. Remove post_id fallback logic

---

#### `static/js/planning/calendar-week-view.js`

**Current:** Reads week context, makes API calls
**Required:** 
- Ensure year/week always in API calls
- Update to use new API endpoints
- Remove idea_id references

---

#### `static/js/planning/taxonomy-assignment.js`

**Current:** Passes year/week to API
**Required:** Verify API calls use new endpoints

---

#### `static/js/shared/week-context.js`

**Status:** Already correct - keep as-is
**Action:** Ensure all code uses WeekContext module

---

### 4.2 Template Updates

**All templates using post_id or week context:**

**Required Pattern:**
```javascript
// Read week context from URL
const weekContext = window.WeekContext ? window.WeekContext.getWeekContext() : null;

// Make API calls with year/week
if (weekContext) {
    fetch(`/api/endpoint?year=${weekContext.year}&week=${weekContext.week}`)
}
```

**Templates to Update:**
- All planning templates (31 files)
- All authoring templates (47 files)
- See audit plan for complete list

---

## Phase 5: Migration Execution Order

### Step 1: Database Migration
1. Create new tables (calendar_week_selection, calendar_week_posts)
2. Migrate data from calendar_schedule
3. Validate data integrity
4. Keep calendar_schedule table (for rollback)

### Step 2: Backend Updates
1. Update `resolve_post_for_week()` utility
2. Update `api_calendar_schedule()` endpoint
3. Update `api_select_theme()` endpoint
4. Update post-specific endpoints
5. Remove deprecated endpoints

### Step 3: Route Updates
1. Update planning routes (batch by file)
2. Update authoring routes
3. Test redirects preserve week context

### Step 4: Frontend Updates
1. Update JavaScript API calls
2. Update templates
3. Test week persistence in navigation

### Step 5: Testing
1. Unit tests for new endpoints
2. Integration tests for week persistence
3. Manual testing of full pipeline
4. Verify no data loss

### Step 6: Cleanup
1. Mark calendar_schedule columns as deprecated
2. Document migration in CHANGELOG
3. Remove old endpoints after verification

---

## Testing Checklist

### Database
- [ ] New tables created with correct constraints
- [ ] Data migrated correctly (counts match)
- [ ] Theme selections preserved (one per week)
- [ ] Post assignments preserved (all posts)
- [ ] No duplicate entries created

### Backend APIs
- [ ] `api_calendar_schedule()` returns theme + posts
- [ ] `api_select_theme()` updates calendar_week_selection
- [ ] `resolve_post_for_week()` uses calendar_week_posts
- [ ] `api_posts_expanded_idea()` uses new tables
- [ ] `confirm_calendar_idea()` requires selected theme
- [ ] All endpoints remove idea_id references

### Routes
- [ ] Week context preserved in URLs
- [ ] Post resolution works correctly
- [ ] Redirects include year/week params
- [ ] Templates receive week context

### Frontend
- [ ] Week context persists in navigation
- [ ] API calls include year/week
- [ ] Theme selection works
- [ ] Post assignment works
- [ ] No console errors

---

## Rollback Plan

1. **If migration fails:**
   - Restore from calendar_schedule_backup
   - Drop new tables
   - Revert code changes

2. **If data issues found:**
   - Keep both old and new tables during transition
   - Fix data in new tables
   - Verify before dropping old table

3. **If performance issues:**
   - Add additional indexes
   - Optimize queries
   - Monitor database performance

---

## Dependencies

### Must Complete First
1. Database migration (creates tables)
2. Data migration (populates tables)
3. `resolve_post_for_week()` update (used by routes)

### Can Parallel
- Backend endpoint updates (after resolve_post_for_week)
- Route handler updates
- Frontend updates

### Final Steps
- Remove deprecated code
- Update documentation
- Clean up old tables (after verification)

---

## Files Summary

### Files Requiring Changes: ~60 files

**Database (2 new files):**
- `migrations/create_week_persistence_v2_tables.sql`
- `migrations/migrate_to_week_persistence_v2.sql`

**Backend (8 files):**
- `utils/week_post_resolver.py`
- `blueprints/planning_api_calendar_schedule.py`
- `blueprints/planning_api_post_specific.py`
- `blueprints/planning_api_posts.py`
- `blueprints/planning_api_taxonomy.py`
- `blueprints/planning.py` (20+ routes)
- `blueprints/authoring.py` (5+ routes)
- `blueprints/planning_calendar_clean.py`

**Frontend (20+ files):**
- `static/js/shared/blog-pipeline-header.js`
- `static/js/planning/calendar-week-view.js`
- `static/js/planning/taxonomy-assignment.js`
- All authoring panel JS files
- All template files (78+ files)

### Files to Delete
- Endpoint: `api_schedule_update_theme_to_idea()` - Remove entirely

---

## Estimated Effort

- Database migration: 2-4 hours
- Backend updates: 8-12 hours
- Route updates: 4-6 hours
- Frontend updates: 12-16 hours
- Testing: 8-10 hours
- **Total: 34-48 hours**

---

## Risk Assessment

**High Risk:**
- Data migration (must preserve all data)
- Post resolution changes (affects many pages)

**Medium Risk:**
- API endpoint changes (frontend must update)
- Route updates (navigation must work)

**Low Risk:**
- Frontend template updates (mostly adding params)
- Removing deprecated code (after verification)

---

## Success Criteria

1. All theme selections preserved and working
2. All post assignments preserved
3. Week context persists throughout navigation
4. No data loss or corruption
5. All endpoints respond correctly
6. Frontend displays correct data
7. Performance acceptable

---

## Notes

- Keep calendar_schedule table during transition for rollback
- Test thoroughly before removing deprecated code
- Document all changes in commit messages
- Update API documentation
- Update user documentation if needed

