# Workflow API Endpoints Reference

## Overview

This document provides a reference for workflow-specific API endpoints. For comprehensive API documentation including detailed examples, error handling, and testing information, see the main API reference:

**[📚 Complete API Reference](../api/current/README.md)**

## Quick Reference

### Core API Documentation

- **[LLM Integration](../api/current/llm.md)** - LLM provider management, model access, and action execution
- **[Post Management](../api/current/posts.md)** - Post development, structure planning, and content management  
- **[Field Mapping](../api/current/fields.md)** - Database field relationships and UI component mapping
- **[Format Templates](../api/current/formats.md)** - Structured data format definitions and validation

### Workflow-Specific Endpoints

The following endpoints are specifically designed for workflow operations:

#### Execute LLM Workflow Step
```http
POST /api/workflow/posts/{post_id}/{stage}/{substage}/llm
```

**Example:**
```bash
curl -X POST "http://localhost:5000/api/workflow/posts/21/planning/idea/llm" \
  -H "Content-Type: application/json" \
  -d '{"step": "initial_concept"}'
```

#### Get Workflow Steps
```http
GET /api/workflow/steps
```

#### Get Step by ID
```http
GET /api/workflow/steps/{step_id}
```

#### Update Step Configuration
```http
PUT /api/workflow/steps/{step_id}
```

## Workflow Integration

The workflow system integrates with all core API endpoints:

- **Field Management**: Use field mapping endpoints to configure workflow step inputs/outputs
- **LLM Processing**: Execute LLM actions within workflow context
- **Post Development**: Update post data as workflow progresses
- **Format System**: Apply structured formats to workflow outputs

## Testing

For comprehensive testing examples and error handling, refer to the individual API documentation files listed above.

## Related Documentation

- [Workflow System Overview](README.md)
- [LLM Panel Integration](llm_panel.md)
- [Format System](formats.md)
- [Database Schema](../database/schema.md)

---

**Note**: This document provides a quick reference for workflow-specific endpoints. For complete API documentation with detailed examples, error codes, and testing information, please refer to the main API reference documentation. 