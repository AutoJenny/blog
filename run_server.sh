#!/bin/bash

# Kill any existing processes
pkill -f flask

# Ensure logs directory exists
mkdir -p logs

# Backup database before starting
echo "Creating database backup..."
if ! ./scripts/db_backup.py; then
    echo "Warning: Database backup failed!"
    read -p "Continue anyway? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Set default port if not specified in environment
export PORT=${PORT:-5000}
export HOST=${HOST:-127.0.0.1}

# Start Flask in the background
echo "Server starting on http://$HOST:$PORT"
echo "Check logs/flask.log for details"
nohup python3 run.py > logs/flask.log 2>&1 &

# Wait a moment for the server to start
sleep 2

# Check if server started successfully
if ! curl -s "http://$HOST:$PORT/health" > /dev/null; then
    echo "Warning: Server may not have started properly. Checking logs:"
    tail -n 20 logs/flask.log
else
    echo "Server started successfully!"
    tail -n 10 logs/flask.log
fi 