# Knowledge Base Content Generation — Implementation Roadmap
**Date:** 2025-01-10 (Revised)  
**Purpose:** Social Media & Blog Content Generation from Products, Categories, and Knowledge Base  
**Scope:** LLM-driven blog post creation using vector search and semantic retrieval

> **Note:** This roadmap is part of the [Data Intelligence System](../README.md). See [Content Generator Status](./CONTENT_GENERATOR_STATUS.md) for current implementation status.

---

## Overview
Build a content generation system that mines product/category data (and later KB data) to create blog posts. **Starting with products/categories** to build the infrastructure, then adding KB data using the same system. Designed as a reusable component for future ClanGuide expansion.

---

## Implementation Phases (Revised Order)

### **Phase 1: Products/Categories Vector Search Infrastructure** ⚡ STARTING HERE
- **1.1** Design chunking strategy for products/categories data
  - Products: Combine `name`, `description`, `short_description`, `supplier_name`, `supplier_description`
  - Categories: Combine `name`, `description`, `heritage_data` (if available)
- **1.2** Create `content_chunks` table for storing chunks + metadata
- **1.3** Build chunking pipeline: extract text → normalize → chunk (800-1200 tokens)
- **1.4** Generate embeddings (E5-large or bge-large) for each chunk
- **1.5** Set up FAISS/HNSW vector index with PostgreSQL metadata
- **1.6** Create retrieval API: query → vector search → top-K chunks

**Output:** Working vector search system for products/categories data

**Data Sources:**
- `clan_products`: name, description, short_description, supplier_name, supplier_description
- `clan_categories`: name, description, heritage_data (JSONB)

---

### **Phase 2: Content Generation Engine (Products/Categories)**
- **2.1** Build retrieval system: query → vector search → top-K relevant chunks
- **2.2** Create prompt templates for:
  - Product deep-dives ("write about product X using product context")
  - Category features ("write about category Y with cultural context")
  - Product comparisons ("compare products in category Z")
- **2.3** Integrate with existing Ollama LLM infrastructure (`LLMService`)
- **2.4** Create content generation pipeline:
  - Select product/category
  - Retrieve relevant chunks via vector search
  - Generate headline (LLM)
  - Generate post structure (outline)
  - Generate sections with retrieved context
  - Pull product images from existing product data
- **2.5** Integrate with existing blog post creation workflow (`post` table)

**Output:** End-to-end workflow from product/category → generated blog post draft

---

### **Phase 3: User Interface (Products/Categories)**
- **3.1** Add "Content Generator" row to calendar (like Profiles row)
- **3.2** Product/category selector with preview
- **3.3** Idea suggestion panel (query vector index for interesting products/categories)
- **3.4** Generation modal (similar to `profile_modal.html`)
- **3.5** Generation controls (tone, length, focus areas)
- **3.6** Preview/edit generated content before saving to post
- **3.7** Product image integration (auto-pull from product data)

**Output:** UI integrated into existing blog workflow, generating posts from products/categories

---

### **Phase 4: Knowledge Base Integration** 🔄 LATER (when KB data available)
- **4.1** Download Knowledge Base content from CLAN.com (`/knowledge` endpoints)
- **4.2** Design database schema for KB storage (articles, sections, metadata)
- **4.3** Create migration scripts to populate `clan_knowledge_base` tables
- **4.4** Apply same chunking pipeline to KB data (reuse Phase 1 infrastructure)
- **4.5** Generate embeddings and add to existing vector index
- **4.6** Link KB entries to products/categories via foreign keys
- **4.7** Extend retrieval to include KB chunks in search results
- **4.8** Add KB-specific prompt templates (Tartan Designer guides, cultural themes)

**Output:** KB data integrated into same vector search and generation system

---

### **Phase 5: Enhanced Generation (with KB)**
- **5.1** Extend idea mining to query KB for interesting topics/services
- **5.2** Add KB-specific generation types:
  - Service guides ("write Tartan Designer how-to")
  - Cultural content ("write about heritage theme Y")
  - Combined posts ("product X + KB context about its cultural significance")
- **5.3** Multi-source retrieval: products + categories + KB chunks
- **5.4** Enhanced prompt templates using KB context

**Output:** Full content generation system with products, categories, and KB

---

### **Phase 6: Automation & Refinement**
- **6.1** Scheduled product/category embedding updates (when data changes)
- **6.2** Scheduled KB sync and embedding updates (weekly)
- **6.3** Quality checks (tone, accuracy, citations)
- **6.4** Usage analytics (what topics/products generate most content)
- **6.5** Re-ranker for relevance (cross-encoder model)

**Output:** Self-maintaining system with quality controls

---

## Key Design Decisions

**Embeddings:** Yes, required for semantic search and idea mining  
**Vector Store:** FAISS/HNSW (local) with PostgreSQL metadata — compatible with future ClanGuide  
**LLM:** Reuse existing Ollama infrastructure (`LLMService` from `blueprints.llm_actions`)  
**Data Flow:** Products/Categories → Chunks → Embeddings → Vector Index → LLM Retrieval → Content Generation  
**Later:** KB → Same pipeline → Same vector index → Enhanced retrieval  
**Integration:** New module in existing blog authoring workflow, not separate system

**Chunking Strategy:**
- Products: Single chunk per product (combine all text fields)
- Categories: Single chunk per category (combine name, description, heritage_data)
- KB (later): Multiple chunks per article (800-1200 tokens with overlap)

**Reusability:**
- Same chunking pipeline for products/categories and KB
- Same vector index (just add more chunks)
- Same retrieval system (works with any chunk type)
- Same generation engine (just different prompt templates)

---

## Future Compatibility
All components designed to be reusable for full ClanGuide:
- Vector index structure compatible
- Retrieval system extensible
- LLM integration layer shared
- Data normalization process reusable
- KB integration is additive, not replacement

