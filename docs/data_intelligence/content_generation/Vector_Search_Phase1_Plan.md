# Phase 1: Products/Categories Vector Search Infrastructure
**Date:** 2025-01-10  
**Status:** Planning  
**Goal:** Build working vector search system for products/categories data

---

## Overview

Create a semantic search system that allows querying products and categories by meaning, not just keywords. This enables:
- Idea mining ("find interesting products about tartans")
- Context retrieval for content generation
- Similar product discovery
- Category exploration

---

## Database Schema

### New Table: `content_chunks`

Stores text chunks with metadata and embedding references.

```sql
CREATE TABLE content_chunks (
    id SERIAL PRIMARY KEY,
    chunk_type VARCHAR(20) NOT NULL CHECK (chunk_type IN ('product', 'category', 'kb')),  -- 'kb' for later
    source_id INTEGER NOT NULL,  -- product_id or category_id
    chunk_text TEXT NOT NULL,  -- Normalized text content
    chunk_index INTEGER DEFAULT 0,  -- For multi-chunk sources (0 for single-chunk products/categories)
    metadata JSONB DEFAULT '{}',  -- Additional context (product name, category path, etc.)
    embedding_model VARCHAR(50),  -- e.g., 'e5-large', 'bge-large'
    embedding_dim INTEGER,  -- Dimension of embedding vector
    faiss_index_id INTEGER,  -- Index in FAISS (for fast lookup)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_embedded_at TIMESTAMP  -- When embedding was last generated
);

CREATE INDEX idx_content_chunks_type_source ON content_chunks(chunk_type, source_id);
CREATE INDEX idx_content_chunks_faiss_id ON content_chunks(faiss_index_id) WHERE faiss_index_id IS NOT NULL;
CREATE INDEX idx_content_chunks_metadata ON content_chunks USING GIN (metadata);
```

**Design Notes:**
- `chunk_type` allows same table for products, categories, and future KB
- `source_id` references `clan_products.id` or `clan_categories.id`
- `chunk_index` is 0 for products/categories (single chunk), but allows multi-chunk for KB later
- `metadata` stores context like product name, category path, supplier name
- `faiss_index_id` links to FAISS index position for fast retrieval

---

## Chunking Strategy

### Products

**Source Fields:**
- `name` - Product title
- `short_description` - Brief description
- `description` - Full HTML description (needs cleaning)
- `supplier_name` - Producer/manufacturer
- `supplier_description` - HTML supplier info (needs cleaning)
- `specifications` - Product specifications (dict or string)
- `additional_data` - Structured product attributes (material, pattern, clan crest info, etc.)
- `dimensions` - Product dimensions (text)
- `configurable_options` - Product options (sizes, colors, etc.)

**Chunking Process:**
1. Extract all text fields
2. Clean HTML: strip tags, decode entities, normalize whitespace
3. Format structured data (specifications, additional_data, options)
4. Combine into single text block with structure:
   ```
   Product: {name}
   Producer: {supplier_name}
   
   {short_description}
   
   {description (cleaned)}
   
   Specifications:
   {specifications formatted}
   
   Product Details:
   {additional_data formatted as label: value}
   
   Dimensions: {dimensions}
   
   Available Options:
   {configurable_options formatted}
   
   About the Producer: {supplier_description (cleaned)}
   ```
5. Single chunk per product (products are typically 500-1500 tokens with new fields)
6. Store metadata: `{product_name, sku, supplier_name, category_ids, price}`

### Categories

**Source Fields:**
- `name` - Category name
- `description` - Category description
- `heritage_data` (JSONB) - Historical/cultural context (if available)

**Chunking Process:**
1. Extract name and description
2. Extract heritage_data fields if available (handles both legacy string format and new dict format):
   - `historical_origins` - Narrative, key themes, significant elements
   - `cultural_significance` - Narrative, key themes, significant elements
   - `evolution` - Narrative, key themes, significant elements
   - `scottish_heritage_connections` - Narrative, key themes, significant elements
   - `industrial_legacy` - Narrative, key themes, significant elements
3. Combine into single text block:
   ```
   Category: {name}
   
   {description}
   
   Historical Origins:
   {narrative}
   Key Themes: {themes}
   Significant Elements: {elements}
   
   Cultural Significance:
   {narrative}
   Key Themes: {themes}
   Significant Elements: {elements}
   
   [Similar structure for other dimensions...]
   ```
4. Single chunk per category
5. Store metadata: `{category_name, category_id, parent_id, level, category_path}`

---

## Text Normalization

**Process:**
1. **HTML Cleaning:**
   - Strip HTML tags
   - Decode HTML entities (`&amp;` → `&`)
   - Preserve line breaks where meaningful
   - Remove excessive whitespace

2. **Text Normalization:**
   - Normalize whitespace (multiple spaces → single space)
   - Trim leading/trailing whitespace
   - Remove control characters
   - Preserve punctuation and structure

3. **Metadata Extraction:**
   - Extract product/category identifiers
   - Extract related IDs (category_ids, parent_id)
   - Extract display names for context

**Implementation:**
- Use `BeautifulSoup4` for HTML cleaning (already in use)
- Custom normalization function for text cleanup
- JSONB metadata for structured context

---

## Embedding Generation

### Model Selection

**Options:**
1. **E5-large** (recommended)
   - 1024 dimensions
   - Good for semantic search
   - Supports query/document distinction

2. **bge-large-en-v1.5**
   - 1024 dimensions
   - Strong retrieval performance
   - Good for English content

**Decision:** Start with **E5-large** (can switch later, embeddings are regeneratable)

### Embedding Process

1. **Generate Embedding:**
   - Use embedding model API (HuggingFace Transformers or API)
   - Input: normalized chunk text
   - Output: 1024-dimension vector (float32 array)

2. **Store Embedding:**
   - Store in FAISS index (for fast similarity search)
   - Store metadata in PostgreSQL (`content_chunks` table)
   - Link via `faiss_index_id`

3. **Update Strategy:**
   - Initial: Generate embeddings for all products/categories
   - Incremental: Regenerate when source data changes (detect via `product_content_hash` or `last_updated`)
   - Batch: Process in batches of 100-500 chunks

---

## FAISS Index Setup

### Index Type

**HNSW (Hierarchical Navigable Small World)** - Recommended
- Fast approximate nearest neighbor search
- Good for high-dimensional vectors (1024 dims)
- Supports incremental updates

**Alternative: Flat Index**
- Exact search (slower but more accurate)
- Good for smaller datasets (<100K chunks)

**Decision:** Start with **HNSW** (can switch if needed)

### Index Configuration

```python
import faiss

# HNSW index for 1024-dimensional vectors
dimension = 1024
index = faiss.IndexHNSWFlat(dimension, 32)  # 32 = M parameter (connectivity)
index.hnsw.efConstruction = 200  # Construction time vs quality
index.hnsw.efSearch = 50  # Search quality vs speed
```

### Index Storage

**Location:** `data/vector_index/`
- `products_categories.faiss` - FAISS index file
- `products_categories_metadata.json` - Mapping file (faiss_index_id → chunk_id)

**Backup:** Include in daily backups, version control metadata

### Index Management

1. **Initial Build:**
   - Generate all embeddings
   - Add to FAISS index sequentially
   - Save index to disk
   - Store metadata mapping

2. **Incremental Updates:**
   - Detect changed products/categories
   - Regenerate embeddings for changed items
   - Update FAISS index (remove old, add new)
   - Update metadata mapping

3. **Index Loading:**
   - Load FAISS index from disk on startup
   - Load metadata mapping
   - Keep in memory for fast queries

---

## Retrieval API

### Endpoint: `POST /api/content/search`

**Request:**
```json
{
  "query": "Scottish tartan scarves",
  "chunk_types": ["product", "category"],  // Optional filter
  "limit": 10,
  "min_score": 0.5  // Optional relevance threshold
}
```

**Response:**
```json
{
  "success": true,
  "results": [
    {
      "chunk_id": 123,
      "chunk_type": "product",
      "source_id": 456,
      "chunk_text": "...",
      "metadata": {
        "product_name": "Lambswool Scarf",
        "supplier_name": "Lochcarron",
        "sku": "SCARF-001"
      },
      "score": 0.87,
      "faiss_index_id": 42
    }
  ],
  "query_time_ms": 45
}
```

### Implementation

1. **Query Embedding:**
   - Generate embedding for query text
   - Use same model as chunks

2. **Vector Search:**
   - Search FAISS index for top-K nearest neighbors
   - Get `faiss_index_id` and similarity scores

3. **Metadata Retrieval:**
   - Look up chunk details from PostgreSQL using `faiss_index_id`
   - Filter by `chunk_type` if specified
   - Filter by `min_score` if specified

4. **Result Formatting:**
   - Combine FAISS results with PostgreSQL metadata
   - Return formatted results with scores

---

## Implementation Steps

### Step 1: Database Migration
- Create `content_chunks` table
- Add indexes
- Test schema

### Step 2: Chunking Pipeline
- Build text extraction from products/categories
- Implement HTML cleaning
- Implement text normalization
- Test with sample products/categories

### Step 3: Embedding Generation
- Set up embedding model (E5-large)
- Generate embeddings for sample chunks
- Test embedding quality

### Step 4: FAISS Index Setup
- Create FAISS index structure
- Implement index save/load
- Test with sample embeddings

### Step 5: Full Pipeline
- Process all products → chunks → embeddings → FAISS
- Process all categories → chunks → embeddings → FAISS
- Verify index integrity

### Step 6: Retrieval API
- Implement search endpoint
- Test query → embedding → search → results
- Verify performance

### Step 7: Integration Testing
- Test with real queries
- Verify relevance of results
- Performance testing

---

## File Structure

```
utils/
├── vector_search/
│   ├── __init__.py
│   ├── chunking.py          # Text extraction and chunking
│   ├── embeddings.py        # Embedding generation
│   ├── faiss_index.py       # FAISS index management
│   └── retrieval.py         # Search/retrieval logic

blueprints/
└── content_search_api.py   # API endpoints

migrations/
└── create_content_chunks_table.sql

scripts/
├── generate_embeddings.py  # Initial embedding generation
└── update_embeddings.py     # Incremental updates

data/
└── vector_index/
    ├── products_categories.faiss
    └── products_categories_metadata.json
```

---

## Dependencies

**Python Packages:**
- `faiss-cpu` or `faiss-gpu` - Vector similarity search
- `sentence-transformers` - Embedding models (E5-large)
- `beautifulsoup4` - HTML cleaning (already installed)
- `numpy` - Vector operations (already installed)

**Installation:**
```bash
pip install faiss-cpu sentence-transformers
```

---

## Testing Strategy

1. **Unit Tests:**
   - Chunking: Test text extraction and normalization
   - Embeddings: Test embedding generation
   - FAISS: Test index operations

2. **Integration Tests:**
   - Full pipeline: product → chunk → embedding → index → search
   - Query relevance: Verify search results make sense
   - Performance: Query time < 100ms for 10 results

3. **Data Validation:**
   - Verify all products have chunks
   - Verify all categories have chunks
   - Verify embeddings are valid (not NaN, correct dimension)
   - Verify FAISS index integrity

---

## Next Steps

Once Phase 1 is complete:
- Phase 2: Content generation using retrieved chunks
- Phase 3: UI for content generation
- Phase 4: KB integration (reuse same infrastructure)

---

**Status:** Ready to implement  
**Estimated Time:** 2-3 days for full Phase 1 implementation

