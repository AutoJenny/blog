# Workflow API

## Overview
The Workflow API handles workflow state management and transitions between different stages of post creation.

## Endpoints

### Get Workflow State
```http
GET /api/v1/workflow/{post_id}/state
```

#### Response
```json
{
    "status": "success",
    "data": {
        "workflow": {
            "id": 1,
            "post_id": 1,
            "current_stage": "idea",
            "stages": [
                {
                    "id": "idea",
                    "name": "Idea Development",
                    "status": "completed",
                    "completed_at": "2024-03-20T10:00:00Z"
                },
                {
                    "id": "structure",
                    "name": "Structure Planning",
                    "status": "in_progress",
                    "started_at": "2024-03-20T10:00:00Z"
                },
                {
                    "id": "content",
                    "name": "Content Creation",
                    "status": "pending"
                },
                {
                    "id": "images",
                    "name": "Image Generation",
                    "status": "pending"
                },
                {
                    "id": "review",
                    "name": "Review & Edit",
                    "status": "pending"
                }
            ],
            "created_at": "2024-03-20T10:00:00Z",
            "updated_at": "2024-03-20T10:00:00Z"
        }
    }
}
```

### Transition Stage
```http
POST /api/v1/workflow/{post_id}/transition
```

#### Request Body
```json
{
    "stage": "structure",
    "action": "start"
}
```

#### Response
```json
{
    "status": "success",
    "data": {
        "workflow": {
            "id": 1,
            "post_id": 1,
            "current_stage": "structure",
            "stages": [
                {
                    "id": "idea",
                    "name": "Idea Development",
                    "status": "completed",
                    "completed_at": "2024-03-20T10:00:00Z"
                },
                {
                    "id": "structure",
                    "name": "Structure Planning",
                    "status": "in_progress",
                    "started_at": "2024-03-20T10:00:00Z"
                }
            ],
            "created_at": "2024-03-20T10:00:00Z",
            "updated_at": "2024-03-20T10:00:00Z"
        }
    }
}
```

### Get Stage Data
```http
GET /api/v1/workflow/{post_id}/stages/{stage_id}
```

#### Response
```json
{
    "status": "success",
    "data": {
        "stage": {
            "id": "idea",
            "name": "Idea Development",
            "status": "completed",
            "data": {
                "idea_seed": "Initial idea for the post",
                "summary": "Generated summary text",
                "facts": ["Fact 1", "Fact 2"]
            },
            "completed_at": "2024-03-20T10:00:00Z"
        }
    }
}
```

### Update Stage Data
```http
PUT /api/v1/workflow/{post_id}/stages/{stage_id}
```

#### Request Body
```json
{
    "data": {
        "idea_seed": "Updated idea for the post",
        "summary": "Updated summary text",
        "facts": ["Updated Fact 1", "Updated Fact 2"]
    }
}
```

#### Response
```json
{
    "status": "success",
    "data": {
        "stage": {
            "id": "idea",
            "name": "Idea Development",
            "status": "completed",
            "data": {
                "idea_seed": "Updated idea for the post",
                "summary": "Updated summary text",
                "facts": ["Updated Fact 1", "Updated Fact 2"]
            },
            "completed_at": "2024-03-20T10:00:00Z"
        }
    }
}
```

## Error Responses

### Invalid Transition
```json
{
    "status": "error",
    "message": "Invalid transition",
    "errors": [
        {
            "code": "invalid_transition",
            "message": "Cannot transition from 'idea' to 'content' without completing 'structure'"
        }
    ]
}
```

### Stage Not Found
```json
{
    "status": "error",
    "message": "Stage not found",
    "errors": [
        {
            "code": "not_found",
            "message": "Stage 'invalid_stage' not found"
        }
    ]
}
```

## Notes
- All timestamps are in ISO 8601 format
- All endpoints require authentication
- Rate limiting applies to all endpoints
- Stage transitions are validated against workflow rules
- Stage data is validated against schema
- Workflow state is persisted in database
- Stage completion triggers next stage automatically 