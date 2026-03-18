# Clan Products Integration - Overview

## Purpose
This system synchronizes product catalog data from clan.com API into a local PostgreSQL cache. It provides efficient weekly discovery of new products, hash-based change detection, and on-demand enrichment for product profile writing.

## Architecture

### Components
1. **Database Cache** (`blog-launchpad/clan_cache.py`)
   - PostgreSQL tables: `clan_products`, `clan_categories`, `clan_cache_metadata`
   - Provides storage and retrieval methods

2. **API Client** (`blog-clan-api/clan_client.py`)
   - Communicates with clan.com API
   - Handles getProducts (list) and getProductData (detail) endpoints

3. **Sync Workers** (`blueprints/clan_cache.py`)
   - Weekly discovery sync (runs automatically when triggered)
   - Background job management with status tracking

### Data Flow

```
User creates blog post
    ↓
Triggers weekly sync (non-blocking)
    ↓
Weekly sync worker:
    1. Discovers new/changed products via getProducts (id DESC, created_at filter)
    2. Enriches candidates with getProductData
    3. Compares content hash to detect changes
    4. Upserts only when new or changed
```

## Endpoints

### Sync Management
- `POST /api/clan/cache/sync/start` - Start weekly discovery sync (idempotent, gates on 7-day window)
- `GET /api/clan/cache/sync/status` - Get sync progress and statistics
- `POST /api/clan/cache/fetch-new-by-id` - Fetch products with IDs above current max (scans API pages)

### Product Enrichment
- `POST /api/clan/cache/enrich` - Enrich single SKU with extended data
- `GET /api/clan/products/<sku>/full` - Get merged DB + live detail (read-only, for profile writing)
  - Supports `?all_images=true` parameter to fetch all product images for profile writing

### Cache Management
- `GET /api/clan/cache/stats` - Cache statistics (counts, last updates)
- `POST /api/clan/cache/save-product` - Save single product (internal use)

## Schedule

**Weekly Sync Trigger**: Automatically triggered on blog post creation (Planning → Calendar → Create Post). The sync worker itself gates execution to once per 7 days (unless `force=true`).

**Manual Trigger**: Can be started via `/api/clan/cache/sync/start?force=true` to bypass the 7-day gate.

## Key Features

1. **Idempotent Sync**: Multiple triggers won't cause duplicate work
2. **Hash-Based Change Detection**: Only updates products when content actually changes
3. **first_seen_at Preservation**: Never overwrites when product was first discovered
4. **On-Demand Enrichment**: Extended fields (supplier, options) fetched only when needed
5. **Non-Blocking**: Sync runs in background, doesn't delay blog post creation

## Sync Methods

### 1. CSV-Based Sync (Recommended for Bulk Updates)
Compare product IDs from CSV export with database, then fetch missing products via API. Most efficient method for initial sync or catch-up.

**See**: [CSV Sync Guide](csv_sync.md)

### 2. Weekly API Sync (Automated)
Automated discovery triggered by blog post creation. Scans API pages to find new products. Gates execution to once per 7 days.

**See**: [Sync Flow](sync_flow.md)

### 3. ID-Based Fetch
Manual endpoint to fetch products with IDs above current max. Scans API pages (less efficient than CSV method).

**Endpoint**: `POST /api/clan/cache/fetch-new-by-id`

## Related Documentation

- [Schema Details](schema.md) - Database structure and field descriptions
- [Sync Flow](sync_flow.md) - Detailed weekly sync process
- [CSV Sync](csv_sync.md) - CSV-based bulk sync method (recommended)
- [Enrichment](enrichment.md) - Single-SKU enrichment and on-demand detail fetching

