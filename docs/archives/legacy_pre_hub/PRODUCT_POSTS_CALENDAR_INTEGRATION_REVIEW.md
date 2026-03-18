# Product Posts Calendar Integration Review

**Date:** 2026-01-XX  
**Purpose:** Review current state of product post scheduling data and plan integration into Social Posts calendar

---

## Current State of Product Post Scheduling

### Data in `posting_queue` Table

**Total Product Posts:** 84  
**Upcoming Scheduled:** 8 posts

**Upcoming Product Posts:**
- 2026-01-18 15:00 - Product ID 152532
- 2026-01-20 17:00 - Product ID 687
- 2026-01-22 17:00 - Product ID 689
- 2026-01-24 15:00 - Product ID 143514
- 2026-01-25 15:00 - Product ID 67
- 2026-01-27 17:00 - Product ID 203
- 2026-01-29 17:00 - Product ID 7627
- 2026-01-31 15:00 - Product ID 965

**Status:** All are `ready` status

### Active Schedules in `daily_posts_schedule`

**Schedule 1: Weekends**
- Time: 15:00:00
- Days: [6, 7] (Saturday, Sunday)
- Platform: facebook
- Content Type: product
- Active: True

**Schedule 2: TuesThurs5pm**
- Time: 17:00:00
- Days: [2, 4] (Tuesday, Thursday)
- Platform: facebook
- Content Type: product
- Active: True

---

## Current Calendar System Architecture

### Supported Categories
The calendar system currently supports:
- `theme` - Blog Posts
- `recipe` - Blog Posts
- `profile_product` - Blog Posts
- `profile_surname` - Blog Posts
- `weekly_word` - Social Posts
- `weekly_phrase` - Social Posts
- `weekly_insult` - Social Posts

**Product posts are NOT currently supported.**

### How Calendar System Works

1. **JSON Files:** Pre-computed JSON files in `data/calendar/schedule/<category>/<year>.json`
2. **Array Format:** Each file contains array of objects: `[{week: 1, item_id: ..., position: ..., title: ...}, ...]`
3. **Builder Script:** `scripts/build_calendar_schedules.py` generates JSON from database base lists
4. **Display API:** `blueprints/planning_api_calendar_scheduling_cache.py` reads JSON files (no DB queries)
5. **Week Resolution:** Uses ISO week numbers (1-52) per year

### Current Data Structure

**Weekly Content (Reference):**
- Stored in `calendar_ideas` table
- Has `week_number` field (1-52, perpetual)
- JSON builder reads from base lists and applies cyclic logic
- One item per week per category

**Product Posts (Current):**
- Stored in `posting_queue` table
- Has `scheduled_date` and `scheduled_time` (specific dates, not week numbers)
- Uses `daily_posts_schedule` for recurring patterns
- Multiple posts can be scheduled per week/day

---

## Integration Challenges

### Challenge 1: Date-Based vs Week-Based

**Problem:**
- Product posts use **specific dates** (`scheduled_date`, `scheduled_timestamp`)
- Calendar system uses **week numbers** (1-52 per year)
- Need to convert dates to week numbers for calendar display

**Solution:**
- Convert `scheduled_date` to ISO week number
- Group product posts by week
- Display all product posts scheduled for that week

### Challenge 2: Multiple Posts Per Week

**Problem:**
- Weekly content: **1 item per week** (word on Monday, phrase on Wednesday, insult on Friday)
- Product posts: **Multiple posts per week** (could be 2-7 posts per week based on schedules)

**Solution:**
- Calendar can show multiple product posts per week
- Display as list/stack in the cell
- Or show count with "X products" label

### Challenge 3: No Base List for Products

**Problem:**
- Weekly content has base lists in database (`calendar_ideas`, `calendar_themes`, etc.)
- Product posts don't have a base list - they're created ad-hoc
- JSON builder expects base lists with positions

**Solution Options:**
- **Option A:** Read directly from `posting_queue` (bypass JSON system)
- **Option B:** Create virtual base list from `posting_queue` entries
- **Option C:** Generate JSON on-the-fly from `posting_queue` queries

### Challenge 4: Recurring vs One-Off

**Problem:**
- Weekly content: **Cyclic/recurring** (same items repeat each year)
- Product posts: **One-off** (specific products on specific dates)
- `daily_posts_schedule` defines patterns, but actual products are in `posting_queue`

**Solution:**
- Product posts are date-specific, not cyclic
- Need to read from `posting_queue` for actual scheduled items
- Can't use the same JSON builder pattern

---

## Recommended Integration Approach

### Option 1: Direct Database Query (Recommended)

**Approach:**
- Add `product` to `CATEGORIES` list in `planning_api_calendar_scheduling_cache.py`
- In `scheduling_all()`, query `posting_queue` directly for product posts
- Convert `scheduled_date` to ISO week numbers
- Group by week and include in schedule response

**Pros:**
- Works with existing date-based scheduling
- No need to generate JSON files
- Real-time data (always current)
- Handles multiple posts per week naturally

**Cons:**
- Requires database query (but only for product posts)
- Different from other categories (which use JSON)

### Option 2: Hybrid JSON + Database

**Approach:**
- Generate JSON files for product posts from `posting_queue`
- Update JSON when `posting_queue` changes
- Use same JSON loader as other categories

**Pros:**
- Consistent with other categories
- Fast display (no DB queries)

**Cons:**
- Requires JSON regeneration on every schedule change
- More complex (need to sync JSON with queue)

---

## Implementation Plan

### Phase 1: Add Product Posts to Calendar API

1. **Update `planning_api_calendar_scheduling_cache.py`:**
   - Add `product` to `CATEGORIES` list
   - Add `build_schedule_item()` handler for `product` category
   - Query `posting_queue` for product posts in date range
   - Convert dates to week numbers
   - Group by week

2. **Add Product Post Query Function:**
   ```python
   def get_product_posts_for_weeks(week_list):
       """Get product posts for a list of (year, week) tuples"""
       # Query posting_queue for dates in those weeks
       # Return grouped by week
   ```

3. **Update `build_schedule_item()`:**
   - Add case for `cat == "product"`
   - Return structure: `{"type": "product", "product_id": ..., "title": ..., ...}`

### Phase 2: Update Frontend

1. **Add Product Column to Scheduling Table:**
   - Add "Product" header in Social Posts section
   - Update `createCategoryCell()` to handle `product` category
   - Display product posts in cells

2. **Update Week View:**
   - Add product posts to Social Posts section
   - Show product posts for each day of the week

3. **Styling:**
   - Use consistent styling with other social posts
   - Show product name/title
   - Link to product post details

### Phase 3: Status Resolution

1. **Update `publication_status_resolver.py`:**
   - Add product post status resolution
   - Link `posting_queue.id` to post status
   - Show publication status for product posts

---

## Data Structure for Product Posts in Calendar

### API Response Format

```json
{
  "type": "product",
  "product_id": 152532,
  "posting_queue_id": 642,
  "title": "Product Name",
  "scheduled_date": "2026-01-18",
  "scheduled_time": "15:00:00",
  "position": 1,  // Order within the week
  "post_id": null,  // If linked to a blog post
  "post_exists": false,
  "post_status": null
}
```

### Multiple Posts Per Week

If multiple product posts are scheduled for the same week:
- Return array of product items
- Frontend displays as list or stack
- Each item is clickable/editable

---

## Questions to Resolve

1. **Display Format:**
   - Show all product posts in one cell per week?
   - Or show count with "X products" and expand on click?
   - Or show as separate rows?

2. **Day Assignment:**
   - Should product posts show on specific days in week view?
   - Or just show in the week cell?

3. **Integration with Schedules:**
   - Should we show scheduled patterns from `daily_posts_schedule`?
   - Or only show actual scheduled posts from `posting_queue`?

4. **Future Scheduling:**
   - Should product posts use calendar JSON system?
   - Or continue using `posting_queue` with date-based scheduling?

---

## Next Steps

1. **Review this analysis** with user
2. **Decide on integration approach** (Option 1 vs Option 2)
3. **Implement API changes** to include product posts
4. **Update frontend** to display product posts
5. **Test with current data** (8 upcoming posts)

---

## Current Data Summary

- **84 total product posts** in queue
- **8 upcoming posts** scheduled (Jan 18-31, 2026)
- **2 active schedules** (Weekends 15:00, TuesThurs 17:00)
- **All upcoming posts** are `ready` status
- **Posts span multiple weeks** (2026-W03 through 2026-W05)
