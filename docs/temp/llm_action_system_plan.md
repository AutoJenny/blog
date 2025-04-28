# LLM Action System: Project Plan

## Overview
A robust, transparent system for defining, editing, and running LLM-powered content generation actions on blog post fields. Actions are global templates, user-editable, and support multiple LLMs and prompt templates. The UI integrates process widgets and modals for configuration and history.

---

## Requirements & Design Decisions
- [ ] **Actions are global templates** (reusable for all posts)
- [ ] **Each destination field has one action** (but can be changed/edited)
- [ ] **User-editable on the fly** (add/edit from UI)
- [x] **Multiple LLMs supported** (default: local Ollama)
- [ ] **Prompt templates** (selectable, editable as actions)
- [ ] **Store LLM output history as actions** (for traceability)
- [ ] **Process widget for all fields** (shows 'Add LLM widget' if none exists)
- [ ] **All action fields editable in modal** (source, prompt, destination, model, etc.)
- [ ] **Log all LLM actions** (for audit/debugging, as actions)
- [ ] **Show last generation status/result in UI**

---

## Project Steps

### 1. Data Model & Backend
- [ ] Design `LLMAction` model (fields: id, source_field, prompt_template, destination_field, llm_model, temperature, etc.)
- [ ] Design `LLMActionHistory` model (fields: id, action_id, post_id, input, output, status, timestamp, user, etc.)
- [x] Create migration scripts for new tables (for LLMConfig, LLMPrompt, LLMInteraction)
- [ ] Implement backend CRUD API for actions (list, create, edit, delete)
- [ ] Implement backend API for running an action (trigger LLM, update destination, log history)

### 2. LLM Integration
- [x] Integrate with Ollama (default)
- [x] Integrate with OpenAI
- [ ] Design prompt template system (predefined + custom, as actions)
- [ ] Support for future LLMs (OpenAI, etc. extensible)

### 3. Frontend UI/UX
- [ ] Add process widget below each destination field
    - [ ] If action exists: show [Generate] from <source field> + edit icon
    - [ ] If not: show [Add LLM widget] button
- [ ] Modal for editing/creating actions
    - [ ] Dropdowns for source, destination, LLM, prompt template
    - [ ] Free-text for custom prompt
    - [ ] Save/cancel actions
- [ ] Show last generation status/result (success, error, timestamp)
- [ ] Display LLM action history (optional: expandable/log view)

> **Note:** As of [2025-04-28], backend LLM config, prompt, and logging are implemented, but the LLM Action System (global, reusable, per-field actions, with history and UI widgets) is NOT implemented—neither in the backend nor the frontend.

### 4. Robustness & Transparency
- [ ] Log all LLM actions (backend, as actions)
- [ ] Show audit/debug info in UI (last run, errors)
- [ ] Handle errors gracefully (UI and backend)

### 5. Documentation & Testing
- [ ] Document the system in `/docs` (usage, API, extensibility)
- [ ] Add tests for backend logic and API
- [ ] Add tests for frontend components

---

## Notes
- All actions are global, but run in the context of a specific post. (NOT IMPLEMENTED)
- Only one action per destination field, but can be edited/replaced. (NOT IMPLEMENTED)
- Prompt templates can be managed separately for reuse. (NOT IMPLEMENTED as actions)
- LLMActionHistory enables full traceability and debugging. (NOT IMPLEMENTED)
- UI/UX should be clean, accessible, and non-intrusive.

---

## Next Step
**Review this plan. Once approved, implementation will proceed step by step, checking off each item.** 