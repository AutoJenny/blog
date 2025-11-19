# Newsletter Feature Block

## Overview

The Feature block highlights a recent blog post from the site.

**Purpose**: Showcase latest published blog post with header image and excerpt

**Status**: ✅ Implemented

**File Size Compliance**: All files under 500 lines ✅

## Code Organization

### Feature-Specific Files

| File | Lines | Purpose |
|------|-------|---------|
| `blog-core/newsletter/selectors/blog_feature.py` | 36 | Selects latest published post with header image |
| `templates/newsletter/partials/feature.html` | 29 | Email template for rendering feature block |

### Shared Services (Used by All Block Types)

| File | Lines | Purpose |
|------|-------|---------|
| `blog-core/newsletter/services/block_editor_service.py` | 142 | Editor operations (get_suggestions, apply_suggestion, save_override) |
| `blog-core/newsletter/services/block_suggestion_service.py` | 211 | Unified routing to type-specific logic |
| `templates/newsletter/partials/block_editor_base.html` | 81 | Common wrapper for all block editors |
| `templates/newsletter/partials/block_editor_universal.html` | 36 | Universal JSON editor (used for feature block) |

**Note**: The feature block uses the universal block editor (JSON editor) rather than a custom editor like intro/snapshot blocks.

## Data Sources

- Latest published blog post from `post` table
- Requires: `status='published'` and `header_image_id` (hero image)
- Joins with `images` table to get header image path

## Payload Structure

The feature block payload is stored in `newsletter_block.payload_json`:

```json
{
  "id": 123,
  "title": "Post title",
  "url": "/posts/slug",
  "excerpt": "Post summary",
  "hero_image": "/path/to/image.jpg"
}
```

## File Details

### 1. Selector: `selectors/blog_feature.py` (36 lines)

**Location**: `blog-core/newsletter/selectors/blog_feature.py`

**Main Function**: `select_feature_article() -> Optional[Dict[str, Any]]`

**Process**:
1. Queries `post` table for latest published post
2. Joins with `images` table to get header image
3. Filters: `status='published'` and `header_image_id IS NOT NULL`
4. Orders by `created_at DESC`
5. Returns dict with: `id`, `title`, `url`, `excerpt`, `hero_image`

**SQL Query**:
```sql
SELECT p.id, p.title, p.slug, p.summary, i.file_path AS hero_image
FROM post p
JOIN images i ON p.header_image_id = i.id
WHERE p.status = 'published'
ORDER BY p.created_at DESC
LIMIT 1
```

**URL Generation**:
- Uses slug if available: `/posts/{slug}`
- Falls back to ID: `/posts/{id}`

**Returns**:
- `None` if no published post with header image found
- Dict with post data if found

### 2. Template: `partials/feature.html` (29 lines)

**Location**: `templates/newsletter/partials/feature.html`

**Structure**:
- Email-safe HTML with inline styles
- Cream panel background (#fef9e7) with rounded corners
- Dark brown text (#3d2817)
- Conditional rendering: only shows if `block.title` exists

**Elements**:
1. **Title**: H2 heading with post title
2. **Hero Image**: Optional image display (if `block.hero_image` exists)
   - Max width: 560px
   - Rounded corners: 6px
   - Responsive: 100% width with max-width constraint
3. **Excerpt**: Optional excerpt text (if `block.excerpt` exists)
4. **Link**: "Read more" link to post URL (if `block.url` exists)
   - Brown color (#6b4e3d)
   - Underlined

**Styling**:
- Panel: Cream background (#fef9e7), light brown border (#e8dcc0), 8px rounded corners
- Typography: Georgia serif for headings, Arial sans-serif for body
- Spacing: 20px padding inside panel, 24px spacing between panels

### 3. Editor: Universal JSON Editor

**Location**: `templates/newsletter/partials/block_editor_base.html` (lines 59-76)

**How It Works**:
- Feature block uses the fallback JSON editor (not intro/snapshot custom editors)
- Shows current payload as JSON
- Allows manual JSON editing
- "Regenerate Suggestions" button calls `loadSuggestions()` JavaScript function

**UI Flow**:
1. User clicks "Regenerate Suggestions"
2. JavaScript calls `/newsletter/issue/{issue_id}/block/{block_id}/suggestions`
3. Backend returns latest blog post as suggestion
4. User can manually edit JSON or use suggestion

## Integration Points

### 1. Block Suggestion Service

**File**: `blog-core/newsletter/services/block_suggestion_service.py`

**Function**: `get_suggestions_for_block()` (lines 57-74)

**Process**:
1. Calls `select_feature_article()` to get latest post
2. Formats as suggestion with metadata:
   - `id`: Post ID
   - `title`: Post title
   - `excerpt`: Post summary
   - `url`: Post URL
   - `type`: 'blog_post'
3. Returns dict with:
   - `suggestions`: List with single post (or empty if none found)
   - `current`: The selected post (or None)
   - `metadata`: Empty dict

**Auto-Select**:
- `auto_select_for_block()` (line 191) returns the current post directly
- No additional formatting needed (already in correct format)

### 2. Draft Service

**File**: `blog-core/newsletter/services/draft_service.py`

**Integration**:
- Feature block is included in `block_types` list (line 46)
- Uses `auto_select_for_block()` to get latest post
- Stores payload in `newsletter_block.payload_json`

### 3. Render Template

**File**: `templates/newsletter/render.html`

**Integration**:
- Includes `feature.html` partial when `block.type == 'feature'` (line 40)
- Passes `block.payload_json` as `block` variable to partial

## API Endpoints

### Get Suggestions
```
GET /newsletter/issue/:issue_id/block/:block_id/suggestions
```

**Returns**:
```json
{
  "suggestions": [
    {
      "id": 123,
      "title": "Post title",
      "excerpt": "Post summary",
      "url": "/posts/slug",
      "type": "blog_post"
    }
  ],
  "current": {
    "id": 123,
    "title": "Post title",
    "excerpt": "Post summary",
    "url": "/posts/slug",
    "hero_image": "/path/to/image.jpg"
  },
  "metadata": {}
}
```

**Implementation**: 
`blueprints/newsletter.py::get_block_suggestions()` → 
`block_editor_service.get_suggestions()` → 
`block_suggestion_service.get_suggestions_for_block()` → 
`selectors/blog_feature.select_feature_article()`

### Apply Suggestion
```
POST /newsletter/issue/:issue_id/block/:block_id/select-suggestion
Body: {"suggestion_id": 123}
```

**Implementation**: 
`blueprints/newsletter.py::select_block_suggestion()` → 
`block_editor_service.apply_suggestion()` → 
Updates `newsletter_block.payload_json` with post data

## Suggestion Flow

1. **User clicks "Regenerate Suggestions"**
   - JavaScript calls `loadSuggestions(blockId, 'feature')`
   - Fetches from `/newsletter/issue/{issueId}/block/{blockId}/suggestions`

2. **Backend Processing**
   - `get_suggestions()` → `get_suggestions_for_block()` → `select_feature_article()`
   - `select_feature_article()` queries database for latest published post
   - Returns post data formatted as suggestion

3. **UI Display**
   - JavaScript renders suggestion in list
   - Shows "Use This" button
   - User can apply suggestion or manually edit JSON

4. **Auto-Select Behavior**
   - When auto-select enabled, latest post is automatically selected
   - Post data stored in block payload
   - No text generation needed (data is already formatted)

## Current Limitations

1. **Single Suggestion**: Only returns latest post, no alternatives
   - Future: Could fetch multiple recent posts for suggestions list

2. **No Custom Editor**: Uses universal JSON editor instead of custom UI
   - Future: Could create custom editor like intro/snapshot blocks

3. **No Image Optimization**: Uses raw image path from database
   - Future: Could optimize/resize images for email

4. **No Excerpt Generation**: Uses post summary as-is
   - Future: Could generate excerpt if summary is missing

## Testing

To test the feature block:

1. **Check for published posts with header images**:
   ```sql
   SELECT p.id, p.title, p.slug, p.summary, i.file_path
   FROM post p
   JOIN images i ON p.header_image_id = i.id
   WHERE p.status = 'published'
   ORDER BY p.created_at DESC
   LIMIT 5;
   ```

2. **Test selector directly**:
   ```python
   from newsletter.selectors.blog_feature import select_feature_article
   result = select_feature_article()
   print(f"Post: {result.get('title') if result else 'None found'}")
   ```

3. **Test via API**:
   ```bash
   curl http://localhost:5000/newsletter/issue/8/block/{block_id}/suggestions
   ```

## Future Enhancements

- [ ] Fetch multiple recent posts for suggestions (not just latest)
- [ ] Create custom editor UI (like intro/snapshot blocks)
- [ ] Generate excerpt if post summary is missing
- [ ] Image optimization for email (resize, compress)
- [ ] Cooldown tracking (don't feature same post in consecutive issues)
- [ ] Manual post selection from list
- [ ] Preview of post content in editor
