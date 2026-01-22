# Vector Tables Summary

**Date:** 2026-01-22  
**Status:** ✅ **ACTIVE** - Vector search system fully operational  
**Purpose:** Comprehensive summary of all vector tables and embedding infrastructure

---

## Overview

The system uses a **unified vector search infrastructure** for semantic similarity matching across multiple content types. All vector data is stored in a single table (`content_chunks`) with a FAISS index for fast similarity search.

---

## Database Schema

### Primary Table: `content_chunks`

**Migration Files:**
- `migrations/20250110_create_content_chunks_table.sql` - Initial table creation
- `migrations/add_post_embeddings.sql` - Extended to support producers and posts

**Table Structure:**
```sql
CREATE TABLE content_chunks (
    id SERIAL PRIMARY KEY,
    chunk_type VARCHAR(20) NOT NULL CHECK (
        chunk_type IN ('product', 'category', 'kb', 'producer', 'post')
    ),
    source_id INTEGER NOT NULL,  -- References product_id, category_id, producer_id, or post_id
    chunk_text TEXT NOT NULL,     -- Normalized text content ready for embedding
    chunk_index INTEGER DEFAULT 0, -- For multi-chunk sources (0 for single-chunk)
    metadata JSONB DEFAULT '{}',   -- Additional context (names, IDs, paths, etc.)
    embedding_model VARCHAR(50),  -- e.g., 'e5-large-v2'
    embedding_dim INTEGER,        -- Dimension of embedding vector (1024)
    faiss_index_id INTEGER,       -- Index position in FAISS for fast lookup
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_embedded_at TIMESTAMP    -- When embedding was last generated
);
```

**Constraints:**
- `chunk_type` must be one of: `'product'`, `'category'`, `'kb'`, `'producer'`, `'post'`
- `source_id` references the appropriate source table based on `chunk_type`

**Indexes:**
- `content_chunks_pkey` - Primary key on `id`
- `idx_content_chunks_type_source` - Composite index on `(chunk_type, source_id)`
- `idx_content_chunks_faiss_id` - Index on `faiss_index_id` (where not null)
- `idx_content_chunks_metadata` - GIN index on `metadata` JSONB column
- `idx_content_chunks_type_embedded` - Composite index on `(chunk_type, last_embedded_at)`
- `idx_content_chunks_post` - Partial index for post chunks
- `idx_content_chunks_producer` - Partial index for producer chunks

---

## Current Data Status

**As of 2026-01-22:**

| Chunk Type | Chunks | Unique Sources | Description |
|------------|--------|----------------|-------------|
| **product** | 1,157 | 1,157 | Product descriptions, specs, supplier info |
| **category** | 259 | 259 | Category descriptions and heritage data |
| **kb** | 696 | 629 | Knowledge base articles (some articles have multiple chunks) |
| **producer** | 3 | 3 | Producer/supplier information |
| **post** | 2 | 2 | Blog post content (theme posts) |
| **TOTAL** | **2,117** | **2,050** | All chunks indexed in FAISS |

---

## Chunk Types Details

### 1. Product Chunks (`chunk_type = 'product'`)

**Source:** `clan_products` table  
**Chunking:** Single chunk per product  
**Content Includes:**
- Product name
- Short description
- Full description (HTML cleaned)
- Supplier/producer name and description
- Specifications
- Additional data (materials, patterns, dimensions)
- Configurable options

**Metadata Fields:**
- `product_name`
- `sku`
- `supplier_name`
- `category_ids`
- `price`

**Usage:** Product discovery, similar product search, content generation context

---

### 2. Category Chunks (`chunk_type = 'category'`)

**Source:** `clan_categories` table  
**Chunking:** Single chunk per category  
**Content Includes:**
- Category name
- Description
- Heritage data (if available):
  - Historical origins
  - Cultural significance
  - Evolution
  - Scottish heritage connections
  - Industrial legacy

**Metadata Fields:**
- `category_name`
- `category_id`
- `parent_id`
- `level`
- `category_path`

**Usage:** Category exploration, heritage context retrieval

---

### 3. Knowledge Base Chunks (`chunk_type = 'kb'`)

**Source:** `clan_kb_articles` table  
**Chunking:** Multi-chunk support (some articles split into multiple chunks)  
**Content Includes:**
- Article name/title
- Short text
- Full HTML text (cleaned)
- Category context

**Metadata Fields:**
- `article_name`
- `article_id`
- `category_id`
- `url_key`

**Usage:** KB article search, content generation with KB context, semantic linking

**Note:** 696 chunks from 629 articles means some articles are split into multiple chunks for better embedding quality.

---

### 4. Producer Chunks (`chunk_type = 'producer'`)

**Source:** Producer/supplier data  
**Chunking:** Single chunk per producer  
**Content Includes:**
- Producer name
- Description
- Heritage/background information

**Metadata Fields:**
- `producer_name`
- `producer_id`

**Usage:** Producer matching for profile posts, supplier discovery

**Status:** Currently 3 producers embedded (extended from original product/category system)

---

### 5. Post Chunks (`chunk_type = 'post'`)

**Source:** `post_development` table (theme posts)  
**Chunking:** Single chunk per post  
**Content Extraction Priority:**
1. `expanded_idea` (most comprehensive)
2. `idea_seed` (core concept)
3. `summary` (condensed)
4. `intro_blurb` (introduction)
5. `basic_idea` (fallback)

Also includes `post.title` and `post.summary` for broader context.

**Metadata Fields:**
- `post_id`
- `post_title`
- `post_type`

**Usage:** Theme post matching to products/categories/suppliers for profile post generation

**Status:** Currently 2 posts embedded (used for profile post theme matching)

---

## FAISS Index

**Location:** `data/vector_index/products_categories.faiss`  
**Type:** HNSW (Hierarchical Navigable Small World)  
**Dimensions:** 1024 (E5-large-v2 model)  
**Total Vectors:** 2,117

**Configuration:**
- M parameter: 32 (connectivity)
- efConstruction: 200 (construction time vs quality)
- efSearch: 50 (search quality vs speed)

**Metadata Mapping:** `data/vector_index/products_categories_metadata.json`  
Maps `faiss_index_id` → `chunk_id` for fast lookup

---

## Embedding Model

**Model:** `intfloat/e5-large-v2`  
**Dimensions:** 1024  
**Provider:** HuggingFace Transformers  
**Usage:** Both query and document embeddings use the same model

**Implementation:**
- `utils/vector_search/embeddings.py` - `EmbeddingGenerator` class
- Uses `sentence-transformers` library
- Supports query/document distinction (E5 model feature)

---

## Related Tables

### `post_development.embedding_overrides`

**Purpose:** Stores manual overrides for vector embedding similarity matches  
**Column:** `embedding_overrides JSONB DEFAULT '{}'`  
**Content:** Stores selected products, suppliers, categories, and best match type when user manually overrides automatic matching

**Added:** Via `migrations/add_post_embeddings.sql`

---

## Key Files & Scripts

### Core Infrastructure
- `utils/vector_search/chunking.py` - Content chunking logic
- `utils/vector_search/embeddings.py` - Embedding generation
- `utils/vector_search/faiss_index.py` - FAISS index management
- `utils/vector_search/retrieval.py` - Semantic search/retrieval
- `utils/vector_search/post_extractor.py` - Post content extraction

### Scripts
- `scripts/generate_embeddings.py` - Batch embedding generation
  - `--products` - Generate product embeddings
  - `--categories` - Generate category embeddings
  - `--kb` - Generate KB article embeddings
  - `--producers` - Generate producer embeddings
  - `--posts` - Generate post embeddings

### API Endpoints
- `POST /api/content/search` - Vector search endpoint
- `POST /header/api/posts/<post_id>/generate-embeddings` - Generate post embeddings and find matches
- `POST /header/api/posts/<post_id>/save-embedding-overrides` - Save manual overrides
- `GET /header/api/posts/<post_id>/get-embedding-overrides` - Get saved overrides

---

## Use Cases

### 1. Profile Post Theme Matching
**Status:** ✅ **IMPLEMENTED**  
**Purpose:** Match theme posts to products/categories/suppliers for profile post generation  
**Files:**
- `utils/profile_matching/post_matcher.py` - Similarity matching
- `utils/profile_matching/normalization.py` - Weighted selection algorithm
- `blueprints/header/api_seo_meta.py` - API endpoints
- `templates/header/includes/vector_embeddings_panel.html` - UI

### 2. Content Generation
**Status:** ✅ **ACTIVE**  
**Purpose:** Retrieve context for LLM-based content generation  
**Usage:** Content generator modal uses vector search to find relevant products/categories

### 3. Product Discovery
**Status:** ✅ **ACTIVE**  
**Purpose:** Find similar products based on semantic similarity  
**Usage:** Product recommendations, alternative product suggestions

### 4. Knowledge Base Search
**Status:** ✅ **ACTIVE**  
**Purpose:** Semantic search across KB articles  
**Usage:** Find relevant KB articles for content generation, linking

---

## Documentation References

### Primary Documentation
- `docs/data_intelligence/content_generation/Vector_Search_Phase1_Plan.md` - Original implementation plan
- `docs/PROFILE_POST_THEME_MATCHING_IMPLEMENTATION.md` - Profile matching implementation
- `docs/data_intelligence/knowledge_base/IMPLEMENTATION_STATUS.md` - KB vector integration
- `docs/data_intelligence/CONTENT_STRUCTURE_ANALYSIS.md` - System overview

### Migration Files
- `migrations/20250110_create_content_chunks_table.sql` - Initial table creation
- `migrations/add_post_embeddings.sql` - Extended support for producers and posts

---

## Maintenance

### Regenerating Embeddings

**Products:**
```bash
python3 scripts/generate_embeddings.py --products
```

**Categories:**
```bash
python3 scripts/generate_embeddings.py --categories
```

**KB Articles:**
```bash
python3 scripts/generate_embeddings.py --kb
```

**Producers:**
```bash
python3 scripts/generate_embeddings.py --producers
```

**Posts:**
```bash
python3 scripts/generate_embeddings.py --posts
```

### Incremental Updates
The system tracks `last_embedded_at` timestamp to support incremental updates. Changed content can be detected and re-embedded without full regeneration.

---

## Future Enhancements

### Planned Extensions
1. **Incremental Update System** - Automatically detect and re-embed changed content
2. **Multiple Embedding Models** - Support for different models per use case
3. **Hybrid Search** - Combine vector search with full-text search
4. **Embedding Versioning** - Track embedding model versions for migration

### Potential New Chunk Types
- `recipe` - Recipe content for semantic matching
- `surname` - Surname profile content
- `theme` - Theme post content (currently using 'post' type)

---

## Statistics

**Total Chunks:** 2,117  
**Total Unique Sources:** 2,050  
**FAISS Index Size:** ~8.7 MB (1024 dims × 2,117 vectors × 4 bytes)  
**Embedding Model:** E5-large-v2 (1024 dimensions)  
**Index Type:** HNSW (Hierarchical Navigable Small World)

**Chunk Distribution:**
- Products: 54.7% (1,157 chunks)
- KB Articles: 32.9% (696 chunks)
- Categories: 12.2% (259 chunks)
- Posts: 0.1% (2 chunks)
- Producers: 0.1% (3 chunks)

---

**Last Updated:** 2026-01-22  
**Status:** ✅ **PRODUCTION READY** - All vector tables operational and actively used
