w# Section-Based Article Development Implementation Plan

> **Status:** DRAFT — To be reviewed before implementation

---

## 1. Schema Review & Rationalization

- [ ] **Review all existing tables and fields for section/article structure**
  - [ ] `post` — article-level metadata
  - [ ] `post_section` — section content, headings, order, and metadata
  - [ ] `post_development` — article-wide fields (intro, conclusion, meta, etc.)
  - [ ] `post_fact` — (to be added) all facts, with optional section assignment
  - [ ] `post_outline` — (to be added) outline items, with optional section assignment
  - [ ] `llm_action`, `llm_prompt`, `llm_interaction` — LLM workflow
  - [ ] `workflow`, `workflow_stage_entity`, `workflow_sub_stage_entity` — workflow tracking
- [ ] **Identify and document any confusing overlaps or redundancies**
  - [ ] Are section fields duplicated in both `post_section` and `post_development`?
  - [ ] Are facts and outline items stored in a way that supports assignment to sections?
  - [ ] Are all per-section fields (images, social, etc.) in `post_section` only?
- [ ] **Propose schema changes for clarity and robustness**
  - [ ] Add `post_fact` table (if not present)
  - [ ] Add `post_outline` table (if not present)
  - [ ] Ensure `post_section` has: `heading`, `theme`, `assigned_facts` (JSONB), `assigned_outline` (JSONB), `content`, `status`, `image_metadata`, etc.
  - [ ] Remove/mark as deprecated any fields in `post_development` that should be per-section
  - [ ] Document all changes in `/docs/database/schema.md` and `create_tables.sql`

---

## 2. Backend API & Model Changes

- [ ] **Design/implement endpoints for section planning and writing**
  - [ ] `GET /api/v1/post/<post_id>/sections` — List all sections
  - [ ] `POST /api/v1/post/<post_id>/sections/plan` — LLM: plan sections, assign facts
  - [ ] `POST /api/v1/post/<post_id>/sections/<section_id>/generate` — LLM: generate section content
  - [ ] `PUT /api/v1/post/<post_id>/sections/<section_id>` — Update section
  - [ ] `GET /api/v1/post/<post_id>/facts` — List all facts
  - [ ] `PUT /api/v1/post/<post_id>/facts/<fact_id>` — Assign/reassign fact
- [ ] **Update models and DB access logic**
  - [ ] Add/modify models for new/changed tables
  - [ ] Ensure robust, parameterized SQL for all new endpoints
  - [ ] Add Marshmallow schemas for validation/serialization
- [ ] **Document all new endpoints in `/docs/database/schema.md` and API docs**

---

## 3. Frontend UI/UX

- [ ] **Section Planner Panel**
  - [ ] Display outline and facts
  - [ ] Run LLM to generate section headings/themes and assign facts
  - [ ] Visualize fact-to-section assignments (drag-and-drop or list)
- [ ] **Section Editor Panel**
  - [ ] For each section: show heading, theme, assigned facts, and content
  - [ ] Run LLM to (re)generate section content
  - [ ] Allow manual editing and status tracking
- [ ] **Fact Store Panel**
  - [ ] Show all facts, assignments, and usage
  - [ ] Allow reassigning facts to sections
- [ ] **Integrate with existing workflow UI**
  - [ ] Ensure section-based workflow fits into modular workflow panels
- [ ] **Document UI/UX in `/docs/frontend/templates.md`**

---

## 4. LLM Workflow Integration

- [ ] **Section Planning LLM Prompt**
  - [ ] Prompt: Given outline and facts, propose section headings/themes and assign facts
  - [ ] Output: JSON with headings, themes, and fact assignments
- [ ] **Section Writing LLM Prompt**
  - [ ] Prompt: For each section, write content using only assigned facts and theme
  - [ ] Output: Section content
- [ ] **Implement LLM API calls and error handling**
  - [ ] Robust error handling and retry logic
  - [ ] Logging and diagnostics for LLM outputs
- [ ] **Document LLM prompt formats and workflow**

---

## 5. Migration & Documentation

- [ ] **Update/create migration scripts for any schema changes**
  - [ ] `create_tables.sql` fully updated
  - [ ] Backup/restore scripts updated
- [ ] **Update all schema and API docs**
  - [ ] `/docs/database/schema.md`
  - [ ] `/docs/database/sql_management.md`
  - [ ] API docs (OpenAPI/Swagger or Markdown)
- [ ] **Document migration/restore process for this change**

---

## 6. Testing & Validation

- [ ] **Unit and integration tests for all new endpoints**
- [ ] **Manual UI/UX testing for section planner/editor/fact store**
- [ ] **Test LLM integration with real and synthetic data**
- [ ] **Test backup/restore and migration process**
- [ ] **Document all test results and known issues**

---

## Technical Notes & Rationale

- Section-based structure is foundational for modular writing, per-section images, and syndication.
- Fact and outline assignment enables LLMs to write with clear scope and avoid repetition.
- All schema and API changes are documented and versioned for robust future development.
- All changes are committed to git and backed up before and after migration. 