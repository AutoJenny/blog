#!/bin/bash

# Start Unified Blog CMS
echo "Starting Unified Blog CMS..."

# Kill any existing processes
echo "Stopping existing processes..."
pkill -f "python.*app.py" 2>/dev/null || true
pkill -f "python.*unified_app" 2>/dev/null || true
sleep 2

# Start unified app
echo "Starting unified app on port 5000..."
cd /Users/autojenny/Documents/projects/blog
nohup python3 unified_app.py > unified_app.log 2>&1 &
echo "Unified app started"

# Wait a moment and test
sleep 3
echo "Testing unified app..."
curl -s "http://localhost:5000/health" | head -3

echo "Unified Blog CMS is running on http://localhost:5000"
