# CLAN.com API Date Fields Diagnosis

## Summary

Investigation into why `clan_created_at` and `clan_updated_at` fields are not being populated in our database.

## API Testing Results

### 1. getProducts API (`/clan/api/getProducts`)

**Response Format:**
- Returns: Array of product objects as **DICT** (not list)
- Each product contains:
  - `created_at`: ✅ **AVAILABLE** (ISO format string, e.g., `"2016-07-01T10:50:06+01:00"`)
  - `updated_at`: ❌ **NOT AVAILABLE** (field does not exist in response)

**Example Response:**
```json
{
  "title": "Essential Tartan Sash",
  "sku": "sr_esssw_tartan_sash_wool",
  "product_url": "https://clan.com/essential-scotweb-tartan-sash",
  "description": "...",
  "created_at": "2016-07-01T10:50:06+01:00",
  "product_id": "182",
  "printable_design_type": false
}
```

### 2. getProductData API (`/clan/api/getProductData?sku=XXX`)

**Response Format:**
- Returns: Single product object as **DICT**
- Date fields: ❌ **NONE AVAILABLE**
  - `created_at`: ❌ **NOT IN RESPONSE**
  - `updated_at`: ❌ **NOT IN RESPONSE**

**Example Response Keys:**
```
['sku', 'product_id', 'title', 'short_description', 'description', 
 'price', 'image', 'product_url', 'printable_design_type', 
 'supplier_name', 'supplier_description', 'configurable_options', 
 'additional_data', 'dimensions']
```

**Note:** No date-related fields are present in this API response.

## Root Causes

### 1. Bug in Our Code (FIXED)

**Location:** `blog-launchpad/clan_cache.py` - `download_full_catalog()` method

**Issue:**
- Code was treating `getProducts` API response as **LIST** format
- Actually returns **DICT** format
- Was accessing fields by index (`product[5]`, `product[0]`) instead of keys
- **Not extracting `created_at` field at all**

**Fix Applied:**
- Updated to handle DICT format correctly
- Now extracts `created_at` from `product.get('created_at')`
- Added date parsing to convert ISO string to datetime object

### 2. API Limitations (REQUIRES CLAN.COM TEAM ACTION)

#### Missing `created_at` in getProductData
- **Issue:** `getProductData` API does not return `created_at` field
- **Impact:** When fetching detailed product data by SKU, we cannot get creation date
- **Request:** Add `created_at` field to `getProductData` API response

#### Missing `updated_at` in Both APIs
- **Issue:** Neither `getProducts` nor `getProductData` return `updated_at` field
- **Impact:** Cannot track when products were last modified on clan.com
- **Request:** Add `updated_at` field to both API responses

## Current Database Status

**Recent Products (ID > 10000):**
- `clan_created_at`: NULL (was not being extracted)
- `clan_updated_at`: NULL (not available from API)
- `first_seen_at`: ✅ Populated (our internal tracking)

## Recommendations for CLAN.com Tech Team

### Priority 1: Add `updated_at` to Both APIs
**Request:** Include `updated_at` field in API responses to track product modifications.

**Suggested Format:**
- ISO 8601 format string (same as `created_at`)
- Example: `"2025-11-15T14:30:00+00:00"`
- Should reflect last modification time in clan.com system

**APIs to Update:**
1. `/clan/api/getProducts` - Add `updated_at` to each product object
2. `/clan/api/getProductData` - Add `updated_at` to product object

### Priority 2: Add `created_at` to getProductData
**Request:** Include `created_at` field in `getProductData` API response for consistency.

**Rationale:**
- `getProducts` already returns `created_at`
- `getProductData` should return the same field for consistency
- Allows us to get creation date when fetching individual products

## Technical Details

### Date Format
- **Current Format:** ISO 8601 with timezone offset
- **Example:** `"2016-07-01T10:50:06+01:00"`
- **Parsing:** Using `dateutil.parser` to convert to Python datetime objects
- **Storage:** PostgreSQL TIMESTAMP column

### Code Changes Made
1. Fixed `download_full_catalog()` to extract `created_at` from DICT format
2. Added date parsing to convert ISO strings to datetime objects
3. Updated `store_products()` to handle `created_at` correctly
4. Updated `store_single_product()` to parse `created_at` if provided

## Testing

After fixes:
- `getProducts` API: ✅ Will now extract and store `created_at`
- `getProductData` API: ⚠️ Still cannot get `created_at` (API limitation)
- `updated_at`: ❌ Still not available (API limitation)

## Next Steps

1. ✅ **COMPLETED:** Fixed our code to extract `created_at` from `getProducts`
2. ⏳ **PENDING:** Request CLAN.com team to add `updated_at` to both APIs
3. ⏳ **PENDING:** Request CLAN.com team to add `created_at` to `getProductData` API

