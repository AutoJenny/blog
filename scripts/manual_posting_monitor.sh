#!/bin/bash
# Manual posting monitor - run this periodically

echo "$(date): Starting manual posting monitor" >> logs/manual_monitor.log

# Set environment
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export PYTHONPATH="/Users/autojenny/Documents/projects/blog"
export DB_HOST="localhost"
export DB_NAME="blog"
export DB_USER="autojenny"

cd /Users/autojenny/Documents/projects/blog

# Run the posting system
bash scripts/run_complete_posting_system.sh >> logs/manual_monitor.log 2>&1

echo "$(date): Manual posting monitor complete" >> logs/manual_monitor.log
