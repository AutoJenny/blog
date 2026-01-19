#!/bin/bash
#
# Stop Monitor Script
# Stops the background posting monitor gracefully
#

set -euo pipefail

# Absolute project root
ROOT_DIR="/Users/autojenny/Documents/projects/blog"
PID_FILE="$ROOT_DIR/logs/background_posting.pid"

echo "=========================================="
echo "Stopping Background Posting Monitor"
echo "=========================================="

if [ ! -f "$PID_FILE" ]; then
    echo ""
    echo "⚠️  No PID file found - monitor may not be running"
    exit 0
fi

PID=$(cat "$PID_FILE" 2>/dev/null || echo "")

if [ -z "$PID" ]; then
    echo ""
    echo "⚠️  PID file is empty - monitor may not be running"
    rm -f "$PID_FILE"
    exit 0
fi

# Check if process is actually running
if ! ps -p "$PID" > /dev/null 2>&1; then
    echo ""
    echo "⚠️  Process $PID is not running (stale PID file)"
    rm -f "$PID_FILE"
    exit 0
fi

echo ""
echo "Stopping monitor (PID: $PID)..."

# Send SIGTERM for graceful shutdown
kill -TERM "$PID" 2>/dev/null || true

# Wait up to 10 seconds for graceful shutdown
for i in {1..10}; do
    if ! ps -p "$PID" > /dev/null 2>&1; then
        echo "✅ Monitor stopped gracefully"
        rm -f "$PID_FILE"
        exit 0
    fi
    sleep 1
done

# If still running, force kill
if ps -p "$PID" > /dev/null 2>&1; then
    echo "⚠️  Monitor didn't stop gracefully, forcing kill..."
    kill -9 "$PID" 2>/dev/null || true
    sleep 1
    rm -f "$PID_FILE"
    echo "✅ Monitor stopped (forced)"
else
    echo "✅ Monitor stopped"
    rm -f "$PID_FILE"
fi
