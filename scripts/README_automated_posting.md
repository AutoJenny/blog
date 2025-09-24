# Automated Social Media Posting System

This system automatically schedules and posts social media content with staggered timing to create a natural, engaging posting pattern.

## Features

- **Staggered Posting**: Random delays (1-29 minutes) prevent posts from going out at exactly the same time daily
- **Smart Timing**: Platform and content-type specific optimal posting times
- **30-Minute Windows**: Checks for due posts every 30 minutes
- **Comprehensive Logging**: Detailed logs for monitoring and debugging
- **Easy Management**: Simple commands to install, remove, and monitor

## How It Works

1. **Cron Job**: Runs every 30 minutes via cron
2. **Due Post Detection**: Finds posts scheduled to go out in the next 30 minutes
3. **Staggered Scheduling**: Adds random delay (1-29 minutes) to each post
4. **Smart Timing**: Adjusts timing based on platform and content type
5. **Status Update**: Changes post status from 'ready' to 'pending'

## Installation

### 1. Install the Cron Job
```bash
python3 scripts/manage_automated_posting.py install
```

### 2. Verify Installation
```bash
python3 scripts/manage_automated_posting.py status
```

### 3. Test the System
```bash
python3 scripts/manage_automated_posting.py test
```

## Management Commands

### Check Status
```bash
python3 scripts/manage_automated_posting.py status
```

### View Logs
```bash
python3 scripts/manage_automated_posting.py logs
```

### Test System
```bash
python3 scripts/manage_automated_posting.py test
```

### Remove Cron Job
```bash
python3 scripts/manage_automated_posting.py remove
```

## Configuration

### Timing Windows
- **Check Interval**: Every 30 minutes
- **Random Delay**: 1-29 minutes
- **Max Future Time**: 2 hours ahead

### Platform-Specific Timing
- **Facebook**: Avoids 8-9 AM and 5-6 PM (rush hours)
- **Instagram**: Prefers 11 AM-1 PM and 5-7 PM
- **Twitter**: Avoids 8-9 AM and 5-6 PM

### Content-Type Timing
- **Blog Posts**: Prefers 10 AM-2 PM and 7-9 PM
- **Product Posts**: Prefers 11 AM-1 PM and 6-8 PM

## Log Files

- **Main Log**: `/Users/autojenny/Documents/projects/blog/logs/automated_posting.log`
- **Cron Log**: `/Users/autojenny/Documents/projects/blog/logs/automated_posting_cron.log`

## Post Status Flow

1. **ready** → Post is scheduled and ready for automated processing
2. **pending** → Post has been processed and scheduled with staggered timing
3. **published** → Post has been successfully published
4. **failed** → Post failed to publish

## Troubleshooting

### Check Cron Job
```bash
crontab -l | grep automated_posting
```

### Manual Test
```bash
cd /Users/autojenny/Documents/projects/blog
python3 scripts/automated_posting.py
```

### View Recent Logs
```bash
tail -f /Users/autojenny/Documents/projects/blog/logs/automated_posting.log
```

## Example Output

```
2025-09-24 21:21:48,778 - INFO - Starting automated posting system
2025-09-24 21:21:48,800 - INFO - Found 3 posts due for publishing in next 30 minutes
2025-09-24 21:21:48,801 - INFO - Scheduled post 123 for 2025-09-24 21:35:00 (originally 2025-09-24 21:30:00)
2025-09-24 21:21:48,802 - INFO - Scheduled post 124 for 2025-09-24 21:42:00 (originally 2025-09-24 21:30:00)
2025-09-24 21:21:48,803 - INFO - Processing complete: {'total_found': 3, 'successfully_scheduled': 3, 'failed': 0, 'skipped': 0}
```

## Benefits

- **Natural Posting Pattern**: Random delays create organic-looking posting schedule
- **Platform Optimization**: Posts go out at optimal times for each platform
- **Content-Aware**: Different timing strategies for different content types
- **Reliable**: Automated system reduces manual posting errors
- **Scalable**: Handles multiple posts efficiently
- **Monitorable**: Comprehensive logging for tracking and debugging
