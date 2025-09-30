#!/bin/bash

# Unified Blog CMS - Single Start Script
# This is the ONLY script you need to start the blog system

echo "🚀 Starting Unified Blog CMS..."

# Kill any existing processes
echo "📋 Stopping existing processes..."
pkill -f "python.*unified_app.py" 2>/dev/null || true
pkill -f "python.*app.py" 2>/dev/null || true
sleep 2

# Change to project directory
cd /Users/autojenny/Documents/projects/blog

# Start unified app
echo "🎯 Starting unified app on port 5000..."
nohup python3 unified_app.py > unified_app.log 2>&1 &
UNIFIED_PID=$!

# Wait for server to start
echo "⏳ Waiting for server to start..."
sleep 5

# Test if server is running
echo "🔍 Testing server..."
if curl -s --max-time 10 "http://localhost:5000/" > /dev/null 2>&1; then
    echo "✅ Unified Blog CMS is running successfully!"
    echo ""
    echo "🌐 Available at:"
    echo "   - Main: http://localhost:5000"
    echo "   - Planning: http://localhost:5000/planning"
    echo "   - Authoring: http://localhost:5000/authoring"
    echo ""
    echo "📝 Server PID: $UNIFIED_PID"
    echo "📄 Logs: unified_app.log"
    echo ""
    echo "🛑 To stop: pkill -f unified_app.py"
else
    echo "❌ Server failed to start!"
    echo "📄 Check logs: unified_app.log"
    echo "🔍 Last 10 lines of log:"
    tail -10 unified_app.log
    exit 1
fi

