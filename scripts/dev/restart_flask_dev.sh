#!/bin/bash

# Kill any processes running on port 5000
echo "Stopping any processes on port 5000..."
lsof -ti:5000 | xargs kill -9 2>/dev/null || echo "No processes found on port 5000"

# Wait a moment for processes to fully stop
sleep 2

# Start Flask development server
echo "Starting Flask development server on port 5000..."
python3 -c "from app import create_app; app = create_app(); app.run(debug=True, port=5000)" 