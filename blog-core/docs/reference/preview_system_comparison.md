# Preview System Comparison: Legacy vs New

## Overview

This document provides a systematic side-by-side comparison of the preview functionality between the legacy blog system (`blog_old`) and the current new blog system. The comparison identifies all elements displayed in previews and maps them to their corresponding data sources in both systems.

## Data Structure Comparison

### Post Metadata

| Element | Legacy System (blog_old) | New System (blog) | Status |
|---------|-------------------------|-------------------|---------|
| **Title** | `metadata.title` | `post.title` | ✅ Available |
| **Subtitle** | `metadata.subtitle` | `post.development.subtitle` | ✅ Available |
| **Concept** | `metadata.concept` | `post.development.idea_seed` | ✅ Available |
| **Author** | `metadata.author` | `post.author` | ✅ Available |
| **Date** | `metadata.date` | `post.created_at` | ✅ Available |
| **Status** | `metadata.status` | `post.status.value` | ✅ Available |
| **Summary** | `metadata.summary` | `post.summary` | ✅ Available |
| **Tags** | `metadata.tags` | `post.tags` | ✅ Available |
| **Categories** | `metadata.categories` | `post.categories` | ❌ Missing |
| **URL Key** | `metadata.url_key` | `post.slug` | ✅ Available |

### Header Image

| Element | Legacy System (blog_old) | New System (blog) | Status |
|---------|-------------------------|-------------------|---------|
| **Image ID** | `metadata.headerImageId` | `post.header_image.id` | ✅ Available |
| **Image Path** | `metadata.headerImage.src` | `post.header_image.path` | ✅ Available |
| **Alt Text** | `metadata.headerImage.alt` | `post.header_image.alt_text` | ✅ Available |
| **Caption** | `metadata.headerImage.caption` | `post.header_image.caption` | ✅ Available |
| **Image Prompt** | `metadata.headerImage.imagePrompt` | `post.header_image.prompt` | ❌ Missing |
| **Notes** | `metadata.headerImage.notes` | `post.header_image.notes` | ❌ Missing |

### Content Sections

| Element | Legacy System (blog_old) | New System (blog) | Status |
|---------|-------------------------|-------------------|---------|
| **Section Heading** | `section.heading` | `section.section_heading` | ✅ Available |
| **Section Text** | `section.text` | `section.optimization` / `section.generation` / `section.uk_british` / `section.first_draft` | ✅ Available (Multiple versions) |
| **Section Image ID** | `section.imageId` | `section.image_id` | ✅ Available |
| **Section Image Path** | `section.image.src` | `section.image.path` | ✅ Available |
| **Section Image Alt** | `section.image.alt` | `section.image.alt_text` | ✅ Available |
| **Section Image Caption** | `section.image.caption` | `section.image_captions` | ✅ Available |
| **Section Image Prompt** | `section.image.imagePrompt` | `section.image_prompts` | ✅ Available |
| **Section Image Notes** | `section.image.notes` | `section.image_meta_descriptions` | ✅ Available |

### Conclusion

| Element | Legacy System (blog_old) | New System (blog) | Status |
|---------|-------------------------|-------------------|---------|
| **Conclusion Heading** | `metadata.conclusion.heading` | `post.conclusion_heading` | ❌ Missing |
| **Conclusion Text** | `metadata.conclusion.text` | `post.conclusion` | ✅ Available |
| **Conclusion Image ID** | `metadata.conclusion.imageId` | `post.conclusion_image.id` | ❌ Missing |
| **Conclusion Image Path** | `metadata.conclusion.image.src` | `post.conclusion_image.path` | ❌ Missing |
| **Conclusion Image Alt** | `metadata.conclusion.image.alt` | `post.conclusion_image.alt_text` | ❌ Missing |
| **Conclusion Image Caption** | `metadata.conclusion.image.caption` | `post.conclusion_image.caption` | ❌ Missing |

### Footer

| Element | Legacy System (blog_old) | New System (blog) | Status |
|---------|-------------------------|-------------------|---------|
| **Footer Content** | `metadata.footer` | `post.footer` | ✅ Available |

## Database Schema Mapping

### Legacy System Data Sources

**File-based Storage:**
- `posts/{slug}.md` - Markdown files with front matter
- `_data/image_library.json` - Image metadata and paths
- `_data/workflow_status.json` - Workflow status tracking

**Content Structure:**
```yaml
# Legacy front matter structure
title: "Post Title"
subtitle: "Post Subtitle"
concept: "Post concept/idea"
author: "author-name"
date: "2025-03-30"
summary: "<p>Post summary...</p>"
headerImageId: "IMG00001"
sections:
  - heading: "Section Title"
    text: "<p>Section content...</p>"
    imageId: "IMG00002"
conclusion:
  heading: "Conclusion"
  text: "<p>Conclusion content...</p>"
```

### New System Data Sources

**Database Tables:**
- `post` - Main post metadata
- `post_development` - Development stage data
- `post_section` - Content sections
- `post_image` - Image metadata
- `workflow_step_entity` - Workflow status

**Content Structure:**
```sql
-- New database structure
post: id, title, slug, created_at, status, summary, footer
post_development: post_id, idea_seed, subtitle, provisional_title, intro_blurb, conclusion
post_section: post_id, section_heading, optimization, generation, uk_british, first_draft, image_prompts, image_captions, image_meta_descriptions, image_id
image: id, post_id, path, alt_text, caption
```

## Missing Elements in New System

### 1. Categories
- **Legacy**: `metadata.categories` (array of category IDs)
- **New**: No equivalent field found
- **Action**: Add `categories` field to `post` table or create `post_category` junction table

### 2. Image Prompts and Notes
- **Legacy**: `imagePrompt` and `notes` fields for all images
- **New**: Available in `post_section` table as `image_prompts` and `image_meta_descriptions`
- **Status**: ✅ Available for section images, ❌ Missing for header images
- **Action**: Add `prompt` and `notes` columns to `image` table for header images

### 3. Conclusion Image
- **Legacy**: `metadata.conclusion.imageId` and related fields
- **New**: No conclusion image support
- **Action**: Add conclusion image support to `post_image` table with `image_type = 'conclusion'`

### 4. Conclusion Heading
- **Legacy**: `metadata.conclusion.heading`
- **New**: No separate conclusion heading field
- **Action**: Add `conclusion_heading` field to `post_development` table

### 5. URL Key
- **Legacy**: `metadata.url_key` for custom URL slugs
- **New**: Uses `post.slug` (auto-generated)
- **Action**: Add `url_key` field to `post` table for custom slugs

## Preview Template Comparison

### Legacy System Template Structure
```html
<!-- Legacy used Eleventy templates with front matter data -->
<article class="blog-post">
  <h1>{{ title }}</h1>
  {% if subtitle %}<div class="subtitle">{{ subtitle }}</div>{% endif %}
  <div class="meta">{{ date }} • {{ author }}</div>
  {% if summary %}<div class="summary">{{ summary | safe }}</div>{% endif %}
  
  {% for section in sections %}
  <section>
    <h2>{{ section.heading }}</h2>
    <div class="content">{{ section.text | safe }}</div>
    {% if section.imageId %}<img src="{{ section.image.src }}" alt="{{ section.image.alt }}">{% endif %}
  </section>
  {% endfor %}
  
  {% if conclusion %}
  <section class="conclusion">
    <h2>{{ conclusion.heading }}</h2>
    <div class="content">{{ conclusion.text | safe }}</div>
  </section>
  {% endif %}
</article>
```

### New System Template Structure
```html
<!-- New system uses Flask templates with database data -->
<article class="blog-post">
  <h1>{{ post.title }}</h1>
  {% if post.development.subtitle %}<div class="subtitle">{{ post.development.subtitle }}</div>{% endif %}
  <div class="meta">{{ post.created_at.strftime('%B %d, %Y') }}</div>
  {% if post.summary %}<div class="summary">{{ post.summary | safe }}</div>{% endif %}
  
  {% for section in sections %}
  <section>
    <h2>{{ section.section_heading }}</h2>
    <div class="content">
      {% if section.optimization %}{{ section.optimization | safe }}{% endif %}
      {% if section.generation %}{{ section.generation | safe }}{% endif %}
      {% if section.uk_british %}{{ section.uk_british | safe }}{% endif %}
      {% if section.first_draft %}{{ section.first_draft | safe }}{% endif %}
    </div>
    {% if section.image %}<img src="{{ section.image.path }}" alt="{{ section.image.alt_text }}">{% endif %}
  </section>
  {% endfor %}
  
  {% if post.conclusion %}
  <section class="conclusion">
    <h2>Conclusion</h2>
    <div class="content">{{ post.conclusion | safe }}</div>
  </section>
  {% endif %}
</article>
```

## Implementation Recommendations

### Phase 1: Core Missing Elements
1. **Add missing database fields:**
   - `image.prompt` (TEXT) - for header images
   - `image.notes` (TEXT) - for header images  
   - `post_development.conclusion_heading` (VARCHAR)
   - `post.categories` (JSONB or separate junction table)

2. **Add conclusion image support:**
   - Extend `image` table to support conclusion images
   - Update preview template to display conclusion images

3. **Add URL key support:**
   - Add `post.url_key` field for custom slugs
   - Update slug generation logic

### Phase 2: Enhanced Preview Features
1. **Improve section content display:**
   - Add logic to choose best content version (optimization > generation > uk_british > first_draft)
   - Add content version selector in preview

2. **Add image metadata display:**
   - Show image prompts and notes in preview
   - Add image metadata panel

3. **Add social media metadata:**
   - Display social media captions and hashtags
   - Add social media preview panel

### Phase 3: Advanced Features
1. **Add content validation:**
   - Validate required fields are present
   - Show validation status in preview

2. **Add publishing readiness check:**
   - Check all required elements are complete
   - Show publishing status and requirements

3. **Add preview customization:**
   - Allow different preview modes (draft, final, social)
   - Add preview settings and options

## Database Schema Updates Required

```sql
-- Add missing fields to existing tables
ALTER TABLE image ADD COLUMN prompt TEXT;
ALTER TABLE image ADD COLUMN notes TEXT;
ALTER TABLE post_development ADD COLUMN conclusion_heading VARCHAR(255);
ALTER TABLE post ADD COLUMN categories JSONB;

-- Add conclusion image support (extend existing image table)
-- No schema change needed - use existing image table with conclusion images

-- Add URL key support
ALTER TABLE post ADD COLUMN url_key VARCHAR(255);
CREATE INDEX idx_post_url_key ON post(url_key);
```

## Migration Strategy

1. **Immediate**: Add missing database fields and update preview template
2. **Short-term**: Implement conclusion image support and URL key functionality
3. **Medium-term**: Add enhanced preview features and validation
4. **Long-term**: Add advanced preview customization and publishing readiness checks

This comparison provides a roadmap for bringing the new preview system to parity with the legacy system while leveraging the improved database structure and workflow integration of the new system. 