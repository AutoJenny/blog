# ComfyUI API

## Overview
The ComfyUI API handles all ComfyUI-related operations, including workflow management, image generation, and node configuration.

## Endpoints

### List Workflows
```http
GET /api/v1/comfyui/workflows
```

#### Response
```json
{
    "status": "success",
    "data": {
        "workflows": [
            {
                "id": 1,
                "name": "Blog Post Image",
                "description": "Generate blog post header image",
                "nodes": [
                    {
                        "id": "text_to_image",
                        "type": "text_to_image",
                        "inputs": {
                            "prompt": "{prompt}",
                            "negative_prompt": "{negative_prompt}"
                        }
                    }
                ],
                "created_at": "2024-03-20T10:00:00Z",
                "updated_at": "2024-03-20T10:00:00Z"
            }
        ]
    }
}
```

### Execute Workflow
```http
POST /api/v1/comfyui/workflows/{workflow_id}/execute
```

#### Request Body
```json
{
    "inputs": {
        "prompt": "A beautiful landscape",
        "negative_prompt": "ugly, blurry"
    }
}
```

#### Response
```json
{
    "status": "success",
    "data": {
        "execution": {
            "id": 1,
            "workflow_id": 1,
            "status": "running",
            "progress": 0,
            "created_at": "2024-03-20T10:00:00Z",
            "updated_at": "2024-03-20T10:00:00Z"
        }
    }
}
```

### Get Execution Status
```http
GET /api/v1/comfyui/executions/{execution_id}
```

#### Response
```json
{
    "status": "success",
    "data": {
        "execution": {
            "id": 1,
            "workflow_id": 1,
            "status": "completed",
            "progress": 100,
            "outputs": {
                "images": [
                    {
                        "url": "/api/v1/images/generated/1.png",
                        "width": 1024,
                        "height": 768
                    }
                ]
            },
            "created_at": "2024-03-20T10:00:00Z",
            "updated_at": "2024-03-20T10:00:00Z"
        }
    }
}
```

### List Nodes
```http
GET /api/v1/comfyui/nodes
```

#### Response
```json
{
    "status": "success",
    "data": {
        "nodes": [
            {
                "id": "text_to_image",
                "name": "Text to Image",
                "description": "Generate image from text prompt",
                "inputs": [
                    {
                        "name": "prompt",
                        "type": "string",
                        "required": true
                    },
                    {
                        "name": "negative_prompt",
                        "type": "string",
                        "required": false
                    }
                ],
                "outputs": [
                    {
                        "name": "image",
                        "type": "image"
                    }
                ]
            }
        ]
    }
}
```

## Error Responses

### Workflow Not Found
```json
{
    "status": "error",
    "message": "Workflow not found",
    "errors": [
        {
            "code": "not_found",
            "message": "Workflow with id 1 not found"
        }
    ]
}
```

### Execution Error
```json
{
    "status": "error",
    "message": "Workflow execution failed",
    "errors": [
        {
            "code": "execution_error",
            "message": "Failed to generate image",
            "details": "Node error: Invalid prompt"
        }
    ]
}
```

## Notes
- All timestamps are in ISO 8601 format
- All endpoints require authentication
- Rate limiting applies to all endpoints
- Workflow execution may take several minutes
- Progress updates are available via WebSocket
- Generated images are stored temporarily
- Node configuration may vary based on ComfyUI version 