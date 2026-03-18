# LLM Reference Stack for BlogForge

Welcome to the LLM (Large Language Model) documentation hub for BlogForge. This directory provides a comprehensive reference for the hybrid LLM framework, including architecture, implementation plans, diagrams, configuration, and onboarding resources.

## Purpose
- Centralize all LLM-related documentation, diagrams, and resources.
- Guide developers through the architecture, extension, and integration of LLM features in BlogForge.
- Serve as the onboarding entry point for new contributors to the LLM stack.

## Key Resources
- [Hybrid LLM Framework Refactor & Extension: Implementation Plan](../temp/llm_framework_hybrid_refactor.md)  ᐧ The main step-by-step checklist and architecture plan.
- [Dark Theme UI Styleguide](../frontend/dark_theme_styleguide.md) ᐧ UI/UX and engineering rules for all LLM-related UI.
- [LLM Service Refactor Notes](../llm_service_refactor.md) ᐧ Additional notes on LLM service design.

## Diagrams
- (Add diagrams here as .md or .png files as the architecture evolves)

## Configurations
- (Add config files or examples here as the stack is built)

## How to Use
- Start with the [Implementation Plan](../temp/llm_framework_hybrid_refactor.md) for a high-level overview and checklist.
- Follow the links above for style, API, and service details.
- Update this README and add new resources as the LLM stack evolves.

## LLM Admin Dashboard

A modern, unified admin interface is now available at `/llm/` in the web app. This dashboard provides access to:

- **Provider Management** (`/llm/providers`): Add, configure, and test LLM providers (OpenAI, Ollama, Anthropic, etc).
- **Model Management** (`/llm/models`): Manage available models, set defaults, and view model details.
- **Prompt Templates** (`/llm/prompts`): Create and edit reusable prompt templates for LLM actions. **Prompt templates and actions now use modular, ordered prompt parts (system, style, instructions, etc.), which are assembled into prompts/messages for LLMs. All backend and UI logic is now direct SQL (psycopg2), ORM-free, and robust.**
- **Actions & Tasks** (`/llm/actions`): Define, schedule, and manage LLM-powered actions and workflows. **Actions now support modular prompt parts: each action specifies input_field, output_field, and an ordered list of prompt parts (system, style, instructions, etc.). The backend assembles these for execution. All endpoints and UI are now direct SQL, ORM-free, and fully tested.**
- **Interaction Logs** (`/llm/logs`): View and audit all LLM interactions, results, and errors.
- **Settings** (`/llm/settings`): Configure global LLM settings, API keys, and advanced options.

See the diagrams and detailed docs in this folder for architecture, workflow, and extensibility details.

---

## LLM Admin Implementation & Extension Log

This section tracks the planned and in-progress implementation for each LLM admin sub-page. Update as features are scaffolded, extended, or completed.

**2025-05-22: All LLM admin sub-pages (Providers, Models, Prompts, Actions, Logs, Settings) are now scaffolded with modern, accessible, dark-themed UI, placeholder tables, modals, and forms. Backend/API integration is the next step. Modular prompt part support is being implemented in the backend and UI.**

### 1. Providers
- **UI:** Responsive table/grid, status badges, action buttons, add/edit/test modals (**scaffolded**)
- **Backend:** CRUD endpoints for providers (planned)
- **API Integration:** Test connection, set default, validation (planned)
- **Extension:** Real-time status, error reporting, provider-specific config fields

### 2. Models
- **UI:** Table/grid of models per provider, add/edit/remove, set default, enable/disable (**scaffolded**)
- **Backend:** CRUD endpoints for models (planned)
- **API Integration:** Fetch models from provider, validate config (planned)
- **Extension:** Model details, cost/context info, analytics

### 3. Prompt Templates
- **UI:** List, add, edit, delete, organize by type, versioning/history, preview (**scaffolded**)
- **Backend:** CRUD endpoints for prompt templates (planned)
- **API Integration:** Assign to actions/tasks, preview rendering (planned)
- **Extension:** Template variables, live preview, usage stats

### 4. Actions & Tasks
- **UI:** List, add, edit, delete, assign prompt/model/provider, schedule/trigger, status/history, run/test (**scaffolded**)
- **Backend:** CRUD endpoints for actions/tasks (planned)
- **API Integration:** Manual/batch run, workflow integration (planned)
  - **NOTE:** Workflow execution must use the `/actions/<id>/execute` endpoint (not `/test`). The payload must include `input_text` (the user input) and `post_id` for correct prompt substitution (e.g., `[data:FIELDNAME]`).
- **Extension:** Action chaining, advanced scheduling, audit trail

### 5. Interaction Logs
- **UI:** List/filter/search logs, view request/response, analytics, export (**scaffolded**)
- **Backend:** Log storage, query endpoints (planned)
- **API Integration:** Token/cost/latency analytics, error reporting (planned)
- **Extension:** Advanced filtering, export formats, alerting

### 6. Settings
- **UI:** Global settings, API keys, advanced options, security, integration (**scaffolded**)
- **Backend:** Settings storage, validation, audit (planned)
- **API Integration:** Webhooks, callback URLs, rate limits (planned)
- **Extension:** Role-based access, change history, environment profiles

---

*Update this log as you scaffold, extend, and implement each area of the LLM admin.*

---

*This directory is a living reference. Please keep it up to date as you build and extend the LLM features in BlogForge.*

- **Prompt Parts**: Modular prompt parts can be created, edited, and linked to actions. Each part has a type (system, style, instructions, etc.), content, and order. Actions can have any number of prompt parts, which are assembled in order for LLM execution. **All prompt part management is now direct SQL, ORM-free, and robust.**
- **API**: The API exposes CRUD for prompt parts and action-prompt part linking. Action details endpoints now return input_field, output_field, and all prompt parts for robust UI display and editing. **All endpoints are direct SQL, ORM-free, and tested.** 
  - **Workflow LLM execution:** Use `/actions/<id>/execute` with `{ input_text, post_id }` for workflow actions. Do not use `/test` for workflow runs.

## 2025-05-29 Update
- LLM actions now use `parse_tagged_prompt_to_messages` to build canonical prompts, ensuring all prompt elements (system, user, operation, data) are included as per [llm_prompt_structuring.md](./llm_prompt_structuring.md). See the changelog for details. 