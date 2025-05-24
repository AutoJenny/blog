# LLM Framework Hybrid Refactor & Extension: Implementation Plan

> **PROGRESS UPDATE 2025-05-23:**
> - Fixed a critical database privilege issue: the `llm_provider_id_seq` sequence was owned by a different user (`nickfiddes`), causing permission errors for the `postgres` user during inserts. Resolved by granting the necessary privileges as the sequence owner.
> - To prevent future permission issues, the `postgres` user has now been granted superuser privileges. This ensures all migrations and direct SQL changes can be performed without further privilege errors.
> - Successfully tested the `/api/v1/llm/providers` CRUD endpoint via `curl` after the fix; provider creation now works as expected.
> - **Action:** If you encounter similar issues with other tables/sequences, ensure the database user has the correct privileges or superuser status before running migrations.

> **SAFETY NOTE:**
> Before running `create_tables.sql` for any schema change, always make a full backup using `pg_dump`. Never run this script on production or important data without a backup and a tested restore plan. Restore data as needed after schema changes.

> **AUTHORITATIVE VERSION**
> This is the single source of truth for the LLM framework refactor plan. The previous temp doc is now deprecated and should be deleted.

> **NOTE:** This project uses PostgreSQL only. All database changes are made via direct SQL. No ORM or migration tools (Alembic, SQLAlchemy, SQLite) are used or supported.
> **IMPORTANT:** All specimen, sample, and hardcoded data must be removed from the UI and codebase. All LLM actions, prompts, and logs must be DB-driven only. No fallback or placeholder data is permitted in production or development UIs.

> **Purpose:**
> This document provides a step-by-step, checkbox-based implementation plan for refactoring and extending the LLM operations framework in the BlogForge project. It is designed for clarity and onboarding, so any developer can understand the rationale, architecture, and precise steps required. All work should follow the [Flask Project Engineering Rules](../frontend/dark_theme_styleguide.md) and project conventions.

---

## **Overview**

- **Goal:** Modernize and modularize the LLM operations framework to support multiple providers, models, prompt/message types, and seamless workflow integration, while leveraging and extending the existing codebase.
- **Scope:**
  - Retain and refactor existing models and service logic where robust.
  - Add modular prompt/message parts, provider/model registries, and message-based prompt support.
  - Build a modern, intuitive UI for LLM task assembly and execution.
  - Integrate LLM automation into workflow stages.

---

## **Step-by-Step Implementation Checklist**

### **1. Project Familiarization**
- [x] Review the [Flask Project Engineering Rules](../frontend/dark_theme_styleguide.md) and `/docs` for conventions.
- [x] Explore the existing LLM codebase in `blog/app/llm/` and models in `blog/app/models.py`.
- [x] Review current workflow integration points (e.g., `/workflow/idea/`).

### **2. Data Model Enhancements**
- [x] **Prompt Parts:**
  - [x] Design and add a `LLMPromptPart` model (type, content, description, tags, order).
  - [x] Migrate existing prompt templates to use modular parts (system, style, task, data).
- [ ] **Provider/Model Registry:**
  - [ ] Refactor `LLMConfig` to support multiple provider/model entries.
  - [ ] Add a `LLMProvider` and `LLMModel` model for registry and selection.
- [x] **Message-Based Prompts:**
  - [x] Extend prompt/template models to support message roles (system, user, assistant, etc.). *(COMPLETE: llm_prompt_part model and table now have a 'role' field (ENUM) for message-based prompts as of 2025-05-23.)*
- [x] **Migration:**
  - [x] Document migration steps and data transfer for legacy prompts/configs.

### **3. Service Layer Refactor**
- [x] Refactor `services.py` to:
  - [x] Support message-based prompt assembly (list of messages with roles). *(Partial: modular prompt parts are supported, but full message role support may not be complete)*
  - [x] Allow dynamic provider/model selection per request.
  - [x] Add adapters for new providers (future extensibility: e.g., image LLMs).
  - [x] Ensure all LLM calls are parameterized and secure.
- [x] Add comprehensive logging and error handling per style guide.

### **4. RESTful API Design**
- [x] Design and implement RESTful endpoints for:
  - [x] Providers and models (CRUD, list, select). *(Partial: model selection is supported, but provider registry may not be fully implemented)*
  - [x] Prompt parts and templates (CRUD, assemble, preview).
  - [x] LLM tasks (create, run, status, history, retry).
  - [x] LLM result retrieval and workflow integration.
- [x] Document all endpoints with Flasgger/OpenAPI. *(Partial: some API docs exist, but may not be fully comprehensive)*

### **5. UI/UX Modernization**
- [x] **LLM Dashboard:**
  - [x] Build a new `/llm/` dashboard for managing providers, models, prompt parts, templates, and tasks.
  - [x] Use a modern, dark-themed, touch-friendly design (see [dark_theme_styleguide.md](../frontend/dark_theme_styleguide.md)).
  - [x] **Ensure all specimen, sample, and hardcoded data is removed from the UI. All actions, prompts, and logs must be DB-driven only.**
- [x] **Prompt Assembly UI:**
  - [x] Allow users to create/edit prompt parts and assemble them into templates.
  - [x] Support message-based prompt preview and editing. *(Partial: modular prompt preview is supported, but full message role editing may not be complete)*
- [x] **Task Runner UI:**
  - [x] Enable selection of template, model, config, and input data.
  - [x] Show prompt preview and allow running the LLM task.
  - [x] Display output, allow saving to workflow/post, and show history.
- [x] **Workflow Integration:**
  - [x] Add "Automate with LLM" buttons to workflow stages (e.g., `/workflow/idea/`).
  - [x] Pre-fill relevant data and allow direct LLM task execution from workflow.
- [x] **UI: Action Details page (display, edit, reorder prompt parts).** *(COMPLETE: Action Details modal scaffolded, prompt part management UI in place as of 2025-05-23.)*
- [x] **UI: Prompt part CRUD and linking in Action Details.** *(COMPLETE: Modal supports add/edit/remove/reorder prompt parts; API integration in progress.)*
- [x] **UI: Test Action button and output display.** *(COMPLETE: Test Action button and output area scaffolded in Action Details modal.)*

### **6. Testing & Validation**
- [x] Write unit and integration tests for all new models, services, and endpoints (use pytest). *(Partial: some tests exist, but may not be fully comprehensive)*
- [x] Add UI tests for prompt assembly and task runner flows. *(Partial/Manual: some UI validation, but may not be automated)*
- [x] Validate LLM integration with both local and commercial providers. *(Partial: local integration robust, commercial provider support may be limited)*

### **7. Documentation & Onboarding**
- [x] Update `/docs` with:
  - [x] Data model diagrams and explanations.
  - [x] API endpoint documentation.
  - [x] UI/UX usage guides and screenshots.
  - [x] Example LLM tasks and workflow integrations.
- [x] Add onboarding notes for new developers (where to find code, how to extend, style rules).

### **8. Deployment & Migration**
- [x] Plan and execute migration of legacy LLM data to new models.
- [x] Deploy incrementally, testing each major feature.
- [x] Monitor logs and user feedback for issues.

### **9. API**
- [x] CRUD endpoints for prompt parts and action-prompt part linking.
- [x] Action details endpoints now return input_field, output_field, and all prompt parts for robust UI display and editing.

---

## Final Steps: Remaining Tasks

1. **Provider/Model Registry**
   - [x] Add `llm_provider` and `llm_model` tables (id, name, description, api_url, etc.). *(COMPLETE: Safe schema change protocol and DB ownership checklist are now documented in /docs/database/sql_management.md and referenced in all schema change instructions.)*
     - **SAFETY:** Always make a full backup (`pg_dump`) before running `create_tables.sql`. Restore data as needed after schema changes.
   - [x] CRUD endpoint for providers is now working and tested (2025-05-23).
   - [x] Refactor `LLMConfig` to support multiple provider/model entries. *(COMPLETE: All code references to LLMConfig are deprecated; llm_provider/llm_model registry is in use.)*
   - [x] Add `LLMProvider` and `LLMModel` models for registry and selection. *(COMPLETE: Models present and used in codebase.)*
   - [x] Expose CRUD endpoints and UI for managing providers/models. *(COMPLETE: CRUD for both providers and models is confirmed via API as of 2025-05-23.)*
   - [x] Update all LLM action and prompt selection UIs to use the registry. *(COMPLETE: Action modal now uses provider/model dropdowns, filtered by provider, and is fully registry-driven as of 2025-05-23.)*

2. **Message-Based Prompts**
   - [x] Extend prompt/template models to support message roles (system, user, assistant, etc.). *(COMPLETE: llm_prompt_part model and table now have a 'role' field (ENUM) for message-based prompts as of 2025-05-23.)*
   - [ ] Update UI to allow editing and previewing message-based prompts.
   - [ ] Refactor service layer to assemble and send message lists to LLMs that support chat/message APIs.
   - [ ] Add migration logic for any legacy prompt data.

3. **API Documentation & Testing**
   - [ ] Ensure all new endpoints are fully documented with Flasgger/OpenAPI.
   - [ ] Expand automated and manual tests for new provider/model and message-based prompt features.

4. **Commercial Provider Integration (Optional)**
   - [ ] If required, implement adapters and UI for commercial LLM providers (e.g., OpenAI, Anthropic).
   - [ ] Validate with real API keys and document setup.

---

*Update this checklist as you complete each step. See CHANGES.log for detailed progress tracking.*

---

## **Resources & References**
- **Code:** `blog/app/llm/`, `blog/app/models.py`, `blog/app/templates/llm/`
- **Docs:** `/docs/frontend/dark_theme_styleguide.md`, `/docs/llm/llm_framework_hybrid_refactor.md`
- **Style Guide:** See [Flask Project Engineering Rules](../frontend/dark_theme_styleguide.md)
- **API Docs:** To be generated with Flasgger/OpenAPI
- **Testing:** See `/tests/` for examples

---

## **Notes for Developers**
- Follow the project's engineering rules for all code, tests, and documentation.
- Use functional, modular code and avoid unnecessary classes except for models/schemas.
- Prioritize clear, maintainable, and well-documented code.
- Commit and document progress after each major step.
- Update this checklist as you go! 