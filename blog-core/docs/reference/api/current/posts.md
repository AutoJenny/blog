# Post-Related API Endpoints

**Note:** This system has both current `/api/workflow/` endpoints and legacy `/api/v1/` endpoints. Both are documented below.

## Post Creation Endpoints

### Create New Post
- **URL**: `/blog/new`
- **Method**: `POST`
- **Description**: Creates a new post with basic idea and redirects to workflow planning
- **Request Body**:
  ```json
  {
    "basic_idea": "string"
  }
  ```
- **Response**:
  ```json
  {
    "id": "integer",
    "message": "Post created successfully",
    "slug": "string"
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `400`: Invalid request data
- **Frontend Behavior**: After successful creation, automatically redirects to `/workflow/posts/<id>/planning/idea`
- **Example**:
  ```bash
  curl -X POST "http://localhost:5000/blog/new" \
       -H "Content-Type: application/json" \
       -d '{"basic_idea": "My new blog post idea"}'
  ```

## Development Endpoints

### Get Post Development Data (Legacy v1)
- **URL**: `/api/v1/post/<post_id>/development`
- **Method**: `GET`
- **Description**: Retrieves development data for a specific post (legacy endpoint)
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

### Update Post Development (Legacy v1)
- **URL**: `/api/v1/post/<post_id>/development`
- **Method**: `POST`
- **Description**: Updates development data for a specific post (legacy endpoint)
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

### Get Post Development Data (Current)
- **URL**: `/api/workflow/posts/<post_id>/development`
- **Method**: `GET`
- **Description**: Retrieves development data for a specific post (current endpoint)
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

### Update Post Development (Current)
- **URL**: `/api/workflow/posts/<post_id>/development`
- **Method**: `POST`
- **Description**: Updates development data for a specific post (current endpoint)
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

## Section Endpoints

### Get Post Sections (Legacy v1)
- **URL**: `/api/v1/post/<post_id>/sections`
- **Method**: `GET`
- **Description**: Retrieves all sections for a post (legacy endpoint)
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

### Get Post Sections (Current)
- **URL**: `/api/workflow/posts/<post_id>/sections`
- **Method**: `GET`
- **Description**: Retrieves all sections for a post (current endpoint)
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

### Create Section (Legacy v1)
- **URL**: `/api/v1/post/<post_id>/sections`
- **Method**: `POST`
- **Description**: Creates a new section for a post (legacy endpoint)
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
    "id": "integer",
    "title": "string",
    "content": "string"
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `400`: Invalid request data

### Create Section (Current)
- **URL**: `/api/workflow/posts/<post_id>/sections`
- **Method**: `POST`
- **Description**: Creates a new section for a post (current endpoint)
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
    "id": "integer",
    "title": "string",
    "content": "string"
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `400`: Invalid request data

### Get Section (Legacy v1)
- **URL**: `/api/v1/section/<section_id>`
- **Method**: `GET`
- **Description**: Retrieves a specific section (legacy endpoint)
- **URL Parameters**:
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

### Get Section (Current)
- **URL**: `/api/workflow/posts/<post_id>/sections/<section_id>`
- **Method**: `GET`
- **Description**: Retrieves a specific section (current endpoint)
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

### Update Section (Legacy v1)
- **URL**: `/api/v1/section/<section_id>`
- **Method**: `PUT`
- **Description**: Updates a specific section (legacy endpoint)
- **URL Parameters**:
  - `section_id`: ID of the section
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
  - `404`: Section not found

### Update Section (Current)
- **URL**: `/api/workflow/posts/<post_id>/sections/<section_id>`
- **Method**: `PUT`
- **Description**: Updates a specific section (current endpoint)
- **URL Parameters**:
  - `post_id`: ID of the post
  - `section_id`: ID of the section
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
  - `404`: Section not found

### Delete Section (Legacy v1)
- **URL**: `/api/v1/section/<section_id>`
- **Method**: `DELETE`
- **Description**: Deletes a specific section (legacy endpoint)
- **URL Parameters**:
  - `section_id`: ID of the section
- **Response**:
  ```json
  {
    "status": "success"
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `404`: Section not found

### Delete Section (Current)
- **URL**: `/api/workflow/posts/<post_id>/sections/<section_id>`
- **Method**: `DELETE`
- **Description**: Deletes a specific section (current endpoint)
- **URL Parameters**:
  - `post_id`: ID of the post
  - `section_id`: ID of the section
- **Response**:
  ```json
  {
    "status": "success"
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

## Workflow LLM Endpoints

### Run Workflow LLM
- **URL**: `/api/workflow/posts/<post_id>/<stage>/<substage>/llm`
- **Method**: `POST`
- **Description**: Executes LLM processing for a specific workflow stage/substage
- **URL Parameters**:
  - `post_id`: ID of the post
  - `stage`: Workflow stage name
  - `substage`: Workflow substage name
- **Request Body**:
  ```json
  {
    "prompt": "string",
    "output_field": "string",
    "output_table": "string",
    "section_ids": ["integer"]
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "result": "string"
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `400`: Invalid request
  - `404`: Post or stage not found

### Run Writing LLM
- **URL**: `/api/workflow/posts/<post_id>/<stage>/<substage>/writing_llm`
- **Method**: `POST`
- **Description**: Executes LLM processing specifically for writing stage
- **URL Parameters**:
  - `post_id`: ID of the post
  - `stage`: Workflow stage name
  - `substage`: Workflow substage name
- **Request Body**:
  ```json
  {
    "prompt": "string",
    "output_field": "string",
    "output_table": "string",
    "section_ids": ["integer"]
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "result": "string"
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `400`: Invalid request
  - `404`: Post or stage not found

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

## Migration Notes

- Legacy `/api/v1/` endpoints are still functional but deprecated
- New development should use `/api/workflow/` endpoints
- Both endpoint sets provide the same functionality
- Migration to current endpoints is recommended for new features

## Related Documentation

- [Field Mapping API](fields.md)
- [LLM Integration](llm.md)
- [Workflow Stages](workflow.md) 