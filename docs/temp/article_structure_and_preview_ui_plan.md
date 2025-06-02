# Article Structure and Preview UI Plan

## Purpose
 
To provide non-technical editorial staff with an intuitive, high-level view of a post's structure and content as it develops, while preserving the clarity and focus of the existing modular workflow panels. This UI will:
- Show all sections, top/tail fields, and their statuses in a single view.
- Allow quick navigation to edit/re-edit any piece.
- Offer a clean, "as published" Preview mode.

## Rationale

- Editors need to see the whole article at a glance, not just field-by-field.
- Modular panels are excellent for focused editing, but not for overview or navigation.
- A structure/template view and a preview mode will make the system more accessible and efficient for editorial workflows.

## Key Concepts

- **Structure/Template View:**
  - Shows the full article breakdown: sections (with headings, themes, content snippets, status), intro, conclusion, metadata, etc.
  - Each piece is clearly labeled and shows its completion status (e.g., draft, reviewed, needs attention).
  - Each piece has an "Edit" button to jump to the relevant modular workflow panel.
  - Drag-and-drop or reorder sections (optional, if supported).

- **Preview Mode:**
  - Renders the article as it would appear to readers, using current content.
  - Read-only, but each section/top/tail can have a "Jump to Edit" link.
  - Accessible from anywhere in the workflow.

## User Flow

1. **Editor opens a post** → sees the Structure/Template view by default.
2. **Clicks on a section or field** → jumps to the modular workflow panel for that piece.
3. **Edits and saves** → returns to Structure/Template view.
4. **Clicks "Preview"** → sees the full article as it will be published.
5. **Clicks "Jump to Edit" in Preview** → returns to editing that piece.

## Feature Breakdown

| Feature                | Structure/Template View | Preview Mode | Modular Workflow |
|------------------------|------------------------|--------------|-----------------|
| See all sections       | ✓                      | ✓            | (fragmented)    |
| Edit in context        | ✓ (via Edit button)    | (via link)   | ✓               |
| Live preview           |                        | ✓            |                 |
| Status tracking        | ✓                      | ✓            | ✓               |
| Navigation             | ✓                      | ✓            | (by field)      |

## Terminology
- **Structure View**: Emphasizes the editable, modular nature of the article.
- **Template View**: Suggests a blueprint for the article, but may be confused with literal templates.
- **Article Overview**: Another possible name.

## Wireframes & Diagrams

(See below for mockups)

---

# Wireframes & Diagrams

## 1. Structure/Template View (Article Overview)

```
+-------------------------------------------------------------+
| [Post Title]         [Status: In Progress]   [Preview Btn]  |
+-------------------------------------------------------------+
| Intro: [content snippet]         [Edit] [Status: Draft]     |
+-------------------------------------------------------------+
| Section 1: [Heading] [Theme]     [Edit] [Status: Complete]  |
|   [Content snippet...]                                      |
+-------------------------------------------------------------+
| Section 2: [Heading] [Theme]     [Edit] [Status: Draft]     |
|   [Content snippet...]                                      |
+-------------------------------------------------------------+
| ...                                                         |
+-------------------------------------------------------------+
| Conclusion: [content snippet]   [Edit] [Status: Needs Work] |
+-------------------------------------------------------------+
| Metadata: [fields...]            [Edit] [Status: Complete]  |
+-------------------------------------------------------------+
```

- Each block is clickable for editing.
- Status is color-coded (e.g., green=complete, yellow=draft, red=needs work).
- [Preview] button in header.

## 2. Preview Mode

```
+-------------------------------------------------------------+
| [Post Title]         [Back to Structure]                    |
+-------------------------------------------------------------+
| [Intro: full content]                                       |
+-------------------------------------------------------------+
| [Section 1: full content]                                   |
+-------------------------------------------------------------+
| [Section 2: full content]                                   |
+-------------------------------------------------------------+
| ...                                                         |
+-------------------------------------------------------------+
| [Conclusion: full content]                                  |
+-------------------------------------------------------------+
| [Metadata: rendered as in published post]                   |
+-------------------------------------------------------------+
```

- No editing in this mode.
- Each section could have a subtle "Edit" link for quick navigation.

## 3. Navigation Diagram

```
[Structure/Template View] <---edit---> [Modular Workflow Panel]
         |                                      ^
         |                                      |
         +------------> [Preview Mode] <--------+
```

---

## Next Steps
- Review and discuss this plan and wireframes.
- Decide on terminology: Structure View, Template View, Article Overview, etc.
- Plan implementation (routes, templates, API integration). 