# Hacky Product Selection Process - Analysis

**Date:** 2025-11-20  
**Purpose:** Identify and document the hacky process for finding recently added products

---

## Executive Summary

The current process for finding "recently added" products uses several **hacky workarounds** that are brittle and unreliable:

1. **Magic number filtering**: `min_product_id: int = 10000` - Assumes product IDs > 10000 are "new"
2. **`first_seen_at` timestamp**: Relies on sync discovery date, not actual product creation date
3. **Arbitrary time windows**: Default 60-day cutoff for "recent" products
4. **String concatenation SQL**: Security risk and code smell
5. **Redundant filtering**: Image URL validation done twice (SQL + Python)
6. **Fragile deduplication**: Uses product name instead of unique identifiers

---

## Current Implementation

### Location
- **File:** `blog-core/newsletter/selectors/products.py`
- **Functions:**
  - `get_product_pool()` - Main function (lines 12-86)
  - `select_new_products()` - Deprecated but still used (lines 169-315)

### Query Logic

```sql
SELECT id, name, sku, image_url, url, short_description, first_seen_at, category_ids
FROM clan_products
WHERE first_seen_at > %s           -- Arbitrary timestamp (default: 60 days ago)
  AND id > %s                      -- MAGIC NUMBER: 10000 (hacky!)
  AND image_url IS NOT NULL
  AND TRIM(image_url) <> ''
  AND (image_url LIKE 'http://%%' OR image_url LIKE 'https://%%')
  AND newsletter_launched_at IS NULL  -- Exclude already launched
ORDER BY first_seen_at DESC
LIMIT %s
```

---

## Hacky Elements Identified

### 1. Magic Number: `min_product_id = 10000` ⚠️ **CRITICAL HACK**

**Location:** Lines 12, 23, 46, 57, 169, 182, 205, 216

**Problem:**
- Hardcoded assumption that products with `id > 10000` are "new"
- No actual relationship between product ID and creation date
- Breaks if:
  - Product IDs aren't sequential
  - There are gaps in ID sequence
  - Old products get re-added with new IDs
  - Product ID sequence resets or changes

**Why it exists:**
- Likely a quick workaround to exclude legacy/test products
- Assumes newer products have higher IDs (may have been true initially)

**Impact:**
- **High**: Could exclude valid new products if IDs are < 10000
- **High**: Could include old products if IDs are > 10000 but products are old
- **Medium**: Makes the system brittle to ID changes

**Example:**
```python
# If a product with ID 5000 is actually new, it will be excluded
# If a product with ID 15000 is actually old, it will be included
```

---

### 2. `first_seen_at` Timestamp ⚠️ **RELIABILITY ISSUE**

**Location:** Lines 15, 20, 42, 45, 51, 175, 179, 201, 204, 210

**Problem:**
- `first_seen_at` is set when the **sync process first discovers** the product, not when it was **actually created** on clan.com
- Dependent on sync frequency and timing
- If sync runs infrequently, "new" products might have old `first_seen_at` values
- If sync runs frequently, old products might get new `first_seen_at` values

**Why it exists:**
- `clan_products` table doesn't have a reliable `created_at` field from clan.com
- `first_seen_at` is the best available proxy

**Impact:**
- **Medium**: May miss truly new products if sync hasn't run recently
- **Medium**: May include old products that were just discovered
- **Low**: Works reasonably well if sync runs regularly

**Better Alternative:**
- Use `clan_created_at` field if available (from clan.com API)
- Or use `last_updated` field if it tracks creation

---

### 3. Arbitrary Time Window: 60 Days ⚠️ **ARBITRARY CUTOFF**

**Location:** `block_suggestion_service.py` (default `since_iso_timestamp`)

**Problem:**
- Default cutoff of "last 60 days" is arbitrary
- No business logic behind this number
- Hardcoded in multiple places

**Impact:**
- **Low**: Works but is inflexible
- **Low**: May need adjustment based on product volume

**Better Alternative:**
- Make it configurable
- Base it on actual business requirements (e.g., "products added this month")

---

### 4. String Concatenation SQL ⚠️ **SECURITY RISK**

**Location:** Lines 32, 50, 191, 209

**Problem:**
```python
exclude_clause = "AND newsletter_launched_at IS NULL" if exclude_launched else ""
query = """
    SELECT ...
    WHERE ...
    """ + exclude_clause + """
    ORDER BY ...
"""
```

**Issues:**
- Not using parameterized queries for conditional clauses
- While not directly vulnerable (no user input), it's a code smell
- Makes query harder to read and maintain

**Impact:**
- **Low**: Security risk is minimal (no user input)
- **Medium**: Code maintainability issue

**Better Alternative:**
```python
conditions = ["first_seen_at > %s", "id > %s", ...]
params = [since_iso_timestamp, min_product_id, ...]

if exclude_launched:
    conditions.append("newsletter_launched_at IS NULL")

query = f"SELECT ... WHERE {' AND '.join(conditions)} ORDER BY ..."
```

---

### 5. Redundant Image URL Filtering ⚠️ **INEFFICIENCY**

**Location:** Lines 48-49 (SQL) and 62-69 (Python)

**Problem:**
- Image URL validation done **twice**:
  1. In SQL: `image_url IS NOT NULL AND TRIM(image_url) <> '' AND (image_url LIKE 'http://%%' OR image_url LIKE 'https://%%')`
  2. In Python: Double-checks the same conditions

**Why it exists:**
- Comment says "safety check" but it's redundant
- SQL should be sufficient

**Impact:**
- **Low**: Performance impact is minimal
- **Low**: Code clarity issue

**Better Alternative:**
- Remove Python check (SQL is sufficient)
- Or remove SQL check and do it all in Python (less efficient)

---

### 6. Fragile Deduplication ⚠️ **RELIABILITY ISSUE**

**Location:** Lines 71-80

**Problem:**
```python
# Deduplicate by product name
seen_names = set()
unique_products = []
for p in valid_products:
    name = p.get('name')
    if name:
        name_str = str(name).strip() if name else ''
        if name_str and name_str not in seen_names:
            seen_names.add(name_str)
            unique_products.append(p)
```

**Issues:**
- Uses product **name** for deduplication instead of unique ID
- Two different products could have the same name (variants, different SKUs)
- Case-sensitive matching (though `.strip()` helps)
- Whitespace differences could cause duplicates

**Impact:**
- **Medium**: Could exclude valid products if names match
- **Medium**: Could include duplicates if names differ slightly

**Better Alternative:**
- Use `id` or `sku` for deduplication (guaranteed unique)
- Or use `(id, sku)` tuple for more robust deduplication

---

## Usage Locations

### Where It's Called

1. **`blog-core/newsletter/services/block_suggestion_service.py`** (lines 108, 117)
   ```python
   get_product_pool(
       since_iso_timestamp=since_iso_timestamp,
       pool_size=50,
       exclude_launched=True,
       min_product_id=10000  # <-- Magic number
   )
   ```

2. **`blog-core/newsletter/services/block_editor_service.py`** (line 51)
   - Uses `get_product_pool()` for product selection

3. **Newsletter block creation/editing**
   - "New Products Spotlight" block uses this logic

---

## Recommended Solutions

### Short-Term Fixes (Low Risk)

1. **Remove magic number filtering**
   - Remove `min_product_id` parameter or make it configurable
   - Or use a more reliable field (e.g., `clan_created_at` if available)

2. **Fix SQL query building**
   - Use proper parameterized queries
   - Build conditions list dynamically

3. **Remove redundant filtering**
   - Remove Python image URL check (SQL is sufficient)

4. **Fix deduplication**
   - Use `id` or `sku` instead of `name`

### Long-Term Solutions (Higher Risk, More Work)

1. **Use proper creation timestamp**
   - Check if `clan_created_at` field exists in `clan_products`
   - If not, add it during sync from clan.com API
   - Use this instead of `first_seen_at`

2. **Add product metadata table**
   - Track actual product creation dates
   - Track product lifecycle (new, featured, archived)
   - More reliable than inferring from IDs or sync dates

3. **Implement proper product status**
   - Add `product_status` field (new, active, archived)
   - Set during sync based on clan.com data
   - Use for filtering instead of magic numbers

---

## Database Schema Check

### Current `clan_products` Fields ✅ **VERIFIED**

**Timestamp-related columns:**
- `first_seen_at` (timestamp) - When sync first discovered product ✅ **IN USE**
- `last_updated` (timestamp) - Last update in our system ✅ **EXISTS**
- `clan_created_at` (timestamp) - **EXISTS BUT NULL** ❌ **NOT POPULATED**
- `clan_updated_at` (timestamp) - **EXISTS BUT NULL** ❌ **NOT POPULATED**
- `newsletter_launched_at` (timestamp) - When product was featured ✅ **IN USE**

**Key Finding:**
- `clan_created_at` and `clan_updated_at` fields **exist** but are **NULL** for all products
- This means the sync process is **not populating** these fields from the clan.com API
- We're forced to use `first_seen_at` (sync discovery date) instead of actual creation date

**Sample Data:**
```
ID 157045:
  first_seen_at: 2025-11-03 14:50:26
  last_updated: 2025-11-03 14:50:26
  clan_created_at: NULL  ← Should be populated from API!
  clan_updated_at: NULL   ← Should be populated from API!
```

**Recommendation:**
- Check if clan.com API provides `created_at` / `updated_at` fields
- Update sync process to populate `clan_created_at` and `clan_updated_at`
- Use `clan_created_at` instead of `first_seen_at` for finding "new" products

---

## Impact Assessment

### Current System Reliability
- **Works for now**: If sync runs regularly and product IDs are sequential
- **Brittle**: Will break if ID sequence changes or sync timing changes
- **Unreliable**: May miss new products or include old ones

### Risk Level
- **High**: Magic number filtering (`id > 10000`)
- **Medium**: `first_seen_at` timestamp reliability
- **Low**: Other issues (redundant filtering, deduplication)

---

## Next Steps

1. **Immediate**: Document the hacky parts (this document)
2. **Short-term**: Check database schema for better timestamp fields
3. **Medium-term**: Remove magic number, fix SQL, improve deduplication
4. **Long-term**: Implement proper product status tracking

---

## Files to Review

- `blog-core/newsletter/selectors/products.py` - Main implementation
- `blog-core/newsletter/services/block_suggestion_service.py` - Usage
- `blog-core/newsletter/services/block_editor_service.py` - Usage
- `docs/newsletter/blocks/products.md` - Documentation (needs update)

---

## Questions for User

1. **Magic Number**: Why is `min_product_id = 10000` used? Is there a business reason?
2. **Timestamps**: Does `clan_products` have `clan_created_at` or similar field?
3. **Time Window**: Why 60 days? Should this be configurable?
4. **Priority**: Which hacky elements should be fixed first?

