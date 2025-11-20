#!/bin/bash
# Setup script for newsletter source prefetch cron job

echo "Setting up newsletter source prefetch cron job..."

PROJECT_DIR="/Users/autojenny/Documents/projects/blog"
SCRIPT_PATH="$PROJECT_DIR/blog-core/newsletter/jobs/daily_source_check.py"
LOG_DIR="$PROJECT_DIR/logs"
LOG_FILE="$LOG_DIR/newsletter_prefetch.log"

# Ensure log directory exists
mkdir -p "$LOG_DIR"

# Create the cron job entry (runs daily at 6:00 AM)
CRON_JOB="0 6 * * * cd $PROJECT_DIR && /usr/bin/python3 $SCRIPT_PATH >> $LOG_FILE 2>&1"

# Add to crontab (avoid duplicates)
(crontab -l 2>/dev/null | grep -v "daily_source_check.py"; echo "$CRON_JOB") | crontab -

echo "✓ Cron job added: $CRON_JOB"
echo ""
echo "The prefetch job will run daily at 6:00 AM to fetch news, events, and weather items."
echo ""
echo "To view current crontab: crontab -l"
echo "To remove this cron job: crontab -e (then delete the line)"
echo ""
echo "Logs will be written to:"
echo "  - $LOG_FILE"

