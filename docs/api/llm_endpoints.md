# LLM API Endpoints Documentation

This document describes the LLM-powered endpoints available in the blog application.

## Authentication

All endpoints require authentication. Use the login endpoint to obtain a session cookie before making requests.

## Endpoints

### Generate Blog Post Idea
`POST /api/llm/generate-idea`

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
`POST /api/llm/expand-section/<section_id>`

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
`POST /api/llm/optimize-seo/<post_id>`

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
`POST /api/llm/generate-social/<section_id>`

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