# Preview System Reference

## Overview
The preview system provides a comprehensive, content-aware preview of blog posts with support for content priority, placeholder handling, and image display. It is designed to show the current state of posts during development and provide clear feedback about missing content.

---

## Architecture
- **Canonical Route:** `/preview/<post_id>/` - The primary preview route
- **Deprecated Route:** `/blog/public/<post_id>/` - Redirects to primary route
- **Template:** `app/templates/preview_post.html` - Single canonical template
- **Processing:** `app/preview/__init__.py` - Image and content processing logic
- **Error Handling:** Graceful handling of missing images and content

---

## Routes and Templates

### Primary Preview Route
- **URL:** `/preview/<post_id>/`
- **Blueprint:** `app/preview/__init__.py`
- **Function:** `post_detail(post_id)`
- **Template:** `app/templates/preview_post.html`
- **Features:** Full content priority, image support, placeholder handling

### Deprecated Public Route
- **URL:** `/blog/public/<post_id>/`
- **Blueprint:** `app/blog/routes.py`
- **Function:** `post_public(post_id)`
- **Action:** Redirects to `/preview/<post_id>/`
- **Status:** Deprecated, maintained for backward compatibility

### Template Inheritance
```
preview_base.html (base template)
└── preview_post.html (content template)
```

---

## Content Priority System

### Priority Levels
1. **optimization** (highest quality) - Green background
2. **generation** (good quality) - Blue background  
3. **uk_british** (style-specific) - Yellow background
4. **first_draft** (basic content) - Red background
5. **placeholder** (missing content) - Gray background

### Helper Functions
- `analyze_content_priority(section)` - Determines best available content
- `get_content_class(section)` - Returns CSS class for styling
- `get_best_content(section)` - Returns the best available content
- `is_placeholder(section)` - Checks if section needs placeholder
- `get_missing_stage(section)` - Returns next missing stage

### Content Fields
- `first_draft` - Initial content
- `uk_british` - UK/British style content
- `generation` - Generated content
- `optimization` - Optimized content

---

## Image Integration

### Image Processing
**Function:** `get_post_sections_with_images(post_id)` in `app/preview/__init__.py`

### Image Field Mapping
The preview system handles two image field types:

1. **Legacy System (`image_id`):**
   ```python
   if section.get('image_id'):
       # Fetch from image table
       cur.execute("SELECT * FROM image WHERE id = %s", (section['image_id'],))
       image = cur.fetchone()
       if image:
           section_dict['image'] = dict(image)
   ```

2. **New System (`generated_image_url`):**
   ```python
   elif section.get('generated_image_url'):
       # Handle direct image URLs
       section_dict['image'] = {
           'path': section['generated_image_url'],
           'alt_text': section.get('image_captions') or 'Section image'
       }
   ```

### Template Image Rendering
```html
{% if section.image %}
<div class="section-image">
    <img src="{{ section.image.path }}" alt="{{ section.image.alt_text or 'Section image' }}" 
         onerror="this.style.display='none'; this.nextElementSibling.style.display='block';">
    <div class="image-error" style="display: none; padding: 1rem; background: #f8f9fa; border: 1px dashed #dee2e6; border-radius: 0.375rem; text-align: center; color: #6c757d;">
        <small><strong>Image not found:</strong> {{ section.image.path }}</small>
    </div>
    {% if section.image_captions %}
    <div class="image-caption">{{ section.image_captions }}</div>
    {% endif %}
    {% if section.image_prompts %}
    <div class="image-prompt">
        <small><strong>Prompt:</strong> {{ section.image_prompts }}</small>
    </div>
    {% endif %}
    {% if section.image_meta_descriptions %}
    <div class="image-notes">
        <small><strong>Notes:</strong> {{ section.image_meta_descriptions }}</small>
    </div>
    {% endif %}
</div>
{% endif %}
```

### Error Handling
- **Missing Images:** Graceful error display with image path for debugging
- **Broken URLs:** `onerror` handler hides broken images and shows error message
- **File System:** `static/uploads/images/` directory created automatically

---

## Database Integration

### Section Data Structure
```sql
SELECT 
    id, post_id, section_order, 
    section_heading,
    section_description, ideas_to_include, facts_to_include,
    first_draft, uk_british, highlighting, image_concepts,
    image_prompts, generation, optimization, watermarking,
    image_meta_descriptions, image_captions, image_prompt_example_id,
    generated_image_url, image_generation_metadata, image_id, status
FROM post_section 
WHERE post_id = %s 
ORDER BY section_order
```

### Image Fields
- `image_id` - References `image.id` (legacy system)
- `generated_image_url` - Direct file path (new system)
- `image_captions` - Image caption text
- `image_prompts` - Generation prompt used
- `image_meta_descriptions` - Additional image notes

---

## Styling and CSS

### Content Priority Indicators
```css
.content-optimization {
    background-color: #d4edda;
    border-left: 4px solid #28a745;
}

.content-generation {
    background-color: #d1ecf1;
    border-left: 4px solid #17a2b8;
}

.content-uk-british {
    background-color: #fff3cd;
    border-left: 4px solid #ffc107;
}

.content-first-draft {
    background-color: #f8d7da;
    border-left: 4px solid #dc3545;
}

.content-placeholder {
    background-color: #f8f9fa;
    border-left: 4px solid #6c757d;
}
```

### Placeholder Styling
```css
.placeholder-content {
    padding: 1.5rem;
    border: 2px dashed #dee2e6;
    border-radius: 0.375rem;
    background: repeating-linear-gradient(45deg,
            #f8f9fa,
            #f8f9fa 10px,
            #e9ecef 10px,
            #e9ecef 20px);
    margin: 1rem 0;
}
```

---

## Usage Examples

### Testing Preview
```bash
# Test working preview
curl http://localhost:5000/preview/22/

# Test deprecated route (should redirect)
curl -I http://localhost:5000/blog/public/22/
```

### Debugging Images
```bash
# Check section images in database
curl -s "http://localhost:5000/api/workflow/posts/22/sections" | jq '.sections[] | select(.generated_image_url != null) | {id, section_heading, generated_image_url}'

# Check if image file exists
ls -la static/uploads/images/section_672_20250709_105226_1d283457.png
```

---

## Removed Templates
The following unused preview templates have been removed:
- `app/templates/preview/post_preview.html` - Unused legacy template
- `app/templates/preview/preview.html` - Unused template
- `app/templates/preview/structure.html` - Unused template
- `app/templates/preview/landing.html` - Unused template
- `app/templates/preview/modular_workflow_stub.html` - Unused template

---

## Related Documentation
- **Image System:** `/docs/reference/images/new_image_system.md`
- **Database Schema:** `/docs/reference/database/schema.md`
- **API Reference:** `/docs/reference/api/current/`
- **Workflow Integration:** `/docs/reference/workflow/`

---

**Note:** The preview system is now clean and canonical. All preview functionality should use `/preview/<post_id>/` route and `preview_post.html` template. 