# Heritage Research System - Quick Reference

## What It Does

Generates authentic, well-sourced historical and cultural context for product categories (e.g., "Shirts", "Kilts", "Plaques"). Each category gets 5 dimensions of heritage data:

1. **Historical Origins** - When/how it emerged in Scotland
2. **Cultural Significance** - Role in Scottish traditions
3. **Evolution** - How it changed over time
4. **Scottish Heritage Connections** - Clans, regions, events
5. **Industrial Legacy** - Historical producers/processes

## How to Use

### Regenerate Heritage Data (UI)
1. Go to product data review page: `/planning/posts/{post_id}/calendar/product-data-review`
2. Click "Regenerate" button in Heritage Data section
3. Wait for completion (page reloads)

### Regenerate Heritage Data (Code)
```python
from utils.category_heritage_research import CategoryHeritageResearcher
from utils.database import get_db_connection

db = get_db_connection()
researcher = CategoryHeritageResearcher(db)
heritage_data = researcher.derive_category_context(category_id=106)
researcher.save_heritage_data(category_id=106, heritage_data=heritage_data)
```

### Check Heritage Data
```python
from utils.database import get_db_connection
import json

db = get_db_connection()
with db.cursor() as cur:
    cur.execute("SELECT heritage_data FROM clan_categories WHERE id = %s", (106,))
    row = cur.fetchone()
    if row and row[0]:
        heritage = json.loads(row[0]) if isinstance(row[0], str) else row[0]
        print(json.dumps(heritage, indent=2))
```

## Key Files

- **Main Class**: `utils/category_heritage_research.py` - `CategoryHeritageResearcher`
- **Research Modules**: `utils/heritage_research/` (QueryGenerator, WikipediaResearcher, ResearchSynthesizer)
- **UI Endpoint**: `blueprints/planning_calendar_product_data_review.py` - `api_regenerate_heritage_data()`
- **UI Template**: `templates/planning/calendar/product_data_review.html`
- **Config**: `utils/heritage_research/config.py`

## Data Format

Each dimension stored as:
```json
{
  "narrative": "300-500 word text...",
  "key_themes": ["Theme 1", "Theme 2"],
  "significant_elements": ["Factoid 1", "Factoid 2"],
  "source_count": 5,
  "research_date": "2024-01-15T10:30:00"
}
```

## Research Process

1. **Query Generation** → LLM creates Wikipedia search queries
2. **Wikipedia Research** → Fetches full article content
3. **Synthesis** → LLM extracts facts and creates narrative
4. **Storage** → Saves to `clan_categories.heritage_data` (JSONB)

## Current Issues

### ⚠️ Truncated Outputs (Mid-Sentence)

**Problem**: Narratives stop mid-sentence.

**Root Cause**: `blueprints/llm_actions.py:55` - `max_tokens: 2000` is too low for 300-500 word narratives + JSON structure.

**Fix**: Increase `max_tokens` to 4000-6000 for synthesis requests.

**Also**: `utils/heritage_research/research_synthesizer.py:202` has `[:1000]` character limit in fallback method.

## Future Improvements

1. **Keyword-Based System**: Replace full narratives with intro + keywords (tartan, Harris Tweed, etc.) for better granularity and cross-category linking via vector analysis.

2. **Google Search Integration**: Add as secondary source when Wikipedia insufficient (Phase 3).

3. **Source Management**: Store source snippets with metadata and citations (Phase 4).

## Configuration

- **Research Frequency**: `on_demand` (configurable in `config.py` for future calendar integration)
- **Wikipedia**: Free, unlimited (enabled)
- **Google Search**: Configured but disabled (Phase 3)

## Testing

```python
# Test research
researcher = CategoryHeritageResearcher(db, use_enhanced_research=True)
heritage_data = researcher.derive_category_context(category_id=106)

# Check for truncation
for dim in heritage_data:
    if isinstance(heritage_data[dim], dict) and heritage_data[dim].get('narrative'):
        narrative = heritage_data[dim]['narrative']
        if narrative and narrative[-1] not in '.!?':
            print(f"WARNING: {dim} may be truncated!")
```

## Full Documentation

See `SYSTEM_DOCUMENTATION.md` for complete details.

