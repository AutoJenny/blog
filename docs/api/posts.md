# Blog Posts API

## Overview
The Posts API provides endpoints for managing blog posts, including their sections, metadata, and publishing workflow.

## Endpoints

### List Posts
```http
GET /api/v1/posts
```

#### Query Parameters
| Parameter | Type | Description |
|-----------|------|-------------|
| page | integer | Page number |
| per_page | integer | Items per page |
| status | string | Filter by status (draft, published, scheduled) |
| category | string | Filter by category slug |
| tag | string | Filter by tag slug |
| author | integer | Filter by author ID |
| search | string | Search in title and content |
| sort | string | Sort field and direction (e.g., created_at:desc) |

#### Response
```json
{
  "status": "success",
  "data": [
    {
      "id": 1,
      "title": "Sample Post",
      "slug": "sample-post",
      "subtitle": "A great post",
      "summary": "Post summary",
      "author": {
        "id": 1,
        "name": "John Doe"
      },
      "created_at": "2025-04-23T15:34:10Z",
      "updated_at": "2025-04-23T15:34:10Z",
      "published_at": "2025-04-23T15:34:10Z",
      "status": "published",
      "metadata": {
        "seo": {},
        "publishing": {}
      }
    }
  ],
  "meta": {
    "page": 1,
    "per_page": 10,
    "total": 100
  }
}
```

### Get Post
```http
GET /api/v1/posts/{slug}
```

#### Response
```json
{
  "status": "success",
  "data": {
    "id": 1,
    "title": "Sample Post",
    "slug": "sample-post",
    "subtitle": "A great post",
    "summary": "Post summary",
    "content": "Post content",
    "author": {
      "id": 1,
      "name": "John Doe"
    },
    "sections": [
      {
        "id": 1,
        "content": "Section content",
        "position": 1,
        "content_type": "markdown"
      }
    ],
    "categories": [
      {
        "id": 1,
        "name": "Technology",
        "slug": "tech"
      }
    ],
    "tags": [
      {
        "id": 1,
        "name": "Programming",
        "slug": "programming"
      }
    ],
    "created_at": "2025-04-23T15:34:10Z",
    "updated_at": "2025-04-23T15:34:10Z",
    "published_at": "2025-04-23T15:34:10Z",
    "status": "published",
    "metadata": {
      "seo": {},
      "publishing": {}
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
  "title": "New Post",
  "subtitle": "Optional subtitle",
  "summary": "Post summary",
  "content": "Initial content",
  "category_ids": [1, 2],
  "tag_ids": [1, 2],
  "metadata": {
    "seo": {
      "title": "SEO Title",
      "description": "SEO Description"
    }
  }
}
```

#### Response
```json
{
  "status": "success",
  "data": {
    "id": 2,
    "slug": "new-post",
    // ... full post object
  }
}
```

### Update Post
```http
PUT /api/v1/posts/{slug}
```

#### Request Body
```json
{
  "title": "Updated Title",
  "subtitle": "New subtitle",
  "summary": "Updated summary",
  "content": "Updated content",
  "category_ids": [1, 2],
  "tag_ids": [1, 2],
  "metadata": {
    "seo": {
      "title": "Updated SEO Title"
    }
  }
}
```

### Delete Post
```http
DELETE /api/v1/posts/{slug}
```

### Publish Post
```http
POST /api/v1/posts/{slug}/publish
```

#### Request Body
```json
{
  "schedule_at": "2025-04-24T00:00:00Z",  // Optional
  "unpublish_at": "2025-05-24T00:00:00Z"  // Optional
}
```

### Unpublish Post
```http
POST /api/v1/posts/{slug}/unpublish
```

## Sections API

### List Sections
```http
GET /api/v1/posts/{slug}/sections
```

### Get Section
```http
GET /api/v1/sections/{id}
```

### Create Section
```http
POST /api/v1/posts/{slug}/sections
```

#### Request Body
```json
{
  "content": "Section content",
  "position": 1,
  "content_type": "markdown",
  "metadata": {
    "title": "Section Title",
    "template_id": 1
  }
}
```

### Update Section
```http
PUT /api/v1/sections/{id}
```

#### Request Body
```json
{
  "content": "Updated content",
  "position": 2,
  "metadata": {
    "title": "New Title"
  }
}
```

### Delete Section
```http
DELETE /api/v1/sections/{id}
```

### Reorder Sections
```http
POST /api/v1/posts/{slug}/sections/reorder
```

#### Request Body
```json
{
  "section_ids": [3, 1, 4, 2]
}
```

## Workflow API

### Get Workflow Status
```http
GET /api/v1/posts/{slug}/workflow
```

### Update Workflow Status
```http
POST /api/v1/posts/{slug}/workflow
```

#### Request Body
```json
{
  "status": "review",
  "comment": "Ready for review"
}
```

### Get Workflow History
```http
GET /api/v1/posts/{slug}/workflow/history
```

## Error Responses

### Not Found
```json
{
  "status": "error",
  "error": {
    "code": "POST_NOT_FOUND",
    "message": "Post not found"
  }
}
```

### Validation Error
```json
{
  "status": "error",
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": {
      "title": ["Title is required"],
      "category_ids": ["Invalid category ID"]
    }
  }
}
```

### Permission Error
```json
{
  "status": "error",
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "Insufficient permissions"
  }
}
```

## Best Practices

### Content Management
1. Use appropriate content types
2. Validate content format
3. Handle section ordering
4. Maintain content history

### Workflow
1. Check status transitions
2. Include workflow comments
3. Track status changes
4. Handle scheduled actions

### Performance
1. Use pagination
2. Request specific fields
3. Cache responses
4. Batch updates

### Security
1. Validate permissions
2. Sanitize content
3. Rate limit requests
4. Validate metadata 