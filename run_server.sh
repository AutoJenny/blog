#!/bin/bash

echo "Stopping any existing servers..."
# Kill any process using our port
lsof -ti:5000 | xargs kill -9 2>/dev/null || true
# Kill any Flask processes
pkill -9 -f flask || true
pkill -9 -f "python.*run.py" || true
sleep 2

# Verify port is free
if lsof -i:5000 > /dev/null 2>&1; then
    echo "Error: Port 5000 is still in use after attempting to kill processes"
    exit 1
fi

# Create logs directory if it doesn't exist
mkdir -p logs

# Clear the log file
> logs/flask.log

# Set fixed environment variables
export FLASK_APP=app.py
export FLASK_DEBUG=1
export FLASK_RUN_PORT=5000

echo "Starting server on http://127.0.0.1:5000"
exec python run.py  # Using exec to replace shell process with Python 