#!/bin/bash

# Automated Posting Background Monitor
# Runs every 5 minutes to check for due posts

SCRIPT_DIR="/Users/autojenny/Documents/projects/blog"
LOG_FILE="$SCRIPT_DIR/logs/background_posting.log"
PID_FILE="$SCRIPT_DIR/logs/background_posting.pid"

# Function to log with timestamp
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" >> "$LOG_FILE"
}

# Function to check if already running
check_running() {
    if [ -f "$PID_FILE" ]; then
        local pid=$(cat "$PID_FILE")
        if ps -p "$pid" > /dev/null 2>&1; then
            log "Background posting already running (PID: $pid)"
            exit 1
        else
            rm -f "$PID_FILE"
        fi
    fi
}

# Function to cleanup on exit
cleanup() {
    log "Background posting monitor stopped"
    rm -f "$PID_FILE"
    exit 0
}

# Set up signal handlers
trap cleanup SIGTERM SIGINT

# Main monitoring loop
main() {
    log "Starting background posting monitor"
    echo $$ > "$PID_FILE"
    
    while true; do
        log "Checking for due posts..."
        
        # Run the posting system
        cd "$SCRIPT_DIR"
        
        # Step 1: Create weekly content posts (1 week in advance)
        log "Creating weekly content posts..."
        PYTHONPATH="$SCRIPT_DIR" /opt/homebrew/bin/python3 "$SCRIPT_DIR/scripts/automated_weekly_content_creator.py" >> "$LOG_FILE" 2>&1
        
        # Step 2: Execute workflow for draft weekly content posts
        log "Executing weekly content workflows..."
        PYTHONPATH="$SCRIPT_DIR" /opt/homebrew/bin/python3 "$SCRIPT_DIR/scripts/automated_weekly_content_workflow.py" >> "$LOG_FILE" 2>&1
        
        # Step 3: Create product posts (1 week in advance)
        log "Creating product posts..."
        PYTHONPATH="$SCRIPT_DIR" /opt/homebrew/bin/python3 "$SCRIPT_DIR/scripts/automated_product_post_creator.py" >> "$LOG_FILE" 2>&1
        
        # Step 4: Execute workflow for draft product posts
        log "Executing product post workflows..."
        PYTHONPATH="$SCRIPT_DIR" /opt/homebrew/bin/python3 "$SCRIPT_DIR/scripts/automated_product_post_workflow.py" >> "$LOG_FILE" 2>&1
        
        # Step 5: Run the automated posting scheduler (for product posts)
        log "Running automated posting scheduler..."
        PYTHONPATH="$SCRIPT_DIR" /opt/homebrew/bin/python3 "$SCRIPT_DIR/scripts/automated_posting.py" >> "$LOG_FILE" 2>&1
        
        # Step 6: Run the posting executor (handles both product and weekly content)
        log "Running posting executor..."
        PYTHONPATH="$SCRIPT_DIR" /opt/homebrew/bin/python3 "$SCRIPT_DIR/scripts/posting_executor.py" >> "$LOG_FILE" 2>&1
        
        # Wait 5 minutes
        log "Waiting 5 minutes until next check..."
        sleep 300
    done
}

# Start the monitor
check_running
main
