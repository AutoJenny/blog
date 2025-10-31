# Newsletter Block Editors

This document describes the block editor system for managing newsletter content with automated suggestions and human override capabilities.

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

- **`block_editor_intro.html`**: Intro block editor
  - 3 suggestions list (weather/event/community)
  - Current content preview
  - Manual override textarea
  - Preview toggle

- **`block_editor_snapshot.html`**: Snapshot block editor
  - Single-item focused suggestions
  - Similar interface to intro but simpler

- **`block_editor_universal.html`**: Universal editor for other block types
  - JSON payload display
  - Basic suggestion support
  - JSON override editor

## Block Types

### Intro Block

**Purpose**: Welcome message with topical content from Scotland

**Data Sources**:
- Weather items (Met Office, BBC Scotland)
- Event items (HES, Museums, Galleries)
- Community items (Reddit discussions)

**Payload Structure**:
```json
{
  "text": "Generated 2-3 sentence intro text...",
  "suggestions": [
    {
      "id": 123,
      "source_name": "Met Office",
      "title": "Weather warning...",
      "url": "...",
      "category": "weather",
      "combined_score": 18.5
    }
  ],
  "selected": {...},
  "items_by_category": {
    "weather": {...},
    "event": {...},
    "community": {...}
  }
}
```

**Text Generation**: Uses `rendering/intro_text.py` to combine items with attribution.

### Snapshot Block

**Purpose**: Single cultural highlight from external sources

**Data Sources**: Same as intro, but selects single best item

**Payload Structure**:
{
  "title": "Item title",
  "publisher": "Source name",
  "url": "...",
  "comment": "Generated snapshot text with attribution",
  "suggestions": [...],
  "selected_id": 123
}
```

**Text Generation**: Uses `rendering/snapshot_text.py` for concise attribution.

### Other Block Types

Feature, Products, Category, Evergreen blocks use existing selectors but now:
- Store suggestions in payload (if available)
- Support suggestion API endpoints
- Can use universal editor UI

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

All endpoints are JSON-based:

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

The QA service (`qa_service.py`) now checks:
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
│   └── snapshot.py                  # Snapshot selector
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

