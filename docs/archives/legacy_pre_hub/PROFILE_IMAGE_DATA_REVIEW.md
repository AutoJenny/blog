# Profile Image Data Review

**Date:** 2025-01-XX  
**Purpose:** Review available image data for products to inform profile image generation template design.

---

## Image Data Available for Products

### 1. **Stored in Database (`clan_products` table)**

**Field:** `image_url` (TEXT)
- **Type:** Single URL string
- **Content:** Main product image URL from clan.com
- **Example:** `https://static.clan.com/media/catalog/product/.../image.jpg`
- **Availability:** Always available (if product exists)
- **Storage:** Persisted in database

### 2. **Available via API (On-Demand, Not Stored)**

**Endpoint:** `GET /api/clan/products/<sku>/full?all_images=true`

**Response Structure:**
```json
{
  "success": true,
  "product": {
    "id": 919,
    "sku": "sr_wilkn_melrose_vn",
    "name": "Luxury Scottish Cashmere Sweater, V‑Neck",
    "image_url": "https://static.clan.com/...",  // Main image (also in DB)
    "all_images": [  // Complete gallery (API only, not stored)
      {
        "url": "https://static.clan.com/media/catalog/product/.../image1.jpg",
        "alt": "Main product image"
      },
      {
        "url": "https://static.clan.com/media/catalog/product/.../image2.jpg",
        "alt": "Detail view"
      },
      {
        "url": "https://static.clan.com/media/catalog/product/.../image3.jpg",
        "alt": "Side view"
      }
      // ... additional images ...
    ]
  }
}
```

**Image Array Structure:**
- **Type:** Array of objects
- **Each Object:**
  - `url` (string): Full image URL
  - `alt` (string): Alt text/description
- **Availability:** Only when `?all_images=true` parameter is used
- **Storage:** Not stored in database (fetched on-demand to keep DB lean)

---

## Current Usage Patterns

### Standard Enrichment
- Uses `all_images=false` to minimize API load
- Only stores main `image_url` in database
- Fast, efficient for bulk operations

### Profile Writing (Recommended)
- Use `GET /api/clan/products/<sku>/full?all_images=true`
- Fetches complete image gallery on-demand
- Access full `configurable_options` for variant details
- All data fetched on-demand, doesn't bloat database

---

## Implications for Profile Image Generation Template

### Available Image Data:
1. **Main Image:** Always available from `clan_products.image_url`
2. **Image Gallery:** Available via API call with `all_images=true`
3. **Image Metadata:** Each image has `url` and `alt` text

### Design Considerations:

1. **Initial Load:**
   - Can display main image immediately (from DB)
   - Fetch full gallery on-demand when needed

2. **Image Selection:**
   - User can browse all available product images
   - Images have alt text for context
   - Can select which images to use for blog post sections

3. **Image Generation:**
   - May want to use existing product images as reference
   - May want to generate new images based on product data
   - May want to combine both approaches

4. **Section-Specific Images:**
   - Different sections may need different images
   - Hero section: Main product image
   - Gallery section: Multiple product images
   - Detail sections: Specific product views

---

## Recommended Template Structure

### Data Loading:
1. **On Page Load:**
   - Fetch product data (including main `image_url` from DB)
   - Display main image immediately
   - Optionally fetch full gallery in background

2. **On Demand:**
   - Button to "Load All Images" if gallery not loaded
   - Fetch via `/api/clan/products/<sku>/full?all_images=true`

### Image Display:
1. **Main Image Preview:**
   - Show main product image
   - Display product name and basic info

2. **Image Gallery:**
   - Grid/list of all available images
   - Show alt text for each image
   - Allow selection of images for different sections

3. **Section Mapping:**
   - Map images to blog post sections
   - Hero section → Main image
   - Gallery section → Multiple selected images
   - Detail sections → Specific images

### Image Generation Options:
1. **Use Existing Images:**
   - Select from product gallery
   - Use as-is or with modifications

2. **Generate New Images:**
   - Use product data to generate images
   - Reference existing images for style/context

3. **Hybrid Approach:**
   - Use existing images where appropriate
   - Generate new images for specific needs

---

## Next Steps

1. **Template Design:**
   - Create UI for displaying product images
   - Add image selection interface
   - Add section-to-image mapping

2. **API Integration:**
   - Create endpoint to fetch product images for profile posts
   - Integrate with existing image generation system

3. **Image Management:**
   - Decide how to handle image selection
   - Decide how to store image-to-section mappings
   - Consider image optimization workflow

