# LLM-Based Product Categorization Proposal
**Date:** 2025-11-12  
**Status:** Proposal  
**Goal:** Replace pattern-matching categorization with LLM-based semantic analysis

---

## Problem with Current Approach

### Pattern Matching Limitations
1. **Brittle**: Requires maintaining extensive keyword lists
2. **Misses Edge Cases**: "Teddy bear charm" vs "Teddy bear" - pattern matching struggles
3. **No Context Understanding**: Can't distinguish "embroidery" (kit) from "embroidery" (decoration on clothing)
4. **Hard to Maintain**: New products require updating keyword lists
5. **False Positives**: "Cat charm" matches "cat" but is jewellery, not pet product
6. **Inconsistent**: Different patterns for similar products

### Example Issues We've Encountered
- **Teddy bear charms**: Pattern matching moved them to recreation, but they're jewellery
- **Embroidery kits**: Had to manually distinguish from embroidery decorations
- **Bags**: Scattered across 7 categories - pattern matching missed many
- **Pets**: Had to filter false positives (cat/dog in names but not pet-related)

---

## Proposed LLM-Based Approach

### Core Concept
Use **semantic understanding** via LLM to categorize products based on:
1. **Product name and description**
2. **Context from similar products** (via vector search)
3. **Category definitions** (what each category means)
4. **Disambiguation** (understanding when "charm" means jewellery vs decoration)

### Advantages
1. **Semantic Understanding**: LLM understands meaning, not just keywords
2. **Context Awareness**: Can distinguish "teddy bear charm" (jewellery) from "teddy bear" (toy)
3. **Handles Edge Cases**: Better at ambiguous products
4. **Self-Improving**: Can learn from examples
5. **Maintainable**: Less hardcoded logic, more flexible
6. **Consistent**: Same reasoning applied to all products

---

## Implementation Strategy

### Option 1: Pure LLM Classification (Recommended)

**Process:**
1. For each product, send to LLM with:
   - Product name
   - Product description (first 200 chars)
   - Current category (if any)
   - List of valid categories with definitions
   - Examples of products in each category

2. LLM returns:
   - Recommended `product_form`
   - Recommended `core_type`
   - Confidence score (0.0-1.0)
   - Reasoning (for review)

3. Batch process with confidence threshold:
   - High confidence (>0.8): Auto-apply
   - Medium confidence (0.6-0.8): Review queue
   - Low confidence (<0.6): Manual review

**Example Prompt:**
```
Categorize this product into one of these categories:

Categories:
- clothing: Items worn on the body (garments, accessories worn with clothing)
- jewellery: Items worn as jewellery (rings, necklaces, brooches, charms)
- bags: Items for carrying/storing (backpacks, purses, totes, wallets)
- homeware: Items for home use (flasks, quaichs, coasters, decorative items)
- pets: Items for pets (dog bandanas, pet bowls, treat bags)
- recreation: Leisure activities (toys, jigsaws, embroidery kits, games)
- artwork: Items that hang on walls (paintings, prints, plaques, maps)
- stationery: Writing supplies (notebooks, pencil cases)
- haberdashery: Sewing supplies (buttons, ribbons, thread)
- voucher: Gift vouchers

Product: "Teddy Bear Charm - C114"
Description: "A charming silver teddy bear charm for charm bracelets"
Current category: recreation

Examples:
- "Angus the Highland Bear" (teddy bear toy) → recreation
- "Silver Celtic Knot Charm" (jewellery item) → jewellery
- "Teddy Bear Charm - C119" (charm for bracelet) → jewellery

Which category does this product belong to? Explain your reasoning.
```

### Option 2: Hybrid Approach (LLM + Vector Search)

**Process:**
1. Use vector search to find 5-10 most similar products
2. Check their categories
3. If all similar products are in same category with high similarity → use that
4. If ambiguous → use LLM to disambiguate
5. LLM considers:
   - Product name/description
   - Similar products and their categories
   - Category definitions

**Advantages:**
- Faster (vector search is quick)
- More consistent (learns from existing data)
- LLM only for edge cases

### Option 3: LLM with Category Embeddings

**Process:**
1. Generate embeddings for each category definition
2. Generate embedding for product name + description
3. Find closest category embedding
4. Use LLM to verify and handle edge cases

---

## Recommended Approach: Option 1 (Pure LLM)

### Why Pure LLM?
1. **Most Reliable**: LLM understands context and nuance
2. **Handles All Cases**: No need for separate logic for different product types
3. **Explainable**: LLM can provide reasoning
4. **Flexible**: Easy to adjust category definitions
5. **Future-Proof**: Can handle new product types without code changes

### Implementation Details

#### 1. Category Definitions
Create clear definitions for each category:
```python
CATEGORY_DEFINITIONS = {
    'clothing': 'Items worn on the body. Includes garments (kilts, shirts, jackets) and accessories worn with clothing (ties, belts, sporrans, kilt pins, scarves).',
    'jewellery': 'Items worn as jewellery. Includes rings, necklaces, bracelets, brooches, charms, pendants. Note: Charms are jewellery, not toys.',
    'bags': 'Items for carrying or storing. Includes backpacks, purses, wallets, totes, shopping bags, pencil cases.',
    'homeware': 'Items for home use. Includes flasks, quaichs, glasses, mugs, coasters, letter openers, decorative items.',
    'pets': 'Items specifically for pets. Includes dog bandanas, pet bowls, treat bags, collars, leads.',
    'recreation': 'Leisure activities and games. Includes toys (teddy bears), jigsaws, embroidery kits, cross stitch kits, board games.',
    'artwork': 'Items that hang on walls. Includes paintings, prints, plaques, maps, pictures, posters.',
    'stationery': 'Writing and office supplies. Includes notebooks, pencil cases, journals.',
    'haberdashery': 'Sewing and craft supplies. Includes buttons, ribbons, thread, needles.',
    'voucher': 'Gift vouchers and certificates.'
}
```

#### 2. LLM Prompt Template
```python
def categorize_product(product_name, description, current_category=None):
    prompt = f"""
Categorize this product into one of these categories:

{CATEGORY_DEFINITIONS_TEXT}

Product: "{product_name}"
Description: {description[:200]}
Current category: {current_category or 'None'}

Examples of correctly categorized products:
- "Angus the Highland Bear" (teddy bear toy) → recreation
- "Silver Celtic Knot Charm" (jewellery item) → jewellery  
- "Teddy Bear Charm - C119" (charm for bracelet) → jewellery
- "Handmade Tartan Dog Bandana" (for pets) → pets
- "Clan Crest Wall Plaque" (wall decoration) → artwork

Return JSON:
{{
    "product_form": "category_name",
    "core_type": "specific_type",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation"
}}
"""
    return llm_call(prompt)
```

#### 3. Batch Processing with Confidence Thresholds
```python
def categorize_all_products():
    products = get_all_products()
    
    high_confidence = []  # Auto-apply
    review_queue = []      # Manual review
    
    for product in products:
        result = categorize_product(product)
        
        if result['confidence'] > 0.8:
            high_confidence.append((product, result))
        elif result['confidence'] > 0.6:
            review_queue.append((product, result))
        else:
            # Manual review required
            pass
    
    # Auto-apply high confidence
    for product, result in high_confidence:
        update_product_category(product, result)
    
    # Generate review queue report
    generate_review_report(review_queue)
```

---

## Comparison: Pattern Matching vs LLM

| Aspect | Pattern Matching | LLM-Based |
|--------|-----------------|-----------|
| **Accuracy** | ~70-80% (many edge cases) | ~90-95% (understands context) |
| **Edge Cases** | Poor (requires manual fixes) | Good (handles ambiguity) |
| **Maintenance** | High (update keyword lists) | Low (adjust definitions) |
| **Speed** | Fast | Slower (but acceptable for batch) |
| **Cost** | Free | Free (Ollama local) |
| **Explainability** | None | High (LLM provides reasoning) |
| **Consistency** | Variable | High (same reasoning) |

---

## Implementation Plan

### Phase 1: Proof of Concept
1. Create LLM categorization function
2. Test on 50 products with known correct categories
3. Compare results with pattern matching
4. Measure accuracy and identify issues

### Phase 2: Batch Processing
1. Process all products with LLM
2. Generate confidence scores
3. Auto-apply high-confidence (>0.8) changes
4. Create review queue for medium/low confidence

### Phase 3: Review and Refine
1. Review medium-confidence products
2. Adjust category definitions based on errors
3. Re-process with improved definitions
4. Iterate until acceptable accuracy

### Phase 4: Ongoing Maintenance
1. Use LLM for new products
2. Periodic review of low-confidence products
3. Update category definitions as needed

---

## Example: How LLM Would Handle Edge Cases

### Case 1: "Teddy Bear Charm"
**Pattern Matching**: Matches "teddy" + "bear" → recreation ❌  
**LLM**: Understands "charm" means jewellery item, "teddy bear" is just the design → jewellery ✅

### Case 2: "Embroidery Kit"
**Pattern Matching**: Matches "embroidery" → could go to clothing or homeware ❌  
**LLM**: Understands "kit" means activity/supplies → recreation ✅

### Case 3: "Tartan Bandana"
**Pattern Matching**: Matches "bandana" → could be clothing or pets ❌  
**LLM**: No "dog" or "pet" context → clothing ✅  
**LLM**: With "dog" context → pets ✅

### Case 4: "Framed Tartan Handbag"
**Pattern Matching**: Matches "framed" → artwork ❌  
**LLM**: Understands "handbag" is functional item with pockets → bags ✅

---

## Cost and Performance

### Ollama (Local)
- **Cost**: Free (runs locally)
- **Speed**: ~1-2 seconds per product
- **Batch of 1,157 products**: ~20-40 minutes
- **Acceptable for**: Batch processing, periodic reviews

### Optimization
- **Batch prompts**: Process multiple products in one LLM call (5-10 at a time)
- **Caching**: Cache results for products that haven't changed
- **Incremental**: Only process new/changed products

---

## Recommendation

**Use LLM-based categorization** because:

1. **More Reliable**: Handles edge cases and context better
2. **Maintainable**: Less hardcoded logic
3. **Scalable**: Easy to add new categories or adjust definitions
4. **Explainable**: LLM reasoning helps with review
5. **Free**: Ollama runs locally
6. **Future-Proof**: Can handle new product types

**Implementation:**
- Start with Option 1 (Pure LLM)
- Use confidence thresholds for batch processing
- Create review queue for manual verification
- Iterate on category definitions based on results

---

## Next Steps

1. **Create LLM categorization function** using Ollama
2. **Test on sample products** (50-100 products)
3. **Compare with current pattern matching** results
4. **Refine category definitions** based on test results
5. **Batch process all products** with confidence thresholds
6. **Review and iterate** until acceptable accuracy

---

**Last Updated:** 2025-11-12

