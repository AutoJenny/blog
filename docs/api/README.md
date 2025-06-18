# API Documentation

## Overview
This document outlines the standardized API structure for the blog application. All API endpoints follow RESTful principles and are organized by resource type.

## Base URL
All API endpoints are prefixed with `/api/v1/`

## Resource Naming Conventions
- Use plural nouns for resource collections (e.g., `/api/v1/posts/`)
- Use singular nouns for individual resources (e.g., `/api/v1/post/<id>/`)
- Use kebab-case for multi-word resources
- Use nested resources for related data (e.g., `/api/v1/posts/<id>/sections/`)

## Authentication
All API endpoints require JWT authentication unless explicitly marked as public.

## Response Format
All responses follow this structure:
```json
{
    "status": "success|error",
    "data": {}, // Response data
    "message": "", // Optional message
    "errors": [] // Optional error details
}
```

## API Categories

### 1. Posts API
- [Documentation](posts.md)
- Base path: `/api/v1/posts/`
- Handles all post-related operations

### 2. Structure API
- [Documentation](structure.md)
- Base path: `/api/v1/structure/`
- Handles post structure planning and management

### 3. LLM API
- [Documentation](llm.md)
- Base path: `/api/v1/llm/`
- Handles all LLM-related operations

### 4. Image API
- [Documentation](images.md)
- Base path: `/api/v1/images/`
- Handles image generation and management

### 5. ComfyUI API
- [Documentation](comfyui.md)
- Base path: `/api/v1/comfyui/`
- Handles ComfyUI integration

### 6. Workflow API
- [Documentation](workflow.md)
- Base path: `/api/v1/workflow/`
- Handles workflow state and transitions

## Error Codes
- 400: Bad Request
- 401: Unauthorized
- 403: Forbidden
- 404: Not Found
- 422: Unprocessable Entity
- 500: Internal Server Error

## Versioning
- Current version: v1
- Version is included in URL path
- Breaking changes will increment version number

## Rate Limiting
- 100 requests per minute per IP
- Rate limit headers included in response

## Best Practices
1. Always use HTTPS
2. Include appropriate headers
3. Handle errors gracefully
4. Validate input data
5. Use proper HTTP methods
6. Return appropriate status codes
7. Include pagination for list endpoints
8. Cache responses when appropriate 