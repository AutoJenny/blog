# Weekly Social Post Creation Audit

**Date:** 2025-12-18  
**Purpose:** Identify all places where `posting_queue` rows are (or could be) created for weekly word/phrase/insult Content Items, and determine if they populate `idea_id`.

---

## Executive Summary

**Current State:** No weekly social posts exist in `posting_queue` table.  
**Finding:** Weekly social posts are not currently being created automatically or manually.  
**Recommendation:** When weekly social post creation is implemented, ensure all creation points use `create_weekly_social_post()` helper or explicitly set `idea_id`.

---

## Database Query Results

**Query:** Count of weekly social posts in `posting_queue` by `content_type`:
```sql
SELECT content_type, COUNT(*) as count, 
       COUNT(CASE WHEN idea_id IS NOT NULL THEN 1 END) as with_idea_id,
       COUNT(CASE WHEN idea_id IS NULL THEN 1 END) as without_idea_id
FROM posting_queue
WHERE content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult')
GROUP BY content_type
```

**Result:** No rows found. No weekly social posts currently exist.

---

## Codebase Analysis: All `posting_queue` INSERT Points

### 1. Product Posts (Not Weekly Content)

#### 1.1 `blueprints/launchpad_content.py::save_generated_content()`
- **Line:** ~58
- **Content Type:** `product` (from `product_id` parameter)
- **Handles Weekly Content?** ❌ No
- **Current Behavior:** 
  ```python
  INSERT INTO posting_queue (product_id, content_type, generated_content, status, created_at, updated_at)
  VALUES (%s, %s, %s, 'draft', NOW(), NOW())
  ```
- **Action Required:** None (product posts use `product_id`, not `idea_id`)

#### 1.2 `blueprints/launchpad_content.py::save_generated_content()` (duplicate endpoint)
- **Line:** ~585
- **Content Type:** `product`
- **Handles Weekly Content?** ❌ No
- **Action Required:** None

#### 1.3 `blueprints/launchpad/blog_post_syndication.py::generate_blog_content()`
- **Line:** ~476
- **Content Type:** Blog post syndication (uses `post_id`)
- **Handles Weekly Content?** ❌ No
- **Current Behavior:**
  ```python
  INSERT INTO posting_queue (
      post_id, content_type, generated_content, 
      post_title, status, platform, channel_type,
      created_at, updated_at
  )
  VALUES (%s, %s, %s, %s, 'draft', 'facebook', 'feed_post', NOW(), NOW())
  ```
- **Action Required:** None (blog syndication uses `post_id`, not `idea_id`)

#### 1.4 `blueprints/launchpad/blog_post_syndication.py::save_blog_content()`
- **Line:** ~554
- **Content Type:** Blog post syndication (uses `post_id`)
- **Handles Weekly Content?** ❌ No
- **Action Required:** None

#### 1.5 `blueprints/launchpad/instagram_carousel.py`
- **Line:** ~1116
- **Content Type:** Instagram carousel (uses `product_id` or `post_id`)
- **Handles Weekly Content?** ❌ No (likely product or blog post carousels)
- **Action Required:** None

#### 1.6 Legacy/Backup Files
- `blueprints/launchpad_old.py` - Legacy code, not in active use
- `blueprints/launchpad_monolithic_backup.py` - Backup file, not in active use
- `blog-launchpad/app_deprecated.py` - Deprecated code

**Action Required:** None (these are not active)

---

### 2. Weekly Content Handling (No Current Creation)

#### 2.1 `blueprints/automation_core.py::create_post_from_item()`
- **Lines:** 321-322, 352-353, 408, 458-465, 533-540, 631
- **Handles Weekly Content?** ✅ Yes (detects weekly_word/phrase/insult)
- **Creates `posting_queue` Rows?** ❌ No
- **Current Behavior:**
  - Detects weekly content types (`weekly_word`, `weekly_phrase`, `weekly_insult`)
  - Checks if content format requires a blog post
  - If format is social-only (e.g., `word_of_day`), returns early without creating blog post
  - **Does NOT create `posting_queue` row** - only handles blog post creation logic
- **Code Snippet:**
  ```python
  if content_format and not requires_post(output_channel, content_format):
      # This is a social media-only format (e.g., word_of_day on Facebook)
      # Don't create a blog post, just return success with channel info
      return jsonify({
          "success": True,
          "post_id": None,
          "message": f"Content ready for {output_channel} ({content_format} format). No blog post needed.",
          ...
      })
  ```
- **Action Required:** 
  - ⚠️ **Future Implementation:** When weekly social post creation is added here, use `create_weekly_social_post()` helper
  - Need to determine `idea_id` from `item_id` (which is `calendar_ideas.id` for weekly content)
  - Need to determine platform from `output_channel` (e.g., `output_channel='facebook'` → `platform='facebook'`)

#### 2.2 `blueprints/planning_api_calendar_social_focus.py`
- **Purpose:** Manages `weekly_social_focus` table (day-of-week social focus themes)
- **Creates `posting_queue` Rows?** ❌ No
- **Handles Weekly Content?** ❌ No (different concept - social focus themes, not weekly word/phrase/insult)
- **Action Required:** None

---

### 3. Potential Creation Points (Not Yet Implemented)

#### 3.1 Automation Scripts
- **Files Checked:**
  - `blueprints/automation_execute.py` - Handles blog post automation, not social posts
  - `blueprints/automation_pipeline.py` - Not examined in detail, but likely blog-focused
  - `blueprints/automation_calendar.py` - Hard-disabled (410 responses)
- **Finding:** No automation scripts currently create weekly social posts
- **Action Required:** When automation is implemented, use `create_weekly_social_post()` helper

#### 3.2 Manual UI Flows
- **Potential Locations:**
  - One-click publication page (`/launchpad/one-click-publication`)
  - Publication dashboard (`/planning/calendar?tab=publication-schedule`)
  - Future weekly content management UI
- **Finding:** No UI currently creates weekly social posts
- **Action Required:** When UI is implemented, ensure backend endpoint uses `create_weekly_social_post()` helper

---

## Recommended Implementation Pattern

When weekly social post creation is implemented, follow this pattern:

### Pattern 1: Using Helper Function (Recommended)

```python
from utils.posting_queue_helpers import create_weekly_social_post

# Determine idea_id from item_id (for weekly content, item_id IS calendar_ideas.id)
idea_id = int(item_id)  # item_id is already calendar_ideas.id for weekly content

# Determine platform from output_channel
platform = output_channel.lower()  # e.g., 'facebook', 'instagram', 'twitter'

# Create social post
queue_id = create_weekly_social_post(
    idea_id=idea_id,
    content_type=category,  # 'weekly_word', 'weekly_phrase', or 'weekly_insult'
    platform=platform,
    generated_content=generated_content,
    status='draft',
    scheduled_date=scheduled_date,  # Optional
    scheduled_time=scheduled_time,  # Optional
    cursor=cursor  # If in transaction
)
```

### Pattern 2: Direct INSERT (If Helper Can't Be Used)

```python
# Only if helper can't be used (e.g., complex transaction logic)
cursor.execute("""
    INSERT INTO posting_queue (
        idea_id,  -- REQUIRED for weekly content
        content_type,
        platform,
        generated_content,
        status,
        scheduled_date,  -- Optional
        scheduled_time,  -- Optional
        created_at,
        updated_at
    )
    VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
    RETURNING id
""", (idea_id, content_type, platform, generated_content, status, scheduled_date, scheduled_time))
```

**Critical:** Always set `idea_id` for weekly content. Never leave it NULL.

---

## Action Items Summary

### Immediate (No Action Needed)
- ✅ All existing `posting_queue` INSERT statements are for products or blog syndication
- ✅ No weekly social posts currently exist
- ✅ Helper function `create_weekly_social_post()` is ready for use

### Future Implementation (When Weekly Social Posts Are Added)

1. **`blueprints/automation_core.py::create_post_from_item()`**
   - When social-only format is detected, create `posting_queue` row using helper
   - Extract `idea_id` from `item_id` (which is `calendar_ideas.id` for weekly content)
   - Extract `platform` from `output_channel`

2. **Any New Automation Scripts**
   - Use `create_weekly_social_post()` helper
   - Ensure `idea_id` is determined from rotation JSON or explicit selection

3. **Any New UI Endpoints**
   - Backend should use `create_weekly_social_post()` helper
   - Frontend should pass `item_id` (which is `calendar_ideas.id` for weekly content)

4. **Validation**
   - Add validation: if `content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult')`, then `idea_id IS NOT NULL`
   - Consider database constraint: `CHECK (content_type NOT IN ('weekly_word', 'weekly_phrase', 'weekly_insult') OR idea_id IS NOT NULL)`

---

## Testing Checklist (For Future Implementation)

When weekly social post creation is implemented, verify:

- [ ] `idea_id` is populated for all weekly social posts
- [ ] `content_type` matches the weekly type (`weekly_word`, `weekly_phrase`, `weekly_insult`)
- [ ] `idea_id` points to valid `calendar_ideas.id`
- [ ] `calendar_ideas.item_classification` matches `posting_queue.content_type`
- [ ] Social posts appear in publication dashboard with correct linkage
- [ ] `SocialOutputView` correctly maps `idea_id` to `content_item_id`

---

## Notes

- **Backward Compatibility:** Existing weekly social posts (if any are created before this audit) will have `idea_id=NULL`. The `SocialOutputView` handles this gracefully, but linkage won't work until backfilled.
- **Helper Function:** `utils/posting_queue_helpers.py::create_weekly_social_post()` is ready and tested. Use it for all new weekly social post creation.
- **Database Constraint:** Consider adding a CHECK constraint to enforce `idea_id IS NOT NULL` for weekly content types (optional, but recommended for data integrity).

