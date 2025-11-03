# Week Persistence V2 - Implementation Status

## Completed Changes

### Database Migration Scripts
✅ Created `migrations/create_week_persistence_v2_tables.sql`
✅ Created `migrations/migrate_to_week_persistence_v2.sql`

### Core Utilities
✅ Updated `utils/week_post_resolver.py`
  - Now queries `calendar_week_posts` (with fallback during migration)
  - Returns first post if multiple exist

### Backend API Endpoints
✅ Updated `blueprints/planning_api_calendar_schedule.py`
  - `api_calendar_schedule()` - Uses new tables, returns unified response
  - `api_select_theme_idea()` - Uses `calendar_week_selection`, removes idea_id support
  - `api_calendar_idea_status()` - Uses new tables, removes cross-week matching
  - `api_schedule_update_theme_to_idea()` - Marked as deprecated, returns 410

✅ Updated `blueprints/planning_api_posts.py`
  - `api_posts()` - Uses new tables for schedule lookup
  - `confirm_calendar_idea()` - Requires selected theme, uses `calendar_week_posts`

✅ Updated `blueprints/planning_api_post_specific.py`
  - `get_post_by_theme()` - Uses new tables, removed idea_id support
  - `api_posts_expanded_idea()` GET - Uses new tables, week-specific only
  - `api_posts_expanded_idea()` POST - Requires year/week, uses `calendar_week_selection`

✅ Updated `blueprints/planning_api_taxonomy.py`
  - `assign_post_taxonomy()` - Uses new tables, week-specific post lookup

## Remaining Work

### Route Handlers (Medium Priority)
✅ Updated `blueprints/planning_views.py` - All routes resolve posts and pass week context
✅ Updated `blueprints/planning_concept.py` - All routes resolve posts and pass week context  
✅ Updated `blueprints/planning_calendar_clean.py` - `planning_calendar_week_view` resolves posts
- [ ] Update `blueprints/authoring.py` routes (uses resolve_post_for_week already via API endpoints)
- [ ] Ensure all routes preserve week context in redirects (most already do)

### Frontend JavaScript (Medium Priority)
- [ ] Update `static/js/shared/blog-pipeline-header.js` - Simplify week mismatch detection
- [ ] Update `static/js/planning/calendar-week-view.js` - Use new API responses
- [ ] Update `static/js/planning/taxonomy-assignment.js` - Verify API calls

### Templates (Low Priority - Can be done incrementally)
- [ ] Ensure all templates pass year/week to API calls
- [ ] Update templates to handle new API response formats

## Migration Steps Remaining

1. **Run database migration** (when ready):
   ```bash
   psql -d blog -f migrations/create_week_persistence_v2_tables.sql
   psql -d blog -f migrations/migrate_to_week_persistence_v2.sql
   ```

2. **Test migration** - Verify data migrated correctly

3. **Update remaining route handlers**

4. **Update frontend code**

5. **Test full pipeline**

6. **Remove deprecated code** (after verification)

## Backwards Compatibility

All updated endpoints include fallback logic:
- Check if new tables exist
- If yes: Use new V2 architecture
- If no: Fallback to old `calendar_schedule` table

This allows gradual migration without breaking existing functionality.

