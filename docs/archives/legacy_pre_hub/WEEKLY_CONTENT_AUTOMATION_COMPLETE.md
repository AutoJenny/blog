# Weekly Content Automation - Implementation Complete

**Date:** 2026-01-17  
**Status:** ✅ **FULLY AUTOMATED** - Weekly content now publishes automatically based on schedule

---

## Overview

The weekly content system is now **fully automated**. Weekly word/phrase/insult posts are automatically:
1. **Created** 1 week in advance based on the calendar schedule
2. **Processed** through the complete workflow (caption generation, image creation)
3. **Published** to Facebook at the scheduled time

**No manual intervention required** - the system runs automatically via background monitor.

---

## Automation Flow

### 1. Automatic Creation (1 Week in Advance)

**Script:** `scripts/automated_weekly_content_creator.py`

**What it does:**
- Runs daily (via `background_posting_monitor.sh`)
- Checks upcoming weeks (next 7 days)
- Resolves weekly content items from calendar schedule using `resolve_item_for_week()`
- Creates `posting_queue` entries with:
  - `status='draft'`
  - `scheduled_date` = Monday of the week
  - `scheduled_time` = 09:00 (default, configurable)
  - `idea_id` properly linked to `calendar_ideas.id`

**When it runs:** Every 5 minutes (via background monitor)

**Output:** Draft posts in `posting_queue` table, ready for workflow execution

---

### 2. Automatic Workflow Execution

**Script:** `scripts/automated_weekly_content_workflow.py`

**What it does:**
- Finds draft weekly content posts (`status='draft'`)
- Executes all workflow stages automatically:
  1. `format_for_facebook` - Formats content
  2. `generate_caption` - Generates caption with Ollama
  3. `add_hashtags` - Adds hashtags
  4. `optimize_for_facebook` - Generates square image with ImageMagick
  5. `publish_to_facebook` - Publishes if scheduled time has passed, otherwise sets status to 'ready'

**When it runs:** Every 5 minutes (via background monitor)

**Output:** 
- Posts with images and captions generated
- Status updated to `'ready'` if scheduled time hasn't passed
- Status updated to `'published'` if published immediately

---

### 3. Automatic Publishing

**Script:** `scripts/posting_executor.py` (updated)

**What it does:**
- Finds posts with `status='ready'` or `'pending'` that are due
- Checks if scheduled time has passed
- Publishes to Facebook using appropriate workflow:
  - **Weekly content:** Uses `execute_publish_to_facebook()` (weekly content workflow)
  - **Product posts:** Uses `execute_facebook_post()` (product workflow)
- Updates status to `'published'` on success

**When it runs:** Every 5 minutes (via background monitor)

**Output:** Posts published to both Facebook pages

---

## Background Monitor

**Script:** `scripts/background_posting_monitor.sh`

**What it does:**
- Runs continuously, checking every 5 minutes
- Executes automation scripts in order:
  1. `automated_weekly_content_creator.py` - Create posts
  2. `automated_weekly_content_workflow.py` - Execute workflows
  3. `automated_posting.py` - Product post scheduling
  4. `posting_executor.py` - Publish due posts

**To start:**
```bash
./scripts/background_posting_monitor.sh
```

**To stop:**
```bash
kill $(cat logs/background_posting.pid)
```

---

## Configuration

### Publication Day and Time

**Default:** Monday at 09:00

**To change:** Edit `scripts/automated_weekly_content_creator.py`:
```python
self.default_publication_day = 1  # Monday (1=Monday, 7=Sunday)
self.default_publication_time = "09:00"  # 9 AM
```

### Days Ahead

**Default:** 7 days (1 week)

**To change:** Edit `scripts/automated_weekly_content_creator.py`:
```python
stats = creator.create_weekly_content_posts(days_ahead=7)
```

---

## Test Results

**Creation Script:**
- ✅ Created 6 posts for 2 upcoming weeks
- ✅ All posts have proper `idea_id` linkage
- ✅ Scheduled dates set correctly

**Workflow Script:**
- ✅ Successfully executed all workflow stages
- ✅ Generated images and captions
- ✅ Published posts that were due (scheduled date in past)
- ✅ Set status to 'ready' for future posts

**Publishing:**
- ✅ Posts published to both Facebook pages
- ✅ Status updated to 'published'
- ✅ Platform post IDs stored

---

## Files Created/Modified

### New Files
- `scripts/automated_weekly_content_creator.py` - Creates posting_queue entries
- `scripts/automated_weekly_content_workflow.py` - Executes workflow stages

### Modified Files
- `scripts/posting_executor.py` - Added weekly content support
- `scripts/background_posting_monitor.sh` - Added weekly content automation steps

---

## How It Works

### Timeline Example

**Week 1 (Monday):**
- Background monitor runs every 5 minutes
- Creator script checks week 2 (7 days ahead)
- Creates draft posts for week 2's weekly content
- Workflow script processes drafts → generates images/captions
- Status set to 'ready' (scheduled date is in future)

**Week 2 (Monday 09:00):**
- Background monitor runs
- Posting executor finds 'ready' posts with scheduled time passed
- Publishes to Facebook automatically
- Status updated to 'published'

**Result:** Weekly content publishes automatically on schedule with zero manual intervention.

---

## Monitoring

**Log Files:**
- `logs/automated_weekly_content_creator.log` - Creation activity
- `logs/automated_weekly_content_workflow.log` - Workflow execution
- `logs/posting_executor.log` - Publishing activity
- `logs/background_posting.log` - Overall monitor activity

**Check Status:**
```bash
# View recent activity
tail -f logs/background_posting.log

# Check for errors
grep ERROR logs/automated_weekly_content_*.log
```

---

## Troubleshooting

### Posts Not Being Created

**Check:**
1. Is background monitor running? `ps aux | grep background_posting`
2. Are there weekly content items in the schedule? Check calendar schedule API
3. Check logs: `tail -f logs/automated_weekly_content_creator.log`

### Workflow Not Executing

**Check:**
1. Are there draft posts? Query `posting_queue` for `status='draft'`
2. Check logs: `tail -f logs/automated_weekly_content_workflow.log`
3. Verify Ollama is running (for caption generation)
4. Verify ImageMagick is installed (for image generation)

### Posts Not Publishing

**Check:**
1. Is scheduled time in the past? Check `scheduled_date` and `scheduled_time`
2. Is status 'ready'? Check `posting_queue.status`
3. Check logs: `tail -f logs/posting_executor.log`
4. Verify Facebook credentials are configured

---

## Status

✅ **FULLY AUTOMATED** - System is production-ready and requires no manual intervention.

Weekly content will automatically:
- Appear in posting_queue 1 week in advance
- Have images and captions generated automatically
- Publish to Facebook at the scheduled time

---

**Last Updated:** 2026-01-17
