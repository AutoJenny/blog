# API Documentation

## Authentication
All API endpoints require authentication. Use one of the following methods:
1. Session-based authentication (for browser clients)
2. API key authentication (for programmatic access)

## Blog Posts

### Create Post
```http
POST /blog/create
Content-Type: application/json

{
    "basic_idea": "string"
}
```

Response:
```json
{
    "id": "integer",
    "title": "string",
    "slug": "string",
    "workflow_status": "string"
}
```

### List Posts
```http
GET /blog/latest
```

Query Parameters:
- `page`: Page number (default: 1)
- `per_page`: Items per page (default: 10)
- `category`: Filter by category
- `tag`: Filter by tag
- `status`: Filter by workflow status

### Get Post
```http
GET /blog/post/{post_id}
```

### Update Post
```http
PUT /blog/post/{post_id}
Content-Type: application/json

{
    "title": "string",
    "content": "string",
    "summary": "string",
    "categories": ["string"],
    "tags": ["string"]
}
```

### Delete Post
```http
DELETE /blog/post/{post_id}
```

## Media Management

### Upload Image
```http
POST /media/upload
Content-Type: multipart/form-data

file: binary
alt_text: string
caption: string
```

### Get Image
```http
GET /media/{image_id}
```

### Update Image
```http
PUT /media/{image_id}
Content-Type: application/json

{
    "alt_text": "string",
    "caption": "string",
    "watermark": "boolean"
}
```

### Delete Image
```http
DELETE /media/{image_id}
```

## Workflow Management

### Update Status
```http
POST /blog/post/{post_id}/workflow
Content-Type: application/json

{
    "stage": "string",
    "notes": "string"
}
```

### Get History
```http
GET /blog/post/{post_id}/workflow/history
```

## AI Integration

### Generate Content
```http
POST /ai/generate
Content-Type: application/json

{
    "prompt_id": "integer",
    "input_text": "string",
    "parameters": {}
}
```

### Enhance Content
```http
POST /ai/enhance
Content-Type: application/json

{
    "content": "string",
    "type": "string"
}
```

### Analyze Content
```http
POST /ai/analyze
Content-Type: application/json

{
    "content": "string",
    "aspects": ["seo", "readability", "tone"]
}
```

## Database Management

### Backup
```http
POST /db/backup
```

### Restore
```http
POST /db/restore
Content-Type: multipart/form-data

backup_file: binary
```

### Health Check
```http
GET /db/health
```

## Error Responses

### 400 Bad Request
```json
{
    "error": "string",
    "message": "string"
}
```

### 401 Unauthorized
```json
{
    "error": "unauthorized",
    "message": "Authentication required"
}
```

### 403 Forbidden
```json
{
    "error": "forbidden",
    "message": "Insufficient permissions"
}
```

### 404 Not Found
```json
{
    "error": "not_found",
    "message": "Resource not found"
}
```

### 500 Server Error
```json
{
    "error": "server_error",
    "message": "Internal server error"
}
```

## Rate Limiting
- 100 requests per minute for authenticated users
- 10 requests per minute for unauthenticated users
- AI endpoints limited to 10 requests per minute

## Webhooks

### Post Status Updates
```http
POST /webhooks/post/status
Content-Type: application/json

{
    "post_id": "integer",
    "status": "string",
    "timestamp": "string"
}
```

### Media Processing
```http
POST /webhooks/media/processed
Content-Type: application/json

{
    "media_id": "integer",
    "status": "string",
    "url": "string"
}
``` 