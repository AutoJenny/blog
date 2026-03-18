# Calendar Scheduling System Audit

**Date**: 2025-01-26  
**Purpose**: Comprehensive audit of the calendar scheduling system to identify issues before UI upgrade

## Executive Summary

The calendar scheduling system manages 8 different content types with inconsistent storage patterns, mixed data models, and incomplete drag-and-drop support. While the system is functional, there are significant architectural inconsistencies that will complicate a unified scheduling interface.

## Content Type Classification

### Category 1: Week-Defining Content (Core)
- **Themes** - Define what a week is "about" in social media terms
  - Multiple themes per week, but only one selected
  - Can be mandatory or random priority

### Category 2: Blog Post Types (Assigned to Week)
- **Recipes** - Recipe blog posts (`post_type='recipe'`)
- **Profiles** - Product/Category profile posts (`post.profile_type IS NOT NULL`)

### Category 3: Supporting Content (Not Standalone Posts)
- **Words of the Week** - Scottish words for newsletter
- **Phrases of the Week** - Scots phrases for newsletter
- **Ideas** - Content ideas (not yet posts)
- **Annual Events** - Recurring annual events
- **Special Events** - One-off events

### Category 4: External Operations
- **Syndication** - Social media posting operations (from Launchpad system)

---

## Database Architecture Analysis

### Tables Used

#### 1. Perpetual Tables (Week Number 1-52, No Year)
- **`calendar_themes`** - Themes (separate table)
- **`calendar_ideas`** - Ideas, Words, Phrases (uses `item_classification` to distinguish)
- **`calendar_recipes`** - Recipe definitions

#### 2. Year-Specific Tables
- **`calendar_events`** - Events (has `year` column)

#### 3. Week Selection Tables
- **`calendar_week_selection`** - Selected theme per week/year (V2 architecture)
- **`calendar_week_posts`** - Posts scheduled to weeks (V2 architecture)
- **`calendar_schedule`** - Legacy table (deprecated, still used as fallback)

#### 4. Post Table
- **`post`** - Stores recipe and profile posts
  - Recipes: `post.recipe_week_number`, `post.recipe_id`
  - Profiles: `post.profile_type`, `post.profile_product_id`, `post.profile_category_id`

### Storage Patterns by Content Type

| Content Type | Storage Table | Week Association | Year Association | Scheduling Table |
|-------------|---------------|------------------|------------------|------------------|
| **Themes** | `calendar_themes` | `week_number` (1-52) | Via `calendar_week_selection` | `calendar_week_selection` |
| **Ideas** | `calendar_ideas` | `week_number` (1-52) | None (perpetual) | None (displayed directly) |
| **Annual Events** | `calendar_events` | `week_number` (calculated) | `year` | None (displayed directly) |
| **Special Events** | `calendar_events` | `week_number` (calculated) | `year` | None (displayed directly) |
| **Recipes** | `calendar_recipes` + `post` | `week_number` (1-52) perpetual | Via `calendar_week_posts` | `calendar_week_posts` |
| **Profiles** | `post` | None (perpetual) | Via `calendar_week_posts` | `calendar_week_posts` |
| **Words/Phrases** | `calendar_ideas` | `week_number` (1-52) | None (perpetual) | None (displayed directly) |
| **Syndication** | External (Launchpad) | Calculated from `scheduled_date` | Calculated from `scheduled_date` | External API |

---

## Critical Issues Identified

### 1. Inconsistent Data Models

**Problem**: Different content types use fundamentally different storage patterns:
- Themes: Separate table + selection table
- Ideas/Words/Phrases: Same table, distinguished by `item_classification`
- Events: Year-specific table
- Recipes: Perpetual table + post table + scheduling table
- Profiles: Post table only + scheduling table
- Syndication: External system

**Impact**: Makes unified scheduling interface difficult. Each type requires different queries and update logic.

**Recommendation**: Consider a unified `calendar_week_items` table that can reference any content type, or at least standardize the scheduling pattern.

### 2. Mixed Classification System

**Problem**: Words and Phrases are stored in `calendar_ideas` table with `item_classification IN ('weekly_word', 'weekly_phrase')`, but they're conceptually different from ideas:
- Ideas are content suggestions
- Words/Phrases are newsletter content snippets

**Impact**: Confusing data model. Queries must filter by `item_classification`, and there's a unique constraint on `(week_number, item_classification)` which prevents multiple words/phrases per week.

**Current Constraint**:
```sql
CREATE UNIQUE INDEX idx_calendar_ideas_week_classification_unique
ON calendar_ideas (week_number, item_classification)
WHERE item_classification IN ('weekly_word', 'weekly_phrase');
```

**Recommendation**: Consider separate `calendar_weekly_words` and `calendar_weekly_phrases` tables, or at least document this clearly.

### 3. Incomplete Scheduling System

**Problem**: Not all content types use the scheduling tables:
- Themes: Use `calendar_week_selection` (one per week)
- Recipes/Profiles: Use `calendar_week_posts` (multiple per week)
- Ideas/Events/Words/Phrases: No scheduling table (displayed directly from perpetual/year tables)
- Syndication: External system

**Impact**: Cannot easily track when items were scheduled, reschedule items, or maintain scheduling history.

**Recommendation**: Either:
- Add scheduling support for all types, OR
- Clearly document which types are "scheduled" vs "displayed"

### 4. Event Type Distinction

**Problem**: Annual Events and Special Events are both stored in `calendar_events` table, distinguished only by:
- `event_recurrence_type = 'annual'` vs `event_recurrence_type = 'one_off'`
- UI rendering logic (different CSS classes)

**Impact**: Works but could be clearer. The distinction is important for UI (separate rows).

**Recommendation**: Consider separate tables or a clearer `event_type` field.

### 5. Recipe Scheduling Complexity

**Problem**: Recipes have a complex two-level system:
1. Perpetual definition in `calendar_recipes` (week_number 1-52)
2. Actual scheduling in `calendar_week_posts` (year/week)
3. Post association via `post.recipe_id` and `post.recipe_week_number`

**Impact**: Confusing which week_number to use. The system calculates mapping from current week, but manual scheduling can override.

**Recommendation**: Document clearly or simplify to one scheduling method.

### 6. Profile Scheduling

**Problem**: Profiles are just posts with `profile_type IS NOT NULL`, scheduled via `calendar_week_posts`. No perpetual definition table.

**Impact**: Profiles can't be "defined" before a post is created (unlike recipes/themes).

**Recommendation**: Consider if profiles need a definition table, or document that they're always created as posts first.

### 7. Syndication External Dependency

**Problem**: Syndication data comes from Launchpad system via API (`/launchpad/api/syndication/schedules`), not from calendar tables.

**Impact**: Cannot schedule syndication items from calendar view. They're read-only display.

**Recommendation**: Either integrate syndication into calendar system, or clearly mark as "external/read-only" in UI.

### 8. Drag & Drop Incomplete

**Problem**: Drag & drop only works for:
- Ideas (`.idea-item`)
- Events (`.event-item`)
- Schedule items (`.schedule-item`)

**Missing**:
- Recipes (`.recipe` items not draggable)
- Profiles (`.profile` items not draggable)
- Words/Phrases (not draggable)
- Syndication (read-only)

**Impact**: Cannot drag & drop to reschedule recipes/profiles/words/phrases.

**Recommendation**: Extend drag & drop to all schedulable types.

### 9. No Unified Item Type Identifier

**Problem**: Each content type uses different identifiers:
- Themes: `theme_id`, `calendar_theme_id`
- Ideas: `idea_id`
- Events: `event_id`, `_eventId`
- Recipes: `recipe_id`, `recipe_week_number`, `_recipe`, `_definition`
- Profiles: `profile_id`, `profile_type`
- Words/Phrases: `idea_id` (shared with ideas!)
- Syndication: `schedule_id`, `_syndication`

**Impact**: No consistent way to identify "what type of item is this" across the system.

**Recommendation**: Add a unified `item_type` field or use a consistent naming pattern.

### 10. UI Organization Issues

**Problem**: All 8 content types are displayed as equal rows, but they have different relationships:
- Themes: Full-width row (not day-specific)
- Events/Ideas/Syndication/Profiles/Words/Recipes: 7-day grid rows
- Some have "Add New" buttons, some don't
- Some are clickable, some aren't

**Impact**: Confusing UX. Users don't understand the hierarchy or relationships.

**Recommendation**: Reorganize UI to show:
- **Week-Level** (Themes, Social Focus)
- **Day-Level** (Events, Ideas, Syndication, Profiles, Words, Recipes)
- **External** (Syndication - mark as read-only)

---

## API Endpoint Analysis

### Current Endpoints

| Content Type | Endpoint | Returns |
|-------------|----------|---------|
| Themes | `/planning/api/calendar/themes/week/{week}` | Perpetual themes |
| Ideas | `/planning/api/calendar/ideas/week/{week}` | Perpetual ideas |
| Events | `/planning/api/calendar/events/{year}/{week}` | Year-specific events |
| Schedule | `/planning/api/calendar/schedule/{year}/{week}` | Selected theme + posts |
| Recipes | `/planning/api/calendar/recipes/{year}/{week}` | Recipe definitions + scheduled posts |
| Profiles | `/planning/api/calendar/profiles/{year}/{week}` | Scheduled profile posts |
| Syndication | `/launchpad/api/syndication/schedules` | External schedules |
| Social Focus | `/planning/api/social-focus/week` | Weekly social focus |

### Issues

1. **Inconsistent Parameters**: Some use `week` only, some use `year/week`
2. **Mixed Response Formats**: Some return arrays, some return objects with nested data
3. **No Unified Endpoint**: Each type has its own endpoint
4. **Missing Update Endpoints**: Not all types have update/reschedule endpoints

---

## Recommendations for UI Upgrade

### Phase 1: Data Model Cleanup (Before UI Work)

1. **Document Content Type Hierarchy**
   - Create clear documentation of which types are "week-defining" vs "assigned"
   - Document which types are "scheduled" vs "displayed"

2. **Standardize Item Identifiers**
   - Add `item_type` field to all scheduling records
   - Use consistent ID naming (`item_id` instead of `theme_id`, `idea_id`, etc.)

3. **Clarify Words/Phrases Storage**
   - Either separate tables or clear documentation
   - Consider if multiple words/phrases per week should be allowed

4. **Unify Scheduling Pattern**
   - Decide: Should all types use `calendar_week_posts` or similar?
   - Or clearly document which types are "perpetual" vs "scheduled"

### Phase 2: UI Reorganization

1. **Group by Category**
   ```
   WEEK-LEVEL CONTENT
   ├── Themes (selected theme highlighted)
   └── Social Focus
   
   DAY-LEVEL CONTENT
   ├── Events (Annual | Special)
   ├── Ideas
   ├── Recipes
   ├── Profiles
   └── Words & Phrases
   
   EXTERNAL OPERATIONS
   └── Syndication (read-only, external)
   ```

2. **Add Drag & Drop for All Schedulable Types**
   - Recipes
   - Profiles
   - Words/Phrases (if multiple allowed)

3. **Unified Scheduling View**
   - New page: `/planning/calendar/week-scheduling/{year}/{week}`
   - List view with drag & drop
   - Group by type
   - Add/remove/reorder interface

4. **Clear Visual Hierarchy**
   - Themes: Prominent, full-width
   - Day-level: Grid layout
   - External: Dimmed, marked as "External"

### Phase 3: Enhanced Features

1. **Scheduling History**
   - Track when items were scheduled/rescheduled
   - Show scheduling conflicts

2. **Bulk Operations**
   - Select multiple items
   - Move to different week/day
   - Delete/archive

3. **Scheduling Rules**
   - Prevent conflicts (e.g., only one recipe per week)
   - Auto-suggest based on type

---

## Files Requiring Updates

### Database Migrations Needed
- [ ] Create unified `calendar_week_items` table (optional)
- [ ] Add `item_type` field to scheduling tables
- [ ] Separate `calendar_weekly_words` and `calendar_weekly_phrases` tables (optional)
- [ ] Document current schema clearly

### API Endpoints to Update
- [ ] Unified `/planning/api/calendar/week/{year}/{week}/items` endpoint
- [ ] Update endpoints for all types
- [ ] Reschedule endpoints for recipes/profiles/words

### Frontend Files
- [ ] `templates/planning/calendar/week_view.html` - Reorganize UI
- [ ] `static/js/planning/calendar-week-view.js` - Extend drag & drop
- [ ] New: `templates/planning/calendar/week_scheduling.html`
- [ ] New: `static/js/planning/calendar-week-scheduling.js`

### Documentation
- [ ] Update `docs/calendar_system_technical_documentation.md`
- [ ] Create content type hierarchy diagram
- [ ] Document scheduling patterns

---

## Conclusion

The system is **functional but inconsistent**. Before building a unified scheduling UI, we should:

1. **Clarify the data model** - Document which types use which storage patterns
2. **Standardize identifiers** - Use consistent naming and add `item_type` fields
3. **Extend drag & drop** - Make all schedulable types draggable
4. **Reorganize UI** - Group by category and show hierarchy clearly

The issues are **manageable** but should be addressed before a major UI upgrade to avoid technical debt and confusion.

