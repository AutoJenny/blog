# Publication Day Assignment UI - Implementation Plan

**Date:** 2025-12-10  
**Purpose:** Plan the implementation of a UI for managing publication day assignments for all post type/channel/content format combinations.

---

## Overview

Currently, day assignments are hardcoded in `blueprints/publication_dashboard.py`. This plan creates a proper management UI that allows configuring which day of the week each (post_type, channel, content_format) combination publishes on.

---

## 1. Database Schema Changes

### 1.1 Add `publication_day` Column

**File:** `migrations/20251210_add_publication_day_to_channel_config.sql`

```sql
-- Add publication_day column to post_type_channel_config
ALTER TABLE post_type_channel_config 
ADD COLUMN IF NOT EXISTS publication_day INTEGER 
CHECK (publication_day BETWEEN 1 AND 7);

COMMENT ON COLUMN post_type_channel_config.publication_day IS 
'Day of week for publication (1=Monday, 7=Sunday). NULL means no specific day assigned.';

-- Create index for queries
CREATE INDEX IF NOT EXISTS idx_post_type_channel_config_publication_day 
ON post_type_channel_config(publication_day) 
WHERE publication_day IS NOT NULL;
```

### 1.2 Default Day Assignments

Based on current hardcoded values and week-view layout:

```sql
-- Set default publication days based on current system behavior
UPDATE post_type_channel_config 
SET publication_day = CASE
    -- Blog channel defaults
    WHEN channel = 'blog' AND post_type = 'themed' THEN 1  -- Monday
    WHEN channel = 'blog' AND post_type = 'recipe' THEN 3  -- Wednesday
    WHEN channel = 'blog' AND post_type = 'profile_product' THEN 6  -- Saturday
    WHEN channel = 'blog' AND post_type = 'profile_surname' THEN 5  -- Friday
    
    -- Facebook channel defaults (for weekly content)
    WHEN channel = 'facebook' AND post_type = 'weekly_word' THEN 1  -- Monday
    WHEN channel = 'facebook' AND post_type = 'weekly_phrase' THEN 3  -- Wednesday
    WHEN channel = 'facebook' AND post_type = 'weekly_insult' THEN 5  -- Friday
    
    -- Other channels can be NULL (no specific day) or set as needed
    ELSE NULL
END
WHERE publication_day IS NULL;
```

---

## 2. Backend API Endpoints

### 2.1 Get All Day Assignments

**File:** `blueprints/settings.py` (or new `blueprints/publication_settings.py`)

**Endpoint:** `GET /settings/publication-days`

**Response:**
```json
{
  "success": true,
  "assignments": [
    {
      "id": 1,
      "post_type": "themed",
      "channel": "blog",
      "content_format": "article",
      "publication_day": 1,
      "day_name": "Monday",
      "is_primary": true,
      "is_required": true
    },
    ...
  ],
  "post_types": ["themed", "recipe", "profile_product", "profile_surname", "weekly_word", "weekly_phrase", "weekly_insult"],
  "channels": ["blog", "facebook", "instagram", "twitter", "newsletter"],
  "day_names": {
    "1": "Monday",
    "2": "Tuesday",
    "3": "Wednesday",
    "4": "Thursday",
    "5": "Friday",
    "6": "Saturday",
    "7": "Sunday"
  }
}
```

### 2.2 Update Day Assignment

**Endpoint:** `PUT /settings/publication-days/<id>`

**Request Body:**
```json
{
  "publication_day": 3  // 1-7 or null to clear
}
```

**Response:**
```json
{
  "success": true,
  "message": "Publication day updated",
  "assignment": {
    "id": 1,
    "post_type": "themed",
    "channel": "blog",
    "content_format": "article",
    "publication_day": 3,
    "day_name": "Wednesday"
  }
}
```

### 2.3 Bulk Update Day Assignments

**Endpoint:** `PUT /settings/publication-days/bulk`

**Request Body:**
```json
{
  "updates": [
    {"id": 1, "publication_day": 3},
    {"id": 2, "publication_day": 1},
    {"id": 5, "publication_day": null}
  ]
}
```

---

## 3. Frontend UI

### 3.1 Settings Page Entry

**File:** `templates/settings/index.html`

Add a new card:
```html
<a href="/settings/publication-days"
    class="bg-[#23273a] rounded-lg border border-dark-border p-6 hover:bg-[#2a2f45] transition group">
    <div class="flex items-center gap-3 mb-3">
        <i class="fa-solid fa-calendar-week text-2xl text-blue-400 group-hover:text-blue-300"></i>
        <h2 class="text-lg font-semibold text-white">Publication Days</h2>
    </div>
    <p class="text-dark-text text-sm">
        Configure which day of the week each post type publishes to each channel.
    </p>
</a>
```

### 3.2 Main Management UI

**File:** `templates/settings/publication_days.html`

**Layout:**
- **Header**: Title, description, save button
- **Filter Controls**: 
  - Filter by post type (dropdown)
  - Filter by channel (dropdown)
  - Show only assigned / show only unassigned
- **Main Table/Grid**:
  - Rows: Post Type + Content Format combinations
  - Columns: Channels (Blog, Facebook, Instagram, Twitter, Newsletter)
  - Cells: Dropdown for day selection (Monday-Sunday, or "Not assigned")
  - Visual indicators:
    - Primary channel highlighted
    - Required channels marked
    - Active/inactive status

**Table Structure:**
```
| Post Type | Format | Blog | Facebook | Instagram | Twitter | Newsletter |
|-----------|--------|------|-----------|-----------|---------|------------|
| themed    | article| Mon ▼| Wed ▼     | -         | -       | -          |
| recipe    | recipe | Wed ▼| Wed ▼     | -         | -       | -          |
| weekly_word| word_of_day | - | Mon ▼ | Mon ▼     | -       | -          |
...
```

### 3.3 JavaScript Controller

**File:** `static/js/settings/publication-days-manager.js`

**Responsibilities:**
- Load all assignments from API
- Render table/grid
- Handle day dropdown changes
- Track unsaved changes
- Bulk save functionality
- Validation (e.g., prevent conflicts if needed)
- Show success/error messages

---

## 4. Backend Integration

### 4.1 Update Dashboard API

**File:** `blueprints/publication_dashboard.py`

**Change:** Remove hardcoded `day_map`, query database instead:

```python
# OLD (hardcoded):
day_map = {
    'theme': 1,
    'recipe': 3,
    ...
}
item_data['day'] = day_map.get(category, 1)

# NEW (database-driven):
# Get publication day from post_type_channel_config
cursor.execute("""
    SELECT publication_day
    FROM post_type_channel_config
    WHERE post_type = %s 
    AND channel = %s 
    AND content_format = %s
    AND is_active = TRUE
""", (post_type, channel, content_format))

result = cursor.fetchone()
item_data['day'] = result['publication_day'] if result and result['publication_day'] else None
```

### 4.2 Helper Function

**File:** `utils/channel_assignment.py`

Add function:
```python
def get_publication_day(post_type: str, channel: str, content_format: str) -> Optional[int]:
    """
    Get publication day for a (post_type, channel, content_format) combination.
    
    Returns:
        int: Day of week (1=Monday, 7=Sunday) or None if not assigned
    """
    # Implementation
```

---

## 5. Implementation Phases

### Phase 1: Database Schema (1-2 hours)
- [ ] Create migration to add `publication_day` column
- [ ] Set default values based on current hardcoded map
- [ ] Test migration

### Phase 2: Backend API (2-3 hours)
- [ ] Create/update blueprint for publication day management
- [ ] Implement GET endpoint (all assignments)
- [ ] Implement PUT endpoint (update single assignment)
- [ ] Implement bulk update endpoint
- [ ] Add helper function to `utils/channel_assignment.py`
- [ ] Test API endpoints

### Phase 3: Frontend UI (3-4 hours)
- [ ] Create settings page template
- [ ] Add entry card to settings index
- [ ] Build table/grid layout
- [ ] Implement JavaScript controller
- [ ] Add save/validation logic
- [ ] Style with dark theme
- [ ] Test UI interactions

### Phase 4: Integration (1-2 hours)
- [ ] Update dashboard API to use database instead of hardcoded map
- [ ] Remove hardcoded `day_map` from `publication_dashboard.py`
- [ ] Test dashboard still works correctly
- [ ] Verify week-view alignment

### Phase 5: Testing & Documentation (1 hour)
- [ ] Test all CRUD operations
- [ ] Test edge cases (null days, inactive configs)
- [ ] Update documentation
- [ ] Add migration notes

---

## 6. UI Design Details

### 6.1 Table Layout Options

**Option A: Post Type × Channel Grid**
- Rows: Post types
- Columns: Channels
- Cells: Day dropdown + format indicator
- **Pros**: Easy to see all channels for a post type
- **Cons**: Doesn't show content_format clearly

**Option B: Post Type + Format × Channel Grid**
- Rows: Post type + content format combinations
- Columns: Channels
- Cells: Day dropdown
- **Pros**: Shows full (post_type, channel, format) combinations
- **Cons**: More rows, might be wide

**Option C: Channel × Post Type Grid**
- Rows: Channels
- Columns: Post types
- Cells: Day dropdown + format indicator
- **Pros**: Easy to see all post types for a channel
- **Cons**: Doesn't show content_format clearly

**Recommendation:** Option B (Post Type + Format × Channel) - most complete view

### 6.2 Day Dropdown Options

Each cell dropdown:
- "Not assigned" (null)
- "Monday" (1)
- "Tuesday" (2)
- ...
- "Sunday" (7)

### 6.3 Visual Indicators

- **Primary Channel**: Bold border or background color
- **Required Channel**: Checkmark icon
- **Inactive Config**: Grayed out, disabled
- **Unsaved Changes**: Yellow/orange border
- **No Assignment**: Light gray background

### 6.4 Bulk Actions

- **Save All**: Save all changes at once
- **Reset**: Revert unsaved changes
- **Set Defaults**: Apply default day assignments
- **Clear All**: Set all to "Not assigned"

---

## 7. Edge Cases & Validation

### 7.1 Multiple Formats Per Channel

Some post types have multiple content formats for the same channel (e.g., `recipe` on `blog` vs `recipe` on `facebook`). Each (post_type, channel, content_format) combination can have its own day.

### 7.2 Null Days

If `publication_day` is NULL, the item won't appear in the dashboard's day-based view. This is valid for:
- Channels that don't need specific day assignments
- Optional channels
- Channels that publish on-demand

### 7.3 Inactive Configs

If `is_active = FALSE`, the assignment should still be editable but clearly marked as inactive. The dashboard API should ignore inactive configs.

### 7.4 Day Conflicts

Currently, no validation for conflicts (e.g., multiple items on same day). This is intentional - multiple items can publish on the same day. If needed later, add validation.

---

## 8. Migration Strategy

1. **Add column** with NULL allowed
2. **Set defaults** based on current hardcoded values
3. **Deploy UI** for management
4. **Update dashboard API** to use database
5. **Remove hardcoded map** from code
6. **Monitor** for any issues

---

## 9. Files to Create/Modify

### New Files:
- `migrations/20251210_add_publication_day_to_channel_config.sql`
- `templates/settings/publication_days.html`
- `static/js/settings/publication-days-manager.js`
- `blueprints/publication_settings.py` (or extend `blueprints/settings.py`)

### Modified Files:
- `templates/settings/index.html` (add entry card)
- `blueprints/publication_dashboard.py` (remove hardcoded day_map, use database)
- `utils/channel_assignment.py` (add helper function)

---

## 10. Success Criteria

- [ ] No hardcoded day assignments in code
- [ ] UI allows editing all (post_type, channel, format) combinations
- [ ] Dashboard API reads from database
- [ ] Changes save correctly
- [ ] Dashboard displays items on correct days
- [ ] Week-view aligns with dashboard
- [ ] UI is intuitive and matches existing settings pages

---

## 11. Future Enhancements (Not in Initial Implementation)

- **Time Assignment**: Add `publication_time` editing (currently only day)
- **Day Templates**: Save/load day assignment presets
- **Validation Rules**: Prevent certain day combinations
- **Bulk Day Shifts**: Move all items by X days
- **Day Statistics**: Show how many items per day
- **Conflict Detection**: Warn about too many items on one day

