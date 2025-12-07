# Product Selection Criteria for Calendar Scheduling

**Date:** 2025-12-07  
**Purpose:** Guide for selecting products to populate the "Product" column in calendar scheduling

---

## Available Data Summary

- **Total Products:** 1,157 (all have detailed data)
- **Products with long descriptions (>1000 chars):** 227
- **Products with very long descriptions (>2000 chars):** 4
- **Average description length:** 666 characters
- **Featured products (blog/newsletter):** 52 (proxy for popularity)
- **Products with producer info:** 47
- **Product levels:** Classic (1,052), Luxury (56), Essential (49)
- **Categories:** 259 total categories available

---

## Recommended Selection Criteria

### 1. **Description Length** ✅ (You mentioned this)
- **Rationale:** Longer descriptions provide more content for article generation
- **Threshold:** Products with `description_char_count > 1000` (227 products available)
- **Query:**
  ```sql
  WHERE description_char_count > 1000
  ```

### 2. **Category Distribution** ✅ (You mentioned this)
- **Rationale:** Ensures variety across product types
- **Approach:** 
  - Select products from diverse categories
  - Avoid over-representing single categories
  - Use `category_ids` JSONB array to identify category membership
- **Note:** Most products belong to multiple categories (Category 12 has 1,155 products)

### 3. **Featured Status** (Proxy for Popularity) ⭐ **RECOMMENDED**
- **Rationale:** Products featured in blog/newsletter likely have higher interest
- **Indicators:**
  - `blog_profiled_at IS NOT NULL` (1 product)
  - `newsletter_launched_at IS NOT NULL` (51 products)
- **Query:**
  ```sql
  WHERE (blog_profiled_at IS NOT NULL OR newsletter_launched_at IS NOT NULL)
  ```
- **Benefit:** These products have already been curated/selected for promotion

### 4. **Producer Information** ⭐ **RECOMMENDED**
- **Rationale:** Products with producer info have richer heritage/storytelling potential
- **Indicator:** `producer_id IS NOT NULL` (47 products)
- **Query:**
  ```sql
  WHERE producer_id IS NOT NULL
  ```
- **Benefit:** Enables deeper content about craftsmanship, heritage, suppliers

### 5. **Product Level** ⭐ **RECOMMENDED**
- **Rationale:** Luxury products may have more interesting stories/premium positioning
- **Distribution:**
  - Classic: 1,052 products
  - Luxury: 56 products
  - Essential: 49 products
- **Query:**
  ```sql
  WHERE product_level = 'luxury'  -- or 'essential' for broader appeal
  ```
- **Benefit:** Luxury products often have richer heritage narratives

### 6. **Recency** ⭐ **RECOMMENDED**
- **Rationale:** Newer products may be more relevant/trending
- **Indicators:**
  - `clan_created_at` - When product was added to CLAN
  - `first_seen_at` - When product was first discovered
  - `clan_updated_at` - Last update time
- **Query:**
  ```sql
  ORDER BY clan_created_at DESC  -- or first_seen_at DESC
  ```
- **Benefit:** Keeps content fresh and current

### 7. **Data Completeness** ⭐ **RECOMMENDED**
- **Rationale:** Complete data enables better content generation
- **Indicators:**
  - `has_detailed_data = TRUE` (all 1,157 products)
  - `supplier_name IS NOT NULL` - Has supplier info
  - `supplier_description IS NOT NULL` - Has supplier story
  - `image_url IS NOT NULL` - Has visual content
- **Query:**
  ```sql
  WHERE has_detailed_data = TRUE 
    AND supplier_name IS NOT NULL
    AND image_url IS NOT NULL
  ```

### 8. **Cross-Reference Activity** (Additional Signal)
- **Rationale:** Products referenced elsewhere may be more important
- **Indicators:**
  - Products with existing profile posts (`post.profile_product_id`)
  - Products in cross-promotion widgets
  - Products in posting queue
- **Query:**
  ```sql
  WHERE id IN (
    SELECT DISTINCT profile_product_id FROM post WHERE profile_product_id IS NOT NULL
  )
  ```

---

## Recommended Selection Strategy

### **Multi-Criteria Scoring Approach**

Combine multiple criteria with weighted scoring:

```sql
SELECT 
    id,
    name,
    description_char_count,
    product_level,
    producer_id,
    blog_profiled_at,
    newsletter_launched_at,
    supplier_name,
    category_ids,
    -- Scoring
    (
        (CASE WHEN description_char_count > 1000 THEN 3 ELSE 0 END) +
        (CASE WHEN description_char_count > 2000 THEN 2 ELSE 0 END) +
        (CASE WHEN blog_profiled_at IS NOT NULL THEN 5 ELSE 0 END) +
        (CASE WHEN newsletter_launched_at IS NOT NULL THEN 4 ELSE 0 END) +
        (CASE WHEN producer_id IS NOT NULL THEN 3 ELSE 0 END) +
        (CASE WHEN product_level = 'luxury' THEN 2 ELSE 0 END) +
        (CASE WHEN supplier_name IS NOT NULL THEN 1 ELSE 0 END)
    ) as selection_score
FROM clan_products
WHERE has_detailed_data = TRUE
ORDER BY selection_score DESC, description_char_count DESC
LIMIT 150  -- For 2-3 years coverage
```

### **Category Distribution Strategy**

1. **Identify top categories** (avoid over-representation)
2. **Select products evenly across categories**
3. **Prioritize within each category** by:
   - Description length
   - Featured status
   - Producer info
   - Product level

```sql
-- Example: Get top products per category
WITH ranked_products AS (
    SELECT 
        id,
        name,
        jsonb_array_elements_text(category_ids)::integer as category_id,
        description_char_count,
        ROW_NUMBER() OVER (
            PARTITION BY jsonb_array_elements_text(category_ids)::integer 
            ORDER BY description_char_count DESC
        ) as rank_in_category
    FROM clan_products
    WHERE has_detailed_data = TRUE
    AND description_char_count > 500
)
SELECT * FROM ranked_products
WHERE rank_in_category <= 5  -- Top 5 per category
ORDER BY category_id, rank_in_category
```

---

## Suggested Selection Priority

### **Tier 1: Best Candidates** (Highest Priority)
- ✅ Long descriptions (>1000 chars)
- ✅ Featured (blog or newsletter)
- ✅ Has producer info
- ✅ Luxury level (if available)
- ✅ Good category distribution

### **Tier 2: Good Candidates** (Secondary Priority)
- ✅ Long descriptions (>500 chars)
- ✅ Has producer info OR supplier info
- ✅ Classic level
- ✅ Good category distribution

### **Tier 3: Acceptable Candidates** (Fill remaining slots)
- ✅ Any detailed product
- ✅ Ensure category diversity
- ✅ Prioritize by description length

---

## Implementation Notes

1. **Target Count:** 150 products for 2-3 years coverage (similar to surnames)
2. **Category Balance:** Aim for 5-10 products per major category
3. **Avoid Duplicates:** Ensure products aren't already in sequence
4. **Manual Review:** Consider manual curation after automated selection
5. **Rebuild JSON:** After selection, rebuild JSON schedules for 2025-2027

---

## Additional Considerations

### **What We DON'T Have:**
- ❌ Direct sales data
- ❌ View/click statistics
- ❌ Customer ratings
- ❌ Inventory levels

### **What We CAN Use as Proxies:**
- ✅ Featured status (newsletter/blog) = likely popular
- ✅ Long descriptions = likely important products
- ✅ Producer info = likely premium/interesting products
- ✅ Recency = likely current/relevant products

---

## Next Steps

1. **Create selection script** using multi-criteria scoring
2. **Review selected products** for category distribution
3. **Create profile posts** for selected products
4. **Populate calendar_profile_sequence** table
5. **Rebuild JSON schedules**

