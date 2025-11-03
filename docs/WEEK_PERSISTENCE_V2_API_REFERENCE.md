# Week Persistence V2 - API Reference

## Endpoint Overview

All endpoints support backwards compatibility:
- If new tables exist: Use V2 architecture
- If new tables don't exist: Fallback to old `calendar_schedule` table

---

## `GET /api/calendar/schedule`

Get schedule for a specific year and week.

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `year` | integer | Yes | Year (e.g., 2024) |
| `week` | integer | Yes | Week number (1-52) |

### Response (V2 Format)

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
            "theme_description": "Tips for spring planting...",
            "updated_at": "2024-04-10T10:30:00"
        },
        {
            "type": "post",
            "id": 456,
            "post_id": 789,
            "post_title": "Guide to Spring Planting",
            "post_status": "draft",
            "post_idea_seed": "Spring planting guide...",
            "scheduled_date": "2024-04-15",
            "created_at": "2024-04-10T11:00:00",
            "updated_at": "2024-04-10T11:30:00"
        }
    ]
}
```

### Example

```bash
curl "http://localhost:5000/api/calendar/schedule?year=2024&week=15"
```

---

## `POST /api/calendar/select-theme`

Select a theme for a specific week/year.

### Request Body

```json
{
    "theme_id": 123,
    "year": 2024,
    "week_number": 15
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `theme_id` | integer | Yes | ID of theme to select |
| `year` | integer | Yes | Year |
| `week_number` | integer | Yes | Week number (1-52) |

**Note:** `idea_id` parameter is deprecated and will be rejected.

### Response (Success)

```json
{
    "success": true,
    "year": 2024,
    "week_number": 15,
    "selected_theme_id": 123,
    "updated_at": "2024-04-10T10:30:00"
}
```

### Response (Error - No Theme Found)

```json
{
    "success": false,
    "error": "Theme not found"
}
```

### Response (Error - Missing Parameters)

```json
{
    "success": false,
    "error": "theme_id is required"
}
```

### Example

```bash
curl -X POST "http://localhost:5000/api/calendar/select-theme" \
  -H "Content-Type: application/json" \
  -d '{
    "theme_id": 123,
    "year": 2024,
    "week_number": 15
  }'
```

---

## `GET /api/calendar/ideas/<idea_id>/status`

Get post creation status for a theme in a specific week.

**Note:** Parameter name is `idea_id` for backwards compatibility, but only `theme_id` values are supported.

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `idea_id` | integer | Yes | Theme ID (despite parameter name) |

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `year` | integer | Yes | Year |
| `week_number` | integer | Yes | Week number (1-52) |

### Response (Success - Post Found)

```json
{
    "success": true,
    "post": {
        "id": 789,
        "title": "Guide to Spring Planting",
        "status": "draft",
        "scheduled_date": "2024-04-15"
    }
}
```

### Response (Success - No Post)

```json
{
    "success": true,
    "post": null
}
```

### Response (Error - Missing Parameters)

```json
{
    "success": false,
    "error": "year and week_number are required"
}
```

### Example

```bash
curl "http://localhost:5000/api/calendar/ideas/123/status?year=2024&week_number=15"
```

---

## `POST /api/posts/confirm-calendar-idea`

Create a post and assign it to a week. **Requires a selected theme.**

### Request Body

```json
{
    "topic": "Spring Planting Guide",
    "week_number": 15,
    "year": 2024,
    "force_new": false
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `topic` | string | Yes | Post title/topic |
| `week_number` | integer | Yes | Week number (1-52) |
| `year` | integer | No | Year (defaults to current year) |
| `force_new` | boolean | No | Force new post creation (default: false) |

### Response (Success)

```json
{
    "success": true,
    "post_id": 789
}
```

### Response (Error - No Theme Selected)

```json
{
    "success": false,
    "error": "No theme selected for week 2024/15. Please select a theme first."
}
```

### Response (Error - Missing Parameters)

```json
{
    "error": "topic and week_number are required"
}
```

### Example

```bash
curl -X POST "http://localhost:5000/api/posts/confirm-calendar-idea" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Spring Planting Guide",
    "week_number": 15,
    "year": 2024
  }'
```

---

## `GET /api/posts/<post_id>/expanded-idea`

Get expanded idea for a post, optionally scoped to a week.

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `post_id` | integer | Yes | Post ID |

### Query Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `year` | integer | No | Year (for week-scoped lookup) |
| `week` | integer | No | Week number (for week-scoped lookup) |

### Response (Success - Expanded Idea Found)

```json
{
    "success": true,
    "expanded_idea": "Detailed expanded idea content..."
}
```

### Response (Success - No Expanded Idea)

```json
{
    "success": true,
    "expanded_idea": null
}
```

### Response (Error)

```json
{
    "error": "Error message"
}
```

### Example

```bash
# Week-scoped lookup
curl "http://localhost:5000/api/posts/789/expanded-idea?year=2024&week=15"

# Post-scoped lookup
curl "http://localhost:5000/api/posts/789/expanded-idea"
```

---

## `POST /api/posts/<post_id>/expanded-idea`

Generate or update expanded idea for a post. **Requires year/week context.**

### Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `post_id` | integer | Yes | Post ID |

### Query Parameters or Request Body

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `year` | integer | Yes | Year |
| `week` | integer | Yes | Week number (1-52) |

### Response (Success)

```json
{
    "success": true,
    "expanded_idea": "Generated expanded idea content..."
}
```

### Response (Error - No Theme Selected)

```json
{
    "error": "No theme selected for week 2024/15. Please select a theme in the calendar week view."
}
```

### Response (Error - Missing Parameters)

```json
{
    "error": "year and week are required. Please provide week context to get the selected theme."
}
```

### Example

```bash
curl -X POST "http://localhost:5000/api/posts/789/expanded-idea?year=2024&week=15" \
  -H "Content-Type: application/json"
```

---

## `POST /api/taxonomy/assign`

Assign taxonomy to a post based on expanded idea. Uses week context to find correct post.

### Request Body

```json
{
    "post_id": 789,
    "expanded_idea": "Content...",
    "year": 2024,
    "week_number": 15
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `post_id` | integer | Yes | Post ID from URL |
| `expanded_idea` | string | Yes | Expanded idea content |
| `year` | integer | No | Year (if provided, resolves post from week) |
| `week_number` | integer | No | Week number (if provided, resolves post from week) |

**Note:** If `year` and `week_number` are provided, the endpoint will resolve the correct post for that week, potentially overriding the `post_id` from the URL.

### Response (Success)

```json
{
    "success": true,
    "assignments": [...]
}
```

---

## Deprecated Endpoints

### `POST /api/schedule/update-theme-to-idea`

**Status:** Deprecated (returns 410 Gone)

This endpoint is no longer needed as `idea_id` is deprecated from week persistence.

### Response

```json
{
    "success": false,
    "error": "This endpoint is deprecated. idea_id is no longer supported in week persistence. Use theme_id instead."
}
```

---

## Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Missing or invalid parameters |
| 404 | Not Found - Resource not found |
| 410 | Gone - Endpoint deprecated |
| 500 | Internal Server Error |

## Backwards Compatibility

All endpoints check if new tables exist:
- If new tables exist: Use V2 architecture
- If new tables don't exist: Fallback to old `calendar_schedule` table

This allows safe migration without breaking existing functionality.

