#!/bin/bash

PORT=5000
LOGFILE="flask.log"

# Stop any process using port 5000
PIDS=$(lsof -ti :$PORT)
if [ -n "$PIDS" ]; then
  echo "Stopping processes on port $PORT: $PIDS"
  kill -9 $PIDS
else
  echo "No process found on port $PORT."
fi

# Stop any background Flask, Gunicorn, or Python servers
pkill -f run.py 2>/dev/null || true
pkill -f flask 2>/dev/null || true
pkill -f gunicorn 2>/dev/null || true
pkill -f python3 2>/dev/null || true

# Start Flask server in background with logging
export PYTHONUNBUFFERED=1
nohup python3 -u run.py > $LOGFILE 2>&1 &

# Wait for server to start
sleep 2
if curl -s http://localhost:$PORT > /dev/null; then
  echo "Flask server started successfully on port $PORT. Logs: $LOGFILE"
else
  echo "Failed to start Flask server. Check $LOGFILE for details."
  tail -20 $LOGFILE
  exit 1
fi 