# Article Structure and Preview UI: Technical Implementation Checklist

> **Instructions:**
> - Tick off each checkbox as you complete the corresponding task.
> - Focus first on frontend mockups and navigation. Backend/API work begins only after frontend sign-off.

---

## 1. Project Setup & Planning
- [ ] Review and confirm UI plan, wireframes, and mockups with stakeholders
- [ ] Create new git branch for UI implementation
- [ ] Set up `/preview/` and `/structure/` routes in Flask (stub only, no backend logic yet)

---

## 2. Frontend: Navigable Mockups (HTML/CSS/JS Stubs)

### 2.1 Structure/Template View (Article Overview)
- [ ] Create `structure.html` template in `app/templates/preview/`
- [ ] Implement static layout for:
    - [ ] Post title, status, and Preview button
    - [ ] Intro block (snippet, Edit, status)
    - [ ] Section blocks (heading, theme, snippet, Edit, status)
    - [ ] Conclusion block (snippet, Edit, status)
    - [ ] Metadata block (fields, Edit, status)
    - [ ] Add Section and Reorder Sections controls (UI only)
- [ ] Color-code status indicators (e.g., green=complete, yellow=draft, red=needs work)
- [ ] Make each [Edit] button/link navigable (links to stub modular workflow panel)
- [ ] Implement breadcrumbs and navigation header

### 2.2 Preview Mode
- [ ] Create `preview.html` template in `app/templates/preview/`
- [ ] Implement static layout for:
    - [ ] Post title and Back to Structure button
    - [ ] Full content for intro, each section, conclusion, metadata
    - [ ] Subtle [Edit] links for each block (links to stub modular workflow panel)
- [ ] Ensure Preview is read-only (no editing in this mode)

### 2.3 Navigation & User Flow
- [ ] Ensure navigation between Structure, Preview, and Modular Workflow Panel stubs
- [ ] Add placeholder/stub for Modular Workflow Panel (for navigation only)
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
- [ ] Integrate backend data with Structure and Preview views
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