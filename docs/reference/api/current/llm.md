# LLM Integration API Endpoints

All LLM-related endpoints are now under the `/api/workflow/llm/` base path.

## Provider Endpoints

### Get Providers
- **URL**: `/api/workflow/llm/providers`
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

### Start Provider
- **URL**: `/api/workflow/llm/providers/start`
- **Method**: `POST`
- **Description**: Starts an LLM provider
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

### Test Provider
- **URL**: `/api/workflow/llm/providers/<provider_id>/test`
- **Method**: `POST`
- **Description**: Tests an LLM provider
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
- **URL**: `/api/workflow/llm/models`
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

## Action Endpoints

### Get Action
- **URL**: `/api/workflow/llm/actions/<action_id>`
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

### Run LLM
- **URL**: `/api/workflow/llm/run`
- **Method**: `POST`
- **Description**: Executes an LLM action
- **Request Body**:
  ```json
  {
    "action_id": "integer",
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