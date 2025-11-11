# Product Type Parsing System - Design Document

**Date:** 2025-11-11  
**Status:** Design Phase  
**Purpose:** Design systematic parsing of product titles into structured identifiers/tags

---

## Goal

Parse all product titles into a structured set of identifiers that can be:
1. Used for product-type-specific heritage research
2. Used for filtering and search
3. Used for content generation context
4. Extended iteratively as we discover more patterns

---

## Data Structure Design

### Proposed JSONB Structure

```json
{
  "core_type": "kilt",
  "subtype": "casual",
  "level": "classic",
  "materials": ["wool", "leather"],
  "patterns": ["tartan"],
  "decorations": ["clan_crest"],
  "occasions": ["casual"],
  "styles": ["box_pleat"],
  "attributes": ["mini", "adjustable"],
  "disambiguation": {
    "is_accessory": false,
    "is_artwork": false,
    "is_jewelry": false,
    "is_clothing": true,
    "product_form": "garment"
  },
  "type_hierarchy": ["garment", "kilt", "casual_kilt"],
  "type_keywords": ["kilt", "casual", "wool", "tartan"],
  "parsed_at": "2025-11-11T10:30:00",
  "parsing_method": "hybrid",
  "confidence": 0.95,
  "needs_review": false,
  "review_threshold": 0.7
}
```

### Field Definitions

#### Required Fields
- **`core_type`** (string): Primary product type
  - Examples: "kilt", "shirt", "sporran", "ring", "scarf", "tie", "waistcoat", "jacket"
  - Must be a recognized core type from master list

#### Optional Fields
- **`subtype`** (string): Specific variant within core type
  - Examples: "jacobite", "argyll", "dress", "daywear", "wedding", "mini"
  - Can be null if product is standard type

- **`level`** (string): Quality/price level (already parsed)
  - Values: "classic", "luxury", "essential"
  - Default: "classic"

- **`materials`** (array): Material identifiers
  - Examples: ["wool", "cashmere", "tweed", "leather", "silk"]
  - Empty array if not specified

- **`patterns`** (array): Pattern identifiers
  - Examples: ["tartan", "plaid", "check", "plain"]
  - Empty array if not specified

- **`decorations`** (array): Decorative elements
  - Examples: ["clan_crest", "celtic", "thistle", "stag", "studded"]
  - Empty array if not specified

- **`occasions`** (array): Occasion/use identifiers
  - Examples: ["wedding", "formal", "casual", "daywear", "evening"]
  - Empty array if not specified

- **`styles`** (array): Style identifiers
  - Examples: ["box_pleat", "knife_pleat", "prince_charlie", "argyll"]
  - Empty array if not specified

- **`attributes`** (array): Other descriptive attributes
  - Examples: ["mini", "adjustable", "made_to_measure", "custom"]
  - Empty array if not specified

#### Disambiguation Fields
- **`disambiguation`** (object): Flags to distinguish product forms
  - `is_accessory`: true if accessory (kilt pin, tie slide, etc.)
  - `is_artwork`: true if artwork/decoration (painting, print, etc.)
  - `is_jewelry`: true if jewelry (ring, earrings, etc.)
  - `is_clothing`: true if clothing/garment
  - `product_form`: Primary form category ("garment", "accessory", "jewelry", "artwork", "homeware", "other")

#### Metadata Fields
- **`type_hierarchy`** (array): Hierarchical type path
  - Example: ["garment", "kilt", "casual_kilt"]
  - Used for inheritance and grouping

- **`type_keywords`** (array): All relevant keywords extracted
  - Used for search and matching

- **`parsed_at`** (timestamp): When parsing occurred

- **`parsing_method`** (string): Method used ("strict", "llm", "hybrid")

- **`confidence`** (float): Confidence score 0.0-1.0
  - **Critical**: Stored in database for filtering and re-processing
  - Used to flag products for review (confidence < threshold)
  - Allows iterative refinement by re-processing low-confidence products

- **`needs_review`** (boolean): Flag for manual review
  - Automatically set to true if confidence < review_threshold (default: 0.7)
  - Can be manually set/unset via UI (future)

- **`review_threshold`** (float): Confidence threshold used (stored for reference)
  - Default: 0.7
  - Can be adjusted per run

---

## Parsing Strategy: Hybrid Approach

### Phase 1: Strict Pattern Matching

**Purpose:** Handle common, unambiguous patterns quickly and reliably

**Patterns to Match:**

1. **Accessory Indicators** (suffixes/prefixes):
   - `* Pin` → accessory, core_type from context
   - `* Keyring` → accessory
   - `* Key Fob` → accessory
   - `* Slide` → accessory
   - `* Brooch` → jewelry/accessory
   - `* Charm` → jewelry/accessory

2. **Artwork Indicators**:
   - `* Painting` → artwork
   - `* Print` → artwork
   - `* Artwork` → artwork
   - `* Poster` → artwork

3. **Jewelry Indicators**:
   - `* Ring` (not "keyring") → jewelry
   - `* Earrings` → jewelry
   - `* Bracelet` → jewelry
   - `* Necklace` → jewelry

4. **Level Indicators** (already parsed):
   - `Luxury *` → level: luxury
   - `Essential *` → level: essential
   - Default → level: classic

5. **Common Subtypes** (dictionary-based):
   - "Jacobite" → subtype: jacobite
   - "Argyll" → subtype: argyll
   - "Prince Charlie" → subtype: prince_charlie
   - "Dress" → subtype: dress
   - "Casual" → subtype: casual
   - "Daywear" → subtype: daywear
   - "Wedding" → subtype: wedding
   - "Mini" → attribute: mini

6. **Material Indicators**:
   - "Tweed" → material: tweed
   - "Cashmere" → material: cashmere
   - "Wool" → material: wool
   - "Leather" → material: leather
   - "Tartan" → pattern: tartan (if not material)

7. **Core Type Extraction** (category-aware):
   - If category contains "Shirts" → core_type: "shirt"
   - If category contains "Kilts" → core_type: "kilt"
   - If category contains "Sporrans" → core_type: "sporran"
   - If category contains "Rings" → core_type: "ring"
   - etc.

**Strict Matching Rules:**
```python
STRICT_PATTERNS = {
    'accessory_suffixes': ['pin', 'keyring', 'key fob', 'slide', 'brooch', 'charm'],
    'artwork_suffixes': ['painting', 'print', 'artwork', 'poster'],
    'jewelry_types': ['ring', 'earrings', 'bracelet', 'necklace'],
    'subtypes': ['jacobite', 'argyll', 'prince charlie', 'dress', 'casual', 'daywear', 'wedding'],
    'materials': ['tweed', 'cashmere', 'wool', 'leather', 'silk', 'cotton'],
    'patterns': ['tartan', 'plaid', 'check'],
    'decorations': ['clan crest', 'celtic', 'thistle', 'stag', 'studded'],
    'occasions': ['wedding', 'formal', 'casual', 'daywear', 'evening'],
    'styles': ['box pleat', 'knife pleat', 'prince charlie', 'argyll'],
    'attributes': ['mini', 'adjustable', 'made to measure', 'custom']
}
```

### Phase 2: Category Context Analysis

**Purpose:** Use category hierarchy to inform parsing

**Process:**
1. Get category path (e.g., "Menswear > Shirts > Casual Shirts")
2. Extract category keywords
3. Use category to determine likely core_type
4. Use category to filter out impossible types

**Example:**
- Product: "Antique Lion Rampant Kilt Pin"
- Categories: ["Jewellery", "Kilt Accessories", "Kilt Pins"]
- Category context: "kilt_accessories" → is_accessory: true
- Core type: "kilt_pin" (not "kilt")
- Disambiguation: is_accessory: true, product_form: "accessory"

### Phase 3: LLM Disambiguation & Refinement

**Purpose:** Handle ambiguous cases and complex titles

**When to Use LLM:**
1. Strict matching confidence < 0.8
2. Ambiguous title (e.g., "Kilt" could be garment or painting)
3. Complex title with multiple potential interpretations
4. Title doesn't match any strict patterns

**LLM Prompt Structure:**
```
Parse this product title into structured identifiers:

Product: {name}
Categories: {category_names}
Description: {description (first 200 chars)}

Context: We need to distinguish between:
- A kilt (garment) vs kilt pin (accessory) vs painting of a kilt (artwork)
- A ring (jewelry) vs keyring (accessory)
- A shirt (garment) vs shirt pin (accessory)

Extract:
1. core_type: Primary product type (e.g., "kilt", "shirt", "sporran", "ring")
2. subtype: Specific variant (e.g., "jacobite", "dress", "wedding") or null
3. materials: Array of materials mentioned
4. patterns: Array of patterns mentioned
5. decorations: Array of decorative elements
6. occasions: Array of occasions/uses
7. styles: Array of style identifiers
8. attributes: Array of other attributes
9. disambiguation: {
   is_accessory: boolean,
   is_artwork: boolean,
   is_jewelry: boolean,
   is_clothing: boolean,
   product_form: "garment" | "accessory" | "jewelry" | "artwork" | "homeware" | "other"
}
10. confidence: 0.0-1.0

Return JSON only.
```

**LLM Response Format:**
```json
{
  "core_type": "kilt_pin",
  "subtype": null,
  "materials": [],
  "patterns": [],
  "decorations": ["lion_rampant"],
  "occasions": [],
  "styles": [],
  "attributes": ["antique"],
  "disambiguation": {
    "is_accessory": true,
    "is_artwork": false,
    "is_jewelry": false,
    "is_clothing": false,
    "product_form": "accessory"
  },
  "confidence": 0.98
}
```

### Phase 4: Validation & Normalization

**Purpose:** Ensure consistency and fix common errors

**Validation Rules:**
1. **Core Type Validation**: Must be from master list
2. **Mutual Exclusivity**: 
   - If is_accessory=true, is_clothing should be false
   - If is_artwork=true, is_clothing should be false
3. **Category Consistency**: 
   - If category is "Kilt Pins", core_type should not be "kilt"
   - If category is "Shirts", core_type should be "shirt" or related
4. **Subtype Validation**: Subtype must be valid for core_type
5. **Material/Pattern Logic**: 
   - "Tartan" is usually a pattern, not material (unless "Tartan Fabric")
   - "Tweed" is a material, not pattern

**Normalization:**
- Lowercase all identifiers
- Standardize spelling (e.g., "jacobite" not "jacobean" for consistency)
- Remove duplicates
- Sort arrays alphabetically

---

## Disambiguation Examples

### Example 1: Kilt vs Kilt Pin vs Kilt Painting

**Product: "Antique Lion Rampant Kilt Pin"**
- Strict match: "* Pin" → accessory indicator
- Category: "Kilt Accessories" → confirms accessory
- Result: 
  - core_type: "kilt_pin"
  - is_accessory: true
  - is_clothing: false

**Product: "Casual Kilt"**
- Strict match: No accessory/artwork indicators
- Category: "Kilts" → confirms garment
- Result:
  - core_type: "kilt"
  - subtype: "casual"
  - is_clothing: true
  - is_accessory: false

**Product: "Highland Kilt Painting"**
- Strict match: "* Painting" → artwork indicator
- Category: "Artwork" or "Homeware" → confirms artwork
- Result:
  - core_type: "artwork"
  - is_artwork: true
  - is_clothing: false
  - subject: "kilt" (stored separately)

### Example 2: Ring vs Keyring

**Product: "Clan Crest Reverse Seal Ring"**
- Strict match: "* Ring" (not "* Keyring") → jewelry
- Category: "Jewellery > Rings" → confirms jewelry
- Result:
  - core_type: "ring"
  - is_jewelry: true
  - decorations: ["clan_crest"]

**Product: "Stag Antler Whistle Keyring"**
- Strict match: "* Keyring" → accessory
- Category: "Accessories" → confirms accessory
- Result:
  - core_type: "keyring"
  - is_accessory: true
  - is_jewelry: false

### Example 3: Shirt vs Shirt Accessory

**Product: "Black Jacobite Shirt"**
- Strict match: No accessory indicators
- Category: "Shirts" → confirms garment
- Result:
  - core_type: "shirt"
  - subtype: "jacobite"
  - is_clothing: true

**Product: "Shirt Pin"** (if exists)
- Strict match: "* Pin" → accessory
- Category: "Accessories" → confirms accessory
- Result:
  - core_type: "shirt_pin"
  - is_accessory: true
  - is_clothing: false

---

## Master Core Type List

**Garments:**
- kilt, shirt, jacket, waistcoat, sporran, tie, bow_tie, cummerbund, scarf, tam, hat, brogues, shoes, boots, trews, skirt, dress, trousers

**Accessories:**
- kilt_pin, tie_slide, keyring, key_fob, flask, bag, belt, buckle, comb

**Jewelry:**
- ring, earrings, bracelet, necklace, brooch, charm, cufflinks

**Artwork/Homeware:**
- painting, print, artwork, poster, plaque, cushion, blanket, rug

**Other:**
- bear, toy, gift_set, outfit (combination)

**Note:** This list will expand as we process the catalog.

---

## Implementation Script Design

### Script Structure

```python
class ProductTypeParser:
    def __init__(self):
        self.strict_patterns = load_strict_patterns()
        self.core_types = load_core_types()
        self.category_context = load_category_context()
    
    def parse_product(self, product_name, category_ids, description=None):
        """
        Main parsing method - hybrid approach
        
        Returns:
        {
            "core_type": "...",
            "subtype": "...",
            "level": "...",
            "materials": [...],
            "patterns": [...],
            "decorations": [...],
            "occasions": [...],
            "styles": [...],
            "attributes": [...],
            "disambiguation": {...},
            "type_hierarchy": [...],
            "type_keywords": [...],
            "parsing_method": "strict|llm|hybrid",
            "confidence": 0.0-1.0
        }
        """
        # Phase 1: Strict matching
        strict_result = self.strict_parse(product_name, category_ids)
        
        # Phase 2: Category context
        category_result = self.apply_category_context(strict_result, category_ids)
        
        # Phase 3: LLM if needed
        if category_result['confidence'] < 0.8:
            llm_result = self.llm_parse(product_name, category_ids, description)
            # Merge results
            final_result = self.merge_results(category_result, llm_result)
        else:
            final_result = category_result
        
        # Phase 4: Validation
        final_result = self.validate_and_normalize(final_result, category_ids)
        
        return final_result
    
    def strict_parse(self, name, category_ids):
        """Phase 1: Pattern matching"""
        # Check for accessory/artwork indicators
        # Extract level (already done)
        # Extract materials, patterns, etc.
        # Determine core_type from category
        pass
    
    def apply_category_context(self, result, category_ids):
        """Phase 2: Use category to refine"""
        # Get category names
        # Check category hierarchy
        # Refine core_type and disambiguation
        pass
    
    def llm_parse(self, name, category_ids, description):
        """Phase 3: LLM disambiguation"""
        # Build prompt with context
        # Call LLM
        # Parse JSON response
        pass
    
    def validate_and_normalize(self, result, category_ids):
        """Phase 4: Validation"""
        # Check core_type against master list
        # Validate disambiguation flags
        # Normalize values
        pass
```

### Batch Processing with Confidence-Based Filtering

```python
def process_all_products(review_threshold=0.7, reprocess_low_confidence=False):
    """
    Process entire catalog in batches with confidence tracking.
    
    Args:
        review_threshold: Confidence below which products are flagged for review
        reprocess_low_confidence: If True, only process products with confidence < threshold
    """
    batch_size = 100
    
    with db_manager.get_cursor() as cursor:
        if reprocess_low_confidence:
            # Only process products with low confidence or no parsing yet
            cursor.execute("""
                SELECT COUNT(*) FROM clan_products
                WHERE product_type_data->>'confidence' IS NULL
                   OR (product_type_data->>'confidence')::float < %s
            """, (review_threshold,))
        else:
            cursor.execute("SELECT COUNT(*) FROM clan_products")
        total = cursor.fetchone()['count']
    
    parser = ProductTypeParser()
    stats = {
        'total': 0,
        'processed': 0,
        'high_confidence': 0,
        'low_confidence': 0,
        'errors': 0
    }
    
    for offset in range(0, total, batch_size):
        if reprocess_low_confidence:
            products = fetch_products_batch_low_confidence(offset, batch_size, review_threshold)
        else:
            products = fetch_products_batch(offset, batch_size)
        
        for product in products:
            stats['total'] += 1
            try:
                parsed = parser.parse_product(
                    product['name'],
                    product['category_ids'],
                    product.get('description', '')[:200]
                )
                
                # Set needs_review flag based on confidence
                parsed['needs_review'] = parsed['confidence'] < review_threshold
                parsed['review_threshold'] = review_threshold
                
                # Save parsed data (overwrites existing if reprocessing)
                save_parsed_data(product['id'], parsed)
                
                stats['processed'] += 1
                if parsed['confidence'] >= review_threshold:
                    stats['high_confidence'] += 1
                else:
                    stats['low_confidence'] += 1
                
            except Exception as e:
                logger.error(f"Error parsing product {product['id']}: {e}")
                stats['errors'] += 1
                # Save with error flag for manual review
                save_parsed_data_error(product['id'], str(e))
    
    logger.info(f"Processing complete: {stats}")
    return stats

def fetch_products_batch_low_confidence(offset, limit, threshold):
    """Fetch products with low confidence or no parsing"""
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT id, name, category_ids, description
            FROM clan_products
            WHERE product_type_data->>'confidence' IS NULL
               OR (product_type_data->>'confidence')::float < %s
            ORDER BY id
            LIMIT %s OFFSET %s
        """, (threshold, limit, offset))
        return cursor.fetchall()

def get_review_queue(threshold=0.7):
    """Get products flagged for review"""
    with db_manager.get_cursor() as cursor:
        cursor.execute("""
            SELECT id, name, product_type_data
            FROM clan_products
            WHERE product_type_data->>'needs_review' = 'true'
               OR (product_type_data->>'confidence')::float < %s
            ORDER BY (product_type_data->>'confidence')::float ASC
        """, (threshold,))
        return cursor.fetchall()
```

---

## Confidence Scoring

**Strict Matching Confidence:**
- All patterns matched: 0.95
- Most patterns matched: 0.85
- Some patterns matched: 0.70
- Few patterns matched: 0.50

**Category Consistency:**
- Category strongly supports type: +0.1
- Category conflicts with type: -0.2

**LLM Confidence:**
- Use LLM-provided confidence score
- If LLM confidence < 0.7, flag for review

**Final Confidence:**
- Weighted average of strict + category + LLM
- **Stored in database** for filtering and re-processing
- If final < threshold (default 0.7), `needs_review: true` flag set
- Allows querying and re-processing without manual intervention

---

## Edge Cases & Handling

### Case 1: Ambiguous Titles
- "Kilt" (could be garment or painting subject)
- **Solution:** Category context + description check
- If category is "Artwork" → artwork
- If category is "Kilts" → garment
- If still ambiguous → LLM with full context

### Case 2: Multiple Types
- "Wedding Ring" → core_type: "ring", occasions: ["wedding"]
- "Dress Sporran" → core_type: "sporran", subtype: "dress"
- **Solution:** Store primary type, use attributes/occasions for secondary

### Case 3: Compound Products
- "Argyll Kilt Outfit" → outfit (combination)
- **Solution:** Parse as "outfit" type, store components in attributes

### Case 4: Unrecognized Types
- New product type not in master list
- **Solution:** LLM suggests type, flag for review, add to master list

### Case 5: Category Mismatch
- Product in wrong category
- **Solution:** Use LLM to override category if title clearly indicates different type

---

## Processing Workflow

### Initial Run (Fast Processing)
```bash
python scripts/parse_product_types.py --threshold 0.7
```
- Processes all products quickly
- Stores confidence scores in database
- Flags products with confidence < 0.7 for review
- Continues without stopping

### Review Low-Confidence Products
```bash
python scripts/parse_product_types.py --review-queue --threshold 0.7
```
- Lists all products with confidence < 0.7
- Shows parsing results for manual review
- Allows manual corrections

### Re-process Low-Confidence (Iterative Refinement)
```bash
python scripts/parse_product_types.py --reprocess-low --threshold 0.7
```
- Only processes products with confidence < 0.7 (or no parsing)
- Overwrites existing low-confidence results
- Allows iterative improvement without re-processing high-confidence products

### Adjust Threshold and Re-run
```bash
python scripts/parse_product_types.py --reprocess-low --threshold 0.8
```
- Raises the bar, re-processes products below new threshold
- Useful for incremental quality improvement

### Statistics and Reporting
```bash
python scripts/parse_product_types.py --stats
```
- Shows distribution of confidence scores
- Counts by core_type, parsing_method
- Lists products needing review

## Database Queries for Review

**Get all low-confidence products:**
```sql
SELECT id, name, product_type_data->>'core_type' as core_type,
       product_type_data->>'confidence' as confidence,
       product_type_data->>'parsing_method' as method
FROM clan_products
WHERE (product_type_data->>'confidence')::float < 0.7
ORDER BY (product_type_data->>'confidence')::float ASC;
```

**Get products by core_type:**
```sql
SELECT product_type_data->>'core_type' as core_type, COUNT(*) as count
FROM clan_products
WHERE product_type_data->>'core_type' IS NOT NULL
GROUP BY product_type_data->>'core_type'
ORDER BY count DESC;
```

**Get parsing method distribution:**
```sql
SELECT product_type_data->>'parsing_method' as method, COUNT(*) as count,
       AVG((product_type_data->>'confidence')::float) as avg_confidence
FROM clan_products
WHERE product_type_data->>'parsing_method' IS NOT NULL
GROUP BY product_type_data->>'parsing_method';
```

## Next Steps

1. **Create master core type list** - Based on catalog analysis
2. **Build strict pattern matcher** - Dictionary-based matching
3. **Create category context mapper** - Map categories to likely types
4. **Build LLM parser** - For ambiguous cases
5. **Create validation rules** - Ensure consistency
6. **Test on sample** - 50-100 products, review results
7. **Refine patterns** - Add more patterns based on test results
8. **Full catalog processing** - Process all 1,157 products (fast, stores confidence)
9. **Review low-confidence** - Query database for products needing review
10. **Iterative refinement** - Re-process low-confidence products with improved patterns/LLM prompts

---

## Questions to Resolve

1. **Core Type Granularity**: 
   - "kilt_pin" vs "pin" (kilt-specific)?
   - Recommendation: Be specific ("kilt_pin") for better heritage research

2. **Subtype vs Attribute**:
   - "Mini Kilt" → subtype: "mini" or attribute: "mini"?
   - Recommendation: Subtype if it changes the product form, attribute if it's just a modifier

3. **Outfit Handling**:
   - "Argyll Kilt Outfit" → How to store components?
   - Recommendation: core_type: "outfit", store components in attributes array

4. **LLM Usage**:
   - Use LLM for all products or only ambiguous?
   - Recommendation: Strict first, LLM only if confidence < 0.8

5. **Manual Override**:
   - Should there be a UI for manual correction?
   - Recommendation: Yes, but defer to Phase 2

---

**End of Design Document**

