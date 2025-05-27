# LLM Action MVP Implementation Plan

> **NOTE:** This project uses PostgreSQL only. All database changes are made via direct SQL. No ORM or migration tools (Alembic, SQLAlchemy, SQLite) are used or supported.

## Purpose
Build a robust, transparent, and extensible MVP for an LLM-powered Action (e.g., "Generate Summary from idea_seed") within the /llm interface and workflow pages. This will serve as a test bed for sustainable, scalable LLM workflow development.

---

## 1. UI/UX Scaffold
- [ ] Add a special LLM Action button (class: `llm-action-btn`) between the idea_seed and Summary panels on `/workflow/idea/`.
- [ ] Button triggers the 'Generate Summary from idea_seed' Action.
- [ ] Action appears in `/llm/actions` list with key datapoints.
- [ ] Clicking the Action opens a detailed Action details view. *(REMOVED: Action Details view removed from /llm/actions as of 2025-05-27. Details and editing now handled elsewhere or pending redesign.)*
- [ ] Action details view includes: *(REMOVED: See above.)*
- [ ] Diagnostics are extensive but non-intrusive (collapsible, tooltips, etc.)
- [ ] Maintain site-wide style and dark theme.

---

## 2. Database Layer
- [ ] Add/extend tables for:
    - [ ] LLMAction (id, name, description, config, input_field, output_field, prompt_ids, model, status, etc.)
    - [ ] LLMActionRun (id, action_id, input_data, output_data, status, diagnostics, timestamps)
    - [ ] Link to existing LLMPrompt, LLMConfig, LLMModel tables

---

## 3. API Layer
- [ ] RESTful endpoints for:
    - [ ] List/create/update/delete LLM Actions
    - [ ] Run/test an Action (POST input, get output/diagnostics)
    - [ ] Retrieve Action run history and diagnostics
    - [ ] Fetch available prompts, models, configs for selectors
- [ ] Use Marshmallow schemas for validation/serialization.
- [ ] Document endpoints with Flasgger/OpenAPI.

---

## 4. Service Layer
- [ ] Service to assemble LLM message from selected fields/prompts/configs.
- [ ] Service to execute LLM call and capture diagnostics (timing, request/response, errors).
- [ ] Store Action run results and diagnostics in DB.
- [ ] Modular, extensible for future Action types and chaining.

---

## 5. Transparency & Diagnostics
- [ ] Log all steps of Action execution (input, prompt assembly, LLM request, response, errors).
- [ ] UI to view diagnostics per Action run (collapsible, downloadable, etc.).
- [ ] Error handling and user-friendly messages.

---

## 6. Testing & Validation
- [ ] Unit/integration tests for DB, API, service, and UI layers.
- [ ] Test Action end-to-end from workflow page and Action details view. *(REMOVED: Action Details view removed from /llm/actions as of 2025-05-27. Testing now handled elsewhere or pending redesign.)*
- [ ] Validate diagnostics and error reporting.

---

## 7. Documentation & Onboarding
- [ ] Update `/docs` with:
    - [ ] Data model diagrams
    - [ ] API docs
    - [ ] UI usage guide
    - [ ] Example Action flows and diagnostics
- [ ] Add onboarding notes for developers.

---

## 8. Sustainability & Extensibility
- [ ] Use modular, functional code per project style guide.
- [ ] Design for future Action chaining and workflow integration.
- [ ] Keep all code, migrations, and docs up to date. 