# Format Template API Endpoints

All format-related endpoints are now under the `/api/workflow/formats/` base path.

## Template Endpoints

### Get Templates
- **URL**: `/api/workflow/formats/templates`
- **Method**: `GET`
- **Description**: Retrieves all format templates
- **Response**:
  ```json
  [
    {
      "id": "integer",
      "name": "string",
      "description": "string",
      "fields": [
        {
          "name": "string",
          "type": "string",
          "required": "boolean",
          "description": "string"
        }
      ],
      "format_type": "string",
      "llm_instructions": "string"
    }
  ]
  ```
- **Status Codes**:
  - `200`: Success

### Get Template
- **URL**: `/api/workflow/formats/templates/<template_id>`
- **Method**: `GET`
- **Description**: Retrieves a specific format template
- **URL Parameters**:
  - `template_id`: ID of the template
- **Response**:
  ```json
  {
    "id": "integer",
    "name": "string",
    "description": "string",
    "fields": [
      {
        "name": "string",
        "type": "string",
        "required": "boolean",
        "description": "string"
      }
    ],
    "format_type": "string",
    "llm_instructions": "string"
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `404`: Template not found

### Create Template
- **URL**: `/api/workflow/formats/templates`
- **Method**: `POST`
- **Description**: Creates a new format template
- **Request Body**:
  ```json
  {
    "name": "string",
    "description": "string",
    "fields": [
      {
        "name": "string",
        "type": "string",
        "required": "boolean",
        "description": "string"
      }
    ],
    "format_type": "string",
    "llm_instructions": "string"
  }
  ```
- **Response**:
  ```json
  {
    "id": "integer",
    "name": "string",
    "description": "string",
    "fields": [
      {
        "name": "string",
        "type": "string",
        "required": "boolean",
        "description": "string"
      }
    ],
    "format_type": "string",
    "llm_instructions": "string"
  }
  ```
- **Status Codes**:
  - `201`: Created successfully
  - `400`: Invalid request data

### Update Template
- **URL**: `/api/workflow/formats/templates/<template_id>`
- **Method**: `PUT`
- **Description**: Updates a format template
- **URL Parameters**:
  - `template_id`: ID of the template
- **Request Body**:
  ```json
  {
    "name": "string",
    "description": "string",
    "fields": [
      {
        "name": "string",
        "type": "string",
        "required": "boolean",
        "description": "string"
      }
    ],
    "format_type": "string",
    "llm_instructions": "string"
  }
  ```
- **Response**:
  ```json
  {
    "id": "integer",
    "name": "string",
    "description": "string",
    "fields": [
      {
        "name": "string",
        "type": "string",
        "required": "boolean",
        "description": "string"
      }
    ],
    "format_type": "string",
    "llm_instructions": "string"
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `400`: Invalid request data
  - `404`: Template not found

### Delete Template
- **URL**: `/api/workflow/formats/templates/<template_id>`
- **Method**: `DELETE`
- **Description**: Deletes a format template
- **URL Parameters**:
  - `template_id`: ID of the template
- **Response**:
  ```json
  {
    "status": "success"
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `404`: Template not found

## Field Descriptions

### Request/Response Fields
- **name**: Required string identifier for the format template
- **description**: Optional string describing the format's purpose
- **fields**: Required array of field definitions
- **format_type**: Optional string, one of "input", "output", or "bidirectional" (defaults to "output")
- **llm_instructions**: Optional string providing guidance to the LLM on how to interpret input data or structure output responses

### Field Definition Structure
Each field in the `fields` array should have:
- **name**: Required string identifier for the field
- **type**: Required string, one of "string", "number", "boolean", "array", "object"
- **required**: Required boolean indicating if the field is mandatory
- **description**: Optional string describing the field's purpose

## Example Usage

### Create a Format Template with LLM Instructions
```bash
curl -X POST http://localhost:5000/api/workflow/formats/templates \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Title-description JSON",
    "description": "Structured JSON with title and description fields",
    "fields": [
      {
        "name": "title",
        "type": "string",
        "required": true,
        "description": "The main title"
      },
      {
        "name": "description",
        "type": "string",
        "required": true,
        "description": "A description of the title"
      }
    ],
    "format_type": "output",
    "llm_instructions": "You must return your response in the following format, with no commentary or introduction—just the JSON object."
  }'
```

### Response Example
```json
{
  "id": 37,
  "name": "Title-description JSON",
  "description": "Structured JSON with title and description fields",
  "fields": [
    {
      "name": "title",
      "type": "string",
      "required": true,
      "description": "The main title"
    },
    {
      "name": "description",
      "type": "string",
      "required": true,
      "description": "A description of the title"
    }
  ],
  "format_type": "output",
  "llm_instructions": "You must return your response in the following format, with no commentary or introduction—just the JSON object."
}
```

## Stage Format Endpoints

### Get Stage Format
- **URL**: `/api/workflow/stages/<stage_id>/format`
- **Method**: `GET`
- **Description**: Retrieves format configuration for a stage
- **URL Parameters**:
  - `stage_id`: ID of the stage
- **Response**:
  ```json
  {
    "template_id": "integer",
    "config": {
      // Stage-specific format configuration
    }
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `404`: Stage not found

### Update Stage Format
- **URL**: `/api/workflow/stages/<stage_id>/format`
- **Method**: `POST`
- **Description**: Updates format configuration for a stage
- **URL Parameters**:
  - `stage_id`: ID of the stage
- **Request Body**:
  ```json
  {
    "template_id": "integer",
    "config": {
      // Stage-specific format configuration
    }
  }
  ```
- **Response**:
  ```json
  {
    "status": "success"
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `400`: Invalid request data
  - `404`: Stage not found

## Post Format Endpoints

### Get Post Format
- **URL**: `/api/workflow/posts/<post_id>/format`
- **Method**: `GET`
- **Description**: Retrieves format data for a post
- **URL Parameters**:
  - `post_id`: ID of the post
- **Response**:
  ```json
  {
    "template_id": "integer",
    "data": {
      // Format-specific data
    }
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `404`: Post not found

### Update Post Format
- **URL**: `/api/workflow/posts/<post_id>/format`
- **Method**: `POST`
- **Description**: Updates format data for a post
- **URL Parameters**:
  - `post_id`: ID of the post
- **Request Body**:
  ```json
  {
    "template_id": "integer",
    "data": {
      // Format-specific data
    }
  }
  ```
- **Response**:
  ```json
  {
    "status": "success"
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `400`: Invalid request data
  - `404`: Post not found

## Error Handling

All endpoints follow standard HTTP status codes and return error responses in the following format:

```json
{
  "error": {
    "code": "string",
    "message": "string",
    "details": {} // Optional additional error details
  }
}
```

Common error codes:
- `400`: Bad Request - Invalid input parameters
- `404`: Not Found - Resource does not exist
- `500`: Internal Server Error - Server-side error

## Database Schema

Format templates and configurations are stored in the following tables:
- `workflow_format_template`: Defines format templates
- `workflow_stage_format`: Maps formats to stages
- `workflow_post_format`: Stores post-specific format data

The schema ensures proper relationships between templates, stages, and posts.

## Format Types

### 1. Structure Format
Used for defining post structure and organization.
```json
{
    "type": "structure",
    "input_format": "json",
    "output_format": "json",
    "input_schema": {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "sections": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "content": {"type": "string"}
                    }
                }
            }
        }
    }
}
```

### 2. Content Format
Used for transforming content between different representations.
```json
{
    "type": "content",
    "input_format": "markdown",
    "output_format": "html",
    "output_rules": [
        "Preserve heading hierarchy",
        "Convert markdown links to HTML"
    ]
}
```

### 3. Metadata Format
Used for managing post metadata and properties.
```json
{
    "type": "metadata",
    "input_format": "json",
    "output_format": "json",
    "input_schema": {
        "type": "object",
        "properties": {
            "tags": {"type": "array"},
            "category": {"type": "string"},
            "publish_date": {"type": "string"}
        }
    }
}
```

## Related Documentation

- [Field Mapping API](fields.md)
- [Post Development](posts.md)
- [LLM Integration](llm.md) 