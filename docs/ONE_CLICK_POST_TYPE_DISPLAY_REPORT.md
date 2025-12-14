# One-Click Publication: Post Type Display Report

**Date:** 2025-12-11  
**Issue:** Should the "Viewing Pipeline For" dropdown show post type (e.g., "Theme") in addition to channel ("Blog")?

---

## Current System Architecture

### Three-Level Hierarchy

The system uses a three-level hierarchy for content management:

1. **Post Type** (WHAT) - Content category
   - `themed` - Regular themed blog posts
   - `recipe` - Recipe posts
   - `profile` / `profile_product` / `profile_surname` - Profile posts
   - `weekly_word` / `weekly_phrase` / `weekly_insult` - Weekly content
   - `generated` - AI-generated content

2. **Channel** (WHERE) - Publication destination
   - `blog` - Blog website
   - `facebook` - Facebook social media
   - `instagram` - Instagram social media
   - `twitter` - Twitter social media
   - `newsletter` - Email newsletter

3. **Content Format** (HOW) - Format within channel
   - Blog: `article`, `recipe`, `profile`, `word_of_day`
   - Facebook: `recipe`, `word_of_day`, `syndication`, `product`
   - Instagram: `word_of_day`, `carousel`, `syndication`
   - Twitter: `word_of_day`, `phrase_of_day`, `syndication`
   - Newsletter: `syndication`, `roundup`

### Database Structure

**Table:** `post_type_channel_config`
- Defines which channels and content formats each post type uses
- Unique constraint: `(post_type, channel, content_format)`
- Example: `('themed', 'blog', 'article')` means themed posts go to blog as articles

**Post Type Detection:**
- Location: `utils/taxonomy_helpers.py::get_post_type()`
- Logic:
  - `recipe_id IS NOT NULL` → `'recipe'`
  - `profile_category_id IS NOT NULL` → `'profile'`
  - `generated_source_type IS NOT NULL` → `'generated'`
  - Default → `'themed'`

---

## Current One-Click Publication Implementation

### Dropdown Display

**Location:** `templates/launchpad/one_click_publication.html` line 97

**Current Format:**
```html
<select id="pipeline-post-selector">
    <option value="699">#699 — Christmas in Scotland</option>
</select>
```

**What it shows:**
- Post ID
- Post title
- **Missing:** Post type (theme, recipe, profile, etc.)

### Post Type Badge

**Location:** Line 90, updated at line 2292-2307

**Current Display:**
- Shows post type badge **next to title** (not in dropdown)
- Badge shows: Recipe, Profile, or Themed (with icons)
- Only visible after post is selected and data loaded

**Badge Config:**
```javascript
{
    'recipe': { icon: 'fa-utensils', label: 'Recipe', ... },
    'profile': { icon: 'fa-tag', label: 'Profile', ... },
    'themed': { icon: 'fa-book', label: 'Themed', ... }
}
```

### Selector Order

**Current Order (as of 2025-12-11):**
1. **Post Selector** - "Viewing Pipeline For:" (selects which post)
2. **Channel Selector** - "Output Channel:" (selects publication destination)
3. **Post Type Selector** - "Post Type:" (selects content type within channel)

**Rationale:**
- Post type is treated as a **subcategory of channel**
- Channel-first workflow: "I'm creating a blog post" → then "What type of blog post?"
- Post type determines layout and production pipeline within the selected channel
- This reflects the production workflow where channel context comes first

### Channel Selector

**Location:** Line 114 (after Post selector, before Post Type selector)

**Current Display:**
```html
<select id="output-channel-selector">
    <option value="blog">Blog</option>
    <option value="facebook">Facebook</option>
    ...
</select>
```

**What it shows:**
- Channel name only (Blog, Facebook, etc.)
- **Missing:** Content format (article, recipe, syndication, etc.)

---

## Pipeline Loading Logic

### Current Implementation

**Function:** `loadPipelineForPostType(postId, postType)` (line 2229)

**What it does:**
1. Fetches pipeline config: `/api/post-type-pipeline/${postType}`
2. Loads steps based on **post type only**
3. **Does NOT consider output channel**

**Function:** `filterSubstagesByPostType(postType)` (line 2564)

**What it does:**
1. Fetches substages: `/launchpad/one-click-publication/api/post-types/${postType}/substages`
2. Filters substages based on **post type only**
3. **Does NOT consider output channel**

### Issue Identified

**Problem:** The pipeline is filtered by post type, but different channels may need different pipelines for the same post type.

**Example:**
- `themed` → `blog`: Full pipeline (calendar → planning → research → authoring → imaging → header)
- `themed` → `facebook`: Syndication pipeline (extract_summary → format_for_facebook → publish)

**Current behavior:** Only shows blog pipeline regardless of selected channel.

---

## API Data Available

### `/api/posts` Endpoint

**Location:** `blueprints/posts.py::api_posts()`

**Returns:**
```json
{
  "posts": [
    {
      "id": 699,
      "title": "Christmas in Scotland",
      "status": "draft",
      "created_at": "...",
      "updated_at": "...",
      "recipe_week_number": null,
      "profile_category_id": null,
      ...
    }
  ]
}
```

**Missing:** Post type is not explicitly returned, but can be inferred from:
- `recipe_week_number` → recipe
- `profile_category_id` → profile
- `generated_source_type` → generated
- Otherwise → themed

### `/planning/api/posts/{post_id}` Endpoint

**Returns:** Full post data including schedule, but post type must be determined client-side or via separate API call.

---

## Recommendations

### 0. Selector Order (IMPLEMENTED 2025-12-11)

**Order:** Post → Channel → Post Type

**Rationale:**
- Post type is treated as a **subcategory of channel**
- Channel-first workflow: "I'm creating a blog post" → then "What type of blog post?"
- Post type determines layout and production pipeline within the selected channel
- This reflects the production workflow where channel context comes first

**Implementation:**
- Selectors appear in order: "Viewing Pipeline For" → "Output Channel" → "Post Type"
- No functional dependencies between selectors (they operate independently)
- Order is organizational/cosmetic, reflecting workflow logic

### 1. Add Post Type to Dropdown Display

**Current:**
```
#699 — Christmas in Scotland
```

**Recommended:**
```
#699 — Christmas in Scotland [Theme]
```
or
```
#699 — Theme: Christmas in Scotland
```

**Rationale:**
- Post type determines which pipeline is shown
- Different post types have different substages
- User needs to know what type of content they're working with
- Currently only visible in badge after selection

### 2. Add Content Format to Channel Selector

**Current:**
```
Output Channel: Blog
```

**Recommended:**
```
Output Channel: Blog (Article)
```
or separate dropdown:
```
Output Channel: Blog
Content Format: Article
```

**Rationale:**
- Same post type + channel can have multiple formats
- Example: `recipe` → `facebook` can be `recipe` format or `syndication` format
- Format determines pipeline steps
- Currently format is implicit/unknown

### 3. Update Pipeline Loading to Consider Channel

**Current:**
- Pipeline loaded based on post type only
- Channel selector has no effect on pipeline display

**Recommended:**
- Load pipeline based on `(post_type, channel, content_format)` combination
- Use `config/output_channel_stages.py` or `post_type_channel_config` table
- Filter substages based on channel-specific config

**Implementation:**
- Update `loadPipelineForPostType()` to accept channel parameter
- Query `post_type_channel_config` for channel-specific stages
- Fallback to `post_type_substages.py` if no channel-specific config

### 4. Enhance API Response

**Add to `/api/posts`:**
- Include `post_type` field (calculated server-side)
- Include available channels for each post
- Include content formats per channel

**Example:**
```json
{
  "id": 699,
  "title": "Christmas in Scotland",
  "post_type": "themed",
  "channels": [
    {
      "channel": "blog",
      "content_format": "article",
      "is_primary": true
    },
    {
      "channel": "facebook",
      "content_format": "syndication",
      "is_primary": false
    }
  ]
}
```

---

## Files That Need Changes

### 1. Frontend Display
- `templates/launchpad/one_click_publication.html`
  - Update dropdown option format (line 1837)
  - Add content format display to channel selector
  - Update pipeline loading to use channel

### 2. Backend API
- `blueprints/posts.py::api_posts()`
  - Add post_type calculation to response
  - Add channels/content_formats to response

### 3. Pipeline Loading
- `templates/launchpad/one_click_publication.html`
  - Update `loadPipelineForPostType()` to accept channel
  - Update `filterSubstagesByPostType()` to consider channel
  - Add channel change listener

### 4. Configuration
- Verify `config/output_channel_stages.py` has all combinations
- Verify `post_type_channel_config` table has correct data

---

## Current Gaps

1. **Post type not visible in dropdown** - Only in badge after selection
2. **Content format not displayed** - Unknown which format is being used
3. **Pipeline doesn't change with channel** - Same pipeline shown regardless of channel selection
4. **API doesn't return post type** - Must be calculated client-side
5. **No channel-specific pipeline filtering** - All channels show same substages

---

## Conclusion

**Yes, the dropdown should show post type** because:
1. Post type determines which pipeline is displayed
2. Different post types have different substages
3. User needs to know content type before selecting
4. Currently only visible after selection in badge

**Additionally, content format should be shown** because:
1. Same post type + channel can have multiple formats
2. Format determines pipeline steps
3. Currently format is implicit/unknown

**The channel selector should also indicate content format** to show the complete hierarchy: Post Type → Channel → Content Format.

