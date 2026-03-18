# Image Management API Endpoints

All image-related endpoints are under the `/api/images/` base path.

## Image Generation

### Generate Image
- **URL**: `/api/images/generate`
- **Method**: `POST`
- **Description**: Generates images using ComfyUI integration
- **Request Body**:
  ```json
  {
    "prompt": "string",
    "negative_prompt": "string",
    "width": "integer",
    "height": "integer",
    "steps": "integer",
    "cfg_scale": "float",
    "seed": "integer"
  }
  ```
- **Response**:
  ```json
  {
    "status": "success",
    "image_url": "string",
    "metadata": {
      "prompt": "string",
      "negative_prompt": "string",
      "width": "integer",
      "height": "integer",
      "steps": "integer",
      "cfg_scale": "float",
      "seed": "integer"
    }
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `400`: Invalid request data
  - `500`: Image generation error

### Generate Images for Post
- **URL**: `/api/v1/posts/<post_id>/generate_images`
- **Method**: `POST`
- **Description**: Generates images for a specific post (legacy endpoint)
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

## Image Settings

### Get Image Settings
- **URL**: `/api/images/settings`
- **Method**: `GET`
- **Description**: Retrieves all image generation settings
- **Response**:
  ```json
  [
    {
      "id": "integer",
      "name": "string",
      "value": "string",
      "description": "string"
    }
  ]
  ```
- **Status Codes**:
  - `200`: Success

### Get Image Setting
- **URL**: `/api/images/settings/<setting_id>`
- **Method**: `GET`
- **Description**: Retrieves a specific image setting
- **URL Parameters**:
  - `setting_id`: ID of the setting
- **Response**:
  ```json
  {
    "id": "integer",
    "name": "string",
    "value": "string",
    "description": "string"
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `404`: Setting not found

### Create Image Setting
- **URL**: `/api/images/settings`
- **Method**: `POST`
- **Description**: Creates a new image setting
- **Request Body**:
  ```json
  {
    "name": "string",
    "value": "string",
    "description": "string"
  }
  ```
- **Response**:
  ```json
  {
    "id": "integer",
    "name": "string",
    "value": "string",
    "description": "string"
  }
  ```
- **Status Codes**:
  - `201`: Created successfully
  - `400`: Invalid request data

### Update Image Setting
- **URL**: `/api/images/settings/<setting_id>`
- **Method**: `PUT`
- **Description**: Updates an image setting
- **URL Parameters**:
  - `setting_id`: ID of the setting
- **Request Body**:
  ```json
  {
    "name": "string",
    "value": "string",
    "description": "string"
  }
  ```
- **Response**:
  ```json
  {
    "id": "integer",
    "name": "string",
    "value": "string",
    "description": "string"
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `400`: Invalid request data
  - `404`: Setting not found

### Delete Image Setting
- **URL**: `/api/images/settings/<setting_id>`
- **Method**: `DELETE`
- **Description**: Deletes an image setting
- **URL Parameters**:
  - `setting_id`: ID of the setting
- **Response**:
  ```json
  {
    "status": "success"
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `404`: Setting not found

## Image Styles

### Get Image Styles
- **URL**: `/api/images/styles`
- **Method**: `GET`
- **Description**: Retrieves all image styles
- **Response**:
  ```json
  [
    {
      "id": "integer",
      "name": "string",
      "description": "string",
      "prompt_template": "string"
    }
  ]
  ```
- **Status Codes**:
  - `200`: Success

### Get Image Style
- **URL**: `/api/images/styles/<style_id>`
- **Method**: `GET`
- **Description**: Retrieves a specific image style
- **URL Parameters**:
  - `style_id`: ID of the style
- **Response**:
  ```json
  {
    "id": "integer",
    "name": "string",
    "description": "string",
    "prompt_template": "string"
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `404`: Style not found

### Create Image Style
- **URL**: `/api/images/styles`
- **Method**: `POST`
- **Description**: Creates a new image style
- **Request Body**:
  ```json
  {
    "name": "string",
    "description": "string",
    "prompt_template": "string"
  }
  ```
- **Response**:
  ```json
  {
    "id": "integer",
    "name": "string",
    "description": "string",
    "prompt_template": "string"
  }
  ```
- **Status Codes**:
  - `201`: Created successfully
  - `400`: Invalid request data

### Update Image Style
- **URL**: `/api/images/styles/<style_id>`
- **Method**: `PUT`
- **Description**: Updates an image style
- **URL Parameters**:
  - `style_id`: ID of the style
- **Request Body**:
  ```json
  {
    "name": "string",
    "description": "string",
    "prompt_template": "string"
  }
  ```
- **Response**:
  ```json
  {
    "id": "integer",
    "name": "string",
    "description": "string",
    "prompt_template": "string"
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `400`: Invalid request data
  - `404`: Style not found

### Delete Image Style
- **URL**: `/api/images/styles/<style_id>`
- **Method**: `DELETE`
- **Description**: Deletes an image style
- **URL Parameters**:
  - `style_id`: ID of the style
- **Response**:
  ```json
  {
    "status": "success"
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `404`: Style not found

## Image Formats

### Get Image Formats
- **URL**: `/api/images/formats`
- **Method**: `GET`
- **Description**: Retrieves all image formats
- **Response**:
  ```json
  [
    {
      "id": "integer",
      "name": "string",
      "description": "string",
      "width": "integer",
      "height": "integer"
    }
  ]
  ```
- **Status Codes**:
  - `200`: Success

### Get Image Format
- **URL**: `/api/images/formats/<format_id>`
- **Method**: `GET`
- **Description**: Retrieves a specific image format
- **URL Parameters**:
  - `format_id`: ID of the format
- **Response**:
  ```json
  {
    "id": "integer",
    "name": "string",
    "description": "string",
    "width": "integer",
    "height": "integer"
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `404`: Format not found

### Create Image Format
- **URL**: `/api/images/formats`
- **Method**: `POST`
- **Description**: Creates a new image format
- **Request Body**:
  ```json
  {
    "name": "string",
    "description": "string",
    "width": "integer",
    "height": "integer"
  }
  ```
- **Response**:
  ```json
  {
    "id": "integer",
    "name": "string",
    "description": "string",
    "width": "integer",
    "height": "integer"
  }
  ```
- **Status Codes**:
  - `201`: Created successfully
  - `400`: Invalid request data

### Update Image Format
- **URL**: `/api/images/formats/<format_id>`
- **Method**: `PUT`
- **Description**: Updates an image format
- **URL Parameters**:
  - `format_id`: ID of the format
- **Request Body**:
  ```json
  {
    "name": "string",
    "description": "string",
    "width": "integer",
    "height": "integer"
  }
  ```
- **Response**:
  ```json
  {
    "id": "integer",
    "name": "string",
    "description": "string",
    "width": "integer",
    "height": "integer"
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `400`: Invalid request data
  - `404`: Format not found

### Delete Image Format
- **URL**: `/api/images/formats/<format_id>`
- **Method**: `DELETE`
- **Description**: Deletes an image format
- **URL Parameters**:
  - `format_id`: ID of the format
- **Response**:
  ```json
  {
    "status": "success"
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `404`: Format not found

## Prompt Examples

### Get Prompt Examples
- **URL**: `/api/images/prompt_examples`
- **Method**: `GET`
- **Description**: Retrieves all prompt examples
- **Response**:
  ```json
  [
    {
      "id": "integer",
      "title": "string",
      "prompt": "string",
      "category": "string"
    }
  ]
  ```
- **Status Codes**:
  - `200`: Success

### Get Prompt Example
- **URL**: `/api/images/prompt_examples/<example_id>`
- **Method**: `GET`
- **Description**: Retrieves a specific prompt example
- **URL Parameters**:
  - `example_id`: ID of the example
- **Response**:
  ```json
  {
    "id": "integer",
    "title": "string",
    "prompt": "string",
    "category": "string"
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `404`: Example not found

### Create Prompt Example
- **URL**: `/api/images/prompt_examples`
- **Method**: `POST`
- **Description**: Creates a new prompt example
- **Request Body**:
  ```json
  {
    "title": "string",
    "prompt": "string",
    "category": "string"
  }
  ```
- **Response**:
  ```json
  {
    "id": "integer",
    "title": "string",
    "prompt": "string",
    "category": "string"
  }
  ```
- **Status Codes**:
  - `201`: Created successfully
  - `400`: Invalid request data

### Update Prompt Example
- **URL**: `/api/images/prompt_examples/<example_id>`
- **Method**: `PUT`
- **Description**: Updates a prompt example
- **URL Parameters**:
  - `example_id`: ID of the example
- **Request Body**:
  ```json
  {
    "title": "string",
    "prompt": "string",
    "category": "string"
  }
  ```
- **Response**:
  ```json
  {
    "id": "integer",
    "title": "string",
    "prompt": "string",
    "category": "string"
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `400`: Invalid request data
  - `404`: Example not found

### Delete Prompt Example
- **URL**: `/api/images/prompt_examples/<example_id>`
- **Method**: `DELETE`
- **Description**: Deletes a prompt example
- **URL Parameters**:
  - `example_id`: ID of the example
- **Response**:
  ```json
  {
    "status": "success"
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `404`: Example not found

## ComfyUI Integration

### Get ComfyUI Status
- **URL**: `/api/images/comfyui/status`
- **Method**: `GET`
- **Description**: Checks ComfyUI service status
- **Response**:
  ```json
  {
    "status": "string",
    "message": "string"
  }
  ```
- **Status Codes**:
  - `200`: Success

### Start ComfyUI
- **URL**: `/api/images/comfyui/start`
- **Method**: `POST`
- **Description**: Starts ComfyUI service
- **Response**:
  ```json
  {
    "status": "success",
    "message": "ComfyUI started successfully"
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `500`: Service start error

## Error Handling

### Common Error Codes

- 400: Bad Request (invalid parameters)
- 404: Not Found (resource doesn't exist)
- 500: Internal Server Error (image generation failed)
- 503: Service Unavailable (ComfyUI not available)

### Error Response Example

```json
{
    "status": "error",
    "message": "Image generation failed",
    "details": {
        "error": "ComfyUI service unavailable",
        "suggestion": "Check if ComfyUI is running"
    }
}
```

## Related Documentation

- [Post Management](posts.md)
- [LLM Integration](llm.md)
- [Workflow Stages](workflow.md) 