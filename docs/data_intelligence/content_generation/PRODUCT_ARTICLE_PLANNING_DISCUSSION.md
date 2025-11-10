# Product Article Planning & CLAN-First Policy — Implementation Plan

**Date:** 2025-01-10  
**Status:** Decisions Finalized — Ready for Implementation  
**Purpose:** Define approach for creating structured product articles with CLAN-first data prioritization

---

## Overview

This document discusses how to create comprehensive product articles using CLAN's own product data as the primary, trusted source, with LLM filling gaps only where CLAN data is unavailable. It also addresses reintroducing planning stages for generated product posts (similar to themed posts) to ensure structured, high-quality content.

---

## Available CLAN Product Data Fields

Based on the `clan_products` table schema and current chunking implementation, we have access to:

### Core Product Information
- **`id`** - Product ID from clan.com
- **`sku`** - Unique product identifier
- **`name`** - Product title/name
- **`price`** - Product price (DECIMAL)
- **`image_url`** - Main product image URL
- **`url`** - Product page URL on clan.com
- **`short_description`** - Brief product description (text)
- **`description`** - Full product description (HTML, can be cleaned to text)

### Producer/Supplier Information
- **`supplier_name`** - Manufacturer/supplier name (e.g., "Lochcarron", "William Lockie")
- **`supplier_description`** - HTML supplier information (craftsmanship, heritage, location)

### Product Variants & Options
- **`configurable_options`** - JSONB array of product options
  - Structure: `[{"option": "Size", "options": [{"label": "S"}, {"label": "M"}]}, {"option": "Colour", "options": [{"label": "Navy"}, {"label": "Red"}]}]`
  - Can include: Sizes, Colors, Tartans, Materials, etc.

### Category Relationships
- **`category_ids`** - JSONB array of category IDs this product belongs to
  - Can be used to fetch category context via `clan_categories` table

### Timestamps
- **`clan_created_at`** - When product was created on clan.com
- **`clan_updated_at`** - When product was last updated
- **`first_seen_at`** - When we first discovered the product
- **`last_updated`** - When our record was last modified

### Extended Fields (via API enrichment)
- **`all_images`** - Complete image gallery (fetched on-demand via `/api/clan/products/<sku>/full?all_images=true`)
- **`specifications`** - JSONB for dimensions, materials, etc. (if added via profiles migration)
- **`producer_id`** - Link to `producers` table (if added via profiles migration)

### Category Data (via `clan_categories`)
- **`name`** - Category name
- **`description`** - Category description
- **`heritage_data`** - JSONB with:
  - `historical_origins`
  - `cultural_significance`
  - `evolution`
  - `scottish_heritage_connections`

---

## Proposed Product Article Structure

Based on the user's suggestion and best practices for product content, articles should follow a structured pattern:

### Standard Sections for Product Articles

1. **Introduction & Historical Context**
   - Product's place in Scottish culture/history
   - Origins and traditional use
   - Cultural significance

2. **Craftsmanship & Materials**
   - How it's made
   - Materials used
   - Production methods
   - Producer/supplier information

3. **Features & Specifications**
   - Product details
   - Available options (sizes, colors, etc.)
   - Technical specifications
   - Care instructions

4. **How to Use / Practical Guide**
   - When and how to use the product
   - Styling tips
   - Occasion recommendations
   - Pairing suggestions

5. **Benefits & Value**
   - Why choose this product
   - Quality and durability
   - Heritage value
   - Investment perspective

6. **Alternative Products**
   - Alternative options at different price points (cheaper or more luxury versions)
   - Differently detailed versions of similar products
   - Different items serving the same need or occasion
   - When to choose each alternative
   - Comparison highlights

7. **Conclusion / Call to Action**
   - Summary
   - Link to product page
   - Related products

---

## Reintroducing Planning Stages for Generated Posts

Currently, generated posts skip planning stages and go directly to taxonomy. For product articles, we should reintroduce the planning workflow (similar to themed posts) to ensure structured, high-quality content.

### Proposed Pipeline for Generated Product Posts

Based on `config/post_type_pipeline_configs.py`, themed posts have these planning stages:
- `taxonomy` - Assign taxonomy
- `idea-generation` - Expand idea
- `topic-brainstorming` - Generate topics
- `section-structure-design` - Design structure
- `section-ideas` - Section ideas
- `section-titling` - Section titles

**For generated product posts, we should:**

1. **Keep `taxonomy`** (already preset, but allow refinement)
2. **Add `product-data-review`** - Review and validate CLAN product data
3. **Add `topic-brainstorming`** - Generate topics based on product data + standard sections
4. **Add `section-structure-design`** - Design structure (can use standard template)
5. **Add `section-ideas`** - Generate section-specific ideas
6. **Add `section-titling`** - Finalize section titles
7. **Continue to `drafting`** - Author drafts

### Modified Pipeline Configuration

```python
'generated': {
    'active': True,
    'steps': [
        'taxonomy',                    # Already preset, allow refinement
        'product-data-review',        # NEW: Review CLAN product data
        'topic-brainstorming',        # Generate topics from CLAN data + standard sections
        'section-structure-design',   # Design structure (template-based)
        'section-ideas',              # Section-specific ideas
        'section-titling',            # Finalize section titles
        'drafting',                   # Author drafts
        'image-concepts',             # Image concepts
        'image-prompts',              # Image prompts
        'image-captions',             # Image captions
        'image-generation',           # Generate images
        'optimise',                   # Optimize images
        'header-title-summary',       # Header title/summary
        'header-image-prompt',        # Header image prompt
        'header-image-details',       # Header image details
        'header-image-generate',      # Header image generation
        'header-image-optimise',      # Header image optimization
        'header-seo-meta',            # SEO metadata
        'final-review'               # Final review
    ]
}
```

---

## CLAN-First Policy Implementation

### Core Principle

**CLAN's own data is the primary, trusted source. LLM should only fill gaps where CLAN data is unavailable or insufficient.**

### Data Priority Hierarchy

1. **Tier 1: CLAN Product Data (Highest Priority)**
   - Product name, description, supplier information
   - Producer/supplier details
   - Product specifications
   - Category information
   - **Action:** Use directly, never override with LLM

2. **Tier 2: CLAN Category Heritage Data**
   - Historical origins
   - Cultural significance
   - Evolution
   - Scottish heritage connections
   - **Action:** Use directly, supplement with LLM only if missing

3. **Tier 3: Related CLAN Products/Categories**
   - Similar products in same category
   - Related categories
   - **Action:** Use for context, but prioritize primary product data

4. **Tier 4: LLM General Knowledge (Lowest Priority)**
   - General Scottish history/culture
   - Traditional uses
   - Styling tips
   - **Action:** Only use when CLAN data is unavailable or insufficient

### Implementation Strategy

#### 1. Data Extraction & Validation Stage (`product-data-review`)

**Purpose:** Extract and validate all available CLAN data before generation

**Process:**
1. Fetch complete product data from `clan_products` table
2. Fetch category data from `clan_categories` table (via `category_ids`)
3. Fetch producer data if `producer_id` exists
4. Extract heritage data from category if available
5. Display extracted data in UI for human review
6. Mark which fields are present/missing
7. Flag any data quality issues

**UI Display:**
```
Product Data Review
├── Core Information
│   ├── Name: [CLAN data] ✓
│   ├── Description: [CLAN data] ✓
│   └── Price: [CLAN data] ✓
├── Producer Information
│   ├── Supplier Name: [CLAN data] ✓
│   └── Supplier Description: [CLAN data] ✓
├── Specifications
│   ├── Options: [CLAN data] ✓
│   └── Dimensions: [CLAN data] ✗ (missing)
└── Category Heritage
    ├── Historical Origins: [CLAN data] ✓
    └── Cultural Significance: [CLAN data] ✓
```

#### 2. Prompt Engineering with CLAN-First Tags

**Strategy:** Use structured prompts that explicitly prioritize CLAN data

**Template Structure:**
```
You are writing a blog post about a Scottish product for CLAN.com.

=== CLAN DATA (USE THIS FIRST - DO NOT OVERRIDE) ===
Product Name: {product_name}
Product Description: {product_description}
Supplier: {supplier_name}
Supplier Information: {supplier_description}
Category: {category_name}
Heritage Data: {heritage_data}

=== RELATED CLAN DATA (USE FOR CONTEXT) ===
Related Products: {related_products}
Category Context: {category_context}

=== ALTERNATIVE PRODUCTS (FOR ALTERNATIVE PRODUCTS SECTION) ===
Alternative Products: {alternative_products}
- Same category alternatives: {same_category_products}
- Similar products (vector search): {similar_products}
- Price alternatives: {price_alternatives} (cheaper: {cheaper_products}, luxury: {luxury_products})
- Same need/occasion: {same_need_products}

=== LLM SUPPLEMENTATION (ONLY IF CLAN DATA MISSING OR < 50 WORDS) ===
If any of the following are missing from CLAN data OR are less than 50 words, you may supplement:
- Historical context (if heritage_data.historical_origins is missing or < 50 words)
- Cultural significance (if heritage_data.cultural_significance is missing or < 50 words)
- Styling tips (if not in product description or description < 50 words)
- Care instructions (if not in specifications or specifications < 50 words)

IMPORTANT: If CLAN data exists but is < 50 words, use it as the foundation and expand with LLM knowledge.

=== REQUIREMENTS ===
1. ALWAYS use CLAN product name exactly as provided
2. ALWAYS use CLAN supplier information if available
3. ALWAYS prioritize CLAN heritage data over general knowledge
4. ONLY use LLM knowledge when CLAN data is explicitly missing
5. Mark any LLM-supplemented content with [GENERAL KNOWLEDGE] tag
6. Maintain CLAN's warm, professional Scottish tone
```

#### 3. Section-Specific Data Mapping

**Map CLAN data to standard sections:**

| Section | Primary CLAN Data Source | LLM Supplement (if missing) |
|---------|-------------------------|----------------------------|
| Introduction & Historical Context | `heritage_data.historical_origins` | General Scottish history |
| Craftsmanship & Materials | `supplier_description`, `specifications` | General production methods |
| Features & Specifications | `description`, `configurable_options`, `specifications` | General product features |
| How to Use | `description` (if includes usage) | Styling tips, occasion recommendations |
| Benefits & Value | `supplier_description` (quality), `description` | General value propositions |
| Alternative Products | Related products from `category_ids`, vector search for similar products | General product recommendations |
| Conclusion | Product name, URL | Summary, related products |

#### 4. Validation & Quality Checks

**Before generation:**
- Verify all CLAN data fields are extracted correctly
- Check for missing critical fields
- Validate data quality (non-empty, meaningful content)

**After generation:**
- Verify CLAN data was used correctly (not overridden)
- Check for [GENERAL KNOWLEDGE] tags where LLM supplemented
- Validate that LLM didn't contradict CLAN data
- Flag any sections that rely heavily on LLM (for human review)

#### 5. Human Review Interface

**Display generated content with data source indicators:**

```
Section: Introduction & Historical Context
├── Source: CLAN heritage_data.historical_origins ✓
└── Content: [Generated text using CLAN data]

Section: Craftsmanship & Materials
├── Source: CLAN supplier_description ✓
├── Source: CLAN specifications ✓
└── Content: [Generated text using CLAN data]

Section: How to Use
├── Source: LLM (CLAN data missing) ⚠️
└── Content: [Generated text with [GENERAL KNOWLEDGE] tags]
```

---

## Technical Implementation Considerations

### 1. Data Extraction Module

Create `utils/content_generation/clan_data_extractor.py`:

```python
class ClanDataExtractor:
    """Extract and validate CLAN product data for content generation."""
    
    def extract_product_data(self, product_id: int) -> Dict:
        """Extract all available CLAN product data."""
        # Fetch from clan_products table
        # Fetch category data
        # Fetch producer data if available
        # Return structured data with presence flags
    
    def validate_data_completeness(self, product_data: Dict) -> Dict:
        """Check which fields are present/missing."""
        # Return validation report
    
    def format_for_prompt(self, product_data: Dict) -> str:
        """Format CLAN data for LLM prompt with priority tags."""
        # Structure with CLAN-FIRST tags
    
    def find_alternative_products(self, product_id: int, limit: int = 5) -> List[Dict]:
        """Find alternative products for the Alternative Products section."""
        # Strategy 1: Same category products (via category_ids)
        # Strategy 2: Vector search for similar products (semantic similarity)
        # Strategy 3: Price-based alternatives (cheaper/more luxury)
        # Strategy 4: Same producer/supplier products
        # Return list of alternative products with metadata (price, category, similarity score)
```

### 2. Enhanced Prompt Templates

Update `llm_prompt` table with CLAN-first templates:

- `product_article_topic_brainstorming` - Generate topics from CLAN data + standard sections
- `product_article_section_structure` - Design structure (template-based, CLAN data prioritized)
- `product_article_section_ideas` - Section-specific ideas (CLAN data first)
- `product_article_section_titling` - Finalize titles (CLAN terminology preferred)

### 3. Planning Stage UI Components

Create new planning stages for generated posts:

- `templates/planning/concept/product_data_review.html` - Review CLAN data
- `templates/planning/concept/product_topic_brainstorming.html` - Generate topics
- `templates/planning/concept/product_section_structure.html` - Design structure
- `templates/planning/concept/product_section_ideas.html` - Section ideas
- `templates/planning/concept/product_section_titling.html` - Section titles

### 4. Data Source Tracking

Add metadata to track data sources:

```python
# In post_development table or new table
{
    "data_sources": {
        "product_name": "clan_products.name",
        "supplier_info": "clan_products.supplier_description",
        "heritage_data": "clan_categories.heritage_data",
        "styling_tips": "llm_general_knowledge"
    },
    "data_completeness": {
        "core_info": 1.0,  # 100% complete
        "heritage": 0.8,   # 80% complete
        "specifications": 0.6  # 60% complete
    }
}
```

---

## Decisions Made

Based on discussion, the following decisions have been finalized:

### 1. Standard Section Template
**Decision:** Follow a **rigid structure** (which can be amended in future if needed)

**Implementation:**
- Enforce the 7-section template strictly
- Sections cannot be removed or reordered during initial generation
- Future amendments can be made to the template itself if needed

### 2. LLM Supplementation Threshold
**Decision:** Use **~50 words as threshold** (configurable variable)

**Implementation:**
- If CLAN data field is < 50 words, consider it insufficient and allow LLM supplementation
- Make threshold configurable (stored in config or database)
- Can be updated based on experience without code changes

### 3. Heritage Data Priority
**Decision:** If conflicts occur, **prioritize product-specific information** over category heritage data

**Implementation:**
- Product description/supplier info takes precedence
- Category heritage data used only when product data is missing
- Flag conflicts for human review (optional)

### 4. Human Review Requirements
**Decision:** Human review **not required, but enabled** (optional)

**Implementation:**
- LLM-supplemented content marked with [GENERAL KNOWLEDGE] tags
- UI provides review interface but doesn't block publishing
- Authors can review and edit as needed

### 5. Data Quality Standards
**Decision:** Require **minimum data completeness**: name, description, supplier

**Implementation:**
- Validation check before generation
- Must have: `name`, `description` (or `short_description`), `supplier_name`
- Block generation if minimum requirements not met
- Display data completeness report in UI

### 6. Section Customization
**Decision:** Allow authors to **add/remove/reorder sections** after generation

**Implementation:**
- Initial generation follows rigid template
- After generation, authors can:
  - Add custom sections
  - Remove sections (with confirmation)
  - Reorder sections via drag-and-drop
- Changes saved to `post_development.section_structure`

### 7. Alternative Products Section
**Decision:** **Always include** alternative products section

**Implementation:**
- Always generate Alternative Products section (section 6)
- Use multiple strategies to find alternatives:
  - Same category products (via `category_ids`)
  - Vector search for similar products (semantic similarity)
  - Price-based alternatives (cheaper/more luxury)
  - Same producer/supplier products
  - Cross-category alternatives (same need/occasion via vector search)
- Aim for 3-5 alternative products
- Include price comparisons (explicit: cheaper/more luxury)
- Use vector search to determine "same need/occasion"

### 8. Image Strategy
**Decision:** 
- **Auto-pull for sections** from `clan_products.image_url` and `all_images`
- **Generate aspirational hero/header image** featuring the product

**Implementation:**
- **Section Images:** Automatically pull product images from CLAN data
  - Use `image_url` for main product image
  - Use `all_images` API endpoint for image gallery
  - Link images to sections automatically
  
- **Hero/Header Image:** Generate aspirational image via imaging LLM
  - Send main product image (`image_url`) to imaging LLM
  - Provide careful instructions about:
    - What the product features
    - How to represent it in the generated image
    - Aspirational/lifestyle context
    - CLAN brand aesthetic
  - Special programming required for product image → LLM image generation pipeline
  - Store generated hero image separately from product images

---

## Implementation Roadmap

### Phase 1: Data Extraction & Validation
1. **Create `ClanDataExtractor` module** (`utils/content_generation/clan_data_extractor.py`)
   - Extract product data from `clan_products`
   - Extract category/heritage data from `clan_categories`
   - Extract producer data if available
   - Validate minimum requirements (name, description, supplier)
   - Check data completeness (< 50 words threshold, configurable)
   - Format data for prompts with CLAN-first tags

2. **Implement `find_alternative_products()` method**
   - Same category products (via `category_ids`)
   - Vector search for similar products
   - Price-based alternatives (cheaper/more luxury)
   - Same producer/supplier products
   - Cross-category alternatives (same need/occasion)

### Phase 2: Planning Stages UI
3. **Create planning stage templates**
   - `product_data_review.html` - Review CLAN data with completeness indicators
   - `product_topic_brainstorming.html` - Generate topics from CLAN data + 7-section template
   - `product_section_structure.html` - Display rigid 7-section structure (read-only initially)
   - `product_section_ideas.html` - Generate section-specific ideas
   - `product_section_titling.html` - Finalize section titles

4. **Update pipeline configuration**
   - Add `generated` post type to `config/post_type_pipeline_configs.py`
   - Include all planning stages in pipeline
   - Update navigation to show planning stages for generated posts

### Phase 3: Prompt Templates & Generation
5. **Create CLAN-first prompt templates**
   - Update `llm_prompt` table with new templates
   - Include CLAN-first tags and data priority hierarchy
   - Add alternative products prompt template
   - Include 50-word threshold logic in prompts (configurable)

6. **Update generation orchestrator**
   - Integrate `ClanDataExtractor`
   - Use CLAN data extraction before generation
   - Pass alternative products to prompts
   - Mark LLM-supplemented content with [GENERAL KNOWLEDGE] tags

### Phase 4: Image Handling
7. **Implement section image auto-pull**
   - Automatically link product images from `clan_products.image_url`
   - Fetch `all_images` via API for image gallery
   - Link images to appropriate sections

8. **Implement hero/header image generation**
   - Special pipeline for product image → LLM image generation
   - Send main product image to imaging LLM
   - Provide detailed instructions about product features
   - Generate aspirational/lifestyle image
   - Store separately from product images

### Phase 5: Data Source Tracking & Validation
9. **Add data source tracking**
   - Track which data sources were used for each section
   - Store in `post_development` table (JSONB field)
   - Display data source indicators in UI

10. **Implement validation checks**
    - Pre-generation: Check minimum requirements (name, description, supplier)
    - Post-generation: Verify CLAN data usage
    - Flag LLM-supplemented content for optional review

### Phase 6: Testing & Refinement
11. **Test with sample products**
    - Test with products with complete CLAN data
    - Test with products with missing data (trigger LLM supplementation)
    - Test alternative products discovery
    - Test image auto-pull and hero generation
    - Validate CLAN-first policy adherence

12. **Refine based on experience**
    - Adjust 50-word threshold if needed (configurable)
    - Refine alternative products discovery strategies
    - Improve prompt templates based on output quality

---

## Related Documentation

- [Content Generator Status](./CONTENT_GENERATOR_STATUS.md)
- [Content Generation Roadmap](./KB_Content_Generation_Roadmap.md)
- [Product & Category Profiles](../profiles/PRODUCT_CATEGORY_PROFILES_DOCUMENTATION.md)
- [Vector Search Phase 1 Plan](./Vector_Search_Phase1_Plan.md)

---

**Last Updated:** 2025-01-10

