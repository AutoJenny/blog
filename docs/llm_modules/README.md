# LLM-Actions Module: Coding Guidelines

## Purpose
This module implements the Inputs, Prompt, Settings, and Outputs accordions for LLM-powered workflow actions. It must:
- Exclude navigation, header/footer, and sections logic
- Work only with the existing database and API
- Be fully modular and self-contained

## Rules
- Only include code, templates, and JS directly related to the four LLM accordions
- No site-wide layout, navigation, or unrelated workflow code
- All endpoints and DB access must follow the project's direct SQL and Marshmallow validation rules
- Use the file list and mapping in LLM_ACTIONS_IMPLEMENTATION.md as your canonical reference
- Document all changes and update this README as needed

## Coding Style
- Follow the project's Flask, Marshmallow, and direct SQL conventions
- Use functional programming for logic, classes only for schemas and views
- Modularize JS and Python code by feature
- Use descriptive variable names and type hints
- Validate all input/output at the API boundary

## Testing
- Use curl and the browser to verify all endpoints and UI
- No changes are complete until tested and documented

---

See LLM_ACTIONS_IMPLEMENTATION.md for the full implementation mapping and checklist. 