# Format Template Regularisation & Cleanup Plan

## Purpose
This plan details the steps required to regularise, clean up, and future-proof the format template system for workflow input/output formats, ensuring:
- All format templates are robust, unambiguous, and API-compliant
- Consistent and correct use of `llm_instructions`, `format_type`, and `fields`
- No mismatches between UI, API, and database
- Strict adherence to all conventions and endpoint contracts in `/docs`

---

## 1. **Audit and Inventory Existing Format Templates**
- List all entries in `workflow_format_template` (ID, name, description, fields, llm_instructions)
- Identify:
  - Duplicate or ambiguous names (e.g., multiple "Plain text (GB)")
  - Templates with missing or null `llm_instructions`
  - Templates with inconsistent or malformed `fields` JSONB
  - Templates missing a clear `format_type` (should be in `fields` as `type`)

## 2. **Standardise Template Structure**
- For each template, ensure:
  - **Unique, descriptive name** (no duplicates)
  - **Description** is present and meaningful
  - **fields** is always an array of objects, each with `name`, `type`, `required`, `description`
  - **format_type** is present and correct ("input", "output", or "bidirectional")
    - Should be stored in the top-level of the `fields` JSONB as `type` or as a top-level DB field if schema is updated
  - **llm_instructions** is non-null and clear (see /docs/workflow/formats.md for examples)

## 3. **Data Cleanup Actions**
- Remove or merge duplicate templates (preserving the most complete/accurate one)
- For any template with missing or unclear `llm_instructions`, draft and add a clear instruction (input: how to interpret, output: how to structure response)
- For any template with malformed `fields`, reformat to the canonical structure:
  ```json
  [
    { "name": "field1", "type": "string", "required": true, "description": "..." },
    ...
  ]
  ```
- For any template missing `format_type`, set it explicitly in the `fields` JSONB as `type` (or as a DB column if/when schema is updated)

## 4. **API and UI Consistency Checks**
- Verify that `/api/workflow/formats/templates` and `/api/workflow/formats/templates/<id>` return all required fields as per `/docs/reference/api/current/formats.md`:
  - `id`, `name`, `description`, `fields`, `format_type`, `llm_instructions`
- Ensure all create/update operations via API require and validate these fields
- Ensure the UI (settings/format_templates and workflow step config) displays both name and ID, and always shows/edit `llm_instructions`

## 5. **Documentation and Best Practices**
- Update `/docs/workflow/formats.md` and `/docs/reference/api/current/formats.md` with:
  - Canonical format template structure
  - Example input/output templates
  - Guidance for writing `llm_instructions`
  - Validation rules for `fields` and `format_type`
- Add a troubleshooting section for common format template issues

## 6. **Validation/Migration Script (Optional)**
- (If needed) Write a script to:
  - List all templates and flag any with missing/ambiguous data
  - Optionally auto-fix or prompt for manual correction
  - Validate that all templates conform to the canonical structure

## 7. **Testing**
- Use `/tests/test_format_integration.py` and `/tests/test_format_ui.py` to verify:
  - All templates are valid and usable in the UI
  - All API endpoints accept and return the correct structure
  - LLM instructions are surfaced and editable everywhere needed

---

## **Summary Table: Canonical Format Template Structure**
| Field            | Type     | Required | Description                                    |
|------------------|----------|----------|------------------------------------------------|
| id               | integer  | yes      | Unique template ID                             |
| name             | string   | yes      | Unique, descriptive name                       |
| description      | string   | yes      | Human-readable description                     |
| fields           | array    | yes      | Array of field definitions (see below)         |
| format_type      | string   | yes      | "input", "output", or "bidirectional"         |
| llm_instructions | string   | yes      | Clear LLM instructions for input/output format |

**Field Definition Structure:**
```json
{
  "name": "field_name",
  "type": "string|number|boolean|array|object",
  "required": true,
  "description": "..."
}
```

---

## **References**
- `/docs/workflow/formats.md`
- `/docs/reference/api/current/formats.md`
- `/docs/workflow/prompts.md`
- `/tests/test_format_integration.py`
- `/tests/test_format_ui.py`

---

**This plan is strictly limited to format template data and its robust, consistent use across the workflow system. No unrelated or incidental changes are included.** 