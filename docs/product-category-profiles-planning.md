# Project Brief: Product & Category Profiles  

*(Editorial-first, Commerce-linked)*



---



## 1️⃣ Overview



We are introducing two complementary **editorial profile types** — both designed as **weekly blog features** that inform, inspire, and gently route readers toward commerce.  

They are not sales pages but *stories of heritage, craftsmanship, and culture*.



### Types



1. **Product Profiles** — Focused on a *specific product type* from a named producer (e.g. "Lambswool Scarf by Lochcarron"), showing its history, craftsmanship, and place within Scottish life.  

   - This product may come in **many tartans or variations**, but is defined as a *single product concept* by a particular maker.



2. **Category Profiles** — Broader, thematic features about *entire product categories* (e.g. "Scottish Wool Scarves"), covering their origins, traditions, and evolution with representative examples from multiple producers.



Both live within the **Blog** system and are promoted through the **weekly newsletter** and **social channels**.



---



## 2️⃣ Editorial Goals



- **Inspiration first:** Engage emotionally before selling.  

- **Authority through heritage:** Build trust by explaining origins, symbolism, and craftsmanship.  

- **Continuity of tradition:** Link historical craft to modern Scottish production.  

- **Route to commerce naturally:** End with tasteful, optional links to explore, not hard sales prompts.



---



## 3️⃣ Core Distinctions



| Aspect | Product Profile | Category Profile |

|--------|----------------|-----------------|

| Focus | A *specific product type* from a named producer | A *broad category* of goods |

| Example | "Lambswool Scarf by Lochcarron" | "Scottish Wool Scarves: Warmth & Tradition" |

| Scope | One producer's product concept (many tartans possible) | Cross-producer, historical and cultural |

| Voice | Personal, narrative, behind-the-scenes | Interpretive, encyclopaedic, comparative |

| Visuals | Workshop, product-in-use, maker close-ups | Mood, history, materials, range overview |

| CTAs | "View this product," "Visit producer," "Shop scarves" | "Shop the category," "Find your tartan," "Learn more" |

| Data Linkage | Product type + producer entity | Category facet + example items |



---



## 4️⃣ Structure & Templates



### 🧵 A. Product Profile Template



**Purpose:** Tell the story of one *real product concept* made by a specific Scottish producer.



#### Layout Structure

1. **Hero Block**

   - Evocative image (AI or photographic)

   - Headline (e.g. "The Lochcarron Lambswool Scarf")

   - Standfirst (one-sentence summary)



2. **The Object**

   - Description of the product concept — its design, feel, and purpose.

   - Why it's distinctive to the maker or tradition.



3. **The Maker**

   - About the producer or workshop.

   - Place, materials, and ethos.

   - Optional quote or maker note.



4. **In Context**

   - Where this product fits in the wider tradition (e.g. tartans, Highlandwear, gifting).

   - Seasonal or cultural significance.



5. **Materials & Making**

   - Key materials and processes.

   - Sustainability or sourcing notes.



6. **Gallery**

   - 4–6 images (product, detail, workshop, lifestyle).

   - Captions add story value.



7. **Explore Further**

   - "View this product →" (links to PDP)

   - "About Lochcarron →" (producer page)

   - "Shop all scarves →" (category page)



8. **Credits & Sources**

   - Image and fact attributions.



---



### 🧭 B. Category Profile Template



**Purpose:** Explore the *broader story* of a class of goods — its origins, evolution, materials, and symbolism.



#### Layout Structure

1. **Hero Block**

   - Atmospheric image or illustration

   - Headline (e.g. "Scottish Wool Scarves: Warmth, Weave & Tradition")

   - Standfirst (summary of scope)



2. **Origins & History**

   - Chronological overview with key dates or developments.

   - Connection to regions or clans.



3. **Materials & Methods**

   - Fibre types, weaving traditions, and regional variations.



4. **Cultural Meaning & Use**

   - Gift customs, gender/seasonal roles, modern interpretations.



5. **Representative Examples**

   - Grid of 4–8 products across makers or families.

   - Short captions, no SKU focus.



6. **Swatch or Tartan Panel (Optional)**

   - Visual array linking to tartan design pages.



7. **Explore Further**

   - "Shop scarves →"

   - "Find your clan's tartan →"

   - "Discover more stories →"



8. **Credits & Sources**

   - Fact sources and image credits.



---



## 5️⃣ CMS / Content Model

### Database Schema

**Post Table Extensions:**
- `profile_type` VARCHAR(20) - 'product' or 'category'
- `profile_product_id` INTEGER - References `clan_products(id)`
- `profile_category_id` INTEGER - References `clan_categories(id)`
- `profile_producer_id` INTEGER - References `producers(id)` (new table)
- `profile_producer_name` VARCHAR(255) - Producer name (for display)
- `profile_standfirst` TEXT - Short summary for hero and meta
- `profile_explore_links` JSONB - CTA links (product, producer, category URLs)
- `profile_quick_facts` JSONB - Quick facts bar data (producer, material, category)

**New Tables:**
- `producers` - Normalized producer/supplier information
- Product specifications stored in `clan_products.specifications` JSONB
- Category heritage stored in `clan_categories.heritage_data` JSONB

### Product Profile Fields

- **Title** (e.g. "Lambswool Scarf by Lochcarron")  
- **Slug**  
- **Hero Image**  
- **Product Reference** (links to `clan_products` table)  
- **Producer Reference** (links to `producers` table)  
- **Standfirst** (short summary)  
- **Quick Facts:** Producer, Material, Category (displayed in bar)
- **Body Sections:** Object Story / Maker / Context / Materials (via `post_section`)  
- **Gallery** (4-6 images stored in `post_images` with section association)  
- **Explore Links:** PDP / Producer / Category (stored in `profile_explore_links` JSONB)  
- **Tags:** Auto-generated `type:product-profile`, `producer:{name}`, `material:{material}`, `category:{category}`  
- **Teaser:** 20–30 word blurb for newsletter/social  

### Category Profile Fields

- **Title** (e.g. "Scottish Wool Scarves: Warmth, Weave & Tradition")  
- **Slug**  
- **Hero Image**  
- **Category Reference** (links to `clan_categories` table)  
- **Standfirst**  
- **Category Context:** Category name, level, parent path (displayed in bar)
- **Body Sections:** Origins / Materials / Cultural Meaning (via `post_section`)  
- **Representative Examples:** 4-8 products selected by price diversity (stored in section JSONB)  
- **Swatch Panel (optional)**  
- **Explore Links:** category / tartan / related posts (stored in `profile_explore_links` JSONB)  
- **Tags:** Auto-generated `type:category-profile`, `category:{name}`, material tags, heritage tags  
- **Teaser:** for newsletter/social  



---



## 6️⃣ Workflow Concept (Weekly Cadence)

### Calendar Integration

Profiles are scheduled via the **Calendar Week View** in a dedicated "Profiles" row (alongside Themes, Events, Ideas, Syndication rows). Each week can have one profile scheduled.

### Workflow Steps

1. **Select Topic (Calendar Week View)**
   - Navigate to Calendar Week View
   - Click "Add Profile" in Profiles row
   - Choose Product Profile or Category Profile
   - Select product from `clan_products` or category from `clan_categories`
   - Profile post created and scheduled to week

2. **Data Enrichment**
   - **For Product Profiles:**
     - Pull product data from `clan_products`
     - Scrape specifications (dimensions, materials) from product page
     - Link to producer, enrich producer data via web research
   - **For Category Profiles:**
     - Pull category data from `clan_categories`
     - Select 4-8 representative products (price diversity algorithm)
     - Research heritage via LLM + web search

3. **Profile Editor**
   - Edit standfirst
   - Edit quick facts (Product) or category context (Category)
   - Create/edit sections (Object, Maker, Context, Materials, etc.)
   - Upload/select gallery images (4-6 images)
   - Select representative products (Category only)
   - Add explore links (product, producer, category URLs)
   - Add credits and sources
   - Auto-generate tags (can be overridden)

4. **Hero Image Creation**
   - Select or generate aspirational image
   - Use existing header image workflow

5. **Editorial Pass**
   - Human refinement, tone alignment, source verification
   - Verify all links work
   - Check image credits

6. **Review & QA**
   - Ensure correct classification (Product vs Category)
   - Fact-checking
   - Link validation
   - Image alt text verification
   - Accessibility check

7. **Publish**
   - Publish profile post
   - Auto-included in next newsletter (via autodraft)
   - Generate teaser for social channels



---



## 7️⃣ QA Checklist



- ✅ Type clearly distinguished (Product vs Category)  

- ✅ Product Profile includes real producer and product type  

- ✅ Category Profile uses multiple examples, not SKU-centric  

- ✅ All imagery credited and licensed (AI images labelled)  

- ✅ Links verified (PDP / producer / category / design)  

- ✅ Metadata unique and SEO compliant  

- ✅ Alt text and accessibility tags complete  



---



## 8️⃣ Integration Points

### Database Integration

- **Product Data:**
  - Product Profile → `clan_products` table via `profile_product_id`
  - Specifications scraped from product pages → `clan_products.specifications` JSONB
  - Producer linked via `producer_id` → `producers` table
  
- **Category Data:**
  - Category Profile → `clan_categories` table via `profile_category_id`
  - Heritage data (LLM + web research) → `clan_categories.heritage_data` JSONB
  - Representative products selected via price diversity algorithm

### Blog System Integration

- Each Profile is a blog post with `profile_type` column set
- Uses existing `post_section` system for content sections
- Uses existing `post_images` system for gallery images
- Uses existing `post_tags` system (with auto-tagging)

### Calendar Integration

- **Profiles Row:** Added to calendar week view (alongside Themes, Events, Ideas, Syndication)
- **Scheduling:** Profiles scheduled via `calendar_week_posts` table
- **Selection UI:** Modal interface to browse and select products/categories
- **Display:** Profile cards shown in appropriate day cells

### Newsletter Integration

- **Profile Block Type:** New `profile` block type in newsletter system
- **Autodraft:** Automatically includes most recent published profile
- **Teaser:** Auto-generated from standfirst
- **Image:** Uses profile hero image

### Frontend Display

- **Index Page:** `/blog/profiles/` with filters (type, tags, producer, category, search)
- **Detail Pages:**
  - `/blog/profiles/product/{slug}/` - Product profile
  - `/blog/profiles/category/{slug}/` - Category profile
- **Templates:** Separate templates for product vs category profiles
- **Components:** Reusable partials (hero, quick facts, gallery, etc.)

### Social Media

- Profile teasers included in social media posts
- Uses existing social media integration
- Profile-specific metadata for sharing



---



## 9️⃣ Metrics for Success



- **Product Profiles:**  

  - Click-through to product or producer pages  

  - Engagement time on article  

  - Shares/bookmarks



- **Category Profiles:**  

  - Click-through to category/tartan routes  

  - Time on page and scroll depth  

  - Newsletter open and link rate



---



## 10️⃣ Phase 2 (Future Enhancements)

- Producer index pages linking from Product Profiles
- Interactive maps/timelines for historical categories
- Schema.org `Article` + `Product` microdata integration (Phase 1 includes basic schema)
- Optional quiz or "Did You Know" engagement block
- Richer visual storytelling templates (AI + human hybrid)
- Profile analytics and performance tracking
- A/B testing for CTA effectiveness

---

## 11️⃣ Implementation Plan

See **[Implementation Plan](product-category-profiles-implementation-plan.md)** for detailed step-by-step development guide.

### Quick Reference

**Phase 1:** Database Schema & Foundation  
**Phase 2:** Data Collection & Enrichment  
**Phase 3:** Content Model & Templates  
**Phase 4:** Calendar Integration  
**Phase 5:** Profile Editor UI  
**Phase 6:** Frontend Display  
**Phase 7:** Newsletter Integration  
**Phase 8:** Testing & Refinement

**Estimated Time:** 70-80 hours (realistic)

---

## Related Documentation

- **[Implementation Plan](product-category-profiles-implementation-plan.md)** - Step-by-step development guide
- **[Implementation Thoughts](product-category-profiles-implementation-thoughts.md)** - Technical recommendations
- **[Data Derivation Strategy](product-category-profiles-data-derivation.md)** - Data extraction approach
- **[Design & Layout](product-category-profiles-design-layout.md)** - Visual design and UI components

---

**End of Brief**

