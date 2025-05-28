# Template Structure

> **NOTE:** This project uses PostgreSQL only. All database changes are made via direct SQL. No ORM or migration tools (Alembic, SQLAlchemy, SQLite) are used or supported.

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

## New Feature Note
- The /llm/prompts page now defaults to the Prompt Parts tab, which features a persistent radio button filter for Type (All, system, user, assistant) above the list. The filter is styled per the dark theme style guide and persists across tab switches.
- The /llm/actions page now features a single in-page Action builder area. The Edit button (formerly Details) for each action, as well as the New Action button, anchor to the builder area below. When Edit is clicked, the builder is preloaded with the action's details and switches to update mode (the Save button becomes Update). When New Action is clicked, the builder is cleared and switches to create mode. There is no modal or separate details page for actions; all editing and creation is handled in-page for a seamless workflow. 