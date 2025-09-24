#!/bin/bash
# Automated Posting Cron Job Script
# Runs every 30 minutes to check for due posts and schedule them with staggered timing

# Set working directory
cd /Users/autojenny/Documents/projects/blog

# Set environment variables
export PYTHONPATH="/Users/autojenny/Documents/projects/blog:$PYTHONPATH"
export DB_HOST="localhost"
export DB_NAME="blog"
export DB_USER="autojenny"

# Run the automated posting script
python3 scripts/automated_posting.py

# Log the exit code
echo "$(date): Automated posting completed with exit code $?" >> logs/automated_posting_cron.log
