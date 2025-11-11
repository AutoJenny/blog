# Database Schema

## Tables

### `clan_products`

Primary table storing product catalog data from clan.com.

#### Columns

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Product ID from clan.com |
| `sku` | TEXT | UNIQUE, NOT NULL | Product SKU (unique identifier) |
| `name` | TEXT | NOT NULL | Product title/name |
| `price` | DECIMAL(10,2) | | Product price |
| `image_url` | TEXT | | Main product image URL |
| `url` | TEXT | | Product page URL on clan.com |
| `short_description` | TEXT | | Brief product description (from extended API) |
| `description` | TEXT | | Full product description (HTML) |
| `supplier_name` | TEXT | | Manufacturer/supplier name |
| `supplier_description` | TEXT | | HTML supplier information |
| `clan_created_at` | TIMESTAMP | | Product creation date from clan.com API |
| `clan_updated_at` | TIMESTAMP | | Product update date from clan.com (when available) |
| `configurable_options` | JSONB | | Product options (sizes, colors, etc.) as JSON array |
| `additional_data` | JSONB | | Structured product attributes from CLAN API (material, pattern, shirt style, clan crest info, etc.) |
| `dimensions` | TEXT | | Product dimensions when available from CLAN API |
| `product_content_hash` | TEXT | | SHA-256 hash of product content fields (for change detection) |
| `category_ids` | JSONB | | Array of category IDs this product belongs to |
| `first_seen_at` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | When product was first discovered in our system (never updated) |
| `last_updated` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last time product record was modified |
| `has_detailed_data` | BOOLEAN | DEFAULT TRUE | Whether extended fields (supplier, options) have been fetched |

#### Indexes
- Primary key on `id`
- Unique index on `sku`

#### Key Behaviors

1. **Upsert Logic**: Uses `ON CONFLICT (id) DO UPDATE` to handle inserts and updates
2. **first_seen_at Preservation**: `first_seen_at` is set only on initial insert, never updated
3. **Hash-Based Change Detection**: `product_content_hash` is computed from name, sku, price, image_url, url, descriptions, supplier fields, and options
4. **Timestamp Fields**:
   - `clan_created_at` / `clan_updated_at`: From clan.com API
   - `first_seen_at`: When we first discovered the product
   - `last_updated`: When our record was last modified

### `clan_categories`

Category hierarchy from clan.com.

#### Columns

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | INTEGER | PRIMARY KEY | Category ID from clan.com |
| `name` | TEXT | NOT NULL | Category name |
| `description` | TEXT | | Category description |
| `level` | INTEGER | DEFAULT 0 | Hierarchy level (0 = root) |
| `parent_id` | INTEGER | | Parent category ID (NULL for root) |
| `last_updated` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last update time |

#### Notes
- Categories are upserted (not bulk-replaced) to preserve existing data
- Hierarchy supports multi-level category trees

### `clan_cache_metadata`

Key-value metadata for cache management.

#### Columns

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `key` | TEXT | PRIMARY KEY | Metadata key |
| `value` | TEXT | | Metadata value (often JSON or timestamp) |
| `last_updated` | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | Last update time |

#### Common Keys
- `list_last_successful_sync_at`: ISO timestamp of last successful weekly sync

## Migration Notes

### New Columns Added

**October 2025:**
- `short_description`
- `supplier_name`
- `supplier_description`
- `clan_created_at`
- `clan_updated_at`
- `configurable_options`
- `product_content_hash`
- `first_seen_at`
- `has_detailed_data`

**November 2025:**
- `additional_data` - Structured product attributes (material, pattern, shirt style, clan crest info, etc.)
- `dimensions` - Product dimensions

All new columns are added with `ADD COLUMN IF NOT EXISTS` to support existing installations without breaking migrations.

### Data Integrity

- **SKU Uniqueness**: Enforced by UNIQUE constraint on `sku`
- **ID Consistency**: `id` (clan.com product ID) is primary key, ensuring one record per product
- **Hash Consistency**: Hash is recomputed on every upsert to reflect current product content





