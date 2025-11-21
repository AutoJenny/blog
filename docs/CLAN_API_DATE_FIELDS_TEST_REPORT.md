# Clan.com API Date Fields Test Report

**Date:** 2025-11-20  
**Status:** ✅ **API PROVIDES FIELDS** | ❌ **NOT BEING STORED**  
**Purpose:** Test if clan.com API now provides `created_at` and `updated_at` fields

---

## Executive Summary

✅ **The clan.com API now provides date fields:**
- `created_at` - Product creation date (e.g., "2016-07-01 09:50:06")
- `updated_at` - Product last update date (e.g., "2025-02-24 16:33:10")

❌ **However, these fields are NOT being stored in the database:**
- `clan_created_at` is NULL for all products
- `clan_updated_at` is NULL for all products

**Root Cause:** The transformer function (`transform_product_for_ui`) does not pass through the date fields from the API response.

---

## API Test Results

### 1. getProductData Endpoint ✅

**URL:** `https://clan.com/clan/api/getProductData?sku=sr_esssw_tartan_sash_wool&include_categories=1`

**Response Fields:**
```json
{
  "sku": "sr_esssw_tartan_sash_wool",
  "product_id": "182",
  "title": "Essential Tartan Sash",
  "created_at": "2016-07-01 09:50:06",  ✅ AVAILABLE
  "updated_at": "2025-02-24 16:33:10",  ✅ AVAILABLE
  ...
}
```

**Status:** ✅ Both `created_at` and `updated_at` are present in the API response

### 2. getProducts Endpoint ✅

**URL:** `https://clan.com/clan/api/getProducts?limit=1&sort=id_desc`

**Response Fields:**
```json
{
  "title": "...",
  "sku": "...",
  "created_at": "2016-07-01T10:50:06+01:00",  ✅ AVAILABLE (ISO format)
  "updated_at": "2025-02-24 16:33:10",         ✅ AVAILABLE
  ...
}
```

**Status:** ✅ Both `created_at` and `updated_at` are present in the API response

---

## Code Analysis

### Current Implementation

#### 1. API Response ✅
- API provides `created_at` and `updated_at` fields
- Fields are strings in various formats (ISO, datetime string)

#### 2. Transformer Function ❌ **ISSUE FOUND**

**Location:** `blog-clan-api/transformers.py` - `transform_product_for_ui()`

**Problem:** The transformer does NOT include date fields in the returned dictionary.

**Current Code (lines 79-94):**
```python
return {
    'id': int(product.get('product_id', 0)),
    'name': product.get('title', ''),
    'sku': product.get('sku', ''),
    'price': f'£{base_price}.99',
    'image_url': image_url,
    'url': product.get('product_url', ''),
    'description': product.get('description', ''),
    'short_description': product.get('short_description', ''),
    'supplier_name': product.get('supplier_name', ''),
    'supplier_description': product.get('supplier_description', ''),
    'configurable_options': product.get('configurable_options', None),
    'additional_data': product.get('additional_data', None),
    'dimensions': product.get('dimensions', ''),
    'category_ids': []
    # ❌ MISSING: 'created_at' and 'updated_at'
}
```

#### 3. Storage Function ✅ **READY**

**Location:** `blog-launchpad/clan_cache.py` - `store_single_product()`

**Status:** The storage function already has logic to extract and store date fields (lines 633-643):

```python
# Parse created_at from API (ISO format string) to datetime
created_at_str = product_data.get('created_at') or product_data.get('clan_created_at')
clan_created_at = None
if created_at_str:
    try:
        from dateutil import parser as date_parser
        clan_created_at = date_parser.parse(created_at_str)
    except Exception:
        clan_created_at = created_at_str

# updated_at is now available in API
clan_updated_at = product_data.get('updated_at') or product_data.get('clan_updated_at')
```

**Note:** The comment on line 642 says "updated_at is not available in API" but this is now **outdated** - the API does provide it!

#### 4. Database Schema ✅

**Table:** `clan_products`
- `clan_created_at` (TIMESTAMP) - ✅ Column exists
- `clan_updated_at` (TIMESTAMP) - ✅ Column exists

**Current State:**
- All products have `clan_created_at = NULL`
- All products have `clan_updated_at = NULL`

---

## Test Results

### Product Test: `sr_esssw_tartan_sash_wool`

**API Response:**
- `created_at`: "2016-07-01 09:50:06" ✅
- `updated_at`: "2025-02-24 16:33:10" ✅

**Database State:**
- `clan_created_at`: NULL ❌
- `clan_updated_at`: NULL ❌
- `first_seen_at`: 2025-09-20 08:42:36 (when sync discovered it)

**Conclusion:** Date fields are available from API but not being stored.

---

## Required Fix

### Update Transformer Function

**File:** `blog-clan-api/transformers.py`

**Change:** Add date fields to the returned dictionary:

```python
return {
    'id': int(product.get('product_id', 0)),
    'name': product.get('title', ''),
    'sku': product.get('sku', ''),
    # ... existing fields ...
    'category_ids': [],
    # ADD THESE:
    'created_at': product.get('created_at'),  # Pass through from API
    'updated_at': product.get('updated_at'),  # Pass through from API
}
```

### Update Storage Function Comment

**File:** `blog-launchpad/clan_cache.py` (line 642)

**Change:** Update the outdated comment:

```python
# OLD COMMENT (line 642):
# updated_at is not available in API - will remain None

# NEW COMMENT:
# updated_at is now available in API (as of 2025-11-20)
clan_updated_at = product_data.get('updated_at') or product_data.get('clan_updated_at')
```

---

## Impact

### After Fix

1. **New Products:** Will have `clan_created_at` and `clan_updated_at` populated during sync
2. **Existing Products:** Will remain NULL until next sync/enrichment
3. **Product Selection:** Can use `clan_created_at` instead of `first_seen_at` for finding "new" products
4. **Magic Number Removal:** Can remove `min_product_id = 10000` hack once all products are synced

### Migration Strategy

**Option 1: Wait for Natural Sync**
- Let existing products get updated during next sync
- No manual intervention needed
- Takes time (depends on sync frequency)

**Option 2: Bulk Enrichment**
- Run enrichment script on all products
- Faster but requires running script
- Can be done in background

---

## Next Steps

1. ✅ **Fix transformer** - Add date fields to `transform_product_for_ui()`
2. ✅ **Update comment** - Fix outdated comment in `store_single_product()`
3. ⏳ **Test with real sync** - Verify dates are stored correctly
4. ⏳ **Update product selection** - Use `clan_created_at` instead of `first_seen_at`
5. ⏳ **Remove magic number** - Remove `min_product_id = 10000` hack

---

## Files to Modify

1. `blog-clan-api/transformers.py` - Add date fields to transformer
2. `blog-launchpad/clan_cache.py` - Update comment (optional, but good practice)

---

## Verification

After fix, verify with:
```sql
SELECT id, sku, name, clan_created_at, clan_updated_at, first_seen_at
FROM clan_products
WHERE clan_created_at IS NOT NULL
LIMIT 10;
```

Expected: New products should have `clan_created_at` and `clan_updated_at` populated.

