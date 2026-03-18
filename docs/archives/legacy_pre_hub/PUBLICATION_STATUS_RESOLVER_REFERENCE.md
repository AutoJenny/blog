# Publication Status Resolver Reference

**Date:** 2025-12-18  
**Module:** `utils/publication_status_resolver.py`  
**Purpose:** Single source of truth for determining post/output status based on explicit ID linkages.

---

## Overview

The Publication Status Resolver provides ID-only status resolution for calendar-driven content and posting-queue items. It replaces ad-hoc status logic scattered across endpoints and ensures consistent status display across all calendar views.

**Key Principles:**
- **ID-only matching** - Never uses title or text heuristics
- **Explicit linkages** - Relies on canonical week→post mappings
- **No fallbacks** - Reports `exists = False` if relationships are missing
- **Unified status enum** - Normalizes raw DB statuses to consistent display values

---

## Public API

### Status Normalization Functions

#### `normalize_post_status(status: Optional[str]) -> Optional[str]`

Normalizes raw `post.status` into display enum.

**Mapping:**
- `"published"`, `"live"` → `"published"`
- `"error"` → `"error"`
- `"publishing"` → `"publishing"`
- `"deleted"` → `"deleted"`
- Everything else (including `None`) → `"draft"`

**Usage:**
```python
from utils.publication_status_resolver import normalize_post_status

normalized = normalize_post_status(post.status)  # "published", "draft", etc.
```

---

#### `normalize_queue_status(status: Optional[str]) -> Optional[str]`

Normalizes raw `posting_queue.status` into display enum.

**Mapping:**
- `"pending"`, `"ready"` → `"scheduled"`
- `"published"` → `"published"`
- `"failed"`, `"error"` → `"error"`
- `"cancelled"` → `"deleted"`
- Unknown values → returned as-is (for diagnostics)

**Usage:**
```python
from utils.publication_status_resolver import normalize_queue_status

normalized = normalize_queue_status(queue_item.status)  # "scheduled", "published", etc.
```

---

### Status Resolution Functions

#### `resolve_post_for_calendar_item(category: str, item_id: int, year: int, week: int, *, cursor=None) -> PostStatusInfo`

Resolves post status for calendar items based on **ID-only matching**.

**Parameters:**
- `category`: Content category (`"theme"`, `"recipe"`, `"profile"`, etc.)
- `item_id`: Content Item ID (e.g., `calendar_themes.id`, `calendar_recipes.id`)
- `year`: ISO year
- `week`: ISO week number
- `cursor`: Optional DB cursor (for transaction sharing)

**Returns:** `PostStatusInfo` dict:
```python
{
    "exists": bool,           # True if post exists
    "status": Optional[str],  # Normalized status ("published", "draft", etc.)
    "post_id": Optional[int], # post.id if exists
    "raw_status": Optional[str] # Original post.status
}
```

**Matching Rules:**
- **Recipes:** Direct lookup via `post.recipe_id = item_id`
- **Profiles:** Direct lookup via `post.profile_product_id` or `post.profile_category_id = item_id`
- **Themes:** Week-based lookup via `calendar_week_posts_v2` by `(year, week)`, filtering out recipes/profiles
- **Weekly items:** Not applicable (weekly words/phrases/insults don't create blog posts directly)

**Usage:**
```python
from utils.publication_status_resolver import resolve_post_for_calendar_item

status_info = resolve_post_for_calendar_item(
    category="theme",
    item_id=58,  # calendar_themes.id
    year=2025,
    week=51
)

if status_info["exists"]:
    print(f"Post {status_info['post_id']} status: {status_info['status']}")
else:
    print("No post exists for this item")
```

---

#### `resolve_product_output(queue_id: int, *, cursor=None) -> QueueStatusInfo`

Resolves status for product posts from `posting_queue`.

**Parameters:**
- `queue_id`: `posting_queue.id`
- `cursor`: Optional DB cursor

**Returns:** `QueueStatusInfo` dict:
```python
{
    "exists": bool,           # True if queue item exists
    "status": Optional[str],  # Normalized status ("scheduled", "published", etc.)
    "queue_id": Optional[int], # posting_queue.id if exists
    "raw_status": Optional[str] # Original posting_queue.status
}
```

**Usage:**
```python
from utils.publication_status_resolver import resolve_product_output

status_info = resolve_product_output(queue_id=123)
```

---

## Status Enum Values

### Unified Display Statuses

All statuses are normalized to one of these values:

- **`"published"`** - Content has been published/live
- **`"scheduled"`** - Content is scheduled for future publication
- **`"draft"`** - Content exists but not ready/scheduled
- **`"publishing"`** - Content is currently being published
- **`"error"`** - Publication failed or needs attention
- **`"deleted"`** - Content was explicitly deleted/cancelled
- **`None`** - Status unknown or not applicable

---

## Category→ID Mapping Rules

### Direct Foreign Key Categories

These categories have direct foreign keys in the `post` table:

- **Recipes:** `post.recipe_id = calendar_recipes.id`
- **Product Profiles:** `post.profile_product_id = clan_products.id`
- **Category Profiles:** `post.profile_category_id = clan_categories.id`

**Resolution:** Direct SQL lookup by foreign key.

---

### Week-Based Categories

These categories use week→post mapping via `calendar_week_posts_v2`:

- **Themes:** `(year, week)` → `calendar_week_posts_v2` → `post.id`
  - Filters out recipes and profiles
  - One theme per week (primary blog post)

**Resolution:** Query `calendar_week_posts_v2` by `(year, week_number)`, filter by item type.

---

### Social-Only Categories

These categories don't create blog posts:

- **Weekly Word/Phrase/Insult:** Social-only (create `posting_queue` rows, not blog posts)
- **Products:** Social-only (create `posting_queue` rows, not blog posts)

**Resolution:** Not applicable for blog post resolution. Use `SocialOutputView` for social outputs.

---

## Usage Examples

### Example 1: Check Theme Post Status

```python
from utils.publication_status_resolver import resolve_post_for_calendar_item

# Check if Triskelion theme (ID 58) for week 51, 2025 has a post
status = resolve_post_for_calendar_item(
    category="theme",
    item_id=58,
    year=2025,
    week=51
)

if status["exists"]:
    print(f"Post {status['post_id']}: {status['status']}")
else:
    print("No post created yet")
```

### Example 2: Normalize Status for Display

```python
from utils.publication_status_resolver import normalize_post_status, normalize_queue_status

# Normalize blog post status
post_status = normalize_post_status(raw_post.status)  # "published", "draft", etc.

# Normalize social post status
queue_status = normalize_queue_status(raw_queue.status)  # "scheduled", "published", etc.
```

### Example 3: Enrich Calendar Items with Status

```python
from utils.publication_status_resolver import resolve_post_for_calendar_item

# In calendar API endpoint
for item in calendar_items:
    if item["category"] == "theme":
        status_info = resolve_post_for_calendar_item(
            category=item["category"],
            item_id=item["item_id"],
            year=year,
            week=week
        )
        item["post_id"] = status_info["post_id"]
        item["post_exists"] = status_info["exists"]
        item["post_status"] = status_info["status"]
```

---

## Integration Points

### Backend Endpoints Using Resolver

1. **`blueprints/planning_api_calendar_schedule.py::api_calendar_schedule()`**
   - Enriches theme items with `post_id`, `post_exists`, `post_status`

2. **`blueprints/publication_dashboard.py::api_dashboard_schedule()`**
   - Uses resolver for calendar-derived items (themes, recipes, profiles)

3. **`blueprints/planning_api_calendar_scheduling_cache.py::scheduling_all()`**
   - Enriches all items with status via resolver

4. **`blueprints/planning_api_calendar_schedule.py::api_calendar_idea_status()`**
   - Uses resolver for week themes status endpoint

---

## Testing

### Manual Testing

1. **Week View:** Verify status badges match `/posts` list
2. **Future Items Tab:** Verify status matches week view
3. **Publication Schedule:** Verify status consistency across all views

### Test Cases

- Theme with published post → should show "published" status
- Theme with draft post → should show "draft" status
- Theme with no post → should show "Not Created" (exists=False)
- Recipe with post → should show correct status
- Deleted post → should show "deleted" or "none" status

---

## Notes

- **No Title Matching:** The resolver never falls back to title-based matching. If ID linkage is missing, it reports `exists=False`.
- **Data Integrity:** Missing or inconsistent relationships should be fixed at source (post creation/persistence), not worked around in the resolver.
- **Performance:** Resolver uses efficient SQL queries with proper indexes. No N+1 query issues.

---

## File Location

- **Module:** `utils/publication_status_resolver.py`
- **Lines:** ~290 lines (under 500 line limit)
- **Dependencies:** `config.database.db_manager`

