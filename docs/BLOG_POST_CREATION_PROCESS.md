# Blog Post Creation Process - Complete Guide

**Date:** 2026-01-19  
**Purpose:** Comprehensive guide to blog post creation process for all post types

---

## Overview

Blog posts are created through a multi-stage workflow that varies by post type. This document describes the complete process from calendar scheduling to publication-ready status.

---

## Post Types

### 1. Themed Posts
- **Source**: Calendar themes (`calendar_themes` table / JSON schedule)
- **Publication Day**: Wednesday, 14:00 (configurable)
- **Pipeline**: Full pipeline with research stage

### 2. Recipe Posts
- **Source**: Calendar recipes (`calendar_recipes` table / JSON schedule)
- **Publication Day**: Monday, 10:00 (configurable)
- **Pipeline**: Planning → Authoring → Imaging → Header (no research)

### 3. Product Profile Posts
- **Source**: Calendar profile sequence (product profiles)
- **Publication Day**: Thursday, 14:00 (configurable)
- **Pipeline**: Planning → Authoring → Imaging → Header (no research)

### 4. Surname Profile Posts
- **Source**: Calendar profile sequence (surname profiles)
- **Publication Day**: Thursday, 14:00 (configurable)
- **Pipeline**: Planning → Authoring → Imaging → Header (no research)

### 5. Family Profile Posts (Future)
- **Source**: Families table (`families` table)
- **Publication Day**: TBD (likely Thursday, 14:00)
- **Pipeline**: Planning → Authoring → Imaging → Header (with family research)

---

## Complete Workflow Stages

### Stage 1: Calendar (Themed Posts Only)

**Purpose**: Select theme/idea for the week

**Substages:**
- **view**: Calendar overview
- **week-view**: Week-specific calendar view
- **ideas-week**: Week theme selection

**Entry Point**: `/planning/posts/<post_id>/calendar/ideas?year=<year>&week=<week>`

**Key Actions:**
- Select theme from calendar
- Confirm idea selection
- Generate expanded idea

**Output**: Post created with `idea_seed` and `expanded_idea`

---

### Stage 2: Planning

**Purpose**: Structure content and develop topics

**Substages (Themed Posts):**
- **ideas**: Idea generation and selection
- **taxonomy**: Content category/type/format assignment
- **topic_brainstorming**: Generate 50+ topic ideas
- **section_structure**: Design content structure
- **topic_allocation**: Allocate topics to sections
- **section_titling**: Create section titles

**Substages (Recipe/Profile Posts):**
- **taxonomy**: Content category/type/format assignment
- **topic_brainstorming**: Generate topic ideas
- **section_structure**: Design content structure
- **topic_allocation**: Allocate topics to sections
- **section_titling**: Create section titles
- **product_data_review** (Product Profiles): Review product data
- **section_content_mapping** (Generated Posts): Map content to sections

**Entry Point**: `/planning/posts/<post_id>/calendar/ideas` (themed) or `/planning/posts/<post_id>/concept/taxonomy` (others)

**Key Actions:**
- Assign taxonomy
- Brainstorm topics
- Design section structure
- Allocate topics to sections
- Create section titles

**Output**: Structured content plan with sections and topics

---

### Stage 3: Research (Themed Posts Only)

**Purpose**: Gather research materials and sources

**Substages:**
- **research**: Research overview
- **sources**: Source collection
- **visuals**: Visual research
- **prompts**: Research prompts
- **verification**: Fact verification

**Entry Point**: `/planning/posts/<post_id>/research`

**Key Actions:**
- Collect research sources
- Gather visual materials
- Verify facts
- Prepare research prompts

**Output**: Research materials ready for authoring

---

### Stage 4: Authoring

**Purpose**: Create draft content

**Substages:**
- **drafting**: Write draft content
- **image_concepts**: Develop image concepts
- **image_prompts**: Generate image prompts
- **image_captions**: Create image captions

**Entry Point**: `/authoring/posts/<post_id>/sections/drafting`

**Key Actions:**
- Write section drafts
- Develop image concepts
- Generate image prompts
- Create captions

**Output**: Draft content with image planning

---

### Stage 5: Imaging

**Purpose**: Generate and optimize images

**Substages:**
- **image_generation**: Generate AI images
- **optimise**: Resize, compress, watermark

**Entry Point**: `/imaging/posts/<post_id>/sections/image-generation`

**Key Actions:**
- Generate images using AI
- Optimize images for web
- Apply watermarks

**Output**: Optimized images ready for publication

---

### Stage 6: Header

**Purpose**: Final content preparation

**Substages:**
- **title_summary**: Generate title and summary
- **header_image**: Create/select header image
- **seo_meta**: Generate SEO metadata
- **publishing_details**: Set publication details
- **final_review**: Final review before publication

**Entry Point**: `/header/posts/<post_id>/title-summary`

**Key Actions:**
- Generate title and summary
- Create header image
- Generate SEO metadata
- Set publication details
- Final review

**Output**: Publication-ready post

---

## Automation Goals

### Current State
- **Manual**: Posts created manually via UI
- **Automated**: Weekly content and product posts fully automated

### Target State
- **Automated Creation**: Posts created 1 week in advance
- **Automated Workflow**: All substages executed automatically
- **Ready Status**: Posts reach 'ready' status automatically
- **Review Gates**: Optional manual review at key stages

### Automation Scripts Needed
1. `scripts/automated_blog_post_creator.py` - Create posts from calendar
2. `scripts/automated_blog_post_workflow.py` - Execute workflow stages

See `docs/BLOG_POST_AUTOMATION_GOALS.md` for detailed automation plan.

---

## Process Differences by Post Type

| Stage | Themed | Recipe | Product Profile | Surname Profile | Family Profile |
|-------|--------|--------|-----------------|-----------------|----------------|
| Calendar | ✅ Yes | ❌ No | ❌ No | ❌ No | ❌ No |
| Planning | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| Research | ✅ Yes | ❌ No | ❌ No | ❌ No | ✅ Yes (family research) |
| Authoring | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| Imaging | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |
| Header | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes | ✅ Yes |

---

## Entry Points

### Manual Creation
1. **Calendar View**: `/planning/calendar?year=<year>&week=<week>`
   - Click "Create" on calendar item
   - Navigates to appropriate planning stage

2. **Planning Ideas**: `/planning/posts/<post_id>/calendar/ideas?year=<year>&week=<week>`
   - Select theme/idea
   - Confirm and create post

3. **One-Click Publication**: `/launchpad/one-click-publication?category=<category>&item_id=<id>&year=<year>&week=<week>`
   - Automated post creation interface
   - Shows pipeline stages

### Automated Creation (Future)
- Background monitor runs `automated_blog_post_creator.py`
- Creates posts 1 week in advance
- Posts start in 'draft' status

---

## Status Flow

### Manual Process
```
Not Created → Draft → In Progress → Ready → Published
```

### Automated Process (Target)
```
Calendar Schedule → Draft (auto-created) → In Progress (auto-workflow) → Ready (auto-complete) → Published (manual)
```

---

## Key Files

### Configuration
- `config/post_type_substages.py` - Stage/substage definitions
- `config/post_type_pipeline_configs.py` - Pipeline execution order
- `config/post_type_config.py` - Publication day/time configs

### Blueprints
- `blueprints/planning_calendar_clean.py` - Planning routes
- `blueprints/planning_api_posts.py` - Post creation APIs
- `blueprints/automation_core.py` - Substage execution

### Automation (To Be Created)
- `scripts/automated_blog_post_creator.py` - Post creation
- `scripts/automated_blog_post_workflow.py` - Workflow execution

---

## Related Documentation

- `docs/BLOG_POST_AUTOMATION_GOALS.md` - Automation goals and plan
- `docs/page-reference/planning/calendar-ideas.md` - Ideas page details
- `docs/post-types-implementation.md` - Post type system
- `docs/ONE_CLICK_PUBLICATION_REPORT.md` - One-click system

---

**Last Updated:** 2026-01-19
