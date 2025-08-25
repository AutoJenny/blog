#!/bin/bash

# Kill any existing Flask processes
echo "Killing existing Flask processes..."
if [ -f flask.pid ]; then
    kill $(cat flask.pid) 2>/dev/null
    rm flask.pid
fi

# Kill any process on port 5000
echo "Cleaning up port 5000..."
lsof -ti:5000 | xargs kill -9 2>/dev/null

# Clear Python cache
echo "Clearing Python cache..."
find . -type d -name "__pycache__" -exec rm -r {} +

# Start server with nohup and store PID
echo "Starting Flask server..."
export FLASK_DEBUG=0
export FLASK_ENV=production
nohup python3 -m flask run --no-reload > flask.log 2>&1 &
echo $! > flask.pid

echo "Server started. Check flask.log for output." 