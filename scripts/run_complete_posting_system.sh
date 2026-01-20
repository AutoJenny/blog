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
echo "$(date): Working directory: $(pwd)" >> logs/complete_posting_system.log
echo "$(date): Python path: $PYTHONPATH" >> logs/complete_posting_system.log

# Step 1: Run the automated posting scheduler (staggered timing)
echo "$(date): Running automated posting scheduler" >> logs/complete_posting_system.log
echo "$(date): Command: python3 scripts/automated_posting.py" >> logs/complete_posting_system.log
python3 scripts/automated_posting.py 2>&1 | tee -a logs/complete_posting_system.log
SCHEDULER_EXIT_CODE=${PIPESTATUS[0]}
echo "$(date): Scheduler completed with exit code: $SCHEDULER_EXIT_CODE" >> logs/complete_posting_system.log

# Step 2: Run the posting executor (actual posting)
echo "$(date): Running posting executor" >> logs/complete_posting_system.log
echo "$(date): Command: python3 scripts/scheduled_posting_executor.py" >> logs/complete_posting_system.log
python3 scripts/scheduled_posting_executor.py 2>&1 | tee -a logs/complete_posting_system.log
EXECUTOR_EXIT_CODE=${PIPESTATUS[0]}
echo "$(date): Executor completed with exit code: $EXECUTOR_EXIT_CODE" >> logs/complete_posting_system.log

# Log results
echo "$(date): Final results - Scheduler exit code: $SCHEDULER_EXIT_CODE, Executor exit code: $EXECUTOR_EXIT_CODE" >> logs/complete_posting_system.log

# Exit with error if either failed
if [ $SCHEDULER_EXIT_CODE -ne 0 ] || [ $EXECUTOR_EXIT_CODE -ne 0 ]; then
    echo "$(date): Complete posting system failed" >> logs/complete_posting_system.log
    exit 1
else
    echo "$(date): Complete posting system completed successfully" >> logs/complete_posting_system.log
    exit 0
fi
