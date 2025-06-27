# Workflow API Documentation

This document describes the API endpoints for the workflow system.

## LLM Processing

### Run LLM (Canonical Endpoint)

```http
POST /api/v1/workflow/run_llm/
```

This is the canonical endpoint for all LLM operations in the workflow system. All LLM requests should be directed here.

**Request Body:**
```json
{
  "post_id": "integer",     // The ID of the post being processed
  "stage": "string",        // The workflow stage (e.g., "planning")
  "substage": "string",     // The workflow substage (e.g., "idea")
  "step": "string"         // The workflow step (e.g., "initial")
}
```

**Response Format:**
```json
{
  "success": true,
  "result": "string"       // The LLM response text
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "string"        // Error message
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:5000/api/v1/workflow/run_llm/" \
  -H "Content-Type: application/json" \
  -d '{
    "post_id": 1,
    "stage": "planning",
    "substage": "idea",
    "step": "initial"
  }'
```

**Example Response:**
```json
{
  "success": true,
  "result": "Generated content from LLM..."
}
```

**Notes:**
- This endpoint replaces the deprecated `/workflow/api/v1/workflow/run_llm/` endpoint
- All LLM requests should use this endpoint for consistency and proper error handling
- The endpoint uses the configured LLM provider (default: Ollama with Mistral model)

### Get Workflow Stages

```http
GET /api/v1/workflow/stages/
```

Returns all workflow stages and their configuration.

**Response Format:**
```json
{
  "success": true,
  "stages": {
    "stage_name": {
      "substage_name": [
        {
          "name": "step_name",
          "config": {}
        }
      ]
    }
  }
}
```

**Example Response:**
```json
{
  "success": true,
  "stages": {
    "planning": {
      "idea": [
        {
          "name": "initial",
          "config": {
            "input_fields": ["idea_seed"],
            "output_fields": ["basic_idea"]
          }
        }
      ]
    }
  }
}
```

## Format Management

### Get Step Formats

```http
GET /api/v1/workflow/api/workflow/steps/{step_id}/formats
```

Returns all format templates associated with a workflow step.

### Get Step Post Format

```http
GET /api/v1/workflow/api/workflow/steps/{step_id}/formats/{post_id}
```

Returns the format template assigned to a specific post for a workflow step.

### Set Step Post Format

```http
PUT /api/v1/workflow/api/workflow/steps/{step_id}/formats/{post_id}
```

Assigns a format template to a specific post for a workflow step.

### Delete Step Post Format

```http
DELETE /api/v1/workflow/api/workflow/steps/{step_id}/formats/{post_id}
```

Removes the format template assignment for a specific post and workflow step.

### Set Step Default Format

```http
PUT /api/v1/workflow/api/workflow/steps/{step_id}/formats
```

Sets the default format template for a workflow step. 