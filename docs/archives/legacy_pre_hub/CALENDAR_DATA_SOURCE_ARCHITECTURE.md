# Calendar Data Source Architecture

**Date:** 2026-01-22  
**Status:** Critical - All calendar views must follow this architecture  
**Purpose:** Prevent data inconsistencies between different calendar views

---

## Problem Statement

Different calendar views were using different data sources, leading to inconsistencies:
- **Publication Schedule View** correctly used `post_type_channel_config` as authoritative source
- **Week View** was querying `posting_queue` directly without checking configuration
- Result: Week view showed product posts on Saturday when Messages should be displayed

---

## Solution: Single Source of Truth

### Authoritative Source: `post_type_channel_config`

**ALL calendar views MUST use `post_type_channel_config` as the authoritative source** to determine:
- Which post types should be displayed on which days
- Which channels each post type uses
- What times posts are scheduled

### Secondary Source: `posting_queue`

`posting_queue` is used for:
- Getting actual scheduled dates/times for specific posts
- Displaying post status (draft, ready, published)
- Showing post content/details

**BUT:** `posting_queue` should NEVER be used to determine WHAT should be displayed. That decision comes from `post_type_channel_config`.

---

## Architecture Rules

### Rule 1: Check Configuration First

Before querying `posting_queue`, always check `post_type_channel_config`:

```python
# ✅ CORRECT: Check config first
cursor.execute("""
    SELECT post_type, channel, publication_day
    FROM post_type_channel_config
    WHERE is_active = TRUE
    AND publication_day IS NOT NULL
    AND channel = 'facebook'
    AND post_type IN ('product', 'message')
""")
configs = cursor.fetchall()

# Determine what should be displayed
product_days = {c['publication_day'] for c in configs if c['post_type'] == 'product'}
message_days = {c['publication_day'] for c in configs if c['post_type'] == 'message'}

# Then query posting_queue with filters based on config
```

### Rule 2: Filter `posting_queue` Based on Config

When querying `posting_queue`, apply filters based on `post_type_channel_config`:

```python
# ✅ CORRECT: Filter based on config
cursor.execute("""
    SELECT ...
    FROM posting_queue pq
    WHERE pq.content_type = 'product'
      AND pq.platform = 'facebook'
      AND EXTRACT(ISODOW FROM pq.scheduled_date) != 6  -- Exclude Saturday per config
""")

# ❌ WRONG: Query everything and filter later
cursor.execute("""
    SELECT ...
    FROM posting_queue pq
    WHERE pq.content_type = 'product'
""")
# Then filter in Python - this ignores config!
```

### Rule 3: Use ISO Weekday

Always use `EXTRACT(ISODOW FROM date)` for weekday calculations:
- ISO weekday: 1=Monday, 2=Tuesday, ..., 6=Saturday, 7=Sunday
- **NOT** `EXTRACT(DOW FROM date) + 1` which gives 1=Sunday, 7=Saturday

```python
# ✅ CORRECT
EXTRACT(ISODOW FROM pq.scheduled_date) = 6  -- Saturday

# ❌ WRONG
EXTRACT(DOW FROM pq.scheduled_date) + 1 = 6  -- This is actually Friday!
```

---

## Implementation Examples

### Publication Schedule View

**File:** `blueprints/publication_dashboard.py::api_dashboard_schedule()`

**Pattern:**
1. Query `post_type_channel_config` for all active configurations
2. Build schedule items from config (post types, days, times)
3. Optionally query `posting_queue` to override times for specific posts
4. Filter out days that shouldn't have posts (e.g., Saturday products)

**Key Code:**
```python
# Query config first
cursor.execute("""
    SELECT post_type, channel, publication_day, publication_time
    FROM post_type_channel_config
    WHERE is_active = TRUE
    AND publication_day IS NOT NULL
""")

# Build items from config
for config in configs:
    if config['post_type'] == 'product' and config['publication_day'] == 6:
        continue  # Skip Saturday products - Messages replace them
    # Add item to schedule

# Then query posting_queue for actual times (optional override)
```

### Week View (Fixed)

**File:** `blueprints/planning_api_calendar_schedule.py::api_calendar_schedule()`

**Pattern:**
1. Query `post_type_channel_config` to determine what should be displayed
2. Query `posting_queue` with filters based on config
3. Exclude days that shouldn't have posts (e.g., Saturday products)
4. Include posts for days that should have them (e.g., Saturday messages)

**Key Code:**
```python
# Check config first
cursor.execute("""
    SELECT post_type, publication_day
    FROM post_type_channel_config
    WHERE is_active = TRUE
    AND channel = 'facebook'
    AND post_type IN ('product', 'message')
""")

# Query posting_queue with config-based filters
cursor.execute("""
    SELECT ...
    FROM posting_queue pq
    WHERE pq.content_type = 'product'
      AND EXTRACT(ISODOW FROM pq.scheduled_date) != 6  -- Exclude Saturday
""")

cursor.execute("""
    SELECT ...
    FROM posting_queue pq
    WHERE pq.content_type = 'message'
      AND EXTRACT(ISODOW FROM pq.scheduled_date) = 6  -- Only Saturday
""")
```

---

## Common Mistakes to Avoid

### ❌ Mistake 1: Query `posting_queue` Without Config Check

```python
# ❌ WRONG: Shows whatever is in posting_queue
cursor.execute("""
    SELECT * FROM posting_queue
    WHERE content_type = 'product'
    AND scheduled_date >= %s AND scheduled_date <= %s
""")
```

**Problem:** If old product posts exist on Saturday, they'll be displayed even though Messages should replace them.

### ❌ Mistake 2: Filter in Python Instead of SQL

```python
# ❌ WRONG: Filters after querying everything
posts = cursor.fetchall()
filtered = [p for p in posts if p['weekday'] != 6]
```

**Problem:** Inefficient and error-prone. Should filter in SQL based on config.

### ❌ Mistake 3: Using Wrong Weekday Function

```python
# ❌ WRONG: DOW gives 0=Sunday, 6=Saturday
EXTRACT(DOW FROM date) + 1  # Saturday = 7, not 6!

# ✅ CORRECT: ISODOW gives 1=Monday, 6=Saturday
EXTRACT(ISODOW FROM date)  # Saturday = 6
```

---

## Testing Checklist

When implementing or modifying calendar views:

- [ ] Does it query `post_type_channel_config` first?
- [ ] Does it filter `posting_queue` based on config?
- [ ] Does it use `ISODOW` for weekday calculations?
- [ ] Does it exclude Saturday product posts?
- [ ] Does it include Saturday message posts?
- [ ] Does it match the publication schedule view behavior?

---

## Related Documentation

- `PUBLICATION_SCHEDULE_VIEW.md` - Publication schedule view implementation
- `FACEBOOK_MESSAGES_POST_TYPE.md` - Messages post type details
- `CALENDAR_SYSTEM_TECHNICAL_DOCUMENTATION.md` - Overall calendar system

---

*Documentation created: 2026-01-22 after fixing week view data source inconsistency*
