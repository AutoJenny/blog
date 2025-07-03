# Mini-Project: Section-Level LLM Actions for Writing Phase

## Purpose
Enable robust, intuitive LLM actions that operate at the section level in the Writing phase, allowing users to select one, several, or all sections for LLM processing, and to specify input/output fields from both post-wide and section-level data.

---

## Guiding Principles
- **ABSOLUTELY NO CODE OUTSIDE THE EXPLICIT TASK IS TO BE CHANGED WITHOUT USER CONSENT.**
- **Each stage must be fully researched, planned, implemented, tested, and committed before moving to the next.**
- **If any risk to existing functionality is detected, STOP and consult before proceeding.**
- **Document all changes and update the changes log after each commit.**

---

## Staged Implementation Plan

### 1. Stage Selection Mechanism (UI)
- **Goal:** Allow users to select one, several, or all sections for LLM actions (e.g., via checkboxes in section accordions).
- **Tasks:**
  - Research best UI patterns for multi-section selection.
  - Plan minimal, non-destructive integration with current UI.
  - Implement selection mechanism.
  - Test thoroughly to ensure no impact on existing LLM actions.
  - **DO NOT CHANGE ANY OTHER CODE.**
  - Commit and document.

### 2. Input/Output Dropdowns Enhancement
- **Goal:** Enable dropdowns to select both post-wide and section-level fields, contextually aware of current selection.
- **Tasks:**
  - Research current dropdown implementation and field sources.
  - Plan how to add section fields without breaking post-level logic.
  - Implement grouped dropdowns (post fields, section fields).
  - Test for both post-level and section-level LLM actions.
  - **DO NOT CHANGE ANY OTHER CODE.**
  - Commit and document.

### 3. API Payload & Backend Adaptation
- **Goal:** Update API to accept per-section field mappings and process LLM actions accordingly.
- **Tasks:**
  - Research current API payload structure and backend logic.
  - Plan changes to support section-level field mapping.
  - Implement backend changes with full validation and error handling.
  - Test with various section/post field combinations.
  - **DO NOT CHANGE ANY OTHER CODE.**
  - Commit and document.

### 4. Prompt Construction Logic
- **Goal:** Ensure prompt templates can flexibly combine post and section data for each LLM call.
- **Tasks:**
  - Research current prompt construction.
  - Plan for robust, RORO-style prompt building.
  - Implement and test with single and multi-section requests.
  - **DO NOT CHANGE ANY OTHER CODE.**
  - Commit and document.

### 5. Output Handling & UI Feedback
- **Goal:** Display LLM results inline in the correct section(s), with clear feedback on processing status.
- **Tasks:**
  - Research current result rendering.
  - Plan for per-section result display.
  - Implement and test for all selection scenarios.
  - **DO NOT CHANGE ANY OTHER CODE.**
  - Commit and document.

### 6. Documentation & User Guidance
- **Goal:** Update user and developer documentation to reflect new section-level LLM action flow.
- **Tasks:**
  - Document new UI, API, and backend logic.
  - Add strong warnings about not changing unrelated code.
  - Commit and document.

---

## Final Reminders (Repeat at Every Stage)
- **NEVER change or delete code outside the explicit task.**
- **ALWAYS seek consent before touching any other part of the codebase.**
- **Test thoroughly and document every change.**
- **If in doubt, STOP and ask.**

---

## [ADDED] Section Selection Mechanism: UI-Only Implementation Details

**Scope:**
- This stage is strictly limited to front-end UI changes for the Writing stage (green area/sections panel).
- No backend or Planning stage code/templates are to be changed.

**Implementation Plan:**
- Add a checkbox to each section card/accordion in the Writing stage sections panel (green area).
- Add a "Select All" checkbox at the top of the panel for convenience.
- By default, all checkboxes are checked (all sections selected for LLM actions).
- User can uncheck to exclude any section from LLM actions.
- When the LLM action is triggered, only the checked section IDs will be collected and (in a future stage) sent to the backend.
- Provide clear visual feedback for selected sections (e.g., highlight, count).
- All changes must be isolated to the Writing stage block in `app/templates/workflow/index.html` and the associated JS module (`app/static/js/workflow/template_view.js`).
- If a new JS module is needed for selection logic, it must only be imported/used in the Writing stage.
- **Absolutely no changes to Planning stage code, templates, or logic.**

**Mockup:**

```
[Select All] [ ]
[Section 1] [x] Title/Desc
[Section 2] [x] Title/Desc
[Section 3] [x] Title/Desc
[LLM Action Button]
```

**Reminders:**
- Do not touch Planning stage code or templates.
- Do not implement backend or API changes at this stage.
- Test thoroughly after each UI change.
- Document every step and update the changes log.

---

## [ADDED] Writing Stage LLM-Actions Framework: Directory, File Structure, and Integration Plan

### 1. Overview
- The Writing stage LLM-actions system will be implemented as a new, independent module.
- All Planning stage (post-level) code, templates, and endpoints will remain untouched and firewalled.
- The new system will provide section-centric LLM actions, with the same (purple) LLM-actions UI/UX and logic as the Planning stage, but adapted for per-section operation.

### 2. Proposed Directory & File Structure

**Backend (Python):**
```
app/
  api/
    writing_llm/                 # NEW: Writing-stage LLM API endpoints
      __init__.py
      routes.py                   # Section-level LLM action endpoints
  writing/
    llm_actions.py               # Section-level LLM action logic (no Planning imports)
    ...
```

**Frontend (Templates & JS):**
```
app/
  templates/
    writing/
      llm_panel.html             # NEW: Writing-stage LLM panel template (purple area)
      ...
  static/
    js/
      writing_llm_panel.js       # NEW: JS for Writing-stage LLM panel (section-centric)
      ...
```

**Docs:**
```
docs/
  temp/
    llm_section_level_actions_mini_project.md  # This planning doc (updated)
```

### 3. API Endpoints (Writing Stage Only)
- **POST** `/api/writing_llm/posts/<post_id>/sections/<section_id>/llm`  
  Run LLM action for a single section, with post context.
- **POST** `/api/writing_llm/posts/<post_id>/sections/batch_llm`  
  Run LLM actions for multiple selected sections (batch processing).
- **GET** `/api/writing_llm/posts/<post_id>/sections/<section_id>/fields`  
  Get available fields for a section (for dropdowns).
- **GET** `/api/writing_llm/posts/<post_id>/fields`  
  Get post-level fields (for context in prompts).

### 4. Templates & JS
- `writing/llm_panel.html`: Identical in look/feel to Planning LLM panel, but operates on section context.
- `static/js/writing_llm_panel.js`: Handles section selection, field mapping, and LLM action triggers for Writing stage.
- **No imports or references to Planning stage code.**

### 5. Field Mapping (Writing Stage)
- **Per-section field mapping**: Store mapping in a new table or as a JSONB field in `post_section` (e.g., `llm_field_mapping`).
- **Dropdowns**: Show both section-level and post-level fields, grouped and clearly labeled.
- **Mapping Storage Example:**
  - `post_section.llm_field_mapping` (JSONB):
    ```json
    {
      "inputs": ["section_heading", "post_development.idea_scope"],
      "output": "first_draft"
    }
    ```
- **Field mapping UI**: Only available in Writing stage LLM panel.

### 6. Data Integration Strategy
- **Section as Primary:**
  - All LLM actions are scoped to a section, with the section's data as the main input/output.
  - The post-level data (from `post_development`) and other sections' data are passed as context only.
- **No Overlap:**
  - Section-level LLM actions never update post-level fields directly.
  - Post-level LLM actions (Planning) never update section fields.
- **Synchronization:**
  - If section structure changes (add/delete/reorder), ensure `post_development.section_headings` is updated via existing triggers.
  - Section content changes do not affect Planning data.

### 7. Documentation & Firewalls
- **All new endpoints, templates, and field mappings for Writing stage are documented in this planning doc.**
- **Explicit note in all new files:**
  - `// DO NOT IMPORT OR REFERENCE PLANNING STAGE CODE. This module is for Writing stage only.`
- **Update this doc with every new file, endpoint, or mapping added.**

### 8. Risks & Mitigations
- **Risk:** Accidental import or reference to Planning code.
  - **Mitigation:** Linting, code review, and explicit comments in all new files.
- **Risk:** User confusion between Planning and Writing LLM panels.
  - **Mitigation:** Clear UI labels and documentation.
- **Risk:** Data drift between section and post-level fields.
  - **Mitigation:** Rely on existing triggers for section structure; never update post-level fields from Writing LLM actions.

---

**No code will be written until you review and approve this plan.** 