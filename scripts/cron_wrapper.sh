#!/bin/bash
# Cron wrapper for automated posting system

# Set environment
export PATH="/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin"
export PYTHONPATH="/Users/autojenny/Documents/projects/blog"
export DB_HOST="localhost"
export DB_NAME="blog"
export DB_USER="autojenny"

# Change to project directory
cd /Users/autojenny/Documents/projects/blog

# Run the posting system
bash scripts/run_complete_posting_system.sh
