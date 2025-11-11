# Product Type Classification & Heritage Data - Proposal

**Date:** 2025-11-11  
**Status:** Proposal - Review Required  
**Purpose:** Add product-type-specific heritage data layer distinct from category-level heritage

---

## Problem Statement

Currently, we have:
- **Category-level heritage data**: Historical/cultural context for broad categories (e.g., "Shirts" category)
- **Missing**: Product-type-specific heritage data (e.g., "Jacobite Shirt" as a specific type within "Shirts")

**Example Gap:**
- Product: "Black Jacobite Shirt"
- Category: "Menswear > Shirts" (has heritage data about shirts in general)
- Missing: Heritage data specific to "Jacobite shirts" - their unique history, styling, cultural significance distinct from shirts in general

**Use Case:**
When writing about a Jacobite shirt, we need:
1. Category context: General history of shirts in Scotland
2. **Product type context**: Specific history of Jacobite/Jacobean shirts, their distinctive features, when they're worn, their cultural associations

---

## Catalog Analysis

### Sample Product Patterns

**Shirts:**
- "Black Jacobite Shirt"
- "Cream Calico Jacobite Shirt"
- "Essential Jacobite Shirt"
- Pattern: `[Level?] [Material?] [Type] Shirt`

**Sporrans:**
- "Dress Sporran with Stag and Hounds Cantle"
- "Semi Dress Sporran with Studs"
- "Daywear Sporran, Celtic Tooled and Studded Flap"
- "Essential Black Dress Sporran"
- Pattern: `[Level?] [Type] Sporran [Details]`

**Kilts:**
- "Argyll Welsh Kilt Outfit"
- "Casual Kilt"
- "Box Pleat Mini Kilt, tartan"
- Pattern: `[Type] Kilt [Material/Variant]`

**Rings:**
- "Clan Crest Reverse Seal Ring"
- "Twin Teardrop Moonstone and Sapphire Ring"
- Pattern: `[Design/Feature] [Type] Ring`

**Jackets:**
- "Made to Measure Argyll Jacket"
- "Classic Argyll Jacket"
- "Tweed Chieftain Waistcoat"
- Pattern: `[Type] [Material?] Jacket/Waistcoat`

### Type Classification Patterns Observed

1. **Style-based types**: Jacobite, Argyll, Prince Charlie, Ghillie, Chieftain
2. **Occasion-based types**: Dress, Semi Dress, Daywear, Wedding, Casual
3. **Material-based types**: Tweed, Cashmere, Tartan, Leather
4. **Feature-based types**: Box Pleat, Plain Top, Studded
5. **Design-based types**: Clan Crest, Celtic, Thistle

### Multi-Type Products

Some products clearly have multiple type classifications:
- "Essential Black Dress Sporran" → `[Essential level] [Black color] [Dress type] Sporran`
- "Luxury Rabbit Dress Sporran" → `[Luxury level] [Rabbit material] [Dress type] Sporran`
- "Made to Measure Argyll Jacket" → `[Custom] [Argyll style] Jacket`

---

## Proposed Solution

### 1. Database Schema

**Add to `clan_products` table:**

```sql
ALTER TABLE clan_products
ADD COLUMN IF NOT EXISTS product_type_data JSONB DEFAULT '{}';

CREATE INDEX IF NOT EXISTS idx_clan_products_product_type_data 
ON clan_products USING GIN (product_type_data);
```

**Structure:**
```json
{
  "primary_type": "Jacobite Shirt",
  "type_hierarchy": ["Shirt", "Jacobite Shirt"],
  "subtypes": ["Jacobite", "Shirt"],
  "type_keywords": ["jacobite", "jacobean", "ghillie"],
  "heritage_data": {
    "historical_origins": {
      "narrative": "...",
      "key_themes": [...],
      "significant_elements": [...]
    },
    "cultural_significance": {...},
    "evolution": {...},
    "scottish_heritage_connections": {...},
    "styling_traditions": {
      "narrative": "When and how Jacobite shirts are worn...",
      "key_themes": [...],
      "significant_elements": [...]
    }
  },
  "classified_at": "2025-11-11T10:30:00",
  "classification_confidence": 0.95
}
```

**Key Differences from Category Heritage:**
- Adds `styling_traditions` dimension (specific to product types)
- Includes `type_hierarchy` for multi-level classification
- Includes `type_keywords` for search/matching
- `classification_confidence` for LLM uncertainty

### 2. Type Classification Approach

#### Option A: LLM-Based Classification (Recommended)

**Process:**
1. **Batch Analysis**: Process products in batches (100-200 at a time)
2. **Context-Aware**: Use product name, description, category, supplier info
3. **Hierarchical Classification**: Identify primary type and subtypes
4. **Confidence Scoring**: LLM provides confidence level
5. **Manual Review Flag**: Flag low-confidence for human review

**LLM Prompt Structure:**
```
Analyze this product and classify its type:

Product: {name}
Category: {category_name}
Description: {description}
Supplier: {supplier_name}

Identify:
1. Primary product type (e.g., "Jacobite Shirt", "Dress Sporran")
2. Type hierarchy (e.g., ["Shirt", "Jacobite Shirt"])
3. Subtypes/keywords (e.g., ["Jacobite", "Jacobean", "Ghillie"])
4. Confidence level (0.0-1.0)

If product has multiple distinct types, list all (e.g., "Wedding Ring" → ["Ring", "Wedding Jewelry"])
```

**Advantages:**
- Handles complex naming patterns
- Can identify multiple types
- Understands context (category + description)
- Can handle edge cases

**Disadvantages:**
- Requires LLM API calls (cost)
- May need iteration/tuning
- Slower for large catalogs

#### Option B: Rule-Based + LLM Hybrid

**Process:**
1. **Pattern Matching**: Extract common patterns (e.g., "X Shirt", "Dress X", "X Kilt")
2. **Keyword Dictionary**: Pre-defined type keywords (Jacobite, Argyll, etc.)
3. **LLM Refinement**: Use LLM only for ambiguous cases
4. **Validation**: LLM validates rule-based classifications

**Advantages:**
- Faster for bulk processing
- Lower cost
- More predictable

**Disadvantages:**
- May miss nuanced types
- Requires maintaining keyword dictionary
- Less flexible

**Recommendation:** Start with Option A (LLM-based) for accuracy, then optimize with Option B for common patterns.

### 3. Heritage Data Generation

**Similar to Category Heritage Research:**

1. **Query Generation**: Generate Wikipedia/search queries for product type
   - Example: "Jacobite shirt Scotland history" or "Jacobean shirt Scottish heritage"
2. **Web Research**: Use Wikipedia API (and future Google Search) to find type-specific information
3. **Synthesis**: LLM synthesizes research into heritage narratives
4. **Dimensions**: Same 5 dimensions as category heritage + `styling_traditions`

**Key Focus Areas:**
- **Historical Origins**: When/where this specific type emerged
- **Cultural Significance**: Unique role of this type (vs. general category)
- **Styling Traditions**: When/how this type is worn, styling rules
- **Evolution**: How this type has changed
- **Scottish Heritage Connections**: Specific associations (clans, events, regions)

### 4. Multi-Type Products

**Handling Strategy:**

**Option 1: Primary Type + Secondary Types**
```json
{
  "primary_type": "Dress Sporran",
  "secondary_types": ["Sporran", "Highlandwear Accessory"],
  "type_hierarchy": ["Sporran", "Dress Sporran"],
  "heritage_data": {
    // Primary type heritage
  },
  "secondary_heritage_data": {
    // Additional context from secondary types
  }
}
```

**Option 2: Multiple Type Records**
- Store array of type classifications
- Each with its own heritage data
- Merge when displaying

**Recommendation:** Option 1 (Primary + Secondary) - simpler, clearer hierarchy

---

## Implementation Plan

### Phase 1: Schema & Infrastructure
1. Add `product_type_data` column to `clan_products`
2. Create classification utility module
3. Create heritage research module (similar to category heritage)
4. Update `ClanDataExtractor` to include product type data

### Phase 2: Classification Script
1. Create batch classification script
2. Process products in batches (100-200 at a time)
3. Store classifications with confidence scores
4. Flag low-confidence for review

### Phase 3: Heritage Research
1. Create `ProductTypeHeritageResearcher` (similar to `CategoryHeritageResearcher`)
2. Generate heritage data for each unique product type
3. Store in `product_type_data.heritage_data`
4. Reuse existing Wikipedia research infrastructure

### Phase 4: UI Integration
1. Display product type heritage in product-data-review page
2. Show alongside category heritage (distinct sections)
3. Update section-content-mapping to include product type data
4. Add regeneration button for product type heritage

### Phase 5: Ongoing Maintenance
1. Auto-classify new products on import
2. Periodic re-classification for updated products
3. Manual override interface for corrections

---

## Data Structure Examples

### Example 1: Jacobite Shirt
```json
{
  "primary_type": "Jacobite Shirt",
  "type_hierarchy": ["Shirt", "Jacobite Shirt"],
  "subtypes": ["Jacobite", "Jacobean", "Ghillie"],
  "type_keywords": ["jacobite", "jacobean", "ghillie", "shirt"],
  "heritage_data": {
    "historical_origins": {
      "narrative": "The Jacobite shirt, also known as Jacobean or Ghillie shirt, emerged in 17th-18th century Scotland...",
      "key_themes": ["Jacobite uprisings", "Highland dress", "Practical Highlandwear"],
      "significant_elements": ["Lace-up front", "No collar", "Traditional fabric"]
    },
    "styling_traditions": {
      "narrative": "Jacobite shirts are traditionally worn with kilts for both formal and casual occasions...",
      "key_themes": ["Kilt outfits", "Highland dress", "Versatile styling"],
      "significant_elements": ["Lace-up styling", "No tie required", "Traditional appearance"]
    }
  }
}
```

### Example 2: Dress Sporran
```json
{
  "primary_type": "Dress Sporran",
  "type_hierarchy": ["Sporran", "Dress Sporran"],
  "subtypes": ["Dress", "Formal", "Sporran"],
  "type_keywords": ["dress", "formal", "sporran", "evening"],
  "heritage_data": {
    "historical_origins": {
      "narrative": "Dress sporrans evolved from practical pouches to formal accessories...",
      "key_themes": ["Formal Highlandwear", "Evening dress", "Traditional accessories"],
      "significant_elements": ["Cantle design", "Leather construction", "Formal occasions"]
    },
    "styling_traditions": {
      "narrative": "Dress sporrans are reserved for formal occasions, typically worn with full Highland dress...",
      "key_themes": ["Formal events", "Weddings", "Evening wear"],
      "significant_elements": ["Evening occasions", "Full Highland dress", "Traditional formality"]
    }
  }
}
```

---

## Questions to Resolve

1. **Field Name**: `product_type_data` or `product_type_classification` or `product_type_heritage`?
2. **Multiple Types**: How to handle products with multiple distinct types? (e.g., "Wedding Ring" = both "Ring" and "Wedding Jewelry")
3. **Type Granularity**: How specific should types be? (e.g., "Jacobite Shirt" vs. "Shirt - Jacobite")
4. **Heritage Scope**: Should product type heritage include all 5 dimensions or focus on type-specific aspects?
5. **Classification Frequency**: One-time bulk classification or ongoing classification for new products?
6. **Manual Override**: Should there be a UI for manual type assignment/correction?

---

## Estimated Scope

**Classification:**
- Products to classify: ~1,157
- Estimated LLM calls: ~1,200 (allowing for retries/refinements)
- Estimated time: 2-3 hours (with batching)
- Estimated cost: $5-10 (depending on LLM provider)

**Heritage Research:**
- Unique product types: ~200-300 (estimated)
- Heritage research per type: Similar to category heritage (5 dimensions)
- Estimated time: 10-15 hours (can be done incrementally)
- Estimated cost: $20-30 (Wikipedia API free, LLM synthesis)

**Total Estimated Effort:** 15-20 hours + LLM costs

---

## Recommendation

**Proceed with:**
1. ✅ Add `product_type_data` JSONB column
2. ✅ LLM-based classification (Option A) with confidence scoring
3. ✅ Primary type + secondary types approach for multi-type products
4. ✅ Heritage research similar to category heritage (5 dimensions + styling_traditions)
5. ✅ Batch processing script for initial classification
6. ✅ Auto-classification for new products

**Defer:**
- Manual override UI (can add later if needed)
- Rule-based optimization (can add after seeing LLM results)

---

## Next Steps

1. **Review this proposal** - Confirm approach and resolve questions
2. **Create migration** - Add `product_type_data` column
3. **Build classification script** - LLM-based batch processor
4. **Test on sample** - Classify 50-100 products, review results
5. **Refine approach** - Adjust based on test results
6. **Full classification** - Process entire catalog
7. **Heritage research** - Generate heritage data for unique types
8. **UI integration** - Display in product-data-review and section-content-mapping

---

**End of Proposal**

