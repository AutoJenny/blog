# Sections Panel: Implementation Mapping

## 1. Overview
This document catalogs all code, templates, JavaScript, backend logic, endpoints, and database tables involved in the Sections panel UI (as seen in the Workflow > Planning/Writing stages). Navigation, header, footer, and unrelated workflow modules are excluded.

---

## 2. Templates
- **Primary UI Template:**
  - `app/templates/workflow/_workflow_content.html`
    - Contains the markup for the Sections card and modal editor.
    - Included by step templates such as `writing/content/sections.html`.
- **Step Template:**
  - `app/templates/workflow/writing/content/sections.html`
    - Extends the workflow base and includes `_workflow_content.html`.

---

## 3. JavaScript
- **Main Workflow JS:**
  - `app/static/js/workflow.js`
    - Handles DOMContentLoaded, fetches sections, initializes UI, and registers event handlers for add/edit/delete/LLM-run.
    - Calls `/workflow/api/sections/` and `/workflow/api/run_llm/` for backend sync.

---

## 4. Backend (Python)
- **Blueprint:**
  - `app/workflow/routes.py`
- **Endpoints:**
  - `/workflow/api/sections/` (POST): Fetch/save all sections for a post/step.
  - `/workflow/api/run_llm/` (POST): Run LLM for a section or step.
  - `/workflow/<int:post_id>/<stage>/<substage>/<step>/sections/` (GET): Fetch all sections for a post/step.
  - `/workflow/<int:post_id>/<stage>/<substage>/<step>/sections/create` (POST): Create a new section.
  - `/workflow/<int:post_id>/<stage>/<substage>/<step>/sections/<int:section_id>` (PUT/DELETE): Update or delete a section.
  - `/workflow/<int:post_id>/<stage>/<substage>/<step>/sections/reorder` (POST): Reorder sections.

---

## 5. Database
- **Table:**
  - `post_section`
    - Fields: `id`, `post_id`, `section_heading`, `section_description`, `ideas_to_include`, `status`, `section_order`
    - Used for all CRUD operations on sections.

---

## 6. Data Flow
- **On Page Load:**
  - JS calls `/workflow/api/sections/` to fetch all sections for the current post/step.
  - Renders each section as an editable card.
- **Add/Edit/Delete:**
  - All changes are sent to `/workflow/api/sections/` (POST) with the full list of sections.
- **LLM Integration:**
  - "Run LLM" button sends a request to `/workflow/api/run_llm/` for the selected section.

---

## 7. File List (for modular extraction)
- Templates:
  - `app/templates/workflow/_workflow_content.html`
  - `app/templates/workflow/writing/content/sections.html`
- JavaScript:
  - `app/static/js/workflow.js`
- Backend:
  - `app/workflow/routes.py`
- Database:
  - `post_section` table and relevant migrations

---

## 8. Exclusions
- **Do NOT include:**
  - Navigation, header, footer, or site-wide layout
  - LLM prompt/inputs/outputs UI (see LLM_ACTIONS_IMPLEMENTATION.md)
  - Any code not directly related to the Sections panel

---

## 9. Next Steps
- Review this mapping for completeness
- Confirm all files and endpoints are correct
- Begin modular extraction and rebuild for the sections panel 