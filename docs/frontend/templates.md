# Template Structure

## 2024-06-14: Universal Modular LLM Workflow Panel
- All workflow substages (Planning, Authoring, Publishing) now use a single modular LLM panel include and JS for input, output, and action selection.
- Dropdowns show all post_development fields, but default to the first field mapped to the current substage for robust cross-stage workflows.
- The modular panel is fully plug-and-play for new substages and fields; no manual DB or template changes are needed.
- All documentation is up to date as of 2024-06-14 and reflects the new universal modular framework and persistence logic.

> **NOTE:** This project uses PostgreSQL only. All database changes are made via direct SQL. No ORM or migration tools (Alembic, SQLAlchemy, SQLite) are used or supported.

**Milestone 2024-06-09:**
- Consolidated workflow idea templates into a single, modular, reusable structure for all workflow stages.
- Deprecated and archived duplicate `idea/index.html` templates.
- Modularized field selection logic; dropdowns now support stage categorization and persistence to the backend.
- Improved maintainability and set foundation for replicating modular workflow for other stages.

The Blog CMS uses Jinja2 templates for all HTML rendering. This document describes the organization and usage of templates.

## Main Template Locations
- `app/templates/base.html`: Main site layout, includes Tailwind CSS and global blocks.
- `app/templates/blog/`: Blog-specific templates (post, list, develop, etc.)
- `app/templates/llm/`: LLM-related templates
- `app/templates/email/`: Email templates
- `app/templates/errors/`: Error pages
- `app/templates/preview/`: Preview UI templates
- `app/templates/db/`: Database-related templates

## Static Assets
- CSS: Referenced via `{{ url_for('static', filename='css/dist/main.css') }}`
- Images: `{{ url_for('static', filename='images/<path>') }}`
- JS: `{{ url_for('static', filename='js/<file>.js') }}`

## Extending Templates
- Use `{% extends 'base.html' %}` for consistent layout and styling.
- Define blocks for content, scripts, and styles as needed.

## Customization
- Add new templates in the appropriate subdirectory.
- Use Tailwind utility classes for styling.

## Blog Index & Dashboard
- The main blog index is now served at the root URL (`/`).
- The dashboard and blog listing are unified in a single, modern, and intuitive design.
- Navigation and template references to the old `/blog/` index have been updated to `/`.
- The new design uses subtle colors, icons, and a card-based layout for clarity and style.
- The UI now uses a true dark theme throughout, with unified header, navigation, and card styling for a premium, cohesive look.

## Area Navigation (LLM & Workflow)
- Area navbars for LLM and Workflow are now auto-included in `base.html` for all subpages (e.g., `/llm/*`, `/workflow/*`).
- The navbars use the same icons and color styling as their respective dashboards for a unified look.
- The navbar is **not** shown on the landing page (e.g., `/llm/`), only on subpages.
- To add or update area nav links, edit the relevant partial (e.g., `llm/_llm_nav.html`).
- Do **not** set `fullwidth_mode` unless you want to suppress all navigation for a page (e.g., docs browser).
- For new sub-areas, follow this pattern for robust, site-wide navigation.

**Update (2024-06):**
- Workflow input/output dropdowns are now populated from the `post_development` table fields for the current post (via `/api/v1/post/<post_id>/development`), not from the `post` table. This ensures the workflow UI always reflects the correct set of development fields.

## New Feature Note
- The /llm/prompts page now defaults to the Prompt Parts tab, which features a persistent radio button filter for Type (All, system, user, assistant) above the list. The filter is styled per the dark theme style guide and persists across tab switches.
- The Prompt Assembler tab now correctly displays all available prompt parts, each with colored tag spans for their tags (role, operation, format, style, specimen). The available list is filtered by the selected type and tags, and the UI logic is robust against missing or malformed tags. (Fixed June 2024)
- The Prompt Assembler and Prompt Parts tab now use background colors to distinguish message types: blue for system, deep green for user, and deep purple for assistant (if used). Tag colors remain as colored spans. This color-coding applies to both the available parts list and the assembled sequence in the Assembler, as well as the main Prompt Parts table. (Updated June 2024)
- The /llm/actions page now features a single in-page Action builder area. The Edit button (formerly Details) for each action, as well as the New Action button, anchor to the builder area below. When Edit is clicked, the builder is preloaded with the action's details and switches to update mode (the Save button becomes Update). When New Action is clicked, the builder is cleared and switches to create mode. There is no modal or separate details page for actions; all editing and creation is handled in-page for a seamless workflow.

## Workflow UI Field Persistence (2024-06-10)

The workflow UI (e.g., /workflow/idea/) now persists all input, output, and LLM action fields directly to the backend database, not just to localStorage. This ensures that user input, generated output, and action selections are always saved and restored reliably, even after reloads or navigation.

### Key Features
- **Input fields** (e.g., idea seed) are loaded from and saved to the `post_development` table via `/api/v1/post/<post_id>/development`.
- **Output fields** (e.g., summary) are loaded from and saved to the same endpoint.
- **LLM action selection** is loaded from and saved to the `post_substage_action` table via `/api/v1/llm/post_substage_actions`.
- All changes are persisted immediately on user interaction (change, click, etc.).
- The logic is generalized and can be reused for any workflow stage or substage by configuring the field and substage names.
- **localStorage is no longer used for persistence**; all state is backend-driven.

This enables robust, permanent persistence and makes the workflow UI easily transferable to other stages/substages with different input/output/action mappings.

## Workflow Modular LLM UI Persistence

- After saving input, output, or action selections, the UI now always re-fetches the latest postSubstageAction from the backend.
- This ensures that both input_field and output_field persist and are always in sync with the backend, even if other users or processes make changes.
- See: app/static/js/workflow_modular_llm.js for implementation details.

**Update (2025-05-30):**
The output dropdown in the modular workflow UI now loads its value from the DB identically to the input dropdown, and is no longer overwritten by the action handler. This resolves the persistent output field bug and ensures both dropdowns always reflect the DB state. 