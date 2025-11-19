# Newsletter Products Blocks

## Overview

Two product-related blocks: **New Products** and **Spotlight Product**.

**Status**: ✅ Implemented

## New Products Block

Shows recently added products (last 6).

**Data Sources**: `product` table, filtered by `created_at` and `is_published=True`

**Payload Structure**:
```json
{
  "items": [
    {
      "id": 123,
      "name": "Product name",
      "slug": "product-slug",
      "image_url": "...",
      "short_description": "..."
    }
  ]
}
```

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

## Files

- `blog-core/newsletter/selectors/products.py` - Product selection logic
  - `select_new_products()` - Recent products
  - `select_spotlight_product()` - Featured product
  - `group_variants()` - Groups product variants

## API Endpoints

Same as intro block (shared endpoints).

