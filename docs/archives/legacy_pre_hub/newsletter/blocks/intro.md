# Newsletter Intro Block

## Overview

The Intro block is the opening section of each newsletter issue, providing a warm welcome message with topical content aggregated from weather, events, and community sources in Scotland.

**Purpose**: Welcome message with topical content from Scotland

**Status**: ✅ Fully implemented and functional

**File Size Compliance**: All files under 500 lines ✅

## Code Organization

### Intro-Specific Files

| File | Lines | Purpose |
|------|-------|---------|
| `templates/newsletter/partials/block_editor_intro.html` | 293 | UI template with JavaScript functions |
| `blog-core/newsletter/selectors/intro.py` | 111 | Content selection logic |
| `blog-core/newsletter/rendering/intro_text.py` | 64 | Text generation from selected items |

### Shared Services (Used by All Block Types)

| File | Lines | Purpose |
|------|-------|---------|
| `blog-core/newsletter/services/block_editor_service.py` | 142 | Editor operations (get_suggestions, apply_suggestion, save_override) |
| `blog-core/newsletter/services/suggestion_service.py` | 168 | Core suggestion generation (generate_suggestions, validate_link) |
| `blog-core/newsletter/services/block_suggestion_service.py` | 211 | Unified routing to type-specific logic |

**Note**: The intro block is modular but not completely stand-alone. It shares services with other block types (snapshot, feature, etc.) for code reuse.

## Data Sources

The intro block aggregates content from three categories:

1. **Weather** (`category='weather'`)
   - Met Office forecasts and warnings
   - BBC Scotland weather reports
   - Sources: `RSSAdapter`, `WeatherHTMLAdapter`

2. **Events** (`category='event'`)
   - Historic Environment Scotland (HES) events
   - Museum and gallery exhibitions
   - Cultural events and festivals
   - Sources: `HTMLAdapter`, `PlaywrightAdapter`

3. **Community** (`category='community'`)
   - Reddit discussions from r/Scotland, r/Highlands
   - Engagement thresholds: 50+ upvotes, 10+ comments
   - Sources: `RedditAdapter`

## Payload Structure

The intro block payload is stored in `newsletter_block.payload_json`:

```json
{
  "text": "The Met Office reports: Monday 10 November - High 10°C / Low 8°C - Light rain and moderate winds. Historic Environment Scotland has announced: The Eagle and the Unicorn exhibition in Edinburgh. If you're nearby, it's worth a look.",
  "suggestions": [
    {
      "id": 467,
      "source_name": "Met Office",
      "title": "Monday 10 November - High 10°C / Low 8°C - Light rain",
      "url": "https://www.metoffice.gov.uk/weather/forecast/...",
      "category": "weather",
      "combined_score": 13.6,
      "signal_score": 9.0,
      "freshness_score": 4.6,
      "location": null,
      "published_at": null,
      "event_date": null
    },
    {
      "id": 123,
      "source_name": "Historic Environment Scotland",
      "title": "The Eagle and the Unicorn",
      "url": "https://www.historicenvironment.scot/...",
      "category": "event",
      "combined_score": 10.3,
      "location": "Edinburgh"
    }
  ],
  "selected": {
    "id": 467,
    "source_name": "Met Office",
    "category": "weather",
    ...
  },
  "items_by_category": {
    "weather": {
      "id": 467,
      "source_name": "Met Office",
      ...
    },
    "event": {
      "id": 123,
      "source_name": "Historic Environment Scotland",
      ...
    },
    "community": null
  },
  "manual_override": false
}
```

## File Details

### 1. Template: `block_editor_intro.html` (293 lines)

**Location**: `templates/newsletter/partials/block_editor_intro.html`

**Structure**:
- HTML template with inline styles
- Embedded JavaScript functions (lines 107-291)
- Jinja2 template variables: `{{ b.id }}`, `{{ issue_id }}`, `{{ b.payload_json }}`

**JavaScript Functions**:

1. **`loadSuggestions(blockId, blockType)`** (lines 108-207)
   - Fetches suggestions from API endpoint
   - Shows loading state
   - Renders suggestions list with scores
   - Handles errors gracefully
   - Uses selector: `.block-editor-intro[data-block-id="${blockId}"]`

2. **`applySuggestion(blockId, suggestionId, blockType)`** (lines 209-238)
   - Applies selected suggestion to block
   - Updates block payload via API
   - Reloads page to show updated content

3. **`saveOverride(blockId, blockType)`** (lines 240-268)
   - Saves manual text override
   - Sets `manual_override: true` in payload
   - Updates preview display

4. **`clearOverride(blockId, blockType)`** (lines 270-272)
   - Clears manual override textarea
   - Does not save (user must click "Save Override")

5. **`loadPreview(blockId, blockType)`** (lines 274-291)
   - Fetches rendered HTML preview
   - Displays in preview section

**Key Features**:
- Current content preview section
- Auto-select toggle (checkbox)
- "Regenerate Suggestions" button
- Suggestions list with "Use This" buttons
- Manual override textarea
- Preview toggle (collapsible)

### 2. Selector: `selectors/intro.py` (111 lines)

**Location**: `blog-core/newsletter/selectors/intro.py`

**Main Function**: `select_intro_content(*, target_week: str) -> Dict[str, Any]`

**Process**:
1. Calls `generate_suggestions(block_type='intro', target_week=target_week, count=9, skip_validation=True)`
2. Groups suggestions by category (weather, event, community)
3. Selects top item from each category
4. Falls back to top items if category-specific selection fails
5. Generates intro text using `generate_intro_text()`
6. Returns dict with suggestions, selected items, text, and items_by_category

**Dependencies**:
- `newsletter.services.suggestion_service.generate_suggestions()`
- `newsletter.rendering.intro_text.generate_intro_text()`
- `newsletter.services.scoring.apply_diversity_rules()`

### 3. Text Generation: `rendering/intro_text.py` (64 lines)

**Location**: `blog-core/newsletter/rendering/intro_text.py`

**Main Function**: `generate_intro_text(weather_item, event_item, community_item) -> str`

**Process**:
1. Builds sentences from available items
2. Weather: "The Met Office reports: {title}" or "{source} reports: {title}"
3. Event: "{source} has announced: {title} in {location}." (if location) or "{source} has announced: {title}."
4. Community: "A fun discussion on {source}: {title}" (if Reddit) or "{source}: {title}"
5. Joins sentences with ". " separator
6. Adds closing phrase "If you're nearby, it's worth a look." if multiple sentences
7. Fallback: "A quick wander through culture & craft from Scotland this week."

**Tone**: Warm, observational, with inline attribution

## API Endpoints

### Get Suggestions
```
GET /newsletter/issue/:issue_id/block/:block_id/suggestions
```

**Returns**:
```json
{
  "suggestions": [
    {
      "id": 467,
      "source_name": "Met Office",
      "title": "...",
      "url": "...",
      "category": "weather",
      "combined_score": 13.6,
      ...
    }
  ],
  "current": {
    "id": 467,
    ...
  },
  "metadata": {
    "items_by_category": {...},
    "text": "Generated intro text..."
  }
}
```

**Implementation**: `blueprints/newsletter.py::get_block_suggestions()` → `block_editor_service.get_suggestions()` → `block_suggestion_service.get_suggestions_for_block()` → `selectors/intro.select_intro_content()`

### Apply Suggestion
```
POST /newsletter/issue/:issue_id/block/:block_id/select-suggestion
Body: {"suggestion_id": 123}
```

**Implementation**: `blueprints/newsletter.py::select_block_suggestion()` → `block_editor_service.apply_suggestion()` → `selectors/intro.select_intro_content()` → `rendering/intro_text.generate_intro_text()`

### Save Override
```
POST /newsletter/issue/:issue_id/block/:block_id/override
Body: {"text": "Custom intro text..."}
```

**Implementation**: `blueprints/newsletter.py::override_block_text()` → `block_editor_service.save_override()` → Updates `newsletter_block.payload_json`

### Preview
```
GET /newsletter/issue/:issue_id/block/:block_id/preview
```

**Returns**: `{"html": "..."}` (currently returns payload, full HTML rendering TODO)

## Suggestion Flow

1. **User clicks "Regenerate Suggestions"**
   - JavaScript calls `loadSuggestions(blockId, 'intro')`
   - Fetches from `/newsletter/issue/{issueId}/block/{blockId}/suggestions`

2. **Backend Processing**
   - `get_suggestions()` → `get_suggestions_for_block()` → `select_intro_content()`
   - `select_intro_content()` calls `generate_suggestions(block_type='intro', count=9, skip_validation=True)`
   - `generate_suggestions()`:
     - Fetches cached items from `newsletter_source_item` (last 14 days, limit 200)
     - Scores items using `score_items()` (freshness + signal)
     - Applies diversity rules (max 1 per category)
     - Skips link validation (cached items already validated)
     - Returns top 9 suggestions

3. **Content Selection**
   - Groups suggestions by category (weather, event, community)
   - Selects top item from each category
   - Generates intro text using `generate_intro_text()`
   - Returns formatted payload with suggestions, selected items, and text

4. **UI Display**
   - JavaScript renders suggestions list with scores
   - Shows "Use This" button for each suggestion
   - Displays current content preview

## Auto-Select Behavior

When auto-select is enabled (default):
- Top-scored suggestion from each category is automatically selected
- Intro text is generated from selected items
- Content is stored in block payload

Editor can:
- Disable auto-select to manually choose from suggestions
- Override generated text manually via textarea
- Mix both (select suggestion but edit text)

## Error Handling

**JavaScript**:
- Validates DOM elements exist before use
- Checks content-type before parsing JSON
- Shows specific error messages in UI
- Handles network errors gracefully

**Backend**:
- Returns helpful error messages if no suggestions available
- Logs errors with context
- Provides fallback text if generation fails

## Dependencies

**Intro-Specific**:
- `selectors/intro.py` → `rendering/intro_text.py`
- `selectors/intro.py` → `services/suggestion_service.py`
- `selectors/intro.py` → `services/scoring.py`

**Shared Services**:
- `services/block_editor_service.py` (used by all block types)
- `services/suggestion_service.py` (used by all block types)
- `services/block_suggestion_service.py` (used by all block types)
- `db/queries_sources.py` (used by all block types)

## Testing

To test the intro block:

1. **Check for cached items**:
   ```sql
   SELECT COUNT(*) FROM newsletter_source_item 
   WHERE category IN ('weather', 'event', 'community') 
   AND cached_at >= NOW() - INTERVAL '14 days';
   ```

2. **Test suggestion generation**:
   ```python
   from newsletter.selectors.intro import select_intro_content
   result = select_intro_content(target_week='2025W44')
   print(f"Suggestions: {len(result['suggestions'])}")
   print(f"Text: {result['text']}")
   ```

3. **Test via API**:
   ```bash
   curl http://localhost:5000/newsletter/issue/8/block/31/suggestions
   ```

## Future Enhancements

- [ ] Rich text editor for override (instead of plain textarea)
- [ ] Suggestion history/cooldown tracking
- [ ] Custom scoring weights for intro block
- [ ] Preview rendering improvements
- [ ] Batch suggestion refresh for all blocks

