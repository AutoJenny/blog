#!/bin/bash

# Flask Development Server Restart Script
# Stops any processes on port 5000 and restarts Flask

echo "Stopping any processes on port 5000..."
lsof -ti:5000 | xargs kill -9 2>/dev/null || echo "No processes found on port 5000"

echo "Starting Flask development server on port 5000..."
python3 -c "from app import create_app; app = create_app(); app.run(debug=True, port=5000)" 