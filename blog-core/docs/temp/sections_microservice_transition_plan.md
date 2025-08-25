# Sections Microservice Transition Plan (Port 5003)

---

**🚨 STRICT EXECUTION WARNING 🚨**

- **DO NOT** stray from this plan for any reason.
- **DO NOT** change, edit, or touch any code, file, or directory that is not explicitly listed in this plan **without explicit written permission from the user**.
- **DO NOT** add, remove, or refactor any features, endpoints, or logic not described here.
- **DO NOT** reference or interact with any other project (e.g., autonick, legacy, or unrelated codebases).
- **If in doubt, STOP and request written clarification from the user.**

---

## Objective
Port the green Sections module from the legacy /blog project (port 5000) to a new, fully independent Flask microservice (port 5003), with no legacy LLM-actions or planning code. This document details every file, function, and step required for a clean, robust transition.

---

## 1. **Database & Data Model**
- **Tables to use:**
  - `post_section` (main section data)
  - `post_section_elements` (facts, ideas, themes per section)
  - `post_development` (for section_headings sync)
- **Triggers:**
  - Automatic sync between `post_development.section_headings` and `post_section` (see `/blog/docs/reference/workflow/section_synchronization.md`)

---

## 2. **API Endpoints to Port (and Clean Up)**
Implement these endpoints in the new microservice, using only section-related logic:

- `GET    /api/workflow/posts/<post_id>/sections` — List all sections for a post
- `POST   /api/workflow/posts/<post_id>/sections` — Create a new section
- `GET    /api/workflow/posts/<post_id>/sections/<section_id>` — Get a specific section
- `PUT    /api/workflow/posts/<post_id>/sections/<section_id>` — Update a section
- `DELETE /api/workflow/posts/<post_id>/sections/<section_id>` — Delete a section
- `PUT    /api/workflow/posts/<post_id>/sections/reorder` — Reorder sections
- `GET    /api/workflow/posts/<post_id>/sections/<section_id>/elements` — List elements for a section
- `POST   /api/workflow/posts/<post_id>/sections/<section_id>/elements` — Add element to section
- `PUT    /api/workflow/posts/<post_id>/sections/<section_id>/elements/<element_id>` — Update element
- `DELETE /api/workflow/posts/<post_id>/sections/<section_id>/elements/<element_id>` — Delete element
- `POST   /api/workflow/posts/<post_id>/sync-sections` — Manual sync endpoint

**Reference:** `/blog/app/api/workflow/routes.py` (see `manage_sections`, `manage_section`, element endpoints)

---

## 3. **Templates to Port**
- `app/templates/workflow/index.html` (writing stage, right pane)
- `app/templates/workflow/writing/content.html` (sections panel)
- Remove all LLM/planning/publishing code and UI
- Only keep the green sections panel and its JS hooks

---

## 4. **JavaScript to Port**
- `/static/js/workflow/template_view.js` (section rendering, accordion, selection)
- `/static/js/workflow/section_drag_drop.js` (drag-and-drop reordering)
- Remove all LLM/planning/publishing code and imports
- Ensure all API calls point to the new microservice (port 5003)

---

## 5. **Other Files/Logic**
- Any CSS for the green theme (copy from `/blog` or adapt from `/blog-llm-actions`)
- README and setup docs for the new microservice
- Health check endpoint (`/health`)

---

## 6. **What to Exclude**
- All LLM actions, context, planning, and publishing endpoints/UI
- Any code for other workflow stages
- Any shared or legacy code not strictly required for section management
- All code related to `/llm-actions`, `/planning`, `/publishing`, or `/images` unless directly used by sections

---

## 7. **Implementation Steps**
- [x] 1. **Set up new Flask project** (already done)
- [ ] 2. **Copy and adapt DB connection logic** (from `/blog/app/api/workflow/routes.py`)
- [ ] 3. **Implement section CRUD and element endpoints** (see above)
- [ ] 4. **Implement sync logic and endpoint**
- [ ] 5. **Copy and adapt templates for the green panel**
- [ ] 6. **Copy and adapt JS for section rendering and drag/drop**
- [ ] 7. **Test all endpoints with curl and UI**
- [ ] 8. **Document all endpoints and setup in README**
- [ ] 9. **Commit after each major step**

---

## 8. **Testing & Validation**
- Use curl to test all endpoints (see `/blog/docs/reference/workflow/sections.md` for examples)
- Validate UI in iframe in 5001
- Confirm no LLM/planning code remains

---

## 9. **References**
- `/blog/docs/reference/workflow/sections.md`
- `/blog/docs/reference/workflow/section_synchronization.md`
- `/blog/app/api/workflow/routes.py` (section endpoints)
- `/blog/app/templates/workflow/index.html` (sections panel)
- `/blog/app/static/js/workflow/template_view.js`, `section_drag_drop.js`

---

**If interrupted, resume by following the steps above, porting only the files and logic listed, and testing each endpoint and UI feature as you go.** 