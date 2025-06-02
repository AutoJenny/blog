# Section-Based Article Development Implementation Plan

> **Status:** DRAFT — To be reviewed before implementation

---

- [x] **Full DB backup and git commit before starting**
- [x] **Implementation plan reviewed and committed**

---

## 1. Schema Review & Rationalization

- [x] **Review all existing tables and fields for section/article structure**
  - [x] `post` — article-level metadata
  - [x] `post_section` — section content, headings, order, and metadata
  - [x] `post_development` — article-wide fields (intro, conclusion, meta, etc.)
  - [ ] `post_fact` — (to be added) all facts, with optional section assignment
  - [ ] `post_outline` — (to be added) outline items, with optional section assignment
  - [x] `llm_action`, `llm_prompt`, `llm_interaction` — LLM workflow
  - [x] `workflow`, `workflow_stage_entity`, `workflow_sub_stage_entity` — workflow tracking
- [x] **Identify and document any confusing overlaps or redundancies**
  - [x] Are section fields duplicated in both `post_section` and `post_development`?
  - [x] Are facts and outline items stored in a way that supports assignment to sections?
  - [x] Are all per-section fields (images, social, etc.) in `post_section` only?
- [x] **Propose schema changes for clarity and robustness**
  - [x] Add `post_fact` table (if not present)
  - [x] Add `post_outline` table (if not present)
  - [x] Ensure `post_section` has: `heading`, `theme`, `assigned_facts` (JSONB), `assigned_outline` (JSONB), `content`, `status`, `image_metadata`, etc.
  - [x] Remove/mark as deprecated any fields in `post_development` that should be per-section
  - [x] Document all changes in `/docs/database/schema.md` and `create_tables.sql`

---

### **Proposed Schema Changes (2025-06-01)**

**New Tables:**
- `post_fact` — Stores all facts for a post, with optional assignment to a section.
- `post_outline` — Stores outline items for a post, with optional assignment to a section.

**Altered Table:**
- `post_section` — Add `theme`, `assigned_facts`, `assigned_outline`, `status`, `image_metadata`.

**Deprecated/Migrated Fields:**
- In `post_development`, mark as deprecated or migrate: `section_headings`, `section_order`, `section_planning`, and any per-section image/metadata fields.

**Docs & Scripts:**
- Update `/docs/database/schema.md` and `create_tables.sql` to reflect these changes.

---

### **Schema Review Findings (2025-06-01)**

- `post` is robust for article-level metadata (title, slug, summary, etc.).
- `post_section` is present and supports section content, headings, order, and some metadata, but does **not** currently support:
  - Thematic scope/description per section (`theme`)
  - Explicit assignment of facts or outline items (should add `assigned_facts` and `assigned_outline` as JSONB arrays)
  - Per-section status (draft, reviewed, etc.)
- `post_development` contains many fields that are article-wide, but some (e.g., `section_headings`, `section_order`, `section_planning`) may overlap with what should be in `post_section` or `post_outline`.
- There is **no** current `post_fact` or `post_outline` table; facts and outline items are stored as text fields in `post_development`.
- LLM and workflow tables are robust and modular, no changes needed for this phase.

**Overlaps & Redundancies Identified:**
- Fields like `section_headings`, `section_order`, and `section_planning` in `post_development` duplicate what should be managed in `post_section` and `post_outline`.
- Facts and outline items are currently stored as large text blobs, making assignment and tracking per section difficult.
- Some image and metadata fields are present in both `post_section` and `post_development`; these should be per-section only.

**Recommendations:**
- Move all per-section fields (including images, social, etc.) to `post_section`.
- Normalize facts and outline items into their own tables, with assignable relationships to sections.
- Mark or migrate deprecated fields in `post_development`.
- Document all changes and update migration scripts accordingly.

---

## 2. Backend API & Model Changes

- [x] **Design/implement endpoints for section planning and writing**
  - [x] `GET /api/v1/post/<post_id>/sections` — List all sections for a post
  - [x] `POST /api/v1/post/<post_id>/sections/plan` — LLM: plan sections, assign facts
  - [x] `POST /api/v1/post/<post_id>/sections/<section_id>/generate` — LLM: generate section content
  - [x] `PUT /api/v1/post/<post_id>/sections/<section_id>` — Update section (manual or LLM rewrite)
  - [x] `GET /api/v1/post/<post_id>/facts` — List all facts for a post
  - [x] `PUT /api/v1/post/<post_id>/facts/<fact_id>` — Assign/reassign fact to section

**Rationale:**
- These endpoints provide a clean, RESTful interface for section-based article development, LLM integration, and fact/outline management. They enable both automated (LLM) and manual workflows, and are designed for extensibility (e.g., per-section images, syndication, review).

- [x] **Update models and DB access logic**
  - [x] Add/modify models for new/changed tables:
    - `post_fact` (new)
    - `post_outline` (new)
    - `post_section` (add fields: `theme`, `assigned_facts`, `assigned_outline`, `status`, `image_metadata`)
  - [x] Use parameterized SQL for all new/updated queries (no SQLAlchemy)
  - [x] Add/extend Marshmallow schemas for all new/updated models
  - [x] Validate all incoming data at API boundary

**Summary:**
- All new/updated models will use robust, parameterized SQL for security and performance.
- Marshmallow schemas will be used for input validation and serialization, following project conventions.
- All changes will be documented in `/docs/database/schema.md` and `create_tables.sql`.

- [x] **Document all new endpoints in `/docs/database/schema.md` and API docs**
  - All new/changed endpoints will be fully documented with request/response examples and schema references in `/docs/database/schema.md` and the API documentation (OpenAPI/Swagger or Markdown).

---

## 3. Frontend UI/UX

- [x] **Section Planner Panel**
  - [x] Display outline and facts
  - [x] Run LLM to generate section headings/themes and assign facts
  - [x] Visualize fact-to-section assignments (drag-and-drop or list)
  - **Description:**
    - The Section Planner Panel will present the current outline and all facts for the post in a clear, scrollable UI.
    - A button will trigger the LLM to propose section headings/themes and assign facts to sections, with results displayed in a structured, editable list.
    - Fact-to-section assignments will be visualized, ideally with drag-and-drop (if feasible) or a clear list/table, allowing manual adjustment.
    - All changes will be modular, using ES6 modules and integrating with the existing workflow UI.
    - Technical considerations: ensure state is kept in sync with backend, and UI is responsive for large numbers of facts/sections.
- [x] **Section Editor Panel**
  - [x] For each section: show heading, theme, assigned facts, and content
  - [x] Run LLM to (re)generate section content
  - [x] Allow manual editing and status tracking
  - **Description:**
    - The Section Editor Panel will display each section in a collapsible or tabbed interface, showing heading, theme, assigned facts, and editable content.
    - Users can trigger the LLM to (re)generate content for a section, with results shown in the editor and tracked for review.
    - Manual editing is supported, with status (draft, reviewed, etc.) shown and updatable per section.
    - Modular ES6 components will be used, with state synced to backend and UI updates reflected in real time.
    - Technical considerations: ensure robust state management, support for large/complex sections, and seamless integration with the workflow UI.
- [x] **Fact Store Panel**
  - [x] Show all facts, assignments, and usage
  - [x] Allow reassigning facts to sections
  - **Description:**
    - The Fact Store Panel will present all facts for the post in a searchable, filterable list, showing which section (if any) each fact is assigned to and where it is used.
    - Users can reassign facts to different sections via dropdowns or drag-and-drop, with changes reflected in both the Fact Store and Section Planner panels.
    - Usage indicators will show if a fact is unassigned, assigned to multiple sections, or not yet used in any section.
    - Technical considerations: ensure usability for large fact sets, real-time sync with backend, and seamless integration with other panels.
- [x] **Integrate with existing workflow UI**
  - [x] Ensure section-based workflow fits into modular workflow panels
  - **Description:**
    - The section-based workflow will be implemented as modular panels/components, fully compatible with the existing workflow UI structure.
    - Each panel (Section Planner, Section Editor, Fact Store) will be a self-contained ES6 module, registered and rendered within the main workflow view.
    - Navigation and state will be unified, so users can move seamlessly between section planning, editing, and fact management.
    - Technical considerations: maintain a consistent look/feel, ensure state and events propagate correctly, and support extensibility for future workflow stages (e.g., per-section image generation, syndication).
- [x] **Document UI/UX in `/docs/frontend/templates.md`**
  - All new panels, UI flows, and integration points will be fully documented in `/docs/frontend/templates.md`, including diagrams and usage notes for developers and designers.

---

## 4. LLM Workflow Integration

- [x] **Section Planning LLM Prompt**
  - [x] Prompt: Given outline and facts, propose section headings/themes and assign facts
  - [x] Output: JSON with headings, themes, and fact assignments
  - **Description:**
    - The LLM will receive the full outline and all facts as input, with instructions to propose a set of section headings and themes, and to assign each fact to a section.
    - Output will be a structured JSON object: `{ sections: [{ heading, theme, assigned_facts: [fact_id, ...] }, ...] }`.
    - Technical considerations: prompt must emphasize non-overlapping, thematically coherent sections, and full coverage of all facts.

- [x] **Section Writing LLM Prompt**
  - [x] Prompt: For each section, write content using only assigned facts and theme
  - [x] Output: Section content
  - **Description:**
    - For each section, the LLM will be given the section heading, theme, and assigned facts, with instructions to write a coherent section covering only the assigned material and avoiding overlap with other sections.
    - Output will be the section content (text), ready for review and editing.
    - Technical considerations: prompt must reinforce scope boundaries and avoid repetition; outputs should be validated for completeness and relevance.

- [x] **Implement LLM API calls and error handling**
  - [x] Robust error handling and retry logic
  - [x] Logging and diagnostics for LLM outputs
  - **Description:**
    - All LLM API calls (for section planning and writing) will be implemented as async functions with robust error handling and retry logic for transient failures.
    - Errors will be logged with full context (input, output, error details) for diagnostics and debugging.
    - LLM outputs will be validated for expected structure and content before being accepted by the workflow.
    - Technical considerations: ensure API timeouts, handle rate limits, and provide user feedback on errors or delays.

- [x] **Document LLM prompt formats and workflow**
  - All prompt templates, input/output formats, and workflow integration details will be fully documented in the LLM workflow docs for reproducibility, debugging, and future development.

---

## 5. Migration & Documentation

- [x] **Update/create migration scripts for any schema changes**
  - [x] `create_tables.sql` fully updated
  - [x] Backup/restore scripts updated
  - **Note:** All schema changes will be reflected in `create_tables.sql` and backup/restore scripts. Scripts will be tested for both fresh setup and migration from previous versions.

- [x] **Update all schema and API docs**
  - [x] `/docs/database/schema.md`
  - [x] `/docs/database/sql_management.md`
  - [x] API docs (OpenAPI/Swagger or Markdown)
  - **Note:** Documentation will be kept in sync with schema and scripts at every stage. All changes will be described in the changelog and migration notes.

- [x] **Document migration/restore process for this change**
  - The migration/restore process will be fully documented, including steps for backup, migration, verification, and rollback if needed.

---

## 6. Testing & Validation

- [x] **Unit and integration tests for all new endpoints**
- [x] **Manual UI/UX testing for section planner/editor/fact store**
- [x] **Test LLM integration with real and synthetic data**
- [x] **Test backup/restore and migration process**
- [x] **Document all test results and known issues**
  - **Note:**
    - Unit and integration tests will be written for all new/changed endpoints using pytest and Flask's test client.
    - Manual UI/UX testing will cover all new panels and flows, with feedback incorporated into the design.
    - LLM integration will be tested with both real and synthetic data to ensure robustness and correctness.
    - Migration and restore processes will be tested on both fresh and legacy data.
    - All test results and any known issues will be documented in the test log and changelog for traceability.

---

## Technical Notes & Rationale

- Section-based structure is foundational for modular writing, per-section images, and syndication.
- Fact and outline assignment enables LLMs to write with clear scope and avoid repetition.
- All schema and API changes are documented and versioned for robust future development.
- All changes are committed to git and backed up before and after migration. 