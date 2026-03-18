# Newsletter Source Prefetch Scheduling

## Problem

The prefetch job (`prefetch_sources.py`) is not scheduled to run automatically. All sources were last fetched on **November 2, 2025** (18 days ago), which is why no recent news or events items are available.

## Current Status

- **Prefetch Job**: ✅ Working (tested manually - fetched 129 items successfully)
- **Sources Configured**: ✅ 15 enabled sources (BBC Scotland, The Herald, The Scotsman, HES, VisitScotland, etc.)
- **Automatic Scheduling**: ❌ **NOT SET UP**

## Solution

The prefetch job needs to be scheduled to run daily. There are two options:

### Option 1: Cron Job (Recommended)

Create a cron job to run the daily source check:

```bash
# Add to crontab (runs daily at 6:00 AM)
0 6 * * * cd /Users/autojenny/Documents/projects/blog && /usr/bin/python3 blog-core/newsletter/jobs/daily_source_check.py >> logs/newsletter_prefetch.log 2>&1
```

### Option 2: Manual Trigger via UI

The prefetch can be triggered manually via:
- **URL**: `POST /newsletter/sources/fetch`
- **UI**: Newsletter Sources Management page (if button exists)

## Files Involved

- `blog-core/newsletter/jobs/prefetch_sources.py` - Main prefetch logic
- `blog-core/newsletter/jobs/daily_source_check.py` - Wrapper for scheduled execution
- `blueprints/newsletter.py` - Manual trigger route (`/newsletter/sources/fetch`)

## Next Steps

1. Set up cron job for daily execution
2. Monitor logs to ensure it runs successfully
3. Verify new items appear in the database daily

