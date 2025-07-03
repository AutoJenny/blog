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