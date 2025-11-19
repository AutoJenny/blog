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
| `blog-core/newsletter/selectors/products.py` | ~400 | Product selection logic (pool management, random selection with category diversity) |
| `blog-core/newsletter/services/block_suggestion_service.py` | ~350 | Unified routing to type-specific logic (includes new_products pool management) |
| `blog-core/newsletter/services/products_intro_service.py` | ~115 | LLM service for generating intro paragraph |
| `blog-core/newsletter/services/product_tracking.py` | ~60 | Service for tracking product launches (`newsletter_launched_at`) |
| `blog-core/newsletter/services/block_editor_service.py` | ~240 | Handles product selection and payload updates |
| `templates/newsletter/partials/new_products.html` | ~40 | Email template for rendering products spotlight block |
| `templates/newsletter/partials/block_editor_new_products.html` | ~200 | Custom editor UI with product selection and intro generation |
| `templates/newsletter/partials/block_editor_base.html` | ~85 | Common wrapper for all block editors |

**Note**: The products spotlight block has a custom editor UI for product selection, re-choosing, and intro generation.

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

### Product Pool & Selection Strategy

**Product Pool Management**:
- `get_product_pool()`: Fetches up to 50 recent products from `clan_products` table
  - First tries to exclude products with `newsletter_launched_at IS NOT NULL`
  - If pool is too small (< 10 products), includes launched products to fill pool
  - Ensures sufficient options for re-choosing without running out
  - Pool is stored in block payload for persistence across re-chooses

**Random Selection with Category Diversity**:
- `select_random_from_pool()`: Randomly selects 3 products from pool
  - Ensures products come from different specific categories (skips generic category ID 12)
  - Shuffles pool for randomness
  - First pass: Selects one product from each unique category
  - Second pass: Fills remaining slots with any products if needed
  - Prevents showing similar products (e.g., multiple backpacks or mouse mats)

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

#### 1. Selector: `selectors/products.py` (~400 lines)

**Location**: `blog-core/newsletter/selectors/products.py`

**Main Functions**:

**`get_product_pool(*, since_iso_timestamp: str, pool_size: int = 50, exclude_launched: bool = True, min_product_id: int = 10000) -> List[Dict[str, Any]]`**
- Fetches up to `pool_size` recent products from `clan_products` table
- Filters by `first_seen_at > since_iso_timestamp` (default: last 60 days)
- Excludes products with `id <= min_product_id` (filters out older products)
- If `exclude_launched=True`, excludes products with `newsletter_launched_at IS NOT NULL`
- Validates image URLs (must be non-empty and start with `http://` or `https://`)
- Deduplicates by product name
- Returns list of product dicts with: `id`, `name`, `sku`, `image_url`, `url`, `short_description`, `category_ids`

**`select_random_from_pool(*, pool: List[Dict[str, Any]], limit: int = 3) -> List[Dict[str, Any]]`**
- Randomly selects `limit` products from pool
- Ensures category diversity by selecting products from different specific categories
- Skips generic category ID 12 ("CLAN Main Category") for diversity
- Shuffles pool first for randomness
- Returns 3 diverse products

**`select_spotlight_product() -> Dict[str, Any]`**
- Returns single most recently updated published product
- Used by spotlight block (not products spotlight)

#### 2. Suggestion Service: `services/block_suggestion_service.py`

**Function**: `get_suggestions_for_block(block_type='new_products', ...)`

**Process**:
1. Checks if existing `product_pool` exists in any `new_products` block for this issue (pools are shared per issue)
2. If no pool exists or pool is empty:
   - Calculates `since_date` (60 days ago)
   - Calls `get_product_pool(since_iso_timestamp=since_date, pool_size=50, exclude_launched=True, min_product_id=10000)`
   - If pool has < 10 products, includes launched products to fill pool
3. Calls `select_random_from_pool(pool=product_pool, limit=3)` to get 3 diverse products
4. Formats as suggestions with: `id`, `name`, `sku`, `image_url`, `url`, `short_description`, `category_ids`, `type: 'product'`
5. Returns:
   ```python
   {
       'suggestions': [...],  # List of 3 randomly selected products
       'current': {'items': current_items},  # Current selection from payload (if exists)
       'metadata': {'count': 3, 'pool_size': len(product_pool)},
       '_product_pool': product_pool  # Pool stored in payload for future re-chooses
   }
   ```

**Note**: Products are NOT marked as launched when selected. They are only marked when user clicks "Confirm Selection & Generate Intro".

#### 3. Intro Service: `services/products_intro_service.py` (~115 lines)

**Function**: `generate_products_intro(products: List[Dict[str, Any]]) -> str`

**Process**:
1. Takes list of 3 product dicts with `name`, `short_description`, `sku`
2. Builds product descriptions for LLM prompt
3. Uses LLM (Ollama llama3.2:latest) to generate brief intro paragraph
4. Requirements:
   - 2-3 sentences, maximum 75 words total
   - Mentions products are recently added to website
   - Comments briefly on products based on descriptions
   - Conversational, warm tone
5. Returns generated intro paragraph (with fallback if LLM fails)

#### 4. Tracking Service: `services/product_tracking.py` (~60 lines)

**Functions**:
- `mark_products_newsletter_launched(product_ids: List[int])`: Sets `newsletter_launched_at = CURRENT_TIMESTAMP` for products
- `extract_product_ids_from_payload(payload: Dict, block_type: str) -> List[int]`: Extracts product IDs from block payload
- `mark_product_blog_profiled(product_id: int)`: Sets `blog_profiled_at` timestamp (for blog posts, not newsletters)

#### 5. Editor Template: `templates/newsletter/partials/block_editor_new_products.html` (~200 lines)

**Features**:
- Displays current selection with product thumbnails, names, and SKUs
- "Re-choose Products" button: Randomly selects 3 new products from pool
- "Confirm Selection & Generate Intro" button:
  - Generates intro paragraph via LLM
  - Saves intro to block payload
  - Marks products as launched in database
  - Updates button to show "Confirmed" state
- Preview of generated intro paragraph
- Manual override section (collapsible JSON editor)

**JavaScript Functions**:
- `rechooseProducts(blockId, issueId)`: Fetches new suggestions and applies them
- `confirmProducts(blockId, issueId)`: Generates intro and confirms selection
- `loadProductsPreview(blockId, issueId)`: Loads current selection for display

#### 6. Preview Template: `templates/newsletter/partials/new_products.html` (~40 lines)

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

### User Workflow

1. **Initial Selection / Re-choose Products**
   - User clicks "Re-choose Products" button
   - JavaScript calls `rechooseProducts(blockId, issueId)`
   - Fetches from `/newsletter/issue/{issueId}/block/{blockId}/suggestions`
   - Backend: `get_suggestions_for_block()` → `get_product_pool()` → `select_random_from_pool()`
   - Returns 3 randomly selected products with category diversity
   - Products displayed in preview grid (thumbnails, names, SKUs)
   - Products stored in block payload with `product_pool` for future re-chooses
   - **Products are NOT marked as launched yet**

2. **Confirm Selection & Generate Intro**
   - User clicks "Confirm Selection & Generate Intro" button
   - JavaScript calls `confirmProducts(blockId, issueId)`
   - First: Fetches from `/newsletter/issue/{issueId}/block/{blockId}/generate-products-intro`
     - Backend: `products_intro_service.generate_products_intro()` → LLM generates paragraph
   - Second: Posts to `/newsletter/issue/{issueId}/block/{blockId}/confirm-products`
     - Backend: Saves intro to block payload
     - Backend: `product_tracking.mark_products_newsletter_launched()` → Sets `newsletter_launched_at` timestamp
   - Intro displayed in preview box
   - Button updates to "Confirmed" state

3. **Preview Display**
   - Intro paragraph shown above products (if generated)
   - 3 products displayed in grid (image, name, Explore button)
   - SKU not shown in preview (only in editor)

### Current Features

1. **Product Pool Management**: Up to 50 recent products stored in block payload
   - Enables consistent random selection without running out of options
   - Pool shared per issue to avoid duplicates across blocks

2. **Category Diversity**: Ensures selected products come from different categories
   - Skips generic "CLAN Main Category" (ID 12) for better diversity
   - Prevents showing similar products (e.g., multiple backpacks)

3. **LLM-Generated Intro**: Brief paragraph mentioning products are recently added
   - Generated when user confirms selection
   - 2-3 sentences, ~50-75 words
   - Conversational tone

4. **Product Tracking**: Products marked as launched when confirmed
   - `newsletter_launched_at` timestamp set in `clan_products` table
   - Prevents same products from appearing in future newsletters

5. **Custom Editor UI**: Dedicated interface for product selection
   - Visual preview with thumbnails
   - Re-choose functionality
   - Intro generation and preview

### Future Enhancements

1. **Manual Product Selection**: Could add product picker with search/filter
2. **Configurable Pool Size**: Could allow customization of pool size (currently 50)
3. **Configurable Time Range**: Could allow configuration for "last 7 days", "last 30 days", etc.
4. **Product Details**: Could add price, full description, or other metadata to display

### Database Schema

**clan_products Table** (synced from clan.com API):
```sql
CREATE TABLE clan_products (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255),
    sku VARCHAR(255),
    image_url VARCHAR(500),
    url VARCHAR(500),              -- Full clan.com URL
    short_description TEXT,
    description TEXT,
    price DECIMAL(10,2),
    first_seen_at TIMESTAMPTZ,     -- When product was first synced
    clan_created_at TIMESTAMPTZ,   -- Creation date from clan.com API
    clan_updated_at TIMESTAMPTZ,   -- Update date from clan.com API (not yet available)
    newsletter_launched_at TIMESTAMPTZ,  -- When product was launched in newsletter
    blog_profiled_at TIMESTAMPTZ,  -- When product was profiled in blog post
    category_ids JSONB,            -- Array of category IDs
    last_updated TIMESTAMPTZ,
    product_content_hash TEXT,
    has_detailed_data BOOLEAN
);
```

**Key Fields**:
- `first_seen_at`: Used to identify recently added products (last 60 days)
- `newsletter_launched_at`: Tracks which products have been featured in newsletters
- `category_ids`: JSON array of category IDs for diversity filtering
- `id > 10000`: Filter to exclude older products

### Testing

To test the products spotlight block:

1. **Check for recent products**:
   ```sql
   SELECT id, name, sku, image_url, first_seen_at, newsletter_launched_at, category_ids
   FROM clan_products 
   WHERE first_seen_at > (CURRENT_TIMESTAMP - INTERVAL '60 days')
     AND id > 10000
     AND image_url IS NOT NULL
     AND image_url LIKE 'http%'
     AND newsletter_launched_at IS NULL
   ORDER BY first_seen_at DESC 
   LIMIT 50;
   ```

2. **Verify product pool**:
   - Check that pool contains up to 50 products
   - Verify products have valid image URLs
   - Check that `category_ids` are populated

3. **Test Editor UI**:
   - Navigate to `/newsletter/issue/8`
   - Find "New Products Spotlight" block (should be 3rd section)
   - Click "Re-choose Products"
   - Verify 3 products appear in preview grid
   - Check that products come from different categories
   - Click "Confirm Selection & Generate Intro"
   - Verify intro paragraph is generated and displayed
   - Check that products are marked as launched:
     ```sql
     SELECT id, name, newsletter_launched_at 
     FROM clan_products 
     WHERE id IN (product_ids_from_payload);
     ```

4. **Test Preview**:
   - Navigate to `/newsletter/issue/8/preview`
   - Verify "New Products Spotlight" section appears
   - Check that intro paragraph displays above products (if generated)
   - Verify products display in 3-column layout
   - Check that images, names, and Explore buttons render correctly
   - Verify SKU is NOT displayed in preview

5. **Test Re-choose Functionality**:
   - After confirming products, click "Re-choose Products" again
   - Verify new random selection from pool
   - Check that previously launched products are excluded (if pool is large enough)
   - Verify category diversity is maintained

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
