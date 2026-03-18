# Calendar Unified Data Model - Implementation Progress

**Date**: 2025-01-26  
**Status**: Phase 1, 2, 3, and Phase 4 (Partial) Complete

## Completed Work

### Phase 1: Foundation ✅

1. **Database Table Created**
   - ✅ `calendar_week_items` table created with all required fields
   - ✅ 10 indexes created for performance
   - ✅ Constraints implemented (unique, weekday validation, theme selection)
   - ✅ Table comments and documentation added

2. **Compatibility Views Created**
   - ✅ `calendar_week_selection_v2` - For theme selection queries
   - ✅ `calendar_week_posts_v2` - For post scheduling queries
   - ✅ `calendar_week_items_summary` - Unified view with joined source data

3. **Helper Functions Created**
   - ✅ `utils/calendar_week_items.py` - Complete helper library
   - ✅ Functions for create, read, update, delete operations
   - ✅ Theme selection helper
   - ✅ Type mapping utilities

### Phase 2: Dual-Write Pattern ✅

1. **Theme Selection**
   - ✅ Updated `api_select_theme_idea()` in `blueprints/planning_api_calendar_schedule.py`
   - ✅ Writes to both `calendar_week_selection` (old) and `calendar_week_items` (new)
   - ✅ Maintains backward compatibility

2. **Recipe Scheduling**
   - ✅ Updated `confirm_calendar_idea()` in `blueprints/planning_api_posts.py`
   - ✅ Updated recipe creation in `blueprints/recipes.py`
   - ✅ Writes to both `calendar_week_posts` (old) and `calendar_week_items` (new)
   - ✅ Includes recipe metadata (definition_id, week_number)

3. **Profile Scheduling**
   - ✅ Updated `confirm_calendar_idea()` in `blueprints/planning_api_posts.py`
   - ✅ Writes to both `calendar_week_posts` (old) and `calendar_week_items` (new)
   - ✅ Includes profile metadata (profile_type, product_id, category_id)

### Phase 3: Data Migration ✅

1. **Migration Scripts Created**
   - ✅ `migrations/migrate_calendar_data_to_week_items.sql` - SQL migration
   - ✅ `migrations/run_migration_calendar_data.py` - Python migration runner

2. **Data Migrated**
   - ✅ 198 Ideas migrated (94 ideas + 52 weekly_words + 52 weekly_phrases)
   - ✅ 41 Events migrated (7 annual + 34 special)
   - ✅ Themes: 0 (table doesn't exist yet - will be created when needed)
   - ✅ Recipes: 0 (table doesn't exist yet - will be created when needed)
   - ✅ Profiles: 0 (table doesn't exist yet - will be created when needed)

3. **Migration Results**
   - ✅ Total: 239 items in `calendar_week_items`
   - ✅ All data integrity verified
   - ✅ Migration handles missing tables gracefully

### Phase 4: Read Migration (Partial) ✅

1. **Schedule Endpoint**
   - ✅ Updated `api_calendar_schedule()` to read from `calendar_week_items`
   - ✅ Maintains fallback to V2 tables and legacy `calendar_schedule`
   - ✅ Returns unified format with `item_type` and metadata

2. **Recipes Endpoint**
   - ✅ Updated `api_calendar_recipes()` to read from `calendar_week_items`
   - ✅ Maintains fallback to `calendar_week_posts`
   - ✅ Handles recipe definitions and scheduled posts

3. **Profiles Endpoint**
   - ✅ Updated `api_calendar_profiles()` to read from `calendar_week_items`
   - ✅ Maintains fallback to `calendar_week_posts` and `calendar_schedule`
   - ✅ Returns profile data with metadata

## Current State

### Database
- ✅ New `calendar_week_items` table exists with 239 items
- ✅ Old tables still in use (backward compatibility maintained)
- ✅ Dual-write pattern active for themes, recipes, and profiles
- ✅ All migrated data verified

### Code
- ✅ Helper functions available in `utils/calendar_week_items.py`
- ✅ Theme selection writes to both tables
- ✅ Recipe scheduling writes to both tables
- ✅ Profile scheduling writes to both tables
- ✅ Schedule endpoint reads from `calendar_week_items` (primary) with fallbacks
- ✅ Recipes endpoint reads from `calendar_week_items` (primary) with fallbacks
- ✅ Profiles endpoint reads from `calendar_week_items` (primary) with fallbacks
- ⏳ Ideas endpoint - Still reads from `calendar_ideas` (perpetual, may stay as-is)
- ⏳ Events endpoint - Still reads from `calendar_events` (year-specific, may stay as-is)

## Next Steps

### Phase 4: Complete Read Migration (Optional)
- ⏳ Update ideas endpoint (optional - ideas are perpetual, may stay on source table)
- ⏳ Update events endpoint (optional - events are year-specific, may stay on source table)
- ⏳ Update themes endpoint (optional - themes use selection table)

**Note**: Ideas and Events may remain on their source tables since they're perpetual/year-specific. The `calendar_week_items` entries for them are for tracking which items are "active" for specific years/weeks.

### Phase 5: Frontend Updates (Pending)
1. Update `calendar-week-view.js` data loading
2. Update item rendering to use unified format
3. Extend drag & drop to all types
4. Update item identification logic
5. Update modals to use new format

### Phase 6: Cleanup (Future)
1. Remove dual-write (write only to new table)
2. Update all scripts to use new table
3. Update blog-core services
4. Document deprecation of old tables
5. Plan eventual removal of old tables

## Testing Status

- ✅ Table creation verified
- ✅ Indexes verified
- ✅ Views verified
- ✅ Data migration verified (239 items)
- ✅ Syntax validation passed
- ⏳ Functional testing pending (test theme selection, recipe scheduling, API endpoints)

## Files Modified

### New Files
- `migrations/create_calendar_week_items_table.sql`
- `migrations/create_calendar_week_items_views.sql`
- `migrations/run_migration_calendar_week_items.py`
- `migrations/migrate_calendar_data_to_week_items.sql`
- `migrations/run_migration_calendar_data.py`
- `utils/calendar_week_items.py`
- `docs/diagnostics/calendar_unified_model_progress.md`

### Modified Files
- `blueprints/planning_api_calendar_schedule.py` - Dual-write + read from unified table
- `blueprints/planning_api_posts.py` - Dual-write for recipe/profile scheduling
- `blueprints/recipes.py` - Dual-write for recipe creation
- `blueprints/planning_api_calendar_recipes.py` - Read from unified table
- `blueprints/planning_api_calendar_profiles.py` - Read from unified table

## Notes

- All changes are **backward compatible** - old tables still work
- Dual-write ensures no data loss during migration
- New table is being read from for schedule, recipes, and profiles
- Ideas and Events remain on source tables (perpetual/year-specific nature)
- Next phase will update frontend to use unified format
