# Product Posts Integration Report

**Date:** 2025-12-11  
**Issue:** Product posts from `/launchpad/syndication/facebook/product_post` are not appearing in the publication schedule at `/planning/calendar?year=2025&week=50&tab=publication-schedule`

---

## Investigation Summary

### Current State

**Product Posts Exist:**
- **15 product posts** found in `posting_queue` table for week 50, 2025 (Dec 8-14)
  - 5 posts with scheduled dates (Dec 9, 11, 13, 14)
  - 10 posts in draft status (unscheduled)
- **2 active schedules** in `daily_posts_schedule` table:
  - Weekends (Sat/Sun) at 15:00 GMT
  - TuesThurs5pm (Tue/Thu) at 17:00 GMT

**Publication Schedule API:**
- Location: `blueprints/publication_dashboard.py::api_dashboard_schedule()`
- **Problem:** Only queries calendar JSON files for categories in `CATEGORIES`:
  - theme, recipe, profile_product, profile_surname, weekly_word, weekly_phrase, weekly_insult
- **Missing:** Does NOT query `posting_queue` table for product posts

### Root Cause

The `api_dashboard_schedule()` function (lines 216-519) processes items by:
1. Iterating through `CATEGORIES` list
2. Loading JSON schedule files for each category
3. Resolving items via `resolve_item_for_week()` for calendar items
4. Checking `post_type_channel_config` for channel assignments
5. **Never queries `posting_queue` table**

Product posts are stored in a separate system:
- **Storage:** `posting_queue` table (not calendar JSON files)
- **Scheduling:** `daily_posts_schedule` table (recurring weekday patterns)
- **Platform:** Facebook (primary), but supports multiple platforms
- **Content Type:** `content_type='product'` in `posting_queue`

---

## Integration Requirements

### 1. Immediate Fix: Add Product Posts to Publication Schedule

**File:** `blueprints/publication_dashboard.py`

**Changes Needed:**
1. After processing calendar categories, query `posting_queue` for product posts
2. Map `scheduled_date` to ISO week and weekday
3. Convert to same format as other schedule items
4. Add to appropriate channel (facebook) with correct day assignment

**Implementation:**
```python
# After line 519, add product posts from posting_queue
# Query posting_queue for scheduled product posts in this week
cursor.execute("""
    SELECT 
        pq.id as queue_id,
        pq.product_id,
        pq.scheduled_date,
        pq.scheduled_time,
        pq.status,
        pq.platform,
        pq.content_type,
        cp.name as product_name,
        pq.generated_content
    FROM posting_queue pq
    LEFT JOIN clan_products cp ON pq.product_id = cp.id
    WHERE pq.content_type = 'product'
      AND pq.scheduled_date BETWEEN %s AND %s
      AND pq.status IN ('ready', 'pending')
    ORDER BY pq.scheduled_date, pq.scheduled_time
""", (week_start_date, week_end_date))

# Convert to schedule format and add to channels['facebook']
```

### 2. Unified Automation System Architecture

Based on `docs/AUTOMATION_PIPELINE_ARCHITECTURE.md`, the system should support:

#### Stage 1: Creation (1 week in advance)
- **Trigger:** Automated job runs weekly
- **Action:** Create posts for items scheduled 1 week ahead
- **Sources:**
  - Calendar items (themes, recipes, profiles, weekly content)
  - Product posts from `posting_queue`
- **Output:** Draft posts in `post` table or `posting_queue`

#### Stage 2: Development (1 week window)
- **Duration:** Week between creation and publication
- **Process:** Content generation, editing, refinement
- **Status:** `draft` → `ready_for_review`

#### Stage 3: Editing/Approval
- **Manual Review:** Editors review and approve
- **Status:** `ready_for_review` → `approved` → `ready_to_publish`
- **Gates:** Optional approval gates per post type/channel

#### Stage 4: Publishing (scheduled time)
- **Trigger:** Background job checks `scheduled_date` + `scheduled_time`
- **Condition:** Only if status = `approved` or `ready_to_publish`
- **Action:** Publish to assigned channels
- **Time Staggering:** Use `post_type_channel_config.publication_time` or `posting_queue.scheduled_time`

---

## Current System Gaps

### 1. Product Posts Not Integrated
- ❌ Not in publication schedule view
- ❌ Not in calendar scheduling view
- ❌ Separate system from calendar items

### 2. Time-of-Day Scheduling Missing
- ❌ Blog posts don't have `scheduled_time` (only `scheduled_date`)
- ❌ Product posts have `scheduled_time` but not integrated
- ❌ Need unified `publication_time` for all post types

### 3. Multi-Stage Automation Incomplete
- ❌ No automated creation 1 week in advance
- ❌ No automated development pipeline
- ❌ No unified approval system
- ❌ No automated publishing scheduler

### 4. Redundant Systems
- ❌ `posting_queue` (product posts)
- ❌ `calendar_week_posts_v2` (blog posts)
- ❌ `calendar_schedule` (deprecated)
- ❌ Multiple scheduling systems not unified

---

## Recommended Integration Plan

### Phase 1: Immediate (This Week)
1. ✅ Add product posts to publication schedule API
2. ✅ Display product posts in publication schedule view
3. ✅ Add time-of-day display for all scheduled items

### Phase 2: Short-term (Next 2 Weeks)
1. Create unified scheduling table/view
2. Integrate `posting_queue` with calendar system
3. Add `scheduled_time` to all post types
4. Create automated creation job (1 week ahead)

### Phase 3: Medium-term (Next Month)
1. Implement 4-stage automation pipeline
2. Add approval gates per post type
3. Create unified publishing scheduler
4. Deprecate old redundant systems

### Phase 4: Long-term (Next Quarter)
1. Full automation with manual override
2. Multi-channel publishing coordination
3. Performance monitoring and alerts
4. Complete documentation

---

## Technical Implementation Notes

### Database Schema Updates Needed

1. **Add `scheduled_time` to blog posts:**
   ```sql
   ALTER TABLE calendar_week_posts_v2 
   ADD COLUMN scheduled_time TIME;
   ```

2. **Unified scheduling view:**
   ```sql
   CREATE VIEW unified_schedule AS
   -- Calendar items (themes, recipes, profiles, weekly content)
   SELECT 
       'calendar' as source_type,
       category,
       item_id,
       scheduled_date,
       scheduled_time,
       channel,
       post_id
   FROM calendar_week_posts_v2
   UNION ALL
   -- Product posts
   SELECT 
       'product' as source_type,
       'product' as category,
       product_id as item_id,
       scheduled_date,
       scheduled_time,
       platform as channel,
       NULL as post_id
   FROM posting_queue
   WHERE content_type = 'product' AND scheduled_date IS NOT NULL;
   ```

### API Endpoint Updates

1. **`/publication/api/dashboard/schedule`** - Add product posts
2. **`/planning/api/calendar/schedule`** - Include product posts option
3. **New:** `/api/automation/create-posts` - Automated creation endpoint
4. **New:** `/api/automation/publish` - Automated publishing endpoint

---

## Files to Modify

### Immediate Fix
- `blueprints/publication_dashboard.py` - Add product posts query
- `templates/planning/calendar/includes/publication_schedule_scripts.html` - Handle product posts

### Phase 2
- `utils/calendar_resolver.py` - Add product post resolution
- `blueprints/automation_core.py` - Add automated creation
- `blueprints/publication_scheduler.py` - New unified scheduler

### Phase 3
- `config/post_type_channel_config.py` - Add time scheduling
- `blueprints/approval_gates.py` - New approval system
- `scripts/automated_publisher.py` - New publishing job

---

## Next Steps

1. **Implement immediate fix** - Add product posts to publication schedule
2. **Test integration** - Verify product posts appear correctly
3. **Plan Phase 2** - Design unified scheduling system
4. **Begin automation** - Create automated creation job

