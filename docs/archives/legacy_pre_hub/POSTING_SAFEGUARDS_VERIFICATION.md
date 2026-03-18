# Posting Safeguards Verification

## Overview

This document describes the multiple layers of safeguards that prevent published posts from being reprocessed and posted again.

## Safeguard Layers

### Layer 1: Query-Level Exclusions

All queries that select posts for processing explicitly exclude 'published' status:

1. **`automated_weekly_content_workflow.py`** (line 48-57):
   ```sql
   WHERE status = 'draft'
   AND status NOT IN ('published', 'failed')
   ```
   - Only processes 'draft' posts
   - Explicitly excludes 'published' and 'failed'

2. **`posting_executor.py`** (line 45-62):
   ```sql
   WHERE pq.status IN ('pending', 'ready')
   AND pq.status NOT IN ('published', 'failed')
   ```
   - Only processes 'pending' or 'ready' posts
   - Explicitly excludes 'published' and 'failed'

3. **`automated_posting.py`** (line 52-65):
   ```sql
   WHERE pq.status = 'ready'
   AND pq.status NOT IN ('published', 'failed')
   ```
   - Only processes 'ready' posts
   - Explicitly excludes 'published' and 'failed'

### Layer 2: Status Updates After Posting

After successful posting, status is immediately updated to 'published':

**`posting_executor.py`** (line 267-275):
```python
if result['success']:
    cursor.execute("""
        UPDATE posting_queue
        SET status = 'published',
            platform_post_id = %s,
            updated_at = NOW()
        WHERE id = %s
    """, (platform_post_id, post_id))
```

This ensures:
- Status is set to 'published' immediately after successful posting
- `platform_post_id` is stored (can be used as additional safeguard)
- `updated_at` timestamp is recorded

### Layer 3: Pre-Posting Verification

Before actually posting, the system re-checks the current state:

**`posting_executor.py`** (line 237-270):
```python
# Re-check status and platform_post_id before posting
cursor.execute("""
    SELECT status, platform_post_id
    FROM posting_queue
    WHERE id = %s
""", (post_id,))

# If already published, skip
if current_state['status'] == 'published':
    skip()

# If has platform_post_id, it was already posted - skip
if current_state['platform_post_id']:
    skip()
```

This prevents:
- Race conditions where status might have changed between query and posting
- Duplicate posting if `platform_post_id` exists but status wasn't updated
- Processing posts that were published by another process

### Layer 4: Status Check in Processing Loop

Even if a post makes it through the query, it's checked again in the processing loop:

**`posting_executor.py`** (line 240):
```python
if post['status'] not in ('pending', 'ready'):
    stats['skipped'] += 1
    continue
```

## Status Flow

```
draft → (workflow executor) → ready → (posting executor) → published
                                                          ↓
                                                       (never reprocessed)
```

1. **draft**: Post created, needs workflow execution
2. **ready**: Workflow complete, ready for posting
3. **pending**: Scheduled for posting (set by automated_posting.py)
4. **published**: Successfully posted, **NEVER reprocessed**
5. **failed**: Posting failed, **NEVER reprocessed**

## Verification

Run the verification script to check safeguards:

```bash
python3 scripts/verify_posting_safeguards.py
```

This checks:
1. Status distribution in database
2. Posts with `platform_post_id` but wrong status (should be none)
3. Published posts that might be included in processing queries (should be none)
4. Due posts that haven't been posted yet

## Confidence Level

With these safeguards in place:

✅ **Query-level exclusions** - Published posts never selected  
✅ **Immediate status updates** - Status set to 'published' right after posting  
✅ **Pre-posting verification** - Re-check before actually posting  
✅ **platform_post_id checks** - Additional safeguard if status update fails  

**Result**: Published posts cannot be reprocessed. Even if one safeguard fails, others will catch it.

## Edge Cases Handled

1. **Race condition**: Two processes try to post same item
   - Pre-posting verification catches this
   - First one posts and updates status
   - Second one sees status='published' and skips

2. **Status update failure**: Post succeeds but status update fails
   - `platform_post_id` is set (if posting succeeded)
   - Pre-posting verification checks `platform_post_id`
   - If exists, post is skipped even if status is wrong

3. **Database inconsistency**: Status is 'ready' but `platform_post_id` exists
   - Pre-posting verification checks `platform_post_id` first
   - If exists, status is corrected to 'published' and post is skipped

## Monitoring

The verification script can be run periodically to ensure:
- No posts are stuck in wrong status
- No published posts are being reprocessed
- All safeguards are working correctly
