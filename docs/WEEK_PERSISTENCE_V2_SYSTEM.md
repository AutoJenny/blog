# Week Persistence V2 - System Documentation

## Overview

Week Persistence V2 is a clean architecture for managing calendar week assignments, theme selections, and post scheduling. It replaces the previous `calendar_schedule` table with two dedicated tables that provide clear separation of concerns and enforce data integrity.

## Architecture

### Core Principles

1. **Year/Week as Primary Identifier**: The `(year, week_number)` tuple is the single source of truth for week context
2. **One Selected Theme Per Week**: Each week must have exactly one selected theme (enforced by PRIMARY KEY)
3. **Multiple Posts Per Week**: Weeks can have multiple posts assigned, with the first/most recent created being the "active" one
4. **No idea_id in Week Persistence**: `idea_id` is deprecated - only `theme_id` is used
5. **Week-Specific Lookups**: No cross-week matching - posts are resolved only within their assigned week

### Database Schema

#### `calendar_week_selection`

Stores the selected theme for each week. One theme must be selected per week.

```sql
CREATE TABLE calendar_week_selection (
    year INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    selected_theme_id INTEGER NOT NULL REFERENCES calendar_themes(id) ON DELETE RESTRICT,
    updated_at TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (year, week_number),
    UNIQUE(year, week_number)
);
```

**Key Constraints:**
- PRIMARY KEY on `(year, week_number)` ensures only one selection per week
- `selected_theme_id` is NOT NULL - theme selection is required
- ON DELETE RESTRICT prevents deleting a theme that's selected

#### `calendar_week_posts`

Stores post assignments to weeks. Multiple posts can be assigned to the same week.

```sql
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
```

**Key Constraints:**
- UNIQUE constraint on `(year, week_number, post_id)` prevents duplicate assignments
- No PRIMARY KEY on `(year, week_number)` allows multiple posts per week
- ON DELETE CASCADE removes assignments when posts are deleted

## Usage Patterns

### 1. Selecting a Theme for a Week

Use `api_select_theme_idea()` endpoint:

```python
POST /api/calendar/select-theme
{
    "theme_id": 123,
    "year": 2024,
    "week_number": 15
}
```

This creates or updates the week's selected theme in `calendar_week_selection`.

### 2. Resolving a Post for a Week

Use the utility function `resolve_post_for_week()`:

```python
from utils.week_post_resolver import resolve_post_for_week

post_id = resolve_post_for_week(year=2024, week_number=15)
# Returns first post if multiple exist, None if no post assigned
```

### 3. Assigning a Post to a Week

When creating a post, assign it to a week:

```python
# First ensure theme is selected
# Then create post and assign:
INSERT INTO calendar_week_posts (year, week_number, post_id, created_at, updated_at)
VALUES (2024, 15, new_post_id, NOW(), NOW())
ON CONFLICT (year, week_number, post_id) DO NOTHING;
```

The `confirm_calendar_idea()` endpoint handles this automatically and requires a selected theme.

### 4. Getting Week Schedule

Use `api_calendar_schedule()` endpoint:

```python
GET /api/calendar/schedule?year=2024&week=15
```

Returns:
```json
{
    "success": true,
    "year": 2024,
    "week_number": 15,
    "selected_theme_id": 123,
    "schedule": [
        {
            "type": "theme_selection",
            "selected_theme_id": 123,
            "theme_title": "Spring Gardening",
            "theme_description": "...",
            "updated_at": "2024-04-10T10:30:00"
        },
        {
            "type": "post",
            "id": 456,
            "post_id": 789,
            "post_title": "Guide to Spring Planting",
            "post_status": "draft",
            "scheduled_date": null,
            "created_at": "2024-04-10T11:00:00"
        }
    ]
}
```

### 5. Route Handler Pattern

In route handlers, resolve posts based on week context:

```python
from flask import request
from utils.week_post_resolver import resolve_post_for_week

def my_route(post_id):
    year = request.args.get('year', type=int)
    week = request.args.get('week', type=int)
    
    # Resolve correct post if week context provided
    resolved_post_id = post_id
    if year and week:
        resolved = resolve_post_for_week(year, week)
        if resolved:
            resolved_post_id = resolved
    
    return render_template('template.html', 
                          post_id=resolved_post_id, 
                          year=year, 
                          week=week)
```

## API Endpoints

### `GET /api/calendar/schedule?year=X&week=Y`

Returns schedule for a specific week including:
- Selected theme
- All posts assigned to the week

**Response Format:**
- Uses new tables if available
- Falls back to old `calendar_schedule` during migration

### `POST /api/calendar/select-theme`

Selects a theme for a week/year.

**Request:**
```json
{
    "theme_id": 123,
    "year": 2024,
    "week_number": 15
}
```

**Response:**
```json
{
    "success": true,
    "year": 2024,
    "week_number": 15,
    "selected_theme_id": 123,
    "updated_at": "2024-04-10T10:30:00"
}
```

**Note:** `idea_id` parameter is deprecated and will be rejected.

### `GET /api/calendar/ideas/<idea_id>/status?year=X&week=Y`

Gets post creation status for a theme in a week.

**Important:** Parameter name is `idea_id` for backwards compatibility, but only `theme_id` values are supported.

**Response:**
```json
{
    "success": true,
    "post": {
        "id": 789,
        "title": "Post Title",
        "status": "draft",
        "scheduled_date": "2024-04-15"
    }
}
```

### `POST /api/posts/confirm-calendar-idea`

Creates a post and assigns it to a week. **Requires** a selected theme.

**Request:**
```json
{
    "topic": "Spring Planting Guide",
    "week_number": 15,
    "year": 2024
}
```

**Response:**
```json
{
    "success": true,
    "post_id": 789
}
```

**Error if no theme selected:**
```json
{
    "success": false,
    "error": "No theme selected for week 2024/15. Please select a theme first."
}
```

## Migration Guide

### Step 1: Create New Tables

Run the table creation script:

```bash
psql -d blog -f migrations/create_week_persistence_v2_tables.sql
```

This creates:
- `calendar_week_selection`
- `calendar_week_posts`
- Indexes and constraints

### Step 2: Migrate Data

Run the data migration script:

```bash
psql -d blog -f migrations/migrate_to_week_persistence_v2.sql
```

This:
- Backs up `calendar_schedule` to `calendar_schedule_v2_backup`
- Migrates theme selections to `calendar_week_selection`
- Migrates post assignments to `calendar_week_posts`

### Step 3: Verify Migration

Run these validation queries:

```sql
-- Check theme selection counts
SELECT 
    (SELECT COUNT(*) FROM calendar_schedule WHERE theme_id IS NOT NULL) as schedule_themes,
    (SELECT COUNT(DISTINCT year, week_number) FROM calendar_schedule WHERE theme_id IS NOT NULL) as unique_week_themes,
    (SELECT COUNT(*) FROM calendar_week_selection) as migrated_selections;

-- Check post assignment counts
SELECT 
    (SELECT COUNT(*) FROM calendar_schedule WHERE post_id IS NOT NULL) as schedule_posts,
    (SELECT COUNT(DISTINCT year, week_number, post_id) FROM calendar_schedule WHERE post_id IS NOT NULL) as unique_week_posts,
    (SELECT COUNT(*) FROM calendar_week_posts) as migrated_posts;
```

### Step 4: Test Application

Test all week-related functionality:
- Selecting themes
- Creating posts
- Resolving posts
- Week navigation

### Step 5: Remove Old Table (After Verification)

Once verified, the old `calendar_schedule` table can be dropped:

```sql
DROP TABLE calendar_schedule CASCADE;
```

**Note:** Keep the backup table (`calendar_schedule_v2_backup`) for rollback if needed.

## Backwards Compatibility

All endpoints include automatic fallback logic:

1. Check if new tables exist
2. If yes: Use new V2 architecture
3. If no: Fallback to old `calendar_schedule` table

This allows:
- Gradual migration without breaking changes
- Running old and new code side-by-side
- Safe rollback if needed

## Key Differences from V1

### V1 (Old System)
- Single `calendar_schedule` table with ambiguous relationships
- Multiple entries per week possible (no unique constraint)
- `idea_id` and `theme_id` mixed usage
- Cross-week matching allowed
- No enforced selected theme

### V2 (New System)
- Two dedicated tables with clear purposes
- PRIMARY KEY enforces one selected theme per week
- Only `theme_id` used (no `idea_id`)
- Week-specific lookups only
- Selected theme required for post creation

## Common Queries

### Get Selected Theme for Week

```sql
SELECT cws.selected_theme_id, ct.theme_title
FROM calendar_week_selection cws
JOIN calendar_themes ct ON cws.selected_theme_id = ct.id
WHERE cws.year = 2024 AND cws.week_number = 15;
```

### Get All Posts for Week

```sql
SELECT cwp.post_id, p.title, p.status
FROM calendar_week_posts cwp
JOIN post p ON cwp.post_id = p.id
WHERE cwp.year = 2024 AND cwp.week_number = 15
ORDER BY cwp.created_at DESC;
```

### Get Active Post for Week (First Created)

```sql
SELECT cwp.post_id, p.title, p.status
FROM calendar_week_posts cwp
JOIN post p ON cwp.post_id = p.id
WHERE cwp.year = 2024 AND cwp.week_number = 15
ORDER BY cwp.created_at DESC
LIMIT 1;
```

## Troubleshooting

### Issue: "No theme selected for week"

**Solution:** Use `api_select_theme_idea()` to select a theme before creating posts.

### Issue: Post not found for week

**Solution:** Ensure post is assigned to the week using `calendar_week_posts` table.

### Issue: Multiple posts in week - which one is active?

**Answer:** The first/most recent created (`ORDER BY created_at DESC`) is considered active.

### Issue: Theme selection not persisting

**Check:**
- `calendar_week_selection` table exists
- PRIMARY KEY constraint is working (only one selection per week)
- API endpoint returns success

## Best Practices

1. **Always Pass Week Context**: Include `?year=X&week=Y` in URLs and API calls
2. **Resolve Posts in Routes**: Use `resolve_post_for_week()` to get correct post
3. **Select Theme First**: Always select theme before creating posts
4. **Week-Specific Queries**: Only query posts within their assigned week
5. **Validate Theme Selection**: Check that theme exists before using it

## Related Documentation

- `docs/WEEK_PERSISTENCE_V2_QUICK_REFERENCE.md` - Quick reference guide
- `docs/WEEK_PERSISTENCE_V2_API_REFERENCE.md` - Complete API documentation
- `docs/WEEK_PERSISTENCE_ARCHITECTURE_V2.md` - Architecture design document
- `docs/AUDIT_DATABASE_SCHEMA.md` - Schema audit findings
- `docs/CHANGE_LOG_WEEK_PERSISTENCE_V2.md` - Detailed change log
- `docs/IMPLEMENTATION_STATUS.md` - Current implementation status

