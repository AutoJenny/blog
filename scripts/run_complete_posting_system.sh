#!/bin/bash
# Complete Automated Posting System
# Runs both the scheduler (staggered timing) and executor (actual posting)

# Set working directory
cd /Users/autojenny/Documents/projects/blog

# Set environment variables
export PYTHONPATH="/Users/autojenny/Documents/projects/blog:$PYTHONPATH"
export DB_HOST="localhost"
export DB_NAME="blog"
export DB_USER="autojenny"

echo "$(date): Starting complete posting system" >> logs/complete_posting_system.log

# Step 1: Run the automated posting scheduler (staggered timing)
echo "$(date): Running automated posting scheduler" >> logs/complete_posting_system.log
python3 scripts/automated_posting.py
SCHEDULER_EXIT_CODE=$?

# Step 2: Run the posting executor (actual posting)
echo "$(date): Running posting executor" >> logs/complete_posting_system.log
python3 scripts/posting_executor.py
EXECUTOR_EXIT_CODE=$?

# Log results
echo "$(date): Scheduler exit code: $SCHEDULER_EXIT_CODE, Executor exit code: $EXECUTOR_EXIT_CODE" >> logs/complete_posting_system.log

# Exit with error if either failed
if [ $SCHEDULER_EXIT_CODE -ne 0 ] || [ $EXECUTOR_EXIT_CODE -ne 0 ]; then
    echo "$(date): Complete posting system failed" >> logs/complete_posting_system.log
    exit 1
else
    echo "$(date): Complete posting system completed successfully" >> logs/complete_posting_system.log
    exit 0
fi
