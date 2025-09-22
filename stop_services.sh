#!/bin/bash

echo "Stopping all blog services..."

# Kill all Python processes running app.py
pkill -f "python.*app.py" 2>/dev/null || true

# Wait a moment for processes to stop
sleep 2

# Check if any are still running
if pgrep -f "python.*app.py" > /dev/null; then
    echo "Some processes still running, force killing..."
    pkill -9 -f "python.*app.py" 2>/dev/null || true
    sleep 1
fi

echo "All services stopped!"

