# Format System Guide

## Overview 
This guide documents the format specification system that works alongside the workflow prompt system. The format system ensures consistent data structures for both input and output across workflow stages.

## Format Components

### 1. Format Templates
Format templates define the structure and validation rules for data at each workflow step. They can be either input formats (defining expected input structure) or output formats (defining required output structure).

Example format template for blog section structure:
```json
{
  "type": "object",
  "properties": {
    "title": {
      "type": "string",
      "description": "Section title"
    },
    "content": {
      "type": "string",
      "description": "Main section content"
    },
    "key_points": {
      "type": "array",
      "items": {
        "type": "string"
      },
      "description": "List of key points covered in the section"
    }
  },
  "required": ["title", "content"]
}
```

## Format Management

### Creating Format Templates
```bash
curl -s -X POST "http://localhost:5000/workflow/api/formats/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Blog Section JSON",
    "format_type": "output",
    "format_spec": "{\"type\":\"object\",\"properties\":{...}}"
  }'
```

### Updating Format Templates
```bash
curl -s -X PATCH "http://localhost:5000/workflow/api/formats/{format_id}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Name",
    "format_spec": "Updated spec..."
  }'
```

### Deleting Format Templates
```bash
curl -s -X DELETE "http://localhost:5000/workflow/api/formats/{format_id}"
```

## Format Structure

### Input Formats
Input formats define the expected structure of data before processing:

- **Type Information**: Clear specification of data types (string, number, boolean, object, array)
- **Field Requirements**: Which fields are required vs optional
- **Validation Rules**: Length limits, numeric ranges, pattern matching
- **Field References**: Support for [data:field_name] dynamic references
- **Documentation**: Clear descriptions of each field's purpose

Example input format:
```json
{
  "type": "object",
  "properties": {
    "title": {
      "type": "string",
      "description": "The main title for this section",
      "minLength": 10,
      "maxLength": 100
    },
    "keywords": {
      "type": "array",
      "description": "Key topics to cover",
      "items": {
        "type": "string"
      },
      "minItems": 1,
      "maxItems": 5
    },
    "reference_data": {
      "type": "string",
      "description": "Reference content from previous step",
      "pattern": "^\\[data:[a-z_]+\\]$"
    }
  },
  "required": ["title", "keywords"]
}
```

### Output Formats
Output formats define the required structure for processed results:

- **Strict Structure**: Exact specification of expected output fields
- **Type Enforcement**: Strong typing for consistent output
- **Nested Objects**: Support for complex data structures
- **Array Handling**: Clear specification of list structures
- **Format Instructions**: Additional formatting requirements

Example output format:
```json
{
  "type": "object",
  "properties": {
    "sections": {
      "type": "array",
      "description": "Generated content sections",
      "items": {
        "type": "object",
        "properties": {
          "heading": {
            "type": "string",
            "description": "Section heading"
          },
          "content": {
            "type": "string",
            "description": "Main content",
            "minLength": 100
          },
          "key_points": {
            "type": "array",
            "description": "Key takeaways",
            "items": {
              "type": "string"
            },
            "minItems": 2
          }
        },
        "required": ["heading", "content", "key_points"]
      },
      "minItems": 1
    },
    "summary": {
      "type": "string",
      "description": "Brief overview of all sections",
      "maxLength": 500
    }
  },
  "required": ["sections", "summary"]
}
```

### Format Validation
The format system uses JSON Schema Draft 7 for validation:

1. **Type Validation**
   - Ensures correct data types
   - Validates nested structures
   - Checks array contents

2. **Constraint Validation**
   - String lengths (minLength, maxLength)
   - Numeric ranges (minimum, maximum)
   - Array sizes (minItems, maxItems)
   - Pattern matching (regex patterns)

3. **Structural Validation**
   - Required fields presence
   - Object property names
   - Array item formats

4. **Error Reporting**
   - Clear error messages
   - Field path identification
   - Validation suggestions

## Database Schema

### llm_format_template Table
```sql
CREATE TABLE llm_format_template (
    id SERIAL PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    format_type VARCHAR(32) NOT NULL, -- 'input' or 'output'
    format_spec TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### workflow_step_format Table
```sql
CREATE TABLE workflow_step_format (
    id SERIAL PRIMARY KEY,
    step_id INTEGER REFERENCES workflow_step_entity(id),
    post_id INTEGER REFERENCES post(id),
    input_format_id INTEGER REFERENCES llm_format_template(id),
    output_format_id INTEGER REFERENCES llm_format_template(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Integration with Workflow Steps

### Format Configuration
Each workflow step can have associated input and output formats that are persisted in the `workflow_step_format` table. This configuration determines how data is structured and validated during step processing.

### Applying Formats
1. Input Validation
   - Before processing, input data is validated against the input format
   - Field references are resolved
   - Data is transformed if needed

2. Output Validation
   - LLM output is validated against the output format
   - Output is transformed to match required structure
   - Validation errors trigger reprocessing

## API Endpoints

### 1. List Format Templates
```http
GET /api/formats/templates
```

Returns all available format templates.

**Response Format:**
```json
[
  {
    "id": 1,
    "name": "Blog Section JSON",
    "format_type": "output",
    "format_spec": "{...}",
    "created_at": "2025-06-26T12:00:00Z",
    "updated_at": "2025-06-26T12:00:00Z"
  }
]
```

### 2. Get Format Template
```http
GET /api/formats/templates/{template_id}
```

Returns a specific format template.

**Response Format:**
```json
{
  "id": 1,
  "name": "Blog Section JSON",
  "format_type": "output",
  "format_spec": "{...}",
  "created_at": "2025-06-26T12:00:00Z",
  "updated_at": "2025-06-26T12:00:00Z"
}
```

### 3. Create Format Template
```http
POST /api/formats/templates
```

Creates a new format template.

**Request Body:**
```json
{
  "name": "string",
  "format_type": "input|output",
  "format_spec": "string (valid JSON Schema)"
}
```

**Response Format:**
```json
{
  "id": 1,
  "name": "string",
  "format_type": "input|output",
  "format_spec": "string",
  "created_at": "2025-06-26T12:00:00Z",
  "updated_at": "2025-06-26T12:00:00Z"
}
```

### 4. Update Format Template
```http
PATCH /api/formats/templates/{template_id}
```

Updates a format template. All fields are optional.

**Request Body:**
```json
{
  "name": "string",
  "format_type": "input|output",
  "format_spec": "string (valid JSON Schema)"
}
```

**Response Format:**
```json
{
  "id": 1,
  "name": "string",
  "format_type": "input|output",
  "format_spec": "string",
  "created_at": "2025-06-26T12:00:00Z",
  "updated_at": "2025-06-26T12:00:00Z"
}
```

### 5. Delete Format Template
```http
DELETE /api/formats/templates/{template_id}
```

Deletes a format template.

**Response:**
- Status: 204 No Content
- Body: Empty

### 6. Validate Format
```http
POST /api/formats/validate
```

Validates test data against a format specification.

**Request Body:**
```json
{
  "format_spec": "string (valid JSON Schema)",
  "test_data": "any (data to validate)"
}
```

**Response Format:**
```json
{
  "valid": true|false,
  "errors": [
    "field_path: error message"
  ]
}
```

**Example Request:**
```bash
curl -X POST "http://localhost:5000/api/formats/validate" \
  -H "Content-Type: application/json" \
  -d '{
    "format_spec": "{\"type\":\"object\",\"properties\":{\"test\":{\"type\":\"string\"}}}",
    "test_data": {"test": "value"}
  }'
```

**Example Response (Valid):**
```json
{
  "valid": true,
  "errors": []
}
```

**Example Response (Invalid):**
```json
{
  "valid": false,
  "errors": [
    "test: 123 is not of type 'string'"
  ]
}
```

## Best Practices

1. Format Design
   - Keep formats simple and focused
   - Use clear property names
   - Include descriptive documentation
   - Consider reusability

2. Validation Rules
   - Define clear type constraints
   - Include minimum/maximum values where appropriate
   - Specify required fields
   - Add helpful error messages

3. Integration
   - Maintain consistency with field mappings
   - Consider format compatibility between steps
   - Plan for format evolution
   - Document format relationships

4. Error Handling
   - Provide clear validation error messages
   - Include recovery suggestions
   - Log format validation failures
   - Monitor format usage

## Testing

### Format Template Testing
```bash
# Create format template
curl -s -X POST "http://localhost:5000/workflow/api/formats/" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Format",
    "format_type": "output",
    "format_spec": "{\"type\":\"object\",\"properties\":{...}}"
  }'

# Verify format template
curl -s "http://localhost:5000/workflow/api/formats/1" | python3 -m json.tool
```

### Step Format Configuration Testing
```bash
# Configure step formats
curl -s -X POST "http://localhost:5000/workflow/api/step_formats/22/41" \
  -H "Content-Type: application/json" \
  -d '{
    "input_format_id": 1,
    "output_format_id": 2
  }'

# Verify configuration
curl -s "http://localhost:5000/workflow/api/step_formats/22/41" | python3 -m json.tool
```

## Common Issues

1. Format Validation Errors
   - Check format specification syntax
   - Verify field references exist
   - Ensure data types match
   - Check for missing required fields

2. Configuration Issues
   - Verify format template IDs exist
   - Check step and post IDs
   - Confirm format type compatibility
   - Validate database constraints

3. Integration Problems
   - Check format compatibility between steps
   - Verify field mapping alignment
   - Test format transformations
   - Monitor performance impact

## Future Extensions

1. Advanced Format Features
   - Custom validation functions
   - Format inheritance
   - Conditional formatting
   - Format versioning

2. UI Improvements
   - Format template editor
   - Visual format designer
   - Format testing tools
   - Format documentation viewer

3. Integration Enhancements
   - Format migration tools
   - Bulk format updates
   - Format analytics
   - Format optimization suggestions

## Deployment

### Pre-deployment Checklist
1. Database backup
   ```bash
   pg_dump -U nickfiddes blog > blog_backup_YYYYMMDD_pre_format_system.sql
   ```

2. Verify migrations
   - 20250608_create_llm_format_template.sql
   - 20250608_create_workflow_step_format.sql
   - Ensure proper table ownership (nickfiddes)
   - Check index creation

3. Test environment verification
   - Format template CRUD operations
   - Workflow step format configuration
   - Format validation
   - UI functionality

### Deployment Steps
1. Stop application
   ```bash
   ./scripts/dev/restart_flask_dev.sh stop
   ```

2. Apply migrations
   ```bash
   psql -U nickfiddes -d blog -f migrations/20250608_create_llm_format_template.sql
   psql -U nickfiddes -d blog -f migrations/20250608_create_workflow_step_format.sql
   ```

3. Start application
   ```bash
   ./scripts/dev/restart_flask_dev.sh start
   ```

4. Verify deployment
   - Check table creation
   - Test format template creation
   - Test workflow step format configuration
   - Validate UI functionality

### Rollback Plan
If issues occur during deployment:

1. Stop application
   ```bash
   ./scripts/dev/restart_flask_dev.sh stop
   ```

2. Restore from backup
   ```bash
   dropdb -U nickfiddes blog
   createdb -U nickfiddes blog
   psql -U nickfiddes -d blog -f blog_backup_YYYYMMDD_pre_format_system.sql
   ```

3. Start application
   ```bash
   ./scripts/dev/restart_flask_dev.sh start
   ```

## Monitoring

### Health Checks
- Format template validation
- Workflow step format configuration
- Database table status
- API endpoint responses

### Error Tracking
- Format validation errors
- Configuration issues
- API errors
- UI feedback

## Maintenance

### Backup Schedule
- Daily database backups
- Backup verification
- Retention policy: 14 days

### Format Updates
- Version control for format templates
- Backward compatibility checks
- Format migration process
- Update documentation

## Security

### Data Validation
- Input sanitization
- JSON schema validation
- Error handling
- Access control

### Permissions
- Format template management
- Workflow configuration
- API access control
- UI restrictions 