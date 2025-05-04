# API Endpoints Documentation

## Blog Endpoints
Base URL: `/blog`

| Endpoint | Method | Description |
|----------|---------|-------------|
| `/` | GET | List all non-deleted posts |
| `/new` | POST | Create a new blog post |
| `/develop/<slug>` | GET | Get the development interface for a specific post |
| `/test_insert` | GET | Test endpoint to create a simple post |

## Workflow Endpoints
Base URL: `/api/v1/workflow`

| Endpoint | Method | Description |
|----------|---------|-------------|
| `/<slug>/status` | GET | Get current workflow status and available transitions |
| `/<slug>/transition` | POST | Transition to a new workflow stage |
| `/<slug>/sub-stage` | POST | Update sub-stage status, content, or add notes |
| `/<slug>/history` | GET | Get workflow history for a post |

### Workflow Endpoint Details

#### POST `/<slug>/sub-stage`
Updates a sub-stage with new content, status, or notes.

**Request Body:**
```json
{
    "sub_stage": "string",  // Required
    "status": "string",     // Optional: "not_started", "in_progress", "completed"
    "note": "string",       // Optional
    "content": "string"     // Optional
}
```

#### POST `/<slug>/transition`
Transitions a post to a new workflow stage.

**Request Body:**
```json
{
    "target_stage": "string",  // Required
    "notes": "string",         // Optional
    "user_id": number         // Optional
}
```

## Database Management Endpoints
Base URL: `/db`

| Endpoint | Method | Description |
|----------|---------|-------------|
| `/` | GET | Database management interface |
| `/restore` | GET | Database restore interface |
| `/stats` | GET | Database statistics |
| `/logs` | GET | Database logs |
| `/migrations` | GET | Database migrations interface |

## Main Application Endpoints
Base URL: `/`

| Endpoint | Method | Description |
|----------|---------|-------------|
| `/` | GET | Home page with admin features |
| `/health` | GET | Health check endpoint |
| `/dashboard` | GET | Admin dashboard |

## Error Handling Endpoints

All error endpoints return both HTML and JSON responses based on the Accept header:

| Status Code | Endpoint | Description |
|------------|----------|-------------|
| 404 | `/errors/404` | Not Found error handler |
| 500 | `/errors/500` | Internal Server error handler |
| 429 | `/errors/429` | Too Many Requests error handler |
| 403 | `/errors/403` | Forbidden error handler |

## Common Response Formats

### Success Response
```json
{
    "message": "Operation completed successfully",
    "data": { ... }  // Optional
}
```

### Error Response
```json
{
    "error": "Error message describing what went wrong"
}
```

## Notes

1. All POST endpoints expect JSON data with Content-Type: application/json
2. Authentication is required for most endpoints (implementation details in auth module)
3. All endpoints return appropriate HTTP status codes:
   - 200: Success
   - 400: Bad Request
   - 401: Unauthorized
   - 403: Forbidden
   - 404: Not Found
   - 429: Too Many Requests
   - 500: Internal Server Error

4. The workflow system follows a strict stage progression:
   - idea → research → outlining → authoring → images → metadata → review → publishing → updates → syndication
   - Each stage has its own set of sub-stages and validation rules
   - Transitions between stages are controlled by the VALID_TRANSITIONS configuration 