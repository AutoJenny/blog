# Facebook Posting Bug Analysis

## Critical Bug: Infinite Posting Loop

**Date:** 2026-01-18  
**Severity:** CRITICAL  
**Impact:** Hundreds of duplicate posts sent to Facebook

## Root Cause

The `automated_weekly_content_workflow.py` script has a critical bug where it publishes posts to Facebook but **never updates the database status to 'published'** after successful posting. This causes posts to be republished every 5 minutes indefinitely.

### The Problem Flow

1. **Background Monitor** (`background_posting_monitor.sh`) runs every 5 minutes
2. It calls `automated_weekly_content_workflow.py` which processes up to 10 draft posts
3. For each post where `scheduled_datetime <= now`, it publishes directly to Facebook (line 175-209)
4. **BUG:** After successful posting, the status is NOT updated to 'published'
5. The post remains as 'draft' or gets set to 'ready' (line 216)
6. On the next run (5 minutes later), the same posts are found again
7. They are published again because their scheduled time is still in the past
8. This repeats every 5 minutes, causing hundreds of duplicate posts

### Code Location

**File:** `scripts/automated_weekly_content_workflow.py`  
**Lines:** 175-209

```python
if now >= scheduled_datetime:
    # Publishes to Facebook
    result = execute_publish_to_facebook(queue_id, {})
    if status_code == 200 and result_dict.get('success'):
        results['publish_to_facebook'] = True
        # ❌ BUG: Status is NEVER updated to 'published' here!
        # Post remains as 'draft' or 'ready'
```

### Additional Issues

1. **Double Posting Risk:** Both `automated_weekly_content_workflow.py` and `posting_executor.py` can post the same item
   - Workflow executor posts directly if time has passed
   - Posting executor queries for status 'ready' posts
   - Both can process the same post

2. **No Status Update:** After successful posting, the database status should be updated to 'published' to prevent reprocessing

3. **No Deduplication:** The workflow executor doesn't check if a post was already published before processing it

## Fix Required

1. **Update status after successful posting:**
   ```python
   if status_code == 200 and result_dict.get('success'):
       # Update status to 'published' immediately
       cursor.execute("""
           UPDATE posting_queue
           SET status = 'published',
               platform_post_id = %s,
               updated_at = NOW()
           WHERE id = %s
       """, (platform_post_id, queue_id))
   ```

2. **Check status before processing:**
   - Only process posts with status = 'draft'
   - Skip posts that are already 'published' or 'pending'

3. **Prevent double posting:**
   - Workflow executor should set status to 'pending' instead of posting directly
   - Let posting_executor handle all actual posting
   - OR: If workflow executor posts directly, it must update status immediately

## Timeline

- Background monitor runs every 5 minutes
- Each run processes up to 10 posts
- If posts have past scheduled times, they get published
- Without status update, same posts get published again next run
- Over 8 hours (night): ~96 runs × 10 posts = potentially 960+ duplicate posts

## Prevention

1. Always update status to 'published' after successful posting
2. Add status checks before processing
3. Add logging to track when posts are published
4. Consider using database transactions to prevent race conditions
5. Add unique constraints or checks to prevent duplicate posts
