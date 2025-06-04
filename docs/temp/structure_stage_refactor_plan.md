# Structure Stage Refactor Implementation Plan

> **Instructions:**
> - Tick off each checkbox as you complete the corresponding task.
> - Review and refine this plan before starting implementation.

---

## 1. UI/UX Redesign
- [x] Design a custom template for the Structure stage (not the generic Template View)
- [x] Inputs Panel:
    - [x] Display all relevant input fields (title, idea, facts, etc.)
    - [x] Allow editing of these fields before running the LLM (UI only)
- [x] LLM Action Panel:
    - [x] Prominent "Plan Sections" button to trigger the LLM (UI only)
    - [x] Option to select which inputs to use (checkboxes or multi-select) (UI only)
- [x] Output Panel:
    - [x] Display LLM's proposed section structure as a list/table (placeholder UI only)
    - [ ] Each row = one section (title, assigned ideas, assigned facts)
    - [ ] Enable drag-and-drop reordering of sections
    - [ ] Allow manual assignment of facts/ideas to sections (e.g., via dropdowns or drag-and-drop)
    - [ ] Allow editing of section titles and notes
- [x] Save/Accept Panel:
    - [x] "Accept Structure" button to save the proposed structure to the database (UI only)
    - [ ] Option to review/confirm before saving

---

## 2. Backend/Data Flow
- [ ] Review and document all relevant input fields in the DB (post, post_development, post_fact, etc.)
- [ ] Ensure facts/ideas are available in a structured format for assignment
- [ ] Implement endpoint to run LLM section planning:
    - [ ] Accepts selected input fields
    - [ ] Returns structured section plan (JSON: sections, assigned facts/ideas)
- [ ] Implement endpoint to save structure:
    - [ ] Accepts edited section plan
    - [ ] Persists to post_section and related tables
- [ ] Ensure robust error handling and validation

---

## 3. Drag-and-Drop & Manual Assignment
- [ ] Integrate a drag-and-drop library (e.g., SortableJS, Dragula, or native HTML5)
- [ ] Implement drag-and-drop for reordering sections
- [ ] Implement UI for manual assignment of facts/ideas to sections (drag-and-drop or dropdowns)
- [ ] Ensure assignments are reflected in the output data structure

---

## 4. Data Consistency & Stage Integration
- [ ] Review previous stages to ensure facts/ideas are structured and available
- [ ] If needed, refactor earlier stages to output structured data (not just text blobs)
- [ ] Ensure smooth transition from Structure to Authoring (post_section records created and ready)

---

## 5. Documentation & Review
- [ ] Document all UI/UX flows and backend endpoints
- [ ] Update wireframes and diagrams as needed
- [ ] Review plan with stakeholders before starting implementation

---

## 6. Implementation & Testing
- [ ] Implement frontend and backend changes as per plan
- [ ] Test all user flows (inputs, LLM, drag-and-drop, manual assignment, save)
- [ ] Validate data integrity and transitions to later stages
- [ ] Collect feedback and iterate

---

**Reminder:**
- Tick off each box as you complete the task.
- Review and refine this plan before starting implementation. 