# LLM API Documentation

## Base URL
All API endpoints are prefixed with `/api/v1/llm`.

## Authentication
All API endpoints require authentication. Use one of the following methods:
1. Session-based authentication (for browser clients)
2. API key authentication (for programmatic access)

## Endpoints

### LLM Actions

#### List Actions
```http
GET /actions
```

Response:
```json
[
    {
        "id": "integer",
        "field_name": "string",
        "prompt_template": "string",
        "llm_model": "string",
        "temperature": "number",
        "max_tokens": "number",
        "created_at": "string (ISO datetime)",
        "updated_at": "string (ISO datetime)"
    }
]
```

#### Create Action
```http
POST /actions
Content-Type: application/json

{
    "field_name": "string",
    "prompt_template_id": "integer",
    "llm_model": "string",
    "temperature": "number (optional, default: 0.7)",
    "max_tokens": "number (optional, default: 1000)"
}
```

Response:
```json
{
    "status": "success",
    "action": {
        "id": "integer",
        "field_name": "string",
        "prompt_template": "string",
        "llm_model": "string",
        "temperature": "number",
        "max_tokens": "number",
        "created_at": "string (ISO datetime)",
        "updated_at": "string (ISO datetime)"
    }
}
```

#### Get Action
```http
GET /actions/{action_id}
```

Response:
```json
{
    "id": "integer",
    "field_name": "string",
    "prompt_template": "string",
    "llm_model": "string",
    "temperature": "number",
    "max_tokens": "number",
    "created_at": "string (ISO datetime)",
    "updated_at": "string (ISO datetime)"
}
```

#### Update Action
```http
PUT /actions/{action_id}
Content-Type: application/json

{
    "field_name": "string (optional)",
    "prompt_template_id": "integer (optional)",
    "llm_model": "string (optional)",
    "temperature": "number (optional)",
    "max_tokens": "number (optional)"
}
```

Response:
```json
{
    "status": "success",
    "action": {
        "id": "integer",
        "field_name": "string",
        "prompt_template": "string",
        "llm_model": "string",
        "temperature": "number",
        "max_tokens": "number",
        "created_at": "string (ISO datetime)",
        "updated_at": "string (ISO datetime)"
    }
}
```

#### Delete Action
```http
DELETE /actions/{action_id}
```

Response:
```json
{
    "status": "success"
}
```

#### Get Action History
```http
GET /actions/{action_id}/history
```

Response:
```json
{
    "action": {
        "id": "integer",
        "field_name": "string",
        "prompt_template": "string",
        "llm_model": "string",
        "temperature": "number",
        "max_tokens": "number",
        "created_at": "string (ISO datetime)",
        "updated_at": "string (ISO datetime)"
    },
    "history": [
        {
            "id": "integer",
            "action_id": "integer",
            "post_id": "integer",
            "input_text": "string",
            "output_text": "string",
            "status": "string",
            "error_message": "string",
            "created_at": "string (ISO datetime)"
        }
    ]
}
```

### LLM Configuration

#### Get Configuration
```http
GET /config
```

Response:
```json
{
    "provider_type": "string",
    "model_name": "string",
    "api_base": "string"
}
```

#### Update Configuration
```http
POST /config
Content-Type: application/json

{
    "provider_type": "string (optional)",
    "model_name": "string (optional)",
    "api_base": "string (optional)",
    "auth_token": "string (optional)"
}
```

Response:
```json
{
    "success": true
}
```

### LLM Testing

#### Test LLM
```http
POST /test
Content-Type: application/json

{
    "prompt": "string",
    "model_name": "string (optional)",
    "temperature": "number (optional, default: 0.7)",
    "max_tokens": "number (optional, default: 1000)",
    "input": "string"
}
```

Response:
```json
{
    "result": "string",
    "model": "string",
    "duration": "number (seconds)"
}
```

### Error Responses

All endpoints may return the following error responses:

- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: User is not authenticated
- `404 Not Found`: Requested resource does not exist
- `500 Internal Server Error`: Server-side error occurred

Error responses follow this format:
```json
{
    "status": "error",
    "error": "string"
}
```

## Rate Limiting

The LLM endpoints are subject to rate limiting:
- 100 requests per minute per user for test endpoints
- 1000 requests per day per user for action execution
- No limit on read operations (GET requests)

## Error Handling

The LLM endpoints provide improved error handling:

### Timeout Handling
- Default timeout: 60 seconds for model loading
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

## Interaction Tracking

All LLM interactions are logged in the database for monitoring and improvement purposes. Each interaction record includes:
- Input text
- Output text
- Model used
- Parameters used
- Duration
- Status
- Error message (if any)
- Timestamp

## Error Handling

The LLM endpoints provide improved error handling:

### Timeout Handling
- Default timeout: 60 seconds for model loading
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
    "status": "error",
    "error": {
        "type": "string",
        "message": "string",
        "details": {
            "field": ["error details"]
        },
        "troubleshooting": ["steps to resolve"]
    }
}
```

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

## LLM Action Test Button (UI)

A "Test" button is available in the LLM Action modal on the blog develop page. This button sends the current prompt template and selected model to the `/api/v1/llm/test` endpoint and displays the generated result below the button. This allows users to quickly test prompt/model combinations before saving LLM Action settings.

> Note: The Test Interface on the /llm/ page now sends both the prompt and the selected model to /api/v1/llm/test. The backend will use the selected model for the test. No changes are made to the blog develop modal. 