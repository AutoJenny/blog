# Weekly Sync Flow

## Overview
The weekly sync discovers new and changed products from clan.com using a two-tier approach:
1. **Discovery**: Fast list API (getProducts) to identify candidates
2. **Enrichment**: Detailed API (getProductData) only for candidates

## Process Steps

### 1. Gate Check
- Reads `list_last_successful_sync_at` from `clan_cache_metadata`
- If last run < 7 days ago and `force=false`, sync exits immediately
- Otherwise, proceeds to discovery

### 2. Discovery Phase
- Calls `getProducts` with:
  - `sort=id_desc` (newest first, as recommended by clan.com techs)
  - Pagination: 200 products per page, up to 100 pages
  - Filters client-side by `created_at >= last_successful_sync_at`
  
- Stop conditions:
  - 3 consecutive pages with no candidates
  - API returns error or empty batch
  - Reaches max pages limit

### 3. Enrichment Phase
For each candidate product:
1. Fetch detailed data via `getProductData(sku, all_images=False)`
2. Transform and map extended fields:
   - `short_description`
   - `supplier_name`, `supplier_description`
   - `configurable_options` (JSONB)
   - `clan_created_at`, `clan_updated_at`
3. Build content hash from key fields
4. Compare hash with existing product:
   - **New**: Hash doesn't exist → `inserted` counter
   - **Changed**: Hash differs → `updated` counter
   - **Unchanged**: Hash matches → `unchanged` counter (skip upsert)
5. Upsert product (preserves `first_seen_at` if exists)

### 4. Completion
- Updates `list_last_successful_sync_at` in metadata
- Sets sync state to `finished`
- Returns statistics: `pages_scanned`, `candidates`, `inserted`, `updated`, `unchanged`, `errors`

## Rate Limiting
- 0.5 second delay between detail fetches (`getProductData`)
- Respects clan.com API rate limits

## Hash Calculation
Content hash includes:
- `name` (title)
- `sku`
- `price`
- `image_url`
- `url`
- `short_description`
- `description`
- `supplier_name`
- `supplier_description`
- `configurable_options`

Hash is SHA-256 of JSON-sorted field payload.

## Error Handling
- Failed detail fetches fall back to basic product data
- Individual product errors don't stop the sync
- All errors logged and counted in `errors` counter

## Status Tracking
Real-time status available via `GET /api/clan/cache/sync/status`:
- `running`: Boolean
- `started_at`: ISO timestamp
- `finished_at`: ISO timestamp (null if running)
- `pages_scanned`: Current page count
- `candidates`: Total candidates found
- `inserted`, `updated`, `unchanged`, `errors`: Counters







