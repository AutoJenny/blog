# Article Template and Preview UI: Updated Wireframes

## 1. Template View (Main Editing Home)

```
+-------------------------------------------------------------+
| [Post Title] [Status: In Progress] [Template | Preview]     |
+-------------------------------------------------------------+
| [Stage/Progress Icons: Idea | Research | Template | ...]    |
+-------------------------------------------------------------+
| [TEMPLATE VIEW]                                             |
|-------------------------------------------------------------|
| Intro: [snippet]         [Edit] [Status: Draft]             |
|-------------------------------------------------------------|
| Section 1: [Heading] [Theme] [Edit] [Status: Complete]      |
|   [Content snippet...]                                      |
|-------------------------------------------------------------|
| Section 2: [Heading] [Theme] [Edit] [Status: Draft]         |
|   [Content snippet...]                                      |
|-------------------------------------------------------------|
| Conclusion: [snippet]   [Edit] [Status: Needs Work]         |
|-------------------------------------------------------------|
| Metadata: [fields...]    [Edit] [Status: Complete]          |
|-------------------------------------------------------------|
| [Add Section] [Reorder Sections]                            |
+-------------------------------------------------------------+
```

- [Template | Preview]: Rocker/toggle button, always visible.
- [Edit]: Opens modular edit panel as modal or slide-in.
- [Stage/Progress Icons]: Consistent across all workflow stages.

## 2. Preview View (Toggle)

```
+-------------------------------------------------------------+
| [Post Title] [Status] [Template | Preview]                  |
+-------------------------------------------------------------+
| [Stage/Progress Icons: ...]                                 |
+-------------------------------------------------------------+
| [PREVIEW VIEW]                                              |
|-------------------------------------------------------------|
| [Intro: full content]   [Edit]                              |
|-------------------------------------------------------------|
| [Section 1: full content] [Edit]                            |
|-------------------------------------------------------------|
| [Section 2: full content] [Edit]                            |
|-------------------------------------------------------------|
| [Conclusion: full content] [Edit]                           |
|-------------------------------------------------------------|
| [Metadata: rendered as in published post] [Edit]            |
+-------------------------------------------------------------+
```

- [Edit]: Opens modular edit panel as modal or slide-in.
- No editing in Preview mode except via Edit links.

## 3. Modular Edit Panel (Modal/Subsidiary)

```
+-----------------------------+
| [Edit Section: Heading]     |
+-----------------------------+
| [Modular editing fields...] |
| [Save] [Cancel]             |
+-----------------------------+
```

- Opens over Template or Preview view.
- On save/cancel, returns to Template/Preview.

## 4. Navigation Flow

```
[Posts List] --click post--> [Template View]
     |                            |
     |--toggle Preview----------->|
     |<--toggle Template----------|
     |                            |
     |--Edit (modal)------------->|
     |<--Save/Cancel (modal)------|
```

- All navigation is within the workflow layout.
- Template/Preview toggle is always available. 