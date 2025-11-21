# Hacky Post Selection Process - Analysis

**Date:** 2025-11-20  
**Purpose:** Identify and document the hacky process for finding recent posts for newsletter/blog feature blocks

---

## Executive Summary

The current process for finding "recent" posts for newsletter feature blocks uses several **hacky workarounds** that are brittle and unreliable:

1. **Wrong table join**: Uses `images` table instead of `image_archive` table (foreign key mismatch)
2. **Incorrect date field**: Uses `created_at` instead of `first_published_at` for "recent" posts
3. **Restrictive filtering**: Only shows posts with `theme_id IS NOT NULL`, excluding profile/recipe posts
4. **No consideration of `updated_at`**: Doesn't account for recently updated posts that might be more relevant

---

## Current Implementation

### Location
- **File:** `blog-core/newsletter/selectors/blog_feature.py`
- **Functions:**
  - `select_feature_articles(limit: int = 10)` - Main function (lines 9-54)
  - `select_feature_article()` - Convenience wrapper (lines 57-64)

### Query Logic

```sql
SELECT p.id, p.title, p.slug, p.summary, i.file_path AS hero_image,
       pd.expanded_idea, p.clan_uploaded_url
FROM post p
JOIN images i ON p.header_image_id = i.id  -- ❌ WRONG TABLE
LEFT JOIN post_development pd ON p.id = pd.post_id
WHERE p.status = 'published'
  AND p.theme_id IS NOT NULL  -- ❌ EXCLUDES PROFILE/RECIPE POSTS
ORDER BY p.created_at DESC  -- ❌ WRONG DATE FIELD
LIMIT %s
```

---

## Hacky Elements Identified

### 1. Wrong Table Join: `JOIN images i` ⚠️ **CRITICAL BUG**

**Location:** Line 28 in `blog_feature.py`

**Problem:**
- `post.header_image_id` foreign key points to `image_archive.id`, NOT `images.id`
- The query joins with the wrong table, which may:
  - Return incorrect image paths
  - Fail silently if `images` table has stale data
  - Miss posts where header image exists in `image_archive` but not in `images`

**Evidence:**
- `blog-launchpad/publish/header_image_finder.py` (line 61): Uses `JOIN image_archive ia ON pi.image_id = ia.id`
- `blog-launchpad/publish/post_data_loader.py` (line 59): Uses `JOIN image_archive ia ON pi.image_id = ia.id`
- `blueprints/imaging_api_optimization.py` (line 72): Inserts into `image_archive` table
- Database schema: `post.header_image_id` foreign key constraint points to `image_archive.id`

**Impact:**
- May return posts with incorrect or missing header images
- May exclude valid posts that have header images in `image_archive` but not in `images`

**Fix Required:**
```sql
-- Change from:
JOIN images i ON p.header_image_id = i.id

-- To:
JOIN image_archive ia ON p.header_image_id = ia.id
-- And change field reference:
ia.path AS hero_image  -- Instead of i.file_path
```

---

### 2. Incorrect Date Field: `ORDER BY p.created_at DESC` ⚠️ **LOGIC ERROR**

**Location:** Line 32 in `blog_feature.py`

**Problem:**
- `created_at` is when the post was first created in the system (draft stage)
- `first_published_at` is when the post was actually published
- For "recent" posts, we should use `first_published_at` to show truly recent publications

**Evidence:**
- Database schema shows both fields exist:
  - `created_at: timestamp without time zone`
  - `first_published_at: timestamp without time zone`
  - `updated_at: timestamp without time zone`

**Example Issue:**
- Post created on 2025-01-01 but published on 2025-11-20
- Current query: Shows as "recent" based on 2025-01-01 (wrong)
- Should show: Based on 2025-11-20 (correct)

**Impact:**
- May show old posts as "recent" if they were created long ago but published recently
- May miss truly recent posts if they were created and published quickly

**Fix Required:**
```sql
-- Change from:
ORDER BY p.created_at DESC

-- To:
ORDER BY COALESCE(p.first_published_at, p.created_at) DESC
-- Or if we want to prioritize recently updated posts:
ORDER BY p.updated_at DESC, COALESCE(p.first_published_at, p.created_at) DESC
```

---

### 3. Restrictive Filtering: `AND p.theme_id IS NOT NULL` ⚠️ **FEATURE LIMITATION**

**Location:** Line 31 in `blog_feature.py`

**Problem:**
- Only shows theme posts, excluding profile and recipe posts
- If the goal is to show "recent" posts, this artificially limits the selection

**Evidence:**
- Post table has `post_type` field (theme, profile, recipe)
- Current query only returns posts with `theme_id IS NOT NULL`
- Profile and recipe posts are valid blog content that could be featured

**Impact:**
- Newsletter feature block can only showcase theme posts
- Profile and recipe posts are never featured, even if they're recent and popular

**Fix Options:**
1. **Remove filter entirely** (show all published posts):
   ```sql
   -- Remove: AND p.theme_id IS NOT NULL
   ```

2. **Use post_type instead** (more explicit):
   ```sql
   WHERE p.status = 'published'
     AND p.post_type = 'theme'  -- Explicit type check
   ```

3. **Allow multiple types** (if we want to feature profiles/recipes too):
   ```sql
   WHERE p.status = 'published'
     AND p.post_type IN ('theme', 'profile', 'recipe')
   ```

---

### 4. No Consideration of `updated_at` ⚠️ **MISSING FEATURE**

**Problem:**
- Query doesn't consider `updated_at` for recently updated posts
- A post updated yesterday might be more relevant than one published 2 weeks ago

**Impact:**
- May miss posts that were recently updated with new content
- Doesn't reflect the "freshness" of content

**Fix Option:**
```sql
-- Prioritize recently updated posts:
ORDER BY 
  CASE 
    WHEN p.updated_at > p.first_published_at + INTERVAL '7 days' 
    THEN p.updated_at 
    ELSE COALESCE(p.first_published_at, p.created_at) 
  END DESC
```

---

## Comparison with Product Selection

The product selection process (`blog-core/newsletter/selectors/products.py`) has similar issues:
- Uses `first_seen_at` instead of `clan_created_at` (now fixed with date sync)
- Uses magic number `min_product_id = 10000` (hacky)
- Uses arbitrary 60-day window

The post selection should learn from this and use proper date fields.

---

## Recommended Fixes

### Priority 1: Fix Table Join (CRITICAL)
```python
# blog-core/newsletter/selectors/blog_feature.py
cur.execute(
    """
    SELECT p.id, p.title, p.slug, p.summary, ia.path AS hero_image,
           pd.expanded_idea, p.clan_uploaded_url
    FROM post p
    JOIN image_archive ia ON p.header_image_id = ia.id  -- ✅ FIXED
    LEFT JOIN post_development pd ON p.id = pd.post_id
    WHERE p.status = 'published'
      AND p.theme_id IS NOT NULL
    ORDER BY COALESCE(p.first_published_at, p.created_at) DESC  -- ✅ FIXED
    LIMIT %s
    """,
    (limit,)
)
```

### Priority 2: Use Correct Date Field
- Replace `ORDER BY p.created_at DESC` with `ORDER BY COALESCE(p.first_published_at, p.created_at) DESC`
- Or consider `ORDER BY p.updated_at DESC` if we want recently updated posts

### Priority 3: Review Filtering Logic
- Decide if we want to include profile/recipe posts
- If yes, remove `theme_id IS NOT NULL` filter or use `post_type` instead

---

## Testing Required

After fixes:
1. Verify query returns posts with correct header images
2. Verify posts are ordered by publication date, not creation date
3. Verify all post types are included (if filter is removed)
4. Test with posts that have:
   - Header images in `image_archive` but not in `images`
   - `first_published_at` different from `created_at`
   - Different `post_type` values

---

## Related Files

- `blog-core/newsletter/selectors/blog_feature.py` - Main file to fix
- `blog-core/newsletter/services/block_suggestion_service.py` - Calls `select_feature_articles()`
- `docs/newsletter/blocks/feature.md` - Documentation (needs update after fix)

---

## Notes

- The `images` table may still exist for backward compatibility, but new images are stored in `image_archive`
- The `first_published_at` field may be NULL for older posts, so use `COALESCE()` to fall back to `created_at`
- Consider adding a `published_at` field if we need to distinguish between first publication and republishing

