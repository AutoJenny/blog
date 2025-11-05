# Implementation Thoughts: Product & Category Profiles

## Overview

This document provides technical recommendations for implementing the Product & Category Profiles feature based on the existing BlogForge CMS architecture.

## Current System Understanding

### Post Structure
- Posts are stored in the `post` table with fields: `id`, `title`, `slug`, `summary`, `status`, `header_image_id`, etc.
- Content is organized into `post_section` (sections) and `post_section_elements` (elements within sections)
- Posts have workflow stages managed through `post_workflow_stage` and `workflow_stage_entity`
- Tags are stored in `post_tags` table
- Categories via `post_categories` junction table

### Product/Category Data
- Products stored in `clan_products` table with fields: `id`, `sku`, `name`, `description`, `supplier_name`, `category_ids` (JSONB), etc.
- Categories in `clan_categories` table with hierarchy support (`parent_id`, `level`)
- Supplier/producer information available in `supplier_name` and `supplier_description` fields

### Newsletter Integration
- Newsletter issues stored in `newsletter_issue` table
- Blocks stored in `newsletter_block` with `type` field (feature, snapshot, category, etc.)
- Newsletter blocks support `payload_json` (JSONB) for flexible content storage
- Blocks have `suggested_items`, `auto_selected_item_id`, and `manual_override` fields

## Implementation Recommendations

### 1. Database Schema Extension

#### Option A: Extend Existing Post Table (Recommended)
**Pros:**
- Minimal schema changes
- Leverages existing post workflow
- Reuses existing section/element system
- No migration complexity

**Implementation:**
```sql
-- Add profile metadata columns to post table
ALTER TABLE post ADD COLUMN IF NOT EXISTS profile_type VARCHAR(20) CHECK (profile_type IN ('product', 'category', NULL));
ALTER TABLE post ADD COLUMN IF NOT EXISTS profile_product_id INTEGER REFERENCES clan_products(id) ON DELETE SET NULL;
ALTER TABLE post ADD COLUMN IF NOT EXISTS profile_category_id INTEGER REFERENCES clan_categories(id) ON DELETE SET NULL;
ALTER TABLE post ADD COLUMN IF NOT EXISTS profile_producer_name VARCHAR(255);
ALTER TABLE post ADD COLUMN IF NOT EXISTS profile_standfirst TEXT;
ALTER TABLE post ADD COLUMN IF NOT EXISTS profile_explore_links JSONB DEFAULT '{}';
```

**Note:** Profile-specific data (like representative examples, swatch panels) can be stored in `post_section` with custom section types or in JSONB fields.

#### Option B: Separate Profile Table
**Pros:**
- Cleaner separation of concerns
- Doesn't pollute main post table
- Easier to query profile-specific data

**Cons:**
- More complex joins
- Requires new workflow integration
- Migration overhead

**Recommendation:** Use Option A (extend post table) since profiles are fundamentally blog posts with specialized metadata.

### 2. Profile Type Identification

#### Tag-Based Approach (Recommended)
- Use existing `post_tags` system
- Add tags: `type:product-profile` or `type:category-profile`
- This allows filtering and querying without schema changes
- Can be combined with `profile_type` column for efficient queries

#### URL Pattern
- Product: `/blog/profiles/product/{slug}/`
- Category: `/blog/profiles/category/{slug}/`
- Index: `/blog/profiles/` with filters

**Implementation:**
```python
# In blueprints/core.py or new blueprints/profiles.py
@bp.route('/blog/profiles/')
@bp.route('/blog/profiles/<profile_type>/')
@bp.route('/blog/profiles/<profile_type>/<slug>/')
```

### 3. Content Structure

#### Leverage Existing Section System
The current `post_section` system is perfect for this:

**Product Profile Sections:**
1. `hero` - Hero block with image and standfirst
2. `the_object` - Product description
3. `the_maker` - Producer information
4. `in_context` - Cultural/seasonal context
5. `materials_making` - Materials and processes
6. `gallery` - Image gallery (4-6 images)
7. `explore_further` - CTA links
8. `credits` - Sources and attributions

**Category Profile Sections:**
1. `hero` - Hero block
2. `origins_history` - Historical overview
3. `materials_methods` - Materials and traditions
4. `cultural_meaning` - Cultural significance
5. `representative_examples` - Product grid (link to clan_products)
6. `swatch_panel` - Optional tartan swatch
7. `explore_further` - CTA links
8. `credits` - Sources

**Implementation:**
- Use existing `post_section` table with `section_type` field
- Store profile-specific metadata in `post_section_elements` JSONB or custom fields
- For representative examples, store array of product IDs in JSONB

### 4. Data Integration

#### Product Profile Data Pull
```python
# Pseudo-code for data integration
def get_product_profile_data(product_id, producer_name):
    # Pull from clan_products
    product = get_clan_product(product_id)
    
    # Extract producer info
    producer_info = {
        'name': product.supplier_name,
        'description': product.supplier_description,
        'products': get_products_by_supplier(producer_name)
    }
    
    # Get category context
    categories = get_categories_by_ids(product.category_ids)
    
    return {
        'product': product,
        'producer': producer_info,
        'categories': categories,
        'related_products': get_related_products(product_id)
    }
```

#### Category Profile Data Pull
```python
def get_category_profile_data(category_id):
    category = get_clan_category(category_id)
    
    # Get representative products (not all, just examples)
    example_products = get_representative_products(category_id, limit=8)
    
    # Get subcategories if applicable
    subcategories = get_subcategories(category_id)
    
    return {
        'category': category,
        'examples': example_products,
        'subcategories': subcategories
    }
```

### 5. Newsletter Integration

#### New Block Type: `profile`
Add to `newsletter_block_type` table:
```sql
INSERT INTO newsletter_block_type (type, description) 
VALUES ('profile', 'Weekly product or category profile feature');
```

#### Block Payload Structure
```json
{
  "profile_type": "product",  // or "category"
  "post_id": 123,
  "teaser": "Discover the heritage of Lochcarron scarves...",
  "image_url": "/images/profiles/lochcarron-scarf.jpg",
  "cta_text": "Read the full story",
  "cta_url": "/blog/profiles/product/lochcarron-lambswool-scarf/"
}
```

#### Weekly Automation
- Extend existing newsletter autodraft system
- Add profile selection logic to `newsletter/services/suggestion_service.py`
- Query for most recent profile post: `SELECT * FROM post WHERE profile_type IS NOT NULL AND status='published' ORDER BY created_at DESC LIMIT 1`

### 6. Template System

#### Reuse Existing Templates
- Extend `templates/post/` templates with profile-specific variants
- Create `templates/profiles/product_profile.html` and `templates/profiles/category_profile.html`
- Use template inheritance from base post template

#### Section Templates
- Create section-specific partials in `templates/profiles/sections/`
- Examples:
  - `_maker_section.html`
  - `_gallery_section.html`
  - `_explore_links.html`
  - `_representative_examples.html`

### 7. Workflow Integration

#### Add to Existing Workflow
- Profiles follow same workflow stages: Calendar → Planning → Authoring → Imaging → Header
- Add profile-specific prompts in `llm_prompts` table
- Create profile-specific workflow templates

#### Profile-Specific Workflow Steps
1. **Data Selection**: Choose product/category and producer
2. **Content Generation**: AI generates profile sections
3. **Data Enrichment**: Pull product/category data
4. **Image Selection**: Choose/generate hero and gallery images
5. **Link Validation**: Verify all explore links
6. **Publish**: Standard publish workflow

### 8. Producer Entity

#### Current State
- Producer information exists in `clan_products.supplier_name` and `supplier_description`
- No dedicated producer table

#### Recommendation: Phase 1
- Extract unique suppliers from `clan_products`
- Store producer name in `post.profile_producer_name`
- Link to supplier via text matching

#### Future: Phase 2
- Create `producers` table if needed
- Normalize supplier data
- Add producer index pages

### 9. Representative Examples (Category Profiles)

#### Storage Approach
Store in `post_section` with `section_type='representative_examples'`:
```json
{
  "products": [
    {"id": 123, "name": "Lochcarron Scarf", "image_url": "...", "url": "..."},
    {"id": 456, "name": "Harris Tweed Scarf", "image_url": "...", "url": "..."}
  ],
  "layout": "grid"  // or "carousel"
}
```

#### Data Source
- Query `clan_products` filtered by category
- Select diverse examples (different suppliers, price points)
- Limit to 4-8 products as specified

### 10. URL Routing & Frontend

#### Routes
```python
# In blueprints/core.py or blueprints/profiles.py
@bp.route('/blog/profiles/')
def profiles_index():
    profile_type = request.args.get('type')  # 'product' or 'category'
    # Query and render index

@bp.route('/blog/profiles/<profile_type>/<slug>/')
def profile_detail(profile_type, slug):
    # Load post with profile metadata
    # Render appropriate template
```

#### Index Page Features
- Filter by type (Product vs Category)
- Filter by category/tags
- Search functionality
- Sort by date, popularity, etc.

### 11. SEO & Metadata

#### Leverage Existing Meta Fields
- `post.meta_title` - Customize for profiles
- `post.meta_description` - Use standfirst
- `post.meta_image` - Use hero image
- `post.meta_tags` - Include profile type, category, producer

#### Schema.org Markup
- Add `Article` schema for all profiles
- Add `Product` schema for product profiles (Phase 2)
- Use existing meta_type field

### 12. Migration Strategy

#### Phase 1: Foundation
1. Add profile columns to `post` table
2. Create profile templates
3. Add URL routes
4. Create profile index page
5. Add newsletter block type

#### Phase 2: Content Creation
1. Create first few profiles manually
2. Test newsletter integration
3. Validate workflow

#### Phase 3: Automation
1. Add AI prompt templates for profile generation
2. Integrate product/category data pull
3. Automate newsletter selection

#### Phase 4: Enhancement
1. Producer index pages
2. Interactive elements
3. Schema.org markup
4. Analytics tracking

### 13. Key Considerations

#### Data Integrity
- Ensure `profile_product_id` or `profile_category_id` is set (not both)
- Validate product/category exists before linking
- Handle deleted products gracefully (NULL foreign keys)

#### Performance
- Index `post.profile_type` for filtering
- Cache product/category data lookups
- Optimize gallery image loading

#### Editorial Workflow
- Profiles are weekly features (not daily)
- **Calendar Integration**: Add dedicated "Profiles" row to calendar week view (like "Ideas", "Events", "Syndication" rows)
- Profile selection and scheduling happens within the week view interface
- Ensure editorial review before publishing

#### Commerce Integration
- Links to PDPs should use existing product URL structure
- Category links should use existing category routing
- Ensure UTM parameters for tracking

## Calendar Integration: Profiles Row

### Week View Row Structure

The calendar week view (`/planning/posts/<post_id>/calendar/week-view`) displays content in horizontal rows:
- **Themes** row (top)
- **Annual Events** row
- **Special Events** row  
- **Ideas** row
- **Syndication** row
- **Profiles** row (NEW - to be added)

### Implementation Approach

1. **Add Profiles Row to Template**
   - Add new row section in `templates/planning/calendar/week_view.html`
   - Follow same pattern as existing rows (header + row-grid with 7 day cells)
   - Add filter button for Profiles row

2. **Data Storage**
   - Profiles scheduled per week, stored in `calendar_week_posts` table
   - Link to `post` table via `post_id` where `post.profile_type IS NOT NULL`
   - May need `calendar_profile_selections` table if we want to track selected profiles per week

3. **Profile Selection UI**
   - Add "Add Profile" button in Profiles row header
   - Modal to select Product Profile or Category Profile
   - Product selection: Browse products by producer/category
   - Category selection: Browse categories with sufficient product depth
   - Display selected profile in appropriate day cell

4. **Week View Rendering**
   - Extend `static/js/planning/calendar-week-view.js` to load and render profiles
   - Query: `SELECT * FROM post WHERE profile_type IS NOT NULL AND id IN (SELECT post_id FROM calendar_week_posts WHERE year=? AND week_number=?)`
   - Render profile cards with type badge (Product/Category) and preview

### Database Schema for Calendar Integration

```sql
-- Option 1: Use existing calendar_week_posts (recommended)
-- Profiles are posts, so they can use the same table
-- Filter by post.profile_type IS NOT NULL

-- Option 2: Separate table for profile scheduling (if needed)
CREATE TABLE calendar_week_profiles (
    id SERIAL PRIMARY KEY,
    year INTEGER NOT NULL,
    week_number INTEGER NOT NULL,
    post_id INTEGER REFERENCES post(id) ON DELETE CASCADE,
    profile_type VARCHAR(20) CHECK (profile_type IN ('product', 'category')),
    scheduled_date DATE,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(year, week_number, post_id)
);
```

**Recommendation**: Use Option 1 (existing `calendar_week_posts`) initially. Only create separate table if we need profile-specific scheduling logic.

## Questions to Resolve

1. **Producer Normalization**: Should we create a `producers` table now or defer to Phase 2?
   - **Recommendation**: Defer to Phase 2, use text matching initially

2. **Gallery Storage**: Store in `post_images` or `post_section_elements`?
   - **Recommendation**: Use `post_images` with section association

3. **Representative Examples**: Store full product data or just IDs?
   - **Recommendation**: Store IDs and query on render (ensures data freshness)

4. **Workflow Customization**: Separate workflow stages or extend existing?
   - **Recommendation**: Extend existing with profile-specific prompts

5. **Newsletter Frequency**: One profile per newsletter or multiple?
   - **Recommendation**: Start with one, evaluate engagement

6. **Calendar Row Implementation**: Use existing `calendar_week_posts` or create separate table?
   - **Recommendation**: Use existing `calendar_week_posts`, filter by `profile_type`

## Next Steps

1. Review and approve schema changes
2. Create database migration
3. Build template structure
4. Implement URL routing
5. Create first test profile
6. Integrate with newsletter system
7. Document editorial workflow

