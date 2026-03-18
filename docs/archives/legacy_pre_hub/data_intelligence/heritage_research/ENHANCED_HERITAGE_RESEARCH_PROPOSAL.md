# Enhanced Heritage Research System - Proposal

## Overview

Transform the heritage data research from a superficial LLM-only process into a comprehensive, multi-stage research project that produces authentic, insightful, and well-sourced information about each category's Scottish heritage.

## Current State

**Limitations:**
- LLM generates text from its training data only (no external sources)
- No web research implementation (placeholder)
- Results are generic and lack depth
- No source attribution or credibility validation
- Missing "Industrial Legacy" section
- No synthesis of multiple sources

## Proposed Enhanced Architecture

### Research Dimensions

Each category will be researched across **5 dimensions**:

1. **Historical Origins** - When, where, and how the category emerged in Scotland
2. **Cultural Significance** - Role in Scottish culture, traditions, and identity
3. **Evolution** - How the category has changed over time
4. **Scottish Heritage Connections** - Links to clans, regions, events, traditions
5. **Industrial Legacy** (NEW) - Famous producers, manufacturing processes, regional specializations

### Multi-Stage Research Process

#### Stage 1: Research Planning & Query Generation

**Purpose:** LLM creates specific, targeted search queries for each dimension

**Process:**
1. Input: Category name, full hierarchy path (e.g., "CLAN Main Category > Products > Men > Shirts")
2. LLM generates 3-5 specific search queries per dimension, contextualized to:
   - The category hierarchy
   - Scottish context
   - Historical/cultural focus
   - Credible source targeting

**Example Queries for "Shirts" category:**
- Historical Origins: "history of Scottish tartan shirts 18th century", "Jacobite shirt origins Scotland", "traditional Scottish menswear shirts"
- Cultural Significance: "tartan shirts Scottish clan identity", "Scottish shirt cultural traditions", "Highland dress shirts significance"
- Evolution: "evolution of Scottish shirt design 19th century", "modern Scottish shirt manufacturing", "tartan shirt contemporary fashion"
- Scottish Heritage Connections: "Scottish shirt makers clans", "regional shirt traditions Scotland", "Scottish shirt festivals traditions"
- Industrial Legacy: "famous Scottish shirt manufacturers", "Scottish textile industry shirt production", "traditional Scottish shirt making techniques"

**Output:** Structured query plan with queries per dimension

#### Stage 2: Web Research Execution

**Purpose:** Harvest information from credible sources

**Credible Source Criteria:**
- **Academic:** Universities, research institutions, scholarly articles
- **Cultural Institutions:** Museums (National Museum of Scotland, V&A, etc.), heritage organizations
- **Government:** Historic Environment Scotland, VisitScotland heritage content
- **Established Media:** BBC Scotland, The Scotsman (heritage sections), Scottish history publications
- **Specialist Sites:** Scottish Textile Heritage, Clan societies, Scottish cultural organizations
- **Exclude:** Personal blogs, commercial sites without heritage focus, unverified sources

**Implementation Strategy (Free-First Approach):**

**Primary: Wikipedia API** (Free, Unlimited)
- Start with Wikipedia for structured overview
- Extract references to external credible sources
- Use Wikipedia content as foundation
- No rate limits for reasonable use

**Secondary: Google Custom Search API** (Free Tier: 100 queries/day)
- Use sparingly for deeper research when Wikipedia insufficient
- Restrict to credible domains (.ac.uk, .gov.uk, museum domains)
- Prioritize museum and academic sources
- Track daily query usage to stay within free tier

**Tertiary: Direct Source Access** (Free)
- National Library of Scotland digital collections (if accessible)
- Historic Environment Scotland content
- Museum websites (respectful scraping, robots.txt compliant)

**Fallback: LLM-Enhanced Research**
- If free APIs insufficient or rate-limited, use LLM to generate research
- Base on Wikipedia content + product data + category context
- Clearly mark research as "LLM-enhanced" vs. "web-sourced"

**Process:**
1. Execute each query from Stage 1
2. Filter results by credibility criteria
3. Extract relevant snippets (with source attribution)
4. Collect 10-20 high-quality sources per dimension
5. Store raw research data for synthesis

**Output:** Raw research data per dimension (snippets only, not full content):
```json
{
  "historical_origins": {
    "sources": [
      {
        "title": "The History of Scottish Tartan",
        "url": "https://...",
        "domain": "nms.ac.uk",
        "credibility": "high",
        "snippets": [
          "Scottish tartan shirts emerged in the 18th century...",
          "The Jacobite shirt, also known as Ghillie shirt..."
        ],
        "relevance_score": 0.95,
        "source_type": "museum"  // museum, academic, government, wikipedia
      }
    ],
    "total_sources": 15,
    "research_date": "2025-01-11",
    "research_method": "wikipedia_api"  // wikipedia_api, google_search, llm_enhanced
  },
  ...
}
```

#### Stage 3: LLM Synthesis & Analysis

**Purpose:** Transform raw research into coherent, insightful narratives

**Process:**
1. For each dimension, provide LLM with:
   - All collected sources and snippets
   - Category context and hierarchy
   - Product data from category (for relevance)
   - Instructions to synthesize, identify key themes, and highlight significant elements

2. LLM creates:
   - **Main narrative** (300-500 words): Coherent story synthesizing all sources
   - **Key themes** (bullet points): Major themes identified across sources
   - **Significant elements** (bullet points): Interesting facts, dates, people, events
   - **Source summary**: Which sources contributed most valuable information

3. Quality checks:
   - Verify claims can be traced to sources
   - Flag any contradictions between sources
   - Ensure Scottish context is maintained
   - Check for interesting/unique insights (not just generic information)

**Output:** Synthesized heritage data per dimension

#### Stage 4: Final Assembly & Validation

**Purpose:** Combine all dimensions into final heritage data structure

**Process:**
1. Assemble all 5 dimensions
2. Cross-reference for consistency
3. Add metadata:
   - Research date
   - Source count per dimension
   - Credibility scores
   - Research depth indicator
4. Store in database with full source attribution

**Final Structure:**
```json
{
  "historical_origins": {
    "narrative": "...",
    "key_themes": ["...", "..."],
    "significant_elements": ["...", "..."],
    "source_count": 15,
    "research_date": "2025-01-11"
  },
  "cultural_significance": { ... },
  "evolution": { ... },
  "scottish_heritage_connections": { ... },
  "industrial_legacy": {
    "narrative": "...",
    "famous_historical_producers": ["...", "..."],  // Historical only, not modern
    "historical_manufacturing_processes": ["...", "..."],
    "regional_specializations": ["...", "..."],
    "key_themes": ["...", "..."],
    "source_count": 12
  },
  "research_metadata": {
    "total_sources": 67,
    "research_date": "2025-01-11",
    "researcher_version": "2.0",
    "credibility_score": 0.92,
    "depth_level": "comprehensive"
  },
  "sources": [
    {
      "title": "...",
      "url": "...",
      "domain": "...",
      "credibility": "high",
      "dimensions_used": ["historical_origins", "cultural_significance"]
    }
  ]
}
```

## Technical Implementation

### New Components Needed

1. **Query Generator Module** (`query_generator.py`)
   - LLM-powered query generation
   - Context-aware query creation
   - Query validation and refinement

2. **Web Research Module** (`web_researcher.py`)
   - Search API integration
   - Source credibility filtering
   - Snippet extraction
   - Source attribution

3. **Research Synthesizer Module** (`research_synthesizer.py`)
   - LLM-powered synthesis
   - Theme extraction
   - Significance identification
   - Quality validation

4. **Source Manager** (`source_manager.py`)
   - Source storage and retrieval
   - Credibility scoring
   - Source deduplication
   - Citation management

### Database Schema Updates

**New Table: `heritage_research_sources`**
```sql
CREATE TABLE heritage_research_sources (
    id SERIAL PRIMARY KEY,
    category_id INTEGER REFERENCES clan_categories(id),
    dimension VARCHAR(50),  -- historical_origins, cultural_significance, etc.
    title TEXT,
    url TEXT,
    domain VARCHAR(255),
    credibility_score DECIMAL(3,2),
    snippets JSONB,  -- Array of relevant text snippets
    research_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_heritage_sources_category ON heritage_research_sources(category_id, dimension);
```

**Update `clan_categories.heritage_data` structure:**
- Add `industrial_legacy` section
- Add `research_metadata` section
- Add `sources` array
- Add `key_themes` and `significant_elements` to each dimension

### API Integration Requirements

**Search API Options:**
1. **Google Custom Search API** (Recommended)
   - Free tier: 100 queries/day
   - Paid: $5 per 1000 queries
   - Can restrict to specific domains (.ac.uk, .gov.uk, etc.)

2. **Serper.dev** (Alternative)
   - $50/month for 10,000 queries
   - Good for structured results
   - Easy integration

3. **Bing Search API**
   - Free tier: 3,000 queries/month
   - Can filter by domain

**Wikipedia API** (Free)
- Structured data
- References to sources
- Good starting point

## Benefits

1. **Authenticity:** Real sources, not just LLM training data
2. **Depth:** Comprehensive research across multiple dimensions
3. **Credibility:** Source attribution and credibility scoring
4. **Insight:** Synthesis identifies key themes and significant elements
5. **Reusability:** Rich data supports both product posts and category-level posts
6. **Industrial Context:** New "Industrial Legacy" section adds manufacturing/craftsmanship dimension
7. **Future-Proof:** Structured data can be updated as new sources emerge

## Implementation Phases

### Phase 1: Foundation - Wikipedia Integration (Week 1)
- Set up Wikipedia API integration (free, unlimited)
- Create query generator module
- Implement Wikipedia content extraction
- Extract Wikipedia references to external sources
- Implement basic source filtering and credibility scoring
- Test with one category (Shirts)

### Phase 2: Synthesis & Structure (Week 2)
- Create research synthesizer module
- Implement LLM synthesis prompts
- Add theme and significance extraction
- Create 5-dimension structure (including Industrial Legacy)
- Test synthesis quality

### Phase 3: Google Search Integration (Week 3)
- Set up Google Custom Search API (free tier: 100/day)
- Implement query usage tracking
- Add domain filtering (.ac.uk, .gov.uk, museums)
- Integrate with Wikipedia research as fallback
- Test with multiple categories

### Phase 4: Source Management & Polish (Week 4)
- Add source management and storage (snippets only)
- Implement credibility scoring system
- Create research metadata tracking
- Add "research_method" tracking (wikipedia, google, llm_enhanced)
- Test on-demand regeneration workflow

## Additional Ideas

### 1. Regional Specialization Research
- Identify if category has regional variations (e.g., "Harris Tweed" for textiles)
- Map regional manufacturing centers
- Document regional traditions

### 2. Timeline Development
- Create chronological timeline of category evolution
- Key dates, events, innovations
- Visual timeline for category posts

### 3. Cross-Category Connections
- Identify relationships between categories
- E.g., "Shirts" connects to "Tartan", "Clan Crests", "Highland Dress"
- Build category relationship graph

### 4. Contemporary Relevance
- How category remains relevant today
- Modern adaptations
- Current cultural significance

### 5. Research Refresh Strategy
- Periodic re-research (e.g., annually)
- Track source freshness
- Update when new sources emerge

### 6. Research Quality Metrics
- Source diversity score
- Credibility average
- Coverage completeness
- Synthesis coherence

## Decisions Made

1. **Search API Budget:** Limited - focus on free resources. Use Wikipedia API (free) as primary source, with Google Custom Search free tier (100 queries/day) as secondary. Request permission with defined budget if paid API needed.

2. **Research Frequency:** Currently on-demand only via regenerate button. Existing heritage data is considered evergreen and does not need regeneration when new products in the category are posted. **Note:** Research frequency is configurable and can be updated in the future when product profiling calendar schedule is in place (e.g., scheduled regeneration, refresh intervals).

3. **Source Storage:** Store snippets only (not full content), with source attribution (title, URL, domain, credibility score).

4. **Manual Review:** Not required - system generates and saves directly.

5. **Category Priority:** On-demand as products are posted weekly. Research triggered when user clicks "Regenerate" button for a category.

6. **Industrial Legacy Scope:** Historical only - focus on traditional producers, historical manufacturing processes, and regional specializations. Exclude modern manufacturers.

7. **Synthesis Length:** 300-500 words per dimension narrative, with key themes and significant elements as bullet points.

## Free Resource Strategy

### Primary: Wikipedia API (Free, Unlimited)
- Structured data and references
- Good coverage of Scottish heritage topics
- Can extract references to external sources
- No rate limits for reasonable use

### Secondary: Google Custom Search API (Free Tier)
- 100 queries per day free
- Can restrict to credible domains (.ac.uk, .gov.uk, museum domains)
- Use sparingly for deeper research when Wikipedia insufficient

### Tertiary: Direct Source Access (Free)
- National Library of Scotland digital collections
- Historic Environment Scotland content
- Museum websites (scraping with respect to robots.txt)

### Fallback: LLM-Enhanced Research
- If free APIs insufficient, use LLM to generate research based on:
  - Wikipedia content
  - Product data in category
  - Category hierarchy context
- Clearly mark when research is LLM-only vs. web-sourced

## Next Steps

1. ✅ Decisions finalized
2. Implement Wikipedia API integration (Phase 1)
3. Design database schema updates
4. Create implementation plan with free-resource focus
5. Begin Phase 1 implementation

