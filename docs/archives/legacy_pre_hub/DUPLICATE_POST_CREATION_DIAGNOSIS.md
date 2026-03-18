# Duplicate Post Creation Diagnosis Report

**Date:** 2025-12-11  
**Issue:** System auto-creating multiple posts for the same calendar item  
**Location:** `/posts` page showing duplicate posts (IDs 698-704 mentioned earlier)

---

## Executive Summary

**Root Cause:** Multiple failure points in duplicate prevention:
1. **Frontend tracking is instance-based** - resets on page reload/multiple tabs
2. **Backend API has no duplicate check** - creates new post every time
3. **Race conditions** - multiple simultaneous requests can bypass frontend checks
4. **Fuzzy post detection** - existing post lookup is unreliable

---

## Problem Analysis

### 1. Frontend Auto-Creation Logic

**File:** `static/js/launchpad/one-click-blog-controller.js`

**Location:** Lines 234-242

**Current Implementation:**
```javascript
const autoCreateKey = `${category}-${resolvedItemId || ''}-${year || ''}-${week || ''}-${normalizedOutputChannel}`;
if (!this.autoCreateAttempts) {
    this.autoCreateAttempts = new Set();
}

if (normalizedOutputChannel === 'blog' && !this.autoCreateAttempts.has(autoCreateKey)) {
    this.autoCreateAttempts.add(autoCreateKey);
    const created = await this.autoCreatePostFromCalendarItem(...);
}
```

**Problems:**
- ✅ **Instance-based tracking** - `this.autoCreateAttempts` is per-controller instance
- ✅ **Resets on page reload** - Set is lost when page refreshes
- ✅ **Multiple tabs = multiple instances** - Each tab has its own Set
- ✅ **No persistence** - Not stored in localStorage or sessionStorage
- ✅ **Race condition window** - Check happens before API call, multiple tabs can pass check simultaneously

**Example Scenario:**
1. User opens tab 1 → `autoCreateAttempts` is empty → passes check → starts API call
2. User opens tab 2 (before tab 1 completes) → `autoCreateAttempts` is empty → passes check → starts API call
3. Both API calls complete → 2 posts created

---

### 2. Backend API - No Duplicate Prevention

**File:** `blueprints/automation_core.py`

**Function:** `create_post_from_item()` (lines 425-665)

**Current Implementation:**
```python
def create_post_from_item():
    # ... get item data ...
    
    # NO CHECK FOR EXISTING POST HERE
    
    # Create post (only if blog post is needed)
    cursor.execute("""
        INSERT INTO post (title, slug, status, created_at, updated_at)
        VALUES (%s, %s, 'draft', NOW(), NOW())
        RETURNING id
    """, (title, slug))
    
    post_id = cursor.fetchone()['id']
```

**Problems:**
- ❌ **No duplicate check** - API doesn't check if post already exists for this calendar item
- ❌ **Always creates new post** - Every API call results in a new post
- ❌ **Only profile check** - Only profiles check for existing `post_id` (line 492-498)
- ❌ **No database constraints** - No unique constraint preventing duplicate posts for same item

**Missing Logic:**
- Should check `calendar_week_posts_v2` or `calendar_week_items_deprecated` for existing post
- Should check `post` table for posts linked to this item (recipe_id, theme via idea_seed, etc.)
- Should return existing `post_id` if found instead of creating new

---

### 3. Calendar Item API - Fuzzy Post Detection

**File:** `blueprints/automation_core.py`

**Function:** `get_calendar_item()` (lines 299-422)

**Current Implementation:**
```python
# Check if post exists for this item
post_id = None
with db_manager.get_cursor() as cursor:
    if category == 'theme':
        cursor.execute("""
            SELECT p.id FROM post p
            JOIN post_development pd ON p.id = pd.post_id
            WHERE pd.idea_seed ILIKE %s AND p.status != 'deleted'
            ORDER BY p.created_at DESC
            LIMIT 1
        """, (f'%{item.get("theme_title") or item.get("title", "")}%',))
    elif category == 'recipe':
        cursor.execute("""
            SELECT id FROM post
            WHERE recipe_id = %s AND status != 'deleted'
            ORDER BY created_at DESC
            LIMIT 1
        """, (item.get("id"),))
```

**Problems:**
- ⚠️ **Fuzzy matching for themes** - Uses `ILIKE` with wildcards, can match wrong posts
- ⚠️ **No week/year context** - Doesn't check if post is for the same week/year
- ⚠️ **Recipe check is good** - Uses `recipe_id` which is reliable
- ⚠️ **Weekly content is fuzzy** - Uses `ILIKE` similar to themes

**Example Issue:**
- Theme "Christmas in Scotland" (2025, week 50)
- Post exists for "Christmas in Scotland" (2024, week 50)
- `get_calendar_item()` might find the 2024 post
- But `create_post_from_item()` doesn't use this check anyway

---

### 4. Race Condition Scenarios

**Scenario A: Multiple Tabs**
1. User opens `/launchpad/one-click-publication?category=theme&item_id=56&year=2025&week=50&output=blog` in tab 1
2. Page loads → `autoCreateAttempts` is empty → passes check → starts API call
3. User opens same URL in tab 2 (before tab 1 completes)
4. Tab 2 page loads → `autoCreateAttempts` is empty → passes check → starts API call
5. Both API calls complete → 2 posts created

**Scenario B: Page Reload**
1. User opens page → auto-creation triggered → post created
2. Page reloads (user action or redirect)
3. `autoCreateAttempts` Set is reset (new instance)
4. Auto-creation triggered again → second post created

**Scenario C: Multiple Calendar Views**
1. User clicks "Create" from week-view calendar
2. Auto-creation triggered → post created
3. User navigates to publication-schedule view
4. Clicks "Create" again (different entry point)
5. Auto-creation triggered again → second post created

**Scenario D: Network Delay**
1. User opens page → auto-creation triggered → API call sent
2. Network delay (slow connection)
3. User refreshes page (thinking it's stuck)
4. New auto-creation triggered → second API call sent
5. Both API calls complete → 2 posts created

---

## Current Duplicate Prevention Mechanisms

### ✅ What Exists (But Incomplete)

1. **Frontend Set tracking** - Prevents duplicates within same page instance
   - **Limitation:** Resets on reload, doesn't work across tabs

2. **Calendar Item API post lookup** - Checks for existing posts
   - **Limitation:** Fuzzy matching, not used by create API

3. **Profile post_id check** - Profiles check for existing post_id
   - **Limitation:** Only works for profiles, not other categories

### ❌ What's Missing

1. **Backend duplicate check** - `create_post_from_item()` doesn't check for existing posts
2. **Persistent tracking** - Frontend tracking not stored in localStorage
3. **Database constraints** - No unique constraint preventing duplicate posts
4. **Week/year context** - Post lookup doesn't consider week/year context
5. **Idempotency** - API calls are not idempotent (same request = multiple posts)

---

## Recommended Solutions

### Solution 1: Backend Duplicate Check (CRITICAL)

**Priority:** HIGHEST  
**File:** `blueprints/automation_core.py::create_post_from_item()`

**Implementation:**
1. Before creating post, check for existing post:
   - For recipes: Check `post.recipe_id = item_id`
   - For themes: Check `calendar_week_posts_v2` for same year/week + theme match
   - For weekly content: Check `calendar_week_posts_v2` for same year/week + title match
   - For profiles: Already has check (keep as-is)

2. If existing post found:
   - Return existing `post_id` instead of creating new
   - Return `{"success": true, "post_id": existing_id, "message": "Post already exists"}`

3. Only create new post if no existing post found

**Benefits:**
- Prevents duplicates at the source (backend)
- Works regardless of frontend state
- Handles race conditions
- Idempotent API calls

---

### Solution 2: Persistent Frontend Tracking

**Priority:** MEDIUM  
**File:** `static/js/launchpad/one-click-blog-controller.js`

**Implementation:**
1. Store `autoCreateAttempts` in `sessionStorage` (per-tab) or `localStorage` (cross-tab)
2. Key format: `autoCreate_${category}_${itemId}_${year}_${week}_${channel}`
3. Set expiration (e.g., 5 minutes) to allow retries if needed
4. Clear on successful post creation

**Benefits:**
- Prevents duplicates across page reloads
- Works across tabs (if using localStorage)
- Still allows manual retry after expiration

**Limitation:**
- Not foolproof (can be cleared, doesn't handle race conditions)
- Should be combined with Solution 1

---

### Solution 3: Database Constraints

**Priority:** LOW (defensive)  
**File:** Database migration

**Implementation:**
1. Add unique constraint on `post.recipe_id` (recipes can only have one post)
2. Add unique constraint on `calendar_week_posts_v2(year, week_number, post_id)` (if not exists)
3. Consider adding `post.calendar_item_id` and `post.calendar_item_category` columns for direct linking

**Benefits:**
- Database-level prevention
- Catches edge cases
- Prevents data corruption

**Limitation:**
- Requires schema changes
- May need migration for existing data

---

### Solution 4: Improve Post Lookup

**Priority:** MEDIUM  
**File:** `blueprints/automation_core.py::get_calendar_item()` and `create_post_from_item()`

**Implementation:**
1. Use `calendar_week_posts_v2` or `calendar_week_items_deprecated` for week/year context
2. For themes: Match by `theme_id` if available, or week/year + title
3. For recipes: Use `recipe_id` (already reliable)
4. For weekly content: Match by week/year + title + category

**Benefits:**
- More accurate post detection
- Considers week/year context
- Reduces false matches

---

## Immediate Action Items

### Critical (Do First)
1. ✅ **Add duplicate check to `create_post_from_item()` API**
   - Check for existing post before creating
   - Return existing post_id if found
   - Only create if no existing post

### High Priority
2. ✅ **Add persistent tracking to frontend**
   - Use sessionStorage/localStorage for `autoCreateAttempts`
   - Set expiration time
   - Clear on successful creation

3. ✅ **Improve post lookup logic**
   - Use week/year context
   - Use more reliable matching (recipe_id, theme_id)
   - Reduce fuzzy matching

### Medium Priority
4. ⚠️ **Add database constraints** (if schema allows)
   - Unique constraint on recipe_id
   - Unique constraint on calendar week posts

5. ⚠️ **Add logging/monitoring**
   - Log duplicate creation attempts
   - Alert on multiple posts for same item
   - Track creation frequency

---

## Testing Scenarios

After fixes, test:
1. ✅ Open same calendar item in multiple tabs → should only create one post
2. ✅ Reload page after auto-creation → should not create duplicate
3. ✅ Click "Create" multiple times quickly → should only create one post
4. ✅ Create post manually, then auto-create → should return existing post_id
5. ✅ Network delay + page refresh → should not create duplicate

---

## Conclusion

**Primary Issue:** Backend API `create_post_from_item()` has no duplicate prevention. Every API call creates a new post, regardless of whether one already exists.

**Secondary Issues:** Frontend tracking is ephemeral (resets on reload), and post lookup is fuzzy (doesn't use week/year context).

**Recommended Fix Order:**
1. **Backend duplicate check** (Solution 1) - Most critical, prevents all duplicates
2. **Persistent frontend tracking** (Solution 2) - Improves UX, reduces unnecessary API calls
3. **Improve post lookup** (Solution 4) - Makes detection more reliable
4. **Database constraints** (Solution 3) - Defensive measure, optional

