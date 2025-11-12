# Product & Category Profiles: Project Summary

## Overview

This document provides a quick reference summary of the Product & Category Profiles project, linking to all detailed documentation.

## Project Goal

Create two complementary editorial profile types as weekly blog features:
- **Product Profiles** - Stories about specific products from named producers
- **Category Profiles** - Thematic features about entire product categories

Both are editorial-first, commerce-linked content that informs, inspires, and gently routes readers toward commerce.

## Documentation Structure

### 1. [Planning Document](product-category-profiles-planning.md)
**Purpose:** Original project brief and requirements  
**Contains:**
- Overview and goals
- Editorial goals
- Core distinctions between Product and Category profiles
- Structure & templates
- CMS/content model
- Workflow concept
- QA checklist
- Integration points
- Metrics for success

### 2. [Implementation Plan](product-category-profiles-implementation-plan.md)
**Purpose:** Step-by-step development guide  
**Contains:**
- 8 implementation phases with detailed tasks
- Task dependencies
- File creation/modification lists
- Time estimates
- Implementation checklist

### 3. [Implementation Thoughts](product-category-profiles-implementation-thoughts.md)
**Purpose:** Technical recommendations and architectural decisions  
**Contains:**
- Database schema recommendations
- Profile type identification
- Content structure approach
- Data integration strategies
- Calendar integration details
- Newsletter integration approach

### 4. [Data Derivation Strategy](product-category-profiles-data-derivation.md)
**Purpose:** How to extract and enrich data for profiles  
**Contains:**
- Product selection approach
- Producer information extraction
- Material/dimensions scraping
- Representative products selection (price diversity)
- Historical/cultural context research
- Resolved questions and answers

### 5. [Design & Layout](product-category-profiles-design-layout.md)
**Purpose:** Visual design, UI components, and frontend requirements  
**Contains:**
- Page structure (ASCII mockups)
- Visual design elements
- Template structure
- Tagging system
- Metadata & SEO
- Backend requirements identified from design
- Responsive design considerations
- Accessibility requirements

## Key Decisions Made

### Data Model
- ✅ Select products/categories directly from existing tables (no "product concept" grouping)
- ✅ Create `producers` table to normalize supplier information
- ✅ Scrape specifications (dimensions, materials) from product pages
- ✅ Store heritage data in `clan_categories.heritage_data` JSONB
- ✅ Use existing `post_section` system for content sections

### Calendar Integration
- ✅ Add dedicated "Profiles" row to calendar week view
- ✅ Use existing `calendar_week_posts` table (no separate table needed)
- ✅ Profile selection via modal in calendar UI

### Representative Products
- ✅ Prioritize **price diversity first**, then producer diversity, then material variety
- ✅ Select 4-8 products across price tiers
- ✅ Store product IDs in section JSONB

### Historical Context
- ✅ Use LLM analysis of aggregated product data
- ✅ Supplement with web research
- ✅ Use category hierarchy context (higher-level categories provide context)

## Implementation Phases

### Phase 1: Database Schema & Foundation (2-3 hours)
- Create `producers` table
- Extend `post` table with profile fields
- Link products to producers
- Add specifications column
- Add heritage data to categories

### Phase 2: Data Collection & Enrichment (10-12 hours)
- Build product specifications scraper
- Build producer web research function
- Build category heritage research
- Build representative products selector

### Phase 3: Content Model & Templates (8-10 hours)
- Create profile section types
- Create base profile templates
- Create profile CSS styles
- Create profile index template

### Phase 4: Calendar Integration (7-9 hours)
- Add Profiles row to calendar week view
- Extend calendar week view JavaScript
- Create profile selection API

### Phase 5: Profile Editor UI (18-24 hours)
- Create profile creation workflow
- Create profile editor interface
- Build gallery manager component
- Build representative products selector UI
- Build auto-tagging system

### Phase 6: Frontend Display (8-10 hours)
- Create profile detail routes
- Create profile index route
- Add Schema.org markup
- Add related profiles section

### Phase 7: Newsletter Integration (4-5 hours)
- Add profile block type to newsletter
- Extend newsletter autodraft

### Phase 8: Testing & Refinement (13-17 hours)
- Create test profiles
- Test data collection
- Performance testing
- Accessibility testing
- Documentation

**Total Estimated Time:** 70-80 hours (realistic)

## Database Schema Summary

### New Tables
- `producers` - Normalized producer/supplier information

### Extended Tables
- `post` - Added profile fields:
  - `profile_type`, `profile_product_id`, `profile_category_id`, `profile_producer_id`
  - `profile_producer_name`, `profile_standfirst`
  - `profile_explore_links` JSONB, `profile_quick_facts` JSONB
- `clan_products` - Added:
  - `producer_id`, `specifications` JSONB
- `clan_categories` - Added:
  - `heritage_data` JSONB, `web_researched_at`, `llm_analyzed_at`

## UI Components Summary

### Profile Pages
- Profile badges (Product/Category)
- Hero block with standfirst
- Quick facts bar (Product) / Category context bar (Category)
- Content sections (Object, Maker, Context, Materials, etc.)
- Gallery (4-6 images)
- Representative examples grid (Category)
- Explore links section
- Credits section
- Profile metadata and tags

### Editor Interface
- Product/Category selection
- Standfirst editor
- Quick facts editor
- Section content editors
- Gallery manager
- Representative products selector
- Explore links editor
- Credits editor
- Auto-tagging with override

### Calendar Integration
- Profiles row in week view
- Profile selection modal
- Profile cards in day cells

### Index Page
- Filter by type, tags, producer, category
- Search functionality
- Sort options
- Profile cards layout

## Next Steps

1. **Review all documentation** - Ensure understanding of requirements
2. **Start Phase 1** - Database schema setup
3. **Follow Implementation Plan** - Work through phases sequentially
4. **Create test profiles** - Early testing with real data
5. **Iterate based on feedback** - Refine as needed

## Questions Resolved

✅ Product selection: Direct from `clan_products` table  
✅ Producer normalization: Create `producers` table  
✅ Material/dimensions: Scrape from product pages  
✅ Representative products: Price diversity first  
✅ Historical context: LLM + web research + hierarchy context  
✅ Calendar integration: Add Profiles row to week view  
✅ Design approach: Editorial-first with tasteful CTAs  

## Open Questions

None - all key decisions have been made.

---

**Last Updated:** Based on all planning discussions and design decisions  
**Status:** Ready for implementation  
**See Implementation Plan for detailed development steps**






