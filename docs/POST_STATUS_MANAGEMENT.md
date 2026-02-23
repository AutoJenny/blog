# Post Status Management

**Date:** 2026-02-23 (W2-FIX-4, W2-GOV-1)  
**Status:** ✅ Current — Post reuse logic excludes published posts; status transitions are canonical.

---

## Status Flow

The blog post status follows this workflow (W2-FIX-4):

```
draft → in_process → published
  │          │
  └──→ deleted   └──→ draft (revoke)
                        │
published → archived → draft | deleted
```

**Valid statuses:** `draft`, `in_process`, `published`, `archived`, `deleted`

### Status Definitions

- **`draft`**: New post created; in workflow; not ready for publish
- **`in_process`**: Marked ready; publishable (use "Mark Ready" to set)
- **`published`**: Successfully published to Clan.com (final, never reused)
- **`archived`**: Archived (final)
- **`deleted`**: Soft-deleted (terminal, never reused)

**Note:** Use `in_process` (not `in_progress`). All status writes go through `utils.posts.status_transitions.transition_post_status()`.

---

## Workflow Stage (Internal Progression)

Inside `status=draft`, posts progress through **workflow_stage** (stored in `post.extra_settings`):

```
idea → structured → drafted → imaged → essentials_complete → ready → published
```

See `docs/workflow/workflow_stage_model.md` for criteria, route gates, and integrity rules.

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

### Helper Functions

- **Status transitions:** `utils/posts/status_transitions.py` — `transition_post_status()`, `get_post_status()`, `require_post_editable()`
- **Reuse check:** `utils/post_status_helpers.py` — `can_reuse_post()`, `get_reusable_status_filter()`

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

- `docs/ARCHITECTURE_V2_OVERVIEW.md` — Architecture V2 overview
- `docs/workflow/status_transitions.md` - Status transition rules and override behaviour
- `docs/workflow/workflow_stage_model.md` - Workflow stage flow and integrity
- `docs/api/workflow_stage_api.md` - Workflow stage endpoints
- `docs/PUBLICATION_STATUS_RESOLVER_REFERENCE.md` - Status normalization
- `docs/POSTING_SAFEGUARDS_VERIFICATION.md` - Posting queue status flow
- `docs/BLOG_POST_CREATION_PROCESS.md` - Overall post creation workflow
