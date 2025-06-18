# Article Template and Preview UI Plan (Updated)

## Purpose

To provide non-technical editorial staff with an intuitive, high-level view of a post's structure and content as it develops, while preserving the clarity and focus of the existing modular workflow panels. This UI will:
- Show all sections, top/tail fields, and their statuses in a single Template View.
- Allow quick navigation to edit/re-edit any piece via a modular edit panel.
- Offer a clean, "as published" Preview mode, always accessible via a toggle.
- Integrate Template/Preview views into the main workflow layout, with consistent header and progress panels.

## Rationale

- Editors need to see the whole article at a glance, not just field-by-field.
- Modular panels are excellent for focused editing, but not for overview or navigation.
- A Template View and Preview mode, integrated into the workflow, will make the system more accessible and efficient for editorial workflows.

## Key Concepts

- **Template View:**
  - The main editing home for a post.
  - Shows the full article breakdown: sections (with headings, themes, content snippets, status), intro, conclusion, metadata, etc.
  - Each piece is clearly labeled and shows its completion status (e.g., draft, reviewed, needs attention).
  - Each piece has an "Edit" button to open the modular workflow panel as a modal or subsidiary panel.
  - Drag-and-drop or reorder sections (optional, if supported).
  - Accessible from the Posts List and from any workflow stage.

- **Preview Mode:**
  - Renders the article as it would appear to readers, using current content.
  - Read-only, but each section/top/tail can have a "Jump to Edit" link.
  - Accessible via a toggle in the header, always visible.

- **Workflow Layout:**
  - Header panel: post title, status, Template/Preview toggle.
  - Stage/progress icons: consistent across all workflow stages.
  - Main content area: Template or Preview view, with modular edit panel as modal/subsidiary.

## User Flow

1. **Editor opens a post** → sees the Template View by default.
2. **Clicks on a section or field** → opens the modular workflow panel as a modal/subsidiary.
3. **Edits and saves** → returns to Template View.
4. **Toggles Preview** → sees the full article as it will be published.
5. **Clicks "Edit" in Preview** → opens modular workflow panel as modal/subsidiary.

## Feature Breakdown

| Feature                | Template View | Preview Mode | Modular Workflow |
|------------------------|--------------|--------------|-----------------|
| See all sections       | ✓            | ✓            | (fragmented)    |
| Edit in context        | ✓ (modal)    | (via link)   | ✓               |
| Live preview           |              | ✓            |                 |
| Status tracking        | ✓            | ✓            | ✓               |
| Navigation             | ✓            | ✓            | (by field)      |

## Wireframes & Navigation

See `article_template_and_preview_ui_wireframes.md` for updated wireframes and navigation diagrams reflecting the new layout and flow.

## Next Steps
- Review and discuss this plan and wireframes.
- Plan implementation (routes, templates, API integration) using the new terminology and layout. 