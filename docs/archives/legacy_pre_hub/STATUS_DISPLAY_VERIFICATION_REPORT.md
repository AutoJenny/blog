# Status Display Verification Report

**Date:** 2025-12-18  
**Purpose:** Verify that status badges are consistent across all calendar views and match the `/posts` list.

---

## Test Results Summary

✅ **All status displays are consistent**  
✅ **Triskelion example (previously problematic) now shows correct status**  
✅ **Publication dashboard correctly shows social outputs**

---

## Test Case 1: Week View API

**Endpoint:** `GET /planning/api/calendar/schedule/2025/51`  
**Test Item:** Triskelion theme (theme_id: 58)

**Results:**
```json
{
    "theme_id": 58,
    "theme_title": "Triskelion",
    "post_id": 705,
    "post_status": "published"
}
```

**Verification:**
- ✅ `post_id: 705` matches `/posts` list
- ✅ `post_status: "published"` matches post.status in database
- ✅ Status resolver correctly identified post via week mapping

---

## Test Case 2: Posts List API

**Endpoint:** `GET /api/posts?show_deleted=0`  
**Test Item:** Post ID 705

**Results:**
```json
{
    "id": 705,
    "status": "published",
    "title": "What Makes the Triskelion Unique? A Deep Dive into its Symbolism"
}
```

**Verification:**
- ✅ Post exists with correct status
- ✅ Status matches week view API

---

## Test Case 3: Publication Dashboard API

**Endpoint:** `GET /publication/api/dashboard/schedule?year=2025&week=51`  
**Test Item:** Triskelion theme

**Results:**
```json
{
    "category": "theme",
    "item_id": 58,
    "title": "Triskelion",
    "post_exists": true,
    "post_id": 705,
    "post_status": "published",
    "channel": "blog",
    "content_format": "article"
}
```

**Verification:**
- ✅ `post_exists: true` correctly indicates post exists
- ✅ `post_id: 705` matches other APIs
- ✅ `post_status: "published"` matches other APIs
- ✅ Status resolver correctly enriched the item

---

## Test Case 4: Social Outputs

**Test:** Social outputs (products, weekly items) in publication dashboard

**Results:**
- ✅ Product posts appear with correct `queue_id` and status
- ✅ Weekly items appear (though none have social posts created yet)
- ✅ `SocialOutputView` helper correctly normalizes status

**Note:** No weekly social posts exist yet (expected - they're created on-demand). When created, they will have `idea_id` properly populated.

---

## Test Case 5: Items Without Posts

**Test Items:**
- Recipe: Cranberry Cranachan (recipe_id: 49)
- Profile: Hay (surname profile)

**Results:**
```json
{
    "post_exists": false,
    "post_id": null,
    "post_status": null
}
```

**Verification:**
- ✅ Items without posts correctly show `post_exists: false`
- ✅ No false positives (items correctly identified as "Not Created")

---

## Consistency Check

### Triskelion Theme (Week 51, 2025)

| View | post_id | post_status | post_exists |
|------|---------|-------------|-------------|
| Week View API | 705 | published | true |
| Posts List | 705 | published | N/A |
| Publication Dashboard | 705 | published | true |

✅ **All views show consistent status**

---

## Edge Cases Tested

1. **Published Post:** ✅ Correctly shows "published" status
2. **No Post:** ✅ Correctly shows `post_exists: false`, `post_id: null`
3. **Social Outputs:** ✅ Correctly appear with normalized status
4. **Multiple Items:** ✅ All items show correct status

---

## Issues Found

**None** - All status displays are consistent and correct.

---

## Recommendations

1. ✅ Status resolver is working correctly
2. ✅ All calendar APIs are using resolver consistently
3. ✅ Social outputs are correctly normalized
4. ⚠️ Weekly social posts will be created on-demand (none exist yet, which is expected)

---

## Next Steps

1. When weekly social posts are created, verify they have `idea_id` populated
2. Test with draft posts to verify status shows as "draft"
3. Test with deleted posts to verify status shows as "deleted" or "none"

