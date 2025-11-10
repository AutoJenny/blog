# Product & Category Profiles - Quick Start Guide

## For New Developers

This guide provides a quick overview to get you started working with the Product & Category Profiles feature.

---

## What Are Profiles?

Profiles are weekly editorial blog features that explore Scottish heritage, craftsmanship, and culture through products and product categories. They are:

- **Editorial-first**: Rich narrative content with cultural/historical context
- **Commerce-linked**: Direct links to product pages and category pages
- **Weekly features**: Scheduled via calendar system (not daily posts)

**Two Types**:
1. **Product Profiles**: Focus on a specific product (e.g., "Lambswool Scarf by Lochcarron")
2. **Category Profiles**: Focus on a product category (e.g., "Scottish Wool Scarves")

---

## Quick Setup

### 1. Verify Database Migrations

All migrations should already be applied. To verify:

```bash
# Check if producers table exists
psql -d your_database -c "\d producers"

# Check if profile fields exist in post table
psql -d your_database -c "\d post" | grep profile
```

If migrations haven't been applied:

```bash
python3 scripts/apply_profile_migrations.py
python3 scripts/migrate_suppliers_to_producers.py
```

### 2. Test Profile Creation

1. Navigate to: `/planning/posts/<post_id>/calendar/week-view`
2. Find the "Profiles" row
3. Click "Add New"
4. Select "Product Profile"
5. Search for a product
6. Enter title and standfirst
7. Click "Save Profile"

The profile should appear in the calendar week view.

### 3. Test API Endpoints

```bash
# Get profiles for a week
curl http://localhost:5000/planning/api/calendar/profiles/2025/4

# Create a profile
curl -X POST http://localhost:5000/planning/api/profiles \
  -H "Content-Type: application/json" \
  -d '{
    "profile_type": "product",
    "title": "Test Profile",
    "profile_product_id": 1,
    "year": 2025,
    "week_number": 4
  }'
```

---

## Key Files to Know

### Backend

**API Routes**:
- `blueprints/planning_api_profiles.py` - Profile CRUD operations
- `blueprints/planning_api_calendar_profiles.py` - Calendar week profiles

**Data Tools**:
- `utils/product_specifications_scraper.py` - Scrape product specs
- `utils/producer_research.py` - Research producer info
- `utils/category_heritage_research.py` - Research category heritage
- `utils/representative_products_selector.py` - Select representative products

### Frontend

**Templates**:
- `templates/profiles/product_profile.html` - Product profile page
- `templates/profiles/category_profile.html` - Category profile page
- `templates/profiles/index.html` - Profile index
- `templates/planning/calendar/profile_modal.html` - Creation modal

**JavaScript**:
- `static/js/planning/profile-modal-core.js` - Profile modal logic
- `static/js/planning/calendar-week-view.js` - Calendar integration (extended)

**CSS**:
- `static/css/profiles.css` - Profile page styles
- `static/css/planning/profile-modal.css` - Modal styles

---

## Database Schema Quick Reference

### Key Tables

**`producers`**: Normalized producer information
```sql
SELECT * FROM producers;
```

**`post`**: Blog posts (profiles have `profile_type IS NOT NULL`)
```sql
SELECT * FROM post WHERE profile_type IS NOT NULL;
```

**`calendar_week_posts`**: Week scheduling
```sql
SELECT * FROM calendar_week_posts 
WHERE post_id IN (SELECT id FROM post WHERE profile_type IS NOT NULL);
```

---

## Common Tasks

### Create a Product Profile

1. Open calendar week view
2. Click "Add New" in Profiles row
3. Select "Product Profile"
4. Search and select product
5. Enter title and standfirst
6. Save

### Create a Category Profile

1. Open calendar week view
2. Click "Add New" in Profiles row
3. Select "Category Profile"
4. Select category from dropdown
5. Enter title and standfirst
6. Save

### Scrape Product Specifications

```python
from utils.product_specifications_scraper import ProductSpecificationsScraper

scraper = ProductSpecificationsScraper()
specs = scraper.scrape_product_specifications('https://clan.com/product-url')
```

Or via API:
```bash
curl -X POST http://localhost:5000/api/clan/products/SKU-001/scrape-specifications
```

### Select Representative Products

```python
from utils.representative_products_selector import RepresentativeProductsSelector
from config.database import db_manager

conn = db_manager.get_connection()
selector = RepresentativeProductsSelector(conn)
products = selector.select_representative_products(category_id=123, limit=8)
```

---

## Troubleshooting

### Profiles Not Appearing in Calendar

1. Check if profile has `profile_type` set:
   ```sql
   SELECT id, title, profile_type FROM post WHERE id = <profile_id>;
   ```

2. Check if profile is scheduled:
   ```sql
   SELECT * FROM calendar_week_posts WHERE post_id = <profile_id>;
   ```

3. Check browser console for JavaScript errors
4. Verify API endpoint is working:
   ```bash
   curl http://localhost:5000/planning/api/calendar/profiles/2025/4
   ```

### Modal Not Opening

1. Check if `profile-modal-core.js` is loaded
2. Check browser console for errors
3. Verify modal HTML is included in template
4. Check if `getProfileModal()` function exists

### Product Search Not Working

1. Check if `/api/clan/products` endpoint is accessible
2. Verify product data exists in `clan_products` table
3. Check browser network tab for API errors

---

## Next Steps

1. **Read Full Documentation**: See `PRODUCT_CATEGORY_PROFILES_DOCUMENTATION.md`
2. **Review Implementation Status**: See `implementation-status.md`
3. **Check Section Types**: See `section-types.md`
4. **Review Design Specs**: See `../product-category-profiles-design-layout.md`

---

## Getting Help

1. Check documentation in `docs/profiles/`
2. Review code comments in implementation files
3. Check database schema in migration files
4. Review API responses in browser network tab

---

**Last Updated**: 2025-01-27

