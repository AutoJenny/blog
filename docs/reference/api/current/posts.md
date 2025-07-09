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

## Post Section Text Fields Endpoint

### Get Post Section Text Fields
- **URL**: `/api/workflow/post_section_fields`
- **Method**: `GET`
- **Description**: Returns all text/content fields available in the post_section table. This endpoint is used by the frontend LLM panel to populate the Outputs dropdown for Writing stage actions.
- **URL Parameters**: None (global endpoint, not post-specific)
- **Response**:
  ```json
  {
    "fields": [
      "section_heading",
      "ideas_to_include", 
      "facts_to_include",
      "highlighting",
      "image_concepts",
      "image_prompts",
      "watermarking",
      "image_meta_descriptions",
      "image_captions",
      "generated_image_url",
      "section_description",
      "status",
      "polished",
      "draft"
    ]
  }
  ```
- **Status Codes**:
  - `200`: Success
- **Usage Notes**:
  - **IMPORTANT**: This endpoint does NOT take a post_id parameter
  - Used specifically for Writing stage LLM action Outputs dropdown
  - Returns all text fields from post_section table schema
  - Includes the new simplified content fields: `draft` and `polished`
  - Frontend JavaScript uses this to dynamically populate field selectors
- **Testing**:
  ```bash
  curl -s "http://localhost:5000/api/workflow/post_section_fields" -H "Accept: application/json"
  ```

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