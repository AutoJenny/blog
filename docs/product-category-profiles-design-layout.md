# Product & Category Profiles: Design, Layout & Tagging

## Overview

This document outlines the visual design, layout structure, tagging system, and UI components required for Product and Category Profile pages. This will help identify backend and frontend requirements that may not have been obvious from data derivation alone.

## Design Philosophy

**Editorial-first, Commerce-linked**: These are not sales pages but editorial features that inform, inspire, and gently route readers toward commerce through tasteful CTAs.

**Visual Hierarchy:**
1. **Hero** - Evocative, aspirational imagery
2. **Story** - Rich narrative content with visual breaks
3. **Commerce Links** - Subtle, contextual CTAs
4. **Credits** - Transparent sourcing

## Page Structure

### A. Product Profile Layout

```
┌─────────────────────────────────────────────────┐
│  HEADER (existing blog header)                  │
├─────────────────────────────────────────────────┤
│  [BREADCRUMBS: Blog > Profiles > Product]       │
├─────────────────────────────────────────────────┤
│  [PROFILE BADGE: "Product Profile"]            │
│                                                  │
│  ┌──────────────────────────────────────────┐  │
│  │  HERO BLOCK                               │  │
│  │  [Hero Image - Full Width, 1200x630]    │  │
│  │  [Headline: "The Lochcarron Lambswool    │  │
│  │   Scarf"]                                 │  │
│  │  [Standfirst: One-sentence summary]      │  │
│  └──────────────────────────────────────────┘  │
│                                                  │
│  ┌──────────────────────────────────────────┐  │
│  │  QUICK FACTS BAR                          │  │
│  │  [Producer: Lochcarron] [Material:       │  │
│  │  Lambswool] [Category: Scarves]          │  │
│  └──────────────────────────────────────────┘  │
│                                                  │
│  [SECTION 1: The Object]                        │
│  [Product description, design, feel, purpose]  │
│  [Image: Product detail shot]                   │
│                                                  │
│  [SECTION 2: The Maker]                         │
│  [Producer story, location, craftsmanship]     │
│  [Image: Workshop/maker photo]                  │  │
│                                                  │
│  [SECTION 3: In Context]                       │
│  [Cultural/seasonal significance, tradition]    │
│  [Image: Lifestyle/use case]                    │
│                                                  │
│  [SECTION 4: Materials & Making]               │
│  [Materials, processes, sustainability]         │
│  [Image: Material detail or process]            │
│                                                  │
│  ┌──────────────────────────────────────────┐  │
│  │  GALLERY (4-6 images)                     │  │
│  │  [Grid layout, lightbox on click]        │  │
│  └──────────────────────────────────────────┘  │
│                                                  │
│  ┌──────────────────────────────────────────┐  │
│  │  EXPLORE FURTHER                          │  │
│  │  [CTA 1: View this product →]             │
│  │  [CTA 2: About Lochcarron →]              │
│  │  [CTA 3: Shop all scarves →]              │
│  └──────────────────────────────────────────┘  │
│                                                  │
│  [CREDITS & SOURCES]                            │
│  [Image credits, fact sources]                  │
│                                                  │
│  ┌──────────────────────────────────────────┐  │
│  │  PROFILE METADATA                        │  │
│  │  [Tags: product-profile, scarves,        │  │
│  │   lochcarron, lambswool, heritage]        │  │
│  │  [Categories: Accessories > Scarves]     │  │
│  │  [Published: Date] [Updated: Date]       │  │
│  └──────────────────────────────────────────┘  │
│                                                  │
│  [RELATED PROFILES]                             │
│  [Cards: Other product/category profiles]        │
│                                                  │
│  FOOTER (existing blog footer)                   │
└─────────────────────────────────────────────────┘
```

### B. Category Profile Layout

```
┌─────────────────────────────────────────────────┐
│  HEADER (existing blog header)                  │
├─────────────────────────────────────────────────┤
│  [BREADCRUMBS: Blog > Profiles > Category]      │
├─────────────────────────────────────────────────┤
│  [PROFILE BADGE: "Category Profile"]            │
│                                                  │
│  ┌──────────────────────────────────────────┐  │
│  │  HERO BLOCK                               │  │
│  │  [Atmospheric image - Full Width]        │  │
│  │  [Headline: "Scottish Wool Scarves:       │  │
│  │   Warmth, Weave & Tradition"]             │  │
│  │  [Standfirst: Summary of scope]          │  │
│  └──────────────────────────────────────────┘  │
│                                                  │
│  ┌──────────────────────────────────────────┐  │
│  │  CATEGORY CONTEXT BAR                     │  │
│  │  [Category: Scarves] [Level: 2]          │  │
│  │  [Parent: Accessories]                    │  │
│  └──────────────────────────────────────────┘  │
│                                                  │
│  [SECTION 1: Origins & History]                  │
│  [Chronological overview, key dates]            │
│  [Image: Historical/heritage image]             │
│                                                  │
│  [SECTION 2: Materials & Methods]               │
│  [Fibre types, weaving traditions, variations]  │
│  [Image: Materials/process]                     │
│                                                  │
│  [SECTION 3: Cultural Meaning & Use]           │
│  [Gift customs, seasonal roles, modern use]     │
│  [Image: Cultural context]                      │
│                                                  │
│  ┌──────────────────────────────────────────┐  │
│  │  REPRESENTATIVE EXAMPLES (4-8 products)  │  │
│  │  [Grid layout with product cards]        │  │
│  │  [Each card: Image, Name, Producer,     │  │
│  │   Price, Link]                           │  │
│  └──────────────────────────────────────────┘  │
│                                                  │
│  [SWATCH/TARTAN PANEL (Optional)]              │
│  [Visual array of tartans/designs]             │
│                                                  │
│  ┌──────────────────────────────────────────┐  │
│  │  EXPLORE FURTHER                          │  │
│  │  [CTA 1: Shop scarves →]                 │  │
│  │  [CTA 2: Find your clan's tartan →]      │  │
│  │  [CTA 3: Discover more stories →]       │  │
│  └──────────────────────────────────────────┘  │
│                                                  │
│  [CREDITS & SOURCES]                            │
│                                                  │
│  [PROFILE METADATA]                             │
│  [RELATED PROFILES]                             │
│  FOOTER                                          │
└─────────────────────────────────────────────────┘
```

## Visual Design Elements

### 1. Profile Badge

**Purpose:** Immediate visual identifier that this is a profile (not regular blog post)

**Design:**
- Small badge above hero: "Product Profile" or "Category Profile"
- Color coding: 
  - Product Profile: Blue/Teal (#0ea5e9)
  - Category Profile: Purple/Indigo (#6366f1)
- Icon: Briefcase (product) or Folder (category)

**Implementation:**
```html
<div class="profile-badge profile-badge--product">
    <i class="fas fa-briefcase"></i>
    <span>Product Profile</span>
</div>
```

**CSS:**
```css
.profile-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.375rem 0.75rem;
    border-radius: 9999px;
    font-size: 0.875rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}

.profile-badge--product {
    background: #0ea5e9;
    color: white;
}

.profile-badge--category {
    background: #6366f1;
    color: white;
}
```

### 2. Quick Facts Bar (Product Profiles)

**Purpose:** At-a-glance key information

**Design:**
- Horizontal bar below hero
- Icons + text for: Producer, Material, Category
- Subtle background, border separator

**Implementation:**
```html
<div class="profile-quick-facts">
    <div class="quick-fact">
        <i class="fas fa-industry"></i>
        <span class="label">Producer</span>
        <span class="value">Lochcarron</span>
    </div>
    <div class="quick-fact">
        <i class="fas fa-scroll"></i>
        <span class="label">Material</span>
        <span class="value">Lambswool</span>
    </div>
    <div class="quick-fact">
        <i class="fas fa-tag"></i>
        <span class="label">Category</span>
        <span class="value">Scarves</span>
    </div>
</div>
```

**Backend Requirement:**
- Extract producer, material, category from product data
- Store in `post.profile_quick_facts` JSONB or separate fields

### 3. Category Context Bar (Category Profiles)

**Purpose:** Show category hierarchy and level

**Design:**
- Similar to Quick Facts but for category information
- Shows: Category name, Level, Parent category path

### 4. Representative Examples Grid (Category Profiles)

**Purpose:** Display 4-8 products as examples

**Design:**
- Responsive grid: 2 columns (mobile), 3-4 columns (desktop)
- Product cards with:
  - Product image (thumbnail)
  - Product name
  - Producer name
  - Price
  - "View Product" link

**Implementation:**
```html
<div class="representative-examples">
    <h3>Representative Examples</h3>
    <div class="examples-grid">
        {% for product in representative_products %}
        <div class="product-card">
            <img src="{{ product.image_url }}" alt="{{ product.name }}">
            <div class="product-info">
                <h4>{{ product.name }}</h4>
                <p class="producer">{{ product.supplier_name }}</p>
                <p class="price">£{{ product.price }}</p>
                <a href="{{ product.url }}" class="btn-view">View Product</a>
            </div>
        </div>
        {% endfor %}
    </div>
</div>
```

**Backend Requirement:**
- Query products by category (from `category_ids` JSONB)
- Apply price diversity selection algorithm
- Limit to 4-8 products
- Store selected product IDs in `post_section` JSONB or separate table

### 5. Gallery Component

**Purpose:** Show 4-6 images in elegant grid

**Design:**
- Masonry or grid layout
- Lightbox on click (use existing lightbox library)
- Captions below images
- Responsive: 2 columns (mobile), 3-4 columns (desktop)

**Implementation:**
```html
<div class="profile-gallery">
    {% for image in gallery_images %}
    <figure class="gallery-item">
        <a href="{{ image.url }}" data-lightbox="gallery-{{ post.id }}">
            <img src="{{ image.thumbnail_url }}" alt="{{ image.alt_text }}">
        </a>
        {% if image.caption %}
        <figcaption>{{ image.caption }}</figcaption>
        {% endif %}
    </figure>
    {% endfor %}
</div>
```

**Backend Requirement:**
- Store gallery images in `post_images` table
- Link to `post_section` via `section_id`
- Support multiple images per section
- Store captions in `post_images.caption` or `post_section_elements`

### 6. Explore Further CTAs

**Purpose:** Tasteful commerce links

**Design:**
- Not hard sales buttons
- Subtle, editorial-style links
- Icon + text format
- Arrow indicator (→)

**Implementation:**
```html
<div class="explore-further">
    <h3>Explore Further</h3>
    <ul class="explore-links">
        <li>
            <a href="{{ product_url }}" class="explore-link">
                <i class="fas fa-arrow-right"></i>
                <span>View this product</span>
            </a>
        </li>
        <li>
            <a href="{{ producer_url }}" class="explore-link">
                <i class="fas fa-arrow-right"></i>
                <span>About {{ producer_name }}</span>
            </a>
        </li>
        <li>
            <a href="{{ category_url }}" class="explore-link">
                <i class="fas fa-arrow-right"></i>
                <span>Shop all {{ category_name }}</span>
            </a>
        </li>
    </ul>
</div>
```

**Backend Requirement:**
- Store explore links in `post.profile_explore_links` JSONB:
```json
{
  "product": {"url": "...", "text": "View this product"},
  "producer": {"url": "...", "text": "About Lochcarron"},
  "category": {"url": "...", "text": "Shop all scarves"}
}
```

### 7. Credits & Sources

**Purpose:** Transparency and attribution

**Design:**
- Small text at bottom
- Collapsible/expandable section
- List of image credits and fact sources

**Implementation:**
```html
<details class="credits-section">
    <summary>Credits & Sources</summary>
    <div class="credits-content">
        <h4>Images</h4>
        <ul>
            <li>Hero image: [Source]</li>
            <li>Gallery image 1: [Source]</li>
        </ul>
        <h4>Sources</h4>
        <ul>
            <li>Historical information: [Source]</li>
            <li>Producer information: [Source]</li>
        </ul>
    </div>
</details>
```

**Backend Requirement:**
- Store credits in `post_section` JSONB or separate `post_credits` table
- Link to images and sources

## Tagging System

### Required Tags

**Profile Type Tags:**
- `type:product-profile` - All product profiles
- `type:category-profile` - All category profiles

**Content Tags:**
- Producer tags: `producer:lochcarron`, `producer:william-lockie`
- Material tags: `material:lambswool`, `material:cashmere`, `material:wool`
- Category tags: `category:scarves`, `category:kilts`, `category:plaques`
- Heritage tags: `heritage:scottish`, `heritage:highland`, `heritage:clan`
- Regional tags: `region:scotland`, `region:highlands`, `region:islands`

**Feature Tags:**
- `gift-idea` - Suitable for gifting
- `seasonal:autumn` - Seasonal relevance
- `handmade` - Handcrafted products
- `sustainable` - Sustainability focus

### Tag Implementation

**Database:**
- Use existing `post_tags` table
- Link tags via `post_tags` junction table
- Auto-generate tags from profile data:
  - Producer → `producer:{supplier_name}`
  - Material → `material:{extracted_material}`
  - Category → `category:{category_name}`

**Display:**
- Tag cloud at bottom of profile
- Clickable tags link to filtered profile index
- Visual distinction: Type tags (badges), content tags (pills)

**Backend Requirement:**
- Auto-tagging function when profile is created
- Tag extraction from product/category data
- Manual tag override capability

## Metadata & SEO

### Required Meta Fields

**Profile-Specific:**
- `profile_type` - "product" or "category"
- `profile_product_id` - Link to `clan_products`
- `profile_category_id` - Link to `clan_categories`
- `profile_producer_name` - Producer name
- `profile_standfirst` - Short summary for meta description

**SEO Enhancements:**
- Rich snippets for Product/Category
- Schema.org markup:
  - `Article` schema (base)
  - `Product` schema (for product profiles)
  - `BreadcrumbList` schema
  - `Organization` schema (for producer)

**Implementation:**
```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "Article",
  "headline": "{{ post.title }}",
  "description": "{{ post.profile_standfirst }}",
  "image": "{{ post.header_image.path }}",
  {% if post.profile_type == 'product' %}
  "about": {
    "@type": "Product",
    "name": "{{ product.name }}",
    "brand": {
      "@type": "Brand",
      "name": "{{ product.supplier_name }}"
    }
  }
  {% endif %}
}
</script>
```

## Template Structure

### Template Files

**Main Templates:**
- `templates/profiles/product_profile.html` - Product profile layout
- `templates/profiles/category_profile.html` - Category profile layout
- `templates/profiles/index.html` - Profile index page (filtered listing)

**Partial Templates:**
- `templates/profiles/partials/_hero.html` - Hero block
- `templates/profiles/partials/_quick_facts.html` - Quick facts bar
- `templates/profiles/partials/_maker_section.html` - Maker section
- `templates/profiles/partials/_gallery.html` - Gallery component
- `templates/profiles/partials/_representative_examples.html` - Examples grid
- `templates/profiles/partials/_explore_links.html` - CTA section
- `templates/profiles/partials/_credits.html` - Credits section

### Template Inheritance

```jinja2
{% extends "base.html" %}

{% block title %}{{ post.title }} - Product Profile - Clan.com Blog{% endblock %}

{% block content %}
    {% include 'profiles/partials/_hero.html' %}
    {% include 'profiles/partials/_quick_facts.html' %}
    
    {% for section in sections %}
        {% if section.section_type == 'the_object' %}
            {% include 'profiles/partials/_object_section.html' %}
        {% elif section.section_type == 'the_maker' %}
            {% include 'profiles/partials/_maker_section.html' %}
        {% elif section.section_type == 'gallery' %}
            {% include 'profiles/partials/_gallery.html' %}
        {% endif %}
    {% endfor %}
    
    {% include 'profiles/partials/_explore_links.html' %}
    {% include 'profiles/partials/_credits.html' %}
{% endblock %}
```

## Backend Requirements Identified

### Database Schema Additions

1. **Profile Metadata in `post` table:**
   - `profile_type` VARCHAR(20)
   - `profile_product_id` INTEGER
   - `profile_category_id` INTEGER
   - `profile_producer_name` VARCHAR(255)
   - `profile_standfirst` TEXT
   - `profile_explore_links` JSONB
   - `profile_quick_facts` JSONB

2. **Section-Specific Data:**
   - Store gallery images in `post_images` with `section_id`
   - Store representative products in `post_section_elements` JSONB
   - Store credits in `post_section` JSONB or separate table

3. **Tag Auto-Generation:**
   - Function to auto-generate tags from profile data
   - Tag normalization (lowercase, slugify)

### API Endpoints Needed

1. **Profile Data Endpoints:**
   - `GET /api/profiles/product/<product_id>/data` - Get product data for profile
   - `GET /api/profiles/category/<category_id>/data` - Get category data for profile
   - `GET /api/profiles/<post_id>/representative-products` - Get representative products

2. **Tag Management:**
   - `POST /api/profiles/<post_id>/tags/auto-generate` - Auto-generate tags
   - `GET /api/profiles/tags` - Get available tags with counts

3. **Image Management:**
   - `POST /api/profiles/<post_id>/gallery/add` - Add gallery image
   - `GET /api/profiles/<post_id>/gallery` - Get gallery images

### UI Components Needed

1. **Profile Editor:**
   - Product/Category selection interface
   - Quick facts editor
   - Gallery image uploader/selector
   - Representative products selector (for category profiles)
   - Explore links editor
   - Credits editor

2. **Profile Index Page:**
   - Filter by type (Product/Category)
   - Filter by tags (producer, material, category)
   - Search functionality
   - Sort by date, popularity

3. **Calendar Integration:**
   - Profile selection modal
   - Profile preview in calendar week view
   - Profile scheduling UI

## Responsive Design

### Breakpoints

- **Mobile**: < 768px
  - Single column layout
  - Stacked quick facts
  - 2-column gallery
  - Full-width images

- **Tablet**: 768px - 1024px
  - 2-column sections
  - 3-column gallery
  - Side-by-side quick facts

- **Desktop**: > 1024px
  - Max-width container (1200px)
  - 3-4 column gallery
  - Full visual hierarchy

## Accessibility

### Requirements

1. **Alt Text:**
   - All images require alt text
   - Descriptive alt text for gallery images
   - Empty alt for decorative images

2. **Semantic HTML:**
   - Use `<article>` for main content
   - Use `<section>` for content sections
   - Use `<figure>` and `<figcaption>` for images

3. **ARIA Labels:**
   - Profile badges: `aria-label="Product Profile"`
   - Gallery items: `aria-label="Gallery image {number}"`
   - CTA buttons: Descriptive aria-labels

4. **Keyboard Navigation:**
   - All interactive elements keyboard accessible
   - Gallery lightbox keyboard navigation
   - Focus indicators visible

## Performance Considerations

1. **Image Optimization:**
   - Lazy loading for gallery images
   - Responsive image sizes (srcset)
   - WebP format where supported

2. **Caching:**
   - Cache profile data queries
   - Cache representative products
   - Cache tag counts

3. **Loading States:**
   - Skeleton screens for profile loading
   - Progressive image loading
   - Smooth transitions

## Integration Points

### Existing Systems

1. **Blog Post System:**
   - Profiles are posts with `profile_type` set
   - Use existing post workflow
   - Use existing section system

2. **Image System:**
   - Use existing `post_images` table
   - Use existing image optimization
   - Use existing image upload workflow

3. **Tag System:**
   - Use existing `post_tags` table
   - Use existing tag management
   - Extend with auto-tagging

4. **Newsletter:**
   - Profile teaser in newsletter
   - Use existing newsletter block system
   - Profile-specific newsletter templates

## Next Steps

1. **Design Mockups:**
   - Create visual mockups for key components
   - Test responsive layouts
   - Validate accessibility

2. **Template Development:**
   - Build base templates
   - Create partial templates
   - Test with sample data

3. **Backend Implementation:**
   - Add database fields
   - Create API endpoints
   - Build auto-tagging system

4. **UI Components:**
   - Profile editor interface
   - Gallery manager
   - Representative products selector










