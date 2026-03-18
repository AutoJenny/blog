# `first_seen_at` Field Usage Analysis

**Date:** 2025-11-20  
**Purpose:** Document all contexts where `first_seen_at` is used and identify hacky patterns

---

## Executive Summary

The `first_seen_at` field is used in **multiple contexts** to identify "recently added" products. However, it's a **hacky workaround** because:

1. **It tracks sync discovery date, not actual creation date** - When our sync process first discovers a product, not when it was actually created on clan.com
2. **Dependent on sync frequency** - If sync runs infrequently, truly new products might have old `first_seen_at` values
3. **Now obsolete** - We now have `clan_created_at` and `clan_updated_at` fields populated from the API, which are more accurate

---

## All Contexts Where `first_seen_at` is Used

### 1. Newsletter Product Selection ⚠️ **PRIMARY USE CASE**

**Location:** `blog-core/newsletter/selectors/products.py`

**Functions:**
- `get_product_pool()` (lines 12-86)
- `select_new_products()` (lines 169-315) - DEPRECATED but still used

**Usage:**
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

**Context:**
- Used to find "recently added" products for newsletter "Products Spotlight" block
- Filters products discovered in the last 60 days (arbitrary cutoff)
- Combined with magic number `min_product_id = 10000` to exclude older products
- Orders by `first_seen_at DESC` to show newest discoveries first

**Called From:**
- `blog-core/newsletter/services/block_suggestion_service.py` (lines 102-125)
  - Creates product pool for newsletter block suggestions
  - Uses 60-day window: `since_date = (datetime.now() - timedelta(days=60)).isoformat()`

**Problem:**
- Uses sync discovery date instead of actual product creation date
- Now that `clan_created_at` is populated, should use that instead

---

### 2. Product Cache Management

**Location:** `blog-launchpad/clan_cache.py`

**Usage:**
- **Table Creation** (line 55): Defines `first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP`
- **Column Addition** (line 84): Ensures column exists on existing installations
- **Backfill Logic** (lines 140-143): Backfills `first_seen_at` from `last_updated` where missing
  ```sql
  UPDATE clan_products
  SET first_seen_at = COALESCE(first_seen_at, last_updated)
  ```

**Context:**
- Database schema management
- Ensures `first_seen_at` is set when products are first synced
- Preserves `first_seen_at` on updates (never overwrites)

**Note:**
- The `store_single_product()` method preserves `first_seen_at` on upserts
- This ensures the field tracks when we first discovered the product, not when it was last updated

---

### 3. New Products Check Script

**Location:** `check_new_products.py`

**Usage:**
```python
# Lines 25, 36, 45, 48-49
WHERE first_seen_at >= to_timestamp(%s, 'YYYY-MM-DD HH24:MI:SS')
ORDER BY first_seen_at DESC
```

**Context:**
- Standalone script to check for new products since last update
- Gets cutoff from `/api/clan/cache/stats` endpoint
- Lists products discovered since the cutoff date
- Used for manual monitoring of new product discoveries

**Purpose:**
- Administrative tool to see what products were recently discovered by sync
- Not used in production workflows

---

### 4. Documentation References

**Files:**
- `docs/HACKY_PRODUCT_SELECTION_ANALYSIS.md` - Documents the hacky nature
- `docs/CLAN_API_DATE_FIELDS_TEST_REPORT.md` - Notes that `clan_created_at` should replace it
- `docs/newsletter/blocks/products.md` - Documents newsletter usage
- `docs/clan_products/schema.md` - Schema documentation
- Various other docs mentioning the field

**Context:**
- Documentation of the field's purpose and limitations
- Notes that it's a workaround until `clan_created_at` is available

---

### 5. Knowledge Base (Proposed/Future)

**Location:** `docs/data_intelligence/knowledge_base/TABLE_STRUCTURE_PROPOSAL.md`

**Usage:**
- Proposed schema includes `first_seen_at` for categories and articles
- Similar pattern: track when content was first discovered, not when it was created

**Context:**
- Future feature planning
- Not yet implemented

---

## Key Issues with `first_seen_at`

### 1. **Sync Discovery Date vs. Creation Date** ⚠️ **FUNDAMENTAL PROBLEM**

**Problem:**
- `first_seen_at` = When our sync process first discovered the product
- `clan_created_at` = When the product was actually created on clan.com
- These can be very different!

**Example:**
- Product created on clan.com: 2025-01-01
- Our sync first discovers it: 2025-11-20
- `first_seen_at`: 2025-11-20 (wrong - makes it look "new")
- `clan_created_at`: 2025-01-01 (correct - product is actually 10 months old)

**Impact:**
- Newsletter might feature old products as "new"
- Truly new products might be missed if sync hasn't run recently

---

### 2. **Dependency on Sync Frequency** ⚠️ **RELIABILITY ISSUE**

**Problem:**
- If sync runs daily: `first_seen_at` is reasonably accurate
- If sync runs weekly: Products created 6 days ago might not be discovered yet
- If sync runs monthly: Products created 29 days ago might not be discovered yet

**Impact:**
- Inconsistent "new product" detection
- May miss truly new products if sync is delayed

---

### 3. **Arbitrary Time Windows** ⚠️ **HACKY CUTOFF**

**Problem:**
- Default 60-day cutoff is arbitrary
- No business logic behind this number
- Hardcoded in multiple places

**Locations:**
- `blog-core/newsletter/services/block_suggestion_service.py` (line 102)
- `docs/newsletter/blocks/products.md` (mentions 60 days)

**Impact:**
- Inflexible - can't easily adjust based on product volume
- May need different windows for different use cases

---

### 4. **Combined with Magic Number** ⚠️ **DOUBLE HACKY**

**Problem:**
- `first_seen_at > 60 days ago` AND `id > 10000`
- Two hacky filters combined make it even more unreliable

**Impact:**
- Products with ID < 10000 are excluded even if they're truly new
- Products with ID > 10000 are included even if they're old

---

## Recommended Fixes

### Priority 1: Replace with `clan_created_at` ✅ **NOW AVAILABLE**

**Status:** `clan_created_at` and `clan_updated_at` are now populated from the API (as of date sync completion)

**Action Required:**
1. **Update `get_product_pool()`** in `blog-core/newsletter/selectors/products.py`:
   ```sql
   -- Change from:
   WHERE first_seen_at > %s
   ORDER BY first_seen_at DESC
   
   -- To:
   WHERE clan_created_at > %s
   ORDER BY clan_created_at DESC
   ```

2. **Update `select_new_products()`** (deprecated but still used):
   - Same change as above

3. **Update `block_suggestion_service.py`**:
   - Change function calls to use `clan_created_at` instead of `first_seen_at`

4. **Update `check_new_products.py`**:
   - Change to use `clan_created_at` for more accurate "new product" detection

**Benefits:**
- Uses actual product creation date, not sync discovery date
- More reliable "new product" detection
- Consistent regardless of sync frequency

---

### Priority 2: Remove Magic Number Filter

**Action Required:**
- Remove `min_product_id = 10000` filter from all product selection queries
- Use `clan_created_at` as the sole filter for "new" products

**Benefits:**
- No longer excludes valid new products with low IDs
- Simpler, more reliable logic

---

### Priority 3: Make Time Window Configurable

**Action Required:**
- Replace hardcoded 60-day window with configurable parameter
- Allow different windows for different use cases

**Benefits:**
- More flexible
- Can adjust based on product volume or business needs

---

## Migration Plan

### Step 1: Update Product Selection Functions
- [ ] Update `get_product_pool()` to use `clan_created_at`
- [ ] Update `select_new_products()` to use `clan_created_at`
- [ ] Remove `min_product_id` parameter (or make it optional with default None)

### Step 2: Update Callers
- [ ] Update `block_suggestion_service.py` to pass `clan_created_at` filters
- [ ] Update any other callers of product selection functions

### Step 3: Update Utility Scripts
- [ ] Update `check_new_products.py` to use `clan_created_at`

### Step 4: Testing
- [ ] Verify newsletter product selection still works
- [ ] Verify "new products" are actually new (created recently, not just discovered recently)
- [ ] Test with products that have different `first_seen_at` vs `clan_created_at` values

### Step 5: Documentation
- [ ] Update documentation to reflect use of `clan_created_at`
- [ ] Mark `first_seen_at` as deprecated for "new product" detection
- [ ] Note that `first_seen_at` is still useful for tracking sync discovery

---

## Summary

**Total Contexts Found:** 5
1. ✅ Newsletter product selection (PRIMARY - needs fixing)
2. ✅ Product cache management (schema/backfill - OK as-is)
3. ✅ New products check script (utility - should update)
4. ✅ Documentation (informational - should update)
5. ⏳ Knowledge base (proposed - not yet implemented)

**Critical Fixes Needed:**
- Replace `first_seen_at` with `clan_created_at` in product selection queries
- Remove `min_product_id = 10000` magic number filter
- Update all callers to use new date field

**Status:** `clan_created_at` is now populated and ready to use! ✅



