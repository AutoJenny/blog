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
- Define expected structure of input data
- Validate data before processing
- Support [data:field_name] references
- Include type information and constraints

### Output Formats
- Define required structure of output data
- Provide validation rules for LLM output
- Support template references
- Include formatting instructions

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
GET /workflow/api/formats/
```

Returns all available format templates.

**Response Format:**
```json
[
  {
    "id": 1,
    "name": "Blog Section JSON",
    "format_type": "output",
    "format_spec": "{...}"
  }
]
```

### 2. Get Format Template
```http
GET /workflow/api/formats/{format_id}
```

Returns a specific format template.

### 3. Create Format Template
```http
POST /workflow/api/formats/
```

Creates a new format template.

**Request Body:**
```json
{
  "name": "string",
  "format_type": "string",
  "format_spec": "string"
}
```

### 4. Update Step Format Configuration
```http
POST /workflow/api/step_formats/{post_id}/{step_id}
```

Configures formats for a workflow step.

**Request Body:**
```json
{
  "input_format_id": "integer",
  "output_format_id": "integer"
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