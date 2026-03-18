# Heritage Research System - Complete Documentation

## Overview

The Heritage Research System generates authentic, well-sourced historical and cultural context for product categories in the CLAN.com database. It uses a multi-stage research process combining LLM-powered query generation, web research (Wikipedia API), and intelligent synthesis to produce comprehensive heritage narratives.

## System Architecture

### Core Components

1. **`CategoryHeritageResearcher`** (`utils/category_heritage_research.py`)
   - Main orchestrator class
   - Coordinates the research pipeline
   - Handles database storage and retrieval
   - Provides both enhanced and legacy research methods

2. **Enhanced Research Modules** (`utils/heritage_research/`)
   - `QueryGenerator`: Generates targeted search queries for each heritage dimension
   - `WikipediaResearcher`: Fetches and extracts content from Wikipedia articles
   - `SourceFilter`: Filters sources by credibility (currently basic, can be enhanced)
   - `ResearchSynthesizer`: Synthesizes raw research into coherent narratives

3. **UI Integration**
   - `blueprints/planning_calendar_product_data_review.py`: API endpoint for regeneration
   - `templates/planning/calendar/product_data_review.html`: Display template
   - `static/css/planning/product-data-review.css`: Styling

## Data Structure

### Heritage Dimensions

Each category's heritage data contains 5 dimensions:

1. **`historical_origins`**: When and how the category emerged in Scotland
2. **`cultural_significance`**: Role in Scottish traditions, identity, and heritage
3. **`evolution`**: How the category has changed over time
4. **`scottish_heritage_connections`**: Connections to clans, regions, events, traditions
5. **`industrial_legacy`**: Historical producers, manufacturing processes, regional specializations (historical only)

### Data Format

Each dimension is stored as a dictionary:

```json
{
  "narrative": "300-500 word synthesized narrative...",
  "key_themes": ["Theme 1", "Theme 2", "Theme 3"],
  "significant_elements": ["Element 1", "Element 2", "Element 3"],
  "source_count": 5,
  "research_date": "2024-01-15T10:30:00"
}
```

**Legacy Format Support**: The system also supports legacy string format for backward compatibility.

### Database Storage

Heritage data is stored in the `clan_categories` table:
- Column: `heritage_data` (JSONB)
- Updated via: `CategoryHeritageResearcher.save_heritage_data()`
- Metadata: `llm_analyzed_at`, `web_researched_at` timestamps

## Research Process Flow

### Enhanced Research (Current Default)

```
1. Category Context Gathering
   ├─ Get category hierarchy path (e.g., "Menswear > Shirts")
   ├─ Get category description
   └─ Prepare context for research

2. Query Generation (per dimension)
   ├─ LLM generates Wikipedia article titles/search terms
   ├─ Focus: Scottish context + specific dimension
   └─ Output: List of targeted queries

3. Wikipedia Research (per dimension)
   ├─ Search Wikipedia for each query
   ├─ Fetch FULL page content (not snippets)
   ├─ Extract relevant sections based on dimension keywords
   └─ Collect references to external sources

4. Source Filtering
   ├─ Filter by credibility (basic implementation)
   └─ Limit to top 5 sources per dimension

5. Synthesis (per dimension)
   ├─ LLM reads full Wikipedia article content
   ├─ Extracts specific factual information (dates, names, places, events)
   ├─ Creates 300-500 word narrative
   ├─ Identifies 3-5 key themes
   └─ Identifies 3-5 significant elements (factoids)

6. Data Assembly
   ├─ Combine all dimensions
   ├─ Add metadata (research date, source counts)
   └─ Prepare for database storage
```

### Legacy Research (Fallback)

If enhanced research modules are unavailable, the system falls back to:
- Direct LLM analysis of product data
- No web research
- Simpler output format

## Key Files and Functions

### Main Research Class

**`CategoryHeritageResearcher`** (`utils/category_heritage_research.py`)

- `__init__(db_connection, llm_service, use_enhanced_research=True)`: Initialize researcher
- `get_category_path(category_id)`: Get category hierarchy (e.g., ["Menswear", "Shirts"])
- `derive_category_context(category_id)`: Main entry point - generates heritage data
- `save_heritage_data(category_id, heritage_data)`: Save to database
- `_derive_category_context_enhanced()`: Enhanced research pipeline
- `_derive_category_context_legacy()`: Legacy fallback

### Query Generation

**`QueryGenerator`** (`utils/heritage_research/query_generator.py`)

- `generate_queries(dimension, category_name, hierarchy_context)`: Generate Wikipedia search queries
- Uses LLM to create specific article titles (e.g., "Tartan" not "Scottish tartan shirts")
- Focuses on comprehensive articles about each dimension

### Wikipedia Research

**`WikipediaResearcher`** (`utils/heritage_research/wikipedia_researcher.py`)

- `search(query, max_results=5)`: Search Wikipedia and fetch page summaries
- `get_page(title)`: Fetch FULL Wikipedia page content (`page.text`)
- `research_dimension(dimension, queries)`: Research a specific dimension
  - Fetches full page content for top articles
  - Extracts relevant sections using dimension keywords
  - Returns structured source data with full content

### Synthesis

**`ResearchSynthesizer`** (`utils/heritage_research/research_synthesizer.py`)

- `synthesize_dimension(dimension, sources, category_name, hierarchy_context)`: Main synthesis
- `_build_synthesis_prompt()`: Creates detailed LLM prompt
- `_simple_synthesis()`: Fallback if LLM fails

**Synthesis Prompt Instructions:**
- Read full source content carefully
- Extract specific factual information (dates, names, places, events, processes)
- Focus only on information relevant to the dimension
- Create 300-500 word narrative
- Identify 3-5 key themes
- Identify 3-5 significant elements (specific factoids)

## Configuration

### Research Frequency

Currently set to **`on_demand`** (regenerate via button click).

Location: `utils/heritage_research/config.py`

```python
RESEARCH_FREQUENCY = os.getenv('HERITAGE_RESEARCH_FREQUENCY', 'on_demand')
```

**Future**: Can be changed to support scheduled regeneration (e.g., weekly, monthly) for integration with product profiling calendar.

### Wikipedia Settings

- **API**: `wikipedia-api` library (free, unlimited)
- **Language**: English (`en`)
- **User Agent**: Required by Wikipedia (set in `WikipediaResearcher.__init__`)

### Google Search (Planned - Phase 3)

- **Status**: Configured but disabled
- **Free Tier**: 100 queries/day
- **Enable**: Set `GOOGLE_SEARCH_ENABLED=true` environment variable
- **Credentials**: `GOOGLE_SEARCH_API_KEY`, `GOOGLE_SEARCH_ENGINE_ID`

## API Endpoints

### Regenerate Heritage Data

**Endpoint**: `POST /api/planning/regenerate-heritage-data`

**Parameters**:
- `category_id` (required): Category ID to regenerate

**Response**:
- `success`: Boolean
- `message`: Status message
- `category_id`: Category ID

**Usage**: Triggered by "Regenerate" button on product data review page.

## UI Display

### Template Logic

**File**: `templates/planning/calendar/product_data_review.html`

The template:
1. Checks if heritage data exists for any dimension
2. Displays categories section (always visible)
3. Displays heritage section (only if heritage data exists)
4. Shows each dimension with:
   - Narrative (main text)
   - Key themes (bulleted list)
   - Significant elements (bulleted list)
   - Source count and research date

**Important**: Template uses `if` (not `elif`) to check all dimensions, ensuring heritage data displays if ANY dimension has content.

### Styling

**File**: `static/css/planning/product-data-review.css`

- `.heritage-section`: Yellow/amber background
- `.heritage-item`: Individual dimension display
- `.heritage-note`: Narrative text
- `.heritage-themes`: Key themes list
- `.heritage-elements`: Significant elements list

## Known Issues and Future Improvements

### ⚠️ Critical Issue: Truncated Outputs

**Problem**: Heritage narratives stop mid-sentence in the UI.

**Root Causes**:
1. **Token Limits**: LLM responses may be truncated by token limits
2. **Arbitrary Shortening**: `_simple_synthesis()` fallback uses `[:1000]` character limit (line 202 in `research_synthesizer.py`)
3. **Database Storage**: No explicit truncation, but JSONB may have size limits

**Location of Truncation**:
1. **LLM Token Limit**: `blueprints/llm_actions.py:55` - Hardcoded `max_tokens: 2000` for OpenAI requests
   - A 300-500 word narrative + themes + elements in JSON format can easily exceed 2000 tokens
   - This is the PRIMARY cause of mid-sentence truncation
2. **Fallback Method**: `utils/heritage_research/research_synthesizer.py:202` - `[:1000]` character limit in `_simple_synthesis()`
   - Only used if LLM fails, but still problematic

**Action Required**:
1. **Increase LLM max_tokens**: Change `max_tokens` in `execute_llm_request()` to at least 4000-6000 for synthesis requests
   - Consider making it configurable per request type
   - Or add a parameter to `execute_llm_request()` to allow custom max_tokens
2. **Remove arbitrary character limits**: Remove `[:1000]` limit in `_simple_synthesis()`
3. **Add validation**: Detect truncated narratives (check if ends with proper punctuation)
4. **Verify database**: Check JSONB column size limits (should be fine, but verify)

### 🔮 Future Enhancement: Keyword-Based System

**Proposed Approach**: Move from full narrative text to structured keyword-based system.

**Structure**:
```json
{
  "narrative": "Brief introduction (100-200 words)...",
  "keywords": {
    "tartan": {
      "description": "Brief description...",
      "relevance": "Connection to category...",
      "sources": ["source1", "source2"]
    },
    "harris_tweed": {
      "description": "Brief description...",
      "relevance": "Connection to category...",
      "sources": ["source1", "source2"]
    }
  }
}
```

**Benefits**:
- More granular, searchable data
- Can identify shared concepts across categories (via vector analysis)
- Easier to link related topics
- More flexible for future content generation

**Implementation Notes**:
- Use vector embeddings to identify shared concepts (e.g., "tartan", "Harris Tweed")
- Extract keywords from research sources
- Link keywords across categories
- Maintain narrative for human readability

### Other Planned Improvements

1. **Google Search Integration** (Phase 3)
   - Add Google Custom Search as secondary source
   - Use when Wikipedia insufficient
   - Track daily query usage

2. **Source Management** (Phase 4)
   - Store source snippets with metadata
   - Credibility scoring
   - Source citation in UI

3. **Industrial Legacy Enhancement**
   - Extract specific producer names
   - Extract manufacturing processes
   - Extract regional specializations

4. **Research Quality Metrics**
   - Source count validation
   - Narrative completeness checks
   - Fact verification

## Usage Examples

### Regenerate Heritage Data for a Category

**Via UI**:
1. Navigate to product data review page
2. Click "Regenerate" button in Heritage Data section
3. Wait for completion (page reloads)

**Via Script**:
```python
from utils.category_heritage_research import CategoryHeritageResearcher
from utils.database import get_db_connection

db = get_db_connection()
researcher = CategoryHeritageResearcher(db)

# Generate heritage data
heritage_data = researcher.derive_category_context(category_id=106)

# Save to database
researcher.save_heritage_data(category_id=106, heritage_data=heritage_data)
```

**Via Command Line**:
```bash
python3 utils/category_heritage_research.py 106 --save
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

## Testing

### Test Research Process

```python
from utils.category_heritage_research import CategoryHeritageResearcher
from utils.database import get_db_connection

db = get_db_connection()
researcher = CategoryHeritageResearcher(db, use_enhanced_research=True)

# Test for a specific category
heritage_data = researcher.derive_category_context(category_id=106)

# Check output
print("Dimensions found:", list(heritage_data.keys()))
for dim in ['historical_origins', 'cultural_significance', 'evolution', 
            'scottish_heritage_connections', 'industrial_legacy']:
    if dim in heritage_data and heritage_data[dim].get('narrative'):
        print(f"\n{dim}:")
        print(f"  Narrative length: {len(heritage_data[dim]['narrative'])} chars")
        print(f"  Themes: {len(heritage_data[dim].get('key_themes', []))}")
        print(f"  Elements: {len(heritage_data[dim].get('significant_elements', []))}")
```

### Verify No Truncation

```python
# Check if narratives end mid-sentence
for dim in heritage_data:
    if isinstance(heritage_data[dim], dict) and heritage_data[dim].get('narrative'):
        narrative = heritage_data[dim]['narrative']
        # Check if ends with punctuation
        if narrative and narrative[-1] not in '.!?':
            print(f"WARNING: {dim} narrative may be truncated!")
            print(f"  Ends with: ...{narrative[-50:]}")
```

## Dependencies

- `wikipedia-api==0.8.1`: Wikipedia API access
- `beautifulsoup4`: HTML parsing (if needed)
- LLM Service: OpenAI GPT-4 or Ollama (via `LLMService`)
- PostgreSQL: Database storage (JSONB column)

## Troubleshooting

### Heritage Data Not Displaying

1. **Check template logic**: Ensure `has_heritage_data` is set correctly (uses `if` not `elif`)
2. **Check data format**: Verify heritage data is dictionary format, not string
3. **Check narrative existence**: Ensure at least one dimension has a non-empty narrative

### Research Failing

1. **Check LLM service**: Verify `LLMService` is initialized correctly
2. **Check Wikipedia API**: Verify `wikipedia-api` is installed and user agent is set
3. **Check logs**: Look for errors in application logs

### Truncated Outputs

1. **Check `_simple_synthesis()`**: Remove `[:1000]` limit if fallback is used
2. **Check LLM token limits**: Verify max tokens in LLM service configuration
3. **Check database**: Verify JSONB column size limits

## Related Documentation

- `ENHANCED_HERITAGE_RESEARCH_PROPOSAL.md`: Original proposal
- `IMPLEMENTATION_PLAN.md`: 4-phase implementation plan
- `CURRENT_IMPLEMENTATION_STATUS.md`: Current phase status
- `PHASE1_IMPLEMENTATION_STATUS.md`: Phase 1 completion details

