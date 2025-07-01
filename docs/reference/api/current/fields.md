# Field Mapping API Reference

## Overview

The field mapping system manages relationships between database fields and various parts of the application, including workflow stages, LLM actions, and UI components. These endpoints are core system endpoints used across multiple areas of the application.

## Usage Areas

1. **Settings Panel** (`/settings`)
   - Field mapping management interface
   - Stage/substage assignment
   - Order configuration

2. **Documentation** (`/docs/view/database/schema.md`)
   - Live field mapping display
   - Current configuration reference

3. **LLM Panel**
   - Field selection dropdowns
   - Input/output field mapping
   - Action configuration

4. **Workflow System**
   - Stage/substage field relationships
   - Content progression tracking
   - Field value persistence

## Endpoints

All field-related endpoints are now under the `/api/workflow/fields/` base path.

## Field Mapping Endpoints

### Get Field Mappings
- **URL**: `/api/workflow/fields/mappings`
- **Method**: `GET`
- **Description**: Retrieves all field mappings with stage and substage details
- **Response**:
  ```json
  [
    {
      "field_name": "string",
      "stage_id": "integer",
      "stage_name": "string",
      "substage_id": "integer",
      "substage_name": "string",
      "order_index": "integer"
    }
  ]
  ```
- **Status Codes**:
  - `200`: Success

### Update Field Mapping
- **URL**: `/api/workflow/fields/mappings`
- **Method**: `POST`
- **Description**: Updates field mapping order and associations
- **Request Body**:
  ```json
  {
    "id": "integer",
    "stage_id": "integer",
    "substage_id": "integer",
    "order_index": "integer"
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
  - `400`: Missing required fields

### Get Field Mapping UI
- **URL**: `/api/workflow/fields/mappings/ui`
- **Method**: `GET`
- **Description**: Renders field mapping management interface
- **Response**: HTML page
- **Status Codes**:
  - `200`: Success

## Post Field Endpoints

### Get Post Fields
- **URL**: `/api/workflow/posts/<post_id>/fields`
- **Method**: `GET`
- **Description**: Retrieves all fields for a post
- **URL Parameters**:
  - `post_id`: ID of the post
- **Response**:
  ```json
  {
    "fields": [
      {
        "name": "string",
        "value": "string",
        "stage": "string",
        "substage": "string"
      }
    ]
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `404`: Post not found

### Update Post Field
- **URL**: `/api/workflow/posts/<post_id>/fields/<field_name>`
- **Method**: `POST`
- **Description**: Updates a specific field for a post
- **URL Parameters**:
  - `post_id`: ID of the post
  - `field_name`: Name of the field
- **Request Body**:
  ```json
  {
    "value": "string"
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
  - `400`: Invalid field value
  - `404`: Field not found

## Stage Field Endpoints

### Get Stage Fields
- **URL**: `/api/workflow/stages/<stage_id>/fields`
- **Method**: `GET`
- **Description**: Retrieves all fields for a stage
- **URL Parameters**:
  - `stage_id`: ID of the stage
- **Response**:
  ```json
  {
    "fields": [
      {
        "name": "string",
        "type": "string",
        "required": "boolean",
        "order": "integer"
      }
    ]
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `404`: Stage not found

### Get Substage Fields
- **URL**: `/api/workflow/stages/<stage_id>/substages/<substage_id>/fields`
- **Method**: `GET`
- **Description**: Retrieves all fields for a substage
- **URL Parameters**:
  - `stage_id`: ID of the stage
  - `substage_id`: ID of the substage
- **Response**:
  ```json
  {
    "fields": [
      {
        "name": "string",
        "type": "string",
        "required": "boolean",
        "order": "integer"
      }
    ]
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `404`: Stage or substage not found

## Field Selection Endpoints

**CANONICAL POLICY: Field selection mappings are per-step only, never per-post.**

Field selection mappings determine which database field the output of a workflow step should be saved to. These mappings are global for all posts and stored in the step's configuration.

### Get Field Selection
- **URL**: `/api/workflow/steps/<step_id>/field_selection`
- **Method**: `GET`
- **Description**: Retrieves the field selection mapping for a workflow step
- **URL Parameters**:
  - `step_id`: ID of the workflow step
- **Response**:
  ```json
  {
    "success": true,
    "data": {
      "field": "string",
      "table": "string"
    }
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `404`: Step not found or no field selection mapping exists

### Save Field Selection
- **URL**: `/api/workflow/steps/<step_id>/field_selection`
- **Method**: `POST`
- **Description**: Saves the field selection mapping for a workflow step
- **URL Parameters**:
  - `step_id`: ID of the workflow step
- **Request Body**:
  ```json
  {
    "output_field": "string",
    "output_table": "string"
  }
  ```
- **Response**:
  ```json
  {
    "success": true,
    "message": "Field selection saved successfully"
  }
  ```
- **Status Codes**:
  - `200`: Success
  - `400`: Missing required fields
  - `404`: Step not found

**Note:** Field selection mappings are stored in `workflow_step_entity.config.settings.llm.user_output_mapping` and apply globally to all posts using this step.

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

## Database Schema

Field mappings are stored in the following tables:
- `workflow_field_mapping`: Maps fields to stages and substages
- `workflow_stage_entity`: Defines workflow stages
- `workflow_sub_stage_entity`: Defines workflow substages

The schema ensures referential integrity between fields, stages, and substages.

## JavaScript Integration

### API Configuration

```javascript
// static/js/config/api.js
const API_CONFIG = {
    BASE_URL: '/api/workflow',
    ENDPOINTS: {
        FIELDS: {
            MAPPINGS: '/fields/mappings',
            MAPPINGS_UI: '/fields/mappings/ui'
        }
    }
};
```

### Usage Example

```javascript
// Fetch field mappings
async function getFieldMappings() {
    const response = await fetch(
        `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.FIELDS.MAPPINGS}`
    );
    return await response.json();
}

// Update field mapping
async function updateFieldMapping(data) {
    const response = await fetch(
        `${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.FIELDS.MAPPINGS}`,
        {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(data)
        }
    );
    return await response.json();
}
```

## Best Practices

1. **Field Names**
   - Use snake_case for consistency
   - Keep names descriptive but concise
   - Follow existing naming patterns

2. **Order Management**
   - Keep order_index values sequential
   - Leave gaps for future insertions
   - Update in batches when reordering

3. **Stage/Substage Relationships**
   - Verify stage exists before assigning
   - Ensure substage belongs to stage
   - Maintain proper hierarchy

4. **Error Handling**
   - Always check response status
   - Handle errors gracefully
   - Display appropriate user messages

## Testing

1. **Basic Operations**
   ```bash
   # Get all mappings
   curl -X GET http://localhost:5000/api/workflow/fields/mappings

   # Update mapping
   curl -X POST http://localhost:5000/api/workflow/fields/mappings \
     -H "Content-Type: application/json" \
     -d '{"id": 1, "stage_id": 1, "substage_id": 1, "order_index": 1}'
   ```

2. **Error Cases**
   ```bash
   # Missing required field
   curl -X POST http://localhost:5000/api/workflow/fields/mappings \
     -H "Content-Type: application/json" \
     -d '{"id": 1}'

   # Invalid stage/substage
   curl -X POST http://localhost:5000/api/workflow/fields/mappings \
     -H "Content-Type: application/json" \
     -d '{"id": 1, "stage_id": 999, "substage_id": 999, "order_index": 1}'
   ```

## Related Documentation

- [Database Schema Reference](../../database/schema.md)
- [Field Mapping UI Guide](../../ui/field_mapping.md)
- [LLM Integration](../current/llm.md) 