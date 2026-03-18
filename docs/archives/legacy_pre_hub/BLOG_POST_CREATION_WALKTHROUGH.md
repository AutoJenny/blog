# Blog Post Creation Process Walkthrough

**Date:** 2026-01-19  
**Purpose:** Step-by-step walkthrough of current blog post creation process

---

## Entry Point: Planning Ideas Page

**URL**: `/planning/posts/705/calendar/ideas?year=2026&week=4`

### Current State

1. **Page Loads**
   - Fetches post data for post_id 705
   - Reads year/week from URL parameters (2026, week 4)
   - Displays post information in header
   - Shows LLM module for expanded idea generation

2. **What User Sees**
   - Post header with week context
   - LLM prompts panel (for editing prompts)
   - LLM results panel (for generating expanded idea)
   - Generate button for expanded idea

3. **Current Flow**
   - User can generate expanded idea using LLM module
   - Expanded idea is stored in `post_development.expanded_idea`
   - User manually navigates to next stage (taxonomy or brainstorm)

---

## Process Flow Analysis

### Step 1: Ideas Selection (Current - Manual)

**Location**: `/planning/posts/<post_id>/calendar/ideas?year=<year>&week=<week>`

**What Happens**:
1. Page loads with post context
2. User can generate expanded idea (optional)
3. User manually navigates to next stage

**API Endpoints Used**:
- `GET /planning/api/posts/<post_id>` - Load post data
- `POST /planning/api/posts/<post_id>/expanded-idea` - Generate expanded idea

**Database Operations**:
- Reads from `post` table
- Reads from `post_development` table
- Updates `post_development.expanded_idea` when generated

**Next Step**: User manually clicks to taxonomy or brainstorm page

---

### Step 2: Taxonomy Assignment

**Location**: `/planning/posts/<post_id>/calendar/taxonomy?year=<year>&week=<week>`

**What Happens**:
1. User selects content category, content type, format
2. System assigns taxonomy to post
3. User proceeds to next stage

**API Endpoints Used**:
- `POST /planning/api/posts/<post_id>/taxonomy` - Save taxonomy

**Database Operations**:
- Updates `post.content_type_id`
- Updates taxonomy assignments

**Next Step**: Topic brainstorming

---

### Step 3: Topic Brainstorming

**Location**: `/planning/posts/<post_id>/concept/brainstorm?year=<year>&week=<week>`

**What Happens**:
1. System generates 50+ topic ideas using LLM
2. User selects topics to use
3. Topics stored for section allocation

**API Endpoints Used**:
- `POST /planning/api/posts/<post_id>/brainstorm` - Generate topics
- `POST /planning/api/posts/<post_id>/topics` - Save selected topics

**Database Operations**:
- Updates `post_development` with brainstormed topics
- Stores topic selections

**Next Step**: Section structure design

---

### Step 4: Section Structure Design

**Location**: `/planning/posts/<post_id>/concept/section-structure?year=<year>&week=<week>`

**What Happens**:
1. User designs content structure (sections)
2. System suggests section organization
3. Structure saved to `post_development.section_structure`

**API Endpoints Used**:
- `POST /planning/api/posts/<post_id>/section-structure` - Save structure

**Database Operations**:
- Updates `post_development.section_structure` (JSONB)

**Next Step**: Topic allocation

---

### Step 5: Topic Allocation

**Location**: `/planning/posts/<post_id>/concept/topic-allocation?year=<year>&week=<week>`

**What Happens**:
1. User allocates brainstormed topics to sections
2. System suggests allocations
3. Allocations saved

**API Endpoints Used**:
- `POST /planning/api/posts/<post_id>/topic-allocation` - Save allocations

**Database Operations**:
- Updates `post_development.topic_allocation` (JSONB)

**Next Step**: Section titling

---

### Step 6: Section Titling

**Location**: `/planning/posts/<post_id>/concept/titling?year=<year>&week=<week>`

**What Happens**:
1. User creates titles for each section
2. System suggests titles using LLM
3. Titles saved

**API Endpoints Used**:
- `POST /planning/api/posts/<post_id>/section-titling` - Save titles

**Database Operations**:
- Updates `post_development.section_order` and section headings

**Next Step**: Research (themed posts) or Drafting (others)

---

### Step 7: Research (Themed Posts Only)

**Location**: `/planning/posts/<post_id>/research`

**What Happens**:
1. User collects research sources
2. Gathers visual materials
3. Verifies facts
4. Prepares research prompts

**API Endpoints Used**:
- Various research-related endpoints

**Database Operations**:
- Stores research data in `post_development`

**Next Step**: Drafting

---

### Step 8: Drafting

**Location**: `/authoring/posts/<post_id>/sections/drafting`

**What Happens**:
1. User writes draft content for each section
2. System can assist with LLM-generated drafts
3. Drafts saved to `post_section` and `post_section_elements`

**API Endpoints Used**:
- `POST /authoring/api/posts/<post_id>/sections/draft` - Save drafts

**Database Operations**:
- Updates `post_section` table
- Updates `post_section_elements` table

**Next Step**: Image concepts

---

### Step 9: Image Concepts

**Location**: `/authoring/posts/<post_id>/sections/image-concepts`

**What Happens**:
1. User develops image concepts for sections
2. System suggests concepts
3. Concepts saved

**API Endpoints Used**:
- `POST /authoring/api/posts/<post_id>/image-concepts` - Save concepts

**Database Operations**:
- Updates `post_section` with image concepts

**Next Step**: Image prompts

---

### Step 10: Image Prompts

**Location**: `/authoring/posts/<post_id>/sections/image-prompts`

**What Happens**:
1. User generates AI image prompts
2. System creates prompts from concepts
3. Prompts saved

**API Endpoints Used**:
- `POST /authoring/api/posts/<post_id>/image-prompts` - Save prompts

**Database Operations**:
- Updates `post_section` with image prompts

**Next Step**: Image captions

---

### Step 11: Image Captions

**Location**: `/authoring/posts/<post_id>/sections/image-captions`

**What Happens**:
1. User creates captions for images
2. System suggests captions
3. Captions saved

**API Endpoints Used**:
- `POST /authoring/api/posts/<post_id>/image-captions` - Save captions

**Database Operations**:
- Updates `post_section` with image captions

**Next Step**: Image generation

---

### Step 12: Image Generation

**Location**: `/imaging/posts/<post_id>/sections/image-generation`

**What Happens**:
1. User generates AI images using prompts
2. System calls image generation API (DALL-E/SDXL)
3. Images saved to `images` table

**API Endpoints Used**:
- `POST /imaging/api/posts/<post_id>/generate-image` - Generate image

**Database Operations**:
- Creates records in `images` table
- Links images to `post_section`

**Next Step**: Image optimization

---

### Step 13: Image Optimization

**Location**: `/imaging/posts/<post_id>/sections/optimise`

**What Happens**:
1. User optimizes images (resize, compress, watermark)
2. System processes images
3. Optimized versions saved

**API Endpoints Used**:
- `POST /imaging/api/posts/<post_id>/optimise` - Optimize image

**Database Operations**:
- Updates `images` table with optimized versions

**Next Step**: Title & summary

---

### Step 14: Title & Summary

**Location**: `/header/posts/<post_id>/title-summary`

**What Happens**:
1. User generates post title and summary
2. System suggests using LLM
3. Title and summary saved

**API Endpoints Used**:
- `POST /header/api/posts/<post_id>/title-summary` - Save title/summary

**Database Operations**:
- Updates `post.title` and `post.summary`

**Next Step**: Header image

---

### Step 15: Header Image

**Location**: `/header/posts/<post_id>/header-image`

**What Happens**:
1. User creates/selects header image
2. System can generate header image
3. Image linked to post

**API Endpoints Used**:
- `POST /header/api/posts/<post_id>/header-image` - Save header image

**Database Operations**:
- Updates `post.header_image_id`

**Next Step**: SEO meta

---

### Step 16: SEO Meta

**Location**: `/header/posts/<post_id>/seo-meta`

**What Happens**:
1. User generates SEO metadata
2. System suggests meta tags
3. Metadata saved

**API Endpoints Used**:
- `POST /header/api/posts/<post_id>/seo-meta` - Save SEO data

**Database Operations**:
- Updates SEO-related fields

**Next Step**: Publishing details

---

### Step 17: Publishing Details

**Location**: `/header/posts/<post_id>/publishing-details`

**What Happens**:
1. User sets publication date/time
2. Sets author information
3. Sets post status

**API Endpoints Used**:
- `POST /header/api/posts/<post_id>/publishing` - Save publishing details

**Database Operations**:
- Updates `post.status`
- Updates publication date/time

**Next Step**: Final review

---

### Step 18: Final Review

**Location**: `/header/posts/<post_id>/preview`

**What Happens**:
1. User reviews complete post
2. Checks all content
3. Approves for publication

**API Endpoints Used**:
- Preview endpoints

**Final Status**: Post ready for publication

---

## Current Process Issues & Refinement Points

### Issue 1: Manual Navigation
- **Problem**: User must manually navigate between stages
- **Impact**: Time-consuming, error-prone
- **Refinement**: Automate navigation or provide clear "Next" buttons

### Issue 2: No Automation
- **Problem**: All stages require manual execution
- **Impact**: Cannot achieve "ready status 1 week in advance" goal
- **Refinement**: Create automation scripts to execute stages automatically

### Issue 3: Inconsistent Entry Points
- **Problem**: Different entry points for different post types
- **Impact**: Confusing for users
- **Refinement**: Standardize entry points

### Issue 4: No Progress Tracking
- **Problem**: Difficult to see overall progress
- **Impact**: Unclear what's been done, what's next
- **Refinement**: Add progress indicators

### Issue 5: Review Gates Not Clear
- **Problem**: No clear indication of when review is needed
- **Impact**: May skip important review steps
- **Refinement**: Implement review gate system

---

## Automation Opportunities

### Fully Automatable Stages
1. ✅ Taxonomy assignment (can use defaults or calendar data)
2. ✅ Topic brainstorming (LLM-generated)
3. ✅ Section structure design (LLM-generated)
4. ✅ Topic allocation (algorithm-based)
5. ✅ Section titling (LLM-generated)
6. ✅ Drafting (LLM-generated with review gate)
7. ✅ Image concepts (LLM-generated)
8. ✅ Image prompts (LLM-generated)
9. ✅ Image captions (LLM-generated)
10. ✅ Image generation (API-based)
11. ✅ Image optimization (automated processing)
12. ✅ Title & summary (LLM-generated)
13. ✅ SEO meta (LLM-generated)

### Review Gate Stages
1. ⚠️ Section structure (verify structure makes sense)
2. ⚠️ Drafting (verify content quality)
3. ⚠️ Header image (verify image quality)
4. ⚠️ Final review (comprehensive check)

---

## Recommended Refinements

### 1. Add "Next" Navigation
- Add "Next Stage" button to each page
- Automatically navigate to next substage
- Show progress indicator

### 2. Implement Automation Scripts
- Create `automated_blog_post_workflow.py`
- Execute all automatable stages
- Pause at review gates

### 3. Add Progress Tracking
- Show completion status for each stage
- Display overall progress percentage
- Highlight next required action

### 4. Standardize Entry Points
- Use one-click publication as primary entry
- Provide clear navigation paths
- Support all post types consistently

### 5. Add Review Gate System
- Mark stages requiring review
- Pause automation at review gates
- Provide approval workflow

---

## Next Steps

1. **Document current flow** ✅ (This document)
2. **Identify refinement points** ✅ (Above)
3. **Design automation scripts** (Next todo)
4. **Implement refinements** (After design)
5. **Test and iterate** (Ongoing)

---

**Last Updated:** 2026-01-19
