# Structure API

## Overview
The Structure API handles post structure planning and management, including section planning, organization, and content generation.

## Endpoints

### Plan Structure
```http
POST /api/v1/structure/plan
```

#### Request Body
```json
{
    "title": "Post Title",
    "idea": "Initial idea for the post",
    "facts": [
        "Fact 1",
        "Fact 2"
    ]
}
```

#### Response
```json
{
    "status": "success",
    "data": {
        "sections": [
            {
                "id": 1,
                "title": "Section Title",
                "description": "Section description",
                "facts": ["Fact 1"],
                "order": 1
            }
        ]
    }
}
```

### Save Structure
```http
POST /api/v1/structure/save/{post_id}
```

#### Request Body
```json
{
    "sections": [
        {
            "title": "Section Title",
            "description": "Section description",
            "facts": ["Fact 1"],
            "order": 1
        }
    ]
}
```

#### Response
```json
{
    "status": "success",
    "data": {
        "message": "Structure saved successfully",
        "sections": [
            {
                "id": 1,
                "post_id": 1,
                "title": "Section Title",
                "description": "Section description",
                "facts": ["Fact 1"],
                "order": 1,
                "created_at": "2024-03-20T10:00:00Z",
                "updated_at": "2024-03-20T10:00:00Z"
            }
        ]
    }
}
```

### Get Structure
```http
GET /api/v1/posts/{post_id}/structure
```

#### Response
```json
{
    "status": "success",
    "data": {
        "post": {
            "id": 1,
            "title": "Post Title"
        },
        "sections": [
            {
                "id": 1,
                "title": "Section Title",
                "description": "Section description",
                "facts": ["Fact 1"],
                "order": 1,
                "created_at": "2024-03-20T10:00:00Z",
                "updated_at": "2024-03-20T10:00:00Z"
            }
        ],
        "development": {
            "idea": "Initial idea for the post",
            "facts": ["Fact 1", "Fact 2"]
        }
    }
}
```

## Error Responses

### Validation Error
```json
{
    "status": "error",
    "message": "Validation failed",
    "errors": [
        {
            "field": "title",
            "message": "Title is required"
        }
    ]
}
```

### Not Found
```json
{
    "status": "error",
    "message": "Post not found",
    "errors": [
        {
            "code": "not_found",
            "message": "Post with id 1 not found"
        }
    ]
}
```

## Notes
- All timestamps are in ISO 8601 format
- All endpoints require authentication
- Rate limiting applies to all endpoints
- Structure planning may take several seconds to complete
- Facts are automatically assigned to sections based on relevance 