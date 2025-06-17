# LLM-Actions Module: Implementation Mapping

## 1. Overview
This document catalogs all code, templates, JavaScript, backend logic, endpoints, and database tables involved in the LLM-actions UI (Inputs, Prompt, Settings, Outputs accordions). Sections, navigation, and site-wide layout are explicitly excluded.

---

## 2. Templates
- **Primary UI Template:**
  - `app/templates/workflow/_modular_llm_panels.html` (or similar)
    - Contains the markup for Inputs, Prompt, Settings, and Outputs accordions.
    - Used as an include in workflow substage templates (e.g., `planning/idea/index.html`).
- **Prompt Editor:**
  - Prompt fields and save button (see also `app/templates/workflow/_workflow_content.html` for prompt card logic).
- **Field Mapping/Config:**
  - Field dropdowns and mapping logic are defined in the template and populated by JS.

---

## 3. JavaScript
- **Main Workflow LLM JS:**
  - `app/static/js/workflow.js` (or `archive2/js_workflow/main.js`)
    - Handles DOMContentLoaded, fetches data, initializes UI, and registers event handlers.
  - `archive2/js_workflow/events.js`
    - Registers all event handlers for the accordions (input, output, action, run, save, etc).
  - `archive2/js_workflow/actions.js`
    - Handles execution of LLM actions and result processing.
  - `archive2/js_workflow/api.js`
    - Handles API calls for fetching actions, running LLM, updating fields, etc.
  - `archive2/js_workflow/render.js`
    - Renders dropdowns, prompt panels, and field values.
  - `archive2/js_workflow/llm_utils.js`
    - Utility functions for LLM provider status, error handling, etc.

---

## 4. Backend (Python)
- **API Endpoints:**
  - `app/api/llm.py` (or similar)
    - `/api/v1/llm/actions` (GET): List available LLM actions
    - `/api/v1/llm/actions/<action_id>/execute` (POST): Run LLM action
    - `/api/v1/llm/actions/<action_id>` (GET): Get action details (prompt, settings, etc)
    - `/api/v1/llm/ollama/status` (GET): Check provider status
    - `/api/v1/llm/ollama/start` (POST): Start provider service
    - `/api/v1/llm/prompts` (GET/POST): Manage prompt templates
    - `/api/v1/llm/field_mappings/<substage>` (GET): Get field mappings for substage
    - `/api/v1/post/<post_id>/development` (GET/PUT): Get/update post development fields
    - `/api/v1/llm/post_workflow_step_actions/<pws_id>` (PUT): Update workflow step action mapping
- **Services:**
  - `app/llm/services.py` (or similar)
    - LLMService: Handles prompt rendering, LLM request, and result logging.
    - Utility functions for modular prompt conversion, provider management, etc.

---

## 5. Database
- **Tables:**
  - `llm_action`: Defines available LLM actions (prompt, model, provider, input/output fields, etc)
  - `llm_prompt`: Stores prompt templates (text, JSON, system/task prompts)
  - `llm_provider`: LLM provider registry
  - `llm_model`: LLM model registry
  - `llm_interaction`: Logs LLM runs (input, output, action, timestamps)
  - `post_workflow_step_action`: Maps actions to workflow steps and fields
  - `post_development`: Stores post field values (input/output fields)
- **Relevant migrations:**
  - See `migrations/` and `backups/create_tables_pre_post_workflow_stage_fields.sql` for schema

---

## 6. Config/JSON
- **Prompt/Field Mapping:**
  - `app/workflow/config/planning_steps.json` (and similar):
    - Defines available fields, prompt files, and LLM settings for each substage.
  - `app/data/prompts/planning_idea_basic_idea.json` (and similar):
    - Contains system_prompt and task_prompt for each LLM action.

---

## 7. Data Flow
- **Inputs:**
  - User selects input field (dropdown populated from field mappings)
  - JS fetches and displays current value from `post_development`
- **Prompt:**
  - User can view/edit prompt (from prompt JSON or template)
  - JS/API updates prompt in `llm_prompt` table
- **Settings:**
  - User can view/edit LLM settings (model, temperature, etc)
  - JS/API updates settings in `llm_action` or config JSON
- **Outputs:**
  - User selects output field (dropdown)
  - When LLM is run, output is displayed and can be saved to `post_development`

---

## 8. Exclusions
- **Do NOT include:**
  - Navigation, header, footer, or site-wide layout
  - Sections/drag-and-drop UI
  - Any code not directly related to the four LLM accordions

---

## 9. File List (to collect for module)
- Templates:
  - `app/templates/workflow/_modular_llm_panels.html`
  - Any prompt editor partials
- JavaScript:
  - `app/static/js/workflow.js`
  - `archive2/js_workflow/events.js`
  - `archive2/js_workflow/actions.js`
  - `archive2/js_workflow/api.js`
  - `archive2/js_workflow/render.js`
  - `archive2/js_workflow/llm_utils.js`
- Backend:
  - `app/api/llm.py`
  - `app/llm/services.py`
- Config/JSON:
  - `app/workflow/config/planning_steps.json`
  - `app/data/prompts/planning_idea_basic_idea.json` (and similar)
- Database:
  - All relevant tables and migrations as above

---

## 10. Next Steps
- Review this mapping for completeness
- Confirm all files and endpoints are correct
- Begin modular extraction and rebuild 