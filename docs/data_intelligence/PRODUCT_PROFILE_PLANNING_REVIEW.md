# Product Profile Planning Stage Review

**Date:** 2025-11-11  
**Purpose:** Review planning stages for product profiles and assess if simplification is needed

---

## Executive Summary

The current 4-step planning process (`taxonomy` → `product-data-review` → `topic-brainstorming` → `section-structure-design` → `section-ideas` → `section-titling`) appears **over-engineered for product profiles** where we have structured data readily available. 

**Recommendation:** Simplify to 2-3 essential stages that leverage existing CLAN data directly, with minimal LLM intervention for structure (since sections are predefined).

---

## Product Profile Sections (Decided Structure)

**IMPORTANT:** There are TWO different structures:

### Structure A: Product Profiles (`profile` post type)
From `docs/product-category-profiles-planning.md` - 8 sections:
1. Hero Block
2. The Object
3. The Maker
4. In Context
5. Materials & Making
6. Gallery
7. Explore Further
8. Credits & Sources

### Structure B: Generated Product Articles (`generated` post type) - **THIS IS WHAT POST 88 USES**
From `docs/data_intelligence/content_generation/PRODUCT_ARTICLE_PLANNING_DISCUSSION.md` - 7 sections:

**For the current work (post 88, `generated` type), we use Structure B:**

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
   - Alternative options at different price points
   - Differently detailed versions
   - Different items serving the same need
   - When to choose each alternative
   - Comparison highlights

7. **Conclusion / Call to Action**
   - Summary
   - Link to product page
   - Related products

**The following analysis is based on Structure B (7 sections for generated posts):**

### 1. Introduction & Historical Context
- **Purpose:** Product's place in Scottish culture/history, origins, cultural significance
- **Content:** Historical background, traditional use, cultural importance
- **Data Source:** 
  - Primary: `heritage_data.historical_origins.narrative`
  - Secondary: `heritage_data.cultural_significance.narrative`, `heritage_data.scottish_heritage_connections.narrative`
  - Context: Category description, product description

### 2. Craftsmanship & Materials
- **Purpose:** How it's made, materials, production methods, producer information
- **Content:** Manufacturing process, materials used, producer/supplier details
- **Data Source:**
  - Primary: `supplier_description` (craftsmanship, methods)
  - Secondary: `specifications`, `additional_data` (materials), `supplier_name`
  - Context: `producer_data` (if available)

### 3. Features & Specifications
- **Purpose:** Product details, available options, technical specifications, care instructions
- **Content:** Product features, sizes/colors/tartans, specs, care info
- **Data Source:**
  - Primary: `description` (product details), `configurable_options` (sizes, colors, etc.)
  - Secondary: `specifications`, `additional_data`, `dimensions`
  - Context: Product description may include care instructions

### 4. How to Use / Practical Guide
- **Purpose:** When and how to use, styling tips, occasion recommendations, pairing suggestions
- **Content:** Usage guidance, styling advice, when to wear/use, what to pair with
- **Data Source:**
  - Primary: `description` (if includes usage/styling)
  - Secondary: Category context, heritage_data (cultural use)
  - LLM: General styling/usage knowledge if not in product data

### 5. Benefits & Value
- **Purpose:** Why choose this product, quality, durability, heritage value, investment perspective
- **Content:** Value proposition, quality points, heritage significance, investment angle
- **Data Source:**
  - Primary: `supplier_description` (quality, craftsmanship), `description` (benefits)
  - Secondary: Heritage data (heritage value), price context
  - LLM: General value propositions if not explicit in data

### 6. Alternative Products
- **Purpose:** Alternative options at different price points, different versions, same need items
- **Content:** Similar products, price alternatives, when to choose each
- **Data Source:**
  - Primary: `find_alternative_products()` method results
  - Includes: Same category, similar products (vector search), price alternatives, same producer
  - LLM: Comparison narrative, when to choose each

### 7. Conclusion / Call to Action
- **Purpose:** Summary, link to product page, related products
- **Content:** Brief summary, product link, related items
- **Data Source:**
  - Primary: Product name, `url` (product page link)
  - Secondary: Related products, category links
  - LLM: Summary narrative

---

## Available CLAN Data

### Core Product Data (from `clan_products` table)
- ✅ **name** - Product title
- ✅ **short_description** - Brief description (blurb)
- ✅ **description** - Full HTML description (includes bullet points)
- ✅ **price** - Product price
- ✅ **image_url** - Main product image
- ✅ **url** - Product page URL on CLAN.com
- ✅ **sku** - Product SKU

### Producer/Supplier Data
- ✅ **supplier_name** - Manufacturer name (e.g., "Lochcarron")
- ✅ **supplier_description** - HTML supplier information (craftsmanship, heritage, location)
- ⚠️ **producer_id** - Link to producers table (may not exist for all products)

### Product Specifications
- ✅ **configurable_options** - JSONB: Sizes, colors, tartans, materials, etc.
- ✅ **specifications** - Product specifications (dict or string)
- ✅ **additional_data** - JSONB: Material, pattern, shirt style, clan crest info, etc.
- ✅ **dimensions** - Product dimensions (text)

### Category & Heritage Data
- ✅ **category_ids** - Array of category IDs
- ✅ **categories** - Full category data (name, description, level, parent_id)
- ✅ **heritage_data** - JSONB with 5 dimensions:
  - `historical_origins` (narrative, key_themes, significant_elements)
  - `cultural_significance` (narrative, key_themes, significant_elements)
  - `evolution` (narrative, key_themes, significant_elements)
  - `scottish_heritage_connections` (narrative, key_themes, significant_elements)
  - `industrial_legacy` (narrative, key_themes, significant_elements)

### Images
- ✅ **image_url** - Main product image
- ✅ **all_images** - Complete image gallery (via API: `/api/clan/products/<sku>/full?all_images=true`)

### Alternative Products
- ✅ **find_alternative_products()** - Method in `ClanDataExtractor` that finds:
  - Same category products
  - Vector search similar products
  - Price-based alternatives
  - Same producer products
  - Cross-category alternatives

---

## Content Generation Strategy by Section

### Section 1: Introduction & Historical Context
**Data Available:** ✅ Mostly complete (from category heritage_data)
- **Primary:** `heritage_data.historical_origins.narrative` (full narrative with themes/elements)
- **Secondary:** `heritage_data.cultural_significance.narrative`, `heritage_data.scottish_heritage_connections.narrative`
- **Context:** Category description, product description
- **LLM Needed:**
  - Synthesize heritage narratives into cohesive introduction
  - Connect product to historical/cultural context
  - Add product-specific historical details if not in category heritage

### Section 2: Craftsmanship & Materials
**Data Available:** ✅ Complete
- **Primary:** `supplier_description` (HTML supplier information about craftsmanship, methods)
- **Secondary:** `specifications`, `additional_data` (materials), `supplier_name`, `producer_data` (if available)
- **LLM Needed:**
  - Clean HTML to narrative
  - Synthesize supplier_description with specifications
  - Add process details if missing from supplier_description
  - Format materials from additional_data/specifications

### Section 3: Features & Specifications
**Data Available:** ✅ Complete
- **Primary:** `description` (full HTML, includes product details, bullet points)
- **Secondary:** `configurable_options` (sizes, colors, tartans, etc.), `specifications`, `additional_data`, `dimensions`
- **LLM Needed:**
  - Clean HTML to narrative
  - Format structured data (options, specs) into readable text
  - Extract care instructions if in description
  - Organize into clear feature list

### Section 4: How to Use / Practical Guide
**Data Available:** ⚠️ Partial (may not be in product data)
- **Primary:** `description` (if includes usage/styling information)
- **Secondary:** Category context, heritage_data (cultural use patterns)
- **LLM Needed:**
  - Extract usage info from description if present
  - Generate styling tips if not in product data
  - Add occasion recommendations based on product type
  - Suggest pairings based on category

### Section 5: Benefits & Value
**Data Available:** ⚠️ Partial
- **Primary:** `supplier_description` (quality, craftsmanship mentions), `description` (benefits)
- **Secondary:** Heritage data (heritage value), price context
- **LLM Needed:**
  - Extract value propositions from supplier_description
  - Synthesize quality/durability points
  - Add heritage value narrative from heritage_data
  - Add investment perspective if appropriate

### Section 6: Alternative Products
**Data Available:** ✅ Complete (from `find_alternative_products()` method)
- **Primary:** Results from `ClanDataExtractor.find_alternative_products()`:
  - Same category products
  - Vector search similar products
  - Price-based alternatives (cheaper/more luxury)
  - Same producer products
  - Cross-category alternatives
- **LLM Needed:**
  - Generate comparison narrative
  - Explain when to choose each alternative
  - Highlight key differences

### Section 7: Conclusion / Call to Action
**Data Available:** ✅ Complete
- **Primary:** Product name, `url` (product page link)
- **Secondary:** Related products (from alternatives), category links
- **LLM Needed:**
  - Generate brief summary
  - Create call-to-action narrative
  - Link to product page naturally

---

## Current Planning Stages Analysis

### Current Pipeline for `generated` Posts

From `config/post_type_pipeline_configs.py`:

```
1. taxonomy                    # Assign taxonomy
2. product-data-review        # Review CLAN product data
3. topic-brainstorming        # Generate topics from CLAN data + standard sections
4. section-structure-design   # Design structure (template-based)
5. section-ideas              # Section-specific ideas
6. section-titling            # Finalize section titles
7. drafting                  # Author drafts
```

### Assessment of Each Stage

#### 1. `taxonomy` ✅ **KEEP**
- **Purpose:** Assign categories, tags, metadata
- **Value:** Essential for organization
- **Time:** Quick (product already has category_ids)
- **Verdict:** Keep, but can be auto-populated from product data

#### 2. `product-data-review` ✅ **KEEP & ENHANCE**
- **Purpose:** Review and validate CLAN product data
- **Current:** Shows product data, marks completeness
- **Value:** Essential - ensures data quality before generation
- **Enhancement:** Could auto-validate and flag missing data
- **Verdict:** Keep as critical validation step

#### 3. `topic-brainstorming` ❌ **QUESTIONABLE**
- **Purpose:** Generate 50+ topic ideas for curation
- **Current:** LLM generates topics from expanded idea
- **Problem:** For products, topics are largely predetermined by:
  - Product sections (already defined: 8 sections)
  - Product data (already available)
  - Category heritage (already researched)
- **Value:** Low - we know what to write about (the product)
- **Alternative:** Skip or simplify to "section content planning"
- **Verdict:** **SIMPLIFY OR REMOVE** - Overkill for structured product data

#### 4. `section-structure-design` ❌ **REDUNDANT**
- **Purpose:** Design structure (template-based)
- **Current:** LLM organizes topics into sections
- **Problem:** 
  - Product profiles have **fixed 8-section structure** (already defined)
  - No need to "design" - structure is predetermined
  - Sections map directly to available data
- **Value:** None - structure is already known
- **Verdict:** **REMOVE** - Structure is fixed, no design needed

#### 5. `section-ideas` ⚠️ **SIMPLIFY**
- **Purpose:** Generate section-specific ideas
- **Current:** LLM generates ideas for each section
- **Problem:** 
  - For products, "ideas" = what data to use and how to present it
  - Data sources are already known (see mapping above)
  - Ideas are mostly: "Use X data for Y section"
- **Value:** Medium - could help with content strategy, but data mapping is straightforward
- **Alternative:** Replace with "section content mapping" - show which data goes where
- **Verdict:** **SIMPLIFY** - Change to data mapping rather than idea generation

#### 6. `section-titling` ✅ **KEEP**
- **Purpose:** Finalize section titles
- **Current:** LLM generates section titles
- **Value:** Medium - can create engaging titles, but section types have default titles
- **Verdict:** Keep, but can be quick (default titles + optional refinement)

#### 7. `drafting` ✅ **KEEP**
- **Purpose:** Author drafts content
- **Value:** Essential - this is where content is actually written
- **Verdict:** Keep

---

## Recommended Simplified Pipeline

### Option A: Minimal (2-3 stages)
```
1. taxonomy                    # Auto-populate from product data, allow refinement
2. product-data-review        # Review/validate data, map to sections
3. drafting                   # Generate content directly using data mapping
```

**Rationale:**
- Structure is fixed (8 sections)
- Data sources are known (mapping above)
- No need for brainstorming or structure design
- Go straight to content generation with data mapping

### Option B: Moderate (4 stages) - **RECOMMENDED**
```
1. taxonomy                    # Auto-populate, allow refinement
2. product-data-review        # Review data, show completeness
3. section-content-mapping    # NEW: Show which data maps to which section (visual mapping)
4. section-titling            # Quick title refinement (optional)
5. drafting                   # Generate content with data mapping
```

**Rationale:**
- Keeps validation step (important)
- Adds visual data mapping (helps author understand what will be generated)
- Allows title refinement (quick, optional)
- Streamlined but not too minimal

### Option C: Enhanced (5 stages)
```
1. taxonomy
2. product-data-review
3. section-content-mapping    # Visual data mapping
4. section-content-strategy   # LLM suggests content approach per section (optional)
5. section-titling
6. drafting
```

**Rationale:**
- Adds optional content strategy (how to present data)
- Still streamlined compared to current 6 stages
- Allows for creative input where needed

---

## Data-to-Section Mapping (For Section-Content-Mapping Stage)

### Visual Mapping Interface

Show author which data will be used for each section:

```
Section: hero
├── Data Sources:
│   ├── name → Headline ✓
│   ├── short_description → Standfirst ✓
│   └── image_url → Hero Image ✓
└── LLM Role: Minimal (refine standfirst if needed)

Section: the_object
├── Data Sources:
│   ├── description → Main content ✓
│   ├── category.description → Context ✓
│   └── heritage_data.historical_origins → Historical context ✓
└── LLM Role: Clean HTML, expand if <50 words, add distinctiveness

Section: the_maker
├── Data Sources:
│   ├── supplier_description → Main content ✓
│   ├── supplier_name → Producer name ✓
│   └── producer_data → Additional info (if available) ⚠️
└── LLM Role: Clean HTML, expand if <50 words

Section: in_context
├── Data Sources:
│   ├── heritage_data.cultural_significance → Main content ✓
│   ├── heritage_data.historical_origins → Historical context ✓
│   └── heritage_data.scottish_heritage_connections → Scottish links ✓
└── LLM Role: Synthesize heritage data, add seasonal/cultural context

Section: materials_making
├── Data Sources:
│   ├── specifications → Technical details ✓
│   ├── additional_data → Material/pattern info ✓
│   ├── dimensions → Size information ✓
│   └── supplier_description → Process info (if present) ✓
└── LLM Role: Format structured data, add process details if missing

Section: gallery
├── Data Sources:
│   └── all_images (API) → Gallery images ✓
└── LLM Role: Generate captions

Section: explore_further
├── Data Sources:
│   ├── url → Product link ✓
│   ├── category URLs → Category links ✓
│   └── producer.website → Producer link (if available) ⚠️
└── LLM Role: None (data assembly)

Section: credits
├── Data Sources:
│   ├── CLAN data sources → Product data credits ✓
│   └── Heritage research sources → Category research credits ✓
└── LLM Role: None (data assembly)
```

---

## Content Generation Approach

### CLAN-First Policy (Already Established)

1. **Tier 1: CLAN Product Data** (Highest Priority)
   - Use directly, never override
   - Product name, description, supplier info, specifications

2. **Tier 2: CLAN Category Heritage Data**
   - Use directly, supplement only if missing
   - Historical origins, cultural significance, evolution

3. **Tier 3: LLM General Knowledge** (Lowest Priority)
   - Only when CLAN data is unavailable or < 50 words
   - Mark with [GENERAL KNOWLEDGE] tags

### Generation Strategy Per Section

#### High Data Coverage Sections (Minimal LLM)
- **Craftsmanship & Materials:** 85% data, 15% LLM (HTML cleaning, synthesis, formatting)
- **Features & Specifications:** 90% data, 10% LLM (HTML cleaning, formatting structured data)
- **Alternative Products:** 80% data, 20% LLM (comparison narrative, when to choose)

#### Medium Data Coverage Sections (Moderate LLM)
- **Introduction & Historical Context:** 70% data, 30% LLM (synthesis of heritage narratives, product connection)
- **Benefits & Value:** 65% data, 35% LLM (extract value props, synthesize quality points)

#### Lower Data Coverage Sections (More LLM)
- **How to Use / Practical Guide:** 40% data, 60% LLM (styling tips, occasion recommendations, pairings)
- **Conclusion / Call to Action:** 50% data, 50% LLM (summary narrative, CTA writing)

---

## Drafting Stage Strategy

### Current Drafting Process
- LLM generates content section by section
- Uses prompts with CLAN data prioritized
- Author reviews and edits

### Recommended Approach for Products

**Option 1: Section-by-Section Generation**
- Generate one section at a time
- Show data sources for each section
- Author can review/edit before next section
- **Pros:** Granular control, see data usage
- **Cons:** More steps, slower

**Option 2: Bulk Generation with Review**
- Generate all sections at once
- Show complete draft with data source indicators
- Author reviews and edits all sections
- **Pros:** Faster, see full picture
- **Cons:** Less granular control

**Recommendation:** **Option 2 (Bulk Generation)** for products because:
- Data mapping is clear
- Sections are independent
- Faster workflow
- Author can still edit section-by-section after generation

---

## Simplification Benefits

### Time Savings
- **Current:** 6 planning stages + drafting = 7 steps
- **Simplified:** 3-4 planning stages + drafting = 4-5 steps
- **Savings:** 2-3 steps eliminated (30-40% reduction)

**Note:** This analysis is for `generated` post type (7-section structure), not `profile` post type (8-section structure).

### Reduced Complexity
- **Current:** Brainstorming topics when topics are predetermined
- **Simplified:** Direct data mapping to sections
- **Benefit:** Clearer workflow, less confusion

### Better Data Utilization
- **Current:** LLM "discovers" what to write about
- **Simplified:** LLM "presents" available data effectively
- **Benefit:** More accurate, data-driven content

### Maintained Quality
- **Current:** Multiple LLM calls for structure/ideas
- **Simplified:** Focused LLM calls for content generation
- **Benefit:** Same quality, more efficient

---

## Implementation Recommendations

### Phase 1: Simplify Pipeline (Immediate)
1. Remove `section-structure-design` (redundant - structure is fixed)
2. Replace `topic-brainstorming` with `section-content-mapping`
3. Simplify `section-ideas` or remove (data mapping covers this)

### Phase 2: Enhance Data Mapping (Short-term)
1. Create visual data-to-section mapping interface
2. Show data completeness per section
3. Allow author to override data sources if needed

### Phase 3: Optimize Drafting (Short-term)
1. Implement bulk section generation
2. Show data source indicators in generated content
3. Allow section-by-section regeneration if needed

---

## Questions for Decision

1. **Pipeline Simplification:** Accept Option B (4 stages) or prefer Option A (3 stages)?
2. **Topic Brainstorming:** Remove entirely or replace with data mapping?
3. **Section Structure:** Confirm fixed 8-section structure (no design needed)?
4. **Drafting Approach:** Bulk generation or section-by-section?
5. **Data Mapping UI:** Visual mapping interface or simple list?

---

## Conclusion

The current 6-stage planning process is **over-engineered for product profiles** where:
- ✅ Structure is fixed (8 sections)
- ✅ Data is readily available (CLAN database)
- ✅ Data-to-section mapping is straightforward
- ✅ Heritage context is already researched (category heritage_data)

**Recommended Simplification:**
- Remove redundant stages (structure design, topic brainstorming)
- Replace with data mapping stage (visual, clear)
- Streamline to 3-4 essential stages
- Focus LLM effort on content generation, not structure discovery

This will result in:
- ⚡ Faster workflow (30-40% fewer steps)
- 🎯 Better data utilization (clear mapping)
- ✨ Same quality output (focused LLM usage)
- 👤 Better author experience (clearer process)

---

**End of Review**

