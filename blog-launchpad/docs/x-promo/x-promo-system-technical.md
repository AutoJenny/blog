# Clan Post Template System - Technical Documentation

## Overview
This document details how the `clan_post_raw.html` template functions as the core HTML generator for publishing blog posts to clan.com via their blog API. The template is the single source of truth for the HTML structure that gets uploaded to the live site.

## Core Template: `clan_post_raw.html`

### Purpose
The `clan_post_raw.html` template is the primary template used to generate the exact HTML content that gets uploaded to clan.com. It's designed to produce clean, structured HTML that integrates seamlessly with clan.com's existing CSS and styling system.

### Template Location
- **File**: `blog/blog-launchpad/templates/clan_post_raw.html`
- **Usage**: Rendered by `clan_publisher.py` during the upload process
- **Output**: Raw HTML content sent to clan.com's `createPost` API

## Template Structure and Features

### 1. Post Header Section
```html
<header class="blog-post__header">
    {% if post.subtitle %}
    <p class="blog-post__subtitle">{{ post.subtitle }}</p>
    {% endif %}
    
    <div class="post-meta">
        <span class="post-meta__date">Published on <time datetime="{{ post.created_at.strftime('%Y-%m-%d') if post.created_at else 'Unknown date' }}">{{ post.created_at.strftime('%B %d, %Y') if post.created_at else 'Unknown date' }}</time></span>
        <span class="post-meta__separator"> | </span>
        <span class="post-meta__author">By Caitrin Stewart</span>
    </div>
    
    {% if post.summary %}
    <div class="blog-post__summary">
        <p>{{ post.summary }}</p>
    </div>
    {% endif %}
</header>
```

**Features:**
- Dynamic subtitle display (if available)
- Formatted publication date with proper HTML5 `<time>` element
- Author attribution (hardcoded to "Caitrin Stewart")
- Summary text display (if available)

### 2. Content Sections
```html
{% for section in sections %}
<section class="blog-section" id="section-{{ loop.index }}">
    <h2>{{ section.section_heading or 'Untitled Section' }}</h2>
    <div class="section-text">
        {% if section.polished %}
            {{ section.polished|strip_html_doc|safe }}
        {% elif section.draft %}
            {{ section.draft|strip_html_doc|safe }}
        {% elif section.content %}
            {{ section.content|strip_html_doc|safe }}
        {% else %}
            <p>No content available for this section.</p>
        {% endif %}
    </div>
</section>
{% endfor %}
```

**Content Priority System:**
1. **`section.polished`** - Highest priority, final polished content
2. **`section.draft`** - Secondary priority, draft content
3. **`section.content`** - Fallback content
4. **Fallback message** - If no content available

**HTML Processing:**
- Uses `strip_html_doc` filter to clean HTML content
- Safely renders HTML with `|safe` filter
- Generates unique section IDs for navigation

### 3. Image Handling
```html
{% if section.image and section.image.path and not section.image.placeholder %}
<figure class="section-image">
    <a title="{{ section.image_captions or section.image.alt_text or 'Section image' }}" 
       href="{{ section.image.path }}" 
       rel="lightbox[mpblog_{{ post.id }}]" 
       target="_blank">
        <img alt="{{ section.image.alt_text }}" src="{{ section.image.path }}">
    </a>
    {% if section.image_captions %}
    <figcaption>{{ section.image_captions }}</figcaption>
    {% endif %}
</figure>
{% endif %}
```

**Image Features:**
- **Conditional Display**: Only shows if image exists and has a valid path
- **Lightbox Integration**: Uses `rel="lightbox[mpblog_{{ post.id }}]"` for image galleries
- **Caption Support**: Displays `section.image_captions` in `<figcaption>` elements
- **Accessibility**: Proper `alt` text and `title` attributes
- **Responsive Design**: Images scale with CSS classes

**Critical CSS Integration:**
- **No Inline CSS**: Template relies on clan.com's external CSS system
- **Standard HTML Elements**: Uses `<figure>`, `<img>`, `<figcaption>` for semantic markup
- **CSS Classes**: `section-image` class for styling integration

### 4. Cross-Promotion Widgets
```html
{% if post.cross_promotion and post.cross_promotion.category_position == loop.index %}
    {% if post.cross_promotion.category_widget_html %}
        {{ post.cross_promotion.category_widget_html|safe }}
    {% endif %}
{% endif %}

{% if post.cross_promotion and post.cross_promotion.product_position == loop.index %}
    {% if post.cross_promotion.product_widget_html %}
        {{ post.cross_promotion.product_widget_html|safe }}
    {% endif %}
{% endif %}
```

**Widget Positioning:**
- **Category Widgets**: Inserted at specified section positions
- **Product Widgets**: Inserted at specified section positions
- **End-of-Post**: Widgets can also be positioned after all sections
- **Conditional Rendering**: Only displays if widget HTML exists

## Data Flow and Integration

### 1. Template Rendering Process
```python
# In clan_publisher.py - get_preview_html_content method
def get_preview_html_content(self, post, sections, uploaded_images=None):
    # Load template content
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'clan_post_raw.html')
    with open(template_path, 'r', encoding='utf-8') as f:
        template_content = f.read()
    
    # Create Jinja2 environment with custom filters
    env = Environment(loader=BaseLoader())
    env.filters['strip_html_doc'] = strip_html_doc
    
    # Render template with post and section data
    template = env.from_string(template_content)
    html_content = template.render(post=post, sections=sections)
    
    # Translate local image paths to clan.com URLs
    if uploaded_images:
        # Replace local paths with uploaded clan.com URLs
        for local_path, clan_url in uploaded_images.items():
            html_content = html_content.replace(f'src="{local_path}"', f'src="{clan_url}"')
            html_content = html_content.replace(f'href="{local_path}"', f'href="{clan_url}"')
    
    return html_content
```

### 2. Data Source Integration
```python
# In clan_publisher.py - publish_to_clan method
from app import get_post_sections_with_images
sections_list = get_post_sections_with_images(post['id'])

# Process images and attach paths
for i, section in enumerate(sections_list):
    section_image_path = find_section_image(full_post_data['id'], section['id'])
    if section_image_path:
        section['image'] = {'path': section_image_path}
```

**Data Sources:**
- **Post Data**: From `post` table with development metadata
- **Section Data**: From `post_section` table with image captions
- **Image Paths**: Dynamically discovered from file system
- **Cross-Promotion**: From cross-promotion configuration

### 3. Image Processing Pipeline
1. **Discovery**: `find_section_image()` locates images in file system
2. **Upload**: Images uploaded to clan.com via `uploadImage` API
3. **URL Translation**: Local paths replaced with clan.com media URLs
4. **Template Integration**: Final URLs embedded in rendered HTML

## CSS Integration Strategy

### 1. No Inline CSS Policy
**Why No Inline CSS:**
- **Conflict Prevention**: Avoids conflicts with clan.com's external CSS
- **Maintenance**: Easier to maintain and update styles globally
- **Performance**: External CSS can be cached and shared across posts
- **Consistency**: Ensures consistent styling with existing clan.com posts

### 2. CSS Class Strategy
**Template CSS Classes:**
- `mp-content std fix-me` - Main content wrapper
- `blog-post__header` - Post header styling
- `blog-section` - Section container styling
- `section-image` - Image figure styling
- `post-meta` - Metadata styling

**Integration Points:**
- **clan.com CSS**: External stylesheets handle all visual styling
- **Semantic HTML**: Template uses semantic elements for proper styling hooks
- **Responsive Design**: CSS classes enable responsive behavior

## API Integration

### 1. HTML Upload Process
```python
# Final HTML content sent to clan.com
result = self.create_or_update_post(full_post_data, html_content, is_update, uploaded_images)
```

**Upload Package:**
- **HTML Content**: Rendered template output
- **Post Metadata**: Title, URL key, categories, thumbnails
- **Image URLs**: All images uploaded and URLs translated
- **Cross-Promotion**: Widget HTML embedded in content

### 2. Content Validation
**Pre-Upload Checks:**
- Template renders successfully
- All required data present
- Image paths translated to clan.com URLs
- HTML structure valid and complete

## Template Customization

### 1. Adding New Features
**Safe Additions:**
- New HTML elements with existing CSS classes
- Additional conditional blocks
- New data fields (if supported by data source)

**Avoid:**
- Inline CSS or `<style>` tags
- JavaScript code
- External resource references
- Non-standard HTML attributes

### 2. Modifying Existing Features
**Content Display:**
- Adjust content priority logic
- Modify image display conditions
- Update cross-promotion positioning

**Structure Changes:**
- Add new section types
- Modify HTML element hierarchy
- Update CSS class assignments

## Debugging and Testing

### 1. Local Preview
**Route**: `/clan-post-html/{post_id}`
**Purpose**: Shows exact HTML that will be uploaded
**Features**: Raw HTML output for inspection

### 2. Template Validation
**Check Points:**
- Template renders without errors
- All data fields display correctly
- Images appear with proper paths
- Captions display in figcaption elements
- Cross-promotion widgets render

### 3. Live Site Verification
**Post-Upload Checks:**
- Captions visible on live site
- Images display correctly
- CSS styling applied properly
- Cross-promotion widgets functional

## Best Practices

### 1. Template Maintenance
- **Keep it Simple**: Minimal HTML, rely on CSS for styling
- **Semantic Markup**: Use proper HTML5 elements
- **Accessibility**: Include alt text and proper attributes
- **Performance**: Avoid unnecessary HTML complexity

### 2. Data Integration
- **Consistent Structure**: Maintain predictable data flow
- **Error Handling**: Graceful fallbacks for missing data
- **Validation**: Ensure data integrity before rendering

### 3. CSS Integration
- **External Dependencies**: Rely on clan.com's CSS system
- **Class Naming**: Use descriptive, consistent class names
- **Responsive Design**: Ensure mobile compatibility

## Troubleshooting

### 1. Common Issues
**Captions Not Displaying:**
- Check `section.image_captions` data in database
- Verify template uses `section.image_captions` (not `section.image.caption`)
- Ensure no inline CSS conflicts with external styles

**Images Not Loading:**
- Verify image paths in `section.image.path`
- Check image upload to clan.com completed successfully
- Confirm URL translation from local to clan.com paths

**Styling Issues:**
- Ensure no inline CSS in template
- Verify CSS classes match clan.com's system
- Check for HTML structure conflicts

### 2. Debug Tools
**Local Routes:**
- `/preview/{post_id}` - Full preview with styling
- `/clan-post-html/{post_id}` - Raw HTML for upload
- `/clan-post/{post_id}` - Formatted post display

**Logging:**
- Template rendering logs in clan_publisher.py
- Image processing logs
- API response logs

## Conclusion

The `clan_post_raw.html` template serves as the foundation for all blog post uploads to clan.com. Its design philosophy emphasizes:

1. **Clean HTML Structure**: Semantic markup that integrates with clan.com's CSS
2. **Data-Driven Content**: Dynamic content based on database and file system
3. **No CSS Conflicts**: Reliance on external CSS for consistent styling
4. **Flexible Integration**: Support for images, captions, and cross-promotion
5. **Maintainable Code**: Simple template logic that's easy to debug and modify

This template ensures that all posts published to clan.com maintain consistent structure, styling, and functionality while providing the flexibility needed for diverse content types.
