#!/bin/bash

echo "🔄 Restarting unified Flask server..."

# Kill any existing unified_app.py processes
echo "📋 Stopping existing processes..."
pkill -f "python3 unified_app.py" 2>/dev/null

# Wait a moment for processes to stop
sleep 2

# Start the unified server
echo "🚀 Starting unified server..."
cd /Users/autojenny/Documents/projects/blog
python3 unified_app.py &

# Wait a moment for server to start
sleep 3

echo "✅ Server restarted! Available at:"
echo "   - Main: http://localhost:5000"
echo "   - Planning: http://localhost:5000/planning"
echo "   - Ideas: http://localhost:5000/planning/posts/53/idea"
echo ""
echo "Press Ctrl+C to stop the server when done."
