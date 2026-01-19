# CRITICAL BUG: Duplicate Language Posts Created

**Date:** 2026-01-19  
**Severity:** 🔴 **CRITICAL**  
**Status:** ⚠️ **IDENTIFIED - FIX REQUIRED**

---

## Executive Summary

**624 duplicate language posts** were created on 2026-01-18:
- 208 duplicate `weekly_word` posts
- 208 duplicate `weekly_phrase` posts  
- 208 duplicate `weekly_insult` posts

**Root Cause:** The duplicate check in `automated_weekly_content_creator.py` failed due to a **race condition** or **transaction isolation issue**.

**Impact:** If Facebook posting were enabled, this would have resulted in **624 duplicate posts** being published to Facebook.

---

## Detailed Analysis

### Duplicate Pattern

**Example:** Idea ID 1091 (`weekly_word`) for date 2026-01-18:
- **104 duplicate posts created**
- First created: `2026-01-18 09:33:48`
- Last created: `2026-01-18 23:58:22`
- **Span:** ~14 hours of continuous duplicate creation

**All duplicates:**
- `idea_id=1091` (weekly_word): 104 duplicates
- `idea_id=1234` (weekly_phrase): 104 duplicates
- `idea_id=1187` (weekly_phrase): 104 duplicates
- `idea_id=1293` (weekly_insult): 104 duplicates
- `idea_id=1294` (weekly_insult): 104 duplicates

**Total:** 520 duplicate posts (624 total - 104 unique = 520 duplicates)

---

## Root Cause Analysis

### Current Duplicate Check

**Location:** `scripts/automated_weekly_content_creator.py` lines 54-72

```python
def check_existing_post(self, idea_id: int, content_type: str, platform: str, scheduled_date: str) -> bool:
    try:
        with self.db_manager.get_cursor() as cursor:
            cursor.execute("""
                SELECT id FROM posting_queue
                WHERE idea_id = %s
                AND content_type = %s
                AND platform = %s
                AND scheduled_date = %s
            """, (idea_id, content_type, platform, scheduled_date))
            
            result = cursor.fetchone()
            return result is not None
    except Exception as e:
        logger.error(f"Error checking existing post: {e}")
        return False  # ⚠️ BUG: Returns False on error, allowing duplicates
```

### Why It Failed

1. **Race Condition:**
   - Script runs every 5 minutes
   - Multiple instances might run simultaneously
   - Check happens, then insert happens - gap allows duplicates

2. **Transaction Isolation:**
   - Check uses separate transaction
   - Insert uses separate transaction
   - No locking mechanism

3. **Error Handling:**
   - If check fails (exception), returns `False`
   - This allows post creation even when check fails

4. **No Database Constraint:**
   - No UNIQUE constraint on `(idea_id, content_type, platform, scheduled_date)`
   - Database allows duplicates

---

## Current Safeguards (Insufficient)

### ✅ Existing Safeguards
1. **Query-level exclusions** - Prevents reprocessing published posts
2. **Status checks** - Prevents duplicate publishing
3. **Platform post ID checks** - Prevents duplicate posting

### ❌ Missing Safeguards
1. **No database UNIQUE constraint** - Database allows duplicates
2. **No transaction locking** - Race conditions possible
3. **No atomic check-and-insert** - Gap between check and insert
4. **Error handling allows duplicates** - Returns False on error

---

## Required Fixes

### 1. **Add Database UNIQUE Constraint** (CRITICAL)

```sql
ALTER TABLE posting_queue
ADD CONSTRAINT posting_queue_unique_language_post
UNIQUE (idea_id, content_type, platform, scheduled_date)
WHERE idea_id IS NOT NULL 
  AND content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult');
```

**Benefit:** Database-level prevention of duplicates

### 2. **Fix Duplicate Check with Atomic Operation**

```python
def check_existing_post(self, idea_id: int, content_type: str, platform: str, scheduled_date: str) -> bool:
    """
    Check if a posting_queue entry already exists (atomic with lock)
    """
    try:
        with self.db_manager.get_cursor() as cursor:
            # Use SELECT FOR UPDATE to lock row (prevents race conditions)
            cursor.execute("""
                SELECT id FROM posting_queue
                WHERE idea_id = %s
                AND content_type = %s
                AND platform = %s
                AND scheduled_date = %s
                FOR UPDATE
            """, (idea_id, content_type, platform, scheduled_date))
            
            result = cursor.fetchone()
            return result is not None
    except Exception as e:
        logger.error(f"Error checking existing post: {e}")
        # ⚠️ FIX: Return True on error (safer - prevents duplicates)
        return True  # Assume exists if check fails
```

### 3. **Use INSERT ... ON CONFLICT DO NOTHING**

```python
# Instead of check then insert, use atomic insert
cursor.execute("""
    INSERT INTO posting_queue (
        idea_id, content_type, platform, generated_content,
        status, scheduled_date, scheduled_time, created_at, updated_at
    )
    VALUES (%s, %s, %s, %s, 'draft', %s, %s, NOW(), NOW())
    ON CONFLICT (idea_id, content_type, platform, scheduled_date)
    DO NOTHING
    RETURNING id
""", (idea_id, content_type, platform, generated_content, scheduled_date, scheduled_time))
```

**Benefit:** Atomic operation, no race condition

### 4. **Add Rate Limiting**

Limit how many posts can be created per run:
- Max 3 language posts per day (1 word + 1 phrase + 1 insult)
- Skip if limit already reached

---

## Immediate Actions Required

### 1. **Clean Up Duplicates** (Before Re-enabling Facebook)

```sql
-- Delete duplicate language posts, keeping only the oldest one
WITH ranked_posts AS (
    SELECT id,
           ROW_NUMBER() OVER (
               PARTITION BY idea_id, content_type, platform, scheduled_date
               ORDER BY created_at ASC
           ) as rn
    FROM posting_queue
    WHERE content_type IN ('weekly_word', 'weekly_phrase', 'weekly_insult')
    AND status = 'draft'
    AND scheduled_date = '2026-01-18'
)
DELETE FROM posting_queue
WHERE id IN (
    SELECT id FROM ranked_posts WHERE rn > 1
);
```

### 2. **Add Database Constraint**

Run migration to add UNIQUE constraint (see Fix #1 above)

### 3. **Fix Code**

Update `automated_weekly_content_creator.py` with atomic insert (see Fix #3 above)

### 4. **Verify Fix**

Run script multiple times, verify no duplicates created

---

## Prevention Measures

### Before Re-enabling Facebook Posting:

1. ✅ **Add database UNIQUE constraint**
2. ✅ **Fix duplicate check with atomic operation**
3. ✅ **Clean up existing duplicates**
4. ✅ **Add rate limiting**
5. ✅ **Test thoroughly**

### Ongoing Monitoring:

1. **Daily checks** for duplicate posts
2. **Alert** if duplicates detected
3. **Log** all post creations
4. **Limit** posts per day** (max 3 language posts)

---

## UI to View Queue

**Queue API:** `/launchpad/api/queue`  
**Homepage Timeline:** Shows queue items (filtered by status)  
**Publication Dashboard:** `/publication/dashboard` - Shows scheduled posts

**To view ALL posts:**
- Use API: `curl http://localhost:5000/launchpad/api/queue`
- Or check database directly

---

## Conclusion

**This bug would have caused 624 duplicate Facebook posts if posting were enabled.**

**Status:** 🔴 **CRITICAL - FIX REQUIRED BEFORE RE-ENABLING FACEBOOK POSTING**

**Next Steps:**
1. Clean up duplicates
2. Add database constraint
3. Fix code with atomic operations
4. Test thoroughly
5. Then re-enable Facebook posting

---

*Last updated: 2026-01-19*
