# LLM API

## Overview
The LLM API handles all LLM-related operations, including prompt management, model configuration, and action execution.

## Endpoints

### List Actions
```http
GET /api/v1/llm/actions
```

#### Response
```json
{
    "status": "success",
    "data": {
        "actions": [
            {
                "id": 1,
                "name": "Generate Summary",
                "description": "Generate a summary from idea seed",
                "input_field": "idea_seed",
                "output_field": "summary",
                "model": "gpt-4",
                "status": "active",
                "created_at": "2024-03-20T10:00:00Z",
                "updated_at": "2024-03-20T10:00:00Z"
            }
        ]
    }
}
```

### Execute Action
```http
POST /api/v1/llm/actions/{action_id}/execute
```

#### Request Body
```json
{
    "input_data": {
        "idea_seed": "Initial idea for the post"
    }
}
```

#### Response
```json
{
    "status": "success",
    "data": {
        "action_run": {
            "id": 1,
            "action_id": 1,
            "input_data": {
                "idea_seed": "Initial idea for the post"
            },
            "output_data": {
                "summary": "Generated summary text"
            },
            "status": "completed",
            "diagnostics": {
                "tokens_used": 150,
                "execution_time": 2.5,
                "model": "gpt-4"
            },
            "created_at": "2024-03-20T10:00:00Z",
            "updated_at": "2024-03-20T10:00:00Z"
        }
    }
}
```

### Get Action Run
```http
GET /api/v1/llm/actions/{action_id}/runs/{run_id}
```

#### Response
```json
{
    "status": "success",
    "data": {
        "action_run": {
            "id": 1,
            "action_id": 1,
            "input_data": {
                "idea_seed": "Initial idea for the post"
            },
            "output_data": {
                "summary": "Generated summary text"
            },
            "status": "completed",
            "diagnostics": {
                "tokens_used": 150,
                "execution_time": 2.5,
                "model": "gpt-4"
            },
            "created_at": "2024-03-20T10:00:00Z",
            "updated_at": "2024-03-20T10:00:00Z"
        }
    }
}
```

### List Prompts
```http
GET /api/v1/llm/prompts
```

#### Response
```json
{
    "status": "success",
    "data": {
        "prompts": [
            {
                "id": 1,
                "name": "Summary Generation",
                "content": "Generate a summary based on the following idea: {idea_seed}",
                "variables": ["idea_seed"],
                "created_at": "2024-03-20T10:00:00Z",
                "updated_at": "2024-03-20T10:00:00Z"
            }
        ]
    }
}
```

### List Models
```http
GET /api/v1/llm/models
```

#### Response
```json
{
    "status": "success",
    "data": {
        "models": [
            {
                "id": 1,
                "name": "gpt-4",
                "provider": "openai",
                "max_tokens": 8192,
                "status": "active",
                "created_at": "2024-03-20T10:00:00Z",
                "updated_at": "2024-03-20T10:00:00Z"
            }
        ]
    }
}
```

## Error Responses

### Action Not Found
```json
{
    "status": "error",
    "message": "Action not found",
    "errors": [
        {
            "code": "not_found",
            "message": "Action with id 1 not found"
        }
    ]
}
```

### Execution Error
```json
{
    "status": "error",
    "message": "Action execution failed",
    "errors": [
        {
            "code": "execution_error",
            "message": "Failed to generate summary",
            "details": "Model error: Rate limit exceeded"
        }
    ]
}
```

## Notes
- All timestamps are in ISO 8601 format
- All endpoints require authentication
- Rate limiting applies to all endpoints
- Action execution may take several seconds
- Diagnostics include token usage and execution time
- Model availability may vary based on provider status 