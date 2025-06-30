# Modularisation Plan: workflow_modular_llm.js

**Goal:** Refactor `app/static/js/workflow_modular_llm.js` into smaller, focused ES6 modules for maintainability, safety, and robustness. Each step will be committed separately. This checklist ensures the process can be resumed at any point.

---

## Checklist

- [x] 1. **Preparation**
    - [x] Ensure latest working state is committed to git.
    - [x] Create this plan as `/docs/temp/modularisation.md`.
    - [x] Create `/static/js/workflow/` directory for new modules.

- [ ] 2. **Extract API Utilities**
    - [x] Create `workflow/api.js` for all backend fetch/save functions:
        - fetchFieldMappings
        - fetchPostDevelopment
        - updatePostDevelopmentField
        - fetchLLMActions
        - fetchLLMActionDetails
        - runLLMAction
        - fetchPostSubstageAction
        - savePostSubstageAction
        - fetchLastPostSubstageAction
    - [x] Export all as named functions.
    - [x] Update main script to import and use these.
    - [ ] Commit: "refactor(workflow): extract API utilities to workflow/api.js"

- [x] 3. **Extract State Management**
    - [x] Create `workflow/state.js` for state variables and initialization logic:
        - postId, substage, workflowRoot, etc.
        - fieldMappings, postDev, llmActions, actionDetails, etc.
        - isInitializing, lastActionOutput, etc.
    - [ ] Export state as a singleton or named exports.
    - [x] Update main script to import and use state.
    - [x] Commit: "refactor(workflow): extract state management to workflow/state.js"

- [x] 4. **Extract UI Rendering**
    - [x] Create `workflow/render.js` for all DOM rendering functions:
        - renderFieldDropdown
        - renderActionDropdown
        - renderPostDevFields
        - showActionDetails
        - updatePanelVisibility
    - [x] Export all as named functions.
    - [x] Update main script to import and use these.
    - [x] Commit: "refactor(workflow): extract UI rendering to workflow/render.js"

- [x] 5. **Extract Event Handlers**
    - [x] Create `workflow/events.js` for all event listener registration:
        - inputFieldSelect, outputFieldSelect, actionSelect, runActionBtn, saveOutputBtn
    - [x] Export a function to register all events.
    - [x] Update main script to import and call this.
    - [x] Commit: "refactor(workflow): extract event handlers to workflow/events.js"

- [x] 6. **Extract Action Execution Logic**
    - [x] Create `workflow/actions.js` for LLM action execution and result handling.
    - [x] Export as named function(s).
    - [x] Update main script and events to use this.
    - [x] Commit: "refactor(workflow): extract action execution to workflow/actions.js"

- [x] 7. **Extract Persistence Logic**
    - [x] Create `workflow/persistence.js` for settings persistence, auto-cloning, and defaults.
    - [x] Export as named function(s).
    - [x] Update main script and events to use this.
    - [x] Commit: "refactor(workflow): extract persistence logic to workflow/persistence.js"

- [x] 8. **Create Main Entry Point**
    - [x] Create `workflow/main.js` as the entry point.
    - [x] Import all modules and initialize the workflow.
    - [x] Replace script tag in templates to use `workflow/main.js`.
    - [x] Commit: "refactor(workflow): add main entry point and wire up modules"

- [ ] 9. **Testing and Cleanup**
    - [x] Test all workflow substages in the browser for regression.
    - [x] Remove unused code from the original script.
    - [x] Update documentation if needed.
    - [x] Commit: "refactor(workflow): cleanup and finalize modularisation"

---

**If interrupted:**
- Resume from the last unchecked step.
- Each step is independent and can be committed separately.
- If a step fails, roll back to the previous commit and retry. 