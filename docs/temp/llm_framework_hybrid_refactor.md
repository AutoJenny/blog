# Hybrid LLM Framework Refactor & Extension: Implementation Plan

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
- [ ] Review the [Flask Project Engineering Rules](../frontend/dark_theme_styleguide.md) and `/docs` for conventions.
- [ ] Explore the existing LLM codebase in `blog/app/llm/` and models in `blog/app/models.py`.
- [ ] Review current workflow integration points (e.g., `/workflow/idea/`).

### **2. Data Model Enhancements**
- [ ] **Prompt Parts:**
  - [ ] Design and add a `LLMPromptPart` model (type, content, description, tags, order).
  - [ ] Migrate existing prompt templates to use modular parts (system, style, task, data).
- [ ] **Provider/Model Registry:**
  - [ ] Refactor `LLMConfig` to support multiple provider/model entries.
  - [ ] Add a `LLMProvider` and `LLMModel` model for registry and selection.
- [ ] **Message-Based Prompts:**
  - [ ] Extend prompt/template models to support message roles (system, user, assistant, etc.).
- [ ] **Migration:**
  - [ ] Document migration steps and data transfer for legacy prompts/configs.

### **3. Service Layer Refactor**
- [ ] Refactor `services.py` to:
  - [ ] Support message-based prompt assembly (list of messages with roles).
  - [ ] Allow dynamic provider/model selection per request.
  - [ ] Add adapters for new providers (future extensibility: e.g., image LLMs).
  - [ ] Ensure all LLM calls are parameterized and secure.
- [ ] Add comprehensive logging and error handling per style guide.

### **4. RESTful API Design**
- [ ] Design and implement RESTful endpoints for:
  - [ ] Providers and models (CRUD, list, select).
  - [ ] Prompt parts and templates (CRUD, assemble, preview).
  - [ ] LLM tasks (create, run, status, history, retry).
  - [ ] LLM result retrieval and workflow integration.
- [ ] Document all endpoints with Flasgger/OpenAPI.

### **5. UI/UX Modernization**
- [ ] **LLM Dashboard:**
  - [ ] Build a new `/llm/` dashboard for managing providers, models, prompt parts, templates, and tasks.
  - [ ] Use a modern, dark-themed, touch-friendly design (see [dark_theme_styleguide.md](../frontend/dark_theme_styleguide.md)).
  - [ ] **Ensure all specimen, sample, and hardcoded data is removed from the UI. All actions, prompts, and logs must be DB-driven only.**
- [ ] **Prompt Assembly UI:**
  - [ ] Allow users to create/edit prompt parts and assemble them into templates.
  - [ ] Support message-based prompt preview and editing.
- [ ] **Task Runner UI:**
  - [ ] Enable selection of template, model, config, and input data.
  - [ ] Show prompt preview and allow running the LLM task.
  - [ ] Display output, allow saving to workflow/post, and show history.
- [ ] **Workflow Integration:**
  - [ ] Add "Automate with LLM" buttons to workflow stages (e.g., `/workflow/idea/`).
  - [ ] Pre-fill relevant data and allow direct LLM task execution from workflow.

### **6. Testing & Validation**
- [ ] Write unit and integration tests for all new models, services, and endpoints (use pytest).
- [ ] Add UI tests for prompt assembly and task runner flows.
- [ ] Validate LLM integration with both local and commercial providers.

### **7. Documentation & Onboarding**
- [ ] Update `/docs` with:
  - [ ] Data model diagrams and explanations.
  - [ ] API endpoint documentation.
  - [ ] UI/UX usage guides and screenshots.
  - [ ] Example LLM tasks and workflow integrations.
- [ ] Add onboarding notes for new developers (where to find code, how to extend, style rules).

### **8. Deployment & Migration**
- [ ] Plan and execute migration of legacy LLM data to new models.
- [ ] Deploy incrementally, testing each major feature.
- [ ] Monitor logs and user feedback for issues.

---

## **Resources & References**
- **Code:** `blog/app/llm/`, `blog/app/models.py`, `blog/app/templates/llm/`
- **Docs:** `/docs/frontend/dark_theme_styleguide.md`, `/docs/temp/llm_framework_hybrid_refactor.md`
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