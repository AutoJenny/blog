# Scottish Recipe Series - Implementation Roadmap

## Overview

This roadmap provides step-by-step implementation guidance for completing the Scottish Recipe Series feature. Each phase builds on the previous one, with clear deliverables and file paths.

---

## Phase 1: Content Structure & Section Types

### 1.1 Define Recipe Section Types
**File**: `docs/recipes/section-types.md`

**Tasks**:
1. Create section types documentation following `docs/profiles/section-types.md` pattern
2. Document all 6 recipe section types with purpose, content, and display specs
3. Define storage structure in `post_section` table

**Section Types to Define**:
- `recipe_background` - Historic/cultural background (2-3 paragraphs, 150-200 words)
- `recipe_ingredients` - Ingredients list (formatted clearly)
- `recipe_method` - Recipe method/steps (numbered steps)
- `recipe_variants` - Optional twists and variations (1-2 optional twists)
- `recipe_serving` - Serving suggestions and accompaniments
- `recipe_gallery` - Making process image (second image showing one step)

**Deliverable**: Complete documentation file

---

### 1.2 Post Template & Rendering
**Files**: 
- `blog-launchpad/templates/post_preview.html` (or extend existing)
- `static/css/recipes.css` (new file)

**Tasks**:
1. Review existing post preview template structure
2. Add recipe section rendering logic
3. Create recipe-specific CSS file with:
   - Ingredients list formatting (clear, readable)
   - Method/steps numbering (numbered list styling)
   - Variants section styling
   - Serving suggestions styling
   - Making process image display
4. Ensure proper display order of all recipe sections
5. Test rendering with sample recipe data

**Deliverable**: Recipe sections render correctly in post preview

---

## Phase 2: Content Generation

### 2.1 LLM Prompt Templates
**Files**: 
- Database: `llm_prompt` table entries
- Reference: `docs/recipes/llm-prompts.md` (documentation)

**Tasks**:
1. Create LLM prompt templates for each recipe section:
   - Recipe background (cultural/historic) - warm, storytelling voice
   - Recipe ingredients formatting
   - Recipe method formatting (numbered steps)
   - Recipe variants (optional twists)
   - Serving suggestions
2. Store prompts in `llm_prompt` table via SQL script
3. Create documentation file listing all prompts
4. Ensure consistent voice: warm, storytelling, heritage home cooking (not chef talk)

**Deliverable**: All LLM prompts created and documented

---

### 2.2 Image Generation
**Files**:
- Database: `image_prompt_example` table entries
- Reference: `docs/recipes/image-prompts.md` (documentation)

**Tasks**:
1. Create image prompt templates for:
   - Recipe hero images (warm, authentic Scottish, lived-in aesthetic, not stock photography)
   - Making process images (one step of recipe showing preparation/cooking)
2. Store in `image_prompt_example` table
3. Extend existing header image generation to support recipe hero image style
4. Add image generation workflow for making process images
5. Ensure both images use consistent style/voice

**Deliverable**: Image prompts created and integrated with image generation system

---

## Phase 3: Tags & Categories

### 3.1 Category & Tag Setup
**File**: `scripts/setup_recipe_tags_categories.py`

**Tasks**:
1. Create script to:
   - Create "Scottish Recipes" category (if not exists)
   - Create required tags:
     - "Scottish Recipes"
     - "Traditional Food"
     - "Seasonal Cooking"
2. Test script execution
3. Verify tags/categories in database

**Deliverable**: Tags and categories created in database

---

## Phase 4: Recipe Index Page

### 4.1 Index Page Creation
**Files**:
- `blueprints/recipes.py` (new blueprint)
- `templates/recipes/index.html` (new template)
- `static/css/recipes-index.css` (new file)

**Tasks**:
1. Create recipes blueprint with route `/recipes` or `/blog/recipes`
2. Create index template displaying all 52 recipes
3. Query `calendar_recipes` table for all recipes
4. Display in week order (1-52) with:
   - Recipe title
   - Hero image (when available)
   - Brief description
   - Week number
   - Link to full recipe post
5. Add CSS styling for recipe cards
6. Add navigation link to main blog menu

**Deliverable**: Recipe index page accessible and functional

---

## Phase 5: Post Creation Workflow

### 5.1 Recipe Post Creation
**Files**:
- `blueprints/planning_api_recipes.py` (new file)
- `scripts/create_recipe_post.py` (helper script)

**Tasks**:
1. Create API endpoint to create recipe post from calendar recipe definition
2. When creating recipe post:
   - Set `recipe_week_number` from calendar recipe definition
   - Assign "Scottish Recipes" category
   - Assign appropriate tags
   - Create initial section structure with recipe section types:
     - `recipe_background`
     - `recipe_ingredients`
     - `recipe_method`
     - `recipe_variants` (optional)
     - `recipe_serving`
     - `recipe_gallery`
   - Link to recipe definition in `calendar_recipes` table
3. Ensure recipe posts can be scheduled via `calendar_week_posts`
4. Create helper script for bulk post creation

**Deliverable**: Recipe posts can be created from calendar recipes

---

### 5.2 Cross-linking
**Files**: 
- Update post templates
- Update LLM prompts

**Tasks**:
1. Implement cross-linking in recipe content to:
   - Burns Night content
   - Regional pages
   - Product tie-ins (where relevant)
   - Related recipes
   - Seasonal content
2. Update LLM prompts to include cross-linking suggestions
3. Test cross-links work correctly

**Deliverable**: Cross-linking functional in recipe posts

---

## Phase 6: Newsletter Integration

### 6.1 Newsletter Block Support
**Files**:
- `blog-core/newsletter/` (update existing files)
- Database: `newsletter_block` table

**Tasks**:
1. Add recipe block type to newsletter system
2. Support recipe selection for newsletter issues
3. Ensure recipe posts can be featured in newsletter
4. Test newsletter generation with recipe content

**Deliverable**: Recipes can be included in newsletters

---

## Phase 7: Testing & Validation

### 7.1 End-to-End Testing
**Tasks**:
1. Test creating first recipe post with all sections
2. Test hero image generation with correct style
3. Test making process image generation and display
4. Test all recipe sections render properly in preview
5. Test tags and categories assigned correctly
6. Test weekly scheduling works via calendar system
7. Test index page displays all recipes
8. Test cross-linking to related content works

**Deliverable**: All tests pass, recipe feature fully functional

---

## Implementation Order

1. **Phase 1** (Content Structure) - Foundation for everything else
2. **Phase 3** (Tags & Categories) - Quick setup, needed early
3. **Phase 2** (Content Generation) - Enables actual content creation
4. **Phase 5** (Post Creation Workflow) - Core functionality
5. **Phase 4** (Index Page) - User-facing feature
6. **Phase 6** (Newsletter) - Enhancement
7. **Phase 7** (Testing) - Validation

---

## File Structure

```
docs/recipes/
├── implementation-roadmap.md (this file)
├── implementation-status.md
├── section-types.md (to create)
├── llm-prompts.md (to create)
└── image-prompts.md (to create)

blueprints/
├── recipes.py (to create)
└── planning_api_recipes.py (to create)

templates/recipes/
├── index.html (to create)
└── recipe_post.html (if needed)

static/css/
└── recipes.css (to create)
└── recipes-index.css (to create)

scripts/
├── setup_recipe_tags_categories.py (to create)
└── create_recipe_post.py (to create)

migrations/
└── (SQL scripts for LLM prompts, image prompts)
```

---

## Next Steps

Start with Phase 1.1: Create `docs/recipes/section-types.md`

