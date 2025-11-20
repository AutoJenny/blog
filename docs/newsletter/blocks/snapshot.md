# Newsletter Snapshot Block ("In the News")

## Overview

The Snapshot block (displayed as "In the News" in UI and Preview) provides a single cultural highlight from external sources, focusing on one high-quality item rather than aggregating multiple items like the Intro block.

**Purpose**: Single cultural highlight from external sources

**Display Name**: "In the News" (renamed from "Scottish Snapshot")

**Status**: ✅ Implemented

## Data Sources

Same as intro block:
- Weather items (Met Office, BBC Scotland)
- Event items (HES, Museums, Galleries)
- Community items (Reddit discussions)

But selects **single best item** instead of aggregating multiple.

## Payload Structure

```json
{
  "title": "Item title",
  "publisher": "Source name",
  "url": "...",
  "comment": "Generated snapshot text with attribution",
  "suggestions": [
    {
      "id": 123,
      "source_name": "...",
      "title": "...",
      "combined_score": 15.2
    }
  ],
  "selected_id": 123
}
```

## Files

- `templates/newsletter/partials/block_editor_snapshot.html` - UI template
- `blog-core/newsletter/selectors/snapshot.py` - Content selection
- `blog-core/newsletter/rendering/snapshot_text.py` - Text generation

**Text Generation**: Uses `rendering/snapshot_text.py` for concise attribution.

## API Endpoints

Same as intro block:
- `GET /newsletter/issue/:issue_id/block/:block_id/suggestions`
- `POST /newsletter/issue/:issue_id/block/:block_id/select-suggestion`
- `POST /newsletter/issue/:issue_id/block/:block_id/override`
- `GET /newsletter/issue/:issue_id/block/:block_id/preview`

