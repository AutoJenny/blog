# Product Enrichment

## Overview
Enrichment fetches extended product data (supplier info, options, descriptions) from clan.com API. This can be done:
1. Automatically during weekly sync (for candidates)
2. On-demand for individual SKUs when needed
3. Dynamically merged for profile writing (read-only)

## Single SKU Enrichment

### Endpoint
`POST /api/clan/cache/enrich`

### Request Body
```json
{
  "sku": "sr_wilkn_melrose_vn"
}
```

### Process
1. Fetches `getProductData(sku, all_images=False)` from clan.com
2. Maps extended fields to product record:
   - `short_description`
   - `supplier_name`
   - `supplier_description`
   - `configurable_options` (full JSON structure)
   - `clan_created_at`
   - `clan_updated_at` (if available)
3. Computes content hash
4. Upserts to database (updates if exists, preserves `first_seen_at`)

### Response
```json
{
  "success": true,
  "sku": "sr_wilkn_melrose_vn"
}
```

### Use Cases
- Manually refreshing a specific product
- Enriching products discovered in weekly sync but missed during enrichment phase
- Updating product after clan.com data changes

## On-Demand Full Product Detail

### Endpoint
`GET /api/clan/products/<sku>/full?all_images=true`

**Parameters:**
- `all_images` (optional): Set to `true` to fetch all product images (for profile writing). Default: `false`.

### Process
1. Reads product from database (if exists)
2. Fetches live data from `getProductData` (does not persist)
   - If `all_images=true`, fetches complete image gallery
3. Merges: database fields as base, live API data as overlay
4. Returns merged result

### Response (Standard)
```json
{
  "success": true,
  "product": {
    "id": 919,
    "sku": "sr_wilkn_melrose_vn",
    "name": "Luxury Scottish Cashmere Sweater, V‑Neck",
    "price": "315",
    "image_url": "https://static.clan.com/...",
    "short_description": "Comfort woven in style...",
    "description": "<ul>...</ul>",
    "supplier_name": "William Lockie Knitwear",
    "supplier_description": "<p>Ever since...</p>",
    "configurable_options": [
      {
        "option": "Chest",
        "options": [{"label": "XS: 40\""}, ...]
      },
      {
        "option": "Colour",
        "options": [{"label": "Black"}, ...]
      }
    ],
    "first_seen_at": "2025-09-20T08:50:37Z",
    "last_updated": "2025-11-03T10:30:00Z"
  }
}
```

### Response (With All Images)
When `?all_images=true`:
```json
{
  "success": true,
  "product": {
    // ... all standard fields ...
    "all_images": [
      {
        "url": "https://static.clan.com/media/catalog/product/.../image1.jpg",
        "alt": "Main product image"
      },
      {
        "url": "https://static.clan.com/media/catalog/product/.../image2.jpg",
        "alt": "Detail view"
      }
      // ... additional images ...
    ]
  }
}
```

### Use Cases
- **Product Profile Writing**: 
  - Use `?all_images=true` to get complete image gallery for visual content
  - Access full `configurable_options` for variant details (sizes, colors, etc.)
  - Get latest supplier descriptions and product details
  - All data fetched on-demand, doesn't bloat database
- **Real-time Preview**: See latest data from clan.com without triggering database updates
- **Editor Tools**: Display complete product information for content generation

### Example: Fetching Full Product Data for Profile Writing
```bash
# Standard fetch (main image only)
curl "http://localhost:5000/api/clan/products/sr_wilkn_melrose_vn/full"

# Full fetch with all images (for profile writing)
curl "http://localhost:5000/api/clan/products/sr_wilkn_melrose_vn/full?all_images=true"
```

## Extended Fields Available

When enrichment occurs (via sync or manual), these fields become available:

- `short_description`: Brief product description
- `supplier_name`: Manufacturer/supplier name
- `supplier_description`: HTML supplier information
- `configurable_options`: Array of product options (sizes, colors, etc.)
  - Structure: `[{"option": "Size", "options": [{"label": "S"}, {"label": "M"}]}]`
- `clan_created_at`: Product creation date from clan.com
- `clan_updated_at`: Product update date (when available from API)

## Notes

- **Images**: 
  - Standard enrichment uses `all_images=false` to minimize API load (stores main `image_url` only)
  - For profile writing, use `GET /api/clan/products/<sku>/full?all_images=true` to fetch complete image gallery on-demand
  - Image gallery is returned but not stored in database (keeps DB lean)
- **Options Storage**: Currently stored as JSONB for convenience. Full `configurable_options` structure available via enrichment endpoints.
- **Hash Preservation**: Enrichment updates the content hash, allowing future change detection to work correctly.
- **Profile Writing Best Practice**: Use `/full?all_images=true` endpoint when writing product profiles to get all images and complete option details without storing them permanently.

