# LLM API Endpoints Documentation

This document describes the LLM-powered endpoints available in the blog application.

## Authentication

All endpoints require authentication via JWT token in the Authorization header.

## Endpoints

### Generate Blog Post Ideas
```http
POST /api/v1/llm/generate-idea
```

Generates a blog post idea based on the provided topic and parameters.

**Request Body:**
```json
{
    "topic": "string",
    "style": "string (optional, default: 'informative')",
    "audience": "string (optional, default: 'Scottish heritage enthusiasts')"
}
```

**Response:**
```json
{
    "title": "string",
    "outline": ["string"],
    "keywords": ["string"]
}
```

### Expand Section Content
```http
POST /api/v1/llm/expand-section/<section_id>
```

Expands a section's content with AI-generated material.

**Request Body:**
```json
{
    "tone": "string (optional, default: 'professional')",
    "platforms": ["string"] (optional, default: ["blog"])
}
```

**Response:**
```json
{
    "content": "string",
    "keywords": ["string"],
    "social_media_snippets": {
        "platform": "string"
    }
}
```

### Optimize SEO
```http
POST /api/v1/llm/optimize-seo/<post_id>
```

Provides SEO optimization suggestions for a blog post.

**Request Body:**
```json
{
    "keywords": ["string"]
}
```

**Response:**
```json
{
    "suggestions": {
        "title_suggestions": ["string"],
        "meta_description": "string",
        "keyword_suggestions": ["string"]
    }
}
```

### Generate Social Media Content
```http
POST /api/v1/llm/generate-social/<section_id>
```

Generates social media content for a blog section.

**Request Body:**
```json
{
    "platforms": ["string"] (default: ["tiktok", "instagram"])
}
```

**Response:**
```json
{
    "platform1": "string",
    "platform2": "string"
}
```

## Template Management

### Save Template Settings
`POST /api/v1/llm/actions/`

Saves template settings for a specific LLM action. This endpoint handles both saving existing templates and creating new ones.

**Request Body:**
```json
{
    "source_field": "string",
    "template": "string",
    "llm_model": "string",
    "temperature": "number",
    "max_tokens": "number",
    "template_name": "string (optional, for new templates)"
}
```

**Response:**
```json
{
    "status": "success",
    "message": "Template settings saved successfully",
    "data": {
        "template_id": "string",
        "template_name": "string",
        "source_field": "string",
        "template": "string",
        "llm_model": "string",
        "temperature": "number",
        "max_tokens": "number"
    }
}
```

**Error Response:**
```json
{
    "status": "error",
    "message": "Error description",
    "errors": {
        "field_name": ["error details"]
    }
}
```

### Get Template Settings
`GET /api/v1/llm/actions/<source_field>`

Retrieves template settings for a specific source field.

**Response:**
```json
{
    "status": "success",
    "data": {
        "templates": [
            {
                "template_id": "string",
                "template_name": "string",
                "source_field": "string",
                "template": "string",
                "llm_model": "string",
                "temperature": "number",
                "max_tokens": "number"
            }
        ],
        "models": ["string"]
    }
}
```

### Test Template
`POST /api/v1/llm/test`

Tests a prompt template with the specified model.

**Request Body:**
```json
{
    "prompt": "string",
    "model_name": "string"
}
```

**Response:**
```json
{
    "result": "string"
}
```

## Error Responses

All endpoints may return the following error responses:

- `401 Unauthorized`: User is not authenticated
- `404 Not Found`: Requested resource does not exist
- `500 Internal Server Error`: Server-side error occurred

Error responses follow this format:
```json
{
    "error": "string"
}
```

## Rate Limiting

The LLM endpoints are subject to rate limiting based on your OpenAI API quota. Please ensure your requests are within reasonable limits.

## Interaction Tracking

All LLM interactions are logged in the database for monitoring and improvement purposes. Each interaction record includes:
- Input text
- Output text
- Model used
- Duration
- Parameters used
- Timestamp 

## LLM Action Test Button (UI)

A "Test" button is available in the LLM Action modal on the blog develop page. This button sends the current prompt template and selected model to the `/api/v1/llm/test` endpoint and displays the generated result below the button. This allows users to quickly test prompt/model combinations before saving LLM Action settings.

> Note: The Test Interface on the /llm/ page now sends both the prompt and the selected model to /api/v1/llm/test. The backend will use the selected model for the test. No changes are made to the blog develop modal.

## Error Handling

The LLM endpoints now provide improved error handling and timeout management:

### Timeout Handling
- Default timeout increased to 60 seconds for model loading
- Non-fatal failures allow continued operation
- Clear distinction between temporary and permanent failures

### Error Messages
- Detailed error descriptions
- Specific troubleshooting steps
- Clear indication of error type (timeout/connection/etc)

### Logging
- Comprehensive logging of all operations
- Error tracking with stack traces
- Performance monitoring for timeouts

### Response Format for Errors
```json
{
  "error": "Detailed error message",
  "type": "timeout|connection|validation",
  "suggestions": [
    "Specific troubleshooting step 1",
    "Specific troubleshooting step 2"
  ]
}
``` 