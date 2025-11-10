# Product & Category Profiles - Complete Technical Documentation

> **Note:** This documentation is part of the [Data Intelligence System](../README.md), which includes both Product & Category Profiles and the Content Generation System.

## Overview

Product & Category Profiles are editorial-first, commerce-linked blog features that explore Scottish heritage, craftsmanship, and culture. They are weekly blog features (not daily) that provide in-depth stories about products and product categories.

### Profile Types

1. **Product Profiles**: Focus on a specific product type from a named producer (e.g., "Lambswool Scarf by Lochcarron"), detailing its history, craftsmanship, and place in Scottish life.

2. **Category Profiles**: Broader, thematic features about entire product categories (e.g., "Scottish Wool Scarves"), covering origins, traditions, and evolution with representative examples from multiple producers.

### Key Characteristics

- **Editorial-first**: Rich narrative content with cultural/historical context
- **Commerce-linked**: Direct links to product pages and category pages
- **Weekly features**: Scheduled via calendar system, not daily posts
- **Data-driven**: Pulls from `clan_products` and `clan_categories` tables
- **Enriched content**: Uses web scraping, LLM analysis, and web research for context

---

## Database Schema

### New Tables

#### `producers`
Normalized producer/supplier information for Product Profiles.

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

**Purpose**: Normalize supplier information from `clan_products.supplier_name` and enrich with web research.

**Migration**: `migrations/create_producers_table.sql`

**Data Population**: `scripts/migrate_suppliers_to_producers.py` (3 producers created, 47 products linked)

---

### Extended Tables

#### `post` - Profile Fields

Added columns for profile-specific metadata:

```sql
ALTER TABLE post 
ADD COLUMN profile_type VARCHAR(20) CHECK (profile_type IN ('product', 'category', NULL)),
ADD COLUMN profile_product_id INTEGER REFERENCES clan_products(id) ON DELETE SET NULL,
ADD COLUMN profile_category_id INTEGER REFERENCES clan_categories(id) ON DELETE SET NULL,
ADD COLUMN profile_producer_id INTEGER REFERENCES producers(id) ON DELETE SET NULL,
ADD COLUMN profile_producer_name VARCHAR(255),
ADD COLUMN profile_standfirst TEXT,
ADD COLUMN profile_explore_links JSONB DEFAULT '{}',
ADD COLUMN profile_quick_facts JSONB DEFAULT '{}';

CREATE INDEX idx_post_profile_type ON post(profile_type) WHERE profile_type IS NOT NULL;
CREATE INDEX idx_post_profile_product ON post(profile_product_id) WHERE profile_product_id IS NOT NULL;
CREATE INDEX idx_post_profile_category ON post(profile_category_id) WHERE profile_category_id IS NOT NULL;
CREATE INDEX idx_post_profile_producer ON post(profile_producer_id) WHERE profile_producer_id IS NOT NULL;
```

**Field Descriptions**:
- `profile_type`: Type of profile ('product' or 'category')
- `profile_product_id`: Reference to `clan_products` for Product Profiles
- `profile_category_id`: Reference to `clan_categories` for Category Profiles
- `profile_producer_id`: Reference to `producers` table
- `profile_producer_name`: Denormalized producer name for display
- `profile_standfirst`: Short summary for hero section and meta description
- `profile_explore_links`: JSONB object with CTA links: `{product: {url, text}, producer: {url, text}, category: {url, text}}`
- `profile_quick_facts`: JSONB object with quick facts: `{producer: string, material: string, category: string}`

**Migration**: `migrations/add_profile_fields_to_post.sql`

---

#### `clan_products` - Extended Fields

```sql
ALTER TABLE clan_products
ADD COLUMN producer_id INTEGER REFERENCES producers(id) ON DELETE SET NULL,
ADD COLUMN specifications JSONB;

CREATE INDEX idx_clan_products_producer ON clan_products(producer_id) WHERE producer_id IS NOT NULL;
CREATE INDEX idx_clan_products_specifications ON clan_products USING GIN (specifications);
```

**Field Descriptions**:
- `producer_id`: Link to normalized `producers` table
- `specifications`: JSONB storing scraped product specs: `{dimensions: string, material: string, emblem: string, weight: string, care_instructions: string}`

**Migrations**: 
- `migrations/add_producer_id_to_clan_products.sql`
- `migrations/add_specifications_to_clan_products.sql`

---

#### `clan_categories` - Heritage Data

```sql
ALTER TABLE clan_categories
ADD COLUMN heritage_data JSONB,
ADD COLUMN web_researched_at TIMESTAMP,
ADD COLUMN llm_analyzed_at TIMESTAMP;

CREATE INDEX idx_clan_categories_heritage_data ON clan_categories USING GIN (heritage_data);
```

**Field Descriptions**:
- `heritage_data`: JSONB with historical/cultural context: `{historical_origins: string, cultural_significance: string, evolution: string, scottish_heritage_connections: string, hierarchy_context: string, llm_analysis: object, web_research: object}`
- `web_researched_at`: Timestamp of last web research
- `llm_analyzed_at`: Timestamp of last LLM analysis

**Migration**: `migrations/add_heritage_to_categories.sql`

---

#### `calendar_week_posts` - Profile Scheduling

Profiles are scheduled using the existing `calendar_week_posts` table:

```sql
-- Profiles use existing calendar_week_posts table
-- Filter by: post.profile_type IS NOT NULL
-- Link via: calendar_week_posts.post_id = post.id
```

**Default Weekday**: Profiles default to Thursday (weekday 4) if not specified, using `post_type_config` system.

---

## API Endpoints

### Calendar Integration

#### GET `/planning/api/calendar/profiles/<year>/<week_number>`
Get profiles scheduled for a specific year and week.

**Response**:
```json
[
  {
    "id": 123,
    "title": "Lambswool Scarf by Lochcarron",
    "profile_type": "product",
    "profile_producer_name": "Lochcarron",
    "profile_standfirst": "A timeless Scottish accessory...",
    "slug": "lambswool-scarf-lochcarron",
    "scheduled_date": "2025-01-23",
    "weekday": 4,
    "created_at": "2025-01-15T10:00:00",
    "updated_at": "2025-01-15T10:00:00"
  }
]
```

**Implementation**: `blueprints/planning_api_calendar_profiles.py`

---

### Profile CRUD

#### POST `/planning/api/profiles`
Create a new profile.

**Request Body**:
```json
{
  "profile_type": "product",
  "title": "Lambswool Scarf by Lochcarron",
  "profile_standfirst": "A timeless Scottish accessory...",
  "profile_product_id": 456,
  "profile_producer_name": "Lochcarron",
  "year": 2025,
  "week_number": 4,
  "weekday": 4
}
```

**Response**:
```json
{
  "success": true,
  "post_id": 123,
  "profile_id": 123
}
```

#### GET `/planning/api/profiles/<profile_id>`
Get a profile by ID.

**Response**:
```json
{
  "success": true,
  "profile": {
    "id": 123,
    "title": "Lambswool Scarf by Lochcarron",
    "profile_type": "product",
    "profile_product_id": 456,
    "profile_producer_name": "Lochcarron",
    "profile_standfirst": "...",
    "year": 2025,
    "week_number": 4,
    "weekday": 4
  }
}
```

#### PUT `/planning/api/profiles/<profile_id>`
Update an existing profile.

**Request Body**: Same as POST, all fields optional.

#### DELETE `/planning/api/profiles/<profile_id>`
Delete a profile.

**Response**:
```json
{
  "success": true,
  "message": "Profile deleted"
}
```

**Implementation**: `blueprints/planning_api_profiles.py`

---

### Product & Category Data

#### GET `/api/clan/products?q=<query>&limit=<limit>`
Search products for profile selection.

**Response**:
```json
[
  {
    "id": 456,
    "sku": "SCARF-001",
    "name": "Lambswool Scarf",
    "supplier_name": "Lochcarron",
    "price": "45.00",
    "image_url": "..."
  }
]
```

**Implementation**: `blueprints/clan_cache.py`

#### GET `/api/clan/products/<sku>/full?all_images=true`
Get full product details including all images.

**Implementation**: `blueprints/clan_cache.py`

#### POST `/api/clan/products/<sku>/scrape-specifications`
Scrape product specifications from product page and save to database.

**Response**:
```json
{
  "success": true,
  "product_id": 456,
  "sku": "SCARF-001",
  "specifications": {
    "dimensions": "7\" x 8\"",
    "material": "Wood",
    "emblem": "Clan crest"
  }
}
```

**Implementation**: `blueprints/clan_cache.py`

#### GET `/launchpad/api/syndication/categories`
Get category tree for profile selection.

**Response**:
```json
{
  "success": true,
  "categories": [
    {
      "id": 123,
      "name": "Scarves",
      "parent_id": 10,
      "level": 2
    }
  ]
}
```

**Implementation**: `blueprints/launchpad_content.py`

---

## Frontend Components

### Calendar Integration

#### Template: `templates/planning/calendar/week_view.html`

**Profiles Row**:
```html
<div class="row-section" data-filter="profiles">
    <div class="row-header">
        <span>Profiles</span>
        <button class="row-add-btn" onclick="getProfileModal().openNew()">
            <i class="fas fa-plus"></i> Add New
        </button>
    </div>
    <div class="row-grid" id="profiles-row"></div>
</div>
```

**Filter Pill**:
```html
<label class="filter-pill filter-profiles active">
    <input type="checkbox" id="toggle-profiles" checked> Profiles
</label>
```

**Styling**: Teal/cyan background (`#0d9488` / `#14b8a6`)

---

#### JavaScript: `static/js/planning/calendar-week-view.js`

**Profile Loading**:
```javascript
// Fetch profiles for this week
const profilesPromise = fetchJSON(`/planning/api/calendar/profiles/${year}/${weekNumber}`);

// In Promise.allSettled:
if (profilesRes.status === 'fulfilled') {
    const profilesData = profilesRes.value;
    profiles = Array.isArray(profilesData) ? profilesData : (profilesData?.profiles || []);
}
```

**Profile Rendering**:
```javascript
// Render profiles per day into Profiles row
if (showProfiles && profilesCells && profiles.length) {
    profiles.forEach((profile) => {
        const dayIdx = profile.weekday || profile.day || 1;
        const target = document.getElementById(`profiles-row-day-${Math.min(Math.max(dayIdx, 1), 7)}`);
        if (target) {
            const profileItem = {
                id: profile.id,
                title: profile.title,
                profile_type: profile.profile_type || 'product',
                _profile: true
            };
            renderItems(target, [profileItem], 'profile');
        }
    });
}
```

**Profile Item Rendering** (in `renderItems` function):
```javascript
if (type === 'profile' && item._profile) {
    // Profile display: Icon + Title
    div.classList.add('profile');
    div.style.cursor = 'pointer';
    // ... icon and text rendering
    // Click handler opens profile modal or navigates to profile page
}
```

**Filter Toggle**:
```javascript
const showProfiles = document.getElementById('toggle-profiles')?.checked !== false;
```

---

### Profile Modal

#### Template: `templates/planning/calendar/profile_modal.html`

Modal for creating and editing profiles with:
- Type selector (Product/Category)
- Product search and selection
- Category dropdown selection
- Basic information (title, standfirst)
- Week scheduling

**Included in**: `templates/planning/calendar/week_view.html`

---

#### JavaScript: `static/js/planning/profile-modal-core.js`

**Class**: `ProfileModal`

**Key Methods**:
- `openNew(week, year)`: Open modal for creating new profile
- `open(profileId)`: Open modal for editing existing profile
- `save()`: Save profile (create or update)
- `delete()`: Delete profile
- `searchProducts(query)`: Search products via API
- `loadCategories()`: Load category tree
- `selectProduct(productId, sku)`: Select product for profile
- `selectCategory(categoryId)`: Select category for profile

**Global Access**: `window.getProfileModal()`

---

#### CSS: `static/css/planning/profile-modal.css`

Modal styling matching the idea modal design system with dark theme.

---

### Profile Page Templates

#### Product Profile: `templates/profiles/product_profile.html`

Full page template for displaying Product Profiles with:
- Hero section with image and standfirst
- Quick facts bar
- Content sections (The Object, The Maker, In Context, Materials & Making)
- Gallery section
- Explore links
- Credits
- Related profiles

**Section Types**:
- `hero`: Hero block with image and standfirst
- `the_object`: Product description
- `the_maker`: Producer information
- `in_context`: Cultural/seasonal context
- `materials_making`: Materials and processes
- `gallery`: Image gallery (4-6 images)
- `explore_further`: CTA links
- `credits`: Sources and attributions

---

#### Category Profile: `templates/profiles/category_profile.html`

Full page template for displaying Category Profiles with:
- Hero section
- Category context bar
- Content sections (Origins & History, Materials & Methods, Cultural Meaning, Representative Examples)
- Swatch panel (optional)
- Explore links
- Credits

**Section Types**:
- `hero`: Hero block
- `origins_history`: Historical overview
- `materials_methods`: Materials and traditions
- `cultural_meaning`: Cultural significance
- `representative_examples`: Product grid (4-8 products)
- `swatch_panel`: Tartan/design swatch (optional)
- `explore_further`: CTA links
- `credits`: Sources and attributions

---

#### Profile Index: `templates/profiles/index.html`

Browse page for all profiles with:
- Filters (type, producer, category, search, sort)
- Profile grid with cards
- Pagination support

---

### Partial Templates

Located in `templates/profiles/partials/`:

- `_hero.html`: Hero section with image and standfirst
- `_quick_facts.html`: Quick facts bar (producer, material, category)
- `_category_context.html`: Category context bar
- `_object_section.html`: The Object section
- `_maker_section.html`: The Maker section
- `_context_section.html`: In Context section
- `_materials_section.html`: Materials & Making section
- `_origins_section.html`: Origins & History section
- `_materials_methods_section.html`: Materials & Methods section
- `_cultural_meaning_section.html`: Cultural Meaning section
- `_gallery.html`: Image gallery with lightbox
- `_representative_examples.html`: Representative products grid
- `_explore_links.html`: CTA links section
- `_credits.html`: Credits section
- `_swatch_panel.html`: Tartan swatch panel

---

### CSS Styling

#### `static/css/profiles.css`

Complete styling for profile pages including:
- Profile badges (Product/Category)
- Hero sections
- Quick facts and category context bars
- Section layouts
- Gallery grids
- Product cards
- Explore links
- Credits sections
- Profile index page
- Responsive design

---

## Data Collection Tools

### Product Specifications Scraper

**File**: `utils/product_specifications_scraper.py`

**Class**: `ProductSpecificationsScraper`

**Purpose**: Scrapes product specifications (dimensions, materials, etc.) from clan.com product pages.

**Key Methods**:
- `scrape_product_specifications(product_url)`: Scrape specs from a product page
- `scrape_and_save(product_id, product_url, db_connection)`: Scrape and save to database

**Extraction Methods**:
1. Look for specifications table (`<table>` with key-value rows)
2. Look for definition lists (`<dl><dt>Key</dt><dd>Value</dd></dl>`)
3. Look for specific data attributes or structured divs
4. Pattern matching in page text (dimensions, materials)

**Normalized Keys**: `dimensions`, `material`, `emblem`, `weight`, `care_instructions`

**API Endpoint**: `POST /api/clan/products/<sku>/scrape-specifications`

---

### Producer Research

**File**: `utils/producer_research.py`

**Class**: `ProducerResearcher`

**Purpose**: Researches producer information via web search to enrich producer records.

**Key Methods**:
- `research_producer(producer_name)`: Research producer via web search
- `enrich_from_supplier_description(supplier_description)`: Extract data from supplier_description HTML

**Research Fields**:
- `location`: Producer location
- `founding_year`: Year founded
- `heritage_details`: Heritage information
- `craftsmanship_methods`: Craftsmanship details
- `website_url`: Producer website

**Note**: Currently uses placeholder web search. In production, would use proper web search API (Google, Bing, etc.).

---

### Category Heritage Research

**File**: `utils/category_heritage_research.py`

**Class**: `CategoryHeritageResearcher`

**Purpose**: Researches historical and cultural context for categories using LLM analysis and web research.

**Key Methods**:
- `derive_category_context(category_id)`: Derive complete category context
- `llm_analyze_category(category_name, hierarchy_context, product_data)`: Use LLM to analyze category
- `aggregate_category_data(category_id)`: Aggregate product data for LLM analysis
- `get_category_path(category_id)`: Get category hierarchy path
- `web_research_category(category_name)`: Perform web research (placeholder)
- `save_heritage_data(category_id, heritage_data)`: Save to database

**LLM Analysis Fields**:
- `historical_origins`: When and how category emerged in Scotland
- `cultural_significance`: Meaning in Scottish culture
- `evolution`: How category has evolved
- `scottish_heritage_connections`: Connections to traditions, clans, regions

**LLM Integration**: Uses `blueprints.llm_actions.LLMService` with OpenAI (fallback to Ollama).

---

### Representative Products Selector

**File**: `utils/representative_products_selector.py`

**Class**: `RepresentativeProductsSelector`

**Purpose**: Selects 4-8 representative products from a category using price diversity algorithm.

**Key Methods**:
- `select_representative_products(category_id, limit=8)`: Select representative products

**Selection Priority**:
1. **Price diversity**: Select across price tiers (Low, Medium, High)
2. **Producer diversity**: Different producers within each tier
3. **Material variety**: Additional variety if slots remain

**Algorithm**:
- Divides products into 3 price tiers
- Selects from each tier prioritizing producer diversity
- Fills remaining slots with diverse products

---

## Migrations

### Migration Files

1. **`migrations/create_producers_table.sql`**
   - Creates `producers` table
   - Adds indexes

2. **`migrations/add_profile_fields_to_post.sql`**
   - Adds profile fields to `post` table
   - Adds indexes

3. **`migrations/add_producer_id_to_clan_products.sql`**
   - Adds `producer_id` to `clan_products`
   - Adds index

4. **`migrations/add_specifications_to_clan_products.sql`**
   - Adds `specifications` JSONB column
   - Adds GIN index

5. **`migrations/add_heritage_to_categories.sql`**
   - Adds heritage data columns to `clan_categories`
   - Adds GIN index

### Migration Scripts

**`scripts/apply_profile_migrations.py`**
- Applies all Phase 1 migrations in order
- Usage: `python3 scripts/apply_profile_migrations.py`

**`scripts/migrate_suppliers_to_producers.py`**
- Populates `producers` table from `clan_products.supplier_name`
- Links products to producers via `producer_id`
- Usage: `python3 scripts/migrate_suppliers_to_producers.py`

**Migration Status**: ✅ All migrations applied successfully
- 3 producers created
- 47 products linked (100% coverage)

---

## File Structure

### Backend Files

```
blueprints/
├── planning_api_calendar_profiles.py    # Calendar profiles API
├── planning_api_profiles.py              # Profile CRUD API
└── clan_cache.py                         # Product/category APIs (extended)

utils/
├── product_specifications_scraper.py    # Product specs scraper
├── producer_research.py                   # Producer web research
├── category_heritage_research.py         # Category heritage research
└── representative_products_selector.py    # Representative product selection

migrations/
├── create_producers_table.sql
├── add_profile_fields_to_post.sql
├── add_producer_id_to_clan_products.sql
├── add_specifications_to_clan_products.sql
└── add_heritage_to_categories.sql

scripts/
├── apply_profile_migrations.py
└── migrate_suppliers_to_producers.py
```

### Frontend Files

```
templates/
├── profiles/
│   ├── product_profile.html              # Product profile page
│   ├── category_profile.html             # Category profile page
│   ├── index.html                         # Profile index/browse
│   └── partials/
│       ├── _hero.html
│       ├── _quick_facts.html
│       ├── _category_context.html
│       ├── _object_section.html
│       ├── _maker_section.html
│       ├── _context_section.html
│       ├── _materials_section.html
│       ├── _origins_section.html
│       ├── _materials_methods_section.html
│       ├── _cultural_meaning_section.html
│       ├── _gallery.html
│       ├── _representative_examples.html
│       ├── _explore_links.html
│       ├── _credits.html
│       └── _swatch_panel.html
└── planning/calendar/
    └── profile_modal.html                 # Profile creation modal

static/
├── css/
│   ├── profiles.css                       # Profile page styles
│   └── planning/
│       └── profile-modal.css              # Profile modal styles
└── js/
    └── planning/
        ├── calendar-week-view.js          # Calendar integration (extended)
        └── profile-modal-core.js           # Profile modal JavaScript
```

### Documentation Files

```
docs/
└── profiles/
    ├── section-types.md                   # Section type definitions
    └── implementation-status.md           # Implementation status tracking
```

---

## Calendar Integration Details

### Week View Integration

Profiles are integrated into the calendar week view as a dedicated row, similar to Ideas, Events, and Syndication rows.

**Row Structure**:
- Header with "Profiles" label and "Add New" button
- 7-day grid (Monday-Sunday)
- Profile items rendered in appropriate day cells

**Filter Integration**:
- Filter pill in week filters section
- Toggle to show/hide profiles row
- Styling: Teal/cyan background

**Data Flow**:
1. Calendar week view loads
2. Fetches profiles via `/planning/api/calendar/profiles/<year>/<week_number>`
3. Renders profiles in appropriate day cells
4. Click handlers open profile modal or navigate to profile page

**Default Weekday**: Profiles default to Thursday (weekday 4) if not specified, using `post_type_config` system.

---

## Section Types & Content Model

### Section Storage

Sections are stored in the existing `post_section` table:
- `section_type`: One of the profile section types
- `section_heading`: Section title
- `polished` or `draft`: HTML content
- `post_images`: Linked via `section_id` for gallery/representative examples

### Special Section Data

**Gallery Section**:
- Multiple images stored in `post_images` table
- Linked via `section_id`
- Captions in `post_images.caption` or `post_section_elements`

**Representative Examples Section**:
- Selected product IDs stored in `post_section_elements` JSONB:
  ```json
  {
    "product_ids": [123, 456, 789],
    "layout": "grid"
  }
  ```
- Products queried on render for fresh data

**Full Documentation**: See `docs/profiles/section-types.md`

---

## Data Derivation Strategy

### Product Selection
- Products selected directly from `clan_products` table
- UI manages curated list for profiling
- Selection via profile modal with product search

### Producer Normalization
- `producers` table created and populated from `clan_products.supplier_name`
- Enhanced via web research (location, founding year, heritage)
- Products linked via `clan_products.producer_id`

### Material/Dimensions
- Scraped from product pages (e.g., `https://clan.com/clan-crest-wall-plaque`)
- Stored in `clan_products.specifications` JSONB column
- Scraper handles multiple extraction methods

### Representative Examples
- Selected using `RepresentativeProductsSelector`
- Priority: Price diversity → Producer diversity → Material variety
- 4-8 products per category profile

### Historical/Cultural Context
- LLM analysis of aggregated product data
- Web research for validation and enhancement
- Hierarchy inference from category tree
- Stored in `clan_categories.heritage_data` JSONB

---

## Implementation Status

### ✅ Completed

**Phase 1: Database Schema & Foundation**
- ✅ All migrations created and applied
- ✅ Producers table populated
- ✅ Profile fields added to post table
- ✅ Specifications and heritage data columns added

**Phase 2: Data Collection Tools**
- ✅ Product specifications scraper
- ✅ Producer web research function
- ✅ Category heritage research (LLM + web)
- ✅ Representative products selector
- ✅ API endpoint for scraping specifications

**Phase 3: Content Model & Templates**
- ✅ Section type definitions
- ✅ Product and Category profile page templates
- ✅ 15 partial templates for all sections
- ✅ Profile index/browse page
- ✅ CSS styling with responsive design

**Phase 4: Calendar Integration**
- ✅ Profiles row added to calendar week view
- ✅ JavaScript integration for loading/rendering
- ✅ Profile modal for creating new profiles
- ✅ Filter toggle for profiles
- ✅ Backend API endpoint for calendar week profiles

**Phase 5: Backend Routes & Editor**
- ✅ Full CRUD API routes
- ✅ Profile creation with product/category selection
- ✅ Profile scheduling in calendar
- ✅ Profile modal with product/category search

---

### ⏳ Pending / Optional Enhancements

**Phase 6: Newsletter Integration**
- ⏳ Add `profile` block type to newsletter system
- ⏳ Profile selection for newsletter issues
- ⏳ Profile rendering in newsletter template

**Phase 7: Auto-Tagging & SEO**
- ⏳ Auto-tagging based on profile type, producer, material, category
- ⏳ Enhanced Schema.org markup
- ⏳ SEO meta tag generation refinement

**Testing & Refinement**
- ⚠️ Scraper needs refinement based on actual HTML structure
- ⚠️ LLM integration tested but needs configuration
- ⚠️ Templates need backend route integration for public viewing

---

## Usage Examples

### Creating a Product Profile

1. Navigate to calendar week view
2. Click "Add New" in Profiles row
3. Select "Product Profile" type
4. Search and select a product
5. Enter title and standfirst
6. Select weekday (defaults to Thursday)
7. Click "Save Profile"

**API Call**:
```javascript
POST /planning/api/profiles
{
  "profile_type": "product",
  "title": "Lambswool Scarf by Lochcarron",
  "profile_standfirst": "A timeless Scottish accessory...",
  "profile_product_id": 456,
  "profile_producer_name": "Lochcarron",
  "year": 2025,
  "week_number": 4,
  "weekday": 4
}
```

### Creating a Category Profile

1. Navigate to calendar week view
2. Click "Add New" in Profiles row
3. Select "Category Profile" type
4. Select a category from dropdown
5. Enter title and standfirst
6. Select weekday
7. Click "Save Profile"

### Scraping Product Specifications

```python
from utils.product_specifications_scraper import ProductSpecificationsScraper

scraper = ProductSpecificationsScraper()
specs = scraper.scrape_product_specifications('https://clan.com/clan-crest-wall-plaque')
# Returns: {'dimensions': '7" x 8"', 'material': 'Wood', 'emblem': 'Clan crest'}
```

**API Call**:
```bash
curl -X POST http://localhost:5000/api/clan/products/SCARF-001/scrape-specifications
```

### Selecting Representative Products

```python
from utils.representative_products_selector import RepresentativeProductsSelector
from config.database import db_manager

conn = db_manager.get_connection()
selector = RepresentativeProductsSelector(conn)
products = selector.select_representative_products(category_id=123, limit=8)
# Returns list of 8 products with price/producer diversity
```

---

## Integration Points

### Existing Systems

**Blog System**:
- Profiles are `post` records with `profile_type IS NOT NULL`
- Use existing `post_section` table for content sections
- Use existing `post_images` table for images
- Use existing `post_tags` for tagging

**Calendar System**:
- Profiles scheduled via `calendar_week_posts` table
- Filter by `post.profile_type IS NOT NULL`
- Default weekday from `post_type_config` system

**Product/Category Data**:
- Pulls from `clan_products` and `clan_categories` tables
- Uses existing `/api/clan/products` and category APIs
- Enriches with scraped and researched data

**LLM System**:
- Uses `blueprints.llm_actions.LLMService` for category heritage analysis
- Supports OpenAI (primary) and Ollama (fallback)

---

## Known Issues & Limitations

1. **Specifications Scraper**: Needs refinement based on actual HTML structure of clan.com product pages. Currently extracts some UI text that should be filtered.

2. **LLM Integration**: Tested but needs proper API key configuration. Falls back to Ollama if OpenAI unavailable.

3. **Web Research**: Producer and category web research uses placeholder implementation. In production, would use proper web search API.

4. **Public Routes**: Profile page templates exist but backend routes for public viewing not yet implemented. Profiles can be created and scheduled but not yet viewable on frontend.

5. **Newsletter Integration**: Not yet implemented. Profiles cannot be added to newsletter issues.

---

## Next Steps for New Developer

### Immediate Tasks

1. **Test Profile Creation**
   - Navigate to calendar week view
   - Create a test product profile
   - Verify it appears in calendar
   - Check database records

2. **Implement Public Routes**
   - Create routes for viewing profiles: `/blog/profiles/product/<slug>` and `/blog/profiles/category/<slug>`
   - Connect templates to routes
   - Test profile page rendering

3. **Refine Scraper**
   - Test with real product URLs
   - Adjust extraction patterns
   - Filter out UI text

4. **Configure LLM**
   - Set up OpenAI API key or Ollama
   - Test category heritage research
   - Refine prompts if needed

### Medium Priority

5. **Newsletter Integration**
   - Add profile block type to newsletter system
   - Add profile selection UI
   - Test profile rendering in newsletter

6. **Auto-Tagging**
   - Implement auto-tagging on profile creation
   - Tags: `producer:`, `material:`, `category:`
   - Test tag generation

### Low Priority

7. **Enhancements**
   - Add profile editor UI for section editing
   - Enhance SEO meta tags
   - Add profile analytics tracking

---

## Related Documentation

- `docs/product-category-profiles-planning.md`: Initial project brief
- `docs/product-category-profiles-implementation-thoughts.md`: Technical implementation recommendations
- `docs/product-category-profiles-data-derivation.md`: Data derivation strategy
- `docs/product-category-profiles-design-layout.md`: Design and layout specifications
- `docs/profiles/section-types.md`: Section type definitions
- `docs/profiles/implementation-status.md`: Implementation status tracking

---

## Contact & Support

For questions or issues:
1. Check existing documentation in `docs/profiles/`
2. Review implementation status in `docs/profiles/implementation-status.md`
3. Check code comments in implementation files
4. Review database schema in migration files

---

**Last Updated**: 2025-01-27  
**Version**: 1.0  
**Status**: Core functionality complete, public routes pending

---

## Appendix: Quick Reference

### Database Tables Summary

| Table | Purpose | Key Fields |
|-------|---------|------------|
| `producers` | Normalized producer info | `id`, `name`, `description`, `location`, `founding_year` |
| `post` | Blog posts (includes profiles) | `profile_type`, `profile_product_id`, `profile_category_id`, `profile_producer_id` |
| `clan_products` | Product catalog | `producer_id`, `specifications` (JSONB) |
| `clan_categories` | Category tree | `heritage_data` (JSONB), `web_researched_at`, `llm_analyzed_at` |
| `calendar_week_posts` | Week scheduling | `year`, `week_number`, `post_id`, `weekday` |
| `post_section` | Content sections | `section_type`, `section_heading`, `polished`, `draft` |
| `post_images` | Images | `section_id`, `caption` |

### API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/planning/api/calendar/profiles/<year>/<week>` | GET | Get profiles for week |
| `/planning/api/profiles` | POST | Create profile |
| `/planning/api/profiles/<id>` | GET | Get profile |
| `/planning/api/profiles/<id>` | PUT | Update profile |
| `/planning/api/profiles/<id>` | DELETE | Delete profile |
| `/api/clan/products?q=<query>` | GET | Search products |
| `/api/clan/products/<sku>/full` | GET | Get full product |
| `/api/clan/products/<sku>/scrape-specifications` | POST | Scrape specs |
| `/launchpad/api/syndication/categories` | GET | Get categories |

### Key JavaScript Functions

| Function | File | Purpose |
|----------|------|---------|
| `getProfileModal()` | `profile-modal-core.js` | Get profile modal instance |
| `loadWeek(year, weekNumber)` | `calendar-week-view.js` | Load week data (includes profiles) |
| `renderItems(container, items, type)` | `calendar-week-view.js` | Render items (includes 'profile' type) |

### Key Python Classes

| Class | File | Purpose |
|-------|------|---------|
| `ProductSpecificationsScraper` | `utils/product_specifications_scraper.py` | Scrape product specs |
| `ProducerResearcher` | `utils/producer_research.py` | Research producer info |
| `CategoryHeritageResearcher` | `utils/category_heritage_research.py` | Research category heritage |
| `RepresentativeProductsSelector` | `utils/representative_products_selector.py` | Select representative products |
| `ProfileModal` | `static/js/planning/profile-modal-core.js` | Profile modal UI |

