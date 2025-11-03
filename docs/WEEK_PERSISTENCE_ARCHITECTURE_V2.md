# Week Persistence Architecture V2 - Clean Design

## Design Principles

1. **Year/Week_ID is the Primary Identifier** - Sticky throughout navigation, persistent until explicitly changed
2. **Deprecate idea_id** - Remove from week persistence entirely
3. **Multiple Themes Per Week** - Allowed, but ONE must be "selected"
4. **Multiple Posts Per Week** - Allowed, posts assigned to week/year_id

---

## Proposed Database Schema

### calendar_schedule (Simplified)

```sql
CREATE TABLE calendar_schedule (
    id SERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    
    -- Theme selection (one per week)
    selected_theme_id INTEGER REFERENCES calendar_themes(id) ON DELETE SET NULL,
    is_theme_selected BOOLEAN DEFAULT FALSE, -- Explicit flag for selected theme
    
    -- Post assignments (multiple allowed)
    post_id INTEGER REFERENCES post(id) ON DELETE SET NULL,
    
    scheduled_date DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(year, week_number, selected_theme_id), -- One selected theme per week (but theme can change)
    UNIQUE(year, week_number, post_id), -- Prevent duplicate post assignments
    
    -- Indexes
    INDEX idx_calendar_schedule_year_week ON (year, week_number),
    INDEX idx_calendar_schedule_selected_theme ON (year, week_number, selected_theme_id) WHERE is_theme_selected = TRUE,
    INDEX idx_calendar_schedule_post ON (post_id) WHERE post_id IS NOT NULL
);
```

**Key Points:**
- `selected_theme_id` - ONE theme marked as selected per week
- `is_theme_selected` - Explicit boolean flag (can have multiple entries, but only one with flag=TRUE)
- `post_id` - Multiple posts allowed per week (separate rows)
- NO `idea_id` column (removed/deprecated)

### Alternative: Separate Tables (Cleaner)

For better separation of concerns, consider splitting:

```sql
-- Week metadata and selected theme
CREATE TABLE calendar_week_selection (
    year INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    selected_theme_id INTEGER REFERENCES calendar_themes(id) ON DELETE SET NULL,
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (year, week_number), -- ONE selection per week
    UNIQUE(year, week_number)
);

-- Post assignments to weeks (multiple allowed)
CREATE TABLE calendar_week_posts (
    id SERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    post_id INTEGER REFERENCES post(id) ON DELETE CASCADE,
    scheduled_date DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(year, week_number, post_id) -- Prevent duplicate assignments
);
```

**Benefits:**
- Clear separation: week selection vs post assignments
- Easier queries: `SELECT * FROM calendar_week_selection WHERE year=X AND week_number=Y`
- No confusion between theme selection and post assignment

---

## Data Model Rules

### Theme Selection
- **One selected theme per week** - `calendar_week_selection(year, week_number)` has ONE row
- Selecting a new theme **replaces** the old selection (UPDATE, not INSERT)
- Theme selection persists even if no post exists yet
- Lookup: `SELECT selected_theme_id FROM calendar_week_selection WHERE year=? AND week_number=?`

### Post Assignment
- **Multiple posts allowed per week** - `calendar_week_posts` can have multiple rows for same week
- Each post assignment is independent
- Post can be assigned to week without a selected theme (but not recommended)
- Lookup: `SELECT post_id FROM calendar_week_posts WHERE year=? AND week_number=?`

### Week Context (Navigation)
- **Year/week_id is sticky** - Once set in URL (`?year=2025&week=44`), persists until changed
- `WeekContext` module manages this via URL parameters
- All navigation links automatically include year/week params
- No fallback to `post_id` - week context is primary

---

## API Endpoints (Proposed)

### Theme Selection

```python
# Get selected theme for a week
GET /planning/api/calendar/week/{year}/{week_number}/selected-theme
→ Returns: { selected_theme_id: 123, theme: {...} }

# Select a theme for a week (replaces existing)
POST /planning/api/calendar/week/{year}/{week_number}/select-theme
Body: { theme_id: 123 }
→ Updates calendar_week_selection, returns success

# Get all themes for a week (perpetual + any scheduled)
GET /planning/api/calendar/week/{year}/{week_number}/themes
→ Returns: { themes: [...], selected_theme_id: 123 }
```

### Post Assignment

```python
# Get all posts for a week
GET /planning/api/calendar/week/{year}/{week_number}/posts
→ Returns: { posts: [{ post_id: 1, ... }, { post_id: 2, ... }] }

# Assign post to week
POST /planning/api/calendar/week/{year}/{week_number}/posts
Body: { post_id: 123, scheduled_date: "2025-10-30" }
→ Creates entry in calendar_week_posts

# Remove post from week
DELETE /planning/api/calendar/week/{year}/{week_number}/posts/{post_id}
→ Removes entry from calendar_week_posts
```

### Week Resolution

```python
# Resolve post for week (if only one post, returns it; if multiple, returns first or selected)
GET /planning/api/calendar/week/{year}/{week_number}/resolved-post
→ Returns: { post_id: 123, ... } or null if no posts

# Get full week context
GET /planning/api/calendar/week/{year}/{week_number}
→ Returns: {
    year: 2025,
    week_number: 44,
    selected_theme_id: 123,
    theme: {...},
    posts: [...],
    resolved_post_id: 456  # If multiple, which one?
}
```

---

## Migration Path

### Phase 1: Add New Tables (Non-Breaking)

1. Create `calendar_week_selection` table
2. Create `calendar_week_posts` table
3. Migrate existing `calendar_schedule` data:
   ```sql
   -- Migrate theme selections (take first theme_id per week, mark as selected)
   INSERT INTO calendar_week_selection (year, week_number, selected_theme_id)
   SELECT DISTINCT ON (year, week_number) 
          year, week_number, theme_id
   FROM calendar_schedule
   WHERE theme_id IS NOT NULL
   ORDER BY year, week_number, created_at DESC;
   
   -- Migrate post assignments
   INSERT INTO calendar_week_posts (year, week_number, post_id, scheduled_date)
   SELECT year, week_number, post_id, scheduled_date
   FROM calendar_schedule
   WHERE post_id IS NOT NULL;
   ```

### Phase 2: Update Backend Code

1. Update `api_select_theme_idea()` → `api_select_theme()` to use `calendar_week_selection`
2. Update `resolve_post_for_week()` to query `calendar_week_posts`
3. Remove all `idea_id` references from week persistence code
4. Update `api_calendar_schedule()` to query both tables

### Phase 3: Update Frontend

1. Update theme selection to call new endpoint
2. Update week context to always use year/week (remove post_id fallbacks)
3. Update `WeekContext` to be truly the single source of truth

### Phase 4: Deprecate Old Schema (After Testing)

1. Mark `calendar_schedule.idea_id` as deprecated (add comment)
2. Keep `calendar_schedule` table for backwards compatibility during transition
3. Eventually drop `calendar_schedule` or repurpose it

---

## Benefits of This Design

1. **Clear Separation** - Theme selection vs post assignment are separate concerns
2. **No Ambiguity** - One selected theme per week is explicit
3. **Flexible** - Multiple posts per week are allowed
4. **Predictable** - Year/week_id is always the lookup key
5. **No idea_id Confusion** - Deprecated from week persistence entirely
6. **Scalable** - Easy to add features (e.g., "primary post" flag if multiple posts)

---

## Open Questions

1. **Multiple Posts - Which One is "Active"?**
   - Option A: Return first created (or most recent)
   - Option B: Add `is_primary` flag to `calendar_week_posts`
   - Option C: Match post to selected_theme_id (if post has that theme)

2. **Theme Selection Without Post**
   - Should theme selection require a post? (No - allow selection first)
   - Should post assignment require a selected theme? (Recommended but not required)

3. **Backwards Compatibility**
   - How long to keep `calendar_schedule` table?
   - Should we migrate `idea_id` references to `theme_id` automatically?

---

## Implementation Checklist

- [ ] Create new tables (`calendar_week_selection`, `calendar_week_posts`)
- [ ] Migration script to move data from `calendar_schedule`
- [ ] Update `api_select_theme()` endpoint
- [ ] Update `resolve_post_for_week()` to use new tables
- [ ] Update `api_calendar_schedule()` endpoint
- [ ] Remove `idea_id` references from week persistence code
- [ ] Update frontend theme selection logic
- [ ] Update `WeekContext` to be truly single source
- [ ] Remove post_id fallback logic
- [ ] Test: Theme selection persists across navigation
- [ ] Test: Multiple posts per week work correctly
- [ ] Test: Week context (year/week) is sticky

