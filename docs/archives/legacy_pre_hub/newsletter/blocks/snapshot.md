# Newsletter Snapshot Block ("In the News")

## Overview

The Snapshot block (displayed as "In the News" in UI and Preview) provides a chatty overview of recent news and events from external sources, compiled into two conversational paragraphs with embedded links.

**Purpose**: Chatty overview of news and events with embedded source links

**Display Name**: "In the News" (renamed from "Scottish Snapshot")

**Status**: ✅ Implemented

## Structure

The block uses a modular component approach:
1. **News Component**: Fetches top 5 news items from cached sources
2. **Events Component**: Fetches top 5 event items from cached sources
3. **Compile Function**: Uses LLM to generate two chatty paragraphs (one for news, one for events) with embedded markdown links

## Data Sources

- **News**: BBC Scotland, The Herald, The Scotsman (from `newsletter_source_item` table)
- **Events**: Historic Environment Scotland, VisitScotland, National Museums/Galleries (from `newsletter_source_item` table)
- Items are filtered to last 14 days and sorted by `combined_score`

## Payload Structure

```json
{
  "news_items": [
    {
      "id": 123,
      "title": "Story title",
      "url": "https://...",
      "source_name": "BBC Scotland",
      "summary": "...",
      "published_at": "2025-01-01T00:00:00",
      "combined_score": 15.2
    }
  ],
  "events_items": [
    {
      "id": 456,
      "title": "Event title",
      "url": "https://...",
      "source_name": "HES",
      "location": "Edinburgh",
      "summary": "...",
      "event_date": "2025-01-15T00:00:00",
      "combined_score": 12.8
    }
  ],
  "news_paragraph": "Chatty paragraph about news stories with [embedded links](url)...",
  "events_paragraph": "Chatty paragraph about events with [embedded links](url)...",
  "compiled_at": "2025-01-09T12:00:00"
}
```

## Files

- `templates/newsletter/partials/block_editor_snapshot.html` - UI template with component modules
- `templates/newsletter/partials/snapshot.html` - Preview template
- `blueprints/newsletter.py` - API endpoints for component generation and compilation

## API Endpoints

- `GET /newsletter/issue/:issue_id/block/:block_id/generate-news` - Generate news component (returns top 5 items)
- `GET /newsletter/issue/:issue_id/block/:block_id/generate-snapshot-events` - Generate events component (returns top 5 items)
- `POST /newsletter/issue/:issue_id/block/:block_id/compile-snapshot` - Compile both components into two chatty paragraphs using LLM

## LLM Generation

The compile function uses LLM to:
- Review all news and events items from both components
- Generate a chatty news paragraph (3-5 sentences) with embedded markdown links
- Generate a chatty events paragraph (3-5 sentences) with embedded markdown links
- Identify related/overlapping topics and mention them together naturally
- Use conversational, engaging language

**No fallbacks** - if LLM fails, returns an error message.

