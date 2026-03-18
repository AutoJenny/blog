# Calendar Unified Data Model Implementation Plan

**Date**: 2025-01-26  
**Purpose**: Regularize calendar scheduling system with unified data model for all content types

## Executive Summary

This plan proposes a unified `calendar_week_items` table that provides consistent identification and management for all 8 content types (Themes, Ideas, Events, Recipes, Profiles, Words, Phrases, Syndication). The new model maintains backward compatibility during migration and provides a clear path to deprecate legacy tables.

---

## Proposed Unified Data Model

### Core Table: `calendar_week_items`

```sql
CREATE TABLE calendar_week_items (
    id SERIAL PRIMARY KEY,
    
    -- Unified identification
    item_type VARCHAR(50) NOT NULL CHECK (item_type IN (
        'theme', 'idea', 'annual_event', 'special_event', 
        'recipe', 'profile', 'weekly_word', 'weekly_phrase', 'syndication'
    )),
    item_id INTEGER NOT NULL,  -- References source table (themes.id, ideas.id, etc.)
    
    -- Week association
    year INTEGER NOT NULL,
    week_number INTEGER NOT NULL CHECK (week_number >= 1 AND week_number <= 52),
    
    -- Day-level scheduling (NULL for week-level items like themes)
    weekday INTEGER CHECK (weekday >= 1 AND weekday <= 7),  -- 1=Monday, 7=Sunday
    scheduled_date DATE,  -- Optional specific date
    
    -- Scheduling metadata
    scheduled_at TIMESTAMPTZ DEFAULT NOW(),
    scheduled_by INTEGER REFERENCES users(id),  -- Optional user tracking
    position INTEGER DEFAULT 0,  -- For ordering within same day/type
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Selection/priority flags
    is_selected BOOLEAN DEFAULT FALSE,  -- For themes (one selected per week)
    priority VARCHAR(20) DEFAULT 'normal' CHECK (priority IN ('normal', 'mandatory', 'random')),
    
    -- Metadata
    metadata JSONB DEFAULT '{}',  -- Type-specific data (e.g., syndication platform, recipe definition ID)
    notes TEXT,
    
    -- Timestamps
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Constraints
    UNIQUE(year, week_number, item_type, item_id),  -- Prevent duplicates
    CONSTRAINT valid_weekday CHECK (
        (item_type IN ('theme') AND weekday IS NULL) OR  -- Themes are week-level
        (item_type NOT IN ('theme') AND (weekday IS NULL OR (weekday >= 1 AND weekday <= 7)))
    )
);

-- Indexes
CREATE INDEX idx_calendar_week_items_type_id ON calendar_week_items(item_type, item_id);
CREATE INDEX idx_calendar_week_items_week ON calendar_week_items(year, week_number);
CREATE INDEX idx_calendar_week_items_type_week ON calendar_week_items(item_type, year, week_number);
CREATE INDEX idx_calendar_week_items_selected ON calendar_week_items(year, week_number, is_selected) WHERE is_selected = TRUE;
CREATE INDEX idx_calendar_week_items_active ON calendar_week_items(is_active) WHERE is_active = TRUE;
CREATE INDEX idx_calendar_week_items_weekday ON calendar_week_items(weekday) WHERE weekday IS NOT NULL;
```

### Source Tables (Unchanged)

These tables remain as the "source of truth" for item definitions:

- `calendar_themes` - Theme definitions (perpetual)
- `calendar_ideas` - Idea definitions (perpetual, includes words/phrases via `item_classification`)
- `calendar_events` - Event definitions (year-specific)
- `calendar_recipes` - Recipe definitions (perpetual)
- `post` - Profile posts (`profile_type IS NOT NULL`)
- External API - Syndication (Launchpad system)

### Migration Helper Views

Create views to maintain backward compatibility during migration:

```sql
-- View for themes (replaces calendar_week_selection)
CREATE VIEW calendar_week_selection_v2 AS
SELECT 
    year,
    week_number,
    item_id as selected_theme_id,
    scheduled_at as updated_at
FROM calendar_week_items
WHERE item_type = 'theme' AND is_selected = TRUE;

-- View for posts (replaces calendar_week_posts)
CREATE VIEW calendar_week_posts_v2 AS
SELECT 
    id,
    year,
    week_number,
    item_id as post_id,
    weekday,
    scheduled_date,
    created_at,
    updated_at
FROM calendar_week_items
WHERE item_type IN ('recipe', 'profile');
```

---

## Content Type Mapping

### Current → New Model

| Content Type | Current Storage | New `item_type` | New `item_id` Source | Week Association | Day Association |
|-------------|----------------|-----------------|---------------------|------------------|-----------------|
| **Theme** | `calendar_week_selection` | `'theme'` | `calendar_themes.id` | `year, week_number` | `NULL` (week-level) |
| **Idea** | Direct from `calendar_ideas` | `'idea'` | `calendar_ideas.id` | `year, week_number` | `weekday` (optional) |
| **Annual Event** | Direct from `calendar_events` | `'annual_event'` | `calendar_events.id` | `year, week_number` | `weekday` (from `start_date`) |
| **Special Event** | Direct from `calendar_events` | `'special_event'` | `calendar_events.id` | `year, week_number` | `weekday` (from `start_date`) |
| **Recipe** | `calendar_week_posts` | `'recipe'` | `post.id` | `year, week_number` | `weekday` |
| **Profile** | `calendar_week_posts` | `'profile'` | `post.id` | `year, week_number` | `weekday` |
| **Weekly Word** | Direct from `calendar_ideas` | `'weekly_word'` | `calendar_ideas.id` | `year, week_number` | `NULL` (week-level) |
| **Weekly Phrase** | Direct from `calendar_ideas` | `'weekly_phrase'` | `calendar_ideas.id` | `year, week_number` | `NULL` (week-level) |
| **Syndication** | External API | `'syndication'` | External ID (in `metadata`) | `year, week_number` | `weekday` (from `scheduled_date`) |

### Metadata Field Usage

The `metadata` JSONB field stores type-specific data:

```json
// Recipe
{
  "recipe_definition_id": 123,  // calendar_recipes.id
  "recipe_week_number": 5
}

// Profile
{
  "profile_type": "product",  // or "category"
  "profile_product_id": 456,
  "profile_category_id": null
}

// Syndication
{
  "platform": "facebook",
  "content_type": "product_post",
  "external_schedule_id": 789,
  "operation": "Product",
  "time": "14:00"
}

// Event
{
  "event_recurrence_type": "annual",  // or "one_off"
  "start_date": "2025-11-30",
  "end_date": "2025-12-01"
}
```

---

## Migration Strategy

### Phase 1: Add New Table (Non-Breaking)

1. **Create `calendar_week_items` table**
   - Migration: `migrations/create_calendar_week_items_table.sql`
   - No data migration yet - table starts empty

2. **Create compatibility views**
   - `calendar_week_selection_v2` (for themes)
   - `calendar_week_posts_v2` (for recipes/profiles)

3. **Update API endpoints to write to both tables**
   - Dual-write pattern: Write to old table AND new table
   - Read from old table (backward compatible)

### Phase 2: Data Migration

1. **Migrate Themes**
   ```sql
   INSERT INTO calendar_week_items (item_type, item_id, year, week_number, is_selected, scheduled_at)
   SELECT 'theme', selected_theme_id, year, week_number, TRUE, updated_at
   FROM calendar_week_selection;
   ```

2. **Migrate Recipes**
   ```sql
   INSERT INTO calendar_week_items (item_type, item_id, year, week_number, weekday, scheduled_date, created_at, updated_at, metadata)
   SELECT 
       'recipe', 
       post_id, 
       year, 
       week_number, 
       weekday,
       scheduled_date,
       created_at,
       updated_at,
       jsonb_build_object(
           'recipe_definition_id', p.recipe_id,
           'recipe_week_number', p.recipe_week_number
       )
   FROM calendar_week_posts cwp
   JOIN post p ON cwp.post_id = p.id
   WHERE p.post_type = 'recipe';
   ```

3. **Migrate Profiles**
   ```sql
   INSERT INTO calendar_week_items (item_type, item_id, year, week_number, weekday, scheduled_date, created_at, updated_at, metadata)
   SELECT 
       'profile',
       post_id,
       year,
       week_number,
       weekday,
       scheduled_date,
       created_at,
       updated_at,
       jsonb_build_object(
           'profile_type', p.profile_type,
           'profile_product_id', p.profile_product_id,
           'profile_category_id', p.profile_category_id
       )
   FROM calendar_week_posts cwp
   JOIN post p ON cwp.post_id = p.id
   WHERE p.profile_type IS NOT NULL;
   ```

4. **Migrate Ideas** (from perpetual table, create entries for current year)
   ```sql
   INSERT INTO calendar_week_items (item_type, item_id, year, week_number, scheduled_at)
   SELECT 
       CASE 
           WHEN item_classification = 'weekly_word' THEN 'weekly_word'
           WHEN item_classification = 'weekly_phrase' THEN 'weekly_phrase'
           ELSE 'idea'
       END,
       id,
       EXTRACT(YEAR FROM CURRENT_DATE) as year,
       week_number,
       NOW()
   FROM calendar_ideas
   WHERE item_classification IN ('idea', 'weekly_word', 'weekly_phrase');
   ```

5. **Migrate Events** (already year-specific)
   ```sql
   INSERT INTO calendar_week_items (item_type, item_id, year, week_number, weekday, scheduled_date, metadata)
   SELECT 
       CASE 
           WHEN event_recurrence_type = 'annual' THEN 'annual_event'
           ELSE 'special_event'
       END,
       id,
       year,
       week_number,
       EXTRACT(DOW FROM start_date) + 1 as weekday,
       start_date,
       jsonb_build_object(
           'event_recurrence_type', event_recurrence_type,
           'start_date', start_date::text,
           'end_date', end_date::text
       )
   FROM calendar_events;
   ```

6. **Syndication** (read-only, no migration - handled via API)

### Phase 3: Update Code to Use New Table

1. **Update API endpoints** to read from `calendar_week_items`
2. **Update frontend** to use new unified endpoints
3. **Test all functionality**

### Phase 4: Deprecate Old Tables

1. **Stop writing to old tables**
2. **Monitor for issues**
3. **Eventually drop old tables** (after sufficient testing period)

---

## Files Requiring Updates

### Database Migrations

- [ ] `migrations/create_calendar_week_items_table.sql` - New table
- [ ] `migrations/create_calendar_week_items_views.sql` - Compatibility views
- [ ] `migrations/migrate_calendar_data_to_week_items.sql` - Data migration
- [ ] `migrations/add_calendar_week_items_indexes.sql` - Performance indexes

### API Endpoints (32 files identified)

#### Planning Calendar APIs
- [ ] `blueprints/planning_api_calendar_schedule.py` - **CRITICAL** - Main schedule endpoint
- [ ] `blueprints/planning_api_calendar_ideas.py` - Ideas CRUD
- [ ] `blueprints/planning_api_calendar_events.py` - Events CRUD
- [ ] `blueprints/planning_api_calendar_recipes.py` - Recipes endpoint
- [ ] `blueprints/planning_api_calendar_profiles.py` - Profiles endpoint
- [ ] `blueprints/planning_api_calendar_themes.py` - Themes endpoint
- [ ] `blueprints/planning_api_calendar_utils.py` - Utility functions
- [ ] `blueprints/planning_api_calendar.py` - General calendar API
- [ ] `blueprints/planning_api_calendar_basics.py` - Basic operations
- [ ] `blueprints/planning_api_calendar_content_generator.py` - Content generator
- [ ] `blueprints/planning_api_calendar_social_focus.py` - Social focus

#### Other Blueprints
- [ ] `blueprints/planning_api_posts.py` - Post creation/scheduling
- [ ] `blueprints/planning_api_taxonomy.py` - Taxonomy operations
- [ ] `blueprints/planning_calendar_clean.py` - Calendar routes
- [ ] `blueprints/planning_calendar.py` - Legacy calendar routes
- [ ] `blueprints/planning.py` - Planning routes
- [ ] `blueprints/planning_views.py` - Planning views
- [ ] `blueprints/planning_data.py` - Data operations
- [ ] `blueprints/recipes.py` - Recipe operations
- [ ] `blueprints/posts.py` - Post operations
- [ ] `blueprints/automation_calendar.py` - Automation
- [ ] `blueprints/automation_pipeline.py` - Pipeline automation
- [ ] `blueprints/authoring_api_content.py` - Authoring
- [ ] `blueprints/authoring_api_prompts.py` - Prompts
- [ ] `blueprints/authoring.py` - Authoring routes
- [ ] `blueprints/header/api_prompt_compilation.py` - Prompt compilation
- [ ] `blueprints/header/api_summary_generation.py` - Summary generation
- [ ] `blueprints/header/api_title_generation.py` - Title generation
- [ ] `blueprints/header/api_photo_harvesting.py` - Photo harvesting

### Frontend JavaScript (10 files identified)

- [ ] `static/js/planning/calendar-week-view.js` - **CRITICAL** - Main week view
- [ ] `static/js/planning/calendar-view.js` - Year view
- [ ] `static/js/planning/calendar/ui/calendar-renderer.js` - Rendering logic
- [ ] `static/js/planning/calendar/api/data-loader.js` - API calls
- [ ] `static/js/planning/idea-modal-core.js` - Idea modal
- [ ] `static/js/planning/idea-modal-api.js` - Idea API calls
- [ ] `static/js/planning/idea-modal-conversions.js` - Type conversions
- [ ] `static/js/planning/taxonomy-assignment.js` - Taxonomy
- [ ] `static/js/shared/blog-pipeline-header.js` - Header navigation
- [ ] `static/js/planning/content-generator-modal-core.js` - Content generator

### Templates (10 files identified)

- [ ] `templates/planning/calendar/week_view.html` - **CRITICAL** - Week view template
- [ ] `templates/planning/calendar/ideas_week.html` - Ideas week view
- [ ] `templates/planning/calendar/ideas.html` - Ideas view
- [ ] `templates/planning/calendar.html` - Calendar view
- [ ] `templates/planning/includes/navigation_deprecated.html` - Navigation
- [ ] `templates/shared/data_display.html` - Data display
- [ ] `templates/authoring/includes/database_tables_panel.html` - Database panel
- [ ] `templates/shared/database_tables_panel.html` - Shared database panel
- [ ] `templates/planning/includes/data_tab.html` - Data tab

### Blog-Core Services (7 files identified)

- [ ] `blog-core/newsletter/selectors/words_of_the_week.py` - Words selector
- [ ] `blog-core/newsletter/selectors/theme.py` - Theme selector
- [ ] `blog-core/newsletter/services/events_summary_service.py` - Events summary
- [ ] `blog-core/newsletter/services/event_import_service.py` - Event import
- [ ] `blog-core/newsletter/jobs/prefetch_sources.py` - Prefetch jobs
- [ ] `blog-core/newsletter/services/deduplication_service.py` - Deduplication

### Scripts (8 files identified)

- [ ] `scripts/cleanup_recipe_ideas_from_calendar_ideas.py` - Cleanup script
- [ ] `scripts/populate_recipe_calendar.py` - Recipe population
- [ ] `scripts/fix_seasonal_calendar_content.py` - Seasonal fixes
- [ ] `scripts/fix_calendar_dates.py` - Date fixes
- [ ] `scripts/fix_calendar_weeks.py` - Week fixes
- [ ] `scripts/populate_sample_calendar_data.py` - Sample data
- [ ] `scripts/populate_calendar_weeks.py` - Week population
- [ ] `scripts/evergreen_scheduler.py` - Evergreen scheduling

---

## Breaking Changes Analysis

### API Endpoint Changes

#### 1. Schedule Endpoint (`/planning/api/calendar/schedule/{year}/{week}`)

**Current**: Returns mixed format with `calendar_schedule` entries  
**New**: Returns unified `calendar_week_items` entries

**Breaking**: Response structure changes
```json
// OLD
{
  "schedule": [
    {"type": "theme_selection", "selected_theme_id": 1, ...},
    {"type": "post", "post_id": 2, ...}
  ]
}

// NEW
{
  "items": [
    {"id": 1, "item_type": "theme", "item_id": 1, "is_selected": true, ...},
    {"id": 2, "item_type": "recipe", "item_id": 2, "weekday": 1, ...}
  ]
}
```

**Migration**: Update frontend to handle new format, maintain backward compatibility during Phase 1-2

#### 2. Ideas Endpoint (`/planning/api/calendar/ideas/week/{week}`)

**Current**: Returns ideas directly from `calendar_ideas`  
**New**: Returns ideas from `calendar_week_items` joined with `calendar_ideas`

**Breaking**: May include additional fields (`scheduled_at`, `position`, etc.)

**Migration**: Frontend should ignore new fields if not needed

#### 3. Recipes Endpoint (`/planning/api/calendar/recipes/{year}/{week}`)

**Current**: Returns recipes from `calendar_recipes` + `calendar_week_posts`  
**New**: Returns from `calendar_week_items` where `item_type='recipe'`

**Breaking**: Response structure may change slightly

**Migration**: Update to use new structure

#### 4. Profiles Endpoint (`/planning/api/calendar/profiles/{year}/{week}`)

**Current**: Returns from `calendar_week_posts` joined with `post`  
**New**: Returns from `calendar_week_items` where `item_type='profile'`

**Breaking**: Similar to recipes

#### 5. Theme Selection (`/planning/api/calendar/schedule/select-theme`)

**Current**: Writes to `calendar_week_selection`  
**New**: Writes to `calendar_week_items` with `is_selected=TRUE`

**Breaking**: Endpoint behavior changes (but API contract can remain same)

**Migration**: Dual-write during Phase 1-2

### Frontend Changes

#### 1. Data Loading (`calendar-week-view.js`)

**Current**: Multiple API calls for different types  
**New**: Single unified endpoint or multiple endpoints with consistent format

**Breaking**: API response format changes

**Migration**: Update data loading logic, maintain backward compatibility

#### 2. Drag & Drop

**Current**: Only works for ideas/events/schedule items  
**New**: Should work for all types

**Breaking**: New drag handlers needed

**Migration**: Extend drag & drop to all types

#### 3. Item Identification

**Current**: Uses `theme_id`, `idea_id`, `event_id`, etc.  
**New**: Uses unified `item_type` + `item_id`

**Breaking**: All item identification logic changes

**Migration**: Create helper functions to convert between formats

### Database Query Changes

#### 1. Theme Selection Queries

**Current**:
```sql
SELECT selected_theme_id FROM calendar_week_selection WHERE year=? AND week_number=?
```

**New**:
```sql
SELECT item_id as selected_theme_id 
FROM calendar_week_items 
WHERE item_type='theme' AND year=? AND week_number=? AND is_selected=TRUE
```

#### 2. Post Scheduling Queries

**Current**:
```sql
SELECT post_id FROM calendar_week_posts WHERE year=? AND week_number=?
```

**New**:
```sql
SELECT item_id as post_id 
FROM calendar_week_items 
WHERE item_type IN ('recipe', 'profile') AND year=? AND week_number=?
```

#### 3. Ideas Queries

**Current**:
```sql
SELECT * FROM calendar_ideas WHERE week_number=?
```

**New**:
```sql
SELECT ci.*, cwi.scheduled_at, cwi.position, cwi.weekday
FROM calendar_ideas ci
JOIN calendar_week_items cwi ON ci.id = cwi.item_id
WHERE cwi.item_type='idea' AND cwi.year=? AND cwi.week_number=?
```

---

## Implementation Checklist

### Phase 1: Foundation (Non-Breaking)

- [ ] Create `calendar_week_items` table migration
- [ ] Create compatibility views
- [ ] Add database indexes
- [ ] Write unit tests for table structure
- [ ] Document new schema

### Phase 2: Dual-Write Pattern

- [ ] Update theme selection to write to both tables
- [ ] Update recipe scheduling to write to both tables
- [ ] Update profile scheduling to write to both tables
- [ ] Update idea creation to write to both tables
- [ ] Update event creation to write to both tables
- [ ] Test dual-write doesn't break existing functionality

### Phase 3: Data Migration

- [ ] Write migration script for themes
- [ ] Write migration script for recipes
- [ ] Write migration script for profiles
- [ ] Write migration script for ideas
- [ ] Write migration script for events
- [ ] Run migration on test database
- [ ] Verify data integrity
- [ ] Run migration on production (with backup)

### Phase 4: Read Migration

- [ ] Update schedule endpoint to read from new table
- [ ] Update ideas endpoint to read from new table
- [ ] Update recipes endpoint to read from new table
- [ ] Update profiles endpoint to read from new table
- [ ] Update events endpoint to read from new table
- [ ] Update themes endpoint to read from new table
- [ ] Test all endpoints return correct data

### Phase 5: Frontend Updates

- [ ] Update `calendar-week-view.js` data loading
- [ ] Update item rendering to use unified format
- [ ] Extend drag & drop to all types
- [ ] Update item identification logic
- [ ] Update modals to use new format
- [ ] Test all UI functionality

### Phase 6: Cleanup

- [ ] Remove dual-write (write only to new table)
- [ ] Update all scripts to use new table
- [ ] Update blog-core services
- [ ] Remove compatibility views (optional)
- [ ] Document deprecation of old tables
- [ ] Plan eventual removal of old tables

---

## Testing Strategy

### Unit Tests

- [ ] Test `calendar_week_items` table constraints
- [ ] Test unique constraint prevents duplicates
- [ ] Test weekday constraint for week-level items
- [ ] Test metadata JSONB structure

### Integration Tests

- [ ] Test theme selection creates correct entry
- [ ] Test recipe scheduling creates correct entry
- [ ] Test profile scheduling creates correct entry
- [ ] Test idea creation creates correct entry
- [ ] Test event creation creates correct entry
- [ ] Test querying returns correct items
- [ ] Test updating items
- [ ] Test deleting items

### End-to-End Tests

- [ ] Test week view displays all items correctly
- [ ] Test drag & drop reschedules items
- [ ] Test creating new items from UI
- [ ] Test editing items from UI
- [ ] Test deleting items from UI
- [ ] Test theme selection workflow
- [ ] Test recipe scheduling workflow
- [ ] Test profile scheduling workflow

### Migration Tests

- [ ] Test data migration script
- [ ] Verify all data migrated correctly
- [ ] Test backward compatibility during dual-write
- [ ] Test rollback procedure

---

## Risk Mitigation

### High Risk Areas

1. **Data Loss During Migration**
   - **Mitigation**: Full database backup before migration
   - **Mitigation**: Test migration on copy of production data
   - **Mitigation**: Keep old tables during migration period

2. **API Breaking Changes**
   - **Mitigation**: Maintain backward compatibility during Phase 1-4
   - **Mitigation**: Version API endpoints if needed
   - **Mitigation**: Gradual rollout with feature flags

3. **Frontend Breaking Changes**
   - **Mitigation**: Update frontend gradually
   - **Mitigation**: Test all UI workflows
   - **Mitigation**: Keep old code paths during transition

4. **Performance Degradation**
   - **Mitigation**: Add appropriate indexes
   - **Mitigation**: Monitor query performance
   - **Mitigation**: Optimize queries if needed

### Rollback Plan

1. **If migration fails**: Restore from backup
2. **If API breaks**: Revert to reading from old tables
3. **If frontend breaks**: Revert frontend changes
4. **If performance issues**: Add indexes or optimize queries

---

## Timeline Estimate

- **Phase 1 (Foundation)**: 2-3 days
- **Phase 2 (Dual-Write)**: 3-4 days
- **Phase 3 (Data Migration)**: 2-3 days
- **Phase 4 (Read Migration)**: 4-5 days
- **Phase 5 (Frontend Updates)**: 5-7 days
- **Phase 6 (Cleanup)**: 2-3 days

**Total**: 18-25 days (approximately 4-5 weeks)

---

## Success Criteria

1. ✅ All 8 content types use unified `calendar_week_items` table
2. ✅ All items have consistent `item_type` + `item_id` identification
3. ✅ All scheduling operations work correctly
4. ✅ Drag & drop works for all schedulable types
5. ✅ No data loss during migration
6. ✅ All existing functionality preserved
7. ✅ Performance is acceptable (queries < 100ms)
8. ✅ Documentation updated

---

## Next Steps

1. **Review this plan** with team
2. **Create detailed task breakdown** for each phase
3. **Set up test environment** for migration testing
4. **Begin Phase 1** implementation
5. **Schedule regular checkpoints** to review progress

---

## Appendix: Helper Functions

### Python Helper Functions

```python
def get_item_type_from_source(source_table: str, item_classification: str = None) -> str:
    """Map source table to item_type"""
    mapping = {
        'calendar_themes': 'theme',
        'calendar_ideas': {
            'idea': 'idea',
            'weekly_word': 'weekly_word',
            'weekly_phrase': 'weekly_phrase'
        }.get(item_classification, 'idea'),
        'calendar_events': 'annual_event',  # Will be determined by recurrence_type
        'post': None  # Determined by post_type or profile_type
    }
    return mapping.get(source_table)

def create_week_item(item_type: str, item_id: int, year: int, week_number: int, 
                     weekday: int = None, scheduled_date: date = None, 
                     is_selected: bool = False, metadata: dict = None):
    """Create entry in calendar_week_items"""
    # Implementation
    pass

def get_week_items(year: int, week_number: int, item_type: str = None):
    """Get all items for a week, optionally filtered by type"""
    # Implementation
    pass
```

### JavaScript Helper Functions

```javascript
function getItemType(item) {
    // Determine item_type from item object
    if (item.theme_title) return 'theme';
    if (item._recipe) return 'recipe';
    if (item._profile) return 'profile';
    if (item._syndication) return 'syndication';
    if (item.event_recurrence_type === 'annual') return 'annual_event';
    if (item.event_recurrence_type === 'one_off') return 'special_event';
    if (item.item_classification === 'weekly_word') return 'weekly_word';
    if (item.item_classification === 'weekly_phrase') return 'weekly_phrase';
    return 'idea';
}

function getItemId(item, itemType) {
    // Get item_id based on item_type
    const mapping = {
        'theme': item.id || item.theme_id,
        'idea': item.id || item.idea_id,
        'annual_event': item.id || item.event_id,
        'special_event': item.id || item.event_id,
        'recipe': item.id || item.post_id,
        'profile': item.id || item.post_id,
        'weekly_word': item.id || item.idea_id,
        'weekly_phrase': item.id || item.idea_id,
        'syndication': item.schedule_id || item.id
    };
    return mapping[itemType];
}
```

---

**End of Implementation Plan**

