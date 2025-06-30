# Posts API

## Overview
The Posts API handles all operations related to blog posts, including creation, updates, and management of post content and structure.

## Endpoints

### List Posts
```http
GET /api/v1/posts
```

#### Response
```json
{
    "status": "success",
    "data": {
        "posts": [
            {
                "id": 1,
                "title": "Post Title",
                "slug": "post-title",
                "status": "draft",
                "created_at": "2024-03-20T10:00:00Z",
                "updated_at": "2024-03-20T10:00:00Z"
            }
        ],
        "total": 1,
        "page": 1,
        "per_page": 10
    }
}
```

### Get Post
```http
GET /api/v1/posts/{id}
```

#### Response
```json
{
    "status": "success",
    "data": {
        "post": {
            "id": 1,
            "title": "Post Title",
            "slug": "post-title",
            "status": "draft",
            "created_at": "2024-03-20T10:00:00Z",
            "updated_at": "2024-03-20T10:00:00Z"
        }
    }
}
```

### Create Post
```http
POST /api/v1/posts
```

#### Request Body
```json
{
    "title": "New Post Title",
    "status": "draft"
}
```

#### Response
```json
{
    "status": "success",
    "data": {
        "post": {
            "id": 1,
            "title": "New Post Title",
            "slug": "new-post-title",
            "status": "draft",
            "created_at": "2024-03-20T10:00:00Z",
            "updated_at": "2024-03-20T10:00:00Z"
        }
    }
}
```

### Update Post
```http
PUT /api/v1/posts/{id}
```

#### Request Body
```json
{
    "title": "Updated Post Title",
    "status": "published"
}
```

#### Response
```json
{
    "status": "success",
    "data": {
        "post": {
            "id": 1,
            "title": "Updated Post Title",
            "slug": "updated-post-title",
            "status": "published",
            "created_at": "2024-03-20T10:00:00Z",
            "updated_at": "2024-03-20T10:00:00Z"
        }
    }
}
```

### Delete Post
```http
DELETE /api/v1/posts/{id}
```

#### Response
```json
{
    "status": "success",
    "message": "Post deleted successfully"
}
```

### Get Post Development
```http
GET /api/v1/posts/{id}/development
```

#### Response
```json
{
    "status": "success",
    "data": {
        "development": {
            "id": 1,
            "post_id": 1,
            "idea_seed": "Initial idea",
            "summary": "Post summary",
            "facts": ["Fact 1", "Fact 2"],
            "created_at": "2024-03-20T10:00:00Z",
            "updated_at": "2024-03-20T10:00:00Z"
        }
    }
}
```

### Update Post Development
```http
POST /api/v1/posts/{id}/development
```

#### Request Body
```json
{
    "idea_seed": "Updated idea",
    "summary": "Updated summary",
    "facts": ["Updated Fact 1", "Updated Fact 2"]
}
```

#### Response
```json
{
    "status": "success",
    "data": {
        "development": {
            "id": 1,
            "post_id": 1,
            "idea_seed": "Updated idea",
            "summary": "Updated summary",
            "facts": ["Updated Fact 1", "Updated Fact 2"],
            "created_at": "2024-03-20T10:00:00Z",
            "updated_at": "2024-03-20T10:00:00Z"
        }
    }
}
```

### Get Post Sections
```http
GET /api/v1/posts/{id}/sections
```

#### Response
```json
{
    "status": "success",
    "data": {
        "sections": [
            {
                "id": 1,
                "post_id": 1,
                "title": "Section Title",
                "content": "Section content",
                "order": 1,
                "created_at": "2024-03-20T10:00:00Z",
                "updated_at": "2024-03-20T10:00:00Z"
            }
        ]
    }
}
```

### Create Post Section
```http
POST /api/v1/posts/{id}/sections
```

#### Request Body
```json
{
    "title": "New Section Title",
    "content": "New section content",
    "order": 1
}
```

#### Response
```json
{
    "status": "success",
    "data": {
        "section": {
            "id": 1,
            "post_id": 1,
            "title": "New Section Title",
            "content": "New section content",
            "order": 1,
            "created_at": "2024-03-20T10:00:00Z",
            "updated_at": "2024-03-20T10:00:00Z"
        }
    }
}
```

### Update Post Section
```http
PUT /api/v1/posts/{id}/sections/{section_id}
```

#### Request Body
```json
{
    "title": "Updated Section Title",
    "content": "Updated section content",
    "order": 2
}
```

#### Response
```json
{
    "status": "success",
    "data": {
        "section": {
            "id": 1,
            "post_id": 1,
            "title": "Updated Section Title",
            "content": "Updated section content",
            "order": 2,
            "created_at": "2024-03-20T10:00:00Z",
            "updated_at": "2024-03-20T10:00:00Z"
        }
    }
}
```

### Delete Post Section
```http
DELETE /api/v1/posts/{id}/sections/{section_id}
```

#### Response
```json
{
    "status": "success",
    "message": "Section deleted successfully"
}
```

### Get Post Structure
```http
GET /api/v1/posts/{id}/structure
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
                "order": 1
            }
        ],
        "development": {
            "idea_seed": "Initial idea",
            "summary": "Post summary",
            "facts": ["Fact 1", "Fact 2"]
        }
    }
}
```

## Error Responses

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

## Notes
- All timestamps are in ISO 8601 format
- All endpoints require authentication unless marked as public
- Pagination is available for list endpoints
- Rate limiting applies to all endpoints 