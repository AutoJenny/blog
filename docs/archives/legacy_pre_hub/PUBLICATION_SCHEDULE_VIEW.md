# Publication Schedule View

**Status:** Production Ready  
**URL:** `http://localhost:5000/planning/calendar?tab=publication-schedule`  
**Last Updated:** 2026-01-22

---

## Overview

The Publication Schedule view provides a week-by-week overview of all scheduled posts organized by channel (Blog, Facebook, Instagram, Twitter, Newsletter). It shows post **types** (not specific content) and their scheduled days and times, making it easy to see the overall publication pattern and make adjustments.

---

## Features

### 1. Channel-Based Organization
- Posts are grouped by channel (Blog, Facebook, Instagram, Twitter, Newsletter)
- Each channel shows a 7-day grid (Monday through Sunday)
- Items are placed in the appropriate day column based on their `publication_day` configuration

### 2. Post Type Display
- Shows **post types** (Word, Phrase, Insult, Product, Theme, Recipe, etc.) rather than specific content
- This provides a clean, high-level view of what's scheduled
- Prevents clutter from showing every individual post

### 3. Scheduled Time Display
- **Automated Facebook posts** show their scheduled time (e.g., "Word @ 09:00")
- Times are pulled from `posting_queue` when available (for non-published posts)
- Falls back to `post_type_channel_config.publication_time` if no queue entry exists
- Defaults to 09:00 for weekly content (Word, Phrase, Insult) if no time is configured
- **Weird times** (like 00:04 from auto-publishing) are filtered out in favor of intended times

### 4. Automation Indicators
- **🤖 Automated** (green): Items created and published automatically
  - Weekly content: Word, Phrase, Insult
  - Product posts
- **🔧 Manual** (orange): Items requiring manual creation
  - Theme posts
  - Recipe posts
  - Profile posts

### 5. Edit Schedule
- Click the **edit icon** (pencil) on any item to open the schedule edit modal
- Change the **day of week** (Monday-Sunday)
- Change the **scheduled time** (HH:MM format)
- For automated items, updates both:
  - `post_type_channel_config` (configuration)
  - `posting_queue` entries for the current week (actual scheduled posts)

---

## Data Sources

### Primary: `post_type_channel_config`
The schedule is primarily built from `post_type_channel_config`, which defines:
- Which post types are published on which channels
- What day of week (`publication_day`: 1=Monday, 7=Sunday)
- What time (`publication_time`: HH:MM format)
- Whether the configuration is active

### Secondary: `posting_queue`
For automated Facebook posts, the API also queries `posting_queue` to get:
- Actual scheduled times for non-published posts
- This overrides the config time when available
- Includes published posts to show historical times
- Filters out "weird" times (hour < 8) in favor of intended times

### Products: `daily_posts_schedule`
Product posts use `daily_posts_schedule` to determine:
- Which weekdays products are published
- What time products are published

---

## API Endpoint

**Endpoint:** `GET /publication/api/dashboard/schedule`

**Query Parameters:**
- `year` (optional): Year (default: current year)
- `week` (optional): ISO week number (default: current week)

**Response Structure:**
```json
{
  "success": true,
  "channels": {
    "facebook": [
      {
        "post_type": "weekly_word",
        "type_name": "Word",
        "title": "Word",
        "channel": "facebook",
        "day": 1,
        "scheduled_time": "09:00",
        "is_automated": true,
        "year": 2026,
        "week": 4
      }
    ],
    "blog": [...]
  }
}
```

---

## Update Schedule API

**Endpoint:** `POST /publication/api/dashboard/schedule/update`

**Request Body:**
```json
{
  "post_type": "weekly_word",
  "channel": "facebook",
  "day": 1,
  "time": "10:00",
  "year": 2026,
  "week": 4
}
```

**Behavior:**
1. Updates `post_type_channel_config.publication_day` and `publication_time`
2. For automated post types (weekly content, products), also updates `posting_queue` entries for the specified week:
   - Recalculates `scheduled_date` based on new day
   - Recalculates `scheduled_timestamp` based on new day and time
   - Only updates non-published, non-failed posts

---

## Technical Details

### Time Resolution Logic

1. **Check `posting_queue`** for non-published automated Facebook posts
   - Prefer non-published posts over published
   - Prefer "normal" times (hour >= 8) over weird times (like 00:04)
   - Format: Extract HH:MM from time value

2. **Fall back to `post_type_channel_config.publication_time`**
   - Use config time if no queue entry found
   - Format: Extract HH:MM from time value

3. **Default to 09:00 for weekly content**
   - If no config time and no queue time
   - Matches the default used by `automated_weekly_content_creator.py`

### Filtering Logic

- **Excludes failed posts** from queue lookup
- **Includes published posts** to show historical times
- **Filters weird times**: Times with hour < 8 are ignored for weekly content (treated as auto-publish artifacts)
- **Deduplicates**: If multiple posts exist for same type/day, prefers non-published and normal times

---

## UI Components

### Unified Item Card
- Uses `static/js/planning/unified-item-card.js`
- Displays type name, automation badge, scheduled time
- Edit button opens schedule edit modal

### Schedule Edit Modal
- Inline modal for editing day/time
- Form with dropdowns for day and time input
- Updates both config and queue entries on submit

---

## Related Documentation

- `PUBLICATION_DASHBOARD_IMPLEMENTATION_PLAN.md` - Overall dashboard architecture
- `PUBLICATION_DASHBOARD_MOCKUP_GUIDE.md` - Dashboard user guide
- `CALENDAR_SYSTEM_UI_REVIEW.md` - Calendar system overview

---

## Recent Changes

### 2026-01-22: Scheduled Time Display Fix
- **Issue**: Word and Phrase posts weren't showing scheduled times
- **Root Cause**: 
  - Published posts were excluded from queue lookup
  - Config had `publication_time = NULL` for weekly content
  - Weird times (00:04) from auto-publishing were being displayed
- **Fix**:
  - Include published posts in queue lookup
  - Prefer "normal" times (hour >= 8) over weird times
  - Default to 09:00 for weekly content if no time found
  - Filter out weird times in favor of intended times

---

*Documentation created: 2026-01-22*
