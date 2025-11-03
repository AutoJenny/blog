# Week Persistence V2 - Quick Reference Guide

## Quick Start

### 1. Select Theme for Week
```python
POST /api/calendar/select-theme
{
    "theme_id": 123,
    "year": 2024,
    "week_number": 15
}
```

### 2. Create Post (Requires Selected Theme)
```python
POST /api/posts/confirm-calendar-idea
{
    "topic": "Post Title",
    "week_number": 15,
    "year": 2024
}
```

### 3. Resolve Post for Week
```python
from utils.week_post_resolver import resolve_post_for_week

post_id = resolve_post_for_week(year=2024, week_number=15)
```

### 4. Get Week Schedule
```python
GET /api/calendar/schedule?year=2024&week=15
```

## Database Tables

### `calendar_week_selection`
- **Purpose**: One selected theme per week
- **Key**: PRIMARY KEY (year, week_number)
- **Required**: selected_theme_id (NOT NULL)

### `calendar_week_posts`
- **Purpose**: Post assignments to weeks
- **Key**: UNIQUE (year, week_number, post_id)
- **Allows**: Multiple posts per week

## Route Handler Pattern

```python
from flask import request
from utils.week_post_resolver import resolve_post_for_week

def my_route(post_id):
    year = request.args.get('year', type=int)
    week = request.args.get('week', type=int)
    
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

## Common SQL Queries

### Get Selected Theme
```sql
SELECT selected_theme_id FROM calendar_week_selection
WHERE year = 2024 AND week_number = 15;
```

### Get Active Post (First Created)
```sql
SELECT post_id FROM calendar_week_posts
WHERE year = 2024 AND week_number = 15
ORDER BY created_at DESC LIMIT 1;
```

### Get All Posts for Week
```sql
SELECT post_id FROM calendar_week_posts
WHERE year = 2024 AND week_number = 15
ORDER BY created_at DESC;
```

## Key Rules

1. ✅ Year/Week is primary identifier
2. ✅ One selected theme per week (enforced)
3. ✅ Multiple posts allowed per week
4. ✅ Theme required for post creation
5. ✅ Week-specific lookups only (no cross-week)
6. ❌ No idea_id in week persistence

## API Response Formats

### Schedule Response
```json
{
    "success": true,
    "year": 2024,
    "week_number": 15,
    "selected_theme_id": 123,
    "schedule": [
        {"type": "theme_selection", ...},
        {"type": "post", ...}
    ]
}
```

## Migration Checklist

- [ ] Run `create_week_persistence_v2_tables.sql`
- [ ] Run `migrate_to_week_persistence_v2.sql`
- [ ] Verify data counts match
- [ ] Test theme selection
- [ ] Test post creation
- [ ] Test post resolution
- [ ] Test week navigation
- [ ] Remove old table (after verification)

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "No theme selected" | Call `api_select_theme_idea()` first |
| Post not found | Check `calendar_week_posts` assignment |
| Multiple posts | Use first created (`ORDER BY created_at DESC`) |
| Theme not persisting | Check PRIMARY KEY constraint |

## See Also

- `docs/WEEK_PERSISTENCE_V2_SYSTEM.md` - Full system documentation
- `docs/WEEK_PERSISTENCE_ARCHITECTURE_V2.md` - Architecture details

