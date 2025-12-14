# Post Type Selection Flow Report

**Date:** 2025-12-11  
**Question:** Where in the process is the post type SELECTED? It needs to be selected before it can be displayed.

---

## Executive Summary

**Post type is NOT explicitly selected in the one-click publication flow.** Instead, it is:

1. **DETERMINED from calendar item category** when creating a new post
2. **INFERRED from post database fields** when loading an existing post
3. **MAPPED from category to post_type** during post creation

**There is NO selection step** in the one-click publication page for existing posts.

---

## Post Type Determination Flow

### Scenario 1: Creating Post from Calendar Item

**Flow:**
1. User clicks "Create" button on calendar item (theme, recipe, profile, etc.)
2. Calendar item has a `category` (e.g., `'theme'`, `'recipe'`, `'profile'`)
3. Navigation: `/launchpad/one-click-publication?category=theme&item_id=123&year=2025&week=50&output=blog`
4. JavaScript loads calendar item data (includes `category`)
5. Backend API `/launchpad/one-click-publication/api/create-post-from-item` receives:
   - `category` (e.g., `'theme'`)
   - `item_id`
   - `output_channel` (e.g., `'blog'`)

**Post Type Mapping (in `blueprints/automation_core.py::create_post_from_item()`):**
```python
if category == 'theme':
    post_type = 'themed'
elif category == 'recipe':
    post_type = 'recipe'
elif category == 'weekly_word':
    post_type = 'weekly_word'
elif category == 'weekly_phrase':
    post_type = 'weekly_phrase'
elif category == 'weekly_insult':
    post_type = 'weekly_insult'
elif category == 'profile':
    # Profile already has post_id
    post_type = 'profile'
```

**Result:** Post type is **determined from category**, not selected by user.

---

### Scenario 2: Loading Existing Post

**Flow:**
1. User navigates to: `/launchpad/one-click-publication?post_id=699&output=blog`
2. No `category` parameter provided
3. JavaScript loads post data from `/planning/api/posts/699`
4. Post type is **inferred** from post database fields

**Post Type Inference (in `utils/taxonomy_helpers.py::get_post_type()`):**
```python
def get_post_type(post_id):
    cursor.execute("""
        SELECT 
            CASE 
                WHEN p.recipe_id IS NOT NULL THEN 'recipe'
                WHEN p.profile_category_id IS NOT NULL THEN 'profile'
                WHEN p.generated_source_type IS NOT NULL THEN 'generated'
                ELSE 'themed'
            END as post_type
        FROM post p
        WHERE p.id = %s
    """, (post_id,))
```

**Result:** Post type is **inferred from database fields**, not selected.

---

## Current Implementation Details

### One-Click Publication Page Load

**Location:** `templates/launchpad/one_click_publication.html`

**JavaScript Flow:**
1. Check URL parameters:
   - `post_id` → Load existing post
   - `category` + `item_id` → Load calendar item
2. If `post_id` exists:
   - Fetch post data
   - Call `/launchpad/one-click-publication/api/pipeline-status/{post_id}`
   - API determines post_type from database fields
3. If `category` exists:
   - Fetch calendar item data
   - Use `category` to determine post_type mapping

**Code Location:** `static/js/launchpad/one-click-blog-controller.js::loadCalendarItem()`

---

### Post Type Display

**Current Display:**
- Post type badge shown **after** post is loaded
- Badge appears next to title (line 90, 2292-2307)
- Badge shows: Recipe, Profile, or Themed (with icons)
- Post type selector dropdown available (as of 2025-12-11)

**Selector Order (as of 2025-12-11):**
1. **Post Selector** - "Viewing Pipeline For:" (selects which post)
2. **Channel Selector** - "Output Channel:" (selects publication destination)
3. **Post Type Selector** - "Post Type:" (selects content type within channel)

**Rationale for Order:**
- Post type is treated as a **subcategory of channel**
- Channel-first workflow: "I'm creating a blog post" → then "What type of blog post?"
- Post type determines layout and production pipeline within the selected channel
- This reflects the production workflow where channel context comes first

**Missing:**
- Post type not shown in dropdown before selection (now available via selector)
- Post type not shown in URL parameters when only `post_id` is provided
- Post type can now be overridden via selector dropdown

---

## The Problem

### Issue 1: Post Type Not Available Before Post Load

When loading `/launchpad/one-click-publication?post_id=699&output=blog`:
- Post type is unknown until post data is fetched
- Dropdown shows: `#699 — Christmas in Scotland`
- Post type badge appears **after** post loads
- **Cannot display post type in dropdown** until post is loaded

### Issue 2: No Selection Mechanism

**For existing posts:**
- Post type is **fixed** based on database fields
- Cannot change post type (e.g., convert theme to recipe)
- Post type is **determined**, not **selected**

**For new posts:**
- Post type is **determined** from calendar item category
- User doesn't explicitly select post type
- Category comes from calendar system, not user choice

---

## Where Post Type SHOULD Be Selected

### Option 1: Calendar Item Creation

**Location:** Calendar system when creating items
- User creates theme → category = `'theme'` → post_type = `'themed'`
- User creates recipe → category = `'recipe'` → post_type = `'recipe'`
- User creates profile → category = `'profile'` → post_type = `'profile'`

**Status:** ✅ Already happens - category is set when calendar item is created

### Option 2: Post Creation Modal

**Location:** `templates/includes/post_type_selection_modal.html`

**Current Behavior:**
- Modal allows selecting: Theme, Profile, Recipe
- Theme → Redirects to calendar ideas page
- Profile → Opens profile creation modal
- Recipe → Redirects to recipes page

**Status:** ✅ Exists, but doesn't directly create post with selected type

### Option 3: One-Click Publication Page

**Current Behavior:**
- Post type is **determined/inferred**, not selected
- No UI for selecting/changing post type

**Status:** ❌ **MISSING** - No selection mechanism

---

## Recommendations

### 1. Store Post Type in Database

**Add `post_type` column to `post` table:**
```sql
ALTER TABLE post ADD COLUMN post_type VARCHAR(50);
```

**Benefits:**
- Post type explicitly stored (not inferred)
- Can be displayed immediately without database queries
- Can be changed if needed
- More reliable than inferring from nullable fields

**Migration:**
- Set `post_type` based on existing fields:
  - `recipe_id IS NOT NULL` → `'recipe'`
  - `profile_category_id IS NOT NULL` → `'profile'`
  - `generated_source_type IS NOT NULL` → `'generated'`
  - Default → `'themed'`

### 2. Include Post Type in API Response

**Update `/api/posts` endpoint:**
```json
{
  "id": 699,
  "title": "Christmas in Scotland",
  "post_type": "themed",  // ← Add this
  ...
}
```

**Benefits:**
- Post type available immediately in dropdown
- Can display in dropdown: `#699 — Christmas in Scotland [Theme]`
- No need to infer from database fields

### 3. Add Post Type to URL Parameters

**When navigating to one-click publication:**
- Include `post_type` in URL: `/launchpad/one-click-publication?post_id=699&post_type=themed&output=blog`
- Or fetch post type from API and include in URL

**Benefits:**
- Post type available on page load
- Can display immediately
- No need to wait for post data fetch

### 4. Display Post Type in Dropdown

**Update dropdown format:**
```html
<option value="699">#699 — Christmas in Scotland [Theme]</option>
```

**Implementation:**
- Include `post_type` in `/api/posts` response
- Format dropdown option with post type
- Show immediately, not after post load

---

## Files That Need Changes

### 1. Database Migration
- Add `post_type` column to `post` table
- Backfill existing posts
- Update `get_post_type()` to use column instead of inference

### 2. Backend API
- `blueprints/posts.py::api_posts()` - Add `post_type` to response
- `blueprints/automation_core.py::create_post_from_item()` - Set `post_type` when creating post
- `utils/taxonomy_helpers.py::get_post_type()` - Use `post.post_type` column

### 3. Frontend Display
- `templates/launchpad/one_click_publication.html` - Update dropdown format
- Include post type in dropdown options
- Show post type immediately (not after load)

---

## Conclusion

**Answer to Question (Updated 2025-12-11):** Post type is now **SELECTABLE and OVERRIDABLE** in the one-click publication flow:

1. **Default:** Post type is **determined** from calendar item category when creating new posts, or **inferred** from post database fields when loading existing posts
2. **Override:** User can select/override post type via the "Post Type" dropdown selector
3. **Order:** Selectors appear as: Post → Channel → Post Type (reflecting channel-first workflow)

**Implementation Status:**
- ✅ Post type selector dropdown added (2025-12-11)
- ✅ Post type can be overridden by user selection
- ✅ Selector order: Post → Channel → Post Type
- ✅ Post type defaults to inferred type but can be changed
- ✅ Pipeline updates when post type changes

**Rationale for Order:**
- Post type is treated as a **subcategory of channel**
- Channel-first workflow: "I'm creating a blog post" → then "What type of blog post?"
- Post type determines layout and production pipeline within the selected channel
- This reflects the production workflow where channel context comes first

