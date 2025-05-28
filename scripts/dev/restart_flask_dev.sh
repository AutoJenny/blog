#!/bin/bash

# Stop all processes using port 5000
PORT=5000

# Find and kill processes listening on port 5000
PIDS=$(lsof -ti :$PORT)
if [ -n "$PIDS" ]; then
  echo "Stopping processes on port $PORT: $PIDS"
  kill -9 $PIDS
else
  echo "No processes found on port $PORT."
fi

# Kill any background Flask, Gunicorn, or Python servers
pkill -f run.py 2>/dev/null && echo "Killed run.py" || echo "No run.py process found."
pkill -f flask 2>/dev/null && echo "Killed flask" || echo "No flask process found."
pkill -f gunicorn 2>/dev/null && echo "Killed gunicorn" || echo "No gunicorn process found."
pkill -f python3 2>/dev/null && echo "Killed python3" || echo "No python3 process found."

# Wait a moment for processes to exit
sleep 2

# Start Flask server with full dev diagnostics
export FLASK_ENV=development
export FLASK_DEBUG=1
export PYTHONUNBUFFERED=1

# Use python -u for unbuffered output
echo "Starting Flask server (run.py) with full dev diagnostics..."
python3 -u run.py 