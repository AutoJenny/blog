# Content Generator — Implementation Status

**Date:** 2025-01-10  
**Status:** Phases 1-3 Complete ✅  
**Location:** Calendar Week View → Content Generator Row

---

## Overview

The Content Generator is a UI-driven system for creating blog posts from products and categories using vector search and LLM content generation. It integrates seamlessly into the existing blog authoring workflow.

---

## Current Implementation Status

### ✅ Phase 1: Vector Search Infrastructure — COMPLETE

**Status:** Fully implemented and tested

**Components:**
- ✅ `content_chunks` table (PostgreSQL)
- ✅ Chunking pipeline (`utils/vector_search/chunking.py`)
- ✅ Embedding generation (`utils/vector_search/embeddings.py`)
- ✅ FAISS index manager (`utils/vector_search/faiss_index.py`)
- ✅ Content retriever (`utils/vector_search/retrieval.py`)
- ✅ Search API (`blueprints/content_search_api.py`)
- ✅ Embedding generation script (`scripts/generate_embeddings.py`)

**Data Sources:**
- Products: `clan_products` table
- Categories: `clan_categories` table

**Chunking Strategy:**
- Products: Single chunk per product (combines name, description, supplier info)
- Categories: Single chunk per category (combines name, description, heritage_data)

**Embeddings:**
- Model: `sentence-transformers/e5-large-v2`
- Dimension: 1024
- Storage: FAISS HNSW index + PostgreSQL metadata

**Location:**
- Index file: `data/vector_index/products_categories.faiss`
- Metadata: `data/vector_index/products_categories_metadata.json`

---

### ✅ Phase 2: Content Generation Engine — COMPLETE

**Status:** Fully implemented and tested

**Components:**
- ✅ Prompt manager (`utils/content_generation/prompt_manager.py`)
- ✅ Post creator (`utils/content_generation/post_creator.py`)
- ✅ Generation orchestrator (`utils/content_generation/generation_orchestrator.py`)
- ✅ Generation API (`blueprints/content_generation_api.py`)

**Prompt Templates:**
- ✅ `product_content_generation` - Product deep-dives
- ✅ `category_content_generation` - Category features
- ✅ `product_comparison_generation` - Product comparisons

**Storage:**
- Prompts stored in `llm_prompt` table
- Generated posts in `post` table
- Sections in `post_section` table
- Product images linked via `post_images`

**Features:**
- ✅ Vector search for context retrieval
- ✅ LLM content generation (Ollama/llama3.2:latest)
- ✅ JSON response parsing with error handling
- ✅ Control character escaping in JSON strings
- ✅ Markdown code block removal
- ✅ Post creation with proper metadata

**API Endpoints:**
- `POST /api/content/generate` - Generate and save blog post
- `POST /api/content/preview` - Preview generation without saving
- `POST /api/content/suggest-ideas` - Get content suggestions from vector search

---

### ✅ Phase 3: User Interface — COMPLETE

**Status:** Fully implemented

**Components:**
- ✅ Content Generator modal (`templates/planning/calendar/content_generator_modal.html`)
- ✅ Modal JavaScript (`static/js/planning/content-generator-modal-core.js`)
- ✅ Modal CSS (`static/css/planning/content-generator-modal.css`)
- ✅ Calendar integration (`templates/planning/calendar/week_view.html`)
- ✅ Calendar API (`blueprints/planning_api_calendar_content_generator.py`)

**UI Features:**
- ✅ Product search with autocomplete
- ✅ Category selection dropdown
- ✅ Generation type selection (deep_dive, feature, comparison)
- ✅ Suggestions panel (idea mining)
- ✅ Preview functionality
- ✅ Save to database
- ✅ Open generated post in new tab

**Calendar Integration:**
- ✅ Content Generator row in week view
- ✅ Filter pill for showing/hiding generated posts
- ✅ Generated posts displayed with source type icons
- ✅ Click to navigate to post editor

**User Flow:**
1. Click "Generate Post" button in Content Generator row
2. Select source type (Product or Category)
3. Search/select product or category
4. Choose generation type
5. Click "Generate" to create post
6. Preview generated content
7. Save to database
8. Post appears in calendar and can be edited

---

## Technical Details

### Database Schema

**`content_chunks` table:**
```sql
- id (SERIAL PRIMARY KEY)
- chunk_type (VARCHAR) - 'product', 'category', or 'kb' (future)
- source_id (INTEGER) - Product or category ID
- chunk_text (TEXT) - Normalized text content
- chunk_index (INTEGER) - For multi-chunk sources
- metadata (JSONB) - Additional context
- embedding_model (VARCHAR) - e.g., 'e5-large-v2'
- embedding_dim (INTEGER) - Dimension of embedding
- faiss_index_id (INTEGER) - Index in FAISS
- created_at, updated_at, last_embedded_at (TIMESTAMP)
```

**`llm_prompt` table:**
- Stores prompt templates for content generation
- Includes system prompts, user prompts, and model parameters

### File Structure

```
utils/
  vector_search/
    __init__.py
    chunking.py          # Content chunking
    embeddings.py        # Embedding generation
    faiss_index.py       # FAISS index management
    retrieval.py         # Semantic search

  content_generation/
    __init__.py
    prompt_manager.py    # Prompt template management
    post_creator.py      # Post creation workflow
    generation_orchestrator.py  # Main generation logic

blueprints/
  content_search_api.py           # Vector search API
  content_generation_api.py       # Generation API
  planning_api_calendar_content_generator.py  # Calendar API

templates/planning/calendar/
  content_generator_modal.html

static/
  js/planning/
    content-generator-modal-core.js
  css/planning/
    content-generator-modal.css

scripts/
  generate_embeddings.py  # One-time embedding generation
```

### Dependencies

**Python:**
- `sentence-transformers==2.2.2` - Embedding generation
- `faiss-cpu==1.7.4` - Vector index
- `numpy==1.24.3` - Numerical operations

**Database:**
- PostgreSQL (existing)
- `content_chunks` table
- `llm_prompt` table

**LLM:**
- Ollama (existing infrastructure)
- Model: `llama3.2:latest` (default)

---

## Known Issues & Limitations

### ✅ Resolved

1. **Duplicate `const modal` declaration** - Fixed
2. **`intercept_context` post_id requirement** - Fixed by creating placeholder posts first
3. **JSON parsing errors** - Fixed with improved parsing (markdown removal, control character escaping)
4. **Product search not triggering** - Fixed with event delegation and debouncing
5. **Calendar API errors** - Fixed with fallback to `calendar_schedule` table

### ⚠️ Current Limitations

1. **File Size**: `content-generator-modal-core.js` exceeds 400-500 line limit (730 lines)
   - **Action**: Should be refactored into smaller modules

2. **Error Handling**: Some edge cases in JSON parsing may need refinement
   - **Action**: Monitor logs and improve as needed

3. **Content Quality**: Generated content quality depends on:
   - LLM model quality
   - Prompt template effectiveness
   - Available context from vector search
   - **Action**: Iterate on prompts and test with various products/categories

---

## Usage

### Generating Content

1. Navigate to Calendar Week View
2. Click "Generate Post" in Content Generator row
3. Select source type (Product or Category)
4. Search for and select a product/category
5. Choose generation type:
   - **Deep Dive**: Comprehensive product/category feature
   - **Feature**: Category overview with cultural context
   - **Comparison**: Compare multiple products (product only)
6. Click "Generate"
7. Review preview
8. Click "Save" to create post in database

### Viewing Generated Posts

- Generated posts appear in the Content Generator row in the calendar
- Filter can be toggled to show/hide generated posts
- Click on a generated post to open it in the post editor

### API Usage

**Generate Post:**
```bash
POST /api/content/generate
{
  "source_type": "product",
  "source_id": 123,
  "generation_type": "deep_dive",
  "tone": "warm",
  "length": "medium"
}
```

**Preview (without saving):**
```bash
POST /api/content/preview
{
  "source_type": "product",
  "source_id": 123,
  "generation_type": "deep_dive"
}
```

**Get Suggestions:**
```bash
POST /api/content/suggest-ideas
{
  "query": "interesting Scottish products",
  "limit": 10
}
```

---

## Future Enhancements

### Phase 4: Knowledge Base Integration (Planned)

- Download KB data from CLAN.com
- Normalize and chunk KB articles
- Add KB chunks to existing vector index
- Enhanced retrieval with KB context
- KB-specific prompt templates

### Phase 5: Advanced Features (Planned)

- Idea mining: Suggest content ideas from vector search
- Multi-source generation: Combine product + category + KB context
- Content suggestions: "You might also like to write about..."
- Semantic similarity: Find related products/categories for comparison posts

### Phase 6: ClanGuide Integration (Future)

- Unified AI assistant incorporating all data sources
- Tiered response system (CLAN data first, then external)
- LoRA-tuned LLM for CLAN's specific tone of voice
- Customer service, knowledge, and companion modes

---

## Testing

### Manual Testing Checklist

- [x] Product search functionality
- [x] Category selection
- [x] Content generation (product deep-dive)
- [x] Content generation (category feature)
- [x] Preview functionality
- [x] Save to database
- [x] Calendar display
- [x] Post navigation
- [x] Error handling (invalid product, network errors)
- [x] JSON parsing with various LLM response formats

### Automated Testing

- Unit tests for chunking, embeddings, retrieval (Phase 1)
- Integration tests for generation pipeline (Phase 2)
- UI tests for modal interactions (Phase 3)

---

## Related Documentation

- [Content Generation Roadmap](./KB_Content_Generation_Roadmap.md)
- [Vector Search Phase 1 Plan](./Vector_Search_Phase1_Plan.md)
- [Content Generation Phases 2-3 Plan](./Content_Generation_Phases2-3_Plan.md)
- [Product & Category Profiles](../products/PRODUCT_CATEGORY_PROFILES_DOCUMENTATION.md)
- [Development Rules](../../DEVELOPMENT_RULES.md)

---

**Last Updated:** 2025-01-10

