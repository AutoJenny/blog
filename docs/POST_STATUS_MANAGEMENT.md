# Post Status Management

**Date:** 2025-01-19  
**Status:** ✅ **FIXED** - Post reuse logic now correctly excludes published posts

---

## Status Flow

The blog post status follows this workflow:

```
draft → in_progress → needs_review → ready → published
```

### Status Definitions

- **`draft`**: New post created, initial state
- **`in_process`**: Post is being actively worked on
- **`published`**: Post has been published (final state, never reused)
- **`deleted`**: Post has been soft-deleted (final state, never reused)
- **`archived`**: Post has been archived (final state, never reused)

---

## Post Reuse Rules

### ✅ **Posts That CAN Be Reused**

Only posts in **workflow states** can be reused when creating new posts from calendar items:

- `draft`
- `in_process`

**Rationale:** These posts are still in the workflow and can be continued/updated.

### ❌ **Posts That CANNOT Be Reused**

Posts in **final states** are **never reused** - a new draft post is always created instead:

- `published` - Post is live, cannot be modified
- `deleted` - Post was deleted, should not be reused
- `archived` - Post was archived, should not be reused

**Rationale:** Published posts are immutable. Reusing them would cause status confusion and data integrity issues.

---

## Implementation

### SQL Filter Pattern

All post reuse queries use this pattern:

```sql
WHERE ...
  AND p.status IN ('draft', 'in_process')
```

**Never use:**
```sql
WHERE ...
  AND p.status != 'deleted'  -- ❌ WRONG - allows published posts
```

### Helper Function

Use `utils/post_status_helpers.py` for consistent status validation:

```python
from utils.post_status_helpers import can_reuse_post, get_reusable_status_filter

# Check if a post can be reused
if can_reuse_post(post_status):
    # Reuse post
    pass

# Get SQL filter condition
status_filter = get_reusable_status_filter()
# Returns: "status IN ('draft', 'in_process')"
```

---

## Fixed Locations

The following functions were updated to exclude published posts:

1. **`blueprints/planning_api_posts.py::confirm_calendar_idea()`**
   - Fixed post lookup when confirming calendar ideas
   - Now only reuses workflow-state posts

2. **`blueprints/automation_core.py::create_post_from_item()`**
   - Fixed recipe post lookup
   - Fixed theme post lookup
   - Fixed weekly content post lookup

3. **`blueprints/automation_calendar.py`**
   - Fixed theme post lookup

---

## Root Cause Analysis

### Problem

Previously, post reuse logic only checked `status != 'deleted'`, which meant:
- Published posts could be reused
- New posts would incorrectly show `status='published'`
- Data integrity issues when editing published content

### Solution

Changed all reuse queries to explicitly check for workflow states:
```sql
AND p.status IN ('draft', 'in_process')
```

This ensures:
- Published posts are never reused
- New posts always start as `draft`
- Status correctly reflects post state throughout workflow

---

## Verification

To verify the fix:

1. **Check existing published posts:**
   ```sql
   SELECT id, title, status, clan_post_id 
   FROM post 
   WHERE status = 'published' 
   LIMIT 10;
   ```

2. **Create a new post from a calendar item:**
   - Should create a new `draft` post
   - Should NOT reuse an existing `published` post

3. **Check logs:**
   - Look for "Reusing existing post" messages
   - Verify they only appear for workflow-state posts

---

## Related Documentation

- `docs/PUBLICATION_STATUS_RESOLVER_REFERENCE.md` - Status normalization
- `docs/POSTING_SAFEGUARDS_VERIFICATION.md` - Posting queue status flow
- `docs/BLOG_POST_CREATION_PROCESS.md` - Overall post creation workflow
