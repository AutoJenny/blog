# Product & Category Profiles: Implementation Plan

## Overview

This document provides a step-by-step implementation plan for building the Product & Category Profiles feature. It consolidates all planning documents and provides actionable tasks in the correct order.

## Implementation Phases

### Phase 1: Database Schema & Foundation
**Goal:** Establish database structure and core data models

### Phase 2: Data Collection & Enrichment
**Goal:** Build data collection tools (scraping, web research, LLM integration)

### Phase 3: Content Model & Templates
**Goal:** Create profile templates and content structure

### Phase 4: Calendar Integration
**Goal:** Add Profiles row to calendar week view

### Phase 5: Profile Editor UI
**Goal:** Build interface for creating and editing profiles

### Phase 6: Frontend Display
**Goal:** Public-facing profile pages and index

### Phase 7: Newsletter Integration
**Goal:** Automate profile inclusion in weekly newsletter

### Phase 8: Testing & Refinement
**Goal:** Test, fix, and polish

---

## Phase 1: Database Schema & Foundation

### Task 1.1: Create Producers Table
**Priority:** High  
**Dependencies:** None  
**Estimated Time:** 30 minutes

**Actions:**
1. Create migration file: `migrations/create_producers_table.sql`
2. Define schema:
```sql
CREATE TABLE producers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    location VARCHAR(255),
    founding_year INTEGER,
    heritage_details TEXT,
    craftsmanship_methods TEXT,
    website_url VARCHAR(500),
    web_researched_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_producers_name ON producers(name);
```

3. Run migration
4. Test table creation

**Files to Create:**
- `migrations/create_producers_table.sql`

**Files to Modify:**
- None

---

### Task 1.2: Extend Post Table for Profiles
**Priority:** High  
**Dependencies:** Task 1.1  
**Estimated Time:** 30 minutes

**Actions:**
1. Create migration file: `migrations/add_profile_fields_to_post.sql`
2. Add columns:
```sql
ALTER TABLE post 
ADD COLUMN IF NOT EXISTS profile_type VARCHAR(20) CHECK (profile_type IN ('product', 'category', NULL)),
ADD COLUMN IF NOT EXISTS profile_product_id INTEGER REFERENCES clan_products(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS profile_category_id INTEGER REFERENCES clan_categories(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS profile_producer_id INTEGER REFERENCES producers(id) ON DELETE SET NULL,
ADD COLUMN IF NOT EXISTS profile_producer_name VARCHAR(255),
ADD COLUMN IF NOT EXISTS profile_standfirst TEXT,
ADD COLUMN IF NOT EXISTS profile_explore_links JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS profile_quick_facts JSONB DEFAULT '{}',
ADD COLUMN IF NOT EXISTS specifications JSONB;

CREATE INDEX idx_post_profile_type ON post(profile_type) WHERE profile_type IS NOT NULL;
CREATE INDEX idx_post_profile_product ON post(profile_product_id) WHERE profile_product_id IS NOT NULL;
CREATE INDEX idx_post_profile_category ON post(profile_category_id) WHERE profile_category_id IS NOT NULL;
```

3. Run migration
4. Test column additions

**Files to Create:**
- `migrations/add_profile_fields_to_post.sql`

**Files to Modify:**
- None

---

### Task 1.3: Link Products to Producers
**Priority:** High  
**Dependencies:** Task 1.1, Task 1.2  
**Estimated Time:** 20 minutes

**Actions:**
1. Create migration file: `migrations/add_producer_id_to_clan_products.sql`
2. Add column:
```sql
ALTER TABLE clan_products
ADD COLUMN IF NOT EXISTS producer_id INTEGER REFERENCES producers(id) ON DELETE SET NULL;

CREATE INDEX idx_clan_products_producer ON clan_products(producer_id) WHERE producer_id IS NOT NULL;
```

3. Create data migration script to populate producers from supplier_name
4. Link products to producers

**Files to Create:**
- `migrations/add_producer_id_to_clan_products.sql`
- `scripts/migrate_suppliers_to_producers.py`

**Files to Modify:**
- None

---

### Task 1.4: Add Specifications Column to Products
**Priority:** Medium  
**Dependencies:** None  
**Estimated Time:** 15 minutes

**Actions:**
1. Create migration file: `migrations/add_specifications_to_clan_products.sql`
2. Add column:
```sql
ALTER TABLE clan_products
ADD COLUMN IF NOT EXISTS specifications JSONB;
```

3. Run migration

**Files to Create:**
- `migrations/add_specifications_to_clan_products.sql`

---

### Task 1.5: Add Heritage Data to Categories
**Priority:** Medium  
**Dependencies:** None  
**Estimated Time:** 15 minutes

**Actions:**
1. Create migration file: `migrations/add_heritage_to_categories.sql`
2. Add columns:
```sql
ALTER TABLE clan_categories
ADD COLUMN IF NOT EXISTS heritage_data JSONB,
ADD COLUMN IF NOT EXISTS web_researched_at TIMESTAMP,
ADD COLUMN IF NOT EXISTS llm_analyzed_at TIMESTAMP;
```

3. Run migration

**Files to Create:**
- `migrations/add_heritage_to_categories.sql`

---

## Phase 2: Data Collection & Enrichment

### Task 2.1: Build Product Specifications Scraper
**Priority:** High  
**Dependencies:** Task 1.4  
**Estimated Time:** 2-3 hours

**Actions:**
1. Create scraper module: `utils/product_specifications_scraper.py`
2. Implement scraping function:
   - Parse product page HTML
   - Extract specifications table (dimensions, material, etc.)
   - Return structured JSON
3. Add error handling and retry logic
4. Add rate limiting (respectful scraping)
5. Test with sample products
6. Create API endpoint: `POST /api/clan/products/<sku>/scrape-specifications`

**Files to Create:**
- `utils/product_specifications_scraper.py`
- `tests/test_product_specifications_scraper.py`

**Files to Modify:**
- `blueprints/clan_cache.py` (add endpoint)

**Example Implementation:**
```python
def scrape_product_specifications(product_url):
    """Scrape dimensions, materials, and other specifications from product page"""
    import requests
    from bs4 import BeautifulSoup
    
    response = requests.get(product_url, timeout=10)
    soup = BeautifulSoup(response.content, 'html.parser')
    
    specs = {}
    # Find specifications table and extract key-value pairs
    # Return as JSON
    
    return specs
```

---

### Task 2.2: Build Producer Web Research Function
**Priority:** Medium  
**Dependencies:** Task 1.1  
**Estimated Time:** 2-3 hours

**Actions:**
1. Create research module: `utils/producer_research.py`
2. Implement web search function:
   - Search for `{producer_name} Scotland` or `{producer_name} Scottish`
   - Extract location, founding year, heritage details
   - Store in producers table
3. Add caching to avoid re-searching
4. Create API endpoint: `POST /api/producers/<producer_id>/research`

**Files to Create:**
- `utils/producer_research.py`
- `tests/test_producer_research.py`

**Files to Modify:**
- `blueprints/clan_cache.py` or create new blueprint

---

### Task 2.3: Build Category Heritage Research
**Priority:** Medium  
**Dependencies:** Task 1.5  
**Estimated Time:** 2-3 hours

**Actions:**
1. Create research module: `utils/category_heritage_research.py`
2. Implement LLM + web research function:
   - Aggregate product data from category
   - Get category hierarchy context
   - Use LLM to analyze historical/cultural significance
   - Supplement with web research
   - Store in `clan_categories.heritage_data`
3. Create API endpoint: `POST /api/categories/<category_id>/research-heritage`

**Files to Create:**
- `utils/category_heritage_research.py`
- `tests/test_category_heritage_research.py`

**Files to Modify:**
- `blueprints/clan_cache.py` or create new blueprint

---

### Task 2.4: Build Representative Products Selector
**Priority:** High  
**Dependencies:** Task 1.2  
**Estimated Time:** 2 hours

**Actions:**
1. Create selection module: `utils/representative_products_selector.py`
2. Implement selection algorithm:
   - Priority 1: Price diversity (select across price tiers)
   - Priority 2: Producer diversity
   - Priority 3: Material variety
   - Limit to 4-8 products
3. Create API endpoint: `GET /api/profiles/category/<category_id>/representative-products?limit=8`

**Files to Create:**
- `utils/representative_products_selector.py`
- `tests/test_representative_products_selector.py`

**Files to Modify:**
- Create new blueprint: `blueprints/profiles.py`

**Example Implementation:**
```python
def select_representative_products(category_id, limit=8):
    # Get all products in category
    # Sort by price, divide into tiers
    # Select from each tier ensuring producer diversity
    # Return selected products
```

---

## Phase 3: Content Model & Templates

### Task 3.1: Create Profile Section Types
**Priority:** High  
**Dependencies:** Task 1.2  
**Estimated Time:** 1 hour

**Actions:**
1. Define profile-specific section types:
   - `hero` - Hero block with image and standfirst
   - `the_object` - Product description (Product Profiles)
   - `the_maker` - Producer information
   - `in_context` - Cultural/seasonal context
   - `materials_making` - Materials and processes
   - `gallery` - Image gallery (4-6 images)
   - `origins_history` - Historical overview (Category Profiles)
   - `materials_methods` - Materials and traditions (Category Profiles)
   - `cultural_meaning` - Cultural significance (Category Profiles)
   - `representative_examples` - Product grid (Category Profiles)
   - `swatch_panel` - Tartan swatch (optional)
   - `explore_further` - CTA links
   - `credits` - Sources and attributions

2. Document section types in `docs/profiles/section-types.md`

**Files to Create:**
- `docs/profiles/section-types.md`

**Files to Modify:**
- None (documentation only)

---

### Task 3.2: Create Base Profile Templates
**Priority:** High  
**Dependencies:** Task 3.1  
**Estimated Time:** 3-4 hours

**Actions:**
1. Create template directory: `templates/profiles/`
2. Create base templates:
   - `templates/profiles/product_profile.html`
   - `templates/profiles/category_profile.html`
3. Create partial templates:
   - `templates/profiles/partials/_hero.html`
   - `templates/profiles/partials/_quick_facts.html`
   - `templates/profiles/partials/_category_context.html`
   - `templates/profiles/partials/_maker_section.html`
   - `templates/profiles/partials/_gallery.html`
   - `templates/profiles/partials/_representative_examples.html`
   - `templates/profiles/partials/_explore_links.html`
   - `templates/profiles/partials/_credits.html`
4. Extend base blog template
5. Add profile badges and visual elements

**Files to Create:**
- `templates/profiles/product_profile.html`
- `templates/profiles/category_profile.html`
- `templates/profiles/partials/_hero.html`
- `templates/profiles/partials/_quick_facts.html`
- `templates/profiles/partials/_category_context.html`
- `templates/profiles/partials/_maker_section.html`
- `templates/profiles/partials/_gallery.html`
- `templates/profiles/partials/_representative_examples.html`
- `templates/profiles/partials/_explore_links.html`
- `templates/profiles/partials/_credits.html`

**Files to Modify:**
- None

---

### Task 3.3: Create Profile CSS Styles
**Priority:** High  
**Dependencies:** Task 3.2  
**Estimated Time:** 2-3 hours

**Actions:**
1. Create CSS file: `static/css/profiles.css`
2. Add styles for:
   - Profile badges (Product/Category)
   - Quick facts bar
   - Category context bar
   - Gallery grid
   - Representative examples grid
   - Explore links
   - Credits section
3. Ensure responsive design (mobile, tablet, desktop)
4. Ensure accessibility (focus states, contrast)

**Files to Create:**
- `static/css/profiles.css`

**Files to Modify:**
- Base template (include CSS file)

---

### Task 3.4: Create Profile Index Template
**Priority:** Medium  
**Dependencies:** Task 3.2  
**Estimated Time:** 2 hours

**Actions:**
1. Create template: `templates/profiles/index.html`
2. Add filtering UI:
   - Filter by type (Product/Category)
   - Filter by tags (producer, material, category)
   - Search functionality
3. Add sorting options (date, popularity)
4. Add profile cards layout

**Files to Create:**
- `templates/profiles/index.html`

**Files to Modify:**
- None

---

## Phase 4: Calendar Integration

### Task 4.1: Add Profiles Row to Calendar Week View
**Priority:** High  
**Dependencies:** Task 1.2  
**Estimated Time:** 2-3 hours

**Actions:**
1. Modify template: `templates/planning/calendar/week_view.html`
2. Add Profiles row section:
   - Header with "Profiles" label
   - "Add Profile" button
   - Row grid with 7 day cells
3. Add filter button for Profiles row
4. Style to match existing rows

**Files to Modify:**
- `templates/planning/calendar/week_view.html`
- `static/css/planning/calendar-week-view.css` (if exists)

---

### Task 4.2: Extend Calendar Week View JavaScript
**Priority:** High  
**Dependencies:** Task 4.1  
**Estimated Time:** 3-4 hours

**Actions:**
1. Modify: `static/js/planning/calendar-week-view.js`
2. Add profile loading function:
   - Query profiles for week: `SELECT * FROM post WHERE profile_type IS NOT NULL AND id IN (SELECT post_id FROM calendar_week_posts WHERE year=? AND week_number=?)`
   - Render profile cards in appropriate day cells
3. Add profile selection modal:
   - Browse products (for Product Profiles)
   - Browse categories (for Category Profiles)
   - Select and schedule
4. Add profile card rendering:
   - Show profile type badge
   - Show preview (title, image)
   - Link to profile editor

**Files to Modify:**
- `static/js/planning/calendar-week-view.js`

**Files to Create:**
- `templates/planning/calendar/includes/profile_selection_modal.html`

---

### Task 4.3: Create Profile Selection API
**Priority:** High  
**Dependencies:** Task 4.2  
**Estimated Time:** 2 hours

**Actions:**
1. Create blueprint: `blueprints/profiles.py` (if not exists)
2. Add endpoints:
   - `GET /api/profiles/products` - List products for selection
   - `GET /api/profiles/categories` - List categories for selection
   - `POST /api/profiles/schedule` - Schedule profile to week
   - `GET /api/profiles/week/<year>/<week_number>` - Get profiles for week

**Files to Create:**
- `blueprints/profiles.py` (if not exists)

**Files to Modify:**
- `unified_app.py` (register blueprint)

---

## Phase 5: Profile Editor UI

### Task 5.1: Create Profile Creation Workflow
**Priority:** High  
**Dependencies:** Task 4.3  
**Estimated Time:** 4-5 hours

**Actions:**
1. Create route: `GET /profiles/create` - Profile creation page
2. Create template: `templates/profiles/create.html`
3. Add selection interface:
   - Radio buttons: Product Profile / Category Profile
   - Product selector (if Product Profile)
   - Category selector (if Category Profile)
4. Create profile post on selection
5. Redirect to profile editor

**Files to Create:**
- `templates/profiles/create.html`

**Files to Modify:**
- `blueprints/profiles.py`

---

### Task 5.2: Create Profile Editor Interface
**Priority:** High  
**Dependencies:** Task 5.1  
**Estimated Time:** 6-8 hours

**Actions:**
1. Create route: `GET /profiles/<post_id>/edit` - Profile editor
2. Create template: `templates/profiles/edit.html`
3. Add editor components:
   - Standfirst editor
   - Quick facts editor (Product Profiles)
   - Section content editors
   - Gallery image uploader/selector
   - Representative products selector (Category Profiles)
   - Explore links editor
   - Credits editor
4. Save functionality for each component

**Files to Create:**
- `templates/profiles/edit.html`
- `static/js/profiles/editor.js`

**Files to Modify:**
- `blueprints/profiles.py`

---

### Task 5.3: Build Gallery Manager Component
**Priority:** Medium  
**Dependencies:** Task 5.2  
**Estimated Time:** 3-4 hours

**Actions:**
1. Create gallery management UI:
   - Image upload interface
   - Image selection from existing images
   - Drag-and-drop reordering
   - Caption editor for each image
   - Remove image functionality
2. Store in `post_images` table with `section_id` linking to gallery section
3. Support 4-6 images per gallery

**Files to Create:**
- `templates/profiles/includes/gallery_manager.html`
- `static/js/profiles/gallery_manager.js`

**Files to Modify:**
- `blueprints/profiles.py` (add gallery endpoints)

---

### Task 5.4: Build Representative Products Selector UI
**Priority:** Medium  
**Dependencies:** Task 2.4, Task 5.2  
**Estimated Time:** 3-4 hours

**Actions:**
1. Create UI component for selecting representative products
2. Show products from category with:
   - Product image
   - Product name
   - Producer
   - Price
3. Allow selection of 4-8 products
4. Show price diversity indicator
5. Store selected product IDs in section data

**Files to Create:**
- `templates/profiles/includes/representative_products_selector.html`
- `static/js/profiles/representative_products_selector.js`

**Files to Modify:**
- `blueprints/profiles.py`

---

### Task 5.5: Build Auto-Tagging System
**Priority:** Medium  
**Dependencies:** Task 5.2  
**Estimated Time:** 2-3 hours

**Actions:**
1. Create auto-tagging function:
   - Extract producer → `producer:{supplier_name}`
   - Extract material → `material:{material}`
   - Extract category → `category:{category_name}`
   - Add type tag: `type:product-profile` or `type:category-profile`
2. Create tag suggestion UI:
   - Show auto-generated tags
   - Allow manual override
   - Add custom tags
3. Auto-tag on profile creation/update

**Files to Create:**
- `utils/profile_auto_tagging.py`
- `tests/test_profile_auto_tagging.py`

**Files to Modify:**
- `blueprints/profiles.py` (add auto-tagging endpoint)

---

## Phase 6: Frontend Display

### Task 6.1: Create Profile Detail Routes
**Priority:** High  
**Dependencies:** Task 3.2  
**Estimated Time:** 2 hours

**Actions:**
1. Create routes:
   - `GET /blog/profiles/product/<slug>/` - Product profile page
   - `GET /blog/profiles/category/<slug>/` - Category profile page
2. Load post with profile data
3. Load sections
4. Load related data (product, category, producer)
5. Render appropriate template

**Files to Modify:**
- `blueprints/profiles.py`

---

### Task 6.2: Create Profile Index Route
**Priority:** Medium  
**Dependencies:** Task 3.4  
**Estimated Time:** 2 hours

**Actions:**
1. Create route: `GET /blog/profiles/`
2. Add query parameters:
   - `type` - Filter by product/category
   - `tag` - Filter by tag
   - `producer` - Filter by producer
   - `category` - Filter by category
   - `search` - Search query
   - `sort` - Sort order (date, popularity)
3. Load and render filtered profiles

**Files to Modify:**
- `blueprints/profiles.py`

---

### Task 6.3: Add Schema.org Markup
**Priority:** Medium  
**Dependencies:** Task 6.1  
**Estimated Time:** 2 hours

**Actions:**
1. Add JSON-LD structured data to profile templates:
   - `Article` schema (base)
   - `Product` schema (for product profiles)
   - `BreadcrumbList` schema
   - `Organization` schema (for producer)
2. Test with Google Rich Results Test

**Files to Modify:**
- `templates/profiles/product_profile.html`
- `templates/profiles/category_profile.html`

---

### Task 6.4: Add Related Profiles Section
**Priority:** Low  
**Dependencies:** Task 6.1  
**Estimated Time:** 2 hours

**Actions:**
1. Create related profiles query:
   - Same producer (for Product Profiles)
   - Same category (for Category Profiles)
   - Similar tags
2. Display as card grid at bottom of profile
3. Limit to 3-4 related profiles

**Files to Modify:**
- `templates/profiles/product_profile.html`
- `templates/profiles/category_profile.html`
- `blueprints/profiles.py` (add related query)

---

## Phase 7: Newsletter Integration

### Task 7.1: Add Profile Block Type to Newsletter
**Priority:** Medium  
**Dependencies:** Task 6.1  
**Estimated Time:** 2 hours

**Actions:**
1. Add profile block type to `newsletter_block_type` table:
```sql
INSERT INTO newsletter_block_type (type, description) 
VALUES ('profile', 'Weekly product or category profile feature');
```
2. Create newsletter block template: `templates/newsletter/partials/profile_block.html`
3. Add block editor: `templates/newsletter/partials/block_editor_profile.html`

**Files to Create:**
- `templates/newsletter/partials/profile_block.html`
- `templates/newsletter/partials/block_editor_profile.html`

**Files to Modify:**
- Migration or seed script

---

### Task 7.2: Extend Newsletter Autodraft
**Priority:** Medium  
**Dependencies:** Task 7.1  
**Estimated Time:** 2 hours

**Actions:**
1. Modify: `blog-core/newsletter/services/suggestion_service.py`
2. Add profile selection logic:
   - Query for most recent published profile
   - Create profile block suggestion
   - Include in autodraft
3. Test autodraft with profile block

**Files to Modify:**
- `blog-core/newsletter/services/suggestion_service.py`

---

## Phase 8: Testing & Refinement

### Task 8.1: Create Test Profiles
**Priority:** High  
**Dependencies:** All previous phases  
**Estimated Time:** 4-5 hours

**Actions:**
1. Create 2-3 test Product Profiles:
   - Select products with good data
   - Complete all sections
   - Add gallery images
   - Test all CTAs
2. Create 2-3 test Category Profiles:
   - Select categories with sufficient products
   - Complete all sections
   - Test representative examples
   - Test all CTAs
3. Verify display on frontend
4. Verify calendar integration
5. Verify newsletter integration

**Files to Create:**
- Test data (manual creation through UI)

---

### Task 8.2: Test Data Collection
**Priority:** High  
**Dependencies:** Task 2.1, Task 2.2, Task 2.3  
**Estimated Time:** 2-3 hours

**Actions:**
1. Test specifications scraper:
   - Test with various product types
   - Verify data extraction accuracy
   - Test error handling
2. Test producer research:
   - Test with various producers
   - Verify data extraction
   - Test caching
3. Test category heritage research:
   - Test LLM analysis
   - Test web research
   - Verify data storage

**Files to Modify:**
- Test scripts or manual testing

---

### Task 8.3: Performance Testing
**Priority:** Medium  
**Dependencies:** Task 8.1  
**Estimated Time:** 2 hours

**Actions:**
1. Test page load times
2. Test image loading (lazy loading)
3. Test gallery lightbox performance
4. Test representative examples grid performance
5. Optimize slow queries

**Files to Modify:**
- Templates (add lazy loading if needed)
- Queries (optimize if needed)

---

### Task 8.4: Accessibility Testing
**Priority:** Medium  
**Dependencies:** Task 8.1  
**Estimated Time:** 2 hours

**Actions:**
1. Test keyboard navigation
2. Test screen reader compatibility
3. Test focus indicators
4. Test alt text for all images
5. Test ARIA labels
6. Fix any accessibility issues

**Files to Modify:**
- Templates (add ARIA labels if missing)
- CSS (improve focus indicators if needed)

---

### Task 8.5: Documentation
**Priority:** Medium  
**Dependencies:** All previous phases  
**Estimated Time:** 2-3 hours

**Actions:**
1. Update main documentation:
   - Update `docs/product-category-profiles-planning.md` with final decisions
   - Update `docs/product-category-profiles-implementation-thoughts.md` with actual implementation
   - Update `docs/product-category-profiles-data-derivation.md` with learned insights
   - Update `docs/product-category-profiles-design-layout.md` with final design
2. Create user guide:
   - How to create a Product Profile
   - How to create a Category Profile
   - How to schedule profiles in calendar
3. Create API documentation:
   - Document all profile endpoints
   - Document data structures

**Files to Create:**
- `docs/profiles/user-guide.md`
- `docs/profiles/api-reference.md`

**Files to Modify:**
- Existing planning documents

---

## Implementation Checklist

### Phase 1: Database Schema & Foundation
- [ ] Task 1.1: Create Producers Table
- [ ] Task 1.2: Extend Post Table for Profiles
- [ ] Task 1.3: Link Products to Producers
- [ ] Task 1.4: Add Specifications Column to Products
- [ ] Task 1.5: Add Heritage Data to Categories

### Phase 2: Data Collection & Enrichment
- [ ] Task 2.1: Build Product Specifications Scraper
- [ ] Task 2.2: Build Producer Web Research Function
- [ ] Task 2.3: Build Category Heritage Research
- [ ] Task 2.4: Build Representative Products Selector

### Phase 3: Content Model & Templates
- [ ] Task 3.1: Create Profile Section Types
- [ ] Task 3.2: Create Base Profile Templates
- [ ] Task 3.3: Create Profile CSS Styles
- [ ] Task 3.4: Create Profile Index Template

### Phase 4: Calendar Integration
- [ ] Task 4.1: Add Profiles Row to Calendar Week View
- [ ] Task 4.2: Extend Calendar Week View JavaScript
- [ ] Task 4.3: Create Profile Selection API

### Phase 5: Profile Editor UI
- [ ] Task 5.1: Create Profile Creation Workflow
- [ ] Task 5.2: Create Profile Editor Interface
- [ ] Task 5.3: Build Gallery Manager Component
- [ ] Task 5.4: Build Representative Products Selector UI
- [ ] Task 5.5: Build Auto-Tagging System

### Phase 6: Frontend Display
- [ ] Task 6.1: Create Profile Detail Routes
- [ ] Task 6.2: Create Profile Index Route
- [ ] Task 6.3: Add Schema.org Markup
- [ ] Task 6.4: Add Related Profiles Section

### Phase 7: Newsletter Integration
- [ ] Task 7.1: Add Profile Block Type to Newsletter
- [ ] Task 7.2: Extend Newsletter Autodraft

### Phase 8: Testing & Refinement
- [ ] Task 8.1: Create Test Profiles
- [ ] Task 8.2: Test Data Collection
- [ ] Task 8.3: Performance Testing
- [ ] Task 8.4: Accessibility Testing
- [ ] Task 8.5: Documentation

---

## Dependencies Summary

### Critical Path
1. **Phase 1** (Database) → **Phase 2** (Data Collection) → **Phase 3** (Templates) → **Phase 4** (Calendar) → **Phase 5** (Editor) → **Phase 6** (Frontend) → **Phase 7** (Newsletter) → **Phase 8** (Testing)

### Parallel Work Opportunities
- Task 2.1, 2.2, 2.3 can be done in parallel
- Task 3.2, 3.3 can be done in parallel
- Task 5.3, 5.4 can be done in parallel
- Task 8.2, 8.3, 8.4 can be done in parallel

---

## Estimated Total Time

**Optimistic:** 50-60 hours  
**Realistic:** 70-80 hours  
**Pessimistic:** 90-100 hours

**Breakdown by Phase:**
- Phase 1: 2-3 hours
- Phase 2: 10-12 hours
- Phase 3: 8-10 hours
- Phase 4: 7-9 hours
- Phase 5: 18-24 hours
- Phase 6: 8-10 hours
- Phase 7: 4-5 hours
- Phase 8: 13-17 hours

---

## Notes

- All migrations should be reversible
- All API endpoints should have error handling
- All UI components should be responsive
- All code should follow existing patterns in codebase
- Test data should be created for each component
- Documentation should be updated as development progresses






