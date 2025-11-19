# Newsletter Products Blocks

## Overview

Two product-related blocks: **Products Spotlight** (formerly New Products) and **Spotlight Product**.

**Status**: ✅ Implemented

**File Size Compliance**: All files under 500 lines ✅

## Products Spotlight Block (new_products)

**Purpose**: Display recently added products from the catalog, grouped by variant to avoid duplication

**Display Name**: "New Products Spotlight" (renamed from "Products Spotlight")

**Position**: Typically 3rd section (position 2) in newsletter

### Code Organization

| File | Lines | Purpose |
|------|-------|---------|
| `blog-core/newsletter/selectors/products.py` | 110 | Product selection logic (new products, spotlight, variant grouping) |
| `blog-core/newsletter/services/block_suggestion_service.py` | 227 | Unified routing to type-specific logic (includes new_products handling) |
| `templates/newsletter/partials/new_products.html` | 33 | Email template for rendering products spotlight block |
| `templates/newsletter/partials/block_editor_base.html` | 81 | Common wrapper for all block editors (new_products uses universal editor) |

**Note**: The products spotlight block now has a custom editor UI for product selection and intro generation.

### Data Sources

- `clan_products` table from PostgreSQL (synced from clan.com API)
- Filters:
  - `first_seen_at > since_iso_timestamp` (default: last 60 days)
  - `id > 10000` (excludes older products)
  - `newsletter_launched_at IS NULL` (excludes already launched products)
  - Must have valid image URL: `image_url IS NOT NULL AND image_url LIKE 'http%'`
- Ordering: `first_seen_at DESC` (newest first)
- Product Pool: Up to 50 recent products stored in block payload for consistent random selection
- Selection: 3 products randomly selected from pool, ensuring category diversity

### Variant Grouping

The `group_variants()` function groups product variants by parent to avoid showing duplicate products:
- Looks for `parent_id` or `variant_parent_id` field
- Groups variants under their parent product
- Returns only parent products in the final list
- Tracks number of hidden variants (not currently displayed)

### Payload Structure

The products spotlight block payload is stored in `newsletter_block.payload_json`:

```json
{
  "items": [
    {
      "id": 123,
      "name": "Product Name",
      "sku": "product-sku",
      "image_url": "https://static.clan.com/...",
      "url": "https://clan.com/product-url",
      "short_description": "Product description text",
      "category_ids": [45, 67]
    }
  ],
  "product_pool": [...],
  "intro": "LLM-generated intro paragraph mentioning products are recently added"
}
```

**Fields**:
- `items`: Array of 3 selected product objects
- `product_pool`: Array of up to 50 recent products (for re-choosing)
- `intro`: LLM-generated intro paragraph (added when user confirms selection)
- Each product has:
  - `id`: Product ID (integer)
  - `name`: Product name (string)
  - `sku`: Product SKU (string)
  - `image_url`: Product image URL (string, full URL)
  - `url`: Product URL (string, full clan.com URL)
  - `short_description`: Product description (string, optional)
  - `category_ids`: Array of category IDs (for diversity filtering)

### File Details

#### 1. Selector: `selectors/products.py` (110 lines)

**Location**: `blog-core/newsletter/selectors/products.py`

**Main Functions**:

**`select_new_products(since_iso_timestamp: str, limit: int = 6) -> List[Dict[str, Any]]`**
- Queries `product` table for products created after the given timestamp
- Returns published products with images, ordered by creation date (newest first)
- Defensive error handling: returns empty list on any failure
- Uses `COALESCE` to handle schema variations (name/title, slug/url, image_url/hero_image)

**`group_variants(items: List[Dict[str, Any]]) -> Tuple[List[Dict[str, Any]], int]`**
- Groups product variants by parent ID
- Detects parent key: `parent_id` or `variant_parent_id`
- Returns tuple: (grouped parent products, number of hidden variants)
- If no parent key found, returns items unchanged

**`select_spotlight_product() -> Dict[str, Any]`**
- Returns single most recently updated published product
- Used by spotlight block (not products spotlight)

#### 2. Suggestion Service: `services/block_suggestion_service.py`

**Function**: `get_suggestions_for_block(block_type='new_products', ...)`

**Process**:
1. Gets today's date as ISO timestamp: `f"{date.today().isoformat()}T00:00:00Z"`
2. Calls `select_new_products(since_iso_timestamp=since_date, limit=12)`
3. Groups variants using `group_variants(products)`
4. Takes first 6 products from grouped list
5. Formats as suggestions with: `id`, `title` (from item's `title` field, may be empty if product uses `name`), `url` (from item's `url` field, may be empty if product uses `slug`), `price`, `type: 'product'`
   
   **Note**: The suggestion format uses `title`/`url` fields, but products from the selector use `name`/`slug`. The actual payload stored uses `name`/`slug` from the grouped products.
6. Returns:
   ```python
   {
       'suggestions': [...],  # List of 6 product suggestions
       'current': {'items': grouped[:6]},  # Current selection (auto-selected)
       'metadata': {'count': len(grouped)}  # Number of products found
   }
   ```

**Auto-Select**: `auto_select_for_block(block_type='new_products', ...)`
- Returns `{'items': result.get('suggestions', [])[:6]}`
- Automatically selects top 6 products

#### 3. Template: `templates/newsletter/partials/new_products.html` (33 lines)

**Rendering**:
- Displays products in a 3-column table layout (33.33% width each)
- Each product shows:
  - Product image (160px max width, rounded corners, centered)
  - Product name (bold, dark brown `#3d2817`, 14px font)
  - "Explore" link (if slug exists, brown color `#6b4e3d`)
- Heading: "New Products Spotlight" (18px, bold, dark brown)
- Intro paragraph (if generated): Displayed above products, mentions they're recently added
- Wrapped in cream panel (`#fef9e7`) with rounded corners
- Uses email-safe HTML (table-based layout, inline styles)
- Explore button: Styled as brown button (smaller than "Read more" button)

**Conditional Rendering**:
- Only renders if `block.items` exists and is not empty
- Each product cell only shows image if `p.image_url` exists
- Intro paragraph only shows if `block.intro` exists
- Explore button only shows if `p.url` exists
- SKU is NOT displayed in preview (only in editor)

### API Endpoints

**Get Suggestions**:
```
GET /newsletter/issue/:issue_id/block/:block_id/suggestions
```

**Implementation**: 
`blueprints/newsletter.py::get_block_suggestions()` → 
`block_editor_service.get_suggestions()` → 
`block_suggestion_service.get_suggestions_for_block()` → 
`selectors/products.get_product_pool()` and `select_random_from_pool()`

**Apply Suggestion (Re-choose Products)**:
```
POST /newsletter/issue/:issue_id/block/:block_id/select-suggestion
Body: {"auto_select": true, "product_ids": [123, 456, 789]}
```

**Generate Intro**:
```
POST /newsletter/issue/:issue_id/block/:block_id/generate-products-intro
```

**Confirm Products (Generate Intro & Mark Launched)**:
```
POST /newsletter/issue/:issue_id/block/:block_id/confirm-products
Body: {"intro": "Generated intro paragraph"}
```

**Implementation**: 
- `blueprints/newsletter.py::select_block_suggestion()` → 
- `block_editor_service.apply_suggestion()` → 
- Updates `newsletter_block.payload_json` with product data and pool
- `blueprints/newsletter.py::confirm_products()` →
- Generates intro via `products_intro_service.generate_products_intro()`
- Marks products as launched via `product_tracking.mark_products_newsletter_launched()`

### Suggestion Flow

1. **User clicks "Regenerate Suggestions"**
   - JavaScript calls `loadSuggestions(blockId, 'new_products')`
   - Fetches from `/newsletter/issue/{issueId}/block/{blockId}/suggestions`

2. **Backend Processing**
   - `get_suggestions()` → `get_suggestions_for_block()` → `select_new_products()`
   - `select_new_products()` queries database for products created today
   - Groups variants to show only parent products
   - Returns up to 6 products formatted as suggestions

3. **UI Display**
   - JavaScript renders suggestions in list
   - Shows "Use This" button
   - User can apply suggestion or manually edit JSON

4. **Auto-Select Behavior**
   - When auto-select enabled, top 6 products are automatically selected
   - Product data stored in block payload as `{'items': [...]}`
   - No text generation needed (data is already formatted)

### Current Limitations

1. **Time Range**: Only shows products created "today" (since midnight)
   - Future: Could allow configuration for "last 7 days", "last 30 days", etc.

2. **No Custom Editor**: Uses universal JSON editor instead of custom UI
   - Future: Could create custom editor with product selection interface

3. **No Manual Selection**: No UI to manually pick specific products
   - Future: Could add product picker with search/filter

4. **URL Formatting**: Product links use slug directly
   - Future: Could format as full clan.com URLs if needed

5. **Fixed Limit**: Always shows exactly 6 products (or fewer if not enough available)
   - Future: Could allow configuration of number of products to display

6. **No Product Details**: Only shows name, image, and link
   - Future: Could add price, short description, or other product metadata

### Database Schema

**Product Table** (assumed structure):
```sql
CREATE TABLE product (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255),           -- or title
    slug VARCHAR(255),            -- or url
    image_url VARCHAR(500),       -- or hero_image
    short_description TEXT,
    created_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ,
    is_published BOOLEAN,
    parent_id INTEGER,            -- for variants
    variant_parent_id INTEGER     -- alternative variant key
);
```

**Note**: The selector uses `COALESCE` to handle schema variations, so it works with different field names.

### Testing

To test the products spotlight block:

1. **Check for products created today**:
   ```sql
   SELECT id, name, slug, image_url, created_at 
   FROM product 
   WHERE created_at > CURRENT_DATE 
     AND COALESCE(is_published, TRUE) = TRUE
     AND COALESCE(image_url, hero_image, '') <> ''
   ORDER BY created_at DESC 
   LIMIT 12;
   ```

2. **Verify variant grouping**:
   - Create test products with `parent_id` set
   - Verify only parent products appear in suggestions
   - Check that hidden variant count is tracked

3. **Test UI**:
   - Navigate to `/newsletter/issue/8`
   - Find "Products Spotlight" block (should be 3rd section)
   - Click "Regenerate Suggestions"
   - Verify products appear in suggestions list
   - Apply a suggestion and verify it appears in preview

4. **Test Preview**:
   - Navigate to `/newsletter/issue/8/preview`
   - Verify "Products Spotlight" section appears
   - Check that products display in 3-column layout
   - Verify images, names, and links render correctly

---

## Spotlight Product Block

Shows a single featured product.

**Data Sources**: Most recently updated published product from `product` table

**Payload Structure**:
```json
{
  "id": 123,
  "name": "Product name",
  "slug": "product-slug",
  "image_url": "...",
  "short_description": "..."
}
```

**Implementation**: Uses `select_spotlight_product()` from `selectors/products.py`
- Queries for most recently updated published product
- Returns single product dict (not array)
- See spotlight block documentation for full details
