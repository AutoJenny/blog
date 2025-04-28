# Workflow API Documentation

This document provides a comprehensive reference for all workflow-related API endpoints.

## Workflow Status

### Get Workflow Status
`GET /api/v1/workflow/{slug}/status`

Returns the current workflow status for a post, including current stage, progress, and available transitions.

**Response Format:**
```json
{
  "current_stage": "string",
  "progress": {
    "completed_sub_stages": ["string"],
    "total_sub_stages": 0,
    "percentage": 0
  },
  "available_transitions": ["string"]
}
```

### Update Workflow Status
`POST /api/v1/workflow/{slug}/transition`

Transitions a post to a new workflow stage.

**Request Body:**
```json
{
  "target_stage": "string"
}
```

## Sub-Stage Management

### Get Sub-Stage Content
`GET /api/v1/workflow/{slug}/sub-stage/{sub_stage_id}`

Retrieves the content of a specific sub-stage.

**Response Format:**
```json
{
  "content": "string",
  "metadata": {
    "last_updated": "string",
    "status": "string"
  }
}
```

### Update Sub-Stage Content
`POST /api/v1/workflow/{slug}/sub-stage`

Updates the content of a sub-stage. All sub-stages are now editable asynchronously, allowing content to be saved in any order.

**Request Body:**
```json
{
  "post_workflow_stage_id": "integer",
  "sub_stage_id": "string",
  "content": "string"
}
```

**Response Format:**
```json
{
  "status": "success",
  "message": "Sub-stage updated successfully"
}
```

## Error Handling

All endpoints follow standard HTTP status codes:

- `200`: Success
- `400`: Bad Request (invalid parameters)
- `404`: Not Found (invalid slug or sub-stage)
- `500`: Internal Server Error

Error responses include a descriptive message:

```json
{
  "error": "string",
  "message": "string"
}
```

## Workflow Stage Initialization

When a new post is created, all workflow stages and sub-stages are initialized automatically. This enables:

1. Asynchronous editing of any stage/sub-stage
2. Progress tracking across all stages
3. Validation at transition points rather than during editing

## Deprecated Features

The following JSON-based workflow fields are deprecated and will be removed after migration is complete:
- `workflow_status`
- `workflow_data`
- `workflow_history`

Use the normalized SQL tables and API endpoints described above instead. 