#!/bin/bash

echo "🚀 Starting Workflow Navigation Module..."
echo "📁 Current branch: $(git branch --show-current)"
echo "🔧 Ensuring all dependencies are in place..."

# Kill any existing Flask processes
echo "🛑 Stopping any existing Flask processes..."
lsof -ti:5000 | xargs kill -9 2>/dev/null || echo "No existing processes found"

# Wait for processes to stop
sleep 2

# Start the Flask server
echo "🔥 Starting Flask server with nav module integration..."
echo "🌐 Server will be available at: http://localhost:5000/workflow/"
echo "📋 Press Ctrl+C to stop the server"
echo ""

python3 -c "from app import create_app; app = create_app(); app.run(debug=True, port=5000)" 