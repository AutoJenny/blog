# Section-Specific Facebook Image Workaround Implementation Plan

## Overview
This workaround enables Facebook posts to display section-specific images instead of the main post image by using URL parameters and image IDs that Clan.com's server can detect and process.

## Our Implementation (Our Side)

### 1. Modify URL Generation in ClanPublisher

**File:** `blog-launchpad/clan_publisher.py`

**Function:** `_generate_url_key()`

**Current Code:**
```python
def _generate_url_key(self, post_data):
    """Generate clean URL key."""
    return self._create_clean_slug(post_data['title'])
```

**New Code:**
```python
def _generate_url_key(self, post_data):
    """Generate clean URL key with optional section parameter."""
    base_slug = self._create_clean_slug(post_data['title'])
    
    # Check if we have section-specific data
    section_id = post_data.get('section_id')
    if section_id:
        return f"{base_slug}?section={section_id}"
    else:
        return base_slug
```

**Why:** This adds `?section=710` parameters to URLs when posting specific sections, allowing Clan.com's server to detect which section is being shared.

### 2. Add Section IDs to Images in HTML Content

**File:** `templates/launchpad/clan_post_raw.html`

**Current Code:**
```html
<img src="{{ section.image.url }}" alt="{{ section.image.title }}" />
```

**New Code:**
```html
<img id="section-{{ section.id }}" src="{{ section.image.url }}" alt="{{ section.image.title }}" />
```

**Why:** This adds `id="section-710"` attributes to images, making it easy for Clan.com's server to identify which image corresponds to which section.

### 3. Update Facebook Posting Process

**File:** `blueprints/launchpad.py`

**Function:** `prepare_blog_post_data()`

**Current Code:**
```python
def prepare_blog_post_data(queue_item):
    # ... existing code ...
    return {
        'message': message,
        'link_url': link_url,
        'image_url': image_url
    }
```

**New Code:**
```python
def prepare_blog_post_data(queue_item):
    # ... existing code ...
    
    # Extract section ID from queue item if available
    section_id = queue_item.get('section_id')
    
    # Modify link_url to include section parameter
    if section_id and '?section=' not in link_url:
        link_url = f"{link_url}?section={section_id}"
    
    return {
        'message': message,
        'link_url': link_url,
        'image_url': image_url,
        'section_id': section_id
    }
```

**Why:** This ensures Facebook posts use section-specific URLs that Clan.com can detect and process.

## Clan.com Implementation (Their Side)

### 1. URL Parameter Detection

**Location:** Their header template/logic

**Implementation:**
```php
// Detect section parameter in URL
$section_id = $_GET['section'] ?? null;

if ($section_id) {
    // Look for image with matching ID in content
    $pattern = '/<img[^>]*id="section-' . $section_id . '"[^>]*src="([^"]*)"[^>]*>/i';
    if (preg_match($pattern, $post_content, $matches)) {
        $section_image_url = $matches[1];
    }
}
```

**Why:** This detects the `?section=xyz` parameter and extracts the corresponding image URL from the content.

### 2. Conditional Open Graph Tags

**Location:** Their header template

**Implementation:**
```php
// Set Open Graph image based on section
if ($section_id && isset($section_image_url)) {
    echo '<meta property="og:image" content="' . htmlspecialchars($section_image_url) . '" />';
    echo '<meta property="og:image:width" content="1200" />';
    echo '<meta property="og:image:height" content="630" />';
} else {
    // Use default post image
    echo '<meta property="og:image" content="' . htmlspecialchars($default_image) . '" />';
}
```

**Why:** This sets the appropriate Open Graph image based on the section parameter, ensuring Facebook displays the correct image.

## Updated Facebook Posting Process

### 1. Section-Specific URL Generation

**Process:**
1. **Queue Item Creation:** When creating a queue item for a specific section, include `section_id`
2. **URL Generation:** `ClanPublisher` generates URLs with `?section=xyz` parameters
3. **Image ID Assignment:** Images in HTML content get `id="section-xyz"` attributes
4. **Facebook Posting:** Use section-specific URLs for Facebook posts

### 2. Facebook Post Flow

**Step-by-Step:**
1. **User selects section** to post on Facebook
2. **System generates URL** with `?section=710` parameter
3. **Clan.com server detects** parameter and finds matching image
4. **Server sets Open Graph tags** for that specific image
5. **Facebook crawler** fetches the URL and gets section-specific image
6. **Facebook post displays** with correct section image

### 3. Technical Implementation Details

**Database Changes:**
```sql
-- Add section_id to posting_queue table
ALTER TABLE posting_queue ADD COLUMN section_id INTEGER;
```

**Queue Item Structure:**
```python
queue_item = {
    'post_id': 53,
    'section_id': 710,  # New field
    'status': 'ready',
    'message': 'Ancient Celtic Story-telling was a magical part...',
    'link_url': 'https://clan.com/blog/the-art-of-scottish-storytelling-oral-traditions-and-modern-literature?section=710'
}
```

**Facebook API Call:**
```python
# Post to Facebook with section-specific URL
result = post_to_facebook_unified(
    page_id=page['page_id'],
    access_token=page['access_token'],
    message=post_data['message'],
    link_url=post_data['link_url'],  # Now includes ?section=710
    page_name=page['name']
)
```

## Testing Strategy

### 1. Our Testing
- **Test URL generation** with section parameters
- **Verify image IDs** are added to HTML content
- **Check Facebook posting** uses correct URLs

### 2. Joint Testing
- **Test Clan.com detection** of section parameters
- **Verify Open Graph tags** are set correctly
- **Test Facebook Sharing Debugger** with section URLs
- **Confirm Facebook posts** display correct images

## Expected Results

### Before Implementation:
- **Facebook posts** always show main post image
- **No section-specific** image display
- **Generic sharing** experience

### After Implementation:
- **Facebook posts** show section-specific images
- **Accurate visual representation** of shared content
- **Better engagement** due to relevant imagery
- **Professional appearance** of social media presence

## Timeline

### Phase 1: Our Implementation (1-2 days)
- Modify `ClanPublisher` URL generation
- Add image IDs to HTML templates
- Update Facebook posting process
- Test URL generation and image ID assignment

### Phase 2: Clan.com Implementation (Their timeline)
- Implement parameter detection
- Add conditional Open Graph logic
- Test with our URLs

### Phase 3: Joint Testing (1 day)
- Test complete workflow
- Verify Facebook image display
- Refine implementation as needed

## Success Criteria

1. **URLs include section parameters** when posting specific sections
2. **Images have correct IDs** in HTML content
3. **Clan.com detects parameters** and sets appropriate Open Graph tags
4. **Facebook posts display** section-specific images
5. **Facebook Sharing Debugger** shows correct image for section URLs

This implementation provides a clean, maintainable solution that leverages existing infrastructure while enabling section-specific Facebook sharing.
