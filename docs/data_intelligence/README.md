# Data Intelligence System

**Purpose:** Normalize, analyze, and leverage CLAN's structured data (products, categories, knowledge base) for intelligent content creation, semantic search, and LLM-driven workflows.

---

## Overview

This directory contains documentation for systems that transform CLAN's structured data into intelligent, searchable, and generatable content using LLMs and vector search technologies.

### Key Components

1. **Product & Category Profiles** (`/profiles/`)
   - Editorial-first blog features exploring Scottish heritage, craftsmanship, and culture
   - Uses `clan_products` and `clan_categories` data
   - See: [Product & Category Profiles Documentation](./profiles/PRODUCT_CATEGORY_PROFILES_DOCUMENTATION.md)

2. **Content Generation System** (`/content_generation/`)
   - Vector search infrastructure for semantic retrieval
   - LLM-driven blog post generation from products/categories
   - Future: Knowledge Base integration
   - See: [Content Generation Roadmap](./content_generation/KB_Content_Generation_Roadmap.md)

---

## Architecture

```
Data Sources → Normalization → Vector Search → Content Generation
     ↓              ↓                ↓                ↓
Products      Chunking         FAISS Index    Blog Posts
Categories    Embeddings       Retrieval      Editorial Content
KB (future)   Metadata         Semantic       AI-Generated
```

---

## Current Status

### ✅ Completed

- **Product & Category Profiles**: Fully implemented and documented
- **Vector Search Infrastructure (Phase 1)**: Complete
  - `content_chunks` table
  - Chunking pipeline for products/categories
  - Embedding generation (E5-large-v2)
  - FAISS index with PostgreSQL metadata
  - Retrieval API

- **Content Generation Engine (Phase 2)**: Complete
  - Prompt templates in `llm_prompt` table
  - Generation orchestrator
  - Post creation workflow
  - API endpoints

- **User Interface (Phase 3)**: Complete
  - Content Generator modal in calendar week view
  - Product/category search
  - Generation options
  - Preview and save functionality

### 🚧 In Progress

- Testing and refinement of content generation quality
- Error handling improvements

### 📋 Planned

- **Phase 4**: Knowledge Base Integration
  - KB data download and normalization
  - Chunking KB articles
  - Adding KB chunks to existing vector index
  - Enhanced retrieval with KB context

- **Phase 5**: Advanced Features
  - Idea mining from vector search
  - Multi-source content generation
  - Content suggestions based on semantic similarity

- **Phase 6**: ClanGuide Integration (Future)
  - Unified AI assistant incorporating all data sources
  - Tiered response system
  - LoRA-tuned LLM for CLAN's tone of voice

---

## Documentation Structure

### `/profiles/`
- [Product & Category Profiles Documentation](./profiles/PRODUCT_CATEGORY_PROFILES_DOCUMENTATION.md)
- [Quick Start Guide](./profiles/QUICK_START_GUIDE.md)
- [Implementation Status](./profiles/implementation-status.md)
- [Section Types](./profiles/section-types.md)
- [File Inventory](./profiles/FILE_INVENTORY.md)

### `/content_generation/`
- [Content Generation Roadmap](./content_generation/KB_Content_Generation_Roadmap.md)
- [Vector Search Phase 1 Plan](./content_generation/Vector_Search_Phase1_Plan.md)
- [Content Generation Phases 2-3 Plan](./content_generation/Content_Generation_Phases2-3_Plan.md)
- [Phase 1 Test Results](./content_generation/Phase1_Test_Results.md)
- [Phase 2 Test Results](./content_generation/Phase2_Test_Results.md)
- [Phase 2 Next Steps](./content_generation/Phase2_Next_Steps.md)
- [Implementation Readiness Assessment](./content_generation/Implementation_Readiness_Assessment.md)

---

## Key Design Decisions

1. **Reusability**: All components designed to work with products/categories now, and KB data later
2. **Modularity**: Small, focused files (under 400-500 lines) to prevent bloat
3. **Vector Search**: FAISS/HNSW with PostgreSQL metadata for fast semantic search
4. **LLM Integration**: Reuses existing Ollama infrastructure (`LLMService`)
5. **Database**: PostgreSQL for all metadata and chunk storage
6. **Embeddings**: E5-large-v2 model for semantic representations

---

## Related Documentation

- [Development Rules](../DEVELOPMENT_RULES.md) - File size limits and coding standards
- [ClanGuide Full Plan](../plans/ClanGuide_full.md) - Future unified AI assistant vision

---

**Last Updated:** 2025-01-10

