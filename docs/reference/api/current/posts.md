# Post-Related API Endpoints

All post-related endpoints are now under the `/api/workflow/posts/` base path.

## Development Endpoints

### Get Post Development Data
- **URL**: `/api/workflow/posts/<post_id>/development`
- **Method**: `GET`
- **Description**: Retrieves development data for a specific post
- **URL Parameters**:
  - `post_id`: ID of the post
- **Response**:
  ```json
  {
    "title": "string",
    "content": "string",
    // ... other development fields
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `404`: Post not found

### Update Post Development
- **URL**: `/api/workflow/posts/<post_id>/development`
- **Method**: `POST`
- **Description**: Updates development data for a specific post
- **URL Parameters**:
  - `post_id`: ID of the post
- **Request Body**:
  ```json
  {
    "title": "string",
    "content": "string"
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

## Structure Endpoints

### Plan Post Structure
- **URL**: `/api/workflow/posts/<post_id>/structure/plan`
- **Method**: `POST`
- **Description**: Plans the structure for a post
- **URL Parameters**:
  - `post_id`: ID of the post
- **Request Body**:
  ```json
  {
    "topic": "string",
    "keywords": ["string"]
  }
  ```
- **Response**:
  ```json
  {
    "sections": [
      {
        "title": "string",
        "content": "string"
      }
    ]
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `400`: Invalid request data

### Save Post Structure
- **URL**: `/api/workflow/posts/<post_id>/structure/save`
- **Method**: `POST`
- **Description**: Saves the structure for a post
- **URL Parameters**:
  - `post_id`: ID of the post
- **Request Body**:
  ```json
  {
    "sections": [
      {
        "title": "string",
        "content": "string"
      }
    ]
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

## Image Generation Endpoints

### Generate Images
- **URL**: `/api/workflow/posts/<post_id>/images/generate`
- **Method**: `POST`
- **Description**: Generates images for a post
- **URL Parameters**:
  - `post_id`: ID of the post
- **Request Body**:
  ```json
  {
    "prompt": "string",
    "count": "integer"
  }
  ```
- **Response**:
  ```json
  {
    "image_urls": ["string"]
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `400`: Invalid request data
  - `500`: Image generation error

## Section Endpoints

### Get Post Sections
- **URL**: `/api/workflow/posts/<post_id>/sections`
- **Method**: `GET`
- **Description**: Retrieves all sections for a post
- **URL Parameters**:
  - `post_id`: ID of the post
- **Response**:
  ```json
  [
    {
      "id": "integer",
      "title": "string",
      "content": "string"
    }
  ]
  ```
- **Status Codes**:
  - `200`: Success
  - `404`: Post not found

### Get Section
- **URL**: `/api/workflow/posts/<post_id>/sections/<section_id>`
- **Method**: `GET`
- **Description**: Retrieves a specific section
- **URL Parameters**:
  - `post_id`: ID of the post
  - `section_id`: ID of the section
- **Response**:
  ```json
  {
    "id": "integer",
    "title": "string",
    "content": "string"
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `404`: Section not found

### Get Section Fields
- **URL**: `/api/workflow/posts/<post_id>/sections/<section_id>/fields`
- **Method**: `GET`
- **Description**: Retrieves fields for a specific section
- **URL Parameters**:
  - `post_id`: ID of the post
  - `section_id`: ID of the section
- **Response**:
  ```json
  {
    "fields": [
      {
        "name": "string",
        "value": "string"
      }
    ]
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `404`: Section not found

## Stage Endpoints

### Get Post Stages
- **URL**: `/api/workflow/posts/<post_id>/stages`
- **Method**: `GET`
- **Description**: Retrieves all stages for a post
- **URL Parameters**:
  - `post_id`: ID of the post
- **Response**:
  ```json
  [
    {
      "id": "integer",
      "name": "string",
      "order": "integer"
    }
  ]
  ```
- **Status Codes**:
  - `200`: Success
  - `404`: Post not found

### Get Stage
- **URL**: `/api/workflow/posts/<post_id>/stages/<stage_id>`
- **Method**: `GET`
- **Description**: Retrieves a specific stage
- **URL Parameters**:
  - `post_id`: ID of the post
  - `stage_id`: ID of the stage
- **Response**:
  ```json
  {
    "id": "integer",
    "name": "string",
    "order": "integer"
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `404`: Stage not found

### Get Stage Sub-stages
- **URL**: `/api/workflow/posts/<post_id>/stages/<stage_id>/sub-stages`
- **Method**: `GET`
- **Description**: Retrieves sub-stages for a specific stage
- **URL Parameters**:
  - `post_id`: ID of the post
  - `stage_id`: ID of the stage
- **Response**:
  ```json
  [
    {
      "id": "integer",
      "name": "string",
      "order": "integer"
    }
  ]
  ```
- **Status Codes**:
  - `200`: Success
  - `404`: Stage not found

### Transition Stage
- **URL**: `/api/workflow/posts/<post_id>/stages/<stage_id>/transition`
- **Method**: `POST`
- **Description**: Transitions a post to a new stage
- **URL Parameters**:
  - `post_id`: ID of the post
  - `stage_id`: ID of the stage
- **Request Body**:
  ```json
  {
    "target_stage": "string",
    "target_substage": "string"
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
  - `400`: Invalid transition
  - `404`: Stage not found

## Error Handling

### Common Error Codes

- 400: Bad Request (invalid parameters)
- 404: Not Found (post or section doesn't exist)
- 422: Unprocessable Entity (invalid field values)
- 500: Internal Server Error

### Error Response Example

```json
{
    "status": "error",
    "message": "Failed to update post development data",
    "errors": [
        "Invalid field name: research_note (did you mean research_notes?)",
        "Content exceeds maximum length"
    ]
}
```

## Related Documentation

- [Field Mapping API](fields.md)
- [LLM Integration](llm.md)
- [Workflow Stages](workflow.md) 