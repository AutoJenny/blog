# Article Structure and Preview UI: Mockups (Annotated)

--- 

## 1. Structure/Template View (with Annotations)

```
+-------------------------------------------------------------+
| [Post Title]         [Status: In Progress]   [Preview Btn]  |
| [Breadcrumbs: Home > Posts > Post Title]                    |
+-------------------------------------------------------------+
| Intro: [content snippet]         [Edit] [Status: Draft]     |
|   (Shows first 1-2 lines, ellipsis if longer)               |
+-------------------------------------------------------------+
| Section 1: [Heading] [Theme]     [Edit] [Status: Complete]  |
|   [Content snippet...]                                      |
|   [Assigned Facts: 1, 2, 3]                                |
|   [LLM: Last generated 2024-06-01]                         |
+-------------------------------------------------------------+
| Section 2: [Heading] [Theme]     [Edit] [Status: Draft]     |
|   [Content snippet...]                                      |
|   [Assigned Facts: 4, 5]                                   |
|   [LLM: Needs review]                                       |
+-------------------------------------------------------------+
| ...                                                         |
+-------------------------------------------------------------+
| Conclusion: [content snippet]   [Edit] [Status: Needs Work] |
+-------------------------------------------------------------+
| Metadata: [fields...]            [Edit] [Status: Complete]  |
+-------------------------------------------------------------+
| [Add Section] [Reorder Sections]                            |
+-------------------------------------------------------------+
```

**Annotations:**
- [Preview Btn]: Opens Preview Mode.
- [Edit]: Jumps to modular workflow panel for that piece.
- [Status]: Color-coded, shows completion state.
- [Assigned Facts]: Quick reference for fact assignment.
- [LLM]: Shows last LLM action or review status.
- [Add Section]: Button to add a new section.
- [Reorder Sections]: Drag-and-drop or up/down arrows.

---

## 2. Preview Mode (with Annotations)

```
+-------------------------------------------------------------+
| [Post Title]         [Back to Structure]                    |
+-------------------------------------------------------------+
| [Intro: full content]                                       |
+-------------------------------------------------------------+
| [Section 1: full content]                                   |
|   [Edit] (subtle link, right-aligned)                       |
+-------------------------------------------------------------+
| [Section 2: full content]                                   |
|   [Edit]                                                    |
+-------------------------------------------------------------+
| ...                                                         |
+-------------------------------------------------------------+
| [Conclusion: full content]                                  |
|   [Edit]                                                    |
+-------------------------------------------------------------+
| [Metadata: rendered as in published post]                   |
+-------------------------------------------------------------+
```

**Annotations:**
- [Back to Structure]: Returns to Structure/Template view.
- [Edit]: Subtle link for quick navigation to editing.
- [Full content]: Shows exactly what will be published, including formatting.

---

## 3. User Flow Diagram (Annotated)

```
[Structure/Template View]
   |   ^
   |   |
   v   |
[Preview Mode] <---edit---> [Modular Workflow Panel]
```

- Users start in Structure/Template View.
- Can jump to Preview Mode or Modular Workflow Panel at any time.
- Editing returns them to Structure/Template View. 