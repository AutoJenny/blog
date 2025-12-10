# Publication Schedule Status Report

## Investigation Date
2025-01-XX

## Current State

### API Endpoint: `/publication/api/dashboard/schedule`

**Current Response Structure:**
```json
{
  "success": true,
  "year": 2025,
  "week": 50,
  "channels": {
    "blog": [
      {
        "category": "theme",
        "item_id": 56,
        "post_id": null,  // ⚠️ Can be null if post doesn't exist
        "title": "Salmon migration",
        "description": "...",
        "channel": "blog",
        "content_format": "article",
        "day": 1,
        "type_name": "Theme",
        "week": 50,
        "year": 2025
        // ❌ Missing: post_status, post_exists
      }
    ]
  }
}
```

### Backend Analysis

#### ✅ What Works
1. **Post ID Detection**: The API already returns `post_id` field (can be `null` if post doesn't exist)
2. **Database Schema**: Posts have a `status` field with values: `'draft'`, `'published'`, `'deleted'`
3. **Status Querying**: Other endpoints (e.g., `/planning/api/posts/<post_id>`) successfully query post status
4. **Status Display Logic**: `get_display_status()` function exists in `blueprints/posts.py` to normalize status values

#### ❌ What's Missing
1. **Post Status in API Response**: The `/publication/api/dashboard/schedule` endpoint does NOT fetch or return post status
2. **Post Existence Check**: No explicit `post_exists` boolean flag (though `post_id !== null` can be inferred)
3. **Status Normalization**: Status values are not normalized in the response (raw database values)

### Current Data Flow

```
Calendar JSON Files
    ↓
resolve_item_for_week() / load_category_year()
    ↓
Extract: item_id, title, post_id (if exists)
    ↓
Get channel assignments from post_type_channel_config
    ↓
Return items with post_id (may be null)
    ❌ Missing: Post status lookup
```

### Required Changes

#### Backend Enhancement Needed

**File**: `blueprints/publication_dashboard.py`
**Function**: `api_dashboard_schedule()` (lines 215-406)

**Changes Required:**
1. After extracting `post_id` (line 284), add a database query to fetch post status if `post_id` exists
2. Add `post_status` field to `item_data` dictionary (line 373-386)
3. Add `post_exists` boolean field for clarity
4. Normalize status using `get_display_status()` helper

**Example Enhancement:**
```python
# After line 284 (post_id extraction)
post_status = None
post_exists = post_id is not None

if post_id:
    cursor.execute("""
        SELECT status
        FROM post
        WHERE id = %s
    """, (post_id,))
    post_row = cursor.fetchone()
    if post_row:
        post_status = post_row.get('status')
        # Normalize status
        from blueprints.posts import get_display_status
        post_status = get_display_status(post_status)

# Add to item_data (line 373-386)
item_data = {
    # ... existing fields ...
    'post_id': post_id,
    'post_exists': post_exists,
    'post_status': post_status,  # 'draft', 'published', 'deleted', or None
    # ... rest of fields ...
}
```

#### Frontend Changes Needed

**File**: `templates/planning/calendar/includes/publication_schedule_scripts.html`

**Current Implementation:**
- Line 79: Shows "Work on This" button for all items
- Line 83-86: Navigates to one-click publication page

**Required Changes:**
1. Replace "Work on This" button with status indicator
2. Show "Create" button if `post_id === null` or `post_exists === false`
3. Show status badge if post exists:
   - `draft` → Yellow/Orange badge
   - `published` → Green badge
   - `deleted` → Red/Gray badge
   - `null`/missing → "Create" button

**Example Frontend Logic:**
```javascript
// In renderSchedule() function, replace button section (line 79)
if (item.post_id && item.post_status) {
    // Post exists - show status badge
    const statusBadge = document.createElement('div');
    statusBadge.className = `status-badge status-${item.post_status}`;
    statusBadge.textContent = item.post_status;
    itemCard.appendChild(statusBadge);
} else {
    // Post doesn't exist - show Create button
    const createBtn = document.createElement('button');
    createBtn.className = 'btn-create';
    createBtn.textContent = 'Create';
    createBtn.addEventListener('click', function(e) {
        e.stopPropagation();
        navigateToOneClick(item);
    });
    itemCard.appendChild(createBtn);
}
```

## Backend Fitness Assessment

### ✅ Backend is MOSTLY Fit for Purpose

**Strengths:**
- Database schema supports post status tracking
- Post status querying is straightforward (single SELECT query)
- Status normalization logic already exists
- API structure is extensible (easy to add fields)

**Gaps:**
- Post status is not currently fetched in the schedule API
- No explicit post existence flag (though inferable from `post_id`)
- Status normalization not applied in this endpoint

**Effort Required:**
- **Low**: Adding post status lookup requires ~10-15 lines of code
- **Low Risk**: Simple SELECT query, no schema changes needed
- **Backward Compatible**: Adding new fields won't break existing frontend

## Recommendations

1. **Enhance Backend API** (Priority: High)
   - Add post status lookup when `post_id` exists
   - Add `post_exists` boolean field
   - Normalize status values using existing helper

2. **Update Frontend** (Priority: High)
   - Replace "Work on This" button with status indicator
   - Add "Create" button for items without posts
   - Style status badges appropriately

3. **Testing** (Priority: Medium)
   - Test with items that have posts (various statuses)
   - Test with items that don't have posts
   - Verify status badges display correctly

## Conclusion

**The backend is fit for purpose** with minor enhancements. The required changes are:
- Simple database query addition
- Extending the API response structure
- No schema changes needed
- Low risk, backward compatible

The main work is in the frontend to replace the button with status indicators and create buttons.

