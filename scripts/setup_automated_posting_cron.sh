#!/bin/bash
# Setup script for automated posting cron job

echo "Setting up automated posting cron job..."

# Create the cron job entry
CRON_JOB="*/30 * * * * /Users/autojenny/Documents/projects/blog/scripts/run_automated_posting.sh"

# Add to crontab
(crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -

echo "Cron job added: $CRON_JOB"
echo "This will run every 30 minutes to check for due posts"
echo ""
echo "To view current crontab: crontab -l"
echo "To remove this cron job: crontab -e (then delete the line)"
echo ""
echo "Logs will be written to:"
echo "  - /Users/autojenny/Documents/projects/blog/logs/automated_posting.log"
echo "  - /Users/autojenny/Documents/projects/blog/logs/automated_posting_cron.log"
