# Format System Guide
 
## Overview 
This guide documents the format specification system that works alongside the workflow prompt system. The format system ensures consistent data structures for both input and output across workflow stages.

---

## Format Template Structure

### Core Fields
- **name**: Unique identifier for the format template
- **description**: Human-readable description of the format's purpose
- **fields**: Array of field definitions with name, type, required status, and description
- **format_type**: Either "input", "output", or "bidirectional"
- **llm_instructions**: Clear instructions for the LLM on how to interpret input data or structure output responses

### LLM Instructions Field
The `llm_instructions` field provides explicit guidance to the LLM when processing data according to this format:

- **For Input Formats**: Instructions on how to interpret the input data structure
  - Example: "The input data will be provided in the following format."
- **For Output Formats**: Instructions on how to structure the response
  - Example: "You must return your response in the following format, with no commentary or introduction—just the JSON object."

These instructions are compiled into the final LLM prompt along with the system message and task prompt to ensure consistent data handling.

---

## API Endpoints

### Format Template Endpoints
- `GET /api/workflow/formats/templates` — List all format templates
- `POST /api/workflow/formats/templates` — Create a new format template
- `GET /api/workflow/formats/templates/<id>` — Get a specific format template
- `PUT /api/workflow/formats/templates/<id>` — Update a format template
- `DELETE /api/workflow/formats/templates/<id>` — Delete a format template

### Format Validation Endpoint
- `POST /api/workflow/formats/validate` — Validate data against a format specification
  - Request: `{ "fields": [...], "test_data": {...} }`
  - Response: `{ "valid": true/false, "errors": [...] }`

### Step/Post/Stage Format Configuration
- `GET /api/workflow/steps/<step_id>/formats` — Get format config for a workflow step
- `PUT /api/workflow/steps/<step_id>/formats` — Set format config for a workflow step
- `GET /api/workflow/stages/<stage_id>/format` — Get format config for a stage
- `POST /api/workflow/stages/<stage_id>/format` — Set format config for a stage
- `GET /api/workflow/posts/<post_id>/format` — Get format config for a post
- `POST /api/workflow/posts/<post_id>/format` — Set format config for a post

### Field Mapping
- `GET /api/workflow/fields/available` — List all available fields for mapping
- `POST /api/workflow/fields/mappings` — Set a field mapping

---

## Format Reference System

### Reference Syntax
- Use `[data:field_name]` in prompts or format fields to reference data from previous steps or context.
- Example: `"The previous result was: [data:previous_step_output]"`

### Reference Validation
- All `[data:field_name]` references are validated at runtime.
- If a reference is missing from the available data, a validation error is returned.
- Example error: `Reference 'missing_field' not found in available data.`

### Reference Resolution
- During workflow processing, references are replaced with the actual value from the data context.
- If a reference cannot be resolved, processing fails with a clear error message.

---

## UI Components

### Format Management UI
- Located at `/settings/format_templates`
- Features:
  - List, create, edit, and delete format templates
  - Preview format structure and test validation
  - Error and success feedback for all actions
  - Edit LLM instructions for each format template

### Format Configuration UI
- Located at `/settings/workflow_step_formats`
- Features:
  - Assign input/output formats to workflow steps
  - Preview format structure for each step
  - Test data validation for step formats
  - Visual feedback for format compliance

### Field Mapping UI
- Field selector dropdowns are format-aware
- Format compliance indicators (✓/⚠) shown in dropdowns
- Validation feedback shown when selecting or mapping fields

---

## Testing

### Integration Tests
- `/tests/test_format_integration.py` — End-to-end and workflow integration tests
- `/tests/test_format_ui.py` — Selenium-based UI tests for format management/configuration
- `/tests/api/test_format_endpoints.py` — API endpoint tests for all format operations

### Example Test Cases
- Format template CRUD (create, read, update, delete)
- Format validation (valid/invalid data, error handling)
- Reference resolution and error reporting
- Step/post/stage format configuration
- UI feedback and accessibility
- LLM instructions field validation and persistence

---

## Troubleshooting Guide

### Common Issues
- **Validation fails for correct data:**
  - Check that the format template fields match the data structure exactly.
  - Ensure all required fields are present and types are correct.
- **Reference not found error:**
  - Make sure all `[data:field_name]` references exist in the available data context.
  - Use the format validator to test references before running workflow steps.
- **UI not updating after format changes:**
  - Refresh the page or clear browser cache.
  - Check for JavaScript errors in the browser console.
- **API returns 400/404 errors:**
  - Verify endpoint paths and request payloads.
  - Check for missing or invalid fields in the request.
- **Performance issues with large formats:**
  - Limit the number of fields in a single format template.
  - Use array/object types judiciously for complex structures.
- **LLM instructions not being saved:**
  - Ensure the `llm_instructions` field is included in the request payload.
  - Check that the field is not empty or null.

### Where to Get Help
- Review this guide and the `/docs/temp/format_system_implementation_plan.md` for implementation details.
- Check `/tests/` for working test cases and usage examples.
- If issues persist, consult the engineering rules in the project root or ask for support.

---

## Format System Examples

### Example Format Template (JSON)
```json
{
  "name": "Title-description JSON",
  "description": "Structured JSON with two elements: title (string) and description (string).",
  "fields": [
    { "name": "title", "type": "string", "required": true, "description": "The main title" },
    { "name": "description", "type": "string", "required": true, "description": "A description of the title" }
  ],
  "format_type": "output",
  "llm_instructions": "You must return your response in the following format, with no commentary or introduction—just the JSON object."
}
```

### Example Reference in Prompt
```
"Summarize the previous section: [data:previous_section]"
```

---

## Best Practices

- Keep formats simple and focused
- Use clear field names and descriptions
- Include validation rules where needed
- Document format requirements clearly
- Use consistent naming for references
- Validate all data at API boundaries
- Test all format changes with the provided test suite
- Monitor validation and reference errors in logs
- Write clear, specific LLM instructions for each format
- Ensure LLM instructions are unambiguous about input/output expectations

## Format Components

### 1. Format Templates
Format templates define the structure and validation rules for data at each workflow step. They can be either input formats (defining expected input structure) or output formats (defining required output structure).

Example format template for blog section structure:
```json
{
  "name": "Blog Section Format",
  "description": "Format for structured blog section content",
  "fields": [
    { "name": "title", "type": "string", "required": true, "description": "Section title" },
    { "name": "content", "type": "string", "required": true, "description": "Main section content" },
    { "name": "key_points", "type": "array", "required": false, "description": "List of key points" }
  ],
  "format_type": "output",
  "llm_instructions": "Return a structured blog section with title, content, and optional key points. Use clear, engaging language suitable for the target audience."
}
```

## Format Structure

### Input Formats
Input formats define the expected structure of data before processing:

- **Type Information**: Clear specification of data types (string, number, boolean, object, array)
- **Field Requirements**: Which fields are required vs optional
- **Validation Rules**: Length limits, numeric ranges, pattern matching
- **Field References**: Support for [data:field_name] dynamic references
- **Documentation**: Clear descriptions of each field's purpose
- **LLM Instructions**: Guidance on how to interpret the input data structure

Example input format:
```json
{
  "name": "Blog Post Input",
  "description": "Input format for blog post creation",
  "fields": [
    { "name": "title", "type": "string", "required": true, "description": "The main title for this section" },
    { "name": "themes", "type": "array", "required": true, "description": "Key themes to cover" },
    { "name": "facts", "type": "array", "required": false, "description": "Supporting facts and data" }
  ],
  "format_type": "input",
  "llm_instructions": "The input data will be provided in the following format. Use this structure to guide your processing of the content."
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

## Integration with Workflow Steps

### Format Configuration
Each workflow step can have associated input and output formats. This configuration determines how data is structured and validated during step processing.

### Applying Formats
1. Input Validation
   - Before processing, input data is validated against the input format
   - Field references are resolved
   - Data is transformed if needed

2. Output Validation
   - LLM output is validated against the output format
   - Output is transformed to match required structure
   - Validation errors trigger reprocessing

## Best Practices

1. **Format Design**
   - Keep formats simple and focused
   - Use clear field names and descriptions
   - Include validation rules where needed
   - Document format requirements clearly

2. **Field References**
   - Use consistent naming patterns
   - Document reference sources
   - Validate reference existence
   - Handle missing references gracefully

3. **Validation**
   - Implement comprehensive validation
   - Provide clear error messages
   - Include validation suggestions
   - Handle edge cases appropriately

4. **Integration**
   - Test format compatibility
   - Validate data transformations
   - Monitor validation performance
   - Log validation failures 