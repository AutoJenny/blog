#!/bin/bash
#
# Start Monitor Script
# Simple script to start the background posting monitor
#

set -euo pipefail

# Absolute project root
ROOT_DIR="/Users/autojenny/Documents/projects/blog"
cd "$ROOT_DIR"

echo "=========================================="
echo "Starting Background Posting Monitor"
echo "=========================================="

# Check if PostgreSQL is running
echo ""
echo "Checking PostgreSQL..."
if ! ps aux | grep -E "postgres.*blog|postgres.*5432" | grep -v grep > /dev/null 2>&1; then
    echo "⚠️  Warning: PostgreSQL may not be running"
    echo "   Start with: brew services start postgresql@14"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
else
    echo "✅ PostgreSQL appears to be running"
fi

# Check if monitor is already running
PID_FILE="$ROOT_DIR/logs/background_posting.pid"
if [ -f "$PID_FILE" ]; then
    PID=$(cat "$PID_FILE" 2>/dev/null || echo "")
    if [ -n "$PID" ] && ps -p "$PID" > /dev/null 2>&1; then
        echo ""
        echo "⚠️  Monitor is already running (PID: $PID)"
        echo "   Use 'stop_monitor.sh' to stop it first"
        exit 1
    else
        echo ""
        echo "Cleaning up stale PID file..."
        rm -f "$PID_FILE"
    fi
fi

# Start the monitor
echo ""
echo "Starting monitor..."
MONITOR_SCRIPT="$ROOT_DIR/scripts/background_posting_monitor.sh"

if [ ! -f "$MONITOR_SCRIPT" ]; then
    echo "❌ Error: Monitor script not found: $MONITOR_SCRIPT"
    exit 1
fi

# Make sure it's executable
chmod +x "$MONITOR_SCRIPT"

# Start in background
nohup /bin/bash "$MONITOR_SCRIPT" >> "$ROOT_DIR/logs/background_posting.log" 2>&1 &
MONITOR_PID=$!

# Wait a moment for PID file to be created
sleep 2

# Verify it started
if [ -f "$PID_FILE" ]; then
    ACTUAL_PID=$(cat "$PID_FILE")
    if ps -p "$ACTUAL_PID" > /dev/null 2>&1; then
        echo ""
        echo "✅ Monitor started successfully!"
        echo "   PID: $ACTUAL_PID"
        echo "   Log: $ROOT_DIR/logs/background_posting.log"
        echo ""
        echo "Check status: curl http://localhost:5000/monitoring/status"
        exit 0
    else
        echo ""
        echo "❌ Monitor process not found (PID: $ACTUAL_PID)"
        echo "   Check logs: $ROOT_DIR/logs/background_posting.log"
        exit 1
    fi
else
    echo ""
    echo "❌ Monitor failed to start (PID file not created)"
    echo "   Check logs: $ROOT_DIR/logs/background_posting.log"
    exit 1
fi
