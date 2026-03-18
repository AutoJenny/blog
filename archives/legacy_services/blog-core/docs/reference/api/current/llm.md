# LLM Integration API Endpoints

**Note:** LLM endpoints are distributed across multiple paths:
- `/api/llm/` - Core LLM functionality
- `/api/workflow/llm/` - Workflow-specific LLM operations
- `/api/v1/llm/` - Legacy endpoints (deprecated)

## Core LLM Endpoints (`/api/llm/`)

### Get LLM Configuration
- **URL**: `/api/llm/config`
- **Method**: `GET`
- **Description**: Retrieves current LLM configuration
- **Response**:
  ```json
  {
    "provider_type": "string",
    "model_name": "string",
    "api_base": "string",
    "is_active": "boolean"
  }
  ```
- **Status Codes**:
  - `200`: Success

### Update LLM Configuration
- **URL**: `/api/llm/config`
- **Method**: `POST`
- **Description**: Updates LLM configuration
- **Request Body**:
  ```json
  {
    "provider_type": "string",
    "model_name": "string",
    "api_base": "string"
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
  - `400`: Invalid configuration

### Test LLM Connection
- **URL**: `/api/llm/test`
- **Method**: `POST`
- **Description**: Tests LLM connection and configuration
- **Response**:
  ```json
  {
    "status": "success",
    "message": "Connection successful"
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `500`: Connection failed

## Provider Endpoints

### Get Providers
- **URL**: `/api/llm/providers`
- **Method**: `GET`
- **Description**: Retrieves all available LLM providers
- **Response**:
  ```json
  [
    {
      "id": "integer",
      "name": "string",
      "status": "string",
      "config": {
        // Provider-specific configuration
      }
    }
  ]
  ```
- **Status Codes**:
  - `200`: Success

### Create Provider
- **URL**: `/api/llm/providers`
- **Method**: `POST`
- **Description**: Creates a new LLM provider
- **Request Body**:
  ```json
  {
    "name": "string",
    "provider_type": "string",
    "api_base": "string",
    "config": {}
  }
  ```
- **Response**:
  ```json
  {
    "id": "integer",
    "name": "string",
    "status": "string"
  }
  ```
- **Status Codes**:
  - `201`: Created successfully
  - `400`: Invalid request data

### Get Provider
- **URL**: `/api/llm/providers/<id>`
- **Method**: `GET`
- **Description**: Retrieves a specific LLM provider
- **URL Parameters**:
  - `id`: ID of the provider
- **Response**:
  ```json
  {
    "id": "integer",
    "name": "string",
    "status": "string",
    "config": {}
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `404`: Provider not found

### Update Provider
- **URL**: `/api/llm/providers/<id>`
- **Method**: `PUT`
- **Description**: Updates an LLM provider
- **URL Parameters**:
  - `id`: ID of the provider
- **Request Body**:
  ```json
  {
    "name": "string",
    "provider_type": "string",
    "api_base": "string",
    "config": {}
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
  - `404`: Provider not found

### Delete Provider
- **URL**: `/api/llm/providers/<id>`
- **Method**: `DELETE`
- **Description**: Deletes an LLM provider
- **URL Parameters**:
  - `id`: ID of the provider
- **Response**:
  ```json
  {
    "status": "success"
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `404`: Provider not found

### Start Provider (Legacy)
- **URL**: `/api/v1/llm/providers/start`
- **Method**: `POST`
- **Description**: Starts an LLM provider (legacy endpoint)
- **Request Body**:
  ```json
  {
    "provider_id": "integer"
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
  - `400`: Invalid provider ID
  - `500`: Provider start error

### Test Provider (Legacy)
- **URL**: `/api/v1/llm/providers/<provider_id>/test`
- **Method**: `POST`
- **Description**: Tests an LLM provider (legacy endpoint)
- **URL Parameters**:
  - `provider_id`: ID of the provider
- **Response**:
  ```json
  {
    "status": "string",
    "message": "string"
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `400`: Invalid provider ID
  - `500`: Provider test error

### Get Models
- **URL**: `/api/llm/models`
- **Method**: `GET`
- **Description**: Retrieves available LLM models
- **Response**:
  ```json
  [
    {
      "id": "string",
      "name": "string",
      "provider": "string",
      "capabilities": ["string"]
    }
  ]
  ```
- **Status Codes**:
  - `200`: Success

### Create Model
- **URL**: `/api/llm/models`
- **Method**: `POST`
- **Description**: Creates a new LLM model configuration
- **Request Body**:
  ```json
  {
    "name": "string",
    "provider_id": "integer",
    "config": {}
  }
  ```
- **Response**:
  ```json
  {
    "id": "string",
    "name": "string",
    "provider": "string"
  }
  ```
- **Status Codes**:
  - `201`: Created successfully
  - `400`: Invalid request data

## Action Endpoints

### Get Actions
- **URL**: `/api/llm/actions`
- **Method**: `GET`
- **Description**: Retrieves all available LLM actions
- **Response**:
  ```json
  [
    {
      "id": "integer",
      "name": "string",
      "description": "string",
      "config": {
        // Action-specific configuration
      }
    }
  ]
  ```
- **Status Codes**:
  - `200`: Success

### Get Action
- **URL**: `/api/llm/actions/<action_id>`
- **Method**: `GET`
- **Description**: Retrieves details for a specific LLM action
- **URL Parameters**:
  - `action_id`: ID of the action
- **Response**:
  ```json
  {
    "id": "integer",
    "name": "string",
    "description": "string",
    "config": {
      // Action-specific configuration
    }
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `404`: Action not found

### Create Action
- **URL**: `/api/llm/actions`
- **Method**: `POST`
- **Description**: Creates a new LLM action
- **Request Body**:
  ```json
  {
    "name": "string",
    "description": "string",
    "config": {
      // Action-specific configuration
    }
  }
  ```
- **Response**:
  ```json
  {
    "id": "integer",
    "name": "string",
    "description": "string"
  }
  ```
- **Status Codes**:
  - `201`: Created successfully
  - `400`: Invalid request data

### Update Action
- **URL**: `/api/llm/actions/<action_id>`
- **Method**: `PUT`
- **Description**: Updates an LLM action
- **URL Parameters**:
  - `action_id`: ID of the action
- **Request Body**:
  ```json
  {
    "name": "string",
    "description": "string",
    "config": {
      // Action-specific configuration
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
  - `404`: Action not found

### Delete Action
- **URL**: `/api/llm/actions/<action_id>`
- **Method**: `DELETE`
- **Description**: Deletes an LLM action
- **URL Parameters**:
  - `action_id`: ID of the action
- **Response**:
  ```json
  {
    "status": "success"
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `404`: Action not found

### Execute Action
- **URL**: `/api/llm/actions/<action_id>/execute`
- **Method**: `POST`
- **Description**: Executes an LLM action
- **URL Parameters**:
  - `action_id`: ID of the action
- **Request Body**:
  ```json
  {
    "input": "string",
    "config": {
      // Optional run-specific configuration
    }
  }
  ```
- **Response**:
  ```json
  {
    "result": "string",
    "metadata": {
      "model": "string",
      "provider": "string",
      "tokens": {
        "prompt": "integer",
        "completion": "integer",
        "total": "integer"
      }
    }
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `400`: Invalid request
  - `404`: Action not found
  - `500`: LLM execution error

### Test Action
- **URL**: `/api/llm/actions/<action_id>/test`
- **Method**: `POST`
- **Description**: Tests an LLM action with sample data
- **URL Parameters**:
  - `action_id`: ID of the action
- **Request Body**:
  ```json
  {
    "test_input": "string"
  }
  ```
- **Response**:
  ```json
  {
    "result": "string",
    "test_passed": "boolean"
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `400`: Invalid request
  - `404`: Action not found

### Get Action History
- **URL**: `/api/llm/actions/<action_id>/history`
- **Method**: `GET`
- **Description**: Retrieves execution history for an action
- **URL Parameters**:
  - `action_id`: ID of the action
- **Response**:
  ```json
  [
    {
      "id": "integer",
      "timestamp": "string",
      "input": "string",
      "result": "string",
      "status": "string"
    }
  ]
  ```
- **Status Codes**:
  - `200`: Success
  - `404`: Action not found

## Workflow LLM Endpoints (`/api/workflow/llm/`)

### Get Workflow LLM Models
- **URL**: `/api/workflow/llm/models`
- **Method**: `GET`
- **Description**: Retrieves LLM models for workflow operations
- **Response**:
  ```json
  [
    {
      "id": "string",
      "name": "string",
      "provider": "string"
    }
  ]
  ```
- **Status Codes**:
  - `200`: Success

### Direct LLM Call
- **URL**: `/api/workflow/llm/direct`
- **Method**: `POST`
- **Description**: Makes a direct LLM call for workflow operations
- **Request Body**:
  ```json
  {
    "prompt": "string",
    "model": "string",
    "temperature": "float"
  }
  ```
- **Response**:
  ```json
  {
    "result": "string",
    "metadata": {
      "model": "string",
      "tokens": "integer"
    }
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `400`: Invalid request
  - `500`: LLM execution error

## Legacy Endpoints (`/api/v1/llm/`)

### Get Models (Legacy)
- **URL**: `/api/v1/llm/models`
- **Method**: `GET`
- **Description**: Retrieves available LLM models (legacy endpoint)
- **Response**:
  ```json
  [
    {
      "id": "string",
      "name": "string",
      "provider": "string"
    }
  ]
  ```
- **Status Codes**:
  - `200`: Success

### Get Providers (Legacy)
- **URL**: `/api/v1/llm/providers`
- **Method**: `GET`
- **Description**: Retrieves all available LLM providers (legacy endpoint)
- **Response**:
  ```json
  [
    {
      "id": "integer",
      "name": "string",
      "status": "string"
    }
  ]
  ```
- **Status Codes**:
  - `200`: Success

### Get Action (Legacy)
- **URL**: `/api/v1/llm/actions/<action_id>`
- **Method**: `GET`
- **Description**: Retrieves details for a specific LLM action (legacy endpoint)
- **URL Parameters**:
  - `action_id`: ID of the action
- **Response**:
  ```json
  {
    "id": "integer",
    "name": "string",
    "description": "string"
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `404`: Action not found

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

## Rate Limiting

LLM endpoints are subject to rate limiting based on provider constraints. Rate limit information is included in response headers:
- `X-RateLimit-Limit`: Maximum requests per time window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Time until rate limit resets (Unix timestamp)

## Notes

1. All LLM providers are configured to use local endpoints (e.g., Ollama) rather than external services.
2. Provider configuration and credentials are managed through environment variables.
3. Action configurations are stored in the database and can be customized per workflow stage.

## Related Documentation

- [Field Mapping API](fields.md)
- [Post Development](posts.md)
- [Format Templates](formats.md) 