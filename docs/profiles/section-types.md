# Profile Section Types

This document defines the section types used in Product and Category Profiles.

## Product Profile Sections

### `hero`
**Purpose:** Hero block with image and standfirst  
**Content:** Header image, headline, standfirst (one-sentence summary)  
**Display:** Full-width hero at top of page

### `the_object`
**Purpose:** Product description - design, feel, purpose  
**Content:** Narrative about the product concept, why it's distinctive  
**Display:** Text content with optional product detail image

### `the_maker`
**Purpose:** Producer information  
**Content:** About the producer/workshop, place, materials, ethos, optional quote  
**Display:** Text content with optional workshop/maker image

### `in_context`
**Purpose:** Cultural/seasonal context  
**Content:** Where product fits in tradition, seasonal/cultural significance  
**Display:** Text content with optional lifestyle/use case image

### `materials_making`
**Purpose:** Materials and processes  
**Content:** Key materials, processes, sustainability notes  
**Display:** Text content with optional material/process image

### `gallery`
**Purpose:** Image gallery (4-6 images)  
**Content:** Multiple images with captions  
**Display:** Grid layout with lightbox

### `explore_further`
**Purpose:** CTA links  
**Content:** Links to product, producer, category pages  
**Display:** Editorial-style link list

### `credits`
**Purpose:** Sources and attributions  
**Content:** Image credits, fact sources  
**Display:** Collapsible section at bottom

## Category Profile Sections

### `hero`
**Purpose:** Hero block with image and standfirst  
**Content:** Atmospheric image, headline, standfirst  
**Display:** Full-width hero at top of page

### `origins_history`
**Purpose:** Historical overview  
**Content:** Chronological overview, key dates, connection to regions/clans  
**Display:** Text content with optional historical/heritage image

### `materials_methods`
**Purpose:** Materials and traditions  
**Content:** Fibre types, weaving traditions, regional variations  
**Display:** Text content with optional materials/process image

### `cultural_meaning`
**Purpose:** Cultural significance  
**Content:** Gift customs, gender/seasonal roles, modern interpretations  
**Display:** Text content with optional cultural context image

### `representative_examples`
**Purpose:** Product grid (4-8 products)  
**Content:** Selected products with images, names, producers, prices  
**Display:** Grid layout with product cards

### `swatch_panel`
**Purpose:** Tartan/design swatch (optional)  
**Content:** Visual array of tartans/designs  
**Display:** Grid or carousel of swatches

### `explore_further`
**Purpose:** CTA links  
**Content:** Links to category, tartan, related posts  
**Display:** Editorial-style link list

### `credits`
**Purpose:** Sources and attributions  
**Content:** Fact sources, image credits  
**Display:** Collapsible section at bottom

## Section Storage

Sections are stored in the existing `post_section` table:
- `section_type` - One of the types above
- `section_heading` - Section title
- `polished` or `draft` - HTML content
- `post_images` - Linked via `section_id` for gallery/representative examples

## Special Section Data

### Gallery Section
- Store multiple images in `post_images` table
- Link via `section_id`
- Store captions in `post_images.caption` or `post_section_elements`

### Representative Examples Section
- Store selected product IDs in `post_section_elements` JSONB:
  ```json
  {
    "product_ids": [123, 456, 789],
    "layout": "grid"
  }
  ```
- Query products on render for fresh data




