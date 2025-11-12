# Data Intelligence System

**Purpose:** Normalize, analyze, and leverage CLAN's structured data (products, categories, knowledge base) for intelligent content creation, semantic search, and LLM-driven workflows.

---

## Overview

This directory contains documentation for systems that transform CLAN's structured data into intelligent, searchable, and generatable content using LLMs and vector search technologies.

### Key Components

1. **Products** (`/products/`)
   - Product & Category Profiles: Editorial-first blog features exploring Scottish heritage, craftsmanship, and culture
   - Product Data Parsing: Product type classification and data structure parsing
   - Product Search: Smart semantic search for products
   - See: [Products Documentation](./products/README.md)

2. **Heritage Research System** (`/heritage_research/`)
   - Multi-stage research for category heritage data
   - Wikipedia integration (Phase 1 complete)
   - Google Search integration (Phase 3 planned)
   - See: [Heritage Research Documentation](./heritage_research/SYSTEM_DOCUMENTATION.md)

3. **Content Generation System** (`/content_generation/`)
   - Vector search infrastructure for semantic retrieval
   - LLM-driven blog post generation from products/categories
   - Future: Knowledge Base integration
   - See: [Content Generation Roadmap](./content_generation/KB_Content_Generation_Roadmap.md)

4. **Knowledge Base** (`/knowledge_base/`)
   - Knowledge Base integration (planned)
   - Future integration with vector search and content generation

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
- **Product Data Enhancement**: 
  - Product type parsing (core_type, subtype, materials, patterns, decorations, etc.)
  - Product level classification (classic, luxury, essential)
  - Enhanced product data fields (additional_data, dimensions, product_type_data)
- **Heritage Research System (Phase 1)**: Complete
  - Wikipedia API integration
  - Multi-dimensional research (historical origins, cultural significance, evolution, etc.)
  - LLM synthesis with Mistral 7B
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
- **Product Pipeline Simplification**: Complete
  - Reduced from 6 to 4 stages for `generated` posts
  - Section content mapping stage
- **User Interface (Phase 3)**: Complete
  - Content Generator modal in calendar week view
  - Product/category search (simple filter + semantic "Smart Search")
  - Generation options
  - Preview and save functionality

### 🚧 In Progress

- Product type parsing review (305 products need review)
- Smart product search enhancement (relevance issues)
- Heritage data truncation fix
- Testing and refinement of content generation quality

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

### `/products/`
- [Products Documentation](./products/README.md) - Overview of all product-related systems
- [Product & Category Profiles Documentation](./products/PRODUCT_CATEGORY_PROFILES_DOCUMENTATION.md) - Main profiles documentation
- `/products/profiles/` - Profile-specific documentation (Quick Start, Implementation Status, Section Types, File Inventory)
- `/products/data/` - Product data parsing & classification (Type Parsing Design, Planning Review, Pipeline Checklist)
- `/products/search/` - Smart product search implementation

### `/knowledge_base/`
- Knowledge Base integration documentation (coming soon)

### `/content_generation/`
- [Content Generation Roadmap](./content_generation/KB_Content_Generation_Roadmap.md)
- [Content Generator Status](./content_generation/CONTENT_GENERATOR_STATUS.md)
- [Vector Search Phase 1 Plan](./content_generation/Vector_Search_Phase1_Plan.md)
- [Content Generation Phases 2-3 Plan](./content_generation/Content_Generation_Phases2-3_Plan.md)
- [Product Article Planning Discussion](./content_generation/PRODUCT_ARTICLE_PLANNING_DISCUSSION.md)

### `/heritage_research/`
- [System Documentation](./heritage_research/SYSTEM_DOCUMENTATION.md)
- [Quick Reference](./heritage_research/QUICK_REFERENCE.md)
- [Current Implementation Status](./heritage_research/CURRENT_IMPLEMENTATION_STATUS.md)
- [Enhanced Heritage Research Proposal](./heritage_research/ENHANCED_HERITAGE_RESEARCH_PROPOSAL.md)
- [Implementation Plan](./heritage_research/IMPLEMENTATION_PLAN.md)

### Top-Level Documents
- [Project Status Summary](./PROJECT_STATUS_SUMMARY.md) - Comprehensive project overview and status

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

**Last Updated:** 2025-11-11

