# Post Types & Publication Scheduling - Implementation

## Overview

This document describes the implementation of post type distinction and per-type publication scheduling. The system now supports three post types: **Recipe**, **Themed**, and **Profile**, each with configurable publication schedules.

## Implementation Date

2025-01-XX

## What Was Implemented

### 1. Database Schema

**File**: `migrations/create_post_type_config.sql`

Created `post_type_config` table to store publication preferences:
- `post_type`: Type identifier (recipe, themed, profile)
- `default_publication_day`: Day of week (1=Monday, 7=Sunday)
- `default_publication_time`: Time of day (HH:MM:SS)
- `timezone`: Timezone for publication
- `is_active`: Enable/disable configuration

**Default Configuration**:
- **Recipe**: Monday, 10:00
- **Themed**: Wednesday, 14:00
- **Profile**: Thursday, 14:00

### 2. Post Type Detection (Backend)

**File**: `blueprints/posts.py`

Updated posts list query to include:
- `recipe_week_number` (for recipe detection)
- `profile_category_id` (for profile detection)
- Added `determine_post_type()` helper function
- Returns `post_type`, `is_recipe`, `is_profile`, `is_themed` flags

### 3. UI Distinction

**File**: `templates/posts_list.html`

Added:
- **Type Column**: New "Type" column in posts table
- **Type Badges**: Color-coded badges with icons:
  - 🥘 Recipe (orange/amber)
  - 📚 Themed (blue)
  - 🏷️ Profile (purple/indigo)
- **Sortable**: Type column is sortable
- **CSS Styling**: Custom badge styling matching post type theme

### 4. API Endpoints

**File**: `blueprints/post_type_config.py`

Created REST API:
- `GET /api/post-type-config/<post_type>` - Get config for specific type
- `GET /api/post-type-config` - Get all configurations
- `PUT /api/post-type-config/<post_type>` - Update configuration
- Helper function: `get_publication_day_for_post_type()` for use in other modules

### 5. Publication Scheduling Integration

**Files Updated**:

1. **`blueprints/automation_calendar.py`**
   - Updated to use `post_type_config` for themed posts
   - Calculates publication date based on configured day (default: Wednesday)
   - Falls back to Wednesday if config not found

2. **`blueprints/recipes.py`**
   - Updated `api_create_recipe_post()` to use recipe config (default: Monday)
   - Automatically sets `weekday` in `calendar_week_posts` based on config

3. **`blueprints/planning_api_posts.py`**
   - Updated `confirm_calendar_idea()` to set weekday for themed posts
   - Uses themed post config (default: Wednesday)

4. **`blueprints/planning_api_profiles.py`**
   - Updated profile creation to use profile config (default: Thursday)
   - Sets weekday when scheduling in calendar

## How It Works

### Post Type Detection Logic

1. **Recipe Posts**: `post.recipe_week_number IS NOT NULL`
2. **Profile Posts**: `post.profile_category_id IS NOT NULL`
3. **Themed Posts**: Everything else (has calendar scheduling but no specific category)

### Publication Scheduling Flow

1. When creating a post:
   - System determines post type
   - Looks up `post_type_config` for that type
   - Sets `calendar_week_posts.weekday` based on config
   - If no config found, uses sensible defaults (Monday for recipes, Wednesday for themed, Thursday for profiles)

2. When scheduling in calendar:
   - `automation_calendar.py` uses themed post config for default scheduling
   - Recipe creation uses recipe config
   - Profile creation uses profile config

3. One-click blog integration:
   - `confirm_calendar_idea()` automatically uses themed post config
   - No manual weekday specification needed

## Usage Examples

### Get Post Type Configuration

```bash
curl http://localhost:5000/api/post-type-config/recipe
```

Response:
```json
{
  "success": true,
  "config": {
    "post_type": "recipe",
    "default_publication_day": 1,
    "default_publication_time": "10:00:00",
    "timezone": "Europe/London",
    "is_active": true,
    "description": "Scottish Recipe Series - Monday morning"
  }
}
```

### Update Configuration

```bash
curl -X PUT http://localhost:5000/api/post-type-config/recipe \
  -H "Content-Type: application/json" \
  -d '{
    "default_publication_day": 1,
    "default_publication_time": "09:00:00",
    "timezone": "Europe/London",
    "is_active": true,
    "description": "Scottish Recipe Series - Monday morning (updated)"
  }'
```

## Files Modified

1. `migrations/create_post_type_config.sql` - New migration
2. `blueprints/posts.py` - Post type detection
3. `templates/posts_list.html` - UI badges and styling
4. `blueprints/post_type_config.py` - New API module
5. `unified_app.py` - Registered new blueprint
6. `blueprints/automation_calendar.py` - Themed post scheduling
7. `blueprints/recipes.py` - Recipe post scheduling
8. `blueprints/planning_api_posts.py` - Themed post creation
9. `blueprints/planning_api_profiles.py` - Profile post creation

## Testing Checklist

- [x] Post type config table created
- [x] Recipe posts show with recipe badge
- [x] Profile posts show with profile badge
- [x] Themed posts show with themed badge
- [x] API endpoints return correct config
- [x] Recipe posts scheduled on Monday (config default)
- [x] Themed posts scheduled on Wednesday (config default)
- [x] Profile posts scheduled on Thursday (config default)
- [x] One-click blog integration works
- [ ] Automated recipe publisher (future enhancement)

## Future Enhancements

1. **Automated Recipe Publisher**: Create `automation_recipe_publisher.py` to automatically:
   - Check current week's recipe
   - Verify post is ready
   - Schedule publication on recipe's default day
   - Publish at scheduled time

2. **Type Filtering**: Add filter dropdown in posts list UI

3. **Type Statistics**: Show counts per type in dashboard

4. **Bulk Operations**: Apply type-specific operations in bulk

## Notes

- Post types are detected automatically based on database fields
- No manual type assignment needed
- Configuration is centralized in `post_type_config` table
- Easy to add new post types in the future
- All scheduling respects the configured days and times

