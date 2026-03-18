# Newsletter Evergreen Block

## Overview

The Evergreen block provides reusable content snippets that can be rotated.

**Purpose**: Reusable content with rotation and cooldown

**Status**: ✅ Implemented

## Data Sources

- `newsletter_evergreen` table
- Rotates by `last_used_at` (least recently used first)
- Can filter by `season` and `region_tags`

## Payload Structure

```json
{
  "id": 123,
  "topic": "evergreen_topic",
  "text": "Reusable text content...",
  "length": 150,
  "season": "winter",
  "region_tags": "highlands"
}
```

## Files

- `blog-core/newsletter/selectors/evergreen.py` - Evergreen selection
- Uses universal block editor UI

## API Endpoints

Same as intro block (shared endpoints).

