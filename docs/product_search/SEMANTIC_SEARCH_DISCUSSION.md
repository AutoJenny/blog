# Semantic Product Search - Discussion & Implementation Plan

**Date:** 2025-11-11  
**Status:** Planning & Initial Implementation  
**Goal:** Add intelligent semantic search alongside simple text filtering for product selection

---

## Problem Statement

The current product search in the Generate Post modal uses simple text filtering (`ILIKE` on name and description), which has limitations:

1. **Poor Relevance**: Searching "kilt" returns kilt pins and kilted teddy bears alongside actual kilts
2. **No Context Awareness**: "Macdonald skirt" doesn't prioritize skirts with Macdonald in options/attributes
3. **No Prioritization**: Results are just alphabetical, not ranked by relevance

The main CLAN.com site has similar issues with human-tuned semantic search that produces poor results.

---

## Proposed Solution: Hybrid Search System

### Two Search Fields Side-by-Side

1. **Simple Search** (existing): Fast text filtering for exact matches
2. **Smart Search** (new): Semantic/vector-based search with intelligent ranking

### Smart Search Strategy: Multi-Stage Ranking

#### Stage 1: Vector Search (Semantic Relevance)
- Use existing `/api/content/search` endpoint
- Query vectorized product chunks (includes name, description, specifications, additional_data, options, etc.)
- Get top 20-30 candidates by semantic similarity
- Base score: 0-1 from vector distance

#### Stage 2: Re-Ranking with Boost Factors
Apply boost factors to prioritize better matches:

- **Exact name match**: +50% boost
- **Category match**: +30% boost (e.g., "kilt" query → products in `/kilts` category)
- **Name contains query**: +20% boost
- **Options/attributes match**: +15% boost (e.g., "Macdonald" in configurable_options)
- **Description contains query**: +10% boost

#### Final Scoring Formula
```
final_score = (semantic_score * 0.4) + 
              (exact_name_match * 0.3) + 
              (category_relevance * 0.15) + 
              (options_match * 0.1) + 
              (description_match * 0.05)
```

### Example Scenarios

**Query: "kilt"**
1. Vector search finds: "Balmoral Kilt", "Kilt Pin", "Kilted Teddy Bear"
2. Re-ranking:
   - "Balmoral Kilt" (in `/kilts` category, name match) → score: 0.95
   - "Kilt Pin" (name match, wrong category) → score: 0.65
   - "Kilted Teddy Bear" (semantic match only) → score: 0.45
3. Result: "Balmoral Kilt" appears first

**Query: "Macdonald skirt"**
1. Vector search finds: skirts semantically related
2. Re-ranking:
   - Skirt with "Macdonald" in tartan options → score: 0.90
   - Skirt with "Macdonald" in name → score: 0.95
   - Generic skirt → score: 0.60
3. Result: Macdonald-related skirts appear first

---

## Implementation Plan

### Phase 1: Basic Semantic Search (Current)
- Add second search field beside existing filter
- Use vector search to find products
- Simple re-ranking with basic boost factors
- Only enable when query > 2 characters
- Return same format as current search (id, name, sku, price, image_url, etc.)

### Phase 2: Enhanced Re-Ranking (Future)
- Implement full boost factor system
- Category context matching
- Options/attributes parsing
- Match reason display

### Phase 3: Tuning Interface (Future)
- Interactive tuning interface
- Test suite management
- LLM-assisted parameter optimization
- See tuning discussion below

---

## Tuning & Optimization Discussion

### Problem
Current CLAN.com search uses human-tuned semantic search with poor results. Need a way to optimize for our specific product range.

### Proposed Approaches

#### Approach 1: Interactive Tuning Interface with LLM Feedback Loop
- User enters test queries
- System shows ranked results
- User provides feedback (correct/incorrect, should be higher/lower)
- LLM analyzes feedback and suggests parameter adjustments
- Iterative improvement

**Features:**
- Test query management
- Results analysis (current vs expected)
- Feedback collection (per-result, drag-to-reorder, text feedback)
- LLM analysis panel
- Parameter control panel

#### Approach 2: Automated Test Suite with LLM Optimization
- Create test suite of query/expected-result pairs
- LLM runs suite, analyzes failures, proposes changes
- System tests proposed changes
- Track improvement over time

#### Approach 3: Hybrid (Recommended)
- Start with curated test suite (10-20 critical queries)
- Interactive tuning interface for refinement
- LLM analyzes both test results and user feedback
- LLM proposes parameter adjustments with explanations
- Track improvement metrics

### LLM Optimization Strategy

**Prompt Structure:**
```
You are optimizing a product search ranking system.

Current Parameters:
- Semantic score weight: 0.4
- Exact name match boost: 0.3
- Category relevance boost: 0.15
- Options match boost: 0.1
- Description match boost: 0.05

Test Results:
[Query, Expected Results, Actual Results, Issues]

User Feedback:
[Specific feedback about what's wrong/right]

Analyze and propose specific parameter adjustments with reasoning.
```

**LLM Learning Process:**
1. Pattern recognition: identify common failure modes
2. Root cause analysis: why parameters are misaligned
3. Hypothesis generation: what changes might help
4. Parameter proposal: specific numeric adjustments
5. Impact prediction: expected improvement

### Future: Real Search Data Integration
- Track click-through rates from production
- Track "product selected" events
- Use as implicit feedback
- LLM learns from actual user behavior
- A/B test different parameter sets

---

## Technical Implementation

### API Endpoint
**New Endpoint**: `POST /api/products/semantic-search`

**Request:**
```json
{
  "query": "kilt",
  "limit": 10
}
```

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "id": 123,
      "name": "Balmoral Kilt",
      "sku": "kilt-001",
      "price": "199.99",
      "image_url": "...",
      "url": "...",
      "relevance_score": 0.95,
      "match_reason": "Name match + category match"
    }
  ],
  "query_time_ms": 45.2
}
```

### Implementation Steps
1. Create new API endpoint for semantic product search
2. Use `ContentRetriever` to get vector search results
3. Fetch full product data from database
4. Apply re-ranking with boost factors
5. Return formatted results
6. Update modal UI to add second search field
7. Wire up JavaScript to call new endpoint

### Performance Considerations
- Cache embeddings for common queries
- Limit vector search to top 30-50 candidates
- Re-rank to top 10-15 for display
- Target: sub-200ms response time
- Fallback to simple search if vector search fails

---

## UI Design

### Two Search Fields Side-by-Side
- **Left**: "Search Products" (existing simple filter)
- **Right**: "Smart Search" (new semantic search)
  - Icon indicator (lightbulb/AI)
  - Placeholder: "Search by meaning..."
  - Only enabled when query > 2 characters

### Results Display
- Show results from selected search type
- Smart search shows relevance score (optional, for debugging)
- Match reason (optional, for debugging)
- Same product card format as current search

---

## Decisions Made

1. **Keep both searches initially** - Don't replace, add alongside
2. **Keep it simple** - Basic implementation first, no filters yet
3. **Only enable when >2 characters** - Avoid unnecessary searches
4. **Tuning interface later** - Focus on basic search first
5. **No real search data yet** - Use test suite and manual feedback initially

---

## Future Enhancements

1. **Enhanced Re-Ranking**: Full boost factor system with category context
2. **Tuning Interface**: Interactive optimization with LLM assistance
3. **Test Suite**: Automated testing of search quality
4. **Production Data Integration**: Learn from actual user behavior
5. **Category-Specific Rules**: Different parameters for different product types
6. **Query Enhancement**: Pre-process queries for better embeddings
7. **Result Combination**: Option to merge results from both searches

---

## Related Documentation

- `Vector_Search_Phase1_Plan.md` - Vector search infrastructure
- `clan_products/schema.md` - Product data structure
- `data_intelligence/README.md` - Data intelligence system overview

