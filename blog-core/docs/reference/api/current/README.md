# API Reference Documentation

## Overview

This directory contains the current, authoritative API documentation for the blog workflow system. All endpoints follow RESTful conventions and use standardized request/response formats.

## Base URLs

### blog-core (Main Application)
All blog-core endpoints use the base URL: `http://localhost:5001`

### llm-actions (LLM Microservice)
All llm-actions endpoints use the base URL: `http://localhost:5002`

## Authentication

**Note**: This project does not use authentication. All endpoints are publicly accessible.

## Response Format

All endpoints return JSON responses with the following structure:

### Success Response
```json
{
    "success": true,
    "data": {
        // Response data
    }
}
```

### Error Response
```json
{
    "success": false,
    "error": {
        "code": "ERROR_CODE",
        "message": "Human-readable error message",
        "details": {
            // Additional error details
        }
    }
}
```

## API Documentation Files

### Core Endpoints
- **[LLM Integration](llm.md)** - LLM provider management, model access, and action execution
- **[LLM Actions Microservice](llm_actions.md)** - **NEW**: Complete LLM microservice API with purple interface
- **[Post Management](posts.md)** - Post development, structure planning, and content management
- **[Field Mapping](fields.md)** - Database field relationships and UI component mapping
- **[Format Templates](formats.md)** - Structured data format definitions and validation
- **[Image Management](images.md)** - Image generation, settings, styles, and ComfyUI integration

### API Path Structure

#### blog-core (http://localhost:5001)
- `/api/llm/` - Core LLM functionality (providers, models, actions)
- `/api/workflow/` - Workflow-specific operations (posts, sections, stages)
- `/api/images/` - Image generation and management
- `/api/v1/` - Legacy endpoints (deprecated but still functional)

#### llm-actions (http://localhost:5002)
- `/api/llm/` - LLM configuration, testing, and action execution
- `/api/run-llm` - General LLM execution
- `/api/context` - Context management
- `/api/task` - Task management
- `/health` - Service health check

### Migration Notes
- Legacy `/api/v1/` endpoints are still functional but deprecated
- New development should use current endpoint paths
- Both endpoint sets provide the same functionality
- Migration to current endpoints is recommended for new features

## Common Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `MISSING_REQUIRED_FIELD` | Required field is missing | 400 |
| `INVALID_FORMAT` | Data format is invalid | 400 |
| `STEP_NOT_FOUND` | Workflow step not found | 404 |
| `POST_NOT_FOUND` | Post not found | 404 |
| `FORMAT_NOT_FOUND` | Format template not found | 404 |
| `LLM_SERVICE_ERROR` | LLM service unavailable | 503 |
| `DATABASE_ERROR` | Database operation failed | 500 |
| `VALIDATION_ERROR` | Data validation failed | 400 |

## Testing Endpoints

### Health Check
```http
GET /api/health
```

### API Version
```http
GET /api/version
```

## Rate Limiting

Currently, no rate limiting is implemented. All endpoints are available without restrictions.

## CORS

### blog-core
CORS is configured to allow requests from the same origin (`localhost:5001`).

### llm-actions
CORS is configured to allow cross-origin requests from:
- `http://localhost:5001` (blog-core)
- `http://localhost:5002` (llm-actions)

## Content Types

- **Request**: `application/json` for POST/PUT requests
- **Response**: `application/json` for all responses

## Status Codes

| Status | Description |
|--------|-------------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 404 | Not Found |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

## Related Documentation

- [Microservices Architecture Overview](../microservices_overview.md)
- [Database Schema](../database/schema.md)
- [Workflow System](../workflow/README.md)
- [LLM Integration](../workflow/llm_panel.md)
- [Format System](../workflow/formats.md)

## Support

For API-related issues:

1. Check this endpoint reference first
2. Verify request/response formats
3. Check error codes and messages
4. Test with curl examples provided in each file
5. Contact the project maintainers

Remember: This project does not use authentication. All endpoints are publicly accessible. 