# Facebook Messages Post Type

**Status:** Production Ready  
**Date:** 2026-01-22  
**Purpose:** Replace Saturday product posts with text-only Facebook Messages posts

---

## Overview

The Messages post type is a new automated Facebook post type that publishes calm, human, non-promotional text-only messages on Saturdays at 14:30 UK time. These posts replace the previous Saturday product posts and are designed to build trust rather than drive sales.

---

## Features

### Posting Schedule
- **Day:** Saturday only (day 6)
- **Time:** 14:30 UK time (automatically adjusts for BST/GMT)
- **Frequency:** One post per Saturday (no additional posts)
- **Order:** Sequential from CSV, looping back to start when finished

### Content Rules
- **Text-only by default:** No images, emojis, hashtags, or links
- **Exact wording preserved:** Do not modify wording, punctuation, or spacing
- **Line breaks:** CSV includes `\n\n` which are converted to real line breaks
- **Format:** Two short paragraphs (separated by line break)
- **Case:** Sentence case only (no auto-title-case)
- **No CTAs:** No "Call now", phone numbers, or marketing language

### Images (if manually added later)
- Must contain no text overlays
- Must be calm, real photography
- Must not change or repeat the post text

---

## Data Source

### CSV File
**Location:** `data/facebook_messages.csv`

**Format:**
```csv
message
"Message text with \n\n for line breaks."
"Another message..."
```

**Content:** 29 messages total, posted sequentially

---

## Database Configuration

### Post Type Configuration
**Table:** `post_type_channel_config`

**Configuration:**
- `post_type`: `'message'`
- `channel`: `'facebook'`
- `content_format`: `'syndication'`
- `publication_day`: `6` (Saturday)
- `publication_time`: `'14:30:00'`
- `is_automated`: `TRUE`

### Posting Queue
**Table:** `posting_queue`

**Fields used:**
- `content_type`: `'message'`
- `platform`: `'facebook'`
- `generated_content`: Message text with line breaks preserved
- `scheduled_date`: Saturday date
- `scheduled_time`: `'14:30:00'`
- `status`: `'draft'` → `'ready'` → `'published'`

---

## Automation Scripts

### Message Post Creator
**File:** `scripts/automated_message_post_creator.py`

**Purpose:** Creates `posting_queue` entries for upcoming Saturdays

**How it works:**
1. Loads messages from CSV file
2. Finds upcoming Saturdays (default: 14 days ahead)
3. Gets last used message index from published posts
4. Creates draft posts sequentially, looping back to start
5. Skips dates that already have posts or are in the past

**Usage:**
```bash
python3 scripts/automated_message_post_creator.py
```

**Integration:** Should be run daily (e.g., via cron or background monitor)

---

## Publishing

### Facebook Publisher
**File:** `utils/platform_publishers.py`

**Function:** `publish_to_facebook()`

**Message Post Handling:**
- Detects `content_type == 'message'`
- Uses `/feed` endpoint (text-only, not `/photos`)
- Posts to both Facebook pages (Scotweb CLAN and CLAN by Scotweb)
- Preserves line breaks in message text
- No image upload required

### Scheduled Posting Executor
**File:** `scripts/scheduled_posting_executor.py`

**Handling:**
- Message posts are included in `get_due_posts()` query
- Routed to `publish_to_facebook()` like other Facebook posts
- Status updated to `'published'` on success, `'failed'` on error

---

## Publication Schedule View

### Display
**URL:** `http://localhost:5000/planning/calendar?tab=publication-schedule`

**Saturday Display:**
- Shows "Message" type (not "Product")
- Shows scheduled time: "14:30"
- Marked as automated (🤖 icon)
- Can be edited (day/time) via edit button

### API
**Endpoint:** `GET /publication/api/dashboard/schedule`

**Response includes:**
```json
{
  "channels": {
    "facebook": [
      {
        "post_type": "message",
        "type_name": "Message",
        "day": 6,
        "scheduled_time": "14:30",
        "is_automated": true
      }
    ]
  }
}
```

---

## Product Post Changes

### Saturday Removed
- Product posts no longer scheduled for Saturday
- `daily_posts_schedule` updated to exclude day 6 (Saturday)
- Publication dashboard excludes Saturday from product display

**Before:**
- Saturday: Product @ 15:00

**After:**
- Saturday: Message @ 14:30
- Sunday: Product @ 15:00 (unchanged)

---

## Sequential Posting Logic

### Message Index Tracking
The system tracks which message was last used by:
1. Finding all published message posts
2. Matching their content against the CSV messages
3. Using the index of the most recent match
4. Starting from the next message in sequence

### Loop Behavior
- When all 29 messages have been posted, loops back to message 0
- Ensures continuous posting without gaps
- No randomization - strictly sequential

---

## Migration

### Database Migration
**File:** `migrations/20260122_add_message_post_type.sql`

**Changes:**
- Adds `message` post type to `post_type_channel_config`
- Sets Saturday (day 6) at 14:30
- Marks as automated

**Run:**
```bash
python3 -c "
from config.database import db_manager
with open('migrations/20260122_add_message_post_type.sql') as f:
    sql = f.read()
with db_manager.get_connection() as conn:
    with conn.cursor() as cursor:
        cursor.execute(sql)
        conn.commit()
"
```

---

## Testing

### Create Test Posts
```bash
python3 scripts/automated_message_post_creator.py
```

### Verify Posts Created
```sql
SELECT id, scheduled_date, scheduled_time, status, 
       LEFT(generated_content, 50) as preview
FROM posting_queue
WHERE content_type = 'message'
ORDER BY scheduled_date;
```

### Verify Publication Schedule
```bash
curl "http://localhost:5000/publication/api/dashboard/schedule?year=2026&week=4" | jq '.channels.facebook[] | select(.day == 6)'
```

---

## Files Created/Modified

### Created
- `data/facebook_messages.csv` - Message content (29 messages)
- `scripts/automated_message_post_creator.py` - Post creation script
- `migrations/20260122_add_message_post_type.sql` - Database migration
- `docs/FACEBOOK_MESSAGES_POST_TYPE.md` - This documentation

### Modified
- `utils/platform_publishers.py` - Added text-only posting for messages
- `blueprints/publication_dashboard.py` - Added message type to schedule display
- `daily_posts_schedule` table - Removed Saturday from product schedules

---

## Integration with Background Monitor

The message post creator should be added to the background posting monitor:

**File:** `scripts/background_posting_monitor.sh`

**Add:**
```bash
# Create message posts for upcoming Saturdays
python3 /path/to/scripts/automated_message_post_creator.py
```

---

## Future Enhancements

### Potential Additions
- Manual image attachment (with validation rules)
- Message editing UI
- Analytics tracking
- A/B testing different messages

### Not Planned
- Randomization (strictly sequential)
- Multiple posts per day
- Other days of week
- Auto-generated content

---

*Documentation created: 2026-01-22*
