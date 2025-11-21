# Product Profile Section Structure

**Date:** 2025-01-XX  
**Purpose:** Define a flexible, comprehensive section structure for product profile blog posts that works for almost any product type

---

## Overview

This structure is designed to work for **any product** in the CLAN catalog, from simple accessories to complex items. It leverages:
- Product data from `clan_products`
- Supplier/producer information
- Category heritage data
- Product type classifications (materials, patterns, decorations, occasions, styles)
- Image analysis (when reliable)
- Extrapolation from product type and tags

The structure is **editorial-first** but includes natural commerce links.

---

## Section Structure (10 Sections)

### 1. **Hero Block** (Required)
**Purpose:** Visual introduction and hook

**Content:**
- Hero image (from `product_data.image_url` or AI-generated)
- Headline: Product name + key descriptor (e.g., "6oz Matt Black Hip Flask Lion Rampant: A Scottish Tradition")
- Standfirst: One-sentence summary (from `product_data.short_description` or generated)
- Quick visual identifier (product type, material, or motif)

**Data Sources:**
- `product_data.name`
- `product_data.image_url`
- `product_data.short_description`
- `product_data.product_type_data.core_type`
- `product_data.product_type_data.decorations` (for motifs)

**LLM Extrapolation:**
- Generate compelling headline if name is too technical
- Create standfirst if `short_description` is missing
- Suggest visual style based on product type and occasions

---

### 2. **The Object** (Required)
**Purpose:** Describe what the product is, its design, feel, and distinctive qualities

**Content:**
- Product concept and design philosophy
- Physical characteristics (size, weight, feel, appearance)
- What makes it distinctive
- Design details and aesthetic qualities

**Data Sources:**
- `product_data.description` (main narrative)
- `product_data.specifications`
- `product_data.dimensions`
- `product_data.product_type_data.core_type`
- `product_data.product_type_data.decorations` (motifs, engravings)
- `product_data.product_type_data.patterns` (tartans, designs)
- `product_data.image_url` (visual analysis for design clues)

**LLM Extrapolation:**
- Expand on design philosophy from product type
- Describe aesthetic qualities from image analysis
- Connect decorations/motifs to Scottish symbolism
- Infer feel and quality from materials and product level

---

### 3. **Heritage & Origins** (Conditional - Show if heritage data exists)
**Purpose:** Historical context and Scottish heritage connections

**Content:**
- Historical origins of this product type
- Evolution over time
- Scottish heritage connections
- Cultural significance
- Regional associations

**Data Sources:**
- `product_data.heritage_data.historical_origins.narrative`
- `product_data.heritage_data.evolution.narrative`
- `product_data.heritage_data.scottish_heritage_connections.narrative`
- `product_data.heritage_data.cultural_significance.narrative`
- `product_data.categories[].heritage_data` (category-level heritage)
- `product_data.product_type_data.core_type` (for type-level history)

**LLM Extrapolation:**
- If heritage data missing, research product type history
- Connect to broader Scottish traditions
- Link decorations/motifs to historical significance (e.g., Lion Rampant)
- Infer cultural context from occasions and usage

**Conditional Logic:**
- Show if `heritage_data` exists OR if category has heritage data OR if product type has known history
- Can be collapsed/condensed if minimal data available

---

### 4. **The Maker** (Conditional - Show if supplier/producer data exists)
**Purpose:** Story of the producer, workshop, or brand

**Content:**
- Producer/supplier name and location
- Workshop history and ethos
- Craftsmanship methods
- Materials sourcing
- Optional quote or maker note

**Data Sources:**
- `product_data.supplier_name`
- `product_data.supplier_description`
- `product_data.producer_data` (if available)
- `product_data.product_type_data.materials` (for sourcing story)
- Category context (if producer is category-specific)

**LLM Extrapolation:**
- Research producer if only name available
- Connect materials to producer's expertise
- Infer craftsmanship from product level (classic/luxury/essential)
- Generate producer story from product type and materials

**Conditional Logic:**
- Show if `supplier_name` exists OR if `producer_data` exists
- Can be brief if minimal data, expanded if rich data available

---

### 5. **Materials & Making** (Required)
**Purpose:** How it's made, what it's made from, and production processes

**Content:**
- Key materials and their significance
- Manufacturing processes
- Craftsmanship techniques
- Sustainability and sourcing notes
- Quality indicators

**Data Sources:**
- `product_data.product_type_data.materials`
- `product_data.specifications` (material details)
- `product_data.supplier_description` (craftsmanship methods)
- `product_data.product_level` (classic/luxury/essential - quality indicator)
- `product_data.additional_data` (material-specific info)

**LLM Extrapolation:**
- Expand on material significance (e.g., why this material for this product)
- Describe traditional manufacturing methods for product type
- Connect materials to Scottish heritage (wool, tweed, etc.)
- Infer quality from product level and materials
- Research sustainability if materials suggest it

---

### 6. **In Context** (Required)
**Purpose:** Where this product fits in Scottish life, tradition, and culture

**Content:**
- Traditional use and cultural role
- Seasonal significance
- Occasion appropriateness
- Styling and pairing suggestions
- Modern interpretations

**Data Sources:**
- `product_data.product_type_data.occasions` (gift occasions, events)
- `product_data.product_type_data.styles` (usage styles)
- `product_data.categories` (category context - e.g., "Gifts for Him", "Wedding Gifts")
- `product_data.heritage_data.cultural_significance` (if available)
- `product_data.description` (usage hints)

**LLM Extrapolation:**
- Expand on occasion recommendations from tags
- Suggest styling based on product type and style tags
- Connect to Scottish traditions and customs
- Generate pairing suggestions (e.g., flask with whisky, scarf with Highlandwear)
- Seasonal context from category (e.g., Christmas Gift Guide)

---

### 7. **Features & Specifications** (Required)
**Purpose:** Practical details, options, and technical information

**Content:**
- Key features and capabilities
- Available options (sizes, colors, tartans, engravings, etc.)
- Technical specifications
- Dimensions and sizing
- Product options and customization

**Data Sources:**
- `product_data.description` (feature list)
- `product_data.configurable_options` (sizes, colors, engravings, etc.)
- `product_data.specifications`
- `product_data.dimensions`
- `product_data.additional_data`
- `product_data.product_type_data.attributes` (key features)

**LLM Extrapolation:**
- Organize features into logical groups
- Explain significance of options (e.g., why certain tartans, what engravings mean)
- Connect specifications to use cases
- Generate feature highlights from product type

---

### 8. **Care & Maintenance** (Required)
**Purpose:** How to care for and maintain the product

**Content:**
- Care instructions
- Cleaning methods
- Storage recommendations
- Maintenance tips
- Longevity and durability notes

**Data Sources:**
- `product_data.description` (may include care info)
- `product_data.specifications` (care-related specs)
- `product_data.product_type_data.materials` (material-specific care)
- `product_data.product_level` (quality affects care needs)

**LLM Extrapolation:**
- Generate care instructions from materials (e.g., metal flask care, wool care)
- Research standard care for product type
- Connect durability to product level
- Suggest maintenance based on materials and construction

---

### 9. **Gallery** (Conditional - Show if images available)
**Purpose:** Visual showcase of the product

**Content:**
- 4-6 images showing:
  - Product detail shots
  - Product in use/lifestyle
  - Workshop or making process (if available)
  - Material close-ups
  - Context shots (e.g., flask with whisky, scarf with outfit)

**Data Sources:**
- `product_data.image_url` (main product image)
- Additional images from product data (if available)
- AI-generated images based on product type and context
- Category images (if relevant)

**LLM Extrapolation:**
- Generate image concepts from product type, occasions, and usage
- Suggest lifestyle contexts from occasions tags
- Create detail shot concepts from decorations and materials
- Generate contextual pairings (e.g., flask with whisky, scarf with Highlandwear)

---

### 10. **Explore Further** (Required)
**Purpose:** Natural commerce links and related content

**Content:**
- "View this product on CLAN.com" (link to `product_data.url`)
- "About [Producer Name]" (if producer page exists)
- "Shop [Category Name]" (link to category)
- "Related Products" (similar products or alternatives)
- "More from [Producer]" (if multiple products from same producer)

**Data Sources:**
- `product_data.url` (product page link)
- `product_data.supplier_name` (producer link)
- `product_data.categories` (category links)
- Related products from vector search or category

**LLM Extrapolation:**
- Suggest related products based on product type, materials, occasions
- Generate category exploration links
- Create producer discovery links

---

### 11. **Credits & Sources** (Required)
**Purpose:** Attribution and fact sources

**Content:**
- Image credits
- Fact sources (heritage data sources, research references)
- Data attribution (CLAN product data, category heritage)
- Producer information sources

**Data Sources:**
- Image metadata (if available)
- Heritage data sources (if tracked)
- Product data source (CLAN.com)
- Category heritage sources

---

## Section Flexibility & Conditional Logic

### Always Show:
1. Hero Block
2. The Object
3. Materials & Making
4. In Context
5. Features & Specifications
6. Care & Maintenance
7. Explore Further
8. Credits & Sources

### Conditionally Show:
- **Heritage & Origins**: Show if heritage data exists OR category has heritage OR product type has known history
- **The Maker**: Show if supplier/producer data exists (can be brief if minimal)
- **Gallery**: Show if images available (minimum 1 image, ideally 4-6)

### Content Adaptation:
- **Rich Data**: Expand sections with detailed narratives
- **Minimal Data**: Use concise format, focus on available data
- **Missing Data**: LLM extrapolation from product type, materials, occasions, and category context

---

## Data Mapping Strategy

### Primary Data (Use Directly):
- Product name, description, specifications
- Supplier name and description
- Product type data (materials, patterns, decorations, occasions, styles)
- Category information
- Heritage data (if available)
- Images

### Secondary Data (Extrapolate/Enhance):
- Product type → historical context
- Materials → care instructions, significance
- Occasions → usage context, styling
- Decorations/motifs → symbolism, heritage connections
- Category → cultural context, seasonal relevance
- Product level → quality narrative

### LLM Generation (When Data Missing):
- Standfirst (if short_description missing)
- Heritage context (if heritage_data missing but product type has history)
- Producer story (if only name available)
- Care instructions (from materials)
- Usage context (from occasions and product type)
- Styling suggestions (from styles and occasions)

---

## Section Order Rationale

1. **Hero** - Immediate visual and conceptual hook
2. **The Object** - What it is (foundational understanding)
3. **Heritage & Origins** - Why it matters (historical/cultural context)
4. **The Maker** - Who makes it (craftsmanship story)
5. **Materials & Making** - How it's made (process and quality)
6. **In Context** - Where it fits (usage and culture)
7. **Features & Specifications** - What you get (practical details)
8. **Care & Maintenance** - How to keep it (practical guidance)
9. **Gallery** - Visual showcase (reinforces all above)
10. **Explore Further** - Next steps (commerce links)
11. **Credits & Sources** - Attribution (transparency)

This order flows from **conceptual → contextual → practical → visual → action**.

---

## Implementation Notes

### Section Type IDs:
- `profile_hero`
- `profile_object`
- `profile_heritage`
- `profile_maker`
- `profile_materials`
- `profile_context`
- `profile_features`
- `profile_care`
- `profile_gallery`
- `profile_explore`
- `profile_credits`

### Data Extraction Functions:
- Extract product data from `clan_products`
- Extract supplier/producer data
- Extract category heritage data
- Extract product type classifications
- Analyze image for design clues (when reliable)
- Generate LLM content for missing data

### Content Generation Priority:
1. Use direct data when available
2. Enhance with category/heritage context
3. Extrapolate from product type and tags
4. Generate via LLM only when necessary

---

## Example: Hip Flask (Product ID 131256)

Based on the available data:
- **Hero**: "6oz Matt Black Hip Flask Lion Rampant" + standfirst about Scottish tradition
- **The Object**: Flask design, 6oz capacity, Lion Rampant engraving, matt black finish
- **Heritage & Origins**: History of hip flasks in Scotland, Lion Rampant symbolism, outdoor pursuits tradition
- **The Maker**: Supplier information (if available), UK manufacturing
- **Materials & Making**: Metal construction, engraving process, quality standards
- **In Context**: Outdoor pursuits (shooting, fishing), gift occasions (Gifts for Him, Christmas), Scottish tradition
- **Features & Specifications**: 6oz capacity, matt black finish, Lion Rampant engraving, optional text customization
- **Care & Maintenance**: Metal flask care, cleaning, storage
- **Gallery**: Flask detail, flask with whisky, outdoor context, engraving close-up
- **Explore Further**: Product page, Drinking Vessels category, Gifts for Him
- **Credits**: CLAN product data, heritage sources

---

This structure is designed to be **flexible, comprehensive, and data-driven**, working for any product type while maintaining editorial quality and natural commerce integration.

