# Structure Stage API Documentation

## Overview
The Structure Stage API provides endpoints for planning and managing the structure of blog posts, including section creation, editing, and organization.

## Endpoints

### Plan Structure
`POST /api/v1/structure/plan`

Generates a section structure using the LLM based on provided inputs.

#### Request Body
```json
{
  "title": "string",
  "idea": "string",
  "facts": ["string"]
}
```

#### Response
```json
{
  "sections": [
    {
      "name": "string",
      "description": "string",
      "themes": ["string"],
      "facts": ["string"]
    }
  ]
}
```

#### Error Responses
- `400 Bad Request`: Invalid input format
- `500 Internal Server Error`: LLM service error

### Save Structure
`POST /api/v1/structure/save/<post_id>`

Saves the edited section structure to the database.

#### Request Body
```json
{
  "sections": [
    {
      "title": "string",
      "description": "string",
      "ideas": ["string"],
      "facts": ["string"]
    }
  ]
}
```

#### Response
```json
{
  "message": "Structure saved successfully",
  "sections": [
    {
      "title": "string",
      "description": "string",
      "ideas": ["string"],
      "facts": ["string"]
    }
  ]
}
```

#### Error Responses
- `400 Bad Request`: Invalid input format or missing required fields
- `404 Not Found`: Post not found
- `500 Internal Server Error`: Database error

### Get Structure
`GET /api/v1/post/<post_id>/structure`

Retrieves the current structure of a post.

#### Response
```json
{
  "post": {
    "id": "integer",
    "title": "string",
    "published": "boolean",
    "deleted": "boolean",
    "created_at": "datetime",
    "updated_at": "datetime"
  },
  "intro": {
    "intro": "string",
    "intro_status": "string"
  },
  "sections": [
    {
      "id": "integer",
      "section_heading": "string",
      "section_description": "string",
      "ideas_to_include": ["string"],
      "facts_to_include": ["string"],
      "section_order": "integer",
      "status": "string"
    }
  ],
  "conclusion": {
    "conclusion": "string",
    "conclusion_status": "string"
  },
  "metadata": {
    "key": "value"
  },
  "status": {
    "intro": "string",
    "sections": ["string"],
    "conclusion": "string",
    "metadata": "string"
  }
}
```

#### Error Responses
- `404 Not Found`: Post not found
- `500 Internal Server Error`: Database error

## Data Models

### Section
```json
{
  "id": "integer",
  "post_id": "integer",
  "section_heading": "string",
  "section_description": "string",
  "ideas_to_include": "json",
  "facts_to_include": "json",
  "section_order": "integer",
  "status": "string"
}
```

## Error Handling
All endpoints return appropriate HTTP status codes and error messages in the following format:
```json
{
  "error": "string"
}
```

## Authentication
All endpoints require authentication. Include the JWT token in the Authorization header:
```
Authorization: Bearer <token>
```

## Rate Limiting
- Plan Structure: 10 requests per minute
- Save Structure: 20 requests per minute
- Get Structure: 30 requests per minute

## Versioning
The API version is included in the URL path. The current version is v1.

## Changelog

### 2024-06
- Added section_description field to post_section table
- Implemented drag-and-drop functionality for section reordering
- Added validation for required fields
- Added support for unassigned items
- Implemented transaction support for saving structure 