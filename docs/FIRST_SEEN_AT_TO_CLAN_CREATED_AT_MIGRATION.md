# Migration: `first_seen_at` → `clan_created_at`

**Date:** 2025-11-20  
**Status:** ✅ **COMPLETED**

---

## Summary

Replaced all uses of `first_seen_at` (sync discovery date) with `clan_created_at` (actual product creation date) for finding "recently added" products. Also removed the hacky `min_product_id = 10000` magic number filter.

---

## Changes Made

### 1. `blog-core/newsletter/selectors/products.py`

#### `get_product_pool()` function:
- ✅ **Removed** `min_product_id` parameter (was defaulting to 10000)
- ✅ **Changed** `first_seen_at` to `COALESCE(clan_created_at, first_seen_at)` in WHERE clause
- ✅ **Changed** `ORDER BY first_seen_at DESC` to `ORDER BY COALESCE(clan_created_at, first_seen_at) DESC`
- ✅ **Updated** docstring to reflect use of `clan_created_at` instead of `first_seen_at`
- ✅ **Updated** parameter description from "Minimum first_seen_at date" to "Minimum clan_created_at date"

**Query Changes:**
```sql
-- OLD:
WHERE first_seen_at > %s
  AND id > %s  -- Magic number filter
ORDER BY first_seen_at DESC

-- NEW:
WHERE COALESCE(clan_created_at, first_seen_at) > %s
  -- No magic number filter
ORDER BY COALESCE(clan_created_at, first_seen_at) DESC
```

**Fallback Logic:**
- Uses `clan_created_at` when available (new products from API)
- Falls back to `first_seen_at` for legacy products that don't have `clan_created_at` populated
- This ensures backward compatibility while using accurate dates for new products

#### `select_new_products()` function (DEPRECATED):
- ✅ **Removed** `min_product_id` parameter (was defaulting to 10000)
- ✅ **Changed** `first_seen_at` to `COALESCE(clan_created_at, first_seen_at)` in WHERE clause
- ✅ **Changed** `ORDER BY first_seen_at DESC` to `ORDER BY COALESCE(clan_created_at, first_seen_at) DESC`
- ✅ **Updated** docstring to reflect use of `clan_created_at` instead of `first_seen_at`

---

### 2. `blog-core/newsletter/services/block_suggestion_service.py`

#### `get_suggestions_for_block()` function (new_products block):
- ✅ **Removed** `min_product_id=10000` parameter from both `get_product_pool()` calls
- ✅ No other changes needed (function signature already updated)

**Before:**
```python
product_pool = get_product_pool(
    since_iso_timestamp=since_date,
    pool_size=50,
    exclude_launched=True,
    min_product_id=10000  # ❌ REMOVED
)
```

**After:**
```python
product_pool = get_product_pool(
    since_iso_timestamp=since_date,
    pool_size=50,
    exclude_launched=True
    # ✅ No magic number filter
)
```

---

### 3. `check_new_products.py` (Utility Script)

- ✅ **Changed** query to use `COALESCE(clan_created_at, first_seen_at)` instead of `first_seen_at`
- ✅ **Updated** display to show both `clan_created_at` and `first_seen_at` for comparison
- ✅ **Updated** print message from "Checking for products first_seen_at" to "Checking for products clan_created_at"

**Query Changes:**
```sql
-- OLD:
WHERE first_seen_at >= to_timestamp(%s, 'YYYY-MM-DD HH24:MI:SS')
ORDER BY first_seen_at DESC

-- NEW:
WHERE COALESCE(clan_created_at, first_seen_at) >= to_timestamp(%s, 'YYYY-MM-DD HH24:MI:SS')
ORDER BY COALESCE(clan_created_at, first_seen_at) DESC
```

**Display Changes:**
- Now shows both `clan_created_at` and `first_seen_at` in output
- Indicates when using `first_seen_at` as fallback: `"(sync discovery)"`

---

## Benefits

### 1. **Accurate "New Product" Detection** ✅
- Uses actual product creation date from clan.com API
- No longer dependent on sync frequency
- Products created recently on clan.com are correctly identified as "new"

### 2. **Removed Magic Number Filter** ✅
- No longer excludes valid new products with ID < 10000
- No longer includes old products with ID > 10000
- Simpler, more reliable logic

### 3. **Backward Compatibility** ✅
- Falls back to `first_seen_at` for legacy products without `clan_created_at`
- Existing functionality continues to work
- Gradual migration as more products get `clan_created_at` populated

### 4. **Better Newsletter Content** ✅
- Newsletter "Products Spotlight" block now features truly new products
- Not just products that were recently discovered by sync
- More relevant content for readers

---

## Testing

### Syntax Check ✅
- All files pass Python syntax validation
- No linting errors

### Function Signature Changes ✅
- `get_product_pool()`: Removed `min_product_id` parameter
- `select_new_products()`: Removed `min_product_id` parameter
- All callers updated to match new signatures

### Backward Compatibility ✅
- Uses `COALESCE(clan_created_at, first_seen_at)` to handle legacy products
- Products without `clan_created_at` still work (use `first_seen_at`)

---

## Files Modified

1. ✅ `blog-core/newsletter/selectors/products.py`
   - `get_product_pool()` function
   - `select_new_products()` function

2. ✅ `blog-core/newsletter/services/block_suggestion_service.py`
   - `get_suggestions_for_block()` function (new_products block)

3. ✅ `check_new_products.py`
   - Query and display logic

---

## Related Documentation

- `docs/FIRST_SEEN_AT_USAGE_ANALYSIS.md` - Analysis of all `first_seen_at` uses
- `docs/HACKY_PRODUCT_SELECTION_ANALYSIS.md` - Original analysis of hacky methods
- `docs/CLAN_API_DATE_FIELDS_TEST_REPORT.md` - Testing of `clan_created_at` field

---

## Next Steps (Optional)

1. **Monitor Newsletter Product Selection**
   - Verify newsletter "Products Spotlight" block shows truly new products
   - Check that product selection works correctly

2. **Update Documentation**
   - Update `docs/newsletter/blocks/products.md` to reflect use of `clan_created_at`
   - Update any other docs that mention `first_seen_at` for product selection

3. **Consider Removing `first_seen_at` Fallback** (Future)
   - Once all products have `clan_created_at` populated
   - Can simplify queries to use only `clan_created_at`
   - But keep `first_seen_at` field for tracking sync discovery

---

## Notes

- `first_seen_at` field is **NOT deprecated** - it's still useful for tracking when we first discovered products
- The migration only changes **how we identify "new" products** - from sync discovery date to actual creation date
- `first_seen_at` is still preserved and updated in the cache management code
- The fallback to `first_seen_at` ensures legacy products continue to work

