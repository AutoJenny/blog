# CSV-Based Product Sync

## Overview
The most efficient method for keeping the database in sync with clan.com is to compare product IDs from a CSV export with the local database, then fetch missing products via API.

## Why CSV Sync?

The clan.com API has limitations:
- **No ID range filtering**: Cannot request "products with ID > X"
- **No date filtering**: Cannot request "products created after Y"
- **Unreliable sorting**: `sort=id_desc` doesn't reliably return newest products first
- **Pagination overhead**: Finding new products requires scanning many pages

**CSV export advantages:**
- Complete product list with IDs and SKUs
- Fast comparison: O(n) set operations
- One-time API calls only for missing products
- Works regardless of ID gaps (configurable products)

## Process

### Step 1: Get CSV Export
Export enabled products from clan.com admin panel:
- Format: CSV with columns: `ID`, `SKU`, `Name`, `Status`, etc.
- Location: Save to `/data/products.csv` or similar

### Step 2: Compare IDs
```python
import csv
import psycopg

# Read CSV IDs
csv_ids = set()
with open('data/products.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        csv_ids.add(int(row['ID']))

# Get DB IDs
conn = psycopg.connect(...)
cur = conn.cursor()
cur.execute("SELECT id FROM clan_products")
db_ids = {r[0] for r in cur.fetchall()}

# Find missing
missing_ids = csv_ids - db_ids
```

### Step 3: Extract SKUs for Missing Products
```python
missing_skus = []
with open('data/products.csv', 'r') as f:
    reader = csv.DictReader(f)
    for row in reader:
        if int(row['ID']) in missing_ids:
            sku = row['SKU'].strip()
            if sku:
                missing_skus.append((int(row['ID']), sku, row['Name']))
```

### Step 4: Fetch and Store Missing Products
For each missing SKU:
1. Call `getProductData(sku, all_images=False)` via API
2. Transform and enrich with extended fields
3. Store via `store_single_product()` method
4. Rate limit: 0.5s delay between calls

## Implementation Script

A complete implementation script is available that:
- Reads CSV and identifies missing products
- Fetches full product details via API
- Stores with all extended fields (supplier, options, descriptions)
- Reports success/failure counts
- Handles errors gracefully

See the sync process used in November 2025 for reference.

## When to Use

**Use CSV sync when:**
- Initial database setup
- Bulk catch-up after missed updates
- Monthly/quarterly full reconciliation
- After manual product deletions in admin panel

**Use weekly API sync when:**
- Regular incremental updates (weekly)
- Automatic discovery via blog post creation trigger
- Real-time new product detection

## Notes

- **Disabled products**: Products in CSV with `Status=Disabled` should be excluded from sync
- **Missing SKUs**: Products without SKUs in CSV cannot be fetched via API (e.g., ID 118876 "Fabric Length")
- **Deleted products**: Products in DB but not in CSV are likely disabled/deleted; can be removed from cache
- **ID gaps**: Configurable products create large ID gaps (1800+ IDs per product); CSV handles this naturally









