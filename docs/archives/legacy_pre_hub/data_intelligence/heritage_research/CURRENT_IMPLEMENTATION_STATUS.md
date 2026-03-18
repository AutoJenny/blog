# Current Heritage Research Implementation Status

## Phase Implementation

We're implementing the enhanced heritage research system in **4 phases**:

### ✅ Phase 1: Wikipedia Integration (CURRENT)
- **Status:** Implemented and integrated
- **Resources:** Wikipedia API only (free, unlimited)
- **What it does:**
  - Generates queries for all 5 dimensions
  - Searches Wikipedia for relevant articles
  - Extracts content and references
  - Synthesizes into narratives with themes/elements

### ⏳ Phase 2: Synthesis & Structure (NEXT)
- **Status:** Partially implemented (synthesis exists, needs refinement)
- **Resources:** Wikipedia API + LLM synthesis
- **What it will do:**
  - Complete synthesis implementation
  - Add Industrial Legacy specific research
  - Test synthesis quality

### 📋 Phase 3: Google Search Integration (PLANNED)
- **Status:** Not yet implemented
- **Resources:** Google Custom Search API (free tier: 100 queries/day)
- **What it will do:**
  - Add Google Custom Search as secondary source
  - Use when Wikipedia insufficient
  - Combine Wikipedia + Google results
  - Track daily query usage (stay within free tier)
  - Filter to credible domains (.ac.uk, .gov.uk, museums)

### 📋 Phase 4: Source Management & Polish (PLANNED)
- **Status:** Not yet implemented
- **Resources:** All sources (Wikipedia + Google)
- **What it will do:**
  - Complete source management system
  - Credibility scoring
  - Research metadata tracking

## Current State

**Right now, the system uses:**
- ✅ Wikipedia API (free, unlimited) - **PRIMARY SOURCE**
- ❌ Google Custom Search API - **NOT YET IMPLEMENTED** (Phase 3)

**Why Wikipedia first?**
1. Free and unlimited (no budget concerns)
2. Good coverage of Scottish heritage topics
3. Provides references to external credible sources
4. Allows us to test the research pipeline before adding paid/limited APIs

**When will Google Search be added?**
- Phase 3 (planned for Week 3 in implementation plan)
- Will be used as secondary source when Wikipedia insufficient
- Will require Google Custom Search API setup (free tier: 100 queries/day)
- Will combine results from both sources

## Research Flow (Current)

1. **Query Generation** → LLM creates queries for each dimension
2. **Wikipedia Research** → Searches Wikipedia for each query
3. **Source Filtering** → Filters by credibility
4. **Synthesis** → LLM synthesizes into narratives

## Research Flow (Future - Phase 3)

1. **Query Generation** → LLM creates queries for each dimension
2. **Wikipedia Research** → Searches Wikipedia (primary)
3. **Google Search** → Searches Google if Wikipedia insufficient (secondary)
4. **Source Filtering** → Filters by credibility
5. **Synthesis** → LLM synthesizes from all sources

## Configuration

Google Search is configured but disabled in `utils/heritage_research/config.py`:
```python
GOOGLE_SEARCH_ENABLED = os.getenv('GOOGLE_SEARCH_ENABLED', 'false').lower() == 'true'
```

To enable (when Phase 3 is implemented):
- Set environment variable: `GOOGLE_SEARCH_ENABLED=true`
- Set `GOOGLE_SEARCH_API_KEY` and `GOOGLE_SEARCH_ENGINE_ID`

## Next Steps

1. ✅ Complete Phase 1 (Wikipedia integration) - DONE
2. ⏳ Refine Phase 2 (Synthesis quality)
3. 📋 Implement Phase 3 (Google Search integration)
4. 📋 Complete Phase 4 (Source management)

