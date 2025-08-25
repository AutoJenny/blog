# Format System Guide
 
## Overview 
This guide documents the format specification system that works alongside the workflow prompt system. The format system ensures consistent data structures for both input and output across workflow stages.

**Current Status (June 30, 2025):** The format system has been fully cleaned up and unified. All format configuration is now step-level only, with no post-specific overrides. Format templates are properly integrated into LLM prompts with complete schema and instruction data.

---

## Format Template Structure

### Core Fields
- **name**: Unique identifier for the format template
- **description**: Human-readable description of the format's purpose
- **fields**: JSON schema defining the data structure with type, required status, and description
- **llm_instructions**: Clear instructions for the LLM on how to interpret input data or structure output responses
- **created_at/updated_at**: Timestamps for tracking changes

### LLM Instructions Field
The `llm_instructions` field provides explicit guidance to the LLM when processing data according to this format:

- **For Input Formats**: Instructions on how to interpret the input data structure
  - Example: "The input will be provided as plain text, using only UK English spellings and idioms."
- **For Output Formats**: Instructions on how to structure the response
  - Example: "Return your response as a JSON object with title and description fields. Ensure both fields are present and contain appropriate content."

These instructions are compiled into the final LLM prompt along with the system message and task prompt to ensure consistent data handling.

---

## Step-Level Format Configuration

### Current System (June 2025)
- **Step-level only**: All format configuration is stored in `workflow_step_entity.default_input_format_id` and `default_output_format_id`
- **No post-specific overrides**: All posts use the same step-level format configuration
- **Unified structure**: Format templates appear once in diagnostic logs with complete data
- **Clean integration**: Format template data is properly integrated into LLM prompts

### Database Schema
```sql
-- Step-level format configuration
workflow_step_entity:
  - default_input_format_id (references workflow_format_template.id)
  - default_output_format_id (references workflow_format_template.id)

-- Format template data
workflow_format_template:
  - id, name, description
  - fields (JSON schema)
  - llm_instructions
  - created_at, updated_at
```

### Current Format Templates
- **ID 26:** Plain text (GB) - Input
- **ID 27:** Title-description JSON (Input)  
- **ID 28:** Title-description JSON (Output)
- **ID 38:** Plain text (GB) - Output
- **ID 39:** Plain text (GB) - Input

---

## API Endpoints

### Format Template Endpoints
- `GET /api/workflow/formats/templates` — List all format templates
- `POST /api/workflow/formats/templates` — Create a new format template
- `GET /api/workflow/formats/templates/<id>` — Get a specific format template
- `PUT /api/workflow/formats/templates/<id>` — Update a format template
- `DELETE /api/workflow/formats/templates/<id>` — Delete a format template

### Step Format Configuration (Step-Level Only)
- `GET /api/workflow/steps/<step_id>/formats` — Get step-level format configuration
- `PUT /api/workflow/steps/<step_id>/formats` — Set step-level format configuration

**Note:** Post-specific format configuration has been removed. All format configuration is now step-level only.

### Format Validation Endpoint
- `POST /api/workflow/formats/validate` — Validate data against a format specification
  - Request: `{ "fields": [...], "test_data": {...} }`
  - Response: `{ "valid": true/false, "errors": [...] }`

---

## Diagnostic Log Structure

### Current Log Format (June 2025)
The `workflow_diagnostic_db_fields.json` log now shows a clean, unified structure:

```json
{
  "metadata": { ... },
  "input_format_template": {
    "id": 39,
    "name": "Plain text (GB) - Input",
    "description": "A plain text input using UK English spellings and idioms.",
    "fields": { "type": "input", "schema": { ... } },
    "llm_instructions": "The input will be provided as plain text...",
    "created_at": "...",
    "updated_at": "..."
  },
  "output_format_template": { ... },
  "database_fields": {
    "post_info": { ... },
    "post_development": { ... },
    "workflow_config": { ... },
    "format_config": {
      "step_id": 41,
      "default_input_format_id": 39,
      "default_output_format_id": 28
    }
  }
}
```

**Key Features:**
- Format templates appear once at top level with complete data
- No duplication or redundant sections
- Complete schema and LLM instruction data included
- Clean, unified JSON structure

---

## UI Components

### Format Management UI
- Located at `/settings/format_templates`
- Features:
  - List, create, edit, and delete format templates
  - Preview format structure and test validation
  - Error and success feedback for all actions
  - Edit LLM instructions for each format template

### Step Format Configuration UI
- Located at `/settings/workflow_step_formats`
- Features:
  - Assign input/output formats to workflow steps (step-level only)
  - Preview format structure for each step
  - Test data validation for step formats
  - Visual feedback for format compliance

**Note:** All format configuration is now step-level only. No post-specific overrides are available.

---

## LLM Prompt Integration

### Current Prompt Structure (June 2025)
The format template system is being enhanced to integrate format instructions directly into LLM prompts:

**Desired Structure:**
```
CONTEXT:
[System prompt]

[Input format instructions from format template]

TASK:
[Task prompt]

[Input data]

RESPONSE:
[Output format instructions from format template]
```

### Next Steps
- Externalize prompt construction to dedicated script
- Integrate format template instructions into prompt sections
- Ensure proper input field mapping
- Validate prompt structure and format integration

---

## Testing

### Integration Tests
- `/tests/test_format_integration.py` — End-to-end and workflow integration tests
- `/tests/test_format_ui.py` — Selenium-based UI tests for format management/configuration
- `/tests/api/test_format_endpoints.py` — API endpoint tests for all format operations

### Example Test Cases
- Format template CRUD (create, read, update, delete)
- Format validation (valid/invalid data, error handling)
- Step-level format configuration
- UI feedback and accessibility
- LLM instructions field validation and persistence
- Diagnostic log structure validation

---

## Troubleshooting Guide

### Common Issues
- **Validation fails for correct data:**
  - Check that the format template fields match the data structure exactly.
  - Ensure all required fields are present and types are correct.
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
- **Format templates not appearing in logs:**
  - Verify step-level format configuration is set
  - Check that format templates exist in the database
  - Ensure diagnostic script is using step-level configuration

### Where to Get Help
- Review this guide and the `/docs/temp/format_template_system_status.md` for current status
- Check `/tests/` for working test cases and usage examples
- If issues persist, consult the engineering rules in the project root or ask for support

---

## Format System Examples

### Example Format Template (JSON)
```json
{
  "id": 27,
  "name": "Title-description JSON (Input)",
  "description": "Structured JSON with two elements: title (string) and description (string).",
  "fields": {
    "type": "input",
    "schema": {
      "type": "object",
      "required": ["title", "description"],
      "properties": {
        "title": {
          "type": "string",
          "description": "The main title"
        },
        "description": {
          "type": "string",
          "description": "A description of the title"
        }
      }
    }
  },
  "llm_instructions": "The input will be provided as a JSON object with title and description fields. Process this input according to the specified schema requirements.",
  "created_at": "2025-06-29 10:23:51.020087",
  "updated_at": "2025-06-30 11:31:07.802536"
}
```

### Example Step Configuration
```json
{
  "step_id": 41,
  "name": "Initial Concept",
  "default_input_format_id": 27,
  "default_output_format_id": 38
}
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
- Use step-level configuration only (no post-specific overrides)
- Maintain clean, unified log structures
- Include complete format template data in diagnostic logs

## Recent Changes (June 2025)

### Database Cleanup
- Removed all post-specific `workflow_step_format` rows
- Confirmed step-level format configuration is working correctly
- Verified format templates are properly stored in `workflow_step_entity`

### Backend Updates
- Updated `llm_processor.py` to fetch format configuration from step-level only
- Modified format template fetching to use `workflow_step_entity` table
- Confirmed frontend only calls step-level endpoint

### Log Structure Cleanup
- Eliminated all duplication in `workflow_diagnostic_db_fields.json`
- Format templates appear once at top level with complete data
- Clean, unified JSON structure with no redundant sections
- Complete format template data including schema, LLM instructions, descriptions

### Next Steps
- Externalize prompt construction to dedicated script
- Integrate format template instructions into LLM prompts
- Update all documentation to reflect current system
- Complete format template system integration 