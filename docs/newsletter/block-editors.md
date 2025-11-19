# Newsletter Block Editors

This document provides an overview of the block editor system. For detailed documentation on each block type, see the individual block documentation files.

## Overview

Block editors provide a unified interface for:
- **Automated suggestions**: AI-selected content based on scoring and diversity rules
- **Human override**: Manual text editing and selection override
- **Preview**: Live preview of rendered content
- **Auto-select toggle**: Enable/disable automatic content selection

## Architecture

### Service Layer

- **`block_suggestion_service.py`**: Unified routing to type-specific suggestion logic
  - `get_suggestions_for_block()`: Get suggestions for any block type
  - `auto_select_for_block()`: Auto-select content and format payload
  
- **`block_editor_service.py`**: Editor-specific operations
  - `get_suggestions()`: Fetch suggestions with current selection
  - `apply_suggestion()`: Apply a selected suggestion
  - `save_override()`: Save manual text override
  - `regenerate_text()`: Regenerate from current selection

- **`suggestion_service.py`**: Core suggestion generation
  - `generate_suggestions()`: Score and filter source items
  - `validate_link()`: Check URL validity
  - `select_default()`: Pick top-scored suggestion

### UI Components

- **`block_editor_base.html`**: Common wrapper for all block editors
  - Block header with description
  - Enable/disable toggle
  - Move up/down, delete controls
  - Type-specific editor inclusion

- **`block_editor_intro.html`**: Intro block editor (see [Intro Block](blocks/intro.md))
- **`block_editor_snapshot.html`**: Snapshot block editor (see [Snapshot Block](blocks/snapshot.md))
- **`block_editor_universal.html`**: Universal editor for other block types

## Block Types

Each block type has its own detailed documentation:

- **[Intro Block](blocks/intro.md)** - Welcome message with aggregated weather/event/community content
- **[Snapshot Block](blocks/snapshot.md)** - Single cultural highlight from external sources
- **[Feature Block](blocks/feature.md)** - Latest published blog post
- **[Products Blocks](blocks/products.md)** - New products and spotlight product
- **[Category Block](blocks/category.md)** - Rotating category features
- **[Evergreen Block](blocks/evergreen.md)** - Reusable content snippets
- **[Closing Block](blocks/closing.md)** - Newsletter sign-off

## Suggestion Flow

1. **Fetch**: `get_suggestions()` calls `block_suggestion_service.get_suggestions_for_block()`
2. **Route**: Service routes to type-specific logic (intro uses `select_intro_content()`, etc.)
3. **Score**: Source items are scored (freshness + signal)
4. **Filter**: Safety rules, diversity rules, link validation applied
5. **Format**: Suggestions formatted with metadata (scores, categories, URLs)
6. **Display**: UI shows top 3 suggestions with "Use This" buttons

## Auto-Select Behavior

When auto-select is enabled (default):
- Top-scored suggestion is automatically selected
- For intro: Aggregates best weather + event + community items
- For snapshot: Picks single highest-scored item
- Content is generated and stored in block payload

Editor can:
- Disable auto-select to manually choose from suggestions
- Override generated text manually
- Mix both (select suggestion but edit text)

## API Endpoints

All endpoints are JSON-based and shared across all block types:

### Get Suggestions
```
GET /newsletter/issue/:issue_id/block/:block_id/suggestions
```

Returns:
```json
{
  "suggestions": [...],
  "current": {...},
  "metadata": {...}
}
```

### Apply Suggestion
```
POST /newsletter/issue/:issue_id/block/:block_id/select-suggestion
Body: {"suggestion_id": 123}
```

Applies suggestion, generates text, updates block payload.

### Save Override
```
POST /newsletter/issue/:issue_id/block/:block_id/override
Body: {"text": "Custom text..."}
```

Saves manual override, sets `manual_override: true` in payload.

### Preview
```
GET /newsletter/issue/:issue_id/block/:block_id/preview
```

Returns rendered HTML for the block (currently returns payload, full HTML rendering TODO).

## QA Integration

The QA service (`qa_service.py`) checks:
- **Link validation**: All URLs in suggestions are validated
- **Content safety**: Safety rules applied to suggestions and selected items
- **Image checks**: Image URLs validated (for feature/spotlight blocks)

## File Organization

```
blog-core/newsletter/
├── services/
│   ├── block_suggestion_service.py  # Unified routing
│   ├── block_editor_service.py      # Editor operations
│   ├── suggestion_service.py       # Core suggestion logic
│   └── scoring.py                   # Scoring rules
├── selectors/
│   ├── intro.py                     # Intro selector
│   ├── snapshot.py                  # Snapshot selector
│   ├── blog_feature.py              # Feature selector
│   ├── products.py                  # Products selectors
│   ├── category.py                  # Category selector
│   └── evergreen.py                 # Evergreen selector
├── rendering/
│   ├── intro_text.py                # Intro text generation
│   └── snapshot_text.py             # Snapshot text generation
└── sources/                         # Source adapters
    ├── rss_adapter.py
    ├── reddit_adapter.py
    └── html_adapter.py

templates/newsletter/partials/
├── block_editor_base.html           # Common wrapper
├── block_editor_intro.html          # Intro editor
├── block_editor_snapshot.html       # Snapshot editor
└── block_editor_universal.html     # Universal editor
```

## Future Enhancements

- [ ] Full HTML preview rendering in preview endpoint
- [ ] Rich text editor for override (instead of plain textarea)
- [ ] Suggestion history/cooldown tracking
- [ ] Batch suggestion refresh for all blocks
- [ ] Custom scoring weights per block type

