# Smart Product Search - Implementation Plan

**Date:** 2025-11-11  
**Status:** Planning  
**Goal:** Fix semantic product search to understand query intent and use structured data for accurate, context-aware results

---

## Executive Summary

The current semantic search system uses generic embeddings that fail to distinguish between main products and accessories (e.g., "kilt" vs "kilt pin") and returns irrelevant results (e.g., sweaters when searching for "skirt"). This implementation will add LLM-based query understanding and structured re-ranking to create a smart, context-aware search system that leverages existing data structures (category hierarchy, product types, descriptions) for accurate results.

**Estimated Time:** 5-8 days  
**Priority:** High (affects product search, alternative products, content suggestions, related products)

---

## Problem Statement

### Current Issues

1. **Poor Semantic Understanding**: Generic embeddings treat "kilt" and "kilt pin" as similar because they share the word "kilt"
2. **Irrelevant Results**: Searching "skirt" returns sweaters and shirts (completely unrelated)
3. **No Context Awareness**: System doesn't use category structure, product types, or descriptions effectively
4. **Accessory Confusion**: Accessories rank equally with main products when searching for garment types

### Root Cause

- Embeddings are trained on general text, not product catalogs
- No understanding of query intent (what does "kilt" mean in this context?)
- Structured data (categories, product types) not used effectively
- No distinction between main products and accessories

### Impact

- **Product Search**: Users can't find products effectively
- **Alternative Products**: Blog posts suggest wrong alternatives
- **Content Suggestions**: Poor product recommendations for articles
- **Related Products**: Random or irrelevant suggestions

---

## Goals

### Primary Goals

1. **Accurate Product Search**: "kilt" returns actual kilts, not kilt pins
2. **Context Awareness**: Understand query intent and use category/product type data
3. **Reusable Service**: Single implementation used by all features
4. **Fast Performance**: Sub-200ms response time for search queries

### Success Criteria

- ✅ "kilt" query returns kilts in kilts category as top results
- ✅ "skirt" query returns skirts, not sweaters
- ✅ "Macdonald skirt" finds skirts with Macdonald in options/attributes
- ✅ Accessories rank lower when searching for main product types
- ✅ Category matches boost relevance significantly
- ✅ All existing features (alternative products, suggestions) benefit from improvements

---

## Current System Architecture

### Data Structures

#### `clan_products` Table
```sql
- id (INTEGER, PRIMARY KEY)
- name (TEXT) - Product name
- sku (TEXT) - Product SKU
- price (DECIMAL)
- image_url (TEXT)
- url (TEXT)
- short_description (TEXT) - Brief description
- description (TEXT) - Full HTML description
- supplier_name (TEXT)
- supplier_description (TEXT)
- category_ids (JSONB) - Array of category IDs
- configurable_options (JSONB) - Product options (sizes, colors, tartans, etc.)
- additional_data (JSONB) - Structured attributes (material, pattern, clan crest, etc.)
- dimensions (TEXT)
- specifications (TEXT/JSONB)
```

#### `clan_categories` Table
```sql
- id (INTEGER, PRIMARY KEY)
- name (TEXT) - Category name
- description (TEXT)
- level (INTEGER) - Hierarchy level (0 = root)
- parent_id (INTEGER) - Parent category ID
```

**Category Hierarchy Example:**
- `menswear` (level 0, parent_id: NULL)
  - `kilts` (level 1, parent_id: menswear.id)
  - `shirts` (level 1, parent_id: menswear.id)
- `accessories` (level 0, parent_id: NULL)
  - `kilt pins` (level 1, parent_id: accessories.id)

#### `content_chunks` Table
```sql
- id (SERIAL, PRIMARY KEY)
- chunk_type (VARCHAR) - 'product', 'category', 'kb'
- source_id (INTEGER) - Product or category ID
- chunk_text (TEXT) - Normalized text content
- metadata (JSONB) - Product/category metadata
- embedding_model (VARCHAR)
- embedding_dim (INTEGER)
- faiss_index_id (INTEGER)
```

### Existing Code

#### Vector Search Infrastructure
- **Location**: `utils/vector_search/`
- **Files**:
  - `retrieval.py` - `ContentRetriever` class (semantic search)
  - `chunking.py` - `ContentChunker` class (text extraction)
  - `embeddings.py` - `EmbeddingGenerator` class (embedding generation)
  - `faiss_index.py` - `FAISSIndexManager` class (vector index)
- **Current Usage**: Generic vector search with basic similarity scoring

#### Product Search API
- **Location**: `blueprints/content_search_api.py`
- **Endpoint**: `POST /api/products/semantic-search`
- **Current Implementation**: 
  - Uses `ContentRetriever` for vector search
  - Basic re-ranking with boost factors (name match, category match, etc.)
  - Accessory penalty (recently added, needs improvement)

#### Alternative Products
- **Location**: `utils/content_generation/clan_data_extractor.py`
- **Method**: `find_alternative_products(product_id, limit)`
- **Current Strategy**:
  1. Same category products
  2. Vector search for similar products
  3. Price-based alternatives
  4. Same producer/supplier
  5. Cross-category alternatives via vector search

#### Content Suggestions
- **Location**: `blueprints/content_generation_api.py`
- **Endpoint**: `POST /api/content/suggest-ideas`
- **Current Implementation**: Uses `ContentRetriever` with generic queries

### LLM Service

- **Location**: `modules/llm_service.py`
- **Available Providers**: OpenAI (GPT-4), Ollama (llama3.2)
- **Usage Pattern**:
```python
from modules.llm_service import LLMService
llm_service = LLMService()
result = llm_service.execute_llm_request(
    provider='openai',
    model='gpt-4',
    messages=[...],
    api_key=os.getenv('OPENAI_API_KEY')
)
```

### Database Access

- **Location**: `config/database.py`
- **Pattern**:
```python
from config.database import db_manager
with db_manager.get_cursor() as cursor:
    cursor.execute("SELECT ...", (params,))
    result = cursor.fetchone()  # or fetchall()
```

---

## Technical Approach

### Architecture: Hybrid Search System

```
User Query
    ↓
LLM Query Understanding
    ↓
[Extract: product_type, category_hints, intent]
    ↓
Vector Search (Initial Candidates)
    ↓
[Get top 20-30 semantically similar products]
    ↓
Structured Re-Ranking
    ↓
[Apply boost factors using structured data]
    ↓
Ranked Results
```

### Components

#### 1. Query Understanding Service
- **Purpose**: Analyze query to extract intent and context
- **Input**: User query string (e.g., "kilt", "Macdonald skirt", "rainwear for autumn")
- **Output**: Structured query analysis
  ```python
  {
      "product_type": "kilt",  # Main product type detected
      "category_hints": ["kilts", "menswear"],  # Possible categories
      "intent": "find_main_product",  # or "find_accessory", "find_by_attribute"
      "attributes": ["Macdonald"],  # Specific attributes (clan names, etc.)
      "context": "autumn"  # Additional context
  }
  ```
- **Implementation**: LLM-based analysis with structured output

#### 2. Smart Re-Ranking Service
- **Purpose**: Re-rank vector search results using structured data
- **Input**: 
  - Vector search results (top 20-30 candidates)
  - Query analysis from Query Understanding
  - Full product data from database
- **Output**: Re-ranked products with relevance scores
- **Boost Factors**:
  - Category match: +0.3 to +0.5 (strong boost)
  - Product type match: +0.3 (main product vs accessory)
  - Exact name match: +0.3
  - Name contains query: +0.2
  - Options/attributes match: +0.15
  - Accessory penalty: -0.4 (when searching main products)
  - Category mismatch penalty: -0.2 (wrong category)

#### 3. Reusable Search Service
- **Purpose**: Single service used by all features
- **Location**: `utils/product_search/smart_search.py` (new)
- **Methods**:
  - `search(query, context=None, limit=10)` - General search
  - `find_similar(product_id, limit=5)` - Find similar products
  - `find_related(product_id, limit=5)` - Find related products
  - `find_by_category(category_id, query=None, limit=10)` - Category-specific search

---

## Implementation Phases

### Phase 1: Core Search Fix (2-3 days)

#### Day 1: Query Understanding
**Tasks:**
1. Create `utils/product_search/query_analyzer.py`
   - `QueryAnalyzer` class
   - `analyze_query(query: str) -> Dict` method
   - LLM prompt for query analysis
   - Extract: product_type, category_hints, intent, attributes
2. Create test cases for query analysis
   - "kilt" → product_type: "kilt", category_hints: ["kilts"]
   - "skirt" → product_type: "skirt", category_hints: ["skirts", "kilts"]
   - "Macdonald skirt" → product_type: "skirt", attributes: ["Macdonald"]
   - "rainwear autumn" → product_type: "rainwear", context: "autumn"

**Files to Create:**
- `utils/product_search/__init__.py`
- `utils/product_search/query_analyzer.py`

**Dependencies:**
- `modules/llm_service.py` (existing)
- `config/database.py` (existing)

#### Day 2: Structured Re-Ranking
**Tasks:**
1. Create `utils/product_search/reranker.py`
   - `ProductReranker` class
   - `rerank(results, query_analysis, product_data) -> List[Dict]` method
   - Implement boost factor logic
   - Category matching (check category names, hierarchy)
   - Product type detection (main product vs accessory)
   - Accessory penalty logic
2. Integrate with existing search endpoint
   - Update `blueprints/content_search_api.py`
   - Use `QueryAnalyzer` and `ProductReranker`
   - Maintain backward compatibility

**Files to Create:**
- `utils/product_search/reranker.py`

**Files to Modify:**
- `blueprints/content_search_api.py` - Update `api_semantic_product_search()`

#### Day 3: Testing & Refinement
**Tasks:**
1. Create comprehensive test suite
   - Test queries: "kilt", "skirt", "Macdonald skirt", "rainwear"
   - Verify results are correct
   - Check performance (target: <200ms)
2. Refine boost factors based on test results
3. Handle edge cases
   - Empty results
   - Very short queries
   - Category-less products
   - Products with multiple categories

**Files to Create:**
- `tests/test_smart_search.py` (or add to existing test suite)

### Phase 2: Service Extraction (1-2 days)

#### Day 1: Create Reusable Service
**Tasks:**
1. Create `utils/product_search/smart_search.py`
   - `SmartProductSearch` class
   - Integrate `QueryAnalyzer` and `ProductReranker`
   - Methods:
     - `search(query, context=None, limit=10)`
     - `find_similar(product_id, limit=5)`
     - `find_related(product_id, limit=5)`
2. Update product search endpoint to use service
3. Test service independently

**Files to Create:**
- `utils/product_search/smart_search.py`

**Files to Modify:**
- `blueprints/content_search_api.py`

#### Day 2: Documentation & Integration
**Tasks:**
1. Document service API
2. Create usage examples
3. Update existing code to use service (if time permits)

### Phase 3: Rollout to Other Features (2-3 days)

#### Alternative Products (0.5 day)
**Tasks:**
1. Update `find_alternative_products()` in `clan_data_extractor.py`
2. Use `SmartProductSearch.find_similar()`
3. Test with existing blog posts

**Files to Modify:**
- `utils/content_generation/clan_data_extractor.py`

#### Content Suggestions (0.5 day)
**Tasks:**
1. Update `api_suggest_ideas()` in `content_generation_api.py`
2. Use `SmartProductSearch.search()` with context
3. Test with various queries

**Files to Modify:**
- `blueprints/content_generation_api.py`

#### Related Products (0.5 day)
**Tasks:**
1. Update related products endpoints
2. Use `SmartProductSearch.find_related()`
3. Test product pages

**Files to Modify:**
- `blueprints/clan_api.py` - `get_related_products()`
- `blog-launchpad/clan_api.py` - `get_related_products()`

#### Testing & Documentation (1 day)
**Tasks:**
1. End-to-end testing of all features
2. Performance testing
3. Update documentation
4. Create migration guide

---

## Use Cases

### Use Case 1: Product Search in Generate Post Modal
**Current**: User searches "kilt", gets kilt pins mixed with kilts  
**After Fix**: User searches "kilt", gets actual kilts first, kilt pins ranked lower

**UI Location**: `templates/planning/calendar/content_generator_modal.html`  
**API Endpoint**: `POST /api/products/semantic-search`  
**Expected Behavior**:
- Top 3 results should be actual kilts
- Kilt pins should appear lower (if at all)
- Results show relevance score and match reason

### Use Case 2: Alternative Products in Blog Posts
**Current**: Post about "Balmoral Kilt" suggests random products  
**After Fix**: Suggests other kilts, similar garments, complementary items

**Code Location**: `utils/content_generation/clan_data_extractor.py::find_alternative_products()`  
**Expected Behavior**:
- Same category products prioritized
- Similar products (same type, different style)
- Complementary products (sporrans, kilt pins)
- Price alternatives (cheaper/more luxury)

### Use Case 3: Content Suggestions
**Current**: "interesting Scottish products" returns random items  
**After Fix**: Returns relevant products based on query context

**Code Location**: `blueprints/content_generation_api.py::api_suggest_ideas()`  
**Example Queries**:
- "rainwear for autumn" → waterproof jackets, coats
- "heritage items" → products with rich heritage data
- "Scottish tartan" → tartan products

### Use Case 4: Related Products
**Current**: Random products shown  
**After Fix**: Semantically related products

**Code Location**: `blueprints/clan_api.py::get_related_products()`  
**Expected Behavior**:
- Same category products
- Similar products (same type, different attributes)
- Complementary products (accessories for main products)

---

## UI Requirements

### Product Search Modal
**Location**: `templates/planning/calendar/content_generator_modal.html`

**Current State:**
- Two search fields: "Search Products" (simple) and "Smart Search" (semantic)
- Results show: name, SKU, supplier, relevance score

**No Changes Required** (UI already supports smart search)

**Optional Enhancements:**
- Show match reason in tooltip or expanded view
- Highlight category matches
- Show category path for each result

### Alternative Products Section
**Location**: Blog post editing interface

**Current State:**
- Shows alternative products in blog post sections
- No UI changes needed (backend improvement only)

### Content Suggestions
**Location**: Generate Post modal → "Get Suggestions" section

**Current State:**
- Shows suggested products/categories
- No UI changes needed (backend improvement only)

---

## Test Cases

### Test Suite Structure
Create `tests/test_smart_search.py` or add to existing test suite.

### Test Cases

#### Query Understanding Tests
```python
def test_query_analyzer_kilt():
    """Test 'kilt' query analysis"""
    analyzer = QueryAnalyzer()
    result = analyzer.analyze_query("kilt")
    assert result["product_type"] == "kilt"
    assert "kilts" in result["category_hints"]
    assert result["intent"] == "find_main_product"

def test_query_analyzer_skirt():
    """Test 'skirt' query analysis"""
    analyzer = QueryAnalyzer()
    result = analyzer.analyze_query("skirt")
    assert result["product_type"] == "skirt"
    assert "skirts" in result["category_hints"] or "kilts" in result["category_hints"]

def test_query_analyzer_macdonald_skirt():
    """Test 'Macdonald skirt' query analysis"""
    analyzer = QueryAnalyzer()
    result = analyzer.analyze_query("Macdonald skirt")
    assert result["product_type"] == "skirt"
    assert "Macdonald" in result["attributes"]

def test_query_analyzer_rainwear_autumn():
    """Test contextual query"""
    analyzer = QueryAnalyzer()
    result = analyzer.analyze_query("rainwear for autumn")
    assert result["product_type"] == "rainwear"
    assert result["context"] == "autumn"
```

#### Re-Ranking Tests
```python
def test_reranker_kilt_prioritizes_kilts():
    """Test that 'kilt' query prioritizes actual kilts over kilt pins"""
    reranker = ProductReranker()
    # Mock vector search results with kilt and kilt pin
    results = [
        {"source_id": 1, "score": 0.8, "name": "Kilt Pin"},
        {"source_id": 2, "score": 0.75, "name": "Balmoral Kilt"}
    ]
    query_analysis = {"product_type": "kilt", "category_hints": ["kilts"]}
    # Fetch product data (mock)
    reranked = reranker.rerank(results, query_analysis, product_data)
    # Balmoral Kilt should rank higher
    assert reranked[0]["name"] == "Balmoral Kilt"
    assert reranked[0]["relevance_score"] > reranked[1]["relevance_score"]

def test_reranker_skirt_excludes_sweaters():
    """Test that 'skirt' query excludes sweaters"""
    reranker = ProductReranker()
    results = [
        {"source_id": 1, "score": 0.7, "name": "Cashmere Sweater"},
        {"source_id": 2, "score": 0.65, "name": "Tartan Skirt"}
    ]
    query_analysis = {"product_type": "skirt", "category_hints": ["skirts"]}
    reranked = reranker.rerank(results, query_analysis, product_data)
    # Skirt should rank higher, sweater should be filtered or ranked very low
    assert any(r["name"] == "Tartan Skirt" for r in reranked[:3])
    assert not any(r["name"] == "Cashmere Sweater" for r in reranked[:5])
```

#### Integration Tests
```python
def test_smart_search_kilt():
    """End-to-end test: search for 'kilt'"""
    search_service = SmartProductSearch()
    results = search_service.search("kilt", limit=10)
    # Top 3 should be actual kilts
    assert len(results) > 0
    top_3 = results[:3]
    assert all("kilt" in r["name"].lower() for r in top_3)
    # Check that kilt pins are ranked lower
    kilt_pins = [r for r in results if "pin" in r["name"].lower()]
    if kilt_pins:
        assert kilt_pins[0]["relevance_score"] < top_3[0]["relevance_score"]

def test_smart_search_macdonald_skirt():
    """End-to-end test: search for 'Macdonald skirt'"""
    search_service = SmartProductSearch()
    results = search_service.search("Macdonald skirt", limit=10)
    # Should find skirts with Macdonald in options/attributes
    assert len(results) > 0
    # Top results should be skirts
    assert any("skirt" in r["name"].lower() for r in results[:3])
```

#### Performance Tests
```python
def test_search_performance():
    """Test that search completes in <200ms"""
    import time
    search_service = SmartProductSearch()
    start = time.time()
    results = search_service.search("kilt", limit=10)
    elapsed = (time.time() - start) * 1000  # Convert to ms
    assert elapsed < 200, f"Search took {elapsed}ms, expected <200ms"
```

---

## Technical Details

### Query Analyzer Implementation

#### LLM Prompt Structure
```
You are analyzing product search queries for a Scottish heritage product catalog.

Query: "{query}"

Analyze this query and extract:
1. Product type (e.g., "kilt", "shirt", "scarf", "jacket")
2. Category hints (possible categories this product belongs to)
3. Intent (find_main_product, find_accessory, find_by_attribute)
4. Attributes (specific attributes like clan names, tartan names, etc.)
5. Context (additional context like season, occasion, etc.)

Return JSON:
{
    "product_type": "...",
    "category_hints": ["..."],
    "intent": "...",
    "attributes": ["..."],
    "context": "..."
}
```

#### Category Matching Logic
1. Check if query matches category name exactly
2. Check if query is contained in category name
3. Check category hierarchy (parent categories)
4. Use category path for matching (e.g., "menswear > kilts")

#### Product Type Detection
- **Main Product Types**: kilt, shirt, scarf, jacket, tie, waistcoat, sporran, skirt, dress, etc.
- **Accessory Keywords**: pin, accessory, keychain, badge, patch, button, etc.
- **Detection**: Check product name for accessory keywords when query is main product type

### Re-Ranking Algorithm

#### Score Calculation
```python
base_score = semantic_score * 0.4  # From vector search

# Boost factors
category_boost = 0.0
if category_match:
    if exact_category_match:
        category_boost = 0.5
    elif category_contains_query:
        category_boost = 0.3
    elif parent_category_match:
        category_boost = 0.2

product_type_boost = 0.0
if product_type_match:
    product_type_boost = 0.3

name_boost = 0.0
if exact_name_match:
    name_boost = 0.3
elif name_contains_query:
    name_boost = 0.2

options_boost = 0.0
if query_attributes_in_options:
    options_boost = 0.15

# Penalties
accessory_penalty = 0.0
if is_main_product_query and is_accessory:
    accessory_penalty = -0.4

category_mismatch_penalty = 0.0
if category_hints and not category_match:
    category_mismatch_penalty = -0.2

# Final score
final_score = (
    base_score +
    category_boost +
    product_type_boost +
    name_boost +
    options_boost +
    accessory_penalty +
    category_mismatch_penalty
)
final_score = max(0.0, final_score)  # Ensure non-negative
```

### Database Queries

#### Fetch Product with Categories
```sql
SELECT 
    p.id, p.name, p.sku, p.price, p.image_url, p.url,
    p.category_ids, p.configurable_options, p.additional_data,
    p.supplier_name, p.short_description, p.description
FROM clan_products p
WHERE p.id = %s
```

#### Fetch Category Names
```sql
SELECT name, parent_id, level
FROM clan_categories
WHERE id IN (%s, %s, ...)
```

#### Get Category Path
```sql
WITH RECURSIVE category_path AS (
    SELECT id, name, parent_id, 0 as level
    FROM clan_categories
    WHERE id = %s
    UNION ALL
    SELECT c.id, c.name, c.parent_id, cp.level + 1
    FROM clan_categories c
    JOIN category_path cp ON c.id = cp.parent_id
)
SELECT name FROM category_path ORDER BY level;
```

### Error Handling

#### Query Analysis Failures
- Fallback to simple keyword matching if LLM fails
- Log errors but don't break search
- Return basic analysis: `{"product_type": query, "category_hints": [], "intent": "find_main_product"}`

#### Re-Ranking Failures
- If product data fetch fails, skip that product
- If category lookup fails, continue without category boost
- Log errors for debugging

#### Performance Degradation
- Cache LLM query analysis results (same query = cached result)
- Limit LLM calls (batch processing if possible)
- Timeout handling (fallback to simple search if LLM takes too long)

---

## Success Metrics

### Quantitative Metrics
- **Relevance**: Top 3 results should be correct 90%+ of the time
- **Performance**: Search completes in <200ms (95th percentile)
- **Coverage**: All product types searchable (kilts, shirts, scarves, etc.)

### Qualitative Metrics
- **User Satisfaction**: Users can find products quickly
- **Accuracy**: No irrelevant results in top 5
- **Context Awareness**: System understands query intent

### Test Queries for Validation
1. "kilt" → Should return kilts, not kilt pins
2. "skirt" → Should return skirts, not sweaters
3. "Macdonald skirt" → Should find skirts with Macdonald attributes
4. "rainwear" → Should return waterproof items
5. "tartan scarf" → Should return tartan scarves

---

## Dependencies

### External Dependencies
- **LLM Service**: OpenAI GPT-4 or Ollama llama3.2 (existing)
- **Vector Search**: FAISS index (existing)
- **Embeddings**: E5-large-v2 model (existing)
- **Database**: PostgreSQL (existing)

### Internal Dependencies
- `modules/llm_service.py` - LLM service
- `config/database.py` - Database access
- `utils/vector_search/retrieval.py` - Vector search
- `utils/vector_search/chunking.py` - Text chunking

### New Dependencies
- None (all dependencies exist)

---

## Files to Create

### New Files
```
utils/product_search/
├── __init__.py
├── query_analyzer.py      # Query understanding
├── reranker.py            # Re-ranking logic
└── smart_search.py        # Main service (Phase 2)

tests/
└── test_smart_search.py   # Test suite
```

### Files to Modify
```
blueprints/content_search_api.py          # Update semantic search endpoint
utils/content_generation/clan_data_extractor.py  # Update alternative products
blueprints/content_generation_api.py      # Update content suggestions
blueprints/clan_api.py                    # Update related products (optional)
```

---

## Rollout Plan

### Phase 1: Core Fix (Week 1)
- Implement query analyzer
- Implement re-ranker
- Update product search endpoint
- Test with critical queries
- **Deliverable**: Working product search

### Phase 2: Service Extraction (Week 1-2)
- Extract to reusable service
- Document API
- **Deliverable**: Reusable search service

### Phase 3: Rollout (Week 2)
- Update alternative products
- Update content suggestions
- Update related products (optional)
- End-to-end testing
- **Deliverable**: All features using improved search

---

## Known Limitations

1. **LLM Dependency**: Requires LLM service (OpenAI or Ollama)
2. **Performance**: LLM calls add latency (~100-200ms)
3. **Cost**: LLM API calls have cost (minimal for query analysis)
4. **Category Data**: Requires accurate category hierarchy
5. **Product Type Detection**: Relies on keyword matching (could be improved)

---

## Future Enhancements

1. **Fine-Tuned Embeddings**: Train embeddings on product catalog
2. **Knowledge Graph**: Build explicit product relationships
3. **Learning System**: Learn from user clicks/selections
4. **Multi-Language**: Support Gaelic/Scottish terms
5. **Visual Search**: Image-based product search

---

## References

- **Vector Search Documentation**: `docs/data_intelligence/content_generation/Vector_Search_Phase1_Plan.md`
- **Product Search Discussion**: `docs/product_search/SEMANTIC_SEARCH_DISCUSSION.md`
- **Database Schema**: `docs/clan_products/schema.md`
- **Content Generation**: `docs/data_intelligence/content_generation/PRODUCT_ARTICLE_PLANNING_DISCUSSION.md`

---

## Questions for Implementation

1. **LLM Provider**: Prefer OpenAI GPT-4 or Ollama? (Ollama is free but slower)
2. **Caching**: Should query analysis results be cached? (Recommended: yes)
3. **Fallback**: What should happen if LLM fails? (Recommended: simple keyword matching)
4. **Performance**: Acceptable latency? (Target: <200ms total)
5. **Testing**: Manual testing or automated tests? (Recommended: both)

---

## Contact & Support

For questions during implementation:
- Review existing code in `utils/vector_search/` and `blueprints/content_search_api.py`
- Check database schema in `docs/clan_products/schema.md`
- Test with real queries using the current search endpoint

---

**End of Implementation Plan**

