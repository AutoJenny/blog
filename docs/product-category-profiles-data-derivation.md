# Product & Category Profiles: Data Derivation Strategy

## Overview

This document outlines how we derive data from the `clan_products` and `clan_categories` databases to inform the writing of Product and Category Profiles. This is a collaborative planning document to conceptualize the data extraction and enrichment process.

## Current Data Availability

### From `clan_products` Table

#### Basic Product Information
- `id` - Product ID from clan.com
- `sku` - Unique product identifier
- `name` - Product title/name
- `price` - Product price
- `image_url` - Main product image
- `url` - Product page URL on clan.com
- `short_description` - Brief product description
- `description` - Full product description (HTML)
- `category_ids` - JSONB array of category IDs

#### Producer/Supplier Information
- `supplier_name` - Manufacturer/supplier name (e.g., "Lochcarron", "William Lockie")
- `supplier_description` - HTML supplier information (craftsmanship, heritage, location)

#### Product Variants & Options
- `configurable_options` - JSONB array of product options
  - Structure: `[{"option": "Size", "options": [{"label": "S"}, {"label": "M"}]}, {"option": "Colour", "options": [{"label": "Navy"}, {"label": "Red"}]}]`
  - Can include: Sizes, Colors, Tartans, Materials, etc.

#### Timestamps
- `clan_created_at` - When product was created on clan.com
- `clan_updated_at` - When product was last updated
- `first_seen_at` - When we first discovered the product
- `last_updated` - When our record was last modified

#### Additional (via API enrichment)
- `all_images` - Complete image gallery (fetched on-demand via `/api/clan/products/<sku>/full?all_images=true`)

### From `clan_categories` Table

#### Category Information
- `id` - Category ID
- `name` - Category name (e.g., "Scarves", "Wool Scarves")
- `description` - Category description
- `level` - Hierarchy level (0 = root)
- `parent_id` - Parent category ID (for hierarchy)

## Data Derivation for Product Profiles

### 1. Product Selection & Context

**Answer:** We select products directly from the `clan_products` table. We maintain a curated list of products eligible for profiling, with a UI to select and order them for the calendar.

**Approach:**
- Products are selected from the `clan_products` table (parent products)
- Categories can be selected at any branch or leaf level in the `clan_categories` hierarchy
- A curated list will be maintained with UI support for:
  - Selecting products/categories for profiling
  - Ordering them for calendar scheduling
  - Filtering by producer, category, material, etc.

**Data Available:**
```sql
-- All products with producer information
SELECT id, name, sku, supplier_name, category_ids
FROM clan_products
WHERE supplier_name IS NOT NULL
ORDER BY supplier_name, name;

-- Categories at any level
SELECT id, name, level, parent_id, description
FROM clan_categories
ORDER BY level, parent_id, name;
```

### 2. Producer Information Extraction

**Answer:** Yes, we should normalize into a `producers` table. We can enhance this with web searching for additional data (location, founding year, heritage details).

**Approach:**
1. **Create `producers` table** to normalize supplier information
2. **Extract from `supplier_description`** - Parse HTML to extract structured data
3. **Web search enhancement** - Use web search to find additional producer information:
   - Location
   - Founding year
   - Heritage details
   - Craftsmanship methods
   - Historical significance

**Implementation:**
```sql
-- Create producers table
CREATE TABLE producers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    location VARCHAR(255),
    founding_year INTEGER,
    heritage_details TEXT,
    craftsmanship_methods TEXT,
    website_url VARCHAR(500),
    web_researched_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Link products to producers
ALTER TABLE clan_products 
ADD COLUMN producer_id INTEGER REFERENCES producers(id);

-- Extract from existing supplier_name
INSERT INTO producers (name, description)
SELECT DISTINCT supplier_name, supplier_description
FROM clan_products
WHERE supplier_name IS NOT NULL
ON CONFLICT (name) DO NOTHING;
```

**Web Search Strategy:**
- Search for `{supplier_name} Scotland` or `{supplier_name} Scottish`
- Extract structured data: location, founding year, heritage
- Store in `producers` table with `web_researched_at` timestamp

### 3. Product Selection (Clarified)

**Answer:** We select products directly from the `clan_products` table. Each product is a parent product, not a variant. We maintain a curated list with UI support for selection and calendar ordering.

**Approach:**
- Products are selected individually from `clan_products`
- No need to group by "product concept" - each product is treated as a distinct profile candidate
- UI will allow browsing and selecting products for profiling
- Selected products can be ordered for calendar scheduling

### 4. Material, Dimensions & Specifications

**Answer:** This data is published on the clan.com website (e.g., [Clan Crest Wall Plaque](https://clan.com/clan-crest-wall-plaque) shows Dimensions: 7" x 8" or 10" x 12", Material: Wood, Emblem: Clan crest). We need to scrape this from product pages.

**Current Status:**
- API does not return dimensions/material data
- This information is available on product pages in structured format (tables)

**Web Scraping Approach:**
```python
def scrape_product_specifications(product_url):
    """Scrape dimensions, materials, and other specifications from product page"""
    import requests
    from bs4 import BeautifulSoup
    
    response = requests.get(product_url)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Extract specifications table
    # Example structure from clan.com:
    # <table>
    #   <tr><td>Dimensions</td><td>7" x 8" or 10" x 12"</td></tr>
    #   <tr><td>Material</td><td>Wood</td></tr>
    #   <tr><td>Emblem</td><td>Clan crest</td></tr>
    # </table>
    
    specs = {}
    spec_table = soup.find('table')  # Adjust selector based on actual HTML
    if spec_table:
        for row in spec_table.find_all('tr'):
            cells = row.find_all('td')
            if len(cells) == 2:
                key = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                specs[key.lower()] = value
    
    return specs
```

**Database Schema:**
```sql
-- Add specifications column to clan_products
ALTER TABLE clan_products
ADD COLUMN specifications JSONB;

-- Example structure:
-- {
--   "dimensions": "7\" x 8\" or 10\" x 12\"",
--   "material": "Wood",
--   "emblem": "Clan crest",
--   "weight": "...",
--   "care_instructions": "..."
-- }
```

**Implementation:**
1. Create scraper function to extract specifications from product URLs
2. Add `specifications` JSONB column to `clan_products` table
3. Run scraping job for products selected for profiling
4. Cache results to avoid re-scraping

### 5. Cultural & Seasonal Context

**Question:** How do we derive cultural significance and seasonal relevance?

**Available Data:**
- `category_ids` - May indicate cultural categories
- Product names/descriptions - May contain cultural references
- Tartan options - Link to clan/heritage

**Potential Approaches:**
- **Tartan Analysis**: Extract tartan names from `configurable_options`, link to clan heritage
- **Category Analysis**: Use category hierarchy to infer cultural context
- **LLM Analysis**: Use AI to extract cultural significance from descriptions

**Considerations:**
- Should we create a `tartans` reference table with clan associations?
- Should we tag products with cultural significance flags?
- How do we identify seasonal relevance (gifting, events, etc.)?

## Data Derivation for Category Profiles

### 1. Category Selection

**Question:** Which categories are suitable for Category Profiles?

**Available Data:**
- `clan_categories` table with hierarchy
- Product counts per category
- Category descriptions

**Potential Criteria:**
```sql
-- Categories with sufficient product depth
SELECT c.id, c.name, c.description, COUNT(p.id) as product_count
FROM clan_categories c
LEFT JOIN clan_products p ON c.id = ANY(p.category_ids)
GROUP BY c.id, c.name, c.description
HAVING COUNT(p.id) >= 5  -- Minimum products for "representative examples"
ORDER BY product_count DESC;
```

**Considerations:**
- Which categories have rich historical/cultural significance?
- Which categories have multiple producers (diversity for examples)?
- Which categories have sufficient product depth (4-8 examples)?

### 2. Representative Product Selection

**Answer:** Prioritize price diversity first, then producer diversity, material variety, and other factors.

**Selection Logic:**
```python
def select_representative_products(category_id, limit=8):
    # Get all products in category
    products = get_products_by_category(category_id)
    
    # 1. PRIORITY 1: Price diversity
    # Sort products by price and select across price range
    products_by_price = sorted(products, key=lambda p: float(p.price) if p.price else 0)
    
    # Divide into price tiers
    price_tiers = 3  # Low, Medium, High
    tier_size = len(products_by_price) // price_tiers
    
    representatives = []
    seen_producers = set()
    
    # Select from each price tier
    for tier in range(price_tiers):
        tier_products = products_by_price[tier * tier_size:(tier + 1) * tier_size]
        
        # Within tier, prioritize producer diversity
        for product in tier_products:
            if len(representatives) >= limit:
                break
            if product.supplier_name and product.supplier_name not in seen_producers:
                representatives.append(product)
                seen_producers.add(product.supplier_name)
    
    # 2. Fill remaining slots with diverse materials/variants
    remaining = [p for p in products if p not in representatives]
    representatives.extend(remaining[:limit - len(representatives)])
    
    return representatives
```

### 3. Historical & Cultural Context

**Answer:** Use LLM analysis of aggregated product data, combined with broader web research to support this. We can also draw inferences from the level in the branch/leaf hierarchy (e.g., from the context of higher-level categories).

**Approach:**
```python
def derive_category_context(category_id):
    category = get_category(category_id)
    products = get_products_by_category(category_id)
    
    # 1. Get category hierarchy context
    category_path = get_category_path(category_id)  # e.g., ["Homeware", "Plaques", "Clan Crest Plaques"]
    hierarchy_context = " > ".join(category_path)
    
    # 2. Aggregate product data
    product_descriptions = [p.description for p in products if p.description]
    product_names = [p.name for p in products]
    producer_names = [p.supplier_name for p in products if p.supplier_name]
    
    # 3. LLM analysis with context
    llm_prompt = f"""
    Analyze this product category for historical and cultural significance:
    
    Category: {category.name}
    Hierarchy: {hierarchy_context}
    Products: {', '.join(product_names[:10])}
    Producers: {', '.join(set(producer_names))}
    Descriptions: {product_descriptions[0] if product_descriptions else 'N/A'}
    
    Provide:
    1. Historical origins
    2. Cultural significance
    3. Evolution over time
    4. Scottish heritage connections
    """
    
    llm_analysis = llm_analyze(llm_prompt)
    
    # 4. Web research to validate and enhance
    web_research = web_search(f"{category.name} Scotland history heritage")
    
    # 5. Combine LLM analysis + web research + hierarchy context
    return {
        'historical_origins': llm_analysis['origins'] + web_research['origins'],
        'cultural_significance': llm_analysis['significance'] + web_research['significance'],
        'hierarchy_context': hierarchy_context,
        'llm_analysis': llm_analysis,
        'web_research': web_research,
        'validated_at': datetime.now()
    }
```

**Database Schema:**
```sql
-- Add heritage/research data to categories
ALTER TABLE clan_categories
ADD COLUMN heritage_data JSONB,
ADD COLUMN web_researched_at TIMESTAMP,
ADD COLUMN llm_analyzed_at TIMESTAMP;

-- Example structure:
-- {
--   "historical_origins": "...",
--   "cultural_significance": "...",
--   "hierarchy_context": "Homeware > Plaques > Clan Crest Plaques",
--   "llm_analysis": {...},
--   "web_research": {...}
-- }
```

### 4. Material & Method Traditions

**Question:** How do we extract material and method information for category-level discussion?

**Available Data:**
- Products in category (materials, descriptions)
- Category name (may contain material hints)

**Potential Aggregation:**
```python
def extract_category_materials_and_methods(category_id):
    products = get_products_by_category(category_id)
    
    # Aggregate materials across products
    all_materials = set()
    all_methods = set()
    
    for product in products:
        materials = extract_materials(product)
        methods = extract_methods(product)
        all_materials.update(materials)
        all_methods.update(methods)
    
    return {
        'materials': sorted(list(all_materials)),
        'methods': sorted(list(all_methods)),
        'diversity': len(all_materials)  # Indicates material variety
    }
```

**Questions:**
- Should we create material/method taxonomies?
- How do we handle regional variations in methods?
- Should we track evolution of methods over time?

## Data Enrichment Opportunities

### 1. LLM-Based Extraction

**Use Cases:**
- Extract structured data from unstructured descriptions
- Generate historical context from product/category data
- Identify cultural significance
- Extract material and process information

**Example:**
```python
def enrich_product_for_profile(product_id):
    product = get_product(product_id)
    
    # LLM prompt for structured extraction
    prompt = f"""
    Extract structured information from this product description:
    {product.description}
    
    Return JSON with:
    - materials: [list of materials]
    - processes: [list of production processes]
    - cultural_significance: [cultural context]
    - seasonal_relevance: [seasonal use cases]
    """
    
    extracted = llm_extract(prompt)
    return extracted
```

### 2. Producer Normalization

**Potential Enhancement:**
- Create `producers` table to normalize supplier information
- Extract structured data: location, founding year, specialties
- Link products to normalized producer records
- Enable producer index pages

### 3. Product Family Grouping

**Potential Enhancement:**
- Create `product_families` table to group related products
- Group by: producer + base type + material
- Enable "product concept" identification
- Support multiple tartans/variants per family

### 4. Tartan/Design Reference

**Potential Enhancement:**
- Extract tartan names from `configurable_options`
- Create `tartans` reference table with clan associations
- Link products to tartan designs
- Enable tartan-focused content

## Summary: Clarified Data Derivation Approach

### Product Profiles

1. **Product Selection:** ✅ **RESOLVED**
   - Select products directly from `clan_products` table (parent products)
   - Maintain curated list with UI for selection and calendar ordering
   - Categories can be selected at any branch/leaf level

2. **Producer Information:** ✅ **RESOLVED**
   - Create `producers` table to normalize supplier data
   - Extract from `supplier_description` HTML
   - Enhance with web search for location, founding year, heritage details

3. **Material & Specifications:** ✅ **RESOLVED**
   - Scrape dimensions, materials from product pages (e.g., [Clan Crest Wall Plaque](https://clan.com/clan-crest-wall-plaque))
   - Add `specifications` JSONB column to `clan_products`
   - Cache scraped data to avoid re-scraping

### Category Profiles

1. **Representative Examples:** ✅ **RESOLVED**
   - Prioritize **price diversity first**
   - Then producer diversity, material variety
   - Select 4-8 products across price tiers

2. **Historical & Cultural Context:** ✅ **RESOLVED**
   - Use LLM analysis of aggregated product data
   - Supplement with web research
   - Use category hierarchy context (higher-level categories provide context)

### Implementation Requirements

#### Database Schema Changes
1. **`producers` table** - Normalize supplier information
2. **`clan_products.specifications`** - JSONB for dimensions, materials, etc.
3. **`clan_products.producer_id`** - Link to producers table
4. **`clan_categories.heritage_data`** - JSONB for historical/cultural context

#### Web Scraping
1. **Product specifications scraper** - Extract dimensions, materials from product pages
2. **Producer information scraper** - Web search for producer details

#### UI Components
1. **Product/Category selection UI** - Browse and select products/categories for profiling
2. **Calendar ordering UI** - Order selected profiles for weekly scheduling
3. **Profiles row in calendar week view** - Display scheduled profiles

#### Data Enrichment
1. **Producer web research** - Automated search for producer information
2. **LLM analysis** - Historical/cultural context generation
3. **Web research** - Validation and enhancement of LLM analysis

## Next Steps

1. **Review Data Availability:**
   - Query actual `clan_products` data to see what's available
   - Identify gaps in data for profile writing
   - Determine which fields need enrichment

2. **Prototype Data Extraction:**
   - Build sample queries for product/producer selection
   - Test material extraction from descriptions
   - Experiment with LLM-based extraction

3. **Design Data Structures:**
   - Determine if we need new tables (producers, product_families, tartans)
   - Design schema for profile metadata
   - Plan data enrichment workflow

4. **Calendar Integration:**
   - Design "Profiles" row in week view
   - Determine scheduling mechanism
   - Plan profile selection workflow

