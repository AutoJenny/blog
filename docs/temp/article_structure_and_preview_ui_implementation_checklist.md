# Article Template and Preview UI: Technical Implementation Checklist (Updated)

> **Instructions:**
> - Tick off each checkbox as you complete the corresponding task.
> - Focus first on frontend mockups and navigation. Backend/API work begins only after frontend sign-off.

---

## 1. Project Setup & Planning
- [ ] Review and confirm UI plan, wireframes, and mockups with stakeholders
- [ ] Create new git branch for UI implementation
- [ ] Set up `/workflow/template/` and `/workflow/preview/` routes in Flask (stub only, no backend logic yet)
- [x] Custom Structure stage UI skeleton implemented in planning/structure/index.html (Inputs, LLM Action, Output, Accept panels; static UI only)
- [x] Create `template.html` template in `app/templates/workflow/`
- [x] Implement static layout for Template View (UI only, no backend logic)

---

## 2. Frontend: Navigable Mockups (HTML/CSS/JS Stubs)

### 2.1 Template View (Article Overview)
- [ ] Create `template.html` template in `app/templates/workflow/`
- [ ] Implement static layout for:
    - [ ] Post title, status, and Template/Preview toggle button in header
    - [ ] Stage/progress icons panel
    - [ ] Intro block (snippet, Edit, status)
    - [ ] Section blocks (heading, theme, snippet, Edit, status)
    - [ ] Conclusion block (snippet, Edit, status)
    - [ ] Metadata block (fields, Edit, status)
    - [ ] Add Section and Reorder Sections controls (UI only)
- [ ] Color-code status indicators (e.g., green=complete, yellow=draft, red=needs work)
- [ ] Make each [Edit] button/link open the modular workflow panel as a modal or subsidiary panel
- [ ] Implement breadcrumbs and navigation header

### 2.2 Preview Mode
- [x] Create `preview.html` template in `app/templates/workflow/`
- [x] Implement static layout for Preview Mode (UI only, no backend logic)
- [ ] Ensure Preview is read-only (no editing in this mode except via Edit links)

### 2.3 Modular Edit Panel (Modal/Subsidiary)
- [ ] Create a modal or subsidiary panel for modular workflow editing
- [ ] Ensure it can be opened from both Template and Preview views
- [ ] On save/cancel, return to the previous view

### 2.4 Navigation & User Flow
- [ ] Ensure navigation between Template, Preview, and Modular Edit Panel
- [ ] Update Posts List so clicking a post goes to Template View
- [ ] Test all navigation paths for usability

---

## 3. Frontend: Feedback & Iteration
- [ ] Review mockups with editorial and technical stakeholders
- [ ] Collect feedback and iterate on layout, navigation, and labeling
- [ ] Update wireframes and documentation as needed
- [ ] Obtain sign-off on frontend mockups and navigation

---

## 4. Backend/API Implementation (To Begin After Frontend Sign-off)
- [ ] Design and implement API endpoints for fetching post structure, sections, and content
- [ ] Integrate backend data with Template and Preview views
- [ ] Implement status tracking and editing logic
- [ ] Connect [Edit] actions to real modular workflow panels
- [ ] Implement Add Section and Reorder Sections functionality
- [ ] Test end-to-end user flow

---

## 5. Documentation & Handover
- [ ] Update `/docs/frontend/templates.md` with new UI flows and diagrams
- [ ] Document all routes, templates, and API endpoints
- [ ] Update changelog and migration notes
- [ ] Handover to QA and training for editorial staff

---

## 6. Sign-off
- [ ] Final review and sign-off by stakeholders
- [ ] Merge feature branch to main
- [ ] Deploy to production

---

**Reminder:**
- Tick off each box as you complete the task.
- Do not begin backend/API work until frontend mockups and navigation are signed off by all stakeholders. 