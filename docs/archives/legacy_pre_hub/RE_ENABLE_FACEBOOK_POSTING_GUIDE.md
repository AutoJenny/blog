# Re-Enable Facebook Posting - Safety Guide

**Date:** 2026-01-19  
**Status:** ✅ **SAFE TO RE-ENABLE** (with verification steps)

---

## Pre-Enable Verification ✅

All critical fixes have been applied and verified:

1. ✅ **970 duplicate posts cleaned up** - No duplicates remain
2. ✅ **UNIQUE constraint active** - Database prevents language post duplicates
3. ✅ **Code fixes applied** - Better error handling and duplicate detection
4. ✅ **Product post duplicates fixed** - Only one post per time slot
5. ✅ **Safeguards in place** - Multiple layers of protection

---

## Current Queue Status

**Posts Ready to Post:**
- 1 overdue post (ID 1644, weekly_word "scunner", scheduled for 09:00 today)
- All other posts are scheduled for future dates

**Safeguards Active:**
- ✅ Query-level exclusions (published posts never selected)
- ✅ Pre-posting status verification
- ✅ `platform_post_id` checks
- ✅ UNIQUE constraint on language posts
- ✅ Duplicate detection improved

---

## Steps to Re-Enable Facebook Posting

### Step 1: Review Overdue Posts

Check what will post immediately:
```bash
python3 -c "
from config.database import db_manager
from datetime import datetime, timedelta
now = datetime.now()
with db_manager.get_cursor() as cursor:
    cursor.execute('''
        SELECT pq.id, pq.content_type, pq.scheduled_timestamp,
               cp.name as product_name, ci.idea_title
        FROM posting_queue pq
        LEFT JOIN clan_products cp ON pq.product_id = cp.id
        LEFT JOIN calendar_ideas ci ON pq.idea_id = ci.id
        WHERE pq.status IN ('ready', 'pending')
        AND pq.platform = 'facebook'
        AND (
            pq.scheduled_timestamp IS NOT NULL AND pq.scheduled_timestamp <= %s
            OR (pq.scheduled_date <= CURRENT_DATE AND pq.scheduled_time IS NOT NULL)
        )
        ORDER BY COALESCE(pq.scheduled_timestamp, (pq.scheduled_date::date + pq.scheduled_time::time)::timestamp) ASC
    ''', (now + timedelta(minutes=30),))
    posts = cursor.fetchall()
    print(f'Posts that will post immediately: {len(posts)}')
    for post in posts:
        content = post['product_name'] or post['idea_title'] or post['content_type']
        print(f\"  ID: {post['id']} | {content} | Scheduled: {post['scheduled_timestamp']}\")
"
```

### Step 2: Re-Enable Posting

**File:** `scripts/posting_executor.py`

**Change:**
```python
# Line 99-100: Remove or comment out the early return
def post_to_facebook(self, post: Dict) -> Dict:
    """
    Post content to Facebook using the appropriate posting function
    Handles both product posts and weekly content posts
    """
    # ⚠️ REMOVED: Early return that disabled posting
    # logger.error(f"BLOCKED: post_to_facebook called for post_id={post.get('id')} - Facebook posting is DISABLED")
    # return {'success': False, 'error': 'Facebook posting has been disabled'}
    
    try:
        # ... rest of the function continues normally
```

### Step 3: Monitor First Post

After re-enabling:
1. Watch the logs: `tail -f logs/background_posting.log`
2. Check the queue: `http://localhost:5000/posting-queue`
3. Verify only ONE post publishes (the overdue one)
4. Confirm status changes to 'published'

### Step 4: Verify Safeguards

Run verification script:
```bash
python3 scripts/verify_posting_safeguards.py
```

Expected results:
- ✅ No duplicate posts
- ✅ Published posts not reprocessed
- ✅ Status transitions correct

---

## What Will Happen

**Immediate (within 5 minutes):**
- 1 overdue post (weekly_word "scunner") will post to Facebook
- Status will change from 'ready' → 'published'
- `platform_post_id` will be stored

**Ongoing:**
- Posts scheduled for future dates will post at their scheduled times
- Only one post per time slot
- No duplicates will be created (UNIQUE constraint prevents it)

---

## Safety Features Active

1. **UNIQUE Constraint** - Prevents duplicate language posts at database level
2. **Duplicate Detection** - Code checks before creating posts
3. **Status Verification** - Re-checks status before posting
4. **platform_post_id Check** - Prevents reposting if ID exists
5. **Query Exclusions** - Published posts never selected for processing

---

## Recommendation

✅ **SAFE TO RE-ENABLE** with the following conditions:

1. ✅ All fixes have been applied and verified
2. ✅ No duplicates remain in queue
3. ✅ UNIQUE constraint is active
4. ✅ Only 1 overdue post will post immediately
5. ✅ Monitor first few posts to confirm behavior

**Suggested Approach:**
- Re-enable posting
- Monitor the first post (overdue weekly_word)
- Verify it posts correctly and status updates
- Continue monitoring for next few hours
- If all looks good, system is fully operational

---

## Rollback Plan

If issues occur:
1. Re-add the early return in `posting_executor.py` line 99-100
2. Restart the monitor: `./stop_monitor.sh && ./start_monitor.sh`
3. Check logs for errors
4. Review queue status

---

## Post-Re-Enable Checklist

- [ ] First post published successfully
- [ ] Status updated to 'published'
- [ ] No duplicate posts created
- [ ] Future posts scheduled correctly
- [ ] Logs show no errors
- [ ] Queue view shows correct statuses
