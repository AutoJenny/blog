# Newsletter Category Block

## Overview

The Category block features rotating category content with cooldown tracking.

**Purpose**: Rotate category features to avoid repetition

**Status**: ✅ Implemented

## Data Sources

- `newsletter_category_feature` table
- Filters by `approved=True`
- Rotates by `last_used_at` (least recently used first)

## Payload Structure

```json
{
  "id": 123,
  "title": "Category feature title",
  "body_html": "<p>HTML content...</p>",
  "topic": "category_topic"
}
```

## Files

- `blog-core/newsletter/selectors/category.py` - Category selection
- Uses universal block editor UI

## API Endpoints

Same as intro block (shared endpoints).

