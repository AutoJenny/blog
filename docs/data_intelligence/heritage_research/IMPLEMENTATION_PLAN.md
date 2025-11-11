# Enhanced Heritage Research - Implementation Plan

## Overview

Implementation plan for the enhanced heritage research system, focusing on free resources and on-demand research.

## Key Constraints

- **Budget:** Free resources only (Wikipedia API, Google Custom Search free tier)
- **Frequency:** Currently on-demand via regenerate button (evergreen data). **Configurable for future changes** when product profiling calendar schedule is in place.
- **Storage:** Snippets only (not full content)
- **Review:** No manual review required
- **Priority:** On-demand as products are posted
- **Industrial Legacy:** Historical only (no modern manufacturers)

## Configuration Design

Research frequency will be configurable via:
- Database setting in `heritage_research_config` table (future)
- Environment variable or config file for now
- Easy to switch between: on-demand, scheduled, interval-based

## Phase 1: Foundation - Wikipedia Integration

### Goals
- Set up Wikipedia API integration
- Create query generator for research dimensions
- Extract Wikipedia content and references
- Basic source filtering and credibility scoring

### Tasks

1. **Wikipedia API Integration** (`utils/heritage_research/wikipedia_researcher.py`)
   - Install `wikipedia-api` or `mwparserfromhell` library
   - Create `WikipediaResearcher` class
   - Implement search functionality
   - Extract page content and references
   - Parse references to external sources

2. **Query Generator** (`utils/heritage_research/query_generator.py`)
   - Create `QueryGenerator` class
   - LLM-powered query generation for 5 dimensions
   - Context-aware query creation (category hierarchy)
   - Query validation

3. **Source Filtering** (`utils/heritage_research/source_filter.py`)
   - Credibility scoring system
   - Domain-based filtering (.ac.uk, .gov.uk, museums)
   - Source type classification (museum, academic, government, wikipedia)

4. **Database Schema Updates**
   - Create `heritage_research_sources` table
   - Update `clan_categories.heritage_data` structure
   - Add Industrial Legacy section

5. **Integration with Existing System**
   - Update `CategoryHeritageResearcher` class
   - Integrate Wikipedia research into `derive_category_context()`
   - Test with Shirts category

### Deliverables
- Wikipedia API integration working
- Query generation for all 5 dimensions
- Basic source storage and retrieval
- Test results for Shirts category

### Timeline: Week 1

---

## Phase 2: Synthesis & Structure

### Goals
- Create research synthesizer module
- Implement LLM synthesis for all dimensions
- Add theme and significance extraction
- Structure Industrial Legacy dimension

### Tasks

1. **Research Synthesizer** (`utils/heritage_research/research_synthesizer.py`)
   - Create `ResearchSynthesizer` class
   - LLM synthesis prompts for each dimension
   - Theme extraction from sources
   - Significance identification
   - Narrative generation (300-500 words per dimension)

2. **Industrial Legacy Research**
   - Create specific queries for historical producers
   - Research historical manufacturing processes
   - Identify regional specializations
   - Exclude modern manufacturers

3. **Synthesis Quality**
   - Source attribution in narratives
   - Key themes extraction
   - Significant elements identification
   - Cross-dimension consistency checks

4. **Update Heritage Data Structure**
   - Add Industrial Legacy to heritage_data
   - Add research_metadata section
   - Add sources array
   - Add key_themes and significant_elements to each dimension

### Deliverables
- Complete synthesis system
- All 5 dimensions working
- Quality synthesis output
- Updated database structure

### Timeline: Week 2

---

## Phase 3: Google Search Integration

### Goals
- Set up Google Custom Search API (free tier)
- Implement query usage tracking
- Add domain filtering
- Integrate as secondary research source

### Tasks

1. **Google Custom Search Setup**
   - Create Google Custom Search Engine
   - Configure site restrictions (.ac.uk, .gov.uk, museums)
   - Set up API key management
   - Implement rate limiting (100 queries/day)

2. **Query Usage Tracking** (`utils/heritage_research/query_tracker.py`)
   - Track daily query usage
   - Implement query budget management
   - Fallback to Wikipedia when limit reached
   - Logging and monitoring

3. **Domain Filtering**
   - Filter results by credible domains
   - Prioritize museum and academic sources
   - Extract snippets from results
   - Source credibility scoring

4. **Integration with Research Pipeline**
   - Use Google Search when Wikipedia insufficient
   - Combine Wikipedia + Google results
   - Prioritize sources by credibility
   - Mark research_method in metadata

### Deliverables
- Google Custom Search integration
- Query usage tracking
- Combined Wikipedia + Google research
- Test with multiple categories

### Timeline: Week 3

---

## Phase 4: Source Management & Polish

### Goals
- Complete source management system
- Implement credibility scoring
- Add research metadata tracking
- Polish on-demand regeneration workflow

### Tasks

1. **Source Manager** (`utils/heritage_research/source_manager.py`)
   - Source storage (snippets only)
   - Source deduplication
   - Source retrieval by dimension
   - Citation management

2. **Credibility Scoring System**
   - Domain-based scoring (.ac.uk = high, etc.)
   - Source type scoring (museum > academic > government > wikipedia)
   - Content quality indicators
   - Aggregate credibility scores

3. **Research Metadata**
   - Track research_method (wikipedia_api, google_search, llm_enhanced)
   - Store research_date
   - Track source_count per dimension
   - Store credibility_score
   - Add depth_level indicator

4. **On-Demand Workflow**
   - Update regenerate button to use new system
   - Show research progress (if long-running)
   - Display research metadata in UI
   - Handle errors gracefully

5. **Testing & Documentation**
   - Test with multiple categories
   - Document API usage and limits
   - Create usage guidelines
   - Update user documentation

### Deliverables
- Complete source management
- Credibility scoring system
- Research metadata tracking
- Polished on-demand workflow
- Documentation

### Timeline: Week 4

---

## Technical Specifications

### Dependencies

```python
# requirements.txt additions
wikipedia-api>=0.6.0  # Wikipedia API wrapper
google-api-python-client>=2.0.0  # Google Custom Search API
beautifulsoup4>=4.12.0  # HTML parsing for source extraction
```

### Database Schema

```sql
-- New table for research sources
CREATE TABLE heritage_research_sources (
    id SERIAL PRIMARY KEY,
    category_id INTEGER REFERENCES clan_categories(id),
    dimension VARCHAR(50) NOT NULL,  -- historical_origins, cultural_significance, etc.
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    domain VARCHAR(255),
    source_type VARCHAR(50),  -- museum, academic, government, wikipedia
    credibility_score DECIMAL(3,2),
    snippets JSONB,  -- Array of text snippets
    relevance_score DECIMAL(3,2),
    research_method VARCHAR(50),  -- wikipedia_api, google_search, llm_enhanced
    research_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_heritage_sources_category ON heritage_research_sources(category_id, dimension);
CREATE INDEX idx_heritage_sources_domain ON heritage_research_sources(domain);
```

### Updated Heritage Data Structure

```json
{
  "historical_origins": {
    "narrative": "300-500 word synthesized narrative...",
    "key_themes": ["Theme 1", "Theme 2", "..."],
    "significant_elements": ["Element 1", "Element 2", "..."],
    "source_count": 15,
    "research_date": "2025-01-11"
  },
  "cultural_significance": { ... },
  "evolution": { ... },
  "scottish_heritage_connections": { ... },
  "industrial_legacy": {
    "narrative": "...",
    "famous_historical_producers": ["Producer 1", "Producer 2"],
    "historical_manufacturing_processes": ["Process 1", "Process 2"],
    "regional_specializations": ["Region 1", "Region 2"],
    "key_themes": ["..."],
    "source_count": 12
  },
  "research_metadata": {
    "total_sources": 67,
    "research_date": "2025-01-11",
    "researcher_version": "2.0",
    "credibility_score": 0.92,
    "depth_level": "comprehensive",
    "research_method": "wikipedia_api"  // or "google_search" or "llm_enhanced"
  }
}
```

## Success Criteria

1. **Wikipedia Integration:** Successfully extracts content and references for all 5 dimensions
2. **Synthesis Quality:** Produces coherent, insightful narratives with source attribution
3. **Source Management:** Stores snippets with proper attribution and credibility scores
4. **On-Demand Workflow:** Regenerate button successfully triggers full research process
5. **Free Resource Usage:** Stays within free tier limits (100 Google queries/day)
6. **Industrial Legacy:** Focuses on historical producers and processes only

## Risk Mitigation

1. **API Rate Limits:** 
   - Track usage carefully
   - Fallback to Wikipedia-only research
   - Implement LLM-enhanced research as final fallback

2. **Source Quality:**
   - Strict credibility filtering
   - Multiple source cross-referencing
   - Clear marking of research_method

3. **Research Time:**
   - Implement progress tracking for long-running research
   - Consider async processing for very large categories
   - Show user feedback during research

4. **Cost Overruns:**
   - Strict monitoring of Google API usage
   - Request permission before exceeding free tier
   - Document all API costs

## Next Steps

1. Review implementation plan
2. Set up development environment
3. Begin Phase 1: Wikipedia integration
4. Test with Shirts category
5. Iterate based on results

