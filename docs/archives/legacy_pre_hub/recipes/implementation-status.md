# Scottish Recipe Series - Implementation Status

## ✅ Completed (Phase 0: Calendar Integration)

### Database & Schema
- ✅ Created `calendar_recipes` table (separate from `calendar_ideas`)
- ✅ Added `recipe_week_number` field to `post` table (1-52 for perpetual week assignment)
- ✅ Created indexes for performance
- ✅ Populated 52 recipe definitions into `calendar_recipes` table
- ✅ Cleaned up recipe entries from `calendar_ideas` table

### Calendar Integration
- ✅ Created Recipes API endpoint: `/planning/api/calendar/recipes/<year>/<week_number>`
- ✅ Added Recipes row to calendar week view UI (after Profiles row)
- ✅ Added filter toggle for Recipes row
- ✅ Implemented recipe loading and rendering in JavaScript
- ✅ Recipes display as definitions until posts are scheduled
- ✅ CSS styling for recipe items (warm orange/brown theme)

### API Functionality
- ✅ API returns recipe definitions from `calendar_recipes` table
- ✅ API checks for scheduled recipe posts and returns them if available
- ✅ Handles missing `calendar_week_posts` table gracefully
- ✅ Defaults recipes to Monday (weekday 1) for display

---

## ✅ Completed (Phase 1: Content Structure & Section Types)

### Section Types & Documentation
- ✅ Created `docs/recipes/section-types.md` documenting all recipe section types
- ✅ Created `static/css/recipes.css` with recipe-specific styling
- ✅ Updated `blog-launchpad/templates/post_preview.html` to render recipe sections
- ✅ Updated `blueprints/header.py` to include `section_type` in section data
- ✅ Recipe gallery section displays image first, then caption
- ✅ Recipe sections have proper CSS classes for styling

### Phase 2: Content Generation (Partially Complete)

#### 2.1 LLM Prompt Templates
- ✅ Created LLM prompt templates for recipe content generation:
  - ✅ Recipe background (cultural/historic) - warm, storytelling voice
  - ✅ Recipe ingredients formatting
  - ✅ Recipe method formatting (numbered steps)
  - ✅ Recipe variants (optional twists)
  - ✅ Serving suggestions
- ✅ Stored all prompts in `llm_prompt` table
- ✅ Consistent voice: warm, storytelling, heritage home cooking (not chef talk)

#### 2.2 Image Generation
- ✅ Created image prompt templates for:
  - ✅ Recipe hero images (warm, authentic Scottish, lived-in aesthetic, not stock photography)
  - ✅ Making process images (one step of recipe showing preparation/cooking)
- ✅ Created photo-harvesting search prompts for both hero and making process images
- ✅ Both image types use consistent warm, authentic Scottish aesthetic
- ✅ All prompts stored in `llm_prompt` table:
  - `Recipe Hero Image Generation (Scottish Recipes)`
  - `Recipe Hero Image Search (Scottish Recipes)`
  - `Recipe Making Process Image Generation (Scottish Recipes)`
  - `Recipe Making Process Image Search (Scottish Recipes)`
- [ ] Extend existing header image generation to support recipe hero image style
- [ ] Add image generation workflow for making process images

### Phase 3: Tags & Categories (Complete)

#### 3.1 Category & Tag Setup
- ✅ Created "Scottish Recipes" category in database
- ✅ Created required tags:
  - ✅ "Scottish Recipes"
  - ✅ "Traditional Food"
  - ✅ "Seasonal Cooking"
- [ ] Add additional tags per recipe: dish name, region (e.g., "Moray", "Borders"), season
- [ ] Ensure tag/category assignment happens automatically when recipe posts are created

---

## 🔲 Remaining Work (To Make Recipe Feature Fully Functional)

#### 3.2 Additional Tags (Future)
- [ ] Add additional tags per recipe: dish name, region (e.g., "Moray", "Borders"), season
- [ ] Ensure tag/category assignment happens automatically when recipe posts are created

### Phase 4: Recipe Index Page (Complete)

#### 4.1 Index Page Creation
- ✅ Created "Scottish Recipes" index page at `/recipes`
- ✅ Displays all 52 recipes in week order (1-52)
- ✅ Recipe cards include:
  - ✅ Recipe title
  - ✅ Hero image (if available, with placeholder fallback)
  - ✅ Brief description
  - ✅ Week number badge
  - ✅ Link to full recipe post (if published)
  - ✅ Status indicator (Published / Not Yet Created)
  - ✅ Seasonal context display
- ✅ Created `blueprints/recipes.py` with index route and API endpoint
- ✅ Registered recipes blueprint in `unified_app.py`
- ✅ Created `templates/recipes/index.html` with responsive grid layout
- ✅ API endpoint at `/api/recipes` for JSON access

### Phase 5: Post Creation Workflow (Complete)

#### 5.1 Recipe Post Creation
- ✅ Created API endpoint `/api/recipes/<recipe_week_number>/create-post` for creating recipe posts
- ✅ When creating recipe post:
  - ✅ Sets `recipe_week_number` from calendar recipe definition
  - ✅ Assigns "Scottish Recipes" category automatically
  - ✅ Assigns required tags (Scottish Recipes, Traditional Food, Seasonal Cooking)
  - ✅ Creates initial section structure with all 6 recipe section types:
    - `recipe_background` - Background section
    - `recipe_ingredients` - Ingredients section
    - `recipe_method` - Method section
    - `recipe_variants` - Variations section
    - `recipe_serving` - Serving Suggestions section
    - `recipe_gallery` - Making Process section
  - ✅ Creates `post_development` entry with idea_seed from recipe
  - ✅ Generates unique slug from recipe title
- ✅ Recipe posts can be scheduled via `calendar_week_posts` (optional year/week/weekday parameters)
- ✅ Prevents duplicate posts for the same recipe week
- ✅ UI Integration: Added "Create Post" buttons to:
  - Recipes index page (`/recipes`) - Create button on each recipe card
  - Calendar week view - Small "+" button on recipe definitions in the Recipes row
  - Both interfaces provide visual feedback and auto-reload after creation

#### 5.2 Cross-linking
- [ ] Implement cross-linking to related content:
  - Burns Night, regional pages
  - Product tie-ins (where relevant)
  - Related recipes
  - Seasonal content

### Phase 6: Newsletter Integration

#### 6.1 Newsletter Block Support
- [ ] Add recipe block type to newsletter system
- [ ] Support recipe selection for newsletter issues
- [ ] Ensure recipe posts can be featured in newsletter

### Phase 7: Testing & Validation

#### 7.1 End-to-End Testing
- [ ] Test creating first recipe post with all sections
- [ ] Test hero image generation with correct style
- [ ] Test making process image generation and display
- [ ] Test all recipe sections render properly in preview
- [ ] Test tags and categories assigned correctly
- [ ] Test weekly scheduling works via calendar system
- [ ] Test index page displays all recipes
- [ ] Test cross-linking to related content works

---

## Architecture Notes

### Recipe Identification
- Recipes are identified by `post.recipe_week_number` (1-52)
- Recipe definitions stored in `calendar_recipes` table (perpetual, week-based)
- Recipe posts scheduled via `calendar_week_posts` table

### Content Structure
- Recipe posts use standard `post` table with `recipe_week_number` set
- Recipe sections stored in `post_section` table with recipe-specific section types
- Hero image uses existing `post.header_image_id` → `image` relationship
- Making process image stored in `post_images` table linked to `recipe_gallery` section

### Voice & Style Consistency
- Warm, storytelling tone
- Heritage home cooking (not chef talk)
- Evokes place, people, and time
- Cultural notes should evoke nostalgia and authenticity

