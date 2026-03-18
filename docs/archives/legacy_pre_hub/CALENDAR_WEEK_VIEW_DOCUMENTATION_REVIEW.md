# Calendar Week View Documentation Review

**Date**: 2025-01-24  
**Page**: `/planning/posts/<post_id>/calendar/week-view?year=2025&week=48`  
**Reviewer**: AI Assistant

## Executive Summary

The main documentation file (`docs/calendar_system_technical_documentation.md`) provides a good overview of the calendar system architecture, but it is **outdated** and **incomplete** with respect to the actual week-view implementation. Several key features, API endpoints, and data structures are missing or incorrectly documented.

## Route Handler Analysis

### Current Implementation
**File**: `blueprints/planning_calendar_clean.py:104-168`

**Key Features**:
1. **Week Context Required**: Reads `year` and `week` from URL query parameters
2. **Post Resolution**: Uses `resolve_post_for_week()` to resolve the correct post for themed posts
3. **Post Type Handling**: Special handling for `recipe` and `profile` post types (preserves original post_id)
4. **Template**: Renders `planning/calendar/week_view.html`

### Documentation Status
- ✅ Route path documented correctly: `/planning/posts/<post_id>/calendar/week-view`
- ❌ **Missing**: Week context requirement (year/week query params)
- ❌ **Missing**: Post resolution logic for week-based posts
- ❌ **Missing**: Special handling for recipe/profile post types

## API Endpoints Comparison

### Documented vs. Actual Endpoints

| Endpoint | Documentation | Actual Implementation | Status |
|----------|--------------|----------------------|--------|
| Get ideas for week | `/planning/api/calendar/ideas/<week_number>` | `/planning/api/calendar/ideas/week/<week_number>` | ❌ **Incorrect path** |
| Get events | `/planning/api/calendar/events/<year>/<week_number>` | `/planning/api/calendar/events/<year>/<week_number>` | ✅ Correct |
| Get schedule | `/planning/api/calendar/schedule/<year>/<week_number>` | `/planning/api/calendar/schedule/<year>/<week_number>` | ✅ Correct |
| Get themes | **Not documented** | `/planning/api/calendar/themes/week/<week_number>` | ❌ **Missing** |
| Get profiles | **Not documented** | `/planning/api/calendar/profiles/<year>/<week_number>` | ❌ **Missing** |
| Get recipes | **Not documented** | `/planning/api/calendar/recipes/<year>/<week_number>` | ❌ **Missing** |
| Get content generator | **Not documented** | `/planning/api/calendar/content-generator/<year>/<week_number>` | ❌ **Missing** |
| Get syndication schedules | **Not documented** | `/launchpad/api/syndication/schedules?platform=facebook&content_type=product` | ❌ **Missing** |
| Get social focus | **Not documented** | `/planning/api/social-focus/week` | ❌ **Missing** |

### JavaScript Implementation
**File**: `static/js/planning/calendar-week-view.js:467-480`

The week-view loads data from **9 different API endpoints** in parallel:
1. Ideas (week-only, no year)
2. Events (year + week)
3. Schedule (year + week)
4. Product syndication schedules
5. Blog post syndication schedules
6. Social focus (week-only)
7. Profiles (year + week)
8. Recipes (year + week)
9. Content generator posts (year + week)

**Documentation Status**: Only 2 of 9 endpoints are documented, and one has an incorrect path.

## Database Schema Comparison

### Documented Tables
The documentation mentions:
- `calendar_weeks` - ✅ Exists and accurate
- `calendar_ideas` - ✅ Exists and accurate
- `calendar_events` - ✅ Exists and accurate
- `calendar_schedule` - ⚠️ **Partially accurate** (still used but deprecated in favor of V2)
- `calendar_categories` - ✅ Exists and accurate

### Missing from Documentation
The following tables are used by the week-view but not documented:

1. **`calendar_themes`** - Stores weekly themes (separate from ideas)
   - Used by: `/planning/api/calendar/themes/week/<week_number>`
   - Purpose: Perpetual themes that appear every year in the same week

2. **`calendar_week_selection`** - Week Persistence V2 table
   - Purpose: One selected theme per week (PRIMARY KEY: year, week_number)
   - Used by: Week resolution logic

3. **`calendar_week_posts`** - Week Persistence V2 table
   - Purpose: Post assignments to weeks (allows multiple posts per week)
   - Used by: Week resolution logic

4. **Profile-related tables** - Used for product/profile posts
   - Purpose: Store profile definitions and assignments

5. **Recipe-related tables** - Used for recipe posts
   - Purpose: Store recipe definitions and week assignments

6. **Syndication tables** - Used for social media scheduling
   - Purpose: Track scheduled posts across platforms

7. **Social focus tables** - Used for weekly social media focus
   - Purpose: Track daily social media focus topics

## UI Features Comparison

### Documented Features
- ✅ 52-week structure
- ✅ Visual indicators for content types
- ✅ Priority highlighting (mandatory vs. random)
- ✅ Category color coding
- ✅ Interactive elements (add, edit, delete)

### Missing from Documentation
The week-view includes many features not documented:

1. **Week Navigation**
   - Previous/Next week buttons
   - "This week" button
   - Week picker popup (month/year selector)

2. **Content Type Filters**
   - Themes toggle
   - Annual Events toggle
   - Special Events toggle
   - Ideas toggle
   - Syndication toggle
   - Profiles toggle
   - Content Generator toggle
   - Recipes toggle

3. **Content Rows**
   - Themes row (full-width, above day headers)
   - Annual Events row (7-day grid)
   - Special Events row (7-day grid)
   - Ideas row (7-day grid)
   - Syndication row (7-day grid)
   - Profiles row (7-day grid)
   - Content Generator row (7-day grid)
   - Recipes row (7-day grid)

4. **Day Headers**
   - Day names (Mon-Sun)
   - Calendar day numbers
   - Social focus indicators per day

5. **Advance Notice System**
   - Events can span multiple weeks
   - Visual indicators for events starting in future weeks
   - Arrow indicators showing event progression

6. **Modals**
   - Idea Modal (for themes, ideas, events)
   - Profile Modal (for product profiles)
   - Content Generator Modal (for generated posts)
   - Social Focus Modal (for daily social focus)

## Week Persistence V2 Integration

### Current Status
The week-view uses **Week Persistence V2** architecture, which is partially documented in:
- `docs/WEEK_PERSISTENCE_V2_SYSTEM.md`
- `docs/WEEK_PERSISTENCE_V2_API_REFERENCE.md`
- `docs/WEEK_PERSISTENCE_V2_QUICK_REFERENCE.md`

However, the main `calendar_system_technical_documentation.md` does **not** mention:
- The V2 architecture
- The `calendar_week_selection` table
- The `calendar_week_posts` table
- The `resolve_post_for_week()` function
- The week context requirement

### Recommendation
The main calendar documentation should reference or include information about Week Persistence V2, or at least link to the V2 documentation.

## Post Type Handling

### Current Implementation
The route handler has special logic for different post types:

```python
# Recipe/Profile posts: Preserve original post_id
if year and week and original_post_type not in ('recipe', 'profile'):
    resolved = resolve_post_for_week(year, week)
    if resolved:
        resolved_post_id = resolved
```

**Documentation Status**: ❌ **Not documented**

## Recommendations

### High Priority
1. **Update API Endpoint Documentation**
   - Fix the ideas endpoint path: `/planning/api/calendar/ideas/week/<week_number>`
   - Add all missing endpoints (themes, profiles, recipes, content-generator, syndication, social-focus)

2. **Document Week Context Requirement**
   - Clarify that `year` and `week` query parameters are required for week-view
   - Document the post resolution logic

3. **Document Post Type Handling**
   - Explain special handling for recipe/profile posts
   - Document when post resolution occurs vs. when original post_id is preserved

4. **Add Missing Database Tables**
   - Document `calendar_themes` table
   - Document Week Persistence V2 tables (`calendar_week_selection`, `calendar_week_posts`)
   - Document profile, recipe, and syndication tables (or link to their documentation)

### Medium Priority
5. **Document UI Features**
   - Add section describing week navigation controls
   - Document content type filters
   - Document all content rows and their purposes
   - Document modal interactions

6. **Link to Related Documentation**
   - Add references to Week Persistence V2 docs
   - Link to profile documentation
   - Link to recipe documentation
   - Link to syndication documentation

### Low Priority
7. **Update Examples**
   - Add example URLs with week context
   - Add example API responses for all endpoints
   - Add screenshots or UI mockups

8. **Add Troubleshooting Section**
   - Common issues with week context
   - Post resolution problems
   - API endpoint errors

## Conclusion

The `calendar_system_technical_documentation.md` file provides a solid foundation but is significantly outdated. The week-view implementation has evolved to include many features not documented, and several documented features are incorrect or incomplete.

**Recommendation**: Create a comprehensive update to the documentation, or create a separate `calendar_week_view_documentation.md` file that focuses specifically on the week-view page, with cross-references to the main calendar documentation.

